from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import jwt
import os
from datetime import datetime, timedelta
from typing import List
import logging

from config import (
    SENDGRID_API_KEY, 
    SECRET_KEY, 
    FROM_EMAIL,
    EMAIL_DISH_SELECTION_TEMPLATE,
    EMAIL_RECIPE_TEMPLATE,
    FRONTEND_URL
)
from app.models.state import Dish

logger = logging.getLogger(__name__)

def generate_selection_token(request_id: str, user_id: str) -> str:
    """Generate JWT token for dish selection"""
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode = {
        "request_id": request_id,
        "user_id": user_id,
        "type": "dish_selection",
        "exp": expire
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

def verify_selection_token(token: str) -> dict:
    """Verify and decode selection token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "dish_selection":
            raise ValueError("Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")

def send_dish_selection_email(
    email: str,
    username: str,
    ingredients: List[str],
    dishes: List[Dish],
    request_id: str,
    user_id: str
) -> bool:
    """Send email with dish suggestions for user to select"""
    if not SENDGRID_API_KEY:
        logger.warning("SENDGRID_API_KEY not set, skipping email")
        return False
    
    
    # Generate token for selection
    token = generate_selection_token(request_id, user_id)
    
    # Build dishes HTML
    dishes_html = ""
    for i, dish in enumerate(dishes):
        additional = ", ".join(dish["additional_ingredients"]) if dish["additional_ingredients"] else "Không cần thêm"
        dishes_html += f"""
        <div class="dish-card">
            <div class="dish-name">🍽️ {dish['name']}</div>
            <div class="dish-info">📝 {dish['description']}</div>
            <div class="dish-info">⏱️ Thời gian: {dish['cooking_time']}</div>
            <div class="dish-info">📊 Độ khó: {dish['difficulty']}</div>
            <div class="dish-info">🛒 Cần thêm: {additional}</div>
        </div>
        """
    
    # Build selection buttons
    selection_buttons = ""
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    for i, dish in enumerate(dishes):
        selection_url = f"{backend_url}/agent/select-dish?token={token}&dish_index={i}"
        # selection_url = f"{backend_url}/select-dish?token={token}&dish_index={i}"
        
        selection_buttons += f"""
        <a href="{selection_url}" class="button"> {dish['name']}</a>
        """
        
    logger.info(f"Selection buttons HTML: {selection_buttons}")

    ingredients_tags_html = "\n".join([ # Dùng \n thay vì chuỗi dài khoảng trắng
        f'<span class="ingredient-tag">{ingredient.strip()}</span>'
        for ingredient in ingredients
    ])
    
    # Render email
    html_content = EMAIL_DISH_SELECTION_TEMPLATE.format(
        username=username,
        ingredients_tags=ingredients_tags_html,
        dishes_html=dishes_html,
        selection_buttons=selection_buttons
    )
    
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=email,
        subject=f'🍳 Gợi Ý Món Ăn Từ {len(dishes)} Món - AI Chef',
        html_content=html_content
    )
    
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info(f"Selection email sent to {email}, status: {response.status_code}")
        return response.status_code == 202
    except Exception as e:
        logger.error(f"Error sending selection email: {e}")
        return False

def send_recipe_email(
    email: str,
    username: str,
    dish_name: str,
    recipe_content: str
) -> bool:
    """Send email with detailed cooking recipe"""
    if not SENDGRID_API_KEY:
        logger.warning("SENDGRID_API_KEY not set, skipping email")
        return False
    
    # Render email
    html_content = EMAIL_RECIPE_TEMPLATE.format(
        dish_name=dish_name,
        recipe_content=recipe_content
    )
    
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=email,
        subject=f'👨‍🍳 Hướng Dẫn Nấu: {dish_name} - AI Chef',
        html_content=html_content
    )
    
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info(f"Recipe email sent to {email}, status: {response.status_code}")
        return response.status_code == 202
    except Exception as e:
        logger.error(f"Error sending recipe email: {e}")
        return False

def format_recipe_html(recipe: dict) -> str:
    """Format recipe data into HTML for email"""
    html = ""
    
    # Ingredients section 
    html += '<div class="section">'
    html += '<div class="section-title">📋 Nguyên Liệu</div>'
    
    html += '<div class="ingredient-tags-container">' 
    
    if "ingredients" in recipe and "available" in recipe["ingredients"]:
        html += '<p class="ingredient-category-label">✅ Đã có sẵn:</p>'
        for ing in recipe["ingredients"]["available"]:
            html += f'<span class="ingredient-tag tag-available">{ing}</span>' 
            
    if "ingredients" in recipe and "needed" in recipe["ingredients"]:
        html += '<p class="ingredient-category-label">🛒 Cần mua thêm:</p>'
        for ing in recipe["ingredients"]["needed"]:
            html += f'<span class="ingredient-tag tag-needed">{ing}</span>'
    
    html += '</div></div>'
    
    # Preparation section
    if "preparation" in recipe and recipe["preparation"]:
        html += '<div class="section">'
        html += '<div class="section-title">🔪 Chuẩn Bị</div>'
        for prep in recipe["preparation"]:
            html += f'<p>• {prep}</p>'
        html += '</div>'
    
    # Steps section
    if "steps" in recipe and recipe["steps"]:
        html += '<div class="section">'
        html += '<div class="section-title">👨‍🍳 Các Bước Nấu</div>'
        for i, step in enumerate(recipe["steps"], 1):
            html += f'<div class="step"><span class="step-number">{i}</span>{step}</div>'
        html += '</div>'
    
    # Tips section
    if "tips" in recipe and recipe["tips"]:
        html += '<div class="section">'
        html += '<div class="section-title">💡 Mẹo Và Lưu Ý</div>'
        for tip in recipe["tips"]:
            html += f'<p>• {tip}</p>'
        html += '</div>'
    
    # Nutrition section
    if "nutrition" in recipe:
        html += '<div class="section">'
        html += '<div class="section-title">🥗  (1 khẩu phần)</div>'
        html += '<table class="nutrition-table">'
        for key, value in recipe["nutrition"].items():
            html += f'<tr><td><strong>{key}</strong></td><td>{value}</td></tr>'
        html += '</table></div>'
    
    # Time section
    if "time" in recipe:
        html += '<div class="section">'
        html += '<div class="section-title">⏰ Thời Gian</div>'
        for key, value in recipe["time"].items():
            html += f'<p><strong>{key}:</strong> {value}</p>'
        html += '</div>'
    
    # Servings
    if "servings" in recipe:
        html += f'<div class="section">'
        html += f'<div class="section-title">🍽️ Khẩu Phần</div>'
        html += f'<p><strong>{recipe["servings"]} người</strong></p>'
        html += '</div>'
    
    return html
