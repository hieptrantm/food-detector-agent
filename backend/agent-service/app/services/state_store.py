import json
import os
from typing import Optional
from datetime import datetime
import logging

from app.models.state import AgentState, RequestStatus
from config import PENDING_REQUESTS_DIR

logger = logging.getLogger(__name__)

class StateStore:
    """Simple file-based store for agent states"""
    
    def __init__(self, storage_dir: str = PENDING_REQUESTS_DIR):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
    
    def _get_file_path(self, request_id: str) -> str:
        """Get file path for request state"""
        return os.path.join(self.storage_dir, f"{request_id}.json")
    
    def save_state(self, state: AgentState) -> bool:
        """Save agent state to file"""
        try:
            file_path = self._get_file_path(state["request_id"])
            state["updated_at"] = datetime.utcnow().isoformat()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved state for request {state['request_id']}")
            return True
        except Exception as e:
            logger.error(f"Error saving state: {e}")
            return False
    
    def load_state(self, request_id: str) -> Optional[AgentState]:
        """Load agent state from file"""
        try:
            file_path = self._get_file_path(request_id)
            
            if not os.path.exists(file_path):
                logger.warning(f"State file not found for request {request_id}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            logger.info(f"Loaded state for request {request_id}")
            return state
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            return None
    
    def delete_state(self, request_id: str) -> bool:
        """Delete state file"""
        try:
            file_path = self._get_file_path(request_id)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted state for request {request_id}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error deleting state: {e}")
            return False
    
    def get_request_status(self, request_id: str) -> Optional[RequestStatus]:
        """Get status of a request"""
        state = self.load_state(request_id)
        
        if not state:
            return None
        
        # Map stage to status
        status_map = {
            "detecting": "processing",
            "suggesting": "processing",
            "waiting_selection": "waiting_user",
            "generating_recipe": "processing",
            "completed": "completed",
            "error": "failed"
        }
        
        return {
            "request_id": state["request_id"],
            "stage": state["stage"],
            "status": status_map.get(state["stage"], "pending"),
            "created_at": state["created_at"],
            "updated_at": state["updated_at"]
        }
    
    def list_pending_requests(self) -> list:
        """List all pending requests"""
        try:
            files = os.listdir(self.storage_dir)
            request_ids = [f.replace('.json', '') for f in files if f.endswith('.json')]
            return request_ids
        except Exception as e:
            logger.error(f"Error listing requests: {e}")
            return []

# Global state store instance
state_store = StateStore()
