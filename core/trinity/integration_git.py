import os
import subprocess
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

class IntegrationGitMixin:
    """Mixin for TrinityRuntime containing Git integration logic."""

    def _get_git_root(self) -> Optional[str]:
        try:
            proc = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                return None
            root = (proc.stdout or "").strip()
            return root or None
        except Exception:
            return None

    def _get_repo_changes(self) -> Dict[str, Any]:
        """Get git repository changes."""
        root = self._get_git_root()
        if not root:
            return {"ok": False, "error": "not_a_git_repo"}

        try:
            diff_name = subprocess.run(["git", "diff", "--name-only"], cwd=root, capture_output=True, text=True)
            status = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True)
            diff_stat = subprocess.run(["git", "diff", "--stat"], cwd=root, capture_output=True, text=True)

            changed_files = self._collect_changed_files(diff_name, status)
            deduped = self._dedupe_files(changed_files)

            return {
                "ok": True, "git_root": root, "changed_files": deduped,
                "diff_stat": (diff_stat.stdout or "").strip() if diff_stat.returncode == 0 else "",
                "status_porcelain": (status.stdout or "").strip() if status.returncode == 0 else "",
            }
        except Exception as e:
            if self.verbose:
                print(f"[Trinity][ERROR] _get_repo_changes exception: {e}")
            return {"ok": False, "error": str(e)}

    def _collect_changed_files(self, diff_name, status) -> List[str]:
        """Collect changed files from git commands."""
        files = []
        if diff_name.returncode == 0:
            files.extend([l.strip() for l in (diff_name.stdout or "").splitlines() if l.strip()])
        if status.returncode == 0:
            for line in (status.stdout or "").splitlines():
                s = line.strip()
                if s:
                    parts = s.split(maxsplit=1)
                    if len(parts) == 2:
                        files.append(parts[1].strip())
        return files

    def _dedupe_files(self, files: List[str]) -> List[str]:
        """Deduplicate file list while preserving order."""
        seen = set()
        result = []
        for f in files:
            if f not in seen:
                seen.add(f)
                result.append(f)
        return result

    def _short_task_for_commit(self, task: str, max_len: int = 72) -> str:
        t = re.sub(r"\\s+", " ", str(task or "").strip())
        if not t:
            return "(no task)"
        if len(t) <= max_len:
            return t
        cut = t[: max_len - 1].rstrip()
        return cut + "…"

    def _auto_commit_on_success(self, *, task: str, report: str, repo_changes: Dict[str, Any]) -> Dict[str, Any]:
        """Auto-commit changes on successful task completion."""
        root = self._get_git_root()
        if not root:
            return {"ok": False, "error": "not_a_git_repo"}

        try:
            # Preserve the initial observed changed files snapshot
            initial_changed = list(repo_changes.get("changed_files") or [])
            prev = getattr(self, "_last_seen_changed_files", []) or []
            combined = list(dict.fromkeys(prev + initial_changed))
            self._last_seen_changed_files = combined
            
            env = self._prepare_git_env()

            # Check if there are changes
            status = self._run_git_command(["git", "status", "--porcelain"], root, env)
            if status.returncode != 0:
                return {"ok": False, "error": (status.stderr or "").strip() or "git status failed"}

            has_changes = bool((status.stdout or "").strip())

            # Create commit
            if self.verbose:
                print(f"[Trinity] auto_commit: repo_changes={repo_changes}")
            self._deterministic_log("commit", f"starting create_commit; repo_changes={repo_changes}")
            
            return self._create_commit(root, env, task, repo_changes, has_changes)
            
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _prepare_git_env(self) -> Dict[str, str]:
        """Prepare git environment with Trinity author info."""
        env = os.environ.copy()
        env.setdefault("GIT_AUTHOR_NAME", "Trinity")
        env.setdefault("GIT_AUTHOR_EMAIL", "trinity@local")
        env.setdefault("GIT_COMMITTER_NAME", env["GIT_AUTHOR_NAME"])
        env.setdefault("GIT_COMMITTER_EMAIL", env["GIT_AUTHOR_EMAIL"])
        return env

    def _deterministic_log(self, tag: str, message: str) -> None:
        """Log a deterministic, timestamped message for git operations."""
        ts = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        if hasattr(self, "logger"):
            self.logger.info(f"[Trinity][TS:{ts}] {tag} - {message}")

    def _run_git_command(self, cmd: List[str], cwd: str, env: Dict[str, str]) -> subprocess.CompletedProcess:
        """Run a git command and return result."""
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)

    def _create_commit(self, root: str, env: Dict[str, str], task: str, 
                       repo_changes: Dict[str, Any], has_changes: bool) -> Dict[str, Any]:
        """Create git commit with task info."""
        # Stage all changes
        try:
            if isinstance(repo_changes, dict):
                changed = repo_changes.get("changed_files") or []
                status = self._run_git_command(["git", "status", "--porcelain"], root, env)
                untracked = []
                if status.returncode == 0:
                    for line in (status.stdout or '').splitlines():
                        if line.startswith('?? '):
                            fname = line[3:].strip()
                            untracked.append(fname)
                files_to_add = list(dict.fromkeys(list(changed) + untracked))
                for f in files_to_add:
                    self._run_git_command(["git", "add", f], root, env)
        except Exception as e:
            if self.verbose:
                print(f"[Trinity] _create_commit: failed staging changed files: {e}")

        # Always run a final 'git add .' to ensure untracked files are picked up
        self._run_git_command(["git", "add", "."], root, env)

        # Check if there are staged changes (ready to commit)
        diff_index = self._run_git_command(["git", "diff", "--cached", "--name-only"], root, env)
        if not (diff_index.stdout or '').strip():
            return {"ok": True, "skipped": True, "reason": "no_staged_changes"}

        # Prepare commit message
        short_task = self._short_task_for_commit(task)
        subject = f"Trinity task completed: {short_task}"
        diff_stat = str(repo_changes.get("diff_stat") or "").strip() if isinstance(repo_changes, dict) else ""

        commit_cmd = [
            "git", "-c", "user.name=Trinity", "-c", "user.email=trinity@local",
            "commit", "-m", subject,
        ]
        if diff_stat:
            commit_cmd.extend(["-m", f"Diff stat:\\n{diff_stat}"])

        env_commit = env.copy()
        env_commit["TRINITY_POST_COMMIT_RUNNING"] = "1"
        commit = self._run_git_command(commit_cmd, root, env_commit)

        if commit.returncode != 0:
            combined = (commit.stdout or "") + "\\n" + (commit.stderr or "")
            if "nothing to commit" in combined.lower():
                return {"ok": True, "skipped": True, "reason": "nothing_to_commit"}
            return {"ok": False, "error": (commit.stderr or "").strip() or "git commit failed"}

        # Log commit contents for diagnostics
        try:
            files_in_head = self._run_git_command(["git", "show", "--name-only", "--pretty=format:", "HEAD"], root, env)
            if hasattr(self, "logger"):
                self.logger.info(f"[Trinity] _create_commit: HEAD files after commit: {(files_in_head.stdout or '').splitlines()}")
        except Exception:
            pass

        return {"ok": True, "skipped": False}
