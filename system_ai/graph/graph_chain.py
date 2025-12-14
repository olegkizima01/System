from typing import Any, Dict


class GoalGraph:
    def __init__(
        self,
        *,
        plan_step: Any,
        act_step: Any,
        observe_step: Any,
        verify_step: Any,
    ) -> None:
        self._plan_step = plan_step
        self._act_step = act_step
        self._observe_step = observe_step
        self._verify_step = verify_step

    def run(self, goal: str, *, max_steps: int) -> Any:
        step = 0
        last_plan = None
        last_results = None
        last_observation = ""
        done = False

        while step < int(max_steps) and not done:
            next_step = step + 1
            try:
                last_plan = self._plan_step(goal, step=next_step)
            except TypeError:
                last_plan = self._plan_step(goal)

            try:
                last_results = self._act_step(getattr(last_plan, "actions", []) if last_plan else [], step=next_step)
            except TypeError:
                last_results = self._act_step(getattr(last_plan, "actions", []) if last_plan else [])

            try:
                last_observation = self._observe_step(last_results, step=next_step)
            except TypeError:
                last_observation = self._observe_step(last_results)

            try:
                verify = self._verify_step(goal, last_plan, last_results, last_observation, step=next_step)
            except TypeError:
                verify = self._verify_step(goal, last_plan, last_results, last_observation)

            step = next_step
            done = bool(getattr(last_plan, "done", False))
            if isinstance(verify, dict) and "done" in verify:
                done = bool(verify.get("done"))

            yield {
                "step": step,
                "plan": last_plan,
                "actions_results": last_results,
                "observation": last_observation,
                "verify": verify,
                "done": done,
            }


def is_langgraph_available() -> bool:
    try:
        import langgraph  # noqa: F401

        return True
    except Exception:
        return False


def build_placeholder_graph() -> Dict[str, Any]:
    """Placeholder to keep folder structure stable.

    Later we will replace with a real LangGraph state machine.
    """
    return {"ok": True, "type": "placeholder", "langgraph": is_langgraph_available()}


def build_goal_graph(*, plan_step: Any, act_step: Any, observe_step: Any, verify_step: Any) -> GoalGraph:
    return GoalGraph(plan_step=plan_step, act_step=act_step, observe_step=observe_step, verify_step=verify_step)
