from typing import Annotated, Sequence, TypedDict
import json
import logging
from datetime import datetime
import uuid

from langgraph.graph import StateGraph, END
from langchain_together import ChatTogether
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from sqlalchemy import create_engine, Column, Integer, String, Text, TIMESTAMP, ForeignKey, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import sessionmaker, declarative_base

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

# Database setup
try:
    DATABASE_URL = "postgresql://postgres:postgres@postgres:5432/authdb"
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
except Exception as e:
    logger.error(f"Error setting up database: {e}")
    raise e

class Detect(Base):
    __tablename__ = "detects"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)  # Bỏ ForeignKey constraint
    detected_ingredients = Column(ARRAY(Text))
    recommendation = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

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
        
        # logger.info(f"[{state['request_id']}] LLM raw response: {content[:500]}...")
        
        # Validate response is not empty
        if not content or not content.strip():
            raise ValueError("LLM returned empty response")
        
        # Extract JSON from response
        json_content = content.strip()
        
        # Try to extract JSON from markdown code block if present
        if "```json" in json_content:
            try:
                # Find the JSON block between ```json and ```
                start_idx = json_content.find("```json") + 7
                end_idx = json_content.find("```", start_idx)
                if end_idx != -1:
                    json_content = json_content[start_idx:end_idx].strip()
                else:
                    logger.warning(f"[{state['request_id']}] Could not find closing ``` for JSON block")
            except Exception as e:
                logger.warning(f"[{state['request_id']}] Error extracting JSON from ```json block: {e}")
        elif "```" in json_content:
            try:
                # Generic code block
                start_idx = json_content.find("```") + 3
                end_idx = json_content.find("```", start_idx)
                if end_idx != -1:
                    json_content = json_content[start_idx:end_idx].strip()
                else:
                    logger.warning(f"[{state['request_id']}] Could not find closing ``` for code block")
            except Exception as e:
                logger.warning(f"[{state['request_id']}] Error extracting JSON from ``` block: {e}")
        else:
            # Try to find JSON object by looking for { and }
            try:
                start_idx = json_content.find("{")
                end_idx = json_content.rfind("}")
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_content = json_content[start_idx:end_idx + 1].strip()
            except Exception as e:
                logger.warning(f"[{state['request_id']}] Error extracting JSON by braces: {e}")
        
        # Validate extracted content is not empty
        if not json_content:
            logger.error(f"[{state['request_id']}] Extracted JSON content is empty. Original response: {content}")
            raise ValueError("Failed to extract JSON from LLM response")
        
        # logger.info(f"[{state['request_id']}] Extracted JSON: {json_content[:300]}...")
        
        # Parse JSON with better error handling
        try:
            dishes_data = json.loads(json_content)
        except json.JSONDecodeError as e:
            logger.error(f"[{state['request_id']}] JSON decode error: {e}")
            logger.error(f"[{state['request_id']}] Content that failed to parse: {json_content}")
            raise ValueError(f"Invalid JSON response from LLM: {str(e)}")
        
        # Validate JSON structure
        if not isinstance(dishes_data, dict):
            raise ValueError(f"Expected JSON object, got {type(dishes_data)}")
        
        dishes = dishes_data.get("dishes", [])
        
        if not isinstance(dishes, list):
            raise ValueError(f"Expected 'dishes' to be a list, got {type(dishes)}")
        
        if len(dishes) == 0:
            logger.warning(f"[{state['request_id']}] No dishes found in response")
            raise ValueError("LLM did not suggest any dishes")
        
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

def extract_json_from_response(content: str, request_id: str) -> dict:
    """
    Extract JSON from LLM response, handling multiple formats:
    -
json ...
    -
bash ...
    -
...
    - Raw JSON with { }
    """
    if not content or not content.strip():
        raise ValueError("Empty response content")
    
    json_content = content.strip()
    
    # Try to extract from code blocks (in order of preference)
    extraction_patterns = [
        ("```json", "```"),
        ("```bash", "```"), 
        ("```", "```"),     
    ]
    
    for start_marker, end_marker in extraction_patterns:
        if start_marker in json_content:
            try:
                start_idx = json_content.find(start_marker) + len(start_marker)
                end_idx = json_content.find(end_marker, start_idx)
                
                if end_idx != -1:
                    extracted = json_content[start_idx:end_idx].strip()
                    logger.info(f"[{request_id}] Extracted JSON from {start_marker} block")
                    
                    # Try to parse and return immediately if successful
                    try:
                        return json.loads(extracted)
                    except json.JSONDecodeError as e:
                        logger.warning(f"[{request_id}] Failed to parse extracted {start_marker} content: {e}")
                        # Continue to next pattern
                        continue
            except Exception as e:
                logger.warning(f"[{request_id}] Error extracting {start_marker} block: {e}")
                continue
    
    # Try to find JSON by braces { }
    try:
        start_idx = json_content.find("{")
        end_idx = json_content.rfind("}")
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            extracted = json_content[start_idx:end_idx + 1].strip()
            logger.info(f"[{request_id}] Extracted JSON by braces")
            
            try:
                return json.loads(extracted)
            except json.JSONDecodeError as e:
                logger.warning(f"[{request_id}] Failed to parse brace-extracted content: {e}")
    except Exception as e:
        logger.warning(f"[{request_id}] Error extracting JSON by braces: {e}")
    
    # If all extraction attempts fail, try to parse the whole content
    try:
        logger.info(f"[{request_id}] Attempting to parse entire content as JSON")
        return json.loads(json_content)
    except json.JSONDecodeError as e:
        logger.error(f"[{request_id}] JSON decode error: {e}")
        logger.error(f"[{request_id}] Content that failed to parse (first 500 chars): {json_content[:500]}")
        raise ValueError(f"Failed to extract valid JSON from response: {str(e)}")

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
            ingredients=ingredients_str,
            additional_ingredients=state["additional_ingredients"],
        )
        
        logger.info(f"[{state['request_id']}] Recipe generation prompt: {prompt}...")
        
        # Call LLM
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        recipe_text = response.content
        
        print(f"[{state['request_id']}] LLM raw recipe response:\n {str(recipe_text)}...")
        logger.info(f"[{state['request_id']}] Generated recipe: {len(recipe_text)} chars")
        
        # Parse recipe (we'll store as structured data)
        # For simplicity, we'll parse the markdown-style response
        recipe_json = extract_json_from_response(recipe_text, state["request_id"])
        recipe = parse_recipe_json(recipe_json, state["selected_dish"], state["ingredient_names"], state["additional_ingredients"])
        
        # Save to database
        try:
            db = SessionLocal()
            detect_record = Detect(
                user_id=int(state["user_id"]),
                detected_ingredients=state["ingredient_names"],
                recommendation=json.dumps(recipe, ensure_ascii=False)
            )
            db.add(detect_record)
            db.commit()
            db.refresh(detect_record)
            logger.info(f"[{state['request_id']}] Saved recipe to database with ID: {detect_record.id}")
            db.close()
        except Exception as db_error:
            logger.error(f"[{state['request_id']}] Failed to save to database: {db_error}")
            # Continue even if DB save fails
        
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

def parse_recipe_json(recipe_json: dict, dish_name: str, ingredient_names: list, additional_ingredients: list) -> dict:
    """Parse recipe from JSON format to structured format"""
    
    recipe = {
        "dish_name": dish_name,
        "ingredients": {
            "available": ingredient_names,
            "needed": additional_ingredients
        },
        "preparation": recipe_json.get("preparation", []),
        "steps": recipe_json.get("steps", []),
        "tips": recipe_json.get("tips", []),
        "nutrition": {
            "calories": recipe_json.get("nutrition", {}).get("calories", ""),
            "protein": recipe_json.get("nutrition", {}).get("protein", ""),
            "carbohydrate": recipe_json.get("nutrition", {}).get("carbohydrate", ""),
            "fat": recipe_json.get("nutrition", {}).get("fat", ""),
            "fiber": recipe_json.get("nutrition", {}).get("fiber", ""),
            "vitamins": recipe_json.get("nutrition", {}).get("vitamins", "")
        },
        "time": {
            "prep": recipe_json.get("time", {}).get("prep", ""),
            "cook": recipe_json.get("time", {}).get("cook", ""),
            "total": recipe_json.get("time", {}).get("total", "")
        },
        "servings": recipe_json.get("servings", 2),
        "raw_json": recipe_json
    }
    
    return recipe

def parse_recipe_text(recipe_text: str, dish_name: str, ingredient_names: list, additional_ingredients: list) -> dict:
    """Parse recipe text into structured format"""
    import re
    
    recipe = {
        "dish_name": dish_name,
        "ingredients": {
            "available": [],
            "needed": []
        },
        "preparation": [],
        "steps": [],
        "tips": [],
        "nutrition": {
            "calories": "",
            "protein": "",
            "carbohydrate": "",
            "fat": "",
            "fiber": "",
            "vitamins": ""
        },
        "time": {
            "prep": "",
            "cook": "",
            "total": ""
        },
        "servings": 2,
        "raw_text": recipe_text
    }
    
    # Split text into lines for processing
    lines = recipe_text.split('\\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Detect section headers (must match exactly)
        if line == "**Nguyên liệu cần thiết:**":
            logger.info("Parsing ingredients section")
            current_section = "ingredients"
            continue
        elif line == "**Chuẩn bị:**":
            logger.info("Parsing preparation section")
            current_section = "preparation"
            continue
        elif line == "**Các bước nấu:**":
            logger.info("Parsing steps section")
            current_section = "steps"
            continue
        elif line == "**Mẹo và lưu ý:**":
            logger.info("Parsing tips section")
            current_section = "tips"
            continue
        elif "**Phân tích dinh dưỡng" in line:
            logger.info("Parsing nutrition section")
            current_section = "nutrition"
            continue
        elif line == "**Thời gian:**":
            logger.info("Parsing time section")
            current_section = "time"
            continue
        elif line.startswith("**Số khẩu phần:**"):
            logger.info("Parsing servings section")
            # Extract servings number
            servings_match = re.search(r'(\d+)[-\s]*(\d*)\s*người', line)
            if servings_match:
                # Take first number if range (e.g., "4-6 người" -> 4)
                recipe["servings"] = int(servings_match.group(1))
            current_section = None
            continue
        
        # Skip other header lines
        if line.startswith('**') and line.endswith('**'):
            continue
        
        # Process content based on current section
        if current_section == "ingredients":
            # Parse ingredients: - Item (quantity) *(status)*
            if line.startswith('-'):
                clean_line = line.lstrip('-').strip()
                
                # Check status in parentheses
                if "*(đã có sẵn)*" in clean_line or "*đã có sẵn*" in clean_line:
                    # Remove status markers
                    ingredient = re.sub(r'\*\([^)]*\)\*', '', clean_line).strip()
                    ingredient = re.sub(r'\*[^*]*\*', '', ingredient).strip()
                    recipe["ingredients"]["available"].append(ingredient)
                elif "*(cần mua thêm)*" in clean_line or "*cần mua thêm*" in clean_line:
                    # Remove status markers
                    ingredient = re.sub(r'\*\([^)]*\)\*', '', clean_line).strip()
                    ingredient = re.sub(r'\*[^*]*\*', '', ingredient).strip()
                    recipe["ingredients"]["needed"].append(ingredient)
                else:
                    # No status marker, just clean up
                    ingredient = re.sub(r'\*\([^)]*\)\*', '', clean_line).strip()
                    ingredient = re.sub(r'\*[^*]*\*', '', ingredient).strip()
                    # Check if in detected ingredients
                    ingredient_base = ingredient.split('(')[0].strip()
                    if any(ing in ingredient_base for ing in ingredient_names):
                        recipe["ingredients"]["available"].append(ingredient)
                    else:
                        recipe["ingredients"]["needed"].append(ingredient)
        
        elif current_section == "preparation":
            # Parse preparation steps: - text or + text
            if line.startswith(('-', '+')):
                clean_line = line.lstrip('-+').strip()
                if clean_line:
                    recipe["preparation"].append(clean_line)
        
        elif current_section == "steps":
            # Parse main steps: - **Bước X: Title**
            if line.startswith('-') and '**Bước' in line:
                # Extract step without leading dash and format markers
                clean_line = line.lstrip('-').strip()
                clean_line = clean_line.replace('**', '').strip()
                if clean_line:
                    recipe["steps"].append(clean_line)
            # Parse sub-steps: + text
            elif line.startswith('+'):
                clean_line = line.lstrip('+').strip()
                if clean_line and recipe["steps"]:
                    # Add as sub-step with indent
                    recipe["steps"].append("  " + clean_line)
        
        elif current_section == "tips":
            # Parse tips: - text
            if line.startswith('-'):
                clean_line = line.lstrip('-').strip()
                if clean_line:
                    recipe["tips"].append(clean_line)
        
        elif current_section == "nutrition":
            # Parse nutrition info: - Key: value
            if line.startswith('-') and ':' in line:
                clean_line = line.lstrip('-').strip()
                parts = clean_line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower()
                    value = parts[1].strip()
                    
                    if "calo" in key or "lượng calo" in key:
                        recipe["nutrition"]["calories"] = value
                    elif "protein" in key:
                        recipe["nutrition"]["protein"] = value
                    elif "carbohydrate" in key:
                        recipe["nutrition"]["carbohydrate"] = value
                    elif "fat" in key:
                        recipe["nutrition"]["fat"] = value
                    elif "chất xơ" in key:
                        recipe["nutrition"]["fiber"] = value
                    elif "vitamin" in key or "khoáng chất" in key:
                        recipe["nutrition"]["vitamins"] = value
        
        elif current_section == "time":
            # Parse time info: - Key: value
            if line.startswith('-') and ':' in line:
                clean_line = line.lstrip('-').strip()
                parts = clean_line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower()
                    value = parts[1].strip()
                    
                    if "chuẩn bị" in key:
                        recipe["time"]["prep"] = value
                    elif "nấu" in key and "tổng" not in key:
                        recipe["time"]["cook"] = value
                    elif "tổng" in key:
                        recipe["time"]["total"] = value
    
    # Fallback: if no ingredients parsed, use the provided lists
    if not recipe["ingredients"]["available"] and not recipe["ingredients"]["needed"]:
        recipe["ingredients"]["available"] = ingredient_names
        recipe["ingredients"]["needed"] = additional_ingredients
    
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

async def continue_cooking_session(request_id: str, selected_dish_name: str, additional_ingredients: list) -> AgentState:
    """Continue session after user selects a dish"""
    try:
        # Load state
        logger.info(f"Loading state for request {request_id}")
        state = state_store.load_state(request_id)
        
        if not state:
            logger.error(f"Request {request_id} not found in state store")
            raise ValueError(f"Request {request_id} not found")
        
        logger.info(f"[{request_id}] Current state stage: {state.get('stage')}, awaiting_feedback: {state.get('awaiting_human_feedback')}")
        
        if state["stage"] != "waiting_selection":
            logger.error(f"[{request_id}] Invalid stage: {state['stage']}, expected 'waiting_selection'")
            raise ValueError(f"Request {request_id} is not waiting for selection (current stage: {state['stage']})")
        
        # Update state with selection
        state["selected_dish"] = selected_dish_name
        state["additional_ingredients"] = additional_ingredients
        state["awaiting_human_feedback"] = False
        state["updated_at"] = datetime.utcnow().isoformat()
        state["messages"].append(f"Người dùng đã chọn món: {selected_dish_name}")
        
        logger.info(f"[{request_id}] Updated state - selected_dish: {selected_dish_name}")
        
        # Save state before continuing (important for persistence)
        state_store.save_state(state)
        logger.info(f"[{request_id}] State saved with selected dish")
        
        # Execute remaining nodes manually (generate_recipe -> send_recipe_email)
        # Instead of invoking the whole agent which starts from entry point
        
        logger.info(f"[{request_id}] Executing generate_recipe node...")
        state = generate_recipe_node(state)
        
        if state.get("error"):
            logger.error(f"[{request_id}] Error in generate_recipe: {state['error']}")
            state_store.save_state(state)
            return state
        
        logger.info(f"[{request_id}] Recipe generated successfully, stage: {state['stage']}")
        
        logger.info(f"[{request_id}] Executing send_recipe_email node...")
        state = send_recipe_email_node(state)
        
        logger.info(f"[{request_id}] Final stage: {state['stage']}")
        
        # Save final state
        state_store.save_state(state)
        logger.info(f"[{request_id}] Final state saved")
        
        return state
        
    except Exception as e:
        logger.error(f"[{request_id}] Error continuing cooking session: {e}", exc_info=True)
        raise e
