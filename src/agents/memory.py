"""
Vector Memory Store for AI Agents

This module implements a vector-based memory system using ChromaDB
for storing and retrieving agent memories based on semantic similarity.
"""

import uuid
from typing import List, Optional
import chromadb
from chromadb.config import Settings


class VectorMemoryStore:
    """
    A vector-based memory store that uses ChromaDB for semantic memory retrieval.
    
    Each agent has its own memory collection that stores experiences as
    text embeddings for efficient similarity-based retrieval.
    """
    
    def __init__(self, agent_id: str, persist_directory: Optional[str] = None):
        """
        Initialize the memory store for a specific agent.
        
        Args:
            agent_id: Unique identifier for the agent
            persist_directory: Directory to persist the database (optional)
        """
        self.agent_id = agent_id
        
        # Initialize ChromaDB client
        if persist_directory:
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
        else:
            self.client = chromadb.EphemeralClient(
                settings=Settings(anonymized_telemetry=False)
            )
        
        # Create or get collection for this agent
        self.collection_name = f"agent_{agent_id}_memories"
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
        except Exception:
            # Collection doesn't exist, create it
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"agent_id": agent_id}
            )
    
    def add(self, memory_text: str) -> str:
        """
        Add a new memory to the store.
        
        Args:
            memory_text: The text content of the memory to store
            
        Returns:
            The unique ID of the stored memory
        """
        memory_id = str(uuid.uuid4())
        
        # Add the memory to the collection
        self.collection.add(
            documents=[memory_text],
            ids=[memory_id],
            metadatas=[{
                "agent_id": self.agent_id,
                "memory_type": "experience"
            }]
        )
        
        return memory_id
    
    def retrieve(self, query_text: str, top_k: int = 5) -> List[str]:
        """
        Retrieve the most relevant memories based on a query.
        
        Args:
            query_text: The query text to search for similar memories
            top_k: Maximum number of memories to retrieve
            
        Returns:
            List of relevant memory texts, ordered by relevance
        """
        if not query_text.strip():
            return []
        
        try:
            # Query the collection for similar memories
            results = self.collection.query(
                query_texts=[query_text],
                n_results=min(top_k, self.collection.count())
            )
            
            # Extract and return the document texts
            if results['documents'] and len(results['documents']) > 0:
                return results['documents'][0]  # First (and only) query result
            else:
                return []
                
        except Exception as e:
            # If query fails, return empty list
            print(f"Memory retrieval failed for agent {self.agent_id}: {e}")
            return []
    
    def get_memory_count(self) -> int:
        """
        Get the total number of memories stored.
        
        Returns:
            Number of memories in the store
        """
        return self.collection.count()
    
    def clear_memories(self) -> None:
        """
        Clear all memories from the store.
        """
        # Delete the collection and recreate it
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"agent_id": self.agent_id}
        )
    
    def get_all_memories(self) -> List[str]:
        """
        Retrieve all memories (for debugging/analysis purposes).
        
        Returns:
            List of all memory texts
        """
        try:
            results = self.collection.get()
            return results['documents'] if results['documents'] else []
        except Exception as e:
            print(f"Failed to retrieve all memories for agent {self.agent_id}: {e}")
            return []