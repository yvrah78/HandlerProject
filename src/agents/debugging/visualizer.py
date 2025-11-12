"""
Visualization tools for chain execution flow and metrics.
Provides ASCII diagrams and metrics visualization.
"""
from typing import Dict, Any, List, Optional
from src.core.logging import get_logger

logger = get_logger(__name__)


class ChainVisualizer:
    """Visualizes chain execution structure and flow."""

    @staticmethod
    def visualize_sequential_chain(chain_names: List[str]) -> str:
        """Visualize sequential chain execution.

        Args:
            chain_names: List of chain names in sequence

        Returns:
            str: ASCII visualization
        """
        if not chain_names:
            return "No chains"

        lines = []
        for i, chain in enumerate(chain_names):
            lines.append(f"┌─ {chain} ─┐")
            if i < len(chain_names) - 1:
                lines.append("│")
                lines.append("↓")
                lines.append("│")

        return "\n".join(lines)

    @staticmethod
    def visualize_router_chain(
        router_name: str,
        routes: Dict[str, str],
        default_route: Optional[str] = None,
    ) -> str:
        """Visualize router chain.

        Args:
            router_name: Router name
            routes: Dict of route_key -> chain_name
            default_route: Default route name

        Returns:
            str: ASCII visualization
        """
        lines = [f"Router: {router_name}"]
        lines.append("       /")

        for i, (route_key, chain_name) in enumerate(routes.items()):
            prefix = "├─ " if i < len(routes) - 1 else "└─ "
            lines.append(f"{prefix}{route_key} → {chain_name}")

        if default_route:
            lines.append(f"└─ [default] → {default_route}")

        return "\n".join(lines)

    @staticmethod
    def visualize_execution_tree(
        execution_log: List[Dict[str, Any]],
    ) -> str:
        """Visualize execution tree from log.

        Args:
            execution_log: Execution event log

        Returns:
            str: ASCII visualization
        """
        lines = ["Execution Tree:"]
        indent_level = 0

        for event in execution_log:
            event_type = event.get("event_type", "unknown")
            name = event.get("chain", event.get("step", "unknown"))

            if event_type == "chain_start" or event_type == "step_start":
                prefix = "  " * indent_level + "├─ "
                lines.append(f"{prefix}▶ {name} (start)")
                indent_level += 1
            elif event_type == "chain_end" or event_type == "step_end":
                indent_level = max(0, indent_level - 1)
                prefix = "  " * indent_level + "└─ "
                execution_time = event.get("metadata", {}).get("execution_time", "?")
                lines.append(f"{prefix}✓ {name} ({execution_time}s)")
            elif event_type == "chain_error" or event_type == "error":
                indent_level = max(0, indent_level - 1)
                prefix = "  " * indent_level + "└─ "
                error = event.get("metadata", {}).get("error", "unknown error")
                lines.append(f"{prefix}✗ {name} (ERROR: {error})")

        return "\n".join(lines)

    @staticmethod
    def visualize_dependency_graph(
        task_graph: Dict[str, Dict[str, Any]],
    ) -> str:
        """Visualize task dependency graph.

        Args:
            task_graph: Task dependency information

        Returns:
            str: ASCII visualization
        """
        lines = ["Dependency Graph:"]

        for task_id, task_info in task_graph.items():
            depends_on = task_info.get("depends_on", [])
            chain_name = task_info.get("chain_name", "unknown")

            lines.append(f"{task_id} ({chain_name})")

            if depends_on:
                for dep_id in depends_on:
                    lines.append(f"  ← {dep_id}")
            else:
                lines.append("  [no dependencies]")

            lines.append("")

        return "\n".join(lines)


class MetricsVisualizer:
    """Visualizes execution metrics."""

    @staticmethod
    def create_simple_bar_chart(
        data: Dict[str, float],
        max_width: int = 40,
        title: Optional[str] = None,
    ) -> str:
        """Create simple ASCII bar chart.

        Args:
            data: Data to visualize (label -> value)
            max_width: Maximum bar width
            title: Optional chart title

        Returns:
            str: ASCII bar chart
        """
        if not data:
            return "No data to visualize"

        lines = []
        if title:
            lines.append(title)
            lines.append("")

        max_value = max(data.values()) if data.values() else 1
        max_label_len = max(len(label) for label in data.keys())

        for label, value in data.items():
            # Calculate bar length
            bar_length = int((value / max_value) * max_width)
            bar = "█" * bar_length + "░" * (max_width - bar_length)

            # Format line
            label_str = label.ljust(max_label_len)
            lines.append(f"{label_str} │{bar}│ {value:.2f}")

        return "\n".join(lines)

    @staticmethod
    def create_execution_timeline(
        events: List[Dict[str, Any]],
    ) -> str:
        """Create execution timeline visualization.

        Args:
            events: List of execution events

        Returns:
            str: Timeline visualization
        """
        if not events:
            return "No events"

        lines = ["Execution Timeline:"]
        lines.append("")

        start_time = None
        for event in events:
            timestamp = event.get("timestamp", "?")

            if start_time is None:
                start_time = timestamp
                elapsed = 0
            else:
                elapsed = "?"

            event_type = event.get("event_type", "?")
            chain = event.get("chain", event.get("step", "?"))

            symbol = {
                "chain_start": "▶",
                "chain_end": "✓",
                "chain_error": "✗",
                "step_start": "▶",
                "step_end": "✓",
            }.get(event_type, "•")

            lines.append(f"{symbol} [{elapsed}] {event_type}: {chain}")

        return "\n".join(lines)

    @staticmethod
    def create_metrics_summary(
        metrics: Dict[str, Dict[str, Any]],
    ) -> str:
        """Create metrics summary report.

        Args:
            metrics: Metrics dictionary

        Returns:
            str: Summary report
        """
        lines = ["Metrics Summary:"]
        lines.append("")

        for chain_name, chain_metrics in metrics.items():
            lines.append(f"Chain: {chain_name}")
            lines.append(f"  Executions: {chain_metrics.get('executions', 0)}")
            lines.append(f"  Successes: {chain_metrics.get('successes', 0)}")
            lines.append(f"  Failures: {chain_metrics.get('failures', 0)}")
            lines.append(f"  Avg Time: {chain_metrics.get('avg_time', 0):.3f}s")
            lines.append(f"  Total Time: {chain_metrics.get('total_time', 0):.3f}s")
            lines.append("")

        return "\n".join(lines)


class HierarchyVisualizer:
    """Visualizes hierarchical structures."""

    @staticmethod
    def visualize_scope_hierarchy(
        scope_info: Dict[str, Any],
    ) -> str:
        """Visualize scope hierarchy.

        Args:
            scope_info: Scope information

        Returns:
            str: Hierarchy visualization
        """
        lines = ["Scope Hierarchy:"]
        lines.append("")

        current_scope = scope_info.get("current_scope", "global")
        scope_depth = scope_info.get("scope_depth", 1)

        for i in range(scope_depth):
            indent = "  " * i
            if i == scope_depth - 1:
                marker = "└─"
                lines.append(f"{indent}{marker} {current_scope} (active)")
            else:
                marker = "├─"
                lines.append(f"{indent}{marker} [scope level {i}]")

        return "\n".join(lines)

    @staticmethod
    def visualize_entity_relationships(
        entities: Dict[str, Dict[str, Any]],
    ) -> str:
        """Visualize entity relationship graph.

        Args:
            entities: Entity dictionary

        Returns:
            str: Relationship visualization
        """
        lines = ["Entity Relationships:"]
        lines.append("")

        for entity_id, entity_info in entities.items():
            entity_type = entity_info.get("entity_type", "unknown")
            name = entity_info.get("name", "unnamed")

            lines.append(f"[{entity_type}] {name} ({entity_id})")

            relationships = entity_info.get("relationships", {})
            if relationships:
                for rel_type, target_ids in relationships.items():
                    for target_id in target_ids:
                        lines.append(f"  ─{rel_type}→ {target_id}")

        return "\n".join(lines)


def visualize_execution_flow(
    execution_data: Dict[str, Any],
) -> str:
    """Generate complete execution flow visualization.

    Args:
        execution_data: Complete execution data

    Returns:
        str: Comprehensive visualization
    """
    output = []

    # Title
    output.append("=" * 60)
    output.append("EXECUTION FLOW VISUALIZATION")
    output.append("=" * 60)
    output.append("")

    # Execution tree
    if "execution_trace" in execution_data:
        output.append(ChainVisualizer.visualize_execution_tree(
            execution_data["execution_trace"]
        ))
        output.append("")

    # Metrics
    if "metrics" in execution_data:
        metrics = execution_data.get("metrics", {}).get("chain_metrics", {})
        output.append(MetricsVisualizer.create_metrics_summary(metrics))
        output.append("")

    # Breakpoints
    if "breakpoints" in execution_data:
        output.append("Breakpoints:")
        for bp_id, bp_info in execution_data["breakpoints"].items():
            output.append(f"  {bp_id}: {bp_info.get('chain_name')} "
                         f"(hits: {bp_info.get('hit_count')})")
        output.append("")

    output.append("=" * 60)
    return "\n".join(output)
