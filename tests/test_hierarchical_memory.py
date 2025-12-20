"""Tests for Hierarchical Memory System."""

import pytest
import time
from core.memory import (
    AtlasMemory, 
    HierarchicalMemory, 
    WorkingMemoryItem,
    get_memory,
    get_hierarchical_memory
)


class TestWorkingMemoryItem:
    """Tests for WorkingMemoryItem dataclass."""

    def test_not_expired_initially(self):
        """Verify new items are not expired."""
        item = WorkingMemoryItem(content="test", context="", ttl_seconds=3600)
        assert not item.is_expired()

    def test_expired_after_ttl(self):
        """Verify items expire after TTL."""
        item = WorkingMemoryItem(content="test", context="", ttl_seconds=0)
        time.sleep(0.1)
        assert item.is_expired()


class TestHierarchicalMemory:
    """Tests for HierarchicalMemory class."""

    @pytest.fixture
    def memory(self, tmp_path):
        """Create a test memory instance with temp path."""
        return HierarchicalMemory(persist_path=str(tmp_path / "test_memory"))

    def test_inherits_atlas_memory(self, memory):
        """Verify HierarchicalMemory inherits AtlasMemory."""
        assert isinstance(memory, AtlasMemory)

    def test_working_memory_add_and_get(self, memory):
        """Test working memory add and retrieval."""
        result = memory.add_to_working_memory(
            key="test_key",
            content="Test content",
            context="Test context",
            priority=5
        )
        
        assert result["status"] == "success"
        assert result["layer"] == "working"
        
        item = memory.get_from_working_memory("test_key")
        assert item is not None
        assert item.content == "Test content"
        assert item.priority == 5

    def test_working_memory_query(self, memory):
        """Test working memory query functionality."""
        memory.add_to_working_memory("key1", "Hello world", priority=3)
        memory.add_to_working_memory("key2", "Goodbye world", priority=7)
        memory.add_to_working_memory("key3", "Test data", priority=1)
        
        # Query all
        results = memory.query_working_memory()
        assert len(results) == 3
        # Should be sorted by priority (highest first)
        assert results[0]["priority"] == 7
        
        # Query with search term
        results = memory.query_working_memory(query="world")
        assert len(results) == 2
        
        # Query with min priority
        results = memory.query_working_memory(min_priority=5)
        assert len(results) == 1

    def test_working_memory_clear(self, memory):
        """Test working memory clear."""
        memory.add_to_working_memory("key1", "Content 1")
        memory.add_to_working_memory("key2", "Content 2")
        
        memory.clear_working_memory()
        
        assert memory.query_working_memory() == []

    def test_episodic_memory_add_and_query(self, memory):
        """Test episodic memory operations."""
        result = memory.add_episodic_memory(
            content="Opened Chrome browser",
            action_type="tool_execution",
            outcome="success"
        )
        
        assert result["status"] == "success"
        assert result["layer"] == "episodic"
        
        # Query
        results = memory.query_episodic_memory("Chrome")
        assert len(results) > 0
        assert "Chrome" in results[0]["content"]

    def test_semantic_memory_add_and_query(self, memory):
        """Test semantic memory operations."""
        result = memory.add_semantic_memory(
            content="Pattern: Use AppleScript for GUI automation on macOS",
            knowledge_type="pattern",
            confidence=0.9
        )
        
        assert result["status"] == "success"
        assert result["layer"] == "semantic"
        
        # Query
        results = memory.query_semantic_memory("AppleScript", min_confidence=0.8)
        assert len(results) > 0

    def test_consolidate_to_semantic(self, memory):
        """Test episodic to semantic consolidation."""
        result = memory.consolidate_to_semantic(
            episodic_content="Learned: Browser automation works best with Playwright",
            knowledge_type="pattern",
            confidence_boost=0.2
        )
        
        assert result["status"] == "success"
        assert result["layer"] == "semantic"

    def test_get_relevant_context(self, memory):
        """Test cross-layer context query."""
        # Add to each layer
        memory.add_to_working_memory("work1", "Working on automation")
        memory.add_episodic_memory("Executed browser task", "tool_execution")
        memory.add_semantic_memory("Automation pattern for browsers", "pattern")
        
        # Query all layers
        results = memory.get_relevant_context("automation")
        
        assert "working" in results
        assert "episodic" in results
        assert "semantic" in results
        assert "legacy" in results

    def test_get_stats(self, memory):
        """Test statistics generation."""
        memory.add_to_working_memory("key1", "Content")
        memory.add_episodic_memory("Event", "test")
        memory.add_semantic_memory("Knowledge", "fact")
        
        stats = memory.get_stats()
        
        assert "session_id" in stats
        assert "working_memory" in stats
        assert "episodic_memory" in stats
        assert "semantic_memory" in stats
        assert stats["working_memory"]["active_items"] >= 1


class TestBackwardCompatibility:
    """Tests for backward compatibility with AtlasMemory."""

    @pytest.fixture
    def memory(self, tmp_path):
        return HierarchicalMemory(persist_path=str(tmp_path / "compat_memory"))

    def test_legacy_add_memory(self, memory):
        """Test legacy add_memory still works."""
        result = memory.add_memory(
            category="knowledge_base",
            content="Test knowledge",
            metadata={"tags": "test"}
        )
        
        assert result["status"] == "success"

    def test_legacy_query_memory(self, memory):
        """Test legacy query_memory still works."""
        memory.add_memory("strategies", "Strategy A: Use native tools first")
        
        results = memory.query_memory("strategies", "native tools")
        assert isinstance(results, list)

    def test_legacy_collections_exist(self, memory):
        """Verify legacy collections are available."""
        assert memory.ui_patterns is not None
        assert memory.strategies is not None
        assert memory.user_habits is not None
        assert memory.knowledge_base is not None
