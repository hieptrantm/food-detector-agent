from typing import Annotated, Sequence, TypedDict
import json
import logging
from datetime import datetime
import uuid

from langgraph.graph import StateGraph, END
from langchain_together import ChatTogether
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from app.models.state import AgentState, Dish, Ingredient
from app.services.email_service import (
    send_dish_selection_email, 
    send_recipe_email,
    format_recipe_html
)
from app.services.state_store import state_store
from config import (
    TOGETHER_API_KEY,
    SYSTEM_PROMPT,
    SUGGEST_DISHES_PROMPT,
    GENERATE_RECIPE_PROMPT
)

logger = logging.getLogger(__name__)

try:
    # Initialize LLM with Together AI
    llm = ChatTogether(
        model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        api_key=TOGETHER_API_KEY,
        temperature=0.7
    )
    logger.info(f"Initialized Together AI LLM with Llama 3.1 70B")
except Exception as e:
    logger.error(f"Error initializing Together AI LLM: {e}")
    raise e

def create_initial_state(
    user_id: str,
    user_email: str,
    username: str,
    detected_ingredients: list
) -> AgentState:
    """Create initial agent state"""
    request_id = str(uuid.uuid4())
    
    # Extract ingredient names
    ingredient_names = list(set([ing["label"] for ing in detected_ingredients]))
    
    state: AgentState = {
        "request_id": request_id,
        "user_id": user_id,
        "user_email": user_email,
        "username": username,
        "detected_ingredients": detected_ingredients,
        "ingredient_names": ingredient_names,
        "stage": "suggesting",
        "suggested_dishes": None,
        "selected_dish": None,
        "recipe": None,
        "messages": [],
        "error": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "awaiting_human_feedback": False,
        "feedback_token": None
    }
    
    return state

def suggest_dishes_node(state: AgentState) -> AgentState:
    """Node: Suggest dishes based on detected ingredients"""
    logger.info(f"[{state['request_id']}] Suggesting dishes...")
    
    try:
        ingredients_str = ", ".join(state["ingredient_names"])
        
        # Create prompt
        prompt = SUGGEST_DISHES_PROMPT.format(ingredients=ingredients_str)
        
        # Call LLM
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        content = response.content
        
        logger.info(f"[{state['request_id']}] LLM response: {content}...")
        
        # Parse JSON response
        # Try to extract JSON from markdown code block if present
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            else:
                content = content.strip()
        except Exception as e:
            logger.warning(f"[{state['request_id']}] Error extracting JSON from markdown: {e}")
        
        dishes_data = json.loads(content)
        dishes = dishes_data.get("dishes", [])
        
        logger.info(f"[{state['request_id']}] Parsed {len(dishes)} dishes")
        logger.info(f"[{state['request_id']}] Dishes: {dishes}")
        
        # Update state
        state["suggested_dishes"] = dishes
        state["stage"] = "waiting_selection"
        state["messages"].append(f"Đã gợi ý {len(dishes)} món ăn")
        
        logger.info(f"[{state['request_id']}] Suggested {len(dishes)} dishes")
        
    except Exception as e:
        logger.error(f"[{state['request_id']}] Error suggesting dishes: {e}")
        state["error"] = f"Không thể gợi ý món ăn: {str(e)}"
        state["stage"] = "error"
    
    return state

def send_selection_email_node(state: AgentState) -> AgentState:
    """Node: Send email to user for dish selection"""
    logger.info(f"[{state['request_id']}] Sending selection email...")
    
    try:
        if not state["suggested_dishes"]:
            raise ValueError("No dishes to suggest")
        
        # Send email
        success = send_dish_selection_email(
            email=state["user_email"],
            username=state["username"],
            ingredients=state["ingredient_names"],
            dishes=state["suggested_dishes"],
            request_id=state["request_id"],
            user_id=state["user_id"]
        )
        
        if success:
            state["awaiting_human_feedback"] = True
            state["messages"].append("Đã gửi email gợi ý món ăn")
            logger.info(f"[{state['request_id']}] Selection email sent successfully")
        else:
            raise Exception("Failed to send email")
        
    except Exception as e:
        logger.error(f"[{state['request_id']}] Error sending selection email: {e}")
        state["error"] = f"Không thể gửi email: {str(e)}"
        state["stage"] = "error"
    
    return state

def generate_recipe_node(state: AgentState) -> AgentState:
    """Node: Generate detailed recipe for selected dish"""
    logger.info(f"[{state['request_id']}] Generating recipe for {state['selected_dish']}...")
    
    try:
        if not state["selected_dish"]:
            raise ValueError("No dish selected")
        
        ingredients_str = ", ".join(state["ingredient_names"])
        
        # Create prompt
        prompt = GENERATE_RECIPE_PROMPT.format(
            dish_name=state["selected_dish"],
            ingredients=ingredients_str
        )
        
        # Call LLM
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        recipe_text = response.content
        
        logger.info(f"[{state['request_id']}] Generated recipe: {len(recipe_text)} chars")
        
        # Parse recipe (we'll store as structured data)
        # For simplicity, we'll parse the markdown-style response
        recipe = parse_recipe_text(recipe_text, state["selected_dish"])
        
        state["recipe"] = recipe
        state["stage"] = "completed"
        state["messages"].append(f"Đã tạo hướng dẫn nấu món {state['selected_dish']}")
        
    except Exception as e:
        logger.error(f"[{state['request_id']}] Error generating recipe: {e}")
        state["error"] = f"Không thể tạo hướng dẫn: {str(e)}"
        state["stage"] = "error"
    
    return state

def send_recipe_email_node(state: AgentState) -> AgentState:
    """Node: Send recipe email to user"""
    logger.info(f"[{state['request_id']}] Sending recipe email...")
    
    try:
        if not state["recipe"]:
            raise ValueError("No recipe to send")
        
        # Format recipe as HTML
        recipe_html = format_recipe_html(state["recipe"])
        
        # Send email
        success = send_recipe_email(
            email=state["user_email"],
            username=state["username"],
            dish_name=state["selected_dish"],
            recipe_content=recipe_html
        )
        
        if success:
            state["messages"].append("Đã gửi email hướng dẫn nấu ăn")
            logger.info(f"[{state['request_id']}] Recipe email sent successfully")
        else:
            raise Exception("Failed to send recipe email")
        
    except Exception as e:
        logger.error(f"[{state['request_id']}] Error sending recipe email: {e}")
        state["error"] = f"Không thể gửi email hướng dẫn: {str(e)}"
        # Don't change stage to error since recipe was generated
    
    return state

def parse_recipe_text(recipe_text: str, dish_name: str) -> dict:
    """Parse recipe text into structured format"""
    # This is a simplified parser
    # In production, you might want to use LLM with structured output
    
    recipe = {
        "dish_name": dish_name,
        "ingredients": {
            "available": [],
            "needed": []
        },
        "preparation": [],
        "steps": [],
        "tips": [],
        "nutrition": {},
        "time": {},
        "servings": 2
    }
    
    # Simple parsing logic
    lines = recipe_text.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Detect sections
        if "nguyên liệu" in line.lower():
            current_section = "ingredients"
        elif "chuẩn bị" in line.lower():
            current_section = "preparation"
        elif "bước" in line.lower() or "các bước" in line.lower():
            current_section = "steps"
        elif "mẹo" in line.lower() or "lưu ý" in line.lower():
            current_section = "tips"
        elif "dinh dưỡng" in line.lower():
            current_section = "nutrition"
        elif "thời gian" in line.lower():
            current_section = "time"
        elif "khẩu phần" in line.lower():
            current_section = "servings"
        elif line.startswith(('-', '•', '*', '1.', '2.', '3.')):
            # Add to current section
            clean_line = line.lstrip('-•*0123456789. ')
            
            if current_section == "preparation":
                recipe["preparation"].append(clean_line)
            elif current_section == "steps":
                recipe["steps"].append(clean_line)
            elif current_section == "tips":
                recipe["tips"].append(clean_line)
    
    # If parsing failed, store raw text
    if not recipe["steps"]:
        recipe["raw_text"] = recipe_text
    
    return recipe

def should_wait_for_selection(state: AgentState) -> str:
    """Conditional edge: Check if waiting for user selection"""
    if state["stage"] == "waiting_selection" and state["awaiting_human_feedback"]:
        return "wait"
    elif state["stage"] == "generating_recipe":
        return "generate"
    elif state["stage"] == "completed":
        return "send_email"
    elif state["stage"] == "error":
        return "error"
    else:
        return "continue"

def build_cooking_agent() -> StateGraph:
    """Build the cooking agent graph"""
    
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("suggest_dishes", suggest_dishes_node)
    workflow.add_node("send_selection_email", send_selection_email_node)
    workflow.add_node("generate_recipe", generate_recipe_node)
    workflow.add_node("send_recipe_email", send_recipe_email_node)
    
    # Define edges
    workflow.set_entry_point("suggest_dishes")
    
    workflow.add_edge("suggest_dishes", "send_selection_email")
    
    # Conditional edge from send_selection_email
    workflow.add_conditional_edges(
        "send_selection_email",
        should_wait_for_selection,
        {
            "wait": END,  # Wait for human feedback
            "generate": "generate_recipe",
            "error": END
        }
    )
    
    workflow.add_edge("generate_recipe", "send_recipe_email")
    workflow.add_edge("send_recipe_email", END)
    
    return workflow.compile()

# Global agent instance
cooking_agent = build_cooking_agent()

async def start_cooking_session(
    user_id: str,
    user_email: str,
    username: str,
    detected_ingredients: list
) -> AgentState:
    """Start a new cooking session"""
    
    # Create initial state
    state = create_initial_state(
        user_id=user_id,
        user_email=user_email,
        username=username,
        detected_ingredients=detected_ingredients
    )
    
    # Save initial state
    state_store.save_state(state)
    
    # Run agent until it waits for human feedback
    result = await cooking_agent.ainvoke(state)
    
    # Save updated state
    state_store.save_state(result)
    
    return result

async def continue_cooking_session(request_id: str, selected_dish_name: str) -> AgentState:
    """Continue session after user selects a dish"""
    
    # Load state
    state = state_store.load_state(request_id)
    
    if not state:
        raise ValueError(f"Request {request_id} not found")
    
    if state["stage"] != "waiting_selection":
        raise ValueError(f"Request {request_id} is not waiting for selection")
    
    # Update state with selection
    state["selected_dish"] = selected_dish_name
    state["stage"] = "generating_recipe"
    state["awaiting_human_feedback"] = False
    state["messages"].append(f"Người dùng đã chọn món: {selected_dish_name}")
    
    # Continue agent execution
    result = await cooking_agent.ainvoke(state)
    
    # Save final state
    state_store.save_state(result)
    
    return result
