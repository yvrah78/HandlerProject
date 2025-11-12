"""
Tests for memory systems.
Tests ConversationBuffer, Summary, Entity, and Vector memory.
"""
import pytest
from datetime import datetime, timedelta

from src.agents.memory import (
    ConversationBufferMemory,
    SummaryMemory,
    EntityMemory,
    VectorMemory,
)


class TestConversationBufferMemory:
    """Tests for conversation buffer memory."""

    def test_initialization(self):
        """Test memory initialization."""
        memory = ConversationBufferMemory(max_size=10)
        assert memory.max_size == 10
        assert len(memory.messages) == 0

    def test_add_message(self):
        """Test adding messages."""
        memory = ConversationBufferMemory()
        memory.add_message("user", "Hello")
        memory.add_message("assistant", "Hi there")

        assert len(memory.messages) == 2
        assert memory.messages[0]["content"] == "Hello"

    def test_get_messages(self):
        """Test retrieving messages."""
        memory = ConversationBufferMemory()
        memory.add_message("user", "Hello")
        memory.add_message("assistant", "Hi")

        messages = memory.get_messages()
        assert len(messages) == 2

    def test_max_size_enforcement(self):
        """Test max size enforcement."""
        memory = ConversationBufferMemory(max_size=3)

        for i in range(5):
            memory.add_message("user", f"Message {i}")

        assert len(memory.messages) <= 3

    def test_clear(self):
        """Test clearing memory."""
        memory = ConversationBufferMemory()
        memory.add_message("user", "Hello")
        memory.clear()

        assert len(memory.messages) == 0

    def test_get_summary(self):
        """Test getting summary."""
        memory = ConversationBufferMemory()
        memory.add_message("user", "Hello")

        summary = memory.get_summary()
        assert "Messages" in summary or "messages" in summary.lower()


class TestSummaryMemory:
    """Tests for summary memory."""

    def test_initialization(self):
        """Test summary memory initialization."""
        memory = SummaryMemory(summary_threshold=5)
        assert memory.summary_threshold == 5

    def test_auto_summarization(self):
        """Test automatic summarization."""
        memory = SummaryMemory(summary_threshold=3)

        for i in range(5):
            memory.add_message("user", f"Message {i}")

        # Should trigger summarization
        assert memory.summary is not None and memory.summary != ""

    def test_summary_export(self):
        """Test exporting summary."""
        memory = SummaryMemory()
        memory.add_message("user", "Hello")

        summary = memory.get_summary()
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_get_memory_stats(self):
        """Test memory statistics."""
        memory = SummaryMemory()
        memory.add_message("user", "Hello")
        memory.add_message("assistant", "Hi")

        stats = memory.get_memory_stats()
        assert "buffer_size" in stats
        assert "total_messages" in stats


class TestEntityMemory:
    """Tests for entity memory."""

    def test_add_entity(self):
        """Test adding entities."""
        memory = EntityMemory()
        entity = memory.add_entity(
            "customer_1",
            "customer",
            "John Doe",
            attributes={"email": "john@example.com"},
        )

        assert entity.entity_id == "customer_1"
        assert entity.name == "John Doe"

    def test_get_entity(self):
        """Test retrieving entity."""
        memory = EntityMemory()
        memory.add_entity("customer_1", "customer", "John")

        entity = memory.get_entity("customer_1")
        assert entity is not None
        assert entity.name == "John"

    def test_get_entities_by_type(self):
        """Test retrieving entities by type."""
        memory = EntityMemory()
        memory.add_entity("customer_1", "customer", "John")
        memory.add_entity("customer_2", "customer", "Jane")
        memory.add_entity("vehicle_1", "vehicle", "Car")

        customers = memory.get_entities_by_type("customer")
        assert len(customers) == 2

    def test_entity_relationships(self):
        """Test entity relationships."""
        memory = EntityMemory()
        memory.add_entity("customer_1", "customer", "John")
        memory.add_entity("vehicle_1", "vehicle", "Car")

        memory.add_relationship("customer_1", "owns", "vehicle_1")

        related = memory.get_related_entities("customer_1")
        assert len(related) > 0

    def test_entity_interactions(self):
        """Test recording entity interactions."""
        memory = EntityMemory()
        entity = memory.add_entity("customer_1", "customer", "John")

        memory.record_interaction("customer_1", "booking_created", {"booking_id": "b1"})

        assert entity.mention_count > 0

    def test_find_entity(self):
        """Test finding entity by attributes."""
        memory = EntityMemory()
        memory.add_entity(
            "customer_1",
            "customer",
            "John",
            attributes={"email": "john@example.com"},
        )

        found = memory.find_entity("customer", email="john@example.com")
        assert found is not None
        assert found.name == "John"

    def test_export_entities(self):
        """Test exporting entities."""
        memory = EntityMemory()
        memory.add_entity("customer_1", "customer", "John")

        exported = memory.export_entities()
        assert "customer_1" in exported

    def test_entity_stats(self):
        """Test entity statistics."""
        memory = EntityMemory()
        memory.add_entity("customer_1", "customer", "John")

        stats = memory.get_entity_stats()
        assert stats["total_entities"] == 1


class TestVectorMemory:
    """Tests for vector memory."""

    def test_initialization(self):
        """Test vector memory initialization."""
        memory = VectorMemory()
        assert memory.embedding_model == "text-embedding-3-small"
        assert memory.embedding_dim == 1536

    def test_add_message_with_embedding(self):
        """Test adding message with embedding."""
        memory = VectorMemory()

        # Create dummy embedding
        embedding = [0.1] * 1536

        msg_id = memory.add_message("user", "Hello", embedding=embedding)
        assert msg_id is not None

    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]

        similarity = VectorMemory._cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(1.0, abs=0.01)

    def test_euclidean_distance(self):
        """Test euclidean distance calculation."""
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [3.0, 4.0, 0.0]

        distance = VectorMemory._euclidean_distance(vec1, vec2)
        assert distance == pytest.approx(5.0, abs=0.01)

    def test_search_similar(self):
        """Test similarity search."""
        memory = VectorMemory()

        # Add messages with embeddings
        embedding1 = [1.0, 0.0, 0.0]
        embedding2 = [0.9, 0.1, 0.0]

        memory.add_message("user", "Hello", embedding=embedding1)
        memory.add_message("assistant", "Hi", embedding=embedding2)

        # Search for similar
        results = memory.search_similar(embedding1, top_k=1)
        assert len(results) > 0

    def test_get_messages(self):
        """Test retrieving messages."""
        memory = VectorMemory()
        memory.add_message("user", "Hello")
        memory.add_message("assistant", "Hi")

        messages = memory.get_messages()
        assert len(messages) == 2

    def test_cluster_messages(self):
        """Test message clustering."""
        memory = VectorMemory()

        # Add messages
        memory.add_message("user", "Hello", embedding=[1.0, 0.0, 0.0])
        memory.add_message("user", "Hi", embedding=[1.0, 0.0, 0.0])

        clusters = memory.cluster_messages(num_clusters=1)
        assert len(clusters) > 0

    def test_memory_stats(self):
        """Test memory statistics."""
        memory = VectorMemory()
        memory.add_message("user", "Hello")

        stats = memory.get_memory_stats()
        assert "total_messages" in stats
        assert "embedding_model" in stats

    def test_export_import(self):
        """Test exporting and importing."""
        memory1 = VectorMemory()
        memory1.add_message("user", "Hello")

        exported = memory1.export_vectors()
        assert "messages" in exported

        memory2 = VectorMemory()
        memory2.import_vectors(exported)
        assert len(memory2.messages) > 0


class TestMemoryIntegration:
    """Integration tests for memory systems."""

    def test_mixed_memory_usage(self):
        """Test using multiple memory types together."""
        buffer = ConversationBufferMemory()
        entity = EntityMemory()
        vector = VectorMemory()

        # Simulate conversation
        buffer.add_message("user", "I want to book a car")
        entity.add_entity("customer_1", "customer", "John")

        # All should work together
        assert len(buffer.messages) == 1
        assert entity.get_entity("customer_1") is not None
        assert vector.get_memory_stats() is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
