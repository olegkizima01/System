"""Parallel Tool Executor

Enables parallel execution of independent steps in Trinity Runtime.
Analyzes step dependencies and executes non-dependent steps concurrently.

Features:
- Dependency graph analysis
- Async parallel execution
- Result aggregation with ordering
- Configurable concurrency limits
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from enum import Enum
import threading
import concurrent.futures
import os


class StepStatus(Enum):
    """Status of a step execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepResult:
    """Result of a single step execution."""
    step_id: int
    status: StepStatus
    result: Any = None
    error: Optional[str] = None
    duration_ms: float = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


@dataclass
class DependencyGraph:
    """Represents dependencies between steps."""
    # step_id -> list of step_ids this step depends on
    dependencies: Dict[int, Set[int]] = field(default_factory=dict)
    # step_id -> list of step_ids that depend on this step
    dependents: Dict[int, Set[int]] = field(default_factory=dict)
    
    def add_dependency(self, step_id: int, depends_on: int) -> None:
        """Add a dependency: step_id depends on depends_on."""
        if step_id not in self.dependencies:
            self.dependencies[step_id] = set()
        self.dependencies[step_id].add(depends_on)
        
        if depends_on not in self.dependents:
            self.dependents[depends_on] = set()
        self.dependents[depends_on].add(step_id)
    
    def get_dependencies(self, step_id: int) -> Set[int]:
        """Get all steps this step depends on."""
        return self.dependencies.get(step_id, set())
    
    def get_dependents(self, step_id: int) -> Set[int]:
        """Get all steps that depend on this step."""
        return self.dependents.get(step_id, set())
    
    def get_independent_steps(self, step_ids: List[int], completed: Set[int]) -> List[int]:
        """Get steps that have all dependencies satisfied."""
        independent = []
        for step_id in step_ids:
            deps = self.get_dependencies(step_id)
            if deps.issubset(completed):
                independent.append(step_id)
        return independent


class DependencyAnalyzer:
    """Analyzes step definitions to determine dependencies."""
    
    # Tool pairs that are typically dependent
    DEPENDENT_TOOL_PATTERNS = {
        ("open_app", "click"),  # Must open app before clicking
        ("open_app", "type_text"),  # Must open app before typing
        ("browser_open_url", "browser_click_element"),
        ("browser_open_url", "browser_type_text"),
        ("take_screenshot", "vision_analyze"),
        ("write_file", "read_file"),  # If same file
    }
    
    # Tools that are typically independent
    INDEPENDENT_TOOLS = {
        "get_clipboard",
        "get_monitors_info",
        "get_open_windows",
        "list_processes",
        "get_system_stats"
    }
    
    def analyze(self, steps: List[Dict[str, Any]]) -> DependencyGraph:
        """
        Analyze steps and build dependency graph.
        
        Args:
            steps: List of step definitions with 'id', 'tool', 'args', etc.
            
        Returns:
            DependencyGraph showing step dependencies
        """
        graph = DependencyGraph()
        
        # Ensure all steps have IDs
        for i, step in enumerate(steps):
            if "id" not in step:
                step["id"] = i + 1
        
        # Analyze each step pair for dependencies
        for i, step in enumerate(steps):
            step_id = step.get("id", i + 1)
            step_tool = step.get("tool", "").lower()
            step_args = step.get("args", {})
            
            # Check against all previous steps
            for j in range(i):
                prev_step = steps[j]
                prev_id = prev_step.get("id", j + 1)
                prev_tool = prev_step.get("tool", "").lower()
                prev_args = prev_step.get("args", {})
                
                if self._has_dependency(step_tool, step_args, prev_tool, prev_args):
                    graph.add_dependency(step_id, prev_id)
        
        return graph
    
    def _has_dependency(
        self,
        tool: str,
        args: Dict,
        prev_tool: str,
        prev_args: Dict
    ) -> bool:
        """Check if tool depends on prev_tool."""
        
        # Check known dependent patterns
        if (prev_tool, tool) in self.DEPENDENT_TOOL_PATTERNS:
            return True
        
        # Check if both are independent tools (no dependencies between them)
        if tool in self.INDEPENDENT_TOOLS and prev_tool in self.INDEPENDENT_TOOLS:
            return False
        
        # Check file-based dependencies
        if self._has_file_dependency(tool, args, prev_tool, prev_args):
            return True
        
        # Check app-based dependencies
        if self._has_app_dependency(tool, args, prev_tool, prev_args):
            return True
        
        # Default: assume sequential dependency for safety
        # This ensures correctness at cost of some parallelism
        return True
    
    def _has_file_dependency(
        self,
        tool: str,
        args: Dict,
        prev_tool: str,
        prev_args: Dict
    ) -> bool:
        """Check if there's a file-based dependency."""
        file_tools = {"read_file", "write_file", "copy_file"}
        
        if tool in file_tools and prev_tool in file_tools:
            # Same file = dependency
            file1 = args.get("path", args.get("file", ""))
            file2 = prev_args.get("path", prev_args.get("file", ""))
            if file1 and file2 and file1 == file2:
                return True
            
            # Write before read on same file
            if prev_tool == "write_file" and tool == "read_file":
                if file1 == file2:
                    return True
        
        return False
    
    def _has_app_dependency(
        self,
        tool: str,
        args: Dict,
        prev_tool: str,
        prev_args: Dict
    ) -> bool:
        """Check if there's an app-based dependency."""
        app_opener_tools = {"open_app", "native_open_app", "activate_app"}
        app_interaction_tools = {"click", "type_text", "press_key", "native_click_ui"}
        
        if prev_tool in app_opener_tools and tool in app_interaction_tools:
            # Opening app then interacting = dependency
            return True
        
        return False


StepExecutor = Callable[[Dict[str, Any]], Any]


class ParallelToolExecutor:
    """
    Executes independent steps in parallel.
    
    Features:
    - Dependency analysis
    - Parallel execution batches
    - Result aggregation
    - Ordering preservation
    """
    
    DEFAULT_MAX_WORKERS = 4
    
    def __init__(
        self,
        executor: StepExecutor,
        max_workers: Optional[int] = None,
        verbose: bool = False
    ):
        """
        Args:
            executor: Function to execute individual steps
            max_workers: Max parallel workers (default: 4)
            verbose: Enable verbose logging
        """
        self.executor = executor
        self.max_workers = max_workers or int(os.getenv("PARALLEL_MAX_WORKERS", self.DEFAULT_MAX_WORKERS))
        self.verbose = verbose
        self.analyzer = DependencyAnalyzer()
        self._results: Dict[int, StepResult] = {}
        self._lock = threading.Lock()
    
    def execute_parallel(
        self,
        steps: List[Dict[str, Any]],
        stop_on_error: bool = True
    ) -> List[StepResult]:
        """
        Execute steps with parallel optimization.
        
        Args:
            steps: List of step definitions
            stop_on_error: Stop all execution if any step fails
            
        Returns:
            List of StepResults in original step order
        """
        if not steps:
            return []
        
        # Analyze dependencies
        graph = self.analyzer.analyze(steps)
        
        if self.verbose:
            print(f"[ParallelExecutor] Analyzing {len(steps)} steps...")
        
        # Track completion
        completed: Set[int] = set()
        pending = [s.get("id", i + 1) for i, s in enumerate(steps)]
        step_map = {s.get("id", i + 1): s for i, s in enumerate(steps)}
        
        # Execute in batches
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            while pending:
                # Find steps ready to execute
                ready = graph.get_independent_steps(pending, completed)
                
                if not ready:
                    if self.verbose:
                        print(f"[ParallelExecutor] No ready steps. Pending: {pending}")
                    # If nothing is ready but we have pending, force sequential
                    ready = [pending[0]]
                
                # Limit batch size
                batch = ready[:self.max_workers]
                
                if self.verbose:
                    print(f"[ParallelExecutor] Executing batch: {batch}")
                
                # Submit batch
                futures = {
                    pool.submit(self._execute_step, step_map[step_id]): step_id
                    for step_id in batch
                }
                
                # Wait for batch completion
                error_occurred = False
                for future in concurrent.futures.as_completed(futures):
                    step_id = futures[future]
                    result = future.result()
                    
                    with self._lock:
                        self._results[step_id] = result
                    
                    completed.add(step_id)
                    pending.remove(step_id)
                    
                    if result.status == StepStatus.FAILED:
                        error_occurred = True
                        if self.verbose:
                            print(f"[ParallelExecutor] Step {step_id} failed: {result.error}")
                
                if error_occurred and stop_on_error:
                    # Mark remaining as skipped
                    for step_id in pending:
                        with self._lock:
                            self._results[step_id] = StepResult(
                                step_id=step_id,
                                status=StepStatus.SKIPPED,
                                error="Skipped due to previous failure"
                            )
                    break
        
        # Return results in original order
        return [self._results.get(s.get("id", i + 1)) for i, s in enumerate(steps)]
    
    def _execute_step(self, step: Dict[str, Any]) -> StepResult:
        """Execute a single step."""
        step_id = step.get("id", 0)
        started_at = datetime.now()
        
        try:
            result = self.executor(step)
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds() * 1000
            
            return StepResult(
                step_id=step_id,
                status=StepStatus.COMPLETED,
                result=result,
                duration_ms=duration,
                started_at=started_at,
                completed_at=completed_at
            )
        except Exception as e:
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds() * 1000
            
            return StepResult(
                step_id=step_id,
                status=StepStatus.FAILED,
                error=str(e),
                duration_ms=duration,
                started_at=started_at,
                completed_at=completed_at
            )
    
    async def execute_parallel_async(
        self,
        steps: List[Dict[str, Any]],
        stop_on_error: bool = True
    ) -> List[StepResult]:
        """
        Async version of parallel execution.
        
        Useful when the executor is also async.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: self.execute_parallel(steps, stop_on_error)
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        with self._lock:
            if not self._results:
                return {"executed": 0}
            
            completed = sum(1 for r in self._results.values() if r.status == StepStatus.COMPLETED)
            failed = sum(1 for r in self._results.values() if r.status == StepStatus.FAILED)
            skipped = sum(1 for r in self._results.values() if r.status == StepStatus.SKIPPED)
            
            durations = [r.duration_ms for r in self._results.values() if r.duration_ms > 0]
            
            return {
                "total_steps": len(self._results),
                "completed": completed,
                "failed": failed,
                "skipped": skipped,
                "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
                "max_duration_ms": max(durations) if durations else 0,
                "max_workers": self.max_workers
            }
    
    def clear_results(self) -> None:
        """Clear stored results."""
        with self._lock:
            self._results.clear()


# Environment variable to enable/disable parallel execution
PARALLEL_ENABLED = os.getenv("ENABLE_PARALLEL", "true").lower() == "true"


def create_parallel_executor(
    executor: StepExecutor,
    max_workers: Optional[int] = None,
    verbose: bool = False
) -> ParallelToolExecutor:
    """Factory function to create parallel executor."""
    return ParallelToolExecutor(
        executor=executor,
        max_workers=max_workers,
        verbose=verbose
    )
