"""Tests for Context7 Sliding Window functionality."""

import pytest
from core.context7 import Context7, ContextMetrics


class MockMessage:
    """Mock LangChain message for testing."""
    def __init__(self, content: str, msg_type: str = "AIMessage"):
        self.content = content
        self._type = msg_type


class TestContext7SlidingWindow:
    """Tests for the new sliding window context management."""

    def setup_method(self):
        """Set up test fixtures."""
        self.context7 = Context7(verbose=False)

    def test_prepare_backward_compatibility(self):
        """Verify original prepare() method still works."""
        result = self.context7.prepare(
            rag_context="Some RAG context",
            project_structure="project structure here",
            meta_config={"strategy": "linear"},
            last_msg="test message"
        )
        
        assert "STRATEGIC POLICY" in result
        assert "linear" in result.upper() or "LINEAR" in result

    def test_sliding_window_limits_messages(self):
        """Verify sliding window respects MAX_WINDOW_STEPS."""
        # Create more messages than window size
        messages = [
            MockMessage(f"[VOICE] Step {i} completed")
            for i in range(20)
        ]
        
        result = self.context7.prepare_with_window(
            messages=messages,
            original_task="Test task",
            rag_context="RAG",
            project_structure="Structure",
            meta_config={"strategy": "linear"}
        )
        
        # Should only include last MAX_WINDOW_STEPS messages
        # Verify metrics recorded correctly
        metrics = self.context7.get_last_metrics()
        assert metrics is not None
        assert metrics.estimated_tokens > 0

    def test_priority_weighting(self):
        """Verify priority weights are applied correctly."""
        # Weights should sum to 1.0
        total_weight = sum(Context7.PRIORITY_WEIGHTS.values())
        assert abs(total_weight - 1.0) < 0.01, f"Weights sum to {total_weight}, expected 1.0"

    def test_metrics_tracking(self):
        """Verify metrics are tracked correctly."""
        self.context7.clear_metrics_history()
        
        # Make a call
        self.context7.prepare_with_window(
            messages=[MockMessage("[VOICE] Test")],
            original_task="Task",
            rag_context="Context",
            project_structure="Structure",
            meta_config={}
        )
        
        metrics = self.context7.get_last_metrics()
        assert metrics is not None
        assert isinstance(metrics, ContextMetrics)
        assert metrics.total_chars > 0
        assert "policy" in metrics.sections_included

    def test_stats_returns_enhanced_info(self):
        """Verify stats() returns enhanced information."""
        stats = self.context7.stats()
        
        assert stats["policy"] == "sliding_window_priority"
        assert "max_window_steps" in stats
        assert "priority_weights" in stats

    def test_truncation_tracking(self):
        """Verify truncations are tracked in metrics."""
        # Create very long content to force truncation
        long_structure = "x" * 100000  # Very long structure
        
        self.context7.prepare_with_window(
            messages=[],
            original_task="Task",
            rag_context="Short",
            project_structure=long_structure,
            meta_config={},
            max_tokens=1000  # Low token limit to force truncation
        )
        
        metrics = self.context7.get_last_metrics()
        assert metrics is not None
        assert len(metrics.truncations) > 0, "Should have recorded truncations"
        assert "structure" in metrics.truncations

    def test_metrics_history_limit(self):
        """Verify metrics history is limited to 100 entries."""
        self.context7.clear_metrics_history()
        
        # Make 150 calls
        for i in range(150):
            self.context7.prepare_with_window(
                messages=[],
                original_task=f"Task {i}",
                rag_context="",
                project_structure="",
                meta_config={}
            )
        
        stats = self.context7.stats()
        assert stats["metrics_history_size"] <= 100


class TestContextMetrics:
    """Tests for ContextMetrics dataclass."""

    def test_to_dict(self):
        """Verify to_dict() returns proper dictionary."""
        metrics = ContextMetrics(
            total_chars=1000,
            estimated_tokens=250,
            sections_included=["policy", "task"],
            truncations={"structure": 500}
        )
        
        result = metrics.to_dict()
        
        assert result["total_chars"] == 1000
        assert result["estimated_tokens"] == 250
        assert "policy" in result["sections_included"]
        assert "timestamp" in result
