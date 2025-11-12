"""
Vector Memory with embeddings for semantic similarity search.
Enables semantic search and similarity-based memory retrieval.
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
from src.agents.memory.base_memory import BaseMemory
from src.core.logging import get_logger

logger = get_logger(__name__)


class VectorMemory(BaseMemory):
    """
    Memory system using semantic embeddings for similarity search.

    Features:
    - Store messages with embeddings
    - Semantic similarity search
    - Relevance-based retrieval
    - Clustering of related messages
    """

    def __init__(
        self,
        embedding_model: str = "text-embedding-3-small",
        embedding_dim: int = 1536,
        max_vectors: int = 10000,
        similarity_threshold: float = 0.7,
        ttl_seconds: Optional[int] = None,
    ):
        """Initialize vector memory.

        Args:
            embedding_model: Model for generating embeddings
            embedding_dim: Dimension of embedding vectors
            max_vectors: Maximum vectors to store
            similarity_threshold: Threshold for similarity search
            ttl_seconds: TTL for messages
        """
        super().__init__(ttl_seconds=ttl_seconds)
        self.embedding_model = embedding_model
        self.embedding_dim = embedding_dim
        self.max_vectors = max_vectors
        self.similarity_threshold = similarity_threshold

        self.vectors: Dict[str, List[float]] = {}  # message_id -> embedding
        self.vector_to_message: Dict[str, Dict[str, Any]] = {}  # message_id -> message
        self.message_metadata: Dict[str, Dict[str, Any]] = {}  # message_id -> metadata

        # Approximate similarity index (simplified)
        self.similarity_index: Dict[str, List[Tuple[str, float]]] = {}

    def add_message(
        self,
        role: str,
        content: str,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add message with embedding.

        Args:
            role: Message role
            content: Message content
            embedding: Vector embedding (optional - can compute later)
            metadata: Additional metadata

        Returns:
            str: Message ID
        """
        message_id = f"msg_{len(self.messages)}_{datetime.utcnow().timestamp()}"

        message = {
            "message_id": message_id,
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        }

        self.messages.append(message)

        if embedding:
            if len(self.vectors) >= self.max_vectors:
                self._evict_oldest_vector()
            self.vectors[message_id] = embedding

        self.vector_to_message[message_id] = message
        self.message_metadata[message_id] = metadata or {}

        logger.debug(f"Added message: {message_id}")

        return message_id

    def search_similar(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_role: Optional[str] = None,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Search for similar messages.

        Args:
            query_embedding: Query vector embedding
            top_k: Number of top results
            filter_role: Optional role filter

        Returns:
            List of (message, similarity_score) tuples
        """
        if not self.vectors:
            return []

        # Compute similarities
        similarities: List[Tuple[str, float]] = []
        for msg_id, vector in self.vectors.items():
            similarity = self._cosine_similarity(query_embedding, vector)
            if similarity >= self.similarity_threshold:
                message = self.vector_to_message[msg_id]
                if filter_role is None or message["role"] == filter_role:
                    similarities.append((msg_id, similarity))

        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Return top-k
        results = []
        for msg_id, similarity in similarities[:top_k]:
            message = self.vector_to_message[msg_id]
            results.append((message, similarity))

        return results

    def find_related_messages(
        self,
        message_id: str,
        top_k: int = 5,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Find messages related to a specific message.

        Args:
            message_id: Source message ID
            top_k: Number of results

        Returns:
            List of (message, similarity_score) tuples
        """
        if message_id not in self.vectors:
            logger.warning(f"Message {message_id} not in vector index")
            return []

        query_embedding = self.vectors[message_id]
        return self.search_similar(query_embedding, top_k=top_k)

    def cluster_messages(
        self,
        num_clusters: int = 5,
    ) -> Dict[int, List[Dict[str, Any]]]:
        """Simple clustering of messages using embeddings.

        Args:
            num_clusters: Number of clusters

        Returns:
            Dict mapping cluster ID to messages
        """
        if not self.vectors:
            return {}

        # Simplified clustering: use first messages as cluster centers
        clusters: Dict[int, List[Dict[str, Any]]] = {i: [] for i in range(num_clusters)}

        if len(self.vectors) < num_clusters:
            # Just use one cluster if not enough messages
            for msg_id in self.vectors:
                clusters[0].append(self.vector_to_message[msg_id])
            return clusters

        # Assign messages to nearest cluster
        msg_ids = list(self.vectors.keys())
        centers = [self.vectors[msg_ids[i]] for i in range(num_clusters)]

        for msg_id in msg_ids:
            vector = self.vectors[msg_id]
            # Find nearest center
            nearest_cluster = min(
                range(num_clusters),
                key=lambda i: self._euclidean_distance(vector, centers[i]),
            )
            clusters[nearest_cluster].append(self.vector_to_message[msg_id])

        return clusters

    def get_messages(
        self,
        limit: Optional[int] = None,
        role: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get messages with optional filtering.

        Args:
            limit: Max messages
            role: Optional role filter

        Returns:
            List of messages
        """
        messages = self.messages[-limit:] if limit else self.messages

        if role:
            messages = [m for m in messages if m.get("role") == role]

        return messages

    def get_summary(self) -> str:
        """Get vector memory summary."""
        summary = "Vector Memory Summary:\n"
        summary += f"Total messages: {len(self.messages)}\n"
        summary += f"Vectors indexed: {len(self.vectors)}\n"
        summary += f"Embedding model: {self.embedding_model}\n"
        summary += f"Embedding dimension: {self.embedding_dim}\n"

        # Role distribution
        role_counts = {}
        for msg in self.messages:
            role = msg.get("role", "unknown")
            role_counts[role] = role_counts.get(role, 0) + 1

        summary += "Message distribution:\n"
        for role, count in role_counts.items():
            summary += f"  {role}: {count}\n"

        return summary

    def export_vectors(self) -> Dict[str, Any]:
        """Export vectors and messages.

        Returns:
            Dict with vectors and metadata
        """
        return {
            "model": self.embedding_model,
            "dimension": self.embedding_dim,
            "message_count": len(self.messages),
            "vector_count": len(self.vectors),
            "messages": self.messages,
            "metadata": self.message_metadata,
        }

    def import_vectors(
        self,
        data: Dict[str, Any],
        clear_existing: bool = False,
    ) -> None:
        """Import vectors from export.

        Args:
            data: Exported vector data
            clear_existing: Clear existing vectors
        """
        if clear_existing:
            self.clear()

        if "messages" in data:
            self.messages.extend(data["messages"])

        if "metadata" in data:
            self.message_metadata.update(data["metadata"])

        logger.info(f"Imported {len(data.get('messages', []))} messages")

    def clear(self) -> None:
        """Clear all vectors and messages."""
        self.vectors.clear()
        self.vector_to_message.clear()
        self.message_metadata.clear()
        self.similarity_index.clear()
        self.messages.clear()
        logger.info("Cleared vector memory")

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics.

        Returns:
            Dict with stats
        """
        return {
            "total_messages": len(self.messages),
            "indexed_vectors": len(self.vectors),
            "embedding_model": self.embedding_model,
            "embedding_dimension": self.embedding_dim,
            "memory_usage_estimate_mb": (
                len(self.vectors) * self.embedding_dim * 4 / (1024 * 1024)
            ),
        }

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            float: Similarity score 0-1
        """
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        # Compute dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))

        # Compute magnitudes
        mag1 = sum(a * a for a in vec1) ** 0.5
        mag2 = sum(b * b for b in vec2) ** 0.5

        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot_product / (mag1 * mag2)

    @staticmethod
    def _euclidean_distance(vec1: List[float], vec2: List[float]) -> float:
        """Compute Euclidean distance between vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            float: Distance
        """
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return float("inf")

        return sum((a - b) ** 2 for a, b in zip(vec1, vec2)) ** 0.5

    def _evict_oldest_vector(self) -> None:
        """Evict oldest vector when max capacity reached."""
        if not self.vector_to_message:
            return

        # Find oldest message
        oldest_msg_id = min(
            self.vector_to_message.keys(),
            key=lambda mid: self.vector_to_message[mid].get("timestamp", ""),
        )

        if oldest_msg_id in self.vectors:
            del self.vectors[oldest_msg_id]

        logger.debug(f"Evicted vector: {oldest_msg_id}")
