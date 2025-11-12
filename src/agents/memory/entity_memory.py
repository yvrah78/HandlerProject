"""
Entity Memory for tracking entities and their relationships.
Maintains entity graphs with attributes and interaction history.
"""
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime
from src.agents.memory.base_memory import BaseMemory
from src.core.logging import get_logger

logger = get_logger(__name__)


class Entity:
    """Represents an entity in memory."""

    def __init__(self, entity_id: str, entity_type: str, name: str):
        """Initialize entity.

        Args:
            entity_id: Unique identifier
            entity_type: Type of entity (customer, vehicle, driver, etc.)
            name: Entity name
        """
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.name = name
        self.attributes: Dict[str, Any] = {}
        self.relationships: Dict[str, List[str]] = {}  # relationship_type -> [entity_ids]
        self.first_mentioned = datetime.utcnow()
        self.last_updated = datetime.utcnow()
        self.mention_count = 0
        self.interaction_history: List[Dict[str, Any]] = []

    def add_attribute(self, key: str, value: Any) -> None:
        """Add/update entity attribute."""
        self.attributes[key] = value
        self.last_updated = datetime.utcnow()

    def add_relationship(self, relationship_type: str, target_entity_id: str) -> None:
        """Add relationship to another entity."""
        if relationship_type not in self.relationships:
            self.relationships[relationship_type] = []
        if target_entity_id not in self.relationships[relationship_type]:
            self.relationships[relationship_type].append(target_entity_id)
        self.last_updated = datetime.utcnow()

    def record_interaction(self, interaction_type: str, details: Dict[str, Any]) -> None:
        """Record interaction with entity."""
        self.interaction_history.append({
            "type": interaction_type,
            "timestamp": datetime.utcnow(),
            "details": details,
        })
        self.mention_count += 1
        self.last_updated = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary."""
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "name": self.name,
            "attributes": self.attributes,
            "relationships": self.relationships,
            "first_mentioned": self.first_mentioned.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "mention_count": self.mention_count,
            "interaction_count": len(self.interaction_history),
        }


class EntityMemory(BaseMemory):
    """
    Memory system that tracks entities and their relationships.

    Useful for maintaining knowledge about:
    - Customers and their attributes
    - Vehicles and their status
    - Drivers and their performance
    - Relationships between entities
    """

    def __init__(
        self,
        max_entities: int = 1000,
        max_interactions_per_entity: int = 100,
        ttl_seconds: Optional[int] = None,
    ):
        """Initialize entity memory.

        Args:
            max_entities: Maximum entities to track
            max_interactions_per_entity: Max interaction records per entity
            ttl_seconds: TTL for messages
        """
        super().__init__(ttl_seconds=ttl_seconds)
        self.entities: Dict[str, Entity] = {}
        self.max_entities = max_entities
        self.max_interactions_per_entity = max_interactions_per_entity
        self.entity_index: Dict[str, Set[str]] = {}  # entity_type -> {entity_ids}

    def add_entity(
        self,
        entity_id: str,
        entity_type: str,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Entity:
        """Add or update entity.

        Args:
            entity_id: Unique entity ID
            entity_type: Type of entity
            name: Entity name
            attributes: Initial attributes

        Returns:
            Entity: The entity object
        """
        if entity_id in self.entities:
            entity = self.entities[entity_id]
            if attributes:
                for key, value in attributes.items():
                    entity.add_attribute(key, value)
        else:
            if len(self.entities) >= self.max_entities:
                self._evict_least_recent_entity()

            entity = Entity(entity_id, entity_type, name)
            if attributes:
                for key, value in attributes.items():
                    entity.add_attribute(key, value)

            self.entities[entity_id] = entity

            # Add to index
            if entity_type not in self.entity_index:
                self.entity_index[entity_type] = set()
            self.entity_index[entity_type].add(entity_id)

            logger.debug(f"Added entity: {entity_id} ({entity_type})")

        return entity

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID."""
        return self.entities.get(entity_id)

    def get_entities_by_type(self, entity_type: str) -> List[Entity]:
        """Get all entities of a specific type."""
        entity_ids = self.entity_index.get(entity_type, set())
        return [self.entities[eid] for eid in entity_ids if eid in self.entities]

    def find_entity(self, entity_type: str, **attributes) -> Optional[Entity]:
        """Find entity by type and attributes.

        Args:
            entity_type: Type of entity
            **attributes: Attribute filters

        Returns:
            Entity: First matching entity or None
        """
        candidates = self.get_entities_by_type(entity_type)
        for entity in candidates:
            if all(
                entity.attributes.get(k) == v for k, v in attributes.items()
            ):
                return entity
        return None

    def add_relationship(
        self,
        entity_id: str,
        relationship_type: str,
        target_entity_id: str,
    ) -> None:
        """Add relationship between entities."""
        entity = self.get_entity(entity_id)
        if entity:
            entity.add_relationship(relationship_type, target_entity_id)
            logger.debug(
                f"Added relationship: {entity_id} -[{relationship_type}]-> {target_entity_id}"
            )

    def get_related_entities(
        self,
        entity_id: str,
        relationship_type: Optional[str] = None,
    ) -> List[Tuple[str, str]]:
        """Get related entities.

        Args:
            entity_id: Source entity ID
            relationship_type: Optional filter by relationship type

        Returns:
            List of (entity_id, entity_type) tuples
        """
        entity = self.get_entity(entity_id)
        if not entity:
            return []

        related = []
        relationships = (
            {relationship_type: entity.relationships[relationship_type]}
            if relationship_type and relationship_type in entity.relationships
            else entity.relationships
        )

        for rel_type, target_ids in relationships.items():
            for target_id in target_ids:
                target_entity = self.get_entity(target_id)
                if target_entity:
                    related.append((target_id, target_entity.entity_type))

        return related

    def record_interaction(
        self,
        entity_id: str,
        interaction_type: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record interaction with entity."""
        entity = self.get_entity(entity_id)
        if entity:
            entity.record_interaction(interaction_type, details or {})

    def add_message(self, role: str, content: str) -> None:
        """Add message and extract entities.

        Args:
            role: Message role (user, assistant)
            content: Message content
        """
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def get_messages(
        self,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get messages.

        Args:
            limit: Max messages to return

        Returns:
            List of messages
        """
        messages = self.messages[-limit:] if limit else self.messages
        return messages

    def get_summary(self) -> str:
        """Get entity memory summary."""
        summary = "Entity Memory Summary:\n"
        summary += f"Total entities: {len(self.entities)}\n"
        summary += f"Entity types: {list(self.entity_index.keys())}\n"

        for entity_type, entity_ids in self.entity_index.items():
            summary += f"  {entity_type}: {len(entity_ids)} entities\n"

        # Top mentioned entities
        if self.entities:
            top_entities = sorted(
                self.entities.values(),
                key=lambda e: e.mention_count,
                reverse=True,
            )[:5]
            summary += "\nTop mentioned entities:\n"
            for entity in top_entities:
                summary += f"  - {entity.name} ({entity.entity_type}): {entity.mention_count} mentions\n"

        return summary

    def export_entities(self) -> Dict[str, Any]:
        """Export all entities as dictionary.

        Returns:
            Dict with all entity data
        """
        return {
            entity_id: entity.to_dict()
            for entity_id, entity in self.entities.items()
        }

    def clear(self) -> None:
        """Clear all entities."""
        self.entities.clear()
        self.entity_index.clear()
        self.messages.clear()
        logger.info("Cleared entity memory")

    def _evict_least_recent_entity(self) -> None:
        """Evict entity with oldest last_updated time."""
        if not self.entities:
            return

        least_recent = min(
            self.entities.values(),
            key=lambda e: e.last_updated,
        )

        entity_type = least_recent.entity_type
        del self.entities[least_recent.entity_id]

        if entity_type in self.entity_index:
            self.entity_index[entity_type].discard(least_recent.entity_id)

        logger.debug(f"Evicted entity: {least_recent.entity_id}")

    def get_entity_stats(self) -> Dict[str, Any]:
        """Get memory statistics.

        Returns:
            Dict with stats
        """
        total_interactions = sum(
            len(e.interaction_history) for e in self.entities.values()
        )
        total_relationships = sum(
            sum(len(v) for v in e.relationships.values())
            for e in self.entities.values()
        )

        return {
            "total_entities": len(self.entities),
            "entity_types": len(self.entity_index),
            "total_interactions": total_interactions,
            "total_relationships": total_relationships,
            "messages_count": len(self.messages),
        }
