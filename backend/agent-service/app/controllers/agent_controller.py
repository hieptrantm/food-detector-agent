from fastapi import APIRouter, HTTPException, Depends, Header, Query
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from fastapi.responses import HTMLResponse
import httpx
import logging

from app.services.cooking_agent import start_cooking_session, continue_cooking_session
from app.services.state_store import state_store
from app.services.email_service import verify_selection_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])

AUTH_SERVICE_URL = "http://auth-service:8000"

# Request/Response Models
class IngredientModel(BaseModel):
    label: str
    confidence: float
    bbox: List[float]

class StartCookingRequest(BaseModel):
    detected_ingredients: List[IngredientModel]

class StartCookingResponse(BaseModel):
    request_id: str
    status: str
    message: str
    stage: str

class RequestStatusResponse(BaseModel):
    request_id: str
    stage: str
    status: str
    created_at: str
    updated_at: str
    error: Optional[str] = None

class DishSelectionResponse(BaseModel):
    success: bool
    message: str
    request_id: str

# Token verification
async def verify_token(authorization: str = Header(None)):
    """Verify JWT token from auth service"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization.split(" ")[1]
    
    async with httpx.AsyncClient() as client:
        try:
            user = await client.get(
                f"{AUTH_SERVICE_URL}/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )

            if user.status_code != 200:
                raise HTTPException(status_code=401, detail="User not found")
            return user.json()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Auth service unavailable")

@router.post("/start", response_model=StartCookingResponse)
async def start_cooking(
    request: StartCookingRequest,
    user=Depends(verify_token)  # Temporarily disabled for testing
):
    """
    Start a cooking session with detected ingredients
    
    This will:
    1. Suggest dishes based on detected ingredients
    2. Send email to user with suggestions
    3. Wait for user to select a dish via email
    """
    try:
        # Extract user info
        user_id = user.get("id")
        user_email = user.get("email")
        username = user.get("username", "User")
        
        if not user_email:
            raise HTTPException(status_code=400, detail="User email not found")
        
        # Convert to dict for agent
        ingredients_data = [ing.model_dump() for ing in request.detected_ingredients]
        
        # Start agent session
        state = await start_cooking_session(
            user_id=str(user_id),
            user_email=user_email,
            username=username,
            detected_ingredients=ingredients_data
        )
        
        if state["error"]:
            raise HTTPException(status_code=500, detail=state["error"])
        
        return StartCookingResponse(
            request_id=state["request_id"],
            status="success",
            message="Đã gửi email gợi ý món ăn. Vui lòng kiểm tra email và chọn món bạn muốn nấu.",
            stage=state["stage"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting cooking session: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/select-dish", response_class=HTMLResponse)
async def select_dish(
    token: str = Query(..., description="Selection token from email"),
    dish_index: int = Query(..., description="Index of selected dish")
):
    """
    Handle dish selection from email link
    
    This is called when user clicks a dish selection button in the email
    """
    # Verify token
    payload = verify_selection_token(token)
    request_id = payload.get("request_id")
    user_id = payload.get("user_id")
    
    payload = {
        "request_id": "12321321",
        "user_id": 123
    }
    
    logger.info(f"Dish selection token verified for request {request_id}, user {user_id}")
    try:
        # Mock payload for testing
        # payload = {
        #     "request_id": "test-request-123",
        #     "user_id": "test-user-123"
        # }
        logger.info(f"Dish selection for request {request_id}, dish index {dish_index}")
        
        # Load state
        state = state_store.load_state(request_id)
        logger.debug(f"Loaded state for request {request_id}: {state}")
        
        # logger.info(f"Previous state loaded for request {request_id}: {state}")
        logger.info(f"Current state stage: {state['stage'] if state else 'N/A'}")
        if not state:
            raise HTTPException(status_code=404, detail="Request not found or expired")
        
        if state["stage"] != "waiting_selection":
            raise HTTPException(status_code=400, detail="Request is not waiting for selection")
        
        # Get selected dish
        if not state["suggested_dishes"] or dish_index >= len(state["suggested_dishes"]):
            raise HTTPException(status_code=400, detail="Invalid dish selection")
        
        selected_dish = state["suggested_dishes"][dish_index]
        selected_dish_name = selected_dish["name"]
        additional_ingredients = selected_dish.get("additional_ingredients", [])
        
        logger.info(f"User selected dish: {selected_dish_name}")
        logger.info(f"Additional ingredients needed: {additional_ingredients}")
        
        # Continue agent session
        result_state = await continue_cooking_session(request_id, selected_dish_name, additional_ingredients)
        logger.info(f"Resulting state after selection: {result_state}")
        
        if result_state["error"]:
            raise HTTPException(status_code=500, detail=result_state["error"])
        
        return HTMLResponse(f"""
            <!DOCTYPE html>
            <html lang="vi">
            <head>
                <meta charset="UTF-8" />
                <title>Đã Chọn Món</title>
                <style>
                    body {{
                        margin: 0;
                        padding: 0;
                        height: 100vh;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        background: #f5f6fa;
                        font-family: Arial, sans-serif;
                    }}
                    .box {{
                        background: white;
                        padding: 32px 40px;
                        border-radius: 12px;
                        box-shadow: 0 4px 18px rgba(0,0,0,0.15);
                        text-align: center;
                        max-width: 400px;
                    }}
                    h1 {{
                        margin: 0 0 12px;
                        font-size: 24px;
                        color: #333;
                    }}
                    p {{
                        margin-top: 6px;
                        color: #555;
                        font-size: 16px;
                    }}
                </style>
            </head>
            <body>
                <div class="box">
                    <h1>🎉 Đã chọn món!</h1>
                    <p><b>{selected_dish_name}</b></p>
                    <p>Hướng dẫn nấu ăn sẽ được gửi qua email trong giây lát.</p>
                </div>
            </body>
            </html>
        """)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error selecting dish: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/status/{request_id}", response_model=RequestStatusResponse)
async def get_request_status(
    request_id: str,
    user=Depends(verify_token)
):
    """
    Get status of a cooking request
    """
    try:
        status = state_store.get_request_status(request_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Request not found")
        
        # Load full state for error info
        state = state_store.load_state(request_id)
        
        return RequestStatusResponse(
            request_id=status["request_id"],
            stage=status["stage"],
            status=status["status"],
            created_at=status["created_at"],
            updated_at=status["updated_at"],
            error=state.get("error") if state else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting request status: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "agent-service"}
