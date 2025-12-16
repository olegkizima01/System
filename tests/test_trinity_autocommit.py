import os
import subprocess
from pathlib import Path

import pytest
from langchain_core.messages import AIMessage

from core.trinity import TrinityRuntime


def _run(cmd, *, cwd: Path, env: dict) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True)
    assert proc.returncode == 0, f"Command failed: {cmd}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    return proc


class _DummyWorkflow:
    def stream(self, _initial_state, config=None):
        _ = config
        yield {"atlas": {"messages": [AIMessage(content="ok")], "current_agent": "end", "task_status": "completed"}}


def test_trinity_auto_commit_on_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("COPILOT_API_KEY", "dummy")

    env = os.environ.copy()
    env.setdefault("GIT_AUTHOR_NAME", "Trinity")
    env.setdefault("GIT_AUTHOR_EMAIL", "trinity@example.com")
    env.setdefault("GIT_COMMITTER_NAME", env["GIT_AUTHOR_NAME"])
    env.setdefault("GIT_COMMITTER_EMAIL", env["GIT_AUTHOR_EMAIL"])

    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)

    _run(["git", "init"], cwd=repo, env=env)

    regenerate = repo / "regenerate_structure.sh"
    regenerate.write_text(
        "#!/bin/bash\n"
        "set -e\n"
        "echo 'structure' > project_structure_final.txt\n",
        encoding="utf-8",
    )
    regenerate.chmod(0o755)

    (repo / "some_change.txt").write_text("x", encoding="utf-8")

    monkeypatch.chdir(repo)

    rt = TrinityRuntime(verbose=False)
    rt.workflow = _DummyWorkflow()

    events = list(rt.run("Зроби зміну у файлі some_change.txt"))
    final = events[-1]
    report = final["atlas"]["messages"][1].content

    head = _run(["git", "rev-parse", "HEAD"], cwd=repo, env=env).stdout.strip()
    assert head
    assert head in report
    assert "Зміни закомічені:" in report

    subject = _run(["git", "log", "-1", "--pretty=%s"], cwd=repo, env=env).stdout.strip()
    assert subject.startswith("Trinity task completed: ")

    names = _run(["git", "show", "--name-only", "--pretty=format:", "HEAD"], cwd=repo, env=env).stdout.splitlines()
    assert "some_change.txt" in names
    assert "project_structure_final.txt" in names

    status = _run(["git", "status", "--porcelain"], cwd=repo, env=env).stdout.strip()
    assert status == ""
