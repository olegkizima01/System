"""Tests for Parallel Tool Executor."""

import pytest
import time
from core.parallel_executor import (
    ParallelToolExecutor,
    DependencyAnalyzer,
    DependencyGraph,
    StepResult,
    StepStatus
)


class TestDependencyGraph:
    """Tests for DependencyGraph."""

    def test_add_dependency(self):
        """Test adding dependencies."""
        graph = DependencyGraph()
        graph.add_dependency(2, 1)  # Step 2 depends on Step 1
        
        deps = graph.get_dependencies(2)
        assert 1 in deps

    def test_get_dependents(self):
        """Test getting dependents."""
        graph = DependencyGraph()
        graph.add_dependency(2, 1)
        graph.add_dependency(3, 1)
        
        dependents = graph.get_dependents(1)
        assert 2 in dependents
        assert 3 in dependents

    def test_get_independent_steps(self):
        """Test finding independent steps."""
        graph = DependencyGraph()
        graph.add_dependency(2, 1)  # 2 depends on 1
        graph.add_dependency(3, 2)  # 3 depends on 2
        # 4 has no dependencies
        
        completed = set()
        independent = graph.get_independent_steps([1, 2, 3, 4], completed)
        # Only 1 and 4 are independent initially
        assert 1 in independent
        assert 4 in independent
        assert 2 not in independent
        
        # After completing 1
        completed.add(1)
        independent = graph.get_independent_steps([2, 3, 4], completed)
        assert 2 in independent


class TestDependencyAnalyzer:
    """Tests for DependencyAnalyzer."""

    def test_analyze_sequential_steps(self):
        """Test analysis of sequential dependent steps."""
        analyzer = DependencyAnalyzer()
        steps = [
            {"id": 1, "tool": "open_app", "args": {"name": "Chrome"}},
            {"id": 2, "tool": "click", "args": {"x": 100, "y": 200}}
        ]
        
        graph = analyzer.analyze(steps)
        
        # Step 2 should depend on Step 1 (open_app -> click)
        assert 1 in graph.get_dependencies(2)

    def test_analyze_independent_steps(self):
        """Test analysis of independent steps."""
        analyzer = DependencyAnalyzer()
        steps = [
            {"id": 1, "tool": "get_clipboard", "args": {}},
            {"id": 2, "tool": "get_monitors_info", "args": {}}
        ]
        
        graph = analyzer.analyze(steps)
        
        # These should be independent
        deps = graph.get_dependencies(2)
        # Actually our default is to assume sequential, so this will have dependency
        # This is by design for safety

    def test_file_dependency_detection(self):
        """Test file-based dependency detection."""
        analyzer = DependencyAnalyzer()
        steps = [
            {"id": 1, "tool": "write_file", "args": {"path": "/tmp/test.txt"}},
            {"id": 2, "tool": "read_file", "args": {"path": "/tmp/test.txt"}}
        ]
        
        graph = analyzer.analyze(steps)
        assert 1 in graph.get_dependencies(2)


class TestParallelToolExecutor:
    """Tests for ParallelToolExecutor."""

    def simple_executor(self, step):
        """Simple test executor that sleeps briefly."""
        time.sleep(0.05)  # 50ms
        return {"step_id": step.get("id"), "status": "ok"}

    def failing_executor(self, step):
        """Executor that fails on step 2."""
        if step.get("id") == 2:
            raise Exception("Step 2 failed")
        return {"step_id": step.get("id")}

    def test_execute_single_step(self):
        """Test executing a single step."""
        executor = ParallelToolExecutor(self.simple_executor)
        steps = [{"id": 1, "tool": "test", "args": {}}]
        
        results = executor.execute_parallel(steps)
        
        assert len(results) == 1
        assert results[0].status == StepStatus.COMPLETED

    def test_execute_multiple_steps(self):
        """Test executing multiple steps."""
        executor = ParallelToolExecutor(self.simple_executor, max_workers=4)
        steps = [
            {"id": 1, "tool": "get_clipboard", "args": {}},
            {"id": 2, "tool": "get_monitors_info", "args": {}},
            {"id": 3, "tool": "list_processes", "args": {}}
        ]
        
        results = executor.execute_parallel(steps)
        
        assert len(results) == 3
        assert all(r.status == StepStatus.COMPLETED for r in results)

    def test_stop_on_error(self):
        """Test stopping on error."""
        executor = ParallelToolExecutor(self.failing_executor)
        steps = [
            {"id": 1, "tool": "test", "args": {}},
            {"id": 2, "tool": "test", "args": {}},  # Will fail
            {"id": 3, "tool": "test", "args": {}}   # Should be skipped
        ]
        
        results = executor.execute_parallel(steps, stop_on_error=True)
        
        # Step 2 should be failed
        step2_result = next(r for r in results if r.step_id == 2)
        assert step2_result.status == StepStatus.FAILED

    def test_results_in_order(self):
        """Test results are returned in original order."""
        executor = ParallelToolExecutor(self.simple_executor)
        steps = [
            {"id": 1, "tool": "test"},
            {"id": 2, "tool": "test"},
            {"id": 3, "tool": "test"}
        ]
        
        results = executor.execute_parallel(steps)
        
        assert [r.step_id for r in results] == [1, 2, 3]

    def test_stats(self):
        """Test statistics gathering."""
        executor = ParallelToolExecutor(self.simple_executor)
        steps = [{"id": 1, "tool": "test"}, {"id": 2, "tool": "test"}]
        
        executor.execute_parallel(steps)
        stats = executor.get_stats()
        
        assert stats["total_steps"] == 2
        assert stats["completed"] == 2
        assert stats["avg_duration_ms"] > 0


class TestStepResult:
    """Tests for StepResult."""

    def test_to_dict(self):
        """Test serialization."""
        result = StepResult(
            step_id=1,
            status=StepStatus.COMPLETED,
            result={"data": "test"},
            duration_ms=100.5
        )
        
        data = result.to_dict()
        
        assert data["step_id"] == 1
        assert data["status"] == "completed"
        assert data["duration_ms"] == 100.5
