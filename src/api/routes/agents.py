"""
API routes for intelligent agents.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from src.core.security import get_current_user
from src.models.user import User
from src.agents.coordinator import CoordinatorAgent

# Initialize router
router = APIRouter(prefix="/agents", tags=["Agents"])

# Global coordinator agent instance (singleton pattern)
_coordinator_agent: Optional[CoordinatorAgent] = None


def get_coordinator_agent() -> CoordinatorAgent:
    """
    Get or create the coordinator agent instance.

    Returns:
        CoordinatorAgent: Singleton coordinator agent
    """
    global _coordinator_agent
    if _coordinator_agent is None:
        _coordinator_agent = CoordinatorAgent()
    return _coordinator_agent


# =====================================================
# REQUEST/RESPONSE MODELS
# =====================================================

class NaturalLanguageRequest(BaseModel):
    """Request model for natural language interaction."""
    message: str = Field(..., description="Natural language message to the coordinator", min_length=1)
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional context information")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "I need to create a booking for tomorrow",
                "context": {"customer_id": 1}
            }
        }


class StructuredTaskRequest(BaseModel):
    """Request model for structured task delegation."""
    task_type: str = Field(..., description="Type of task to delegate")
    data: Dict[str, Any] = Field(default_factory=dict, description="Task data")

    class Config:
        json_schema_extra = {
            "example": {
                "task_type": "communications",
                "data": {"action": "send_email", "recipient": "customer@example.com"}
            }
        }


class ChatRequest(BaseModel):
    """Unified chat request that accepts both formats."""
    message: Optional[str] = Field(default=None, description="Natural language message")
    task_type: Optional[str] = Field(default=None, description="Structured task type")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Task data or context")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "message": "Help me create a new booking",
                    "data": {"customer_id": 1}
                },
                {
                    "task_type": "communications",
                    "data": {"action": "send_sms"}
                }
            ]
        }


class AgentResponse(BaseModel):
    """Standard agent response model."""
    success: bool = Field(..., description="Whether the request was successful")
    agent: str = Field(..., description="Agent name that processed the request")
    result: Dict[str, Any] = Field(..., description="Processing result")
    timestamp: str = Field(..., description="Response timestamp")


# =====================================================
# AGENT STATUS ENDPOINTS
# =====================================================

@router.get("/coordinator/status")
def get_coordinator_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get the current status of the coordinator agent.

    Returns:
        Dict: Agent status including AI capabilities, registered agents, and conversation count
    """
    coordinator = get_coordinator_agent()
    return coordinator.get_status()


@router.get("/coordinator/agents")
def list_registered_agents(
    current_user: User = Depends(get_current_user)
):
    """
    List all registered specialized agents.

    Returns:
        Dict: Mapping of agent types to agent names
    """
    coordinator = get_coordinator_agent()
    return {
        "registered_agents": coordinator.get_registered_agents(),
        "count": len(coordinator.specialized_agents)
    }


# =====================================================
# CONVERSATION MANAGEMENT
# =====================================================

@router.get("/coordinator/history")
def get_conversation_history(
    limit: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Get conversation history with the coordinator.

    Args:
        limit: Optional limit on number of messages

    Returns:
        Dict: Conversation history
    """
    coordinator = get_coordinator_agent()
    history = coordinator.get_conversation_history(limit=limit)

    return {
        "conversation_history": history,
        "message_count": len(history),
        "total_messages": len(coordinator.conversation_history)
    }


@router.post("/coordinator/clear-history", status_code=status.HTTP_204_NO_CONTENT)
def clear_conversation_history(
    current_user: User = Depends(get_current_user)
):
    """
    Clear the conversation history.

    Returns:
        None: 204 No Content on success
    """
    coordinator = get_coordinator_agent()
    coordinator.clear_history()
    return None


# =====================================================
# AGENT EXECUTION ENDPOINTS
# =====================================================

@router.post("/coordinator/chat", response_model=AgentResponse)
async def chat_with_coordinator(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Chat with the coordinator agent using natural language or structured tasks.

    This is the main endpoint for interacting with the AI coordinator.
    Supports both natural language messages and structured task delegation.

    Args:
        request: Chat request with message or task_type
        current_user: Authenticated user

    Returns:
        AgentResponse: Agent's response with routing decisions

    Examples:
        Natural language:
        ```json
        {
            "message": "I need help creating a booking for tomorrow",
            "data": {"customer_id": 1}
        }
        ```

        Structured task:
        ```json
        {
            "task_type": "communications",
            "data": {"action": "send_email", "to": "customer@example.com"}
        }
        ```
    """
    coordinator = get_coordinator_agent()

    # Build input data
    input_data = {}

    if request.message:
        input_data["message"] = request.message
        if request.data:
            input_data["context"] = request.data
    elif request.task_type:
        input_data["task_type"] = request.task_type
        input_data["data"] = request.data or {}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request must contain either 'message' or 'task_type'"
        )

    # Add user context
    if "context" not in input_data:
        input_data["context"] = {}
    input_data["context"]["user_id"] = current_user.id
    input_data["context"]["user_name"] = current_user.full_name or current_user.username

    try:
        # Execute coordinator
        result = await coordinator.execute(input_data)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Coordinator execution failed: {str(e)}"
        )


@router.post("/coordinator/execute", response_model=AgentResponse)
async def execute_coordinator(
    request: NaturalLanguageRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Execute the coordinator with a natural language request.

    This is a convenience endpoint for natural language only.
    For full features, use /coordinator/chat instead.

    Args:
        request: Natural language request
        current_user: Authenticated user

    Returns:
        AgentResponse: AI-generated response
    """
    coordinator = get_coordinator_agent()

    input_data = {
        "message": request.message,
        "context": request.context or {}
    }

    # Add user context
    input_data["context"]["user_id"] = current_user.id
    input_data["context"]["user_name"] = current_user.full_name or current_user.username

    try:
        result = await coordinator.execute(input_data)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Coordinator execution failed: {str(e)}"
        )


@router.post("/coordinator/delegate", response_model=AgentResponse)
async def delegate_task(
    request: StructuredTaskRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Delegate a structured task to the coordinator.

    This endpoint is for structured task delegation only.
    For natural language, use /coordinator/execute or /coordinator/chat.

    Args:
        request: Structured task request
        current_user: Authenticated user

    Returns:
        AgentResponse: Delegation result
    """
    coordinator = get_coordinator_agent()

    input_data = {
        "task_type": request.task_type,
        "data": request.data
    }

    # Add user context
    input_data["data"]["user_id"] = current_user.id
    input_data["data"]["user_name"] = current_user.full_name or current_user.username

    try:
        result = await coordinator.execute(input_data)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Task delegation failed: {str(e)}"
        )


# =====================================================
# AGENT TESTING ENDPOINT
# =====================================================

@router.get("/coordinator/test")
async def test_coordinator(
    message: str = "Hello, can you help me?",
    current_user: User = Depends(get_current_user)
):
    """
    Test the coordinator agent with a simple message.

    Args:
        message: Test message (default: "Hello, can you help me?")
        current_user: Authenticated user

    Returns:
        Dict: Test result
    """
    coordinator = get_coordinator_agent()

    input_data = {
        "message": message,
        "context": {
            "user_id": current_user.id,
            "user_name": current_user.full_name or current_user.username,
            "test_mode": True
        }
    }

    try:
        result = await coordinator.execute(input_data)

        return {
            "test": "success",
            "message_sent": message,
            "coordinator_status": coordinator.get_status(),
            "response": result
        }

    except Exception as e:
        return {
            "test": "failed",
            "error": str(e),
            "coordinator_status": coordinator.get_status()
        }
