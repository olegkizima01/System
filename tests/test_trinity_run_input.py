import pytest

from core.trinity import TrinityRuntime, TrinityPermissions


def test_trinity_run_with_task_does_not_raise():
    """Ensure that running Trinity with a simple task does not raise the
    langgraph EmptyInputError when no explicit 'state' is provided by callers.
    """
    perms = TrinityPermissions(hyper_mode=True)
    rt = TrinityRuntime(verbose=False, permissions=perms, preferred_language="en")

    # Should complete without raising an exception
    try:
        rt.run("Open example.com in the browser", gui_mode="auto", execution_mode="native")
    except Exception as e:
        pytest.fail(f"TrinityRuntime.run raised an exception: {e}")
