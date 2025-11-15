"""
Task Analyzer for intelligent task analysis and classification.

Analyzes incoming tasks and determines:
- Task type and category
- Required agent capabilities
- Task complexity and priority
- Estimated processing time
"""
from typing import Dict, Any, List, Set, Optional
from enum import Enum
from dataclasses import dataclass
from src.core.logging import get_logger


class TaskType(Enum):
    """Types of tasks in the system."""

    # Communication tasks
    SEND_SMS = "send_sms"
    SEND_EMAIL = "send_email"
    MAKE_CALL = "make_call"
    SEND_NOTIFICATION = "send_notification"

    # Financial tasks
    CREATE_QUOTE = "create_quote"
    CREATE_INVOICE = "create_invoice"
    PROCESS_PAYMENT = "process_payment"
    REFUND_PAYMENT = "refund_payment"

    # Operations tasks
    CREATE_BOOKING = "create_booking"
    ASSIGN_VEHICLE = "assign_vehicle"
    ASSIGN_DRIVER = "assign_driver"
    CALCULATE_ROUTE = "calculate_route"
    OPTIMIZE_ROUTE = "optimize_route"

    # Analytics tasks
    GENERATE_REPORT = "generate_report"
    CALCULATE_METRICS = "calculate_metrics"
    ANALYZE_TRENDS = "analyze_trends"
    PREDICT = "predict"

    # Workflow tasks
    BOOKING_WORKFLOW = "booking_workflow"
    PAYMENT_WORKFLOW = "payment_workflow"
    COMMUNICATION_WORKFLOW = "communication_workflow"

    # General tasks
    QUERY = "query"
    UPDATE = "update"
    DELETE = "delete"
    UNKNOWN = "unknown"


class TaskComplexity(Enum):
    """Task complexity levels."""

    SIMPLE = 1      # Single operation, < 1s
    MODERATE = 2    # Multiple operations, < 5s
    COMPLEX = 3     # Complex logic, < 30s
    VERY_COMPLEX = 4  # Multi-step workflow, > 30s


@dataclass
class TaskAnalysis:
    """
    Result of task analysis.

    Attributes:
        task_type: Identified task type
        required_agents: List of agent names required
        complexity: Task complexity level
        estimated_duration: Estimated duration in seconds
        priority_score: Priority score (0-100)
        requires_coordination: Whether task needs multi-agent coordination
        dependencies: List of dependent tasks
        metadata: Additional analysis metadata
    """

    task_type: TaskType
    required_agents: List[str]
    complexity: TaskComplexity
    estimated_duration: float
    priority_score: int
    requires_coordination: bool = False
    dependencies: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.metadata is None:
            self.metadata = {}


class TaskAnalyzer:
    """
    Analyzes tasks to determine routing and resource requirements.

    Uses rule-based analysis and pattern matching to classify tasks
    and determine optimal agent assignment.
    """

    def __init__(self):
        """Initialize task analyzer."""
        self.logger = get_logger("task_analyzer")

        # Mapping of task types to required agents
        self._task_to_agents = {
            # Communication tasks
            TaskType.SEND_SMS: ["communications"],
            TaskType.SEND_EMAIL: ["communications"],
            TaskType.MAKE_CALL: ["communications"],
            TaskType.SEND_NOTIFICATION: ["communications"],

            # Financial tasks
            TaskType.CREATE_QUOTE: ["financial"],
            TaskType.CREATE_INVOICE: ["financial"],
            TaskType.PROCESS_PAYMENT: ["financial"],
            TaskType.REFUND_PAYMENT: ["financial"],

            # Operations tasks
            TaskType.CREATE_BOOKING: ["operations"],
            TaskType.ASSIGN_VEHICLE: ["operations"],
            TaskType.ASSIGN_DRIVER: ["operations"],
            TaskType.CALCULATE_ROUTE: ["operations"],
            TaskType.OPTIMIZE_ROUTE: ["operations"],

            # Analytics tasks
            TaskType.GENERATE_REPORT: ["analytics"],
            TaskType.CALCULATE_METRICS: ["analytics"],
            TaskType.ANALYZE_TRENDS: ["analytics"],
            TaskType.PREDICT: ["analytics"],

            # Workflow tasks (require multiple agents)
            TaskType.BOOKING_WORKFLOW: ["operations", "communications", "financial"],
            TaskType.PAYMENT_WORKFLOW: ["financial", "communications"],
            TaskType.COMMUNICATION_WORKFLOW: ["communications"],
        }

        # Complexity mappings
        self._task_complexity = {
            TaskType.SEND_SMS: TaskComplexity.SIMPLE,
            TaskType.SEND_EMAIL: TaskComplexity.SIMPLE,
            TaskType.MAKE_CALL: TaskComplexity.SIMPLE,
            TaskType.CREATE_QUOTE: TaskComplexity.MODERATE,
            TaskType.CREATE_INVOICE: TaskComplexity.MODERATE,
            TaskType.PROCESS_PAYMENT: TaskComplexity.MODERATE,
            TaskType.CALCULATE_ROUTE: TaskComplexity.MODERATE,
            TaskType.ASSIGN_VEHICLE: TaskComplexity.MODERATE,
            TaskType.GENERATE_REPORT: TaskComplexity.COMPLEX,
            TaskType.ANALYZE_TRENDS: TaskComplexity.COMPLEX,
            TaskType.BOOKING_WORKFLOW: TaskComplexity.VERY_COMPLEX,
            TaskType.PAYMENT_WORKFLOW: TaskComplexity.COMPLEX,
            TaskType.COMMUNICATION_WORKFLOW: TaskComplexity.MODERATE,
        }

        # Estimated durations (in seconds)
        self._estimated_durations = {
            TaskComplexity.SIMPLE: 0.5,
            TaskComplexity.MODERATE: 3.0,
            TaskComplexity.COMPLEX: 15.0,
            TaskComplexity.VERY_COMPLEX: 45.0,
        }

        self.logger.info("Task analyzer initialized")

    def analyze(self, task_data: Dict[str, Any]) -> TaskAnalysis:
        """
        Analyze a task and determine routing requirements.

        Args:
            task_data: Task data including type, parameters, etc.

        Returns:
            TaskAnalysis with routing and resource information
        """
        # Identify task type
        task_type = self._identify_task_type(task_data)

        # Determine required agents
        required_agents = self._task_to_agents.get(
            task_type,
            ["coordinator"]  # Default to coordinator if unknown
        )

        # Determine complexity
        complexity = self._task_complexity.get(
            task_type,
            TaskComplexity.MODERATE
        )

        # Estimate duration
        estimated_duration = self._estimated_durations.get(
            complexity,
            5.0
        )

        # Calculate priority score
        priority_score = self._calculate_priority(task_data, task_type)

        # Check if coordination is needed
        requires_coordination = len(required_agents) > 1

        # Extract dependencies
        dependencies = task_data.get("dependencies", [])

        # Build metadata
        metadata = {
            "original_type": task_data.get("type", "unknown"),
            "has_deadline": "deadline" in task_data,
            "user_priority": task_data.get("priority", "normal"),
        }

        analysis = TaskAnalysis(
            task_type=task_type,
            required_agents=required_agents,
            complexity=complexity,
            estimated_duration=estimated_duration,
            priority_score=priority_score,
            requires_coordination=requires_coordination,
            dependencies=dependencies,
            metadata=metadata
        )

        self.logger.debug(
            f"Analyzed task: {task_type.value}, "
            f"Agents: {required_agents}, "
            f"Complexity: {complexity.value}, "
            f"Priority: {priority_score}"
        )

        return analysis

    def _identify_task_type(self, task_data: Dict[str, Any]) -> TaskType:
        """
        Identify the type of task from task data.

        Args:
            task_data: Task data

        Returns:
            Identified task type
        """
        task_type_str = task_data.get("type", "").lower()

        # Direct mapping
        for task_type in TaskType:
            if task_type.value == task_type_str:
                return task_type

        # Pattern matching
        if "sms" in task_type_str or "text" in task_type_str:
            return TaskType.SEND_SMS
        elif "email" in task_type_str or "mail" in task_type_str:
            return TaskType.SEND_EMAIL
        elif "call" in task_type_str or "phone" in task_type_str:
            return TaskType.MAKE_CALL
        elif "quote" in task_type_str:
            return TaskType.CREATE_QUOTE
        elif "invoice" in task_type_str:
            return TaskType.CREATE_INVOICE
        elif "payment" in task_type_str or "pay" in task_type_str:
            return TaskType.PROCESS_PAYMENT
        elif "booking" in task_type_str or "reservation" in task_type_str:
            if "workflow" in task_type_str:
                return TaskType.BOOKING_WORKFLOW
            return TaskType.CREATE_BOOKING
        elif "route" in task_type_str:
            if "optimize" in task_type_str:
                return TaskType.OPTIMIZE_ROUTE
            return TaskType.CALCULATE_ROUTE
        elif "report" in task_type_str:
            return TaskType.GENERATE_REPORT
        elif "metric" in task_type_str:
            return TaskType.CALCULATE_METRICS
        elif "analyze" in task_type_str or "analysis" in task_type_str:
            return TaskType.ANALYZE_TRENDS
        elif "predict" in task_type_str or "forecast" in task_type_str:
            return TaskType.PREDICT

        return TaskType.UNKNOWN

    def _calculate_priority(
        self,
        task_data: Dict[str, Any],
        task_type: TaskType
    ) -> int:
        """
        Calculate priority score for a task.

        Args:
            task_data: Task data
            task_type: Identified task type

        Returns:
            Priority score (0-100)
        """
        score = 50  # Base priority

        # User-specified priority
        user_priority = task_data.get("priority", "normal").lower()
        priority_adjustments = {
            "low": -20,
            "normal": 0,
            "high": 20,
            "critical": 40,
            "urgent": 40
        }
        score += priority_adjustments.get(user_priority, 0)

        # Deadline urgency
        if "deadline" in task_data:
            score += 15

        # Task type priority
        if task_type in [TaskType.PROCESS_PAYMENT, TaskType.REFUND_PAYMENT]:
            score += 10  # Financial tasks are important

        if task_type.value.endswith("_workflow"):
            score += 5  # Workflows have slightly higher priority

        # Clamp to 0-100
        return max(0, min(100, score))

    def get_capabilities_for_task(self, task_type: TaskType) -> Set[str]:
        """
        Get required capabilities for a task type.

        Args:
            task_type: Task type

        Returns:
            Set of required capabilities
        """
        capabilities = set()

        # Map task types to capabilities
        if task_type in [TaskType.SEND_SMS, TaskType.SEND_EMAIL, TaskType.MAKE_CALL]:
            capabilities.add("communication")

        if task_type in [TaskType.CREATE_QUOTE, TaskType.CREATE_INVOICE, TaskType.PROCESS_PAYMENT]:
            capabilities.add("financial")

        if task_type in [TaskType.CALCULATE_ROUTE, TaskType.OPTIMIZE_ROUTE]:
            capabilities.add("routing")

        if task_type in [TaskType.ASSIGN_VEHICLE, TaskType.ASSIGN_DRIVER]:
            capabilities.add("fleet_management")

        if task_type in [TaskType.GENERATE_REPORT, TaskType.CALCULATE_METRICS]:
            capabilities.add("analytics")

        return capabilities
