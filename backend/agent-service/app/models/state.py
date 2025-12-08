from typing import List, Optional, Literal
from typing_extensions import TypedDict
from datetime import datetime

class Ingredient(TypedDict):
    """Detected ingredient from image"""
    label: str
    confidence: float
    bbox: List[float]

class Dish(TypedDict):
    """Suggested dish"""
    name: str
    description: str
    difficulty: Literal["Dễ", "Trung bình", "Khó"]
    cooking_time: str
    additional_ingredients: List[str]

class Recipe(TypedDict):
    """Full recipe with instructions"""
    dish_name: str
    ingredients: dict
    preparation: List[str]
    steps: List[str]
    tips: List[str]
    nutrition: dict
    time: dict
    servings: int

class AgentState(TypedDict):
    """State for the cooking agent"""
    # Request information
    request_id: str
    user_id: str
    user_email: str
    username: str
    
    # Detection results
    detected_ingredients: List[Ingredient]
    ingredient_names: List[str]
    
    # Agent workflow state
    stage: Literal["detecting", "suggesting", "waiting_selection", "generating_recipe", "completed", "error"]
    
    # Suggestions
    suggested_dishes: Optional[List[Dish]]
    
    # User selection
    selected_dish: Optional[str]
    
    # Generated recipe
    recipe: Optional[Recipe]
    
    # Messages and errors
    messages: List[str]
    error: Optional[str]
    
    # Timestamps
    created_at: str
    updated_at: str
    
    # Human feedback tracking
    awaiting_human_feedback: bool
    feedback_token: Optional[str]

class RequestStatus(TypedDict):
    """Status of a cooking request"""
    request_id: str
    stage: str
    status: Literal["pending", "processing", "waiting_user", "completed", "failed"]
    created_at: str
    updated_at: str
