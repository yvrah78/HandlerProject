"""
API routes for intelligent agents.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from src.core.security import get_current_user
from src.models.user import User
from src.agents.coordinator import CoordinatorAgent
from src.agents.communications import CommunicationsAgent
from src.agents.financial import FinancialAgent

# Initialize router
router = APIRouter(prefix="/agents", tags=["Agents"])

# Global agent instances (singleton pattern)
_coordinator_agent: Optional[CoordinatorAgent] = None
_communications_agent: Optional[CommunicationsAgent] = None
_financial_agent: Optional[FinancialAgent] = None


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


# =====================================================
# COMMUNICATIONS AGENT ENDPOINTS
# =====================================================

def get_communications_agent() -> CommunicationsAgent:
    """
    Get or create the communications agent instance.

    Returns:
        CommunicationsAgent: Singleton communications agent
    """
    global _communications_agent
    if _communications_agent is None:
        _communications_agent = CommunicationsAgent()
    return _communications_agent


class CommunicationRequest(BaseModel):
    """Request model for communication."""
    communication_type: str = Field(..., description="Type: sms, email, call, notification")
    to: str = Field(..., description="Recipient (phone number or email)")
    message: str = Field(..., description="Message content")
    subject: Optional[str] = Field(default=None, description="Email subject (email only)")
    from_email: Optional[str] = Field(default=None, description="Sender email (email only)")
    channels: Optional[List[str]] = Field(default=None, description="Channels for notification type")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "communication_type": "sms",
                    "to": "+1234567890",
                    "message": "Your booking has been confirmed!"
                },
                {
                    "communication_type": "email",
                    "to": "customer@example.com",
                    "subject": "Booking Confirmation",
                    "message": "Your booking has been confirmed. Thank you!"
                },
                {
                    "communication_type": "notification",
                    "to": "+1234567890",
                    "message": "Important update",
                    "channels": ["sms", "email"]
                }
            ]
        }


@router.get("/communications/status")
def get_communications_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get the current status of the communications agent.

    Returns:
        Dict: Agent status including enabled channels and history count
    """
    comm_agent = get_communications_agent()
    return comm_agent.get_status()


@router.post("/communications/send")
async def send_communication(
    request: CommunicationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Send a communication via SMS, email, or phone call.

    Supports:
    - SMS via Twilio
    - Email via SendGrid
    - Phone calls via Twilio
    - Multi-channel notifications

    Args:
        request: Communication request
        current_user: Authenticated user

    Returns:
        Dict: Communication result

    Examples:
        SMS:
        ```json
        {
            "communication_type": "sms",
            "to": "+1234567890",
            "message": "Your booking #12345 is confirmed!"
        }
        ```

        Email:
        ```json
        {
            "communication_type": "email",
            "to": "customer@example.com",
            "subject": "Booking Confirmation",
            "message": "Dear customer, your booking has been confirmed."
        }
        ```
    """
    comm_agent = get_communications_agent()

    input_data = {
        "communication_type": request.communication_type,
        "to": request.to,
        "message": request.message
    }

    if request.subject:
        input_data["subject"] = request.subject
    if request.from_email:
        input_data["from_email"] = request.from_email
    if request.channels:
        input_data["channels"] = request.channels

    # Add user context
    input_data["user_id"] = current_user.id
    input_data["user_name"] = current_user.full_name or current_user.username

    try:
        result = await comm_agent.execute(input_data)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Communication failed: {str(e)}"
        )


@router.post("/communications/send-sms")
async def send_sms(
    to: str,
    message: str,
    current_user: User = Depends(get_current_user)
):
    """
    Convenience endpoint to send SMS.

    Args:
        to: Recipient phone number (e.g., +1234567890)
        message: SMS message content
        current_user: Authenticated user

    Returns:
        Dict: SMS delivery result
    """
    comm_agent = get_communications_agent()

    input_data = {
        "communication_type": "sms",
        "to": to,
        "message": message,
        "user_id": current_user.id
    }

    try:
        result = await comm_agent.execute(input_data)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SMS failed: {str(e)}"
        )


@router.post("/communications/send-email")
async def send_email(
    to: str,
    subject: str,
    message: str,
    from_email: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Convenience endpoint to send email.

    Args:
        to: Recipient email address
        subject: Email subject
        message: Email message content
        from_email: Optional sender email
        current_user: Authenticated user

    Returns:
        Dict: Email delivery result
    """
    comm_agent = get_communications_agent()

    input_data = {
        "communication_type": "email",
        "to": to,
        "subject": subject,
        "message": message,
        "user_id": current_user.id
    }

    if from_email:
        input_data["from_email"] = from_email

    try:
        result = await comm_agent.execute(input_data)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email failed: {str(e)}"
        )


@router.get("/communications/history")
def get_communications_history(
    limit: Optional[int] = 50,
    current_user: User = Depends(get_current_user)
):
    """
    Get communication history.

    Args:
        limit: Maximum number of communications to return
        current_user: Authenticated user

    Returns:
        Dict: Communication history
    """
    comm_agent = get_communications_agent()
    history = comm_agent.get_communication_history(limit=limit)

    return {
        "history": history,
        "total": len(comm_agent.communication_history),
        "showing": len(history)
    }


@router.post("/communications/clear-history", status_code=status.HTTP_204_NO_CONTENT)
def clear_communications_history(
    current_user: User = Depends(get_current_user)
):
    """
    Clear the communication history.

    Returns:
        None: 204 No Content on success
    """
    comm_agent = get_communications_agent()
    comm_agent.clear_history()
    return None


@router.get("/communications/test")
async def test_communications(
    channel: str = "sms",
    recipient: str = "+1234567890",
    current_user: User = Depends(get_current_user)
):
    """
    Test the communications agent.

    Args:
        channel: Channel to test (sms, email, call)
        recipient: Test recipient
        current_user: Authenticated user

    Returns:
        Dict: Test result
    """
    comm_agent = get_communications_agent()

    test_messages = {
        "sms": "This is a test SMS from Project Handler",
        "email": "This is a test email from Project Handler",
        "call": "Hello, this is a test call from Project Handler"
    }

    input_data = {
        "communication_type": channel,
        "to": recipient,
        "message": test_messages.get(channel, "Test message"),
        "subject": "Test Email from Project Handler" if channel == "email" else None
    }

    try:
        result = await comm_agent.execute(input_data)

        return {
            "test": "success",
            "channel": channel,
            "recipient": recipient,
            "agent_status": comm_agent.get_status(),
            "result": result
        }

    except Exception as e:
        return {
            "test": "failed",
            "channel": channel,
            "error": str(e),
            "agent_status": comm_agent.get_status()
        }


# =====================================================
# FINANCIAL AGENT ENDPOINTS
# =====================================================

def get_financial_agent() -> FinancialAgent:
    """
    Get or create the financial agent instance.

    Returns:
        FinancialAgent: Singleton financial agent
    """
    global _financial_agent
    if _financial_agent is None:
        _financial_agent = FinancialAgent()
    return _financial_agent


class FinancialOperationRequest(BaseModel):
    """Request model for financial operations."""
    operation_type: str = Field(..., description="Type: payment, invoice, refund, quotation")
    amount: Optional[float] = Field(default=None, description="Amount (required for payment/invoice)")
    currency: Optional[str] = Field(default="usd", description="Currency code")
    description: Optional[str] = Field(default=None, description="Operation description")
    customer_email: Optional[str] = Field(default=None, description="Customer email")
    customer_name: Optional[str] = Field(default=None, description="Customer name")
    payment_intent_id: Optional[str] = Field(default=None, description="Payment intent ID (for refunds)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "operation_type": "payment",
                    "amount": 150.00,
                    "currency": "usd",
                    "description": "Transportation service payment",
                    "customer_email": "customer@example.com"
                },
                {
                    "operation_type": "refund",
                    "payment_intent_id": "pi_1234567890",
                    "amount": 75.00
                }
            ]
        }


class PaymentRequest(BaseModel):
    """Request model for payment creation."""
    amount: float = Field(..., description="Payment amount", gt=0)
    currency: str = Field(default="usd", description="Currency code")
    description: Optional[str] = Field(default="Payment for transportation services", description="Payment description")
    customer_email: Optional[str] = Field(default=None, description="Customer email for receipt")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "amount": 150.00,
                "currency": "usd",
                "description": "Transportation service - Booking #12345",
                "customer_email": "customer@example.com"
            }
        }


class InvoiceRequest(BaseModel):
    """Request model for invoice creation."""
    customer_email: str = Field(..., description="Customer email")
    customer_name: str = Field(..., description="Customer name")
    amount: float = Field(..., description="Invoice amount", gt=0)
    currency: str = Field(default="usd", description="Currency code")
    description: Optional[str] = Field(default="Transportation services", description="Invoice description")
    items: Optional[List[Dict[str, Any]]] = Field(default=None, description="Invoice line items")
    due_date: Optional[str] = Field(default=None, description="Due date (ISO format or Unix timestamp)")

    class Config:
        json_schema_extra = {
            "example": {
                "customer_email": "customer@example.com",
                "customer_name": "John Doe",
                "amount": 250.00,
                "currency": "usd",
                "description": "Transportation services - January 2024",
                "items": [
                    {"description": "Standard delivery", "amount": 150.00},
                    {"description": "Express surcharge", "amount": 100.00}
                ]
            }
        }


class RefundRequest(BaseModel):
    """Request model for refund processing."""
    payment_intent_id: str = Field(..., description="Payment intent ID to refund")
    amount: Optional[float] = Field(default=None, description="Partial refund amount (omit for full refund)")
    reason: Optional[str] = Field(default="requested_by_customer", description="Refund reason")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "payment_intent_id": "pi_1234567890",
                "amount": 75.00,
                "reason": "service_not_delivered"
            }
        }


class QuotationRequest(BaseModel):
    """Request model for price quotation."""
    service_type: str = Field(default="standard_delivery", description="Service type")
    distance_miles: float = Field(default=0, description="Distance in miles", ge=0)
    estimated_hours: float = Field(default=0, description="Estimated hours", ge=0)
    urgency: str = Field(default="normal", description="Urgency level: normal, urgent, emergency")
    special_requirements: Optional[List[str]] = Field(default=None, description="Special requirements")

    class Config:
        json_schema_extra = {
            "example": {
                "service_type": "express_delivery",
                "distance_miles": 45.5,
                "estimated_hours": 2.5,
                "urgency": "urgent",
                "special_requirements": ["refrigerated", "fragile"]
            }
        }


@router.get("/financial/status")
def get_financial_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get the current status of the financial agent.

    Returns:
        Dict: Agent status including Stripe status, operation count, and pricing info
    """
    financial_agent = get_financial_agent()
    return financial_agent.get_status()


@router.post("/financial/process")
async def process_financial_operation(
    request: FinancialOperationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Process a generic financial operation.

    Supports: payment, invoice, refund, quotation

    Args:
        request: Financial operation request
        current_user: Authenticated user

    Returns:
        Dict: Operation result
    """
    financial_agent = get_financial_agent()

    input_data = {
        "operation_type": request.operation_type,
        "user_id": current_user.id
    }

    # Add optional fields if provided
    if request.amount is not None:
        input_data["amount"] = request.amount
    if request.currency:
        input_data["currency"] = request.currency
    if request.description:
        input_data["description"] = request.description
    if request.customer_email:
        input_data["customer_email"] = request.customer_email
    if request.customer_name:
        input_data["customer_name"] = request.customer_name
    if request.payment_intent_id:
        input_data["payment_intent_id"] = request.payment_intent_id
    if request.metadata:
        input_data["metadata"] = request.metadata

    try:
        result = await financial_agent.execute(input_data)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Financial operation failed: {str(e)}"
        )


@router.post("/financial/create-payment")
async def create_payment(
    request: PaymentRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a payment via Stripe.

    Args:
        request: Payment request
        current_user: Authenticated user

    Returns:
        Dict: Payment result with payment_intent_id and client_secret

    Example:
        ```json
        {
            "amount": 150.00,
            "currency": "usd",
            "description": "Transportation service - Booking #12345",
            "customer_email": "customer@example.com"
        }
        ```
    """
    financial_agent = get_financial_agent()

    input_data = {
        "operation_type": "payment",
        "amount": request.amount,
        "currency": request.currency,
        "description": request.description,
        "customer_email": request.customer_email,
        "metadata": request.metadata or {},
        "user_id": current_user.id
    }

    try:
        result = await financial_agent.execute(input_data)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment creation failed: {str(e)}"
        )


@router.post("/financial/create-invoice")
async def create_invoice(
    request: InvoiceRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create an invoice.

    Args:
        request: Invoice request
        current_user: Authenticated user

    Returns:
        Dict: Invoice result with invoice_number and details

    Example:
        ```json
        {
            "customer_email": "customer@example.com",
            "customer_name": "John Doe",
            "amount": 250.00,
            "description": "Transportation services - January 2024"
        }
        ```
    """
    financial_agent = get_financial_agent()

    input_data = {
        "operation_type": "invoice",
        "customer_email": request.customer_email,
        "customer_name": request.customer_name,
        "amount": request.amount,
        "currency": request.currency,
        "description": request.description,
        "items": request.items or [],
        "due_date": request.due_date,
        "user_id": current_user.id
    }

    try:
        result = await financial_agent.execute(input_data)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invoice creation failed: {str(e)}"
        )


@router.post("/financial/process-refund")
async def process_refund(
    request: RefundRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Process a refund for a previous payment.

    Args:
        request: Refund request
        current_user: Authenticated user

    Returns:
        Dict: Refund result with refund_id

    Example:
        ```json
        {
            "payment_intent_id": "pi_1234567890",
            "amount": 75.00,
            "reason": "service_not_delivered"
        }
        ```
    """
    financial_agent = get_financial_agent()

    input_data = {
        "operation_type": "refund",
        "payment_intent_id": request.payment_intent_id,
        "reason": request.reason,
        "metadata": request.metadata or {},
        "user_id": current_user.id
    }

    if request.amount:
        input_data["amount"] = request.amount

    try:
        result = await financial_agent.execute(input_data)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Refund processing failed: {str(e)}"
        )


@router.post("/financial/generate-quote")
async def generate_quote(
    request: QuotationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate an intelligent price quotation.

    Uses distance, time, urgency, and special requirements to calculate pricing.

    Args:
        request: Quotation request
        current_user: Authenticated user

    Returns:
        Dict: Detailed quotation with pricing breakdown

    Example:
        ```json
        {
            "service_type": "express_delivery",
            "distance_miles": 45.5,
            "estimated_hours": 2.5,
            "urgency": "urgent",
            "special_requirements": ["refrigerated", "fragile"]
        }
        ```
    """
    financial_agent = get_financial_agent()

    input_data = {
        "operation_type": "quotation",
        "service_type": request.service_type,
        "distance_miles": request.distance_miles,
        "estimated_hours": request.estimated_hours,
        "urgency": request.urgency,
        "special_requirements": request.special_requirements or [],
        "user_id": current_user.id
    }

    try:
        result = await financial_agent.execute(input_data)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quote generation failed: {str(e)}"
        )


@router.get("/financial/history")
def get_financial_history(
    limit: Optional[int] = 50,
    current_user: User = Depends(get_current_user)
):
    """
    Get financial operation history.

    Args:
        limit: Maximum number of operations to return
        current_user: Authenticated user

    Returns:
        Dict: Financial operation history
    """
    financial_agent = get_financial_agent()
    history = financial_agent.get_financial_history(limit=limit)

    return {
        "history": history,
        "total": len(financial_agent.financial_history),
        "showing": len(history)
    }


@router.get("/financial/pricing")
def get_pricing_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current pricing configuration.

    Returns:
        Dict: Pricing information including base rates and multipliers
    """
    financial_agent = get_financial_agent()
    return financial_agent.get_pricing_info()


@router.post("/financial/clear-history", status_code=status.HTTP_204_NO_CONTENT)
def clear_financial_history(
    current_user: User = Depends(get_current_user)
):
    """
    Clear the financial operation history.

    Returns:
        None: 204 No Content on success
    """
    financial_agent = get_financial_agent()
    financial_agent.clear_history()
    return None


@router.get("/financial/test")
async def test_financial(
    operation: str = "quotation",
    current_user: User = Depends(get_current_user)
):
    """
    Test the financial agent.

    Args:
        operation: Operation to test (payment, invoice, refund, quotation)
        current_user: Authenticated user

    Returns:
        Dict: Test result
    """
    financial_agent = get_financial_agent()

    test_data = {
        "payment": {
            "operation_type": "payment",
            "amount": 99.99,
            "currency": "usd",
            "description": "Test payment",
            "customer_email": "test@example.com"
        },
        "invoice": {
            "operation_type": "invoice",
            "customer_email": "test@example.com",
            "customer_name": "Test Customer",
            "amount": 199.99,
            "description": "Test invoice"
        },
        "refund": {
            "operation_type": "refund",
            "payment_intent_id": "pi_test_123456",
            "amount": 50.00,
            "reason": "test_refund"
        },
        "quotation": {
            "operation_type": "quotation",
            "service_type": "express_delivery",
            "distance_miles": 25.0,
            "estimated_hours": 1.5,
            "urgency": "normal"
        }
    }

    input_data = test_data.get(operation, test_data["quotation"])

    try:
        result = await financial_agent.execute(input_data)

        return {
            "test": "success",
            "operation": operation,
            "agent_status": financial_agent.get_status(),
            "result": result
        }

    except Exception as e:
        return {
            "test": "failed",
            "operation": operation,
            "error": str(e),
            "agent_status": financial_agent.get_status()
        }
