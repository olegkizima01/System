import os
from pathlib import Path
import fnmatch
import subprocess
from datetime import datetime
from typing import Optional

class IgnoreParser:
    def __init__(self, root: Path):
        self.root = root
        self.patterns = []  # список (pattern, negate, directory_only)
        self._load_gitignore(root)

    def _load_gitignore(self, root: Path):
        gitignore_path = root / '.gitignore'
        if not gitignore_path.exists():
            return

        with open(gitignore_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                negate = line.startswith('!')
                if negate:
                    line = line[1:]
                directory_only = line.endswith('/')
                if directory_only:
                    line = line[:-1]
                # Нормалізуємо патерн
                self.patterns.append((line, negate, directory_only))

    def is_ignored(self, path: Path) -> bool:
        rel_path = path.relative_to(self.root)
        rel_str = str(rel_path).replace('\\', '/')

        matched = False
        for pattern, negate, directory_only in self.patterns:
            # Проста fnmatch логіка з підтримкою /**/
            if '/' in pattern or pattern.startswith('**/'):
                full_pattern = pattern
            else:
                # Якщо немає / — шукаємо в будь-якій підпапці
                full_pattern = f'**/{pattern}'

            if fnmatch.fnmatch(rel_str, full_pattern) or fnmatch.fnmatch(rel_str + '/', full_pattern + '/'):
                if directory_only and not path.is_dir():
                    continue
                matched = True
                if negate:
                    return False  # ! — включаємо назад
        return matched

# Додаткові жорсткі виключення (навіть якщо не в .gitignore)
HARD_IGNORED_DIRS = {'node_modules', '__pycache__', '.git', '.venv', 'venv', 'dist', 'build', 'logs', 'cache', 'unused', '.cache', '.atlas_memory', '.pytest_cache', '.env'}
BINARY_EXTENSIONS = {'.log', '.db', '.sqlite', '.pyc', '.bin', '.pt', '.pth', '.h5', '.onnx', '.jpg', '.png', '.gif', '.mp4', '.zip', '.tar.gz', '.pdf', '.exe', '.DS_Store'}

MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 МБ — достатньо для будь-якого коду

LANGUAGE_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.jsx': 'jsx',
    '.tsx': 'tsx',
    '.json': 'json',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.md': 'markdown',
    '.sh': 'bash',
    '.bash': 'bash',
    '.zsh': 'zsh',
    '.fish': 'fish',
    '.html': 'html',
    '.css': 'css',
    '.scss': 'scss',
    '.less': 'less',
    '.sql': 'sql',
    '.xml': 'xml',
    '.toml': 'toml',
    '.ini': 'ini',
    '.cfg': 'ini',
    '.conf': 'conf',
    '.txt': 'text',
}

def get_language(file_path: Path) -> str:
    return LANGUAGE_MAP.get(file_path.suffix.lower(), 'text')

def is_binary_file(file_path: Path) -> bool:
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(8192)
            return b'\x00' in chunk
    except Exception:
        return True

def build_tree(root: Path, parser: IgnoreParser, prefix: str = "") -> list:
    lines = []
    try:
        contents = sorted(root.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    except PermissionError:
        return lines

    visible = []
    for item in contents:
        if parser.is_ignored(item) or item.name in HARD_IGNORED_DIRS or (item.is_dir() and any(ign in item.parts for ign in HARD_IGNORED_DIRS)):
            continue
        visible.append(item)

    for i, item in enumerate(visible):
        is_last = (i == len(visible) - 1)
        connector = "└── " if is_last else "├── "
        lines.append(prefix + connector + item.name + ("/" if item.is_dir() else ""))

        if item.is_dir():
            extension = "    " if is_last else "│   "
            lines.extend(build_tree(item, parser, prefix + extension))
    return lines

def get_git_diff(root: Path) -> str:
    """Get git diff output."""
    try:
        result = subprocess.run(
            ["git", "diff", "--stat"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout if result.returncode == 0 else "[Git diff unavailable]"
    except Exception as e:
        return f"[Error getting git diff: {e}]"

def get_git_log(root: Path, n: int = 5) -> str:
    """Get last n git commits."""
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", f"-{n}"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout if result.returncode == 0 else "[Git log unavailable]"
    except Exception as e:
        return f"[Error getting git log: {e}]"

def get_last_response(response_file: str = ".last_response.txt") -> str:
    """Get last response from file."""
    try:
        if os.path.exists(response_file):
            with open(response_file, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception as e:
        return f"[Error reading last response: {e}]"
    return "[No last response available]"

def get_program_logs(max_lines: int = 100) -> str:
    """Get last program execution logs from ~/.system_cli/logs/cli.log"""
    logs_dir = Path.home() / ".system_cli" / "logs"
    cli_log_file = logs_dir / "cli.log"

    if not cli_log_file.exists():
        return "[No program logs available]"

    try:
        with open(cli_log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        last_lines = lines[-max_lines:] if len(lines) > max_lines else lines

        if not last_lines:
            return "[Program logs are empty]"

        return "".join(last_lines)
    except Exception as e:
        return f"[Error reading program logs: {e}]"

def main(project_root: str = ".", output_file: str = "project_structure_final.txt", last_response: str = None):
    root = Path(project_root).resolve()

    parser = IgnoreParser(root)

    file_count = 0
    skipped = 0
    files_to_include = []

    for file_path in sorted(root.rglob("*")):
        if not file_path.is_file():
            continue
        if parser.is_ignored(file_path):
            continue
        if file_path.suffix.lower() in BINARY_EXTENSIONS:
            skipped += 1
            continue
        if any(ign in file_path.parts for ign in HARD_IGNORED_DIRS):
            skipped += 1
            continue

        size = file_path.stat().st_size
        if size > MAX_FILE_SIZE:
            skipped += 1
            continue

        if is_binary_file(file_path):
            skipped += 1
            continue

        files_to_include.append(file_path)
        file_count += 1

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# {root.name} — Project Structure\n\n")
        f.write("## Metadata\n\n")
        f.write(f"- **Project Root**: `{root}`\n")
        f.write(f"- **Files Included**: {file_count}\n")
        f.write(f"- **Files Skipped**: {skipped}\n")
        f.write(f"- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")

        f.write("## System Algorithm & Entry Points (Codemap)\n\n")
        f.write("### Entry Flow\n")
        f.write("1. **`cli.sh`**: Environment setup, Python version check, sudo permissions.\n")
        f.write("2. **`cli.py`**: Minimal wrapper, arg parsing, logging setup.\n")
        f.write("3. **`tui/cli.py`**: Main TUI application, command dispatching.\n")
        f.write("   - **Scanning**: `tui/scanning.py` (Apps/Browsers)\n")
        f.write("   - **Monitoring**: `tui/monitoring.py` & `monitoring_service.py` (Trace/DB)\n")
        f.write("   - **Agents**: `tui/agents.py` (LLM Session)\n\n")

        f.write("### Error Relevance Note\n")
        f.write("> **Note**: Errors listed below in 'Program Execution Logs' should be cross-referenced with 'Git Diff'.\n")
        f.write("> If code has changed recently (see Git Log/Diff), older errors may be obsolete.\n\n")

        f.write("---\n\n")

        f.write("## Key Scripts & Hooks\n\n")
        f.write("### Commit Hooks\n")
        f.write("- **`templates/bootstrap/post-commit`**: Automatically regenerates this structure file on commit.\n\n")
        
        f.write("### Utility Scripts (`scripts/`)\n")
        scripts_dir = root / "scripts"
        if scripts_dir.exists():
            for s in sorted(scripts_dir.rglob("*.sh")):
                f.write(f"- `{s.relative_to(root)}`\n")
            for s in sorted(scripts_dir.rglob("*.py")):
                 f.write(f"- `{s.relative_to(root)}`\n")
        f.write("\n")

        f.write("---\n\n")

        f.write("## Program Execution Logs (Last 100 lines)\n\n")
        f.write("```\n")
        program_logs = get_program_logs(max_lines=100)
        f.write(program_logs)
        f.write("```\n\n")

        f.write("---\n\n")

        if last_response:
            f.write("## Last Response\n\n")
            f.write(last_response)
            f.write("\n\n---\n\n")

        f.write("## Git Diff (Recent Changes)\n\n")
        f.write("```\n")
        f.write(get_git_diff(root))
        f.write("```\n\n")

        f.write("## Git Log (Last 5 Commits)\n\n")
        f.write("```\n")
        f.write(get_git_log(root, n=5))
        f.write("```\n\n")

        f.write("---\n\n")

        f.write("## Directory Tree\n\n")
        f.write("```\n")
        tree_lines = [root.name + "/"]
        tree_lines.extend(build_tree(root, parser))
        f.write("\n".join(tree_lines) + "\n")
        f.write("```\n\n")

        f.write("---\n\n")

        f.write("## File Contents\n\n")

        for file_path in files_to_include:
            rel_path = file_path.relative_to(root)
            language = get_language(file_path)
            size_kb = file_path.stat().st_size / 1024

            f.write(f"### `{rel_path}` ({size_kb:.1f} KB)\n\n")

            try:
                content = file_path.read_text(encoding='utf-8', errors='replace')
            except Exception as e:
                content = f"[ERROR READING FILE: {e}]"

            f.write(f"```{language}\n")
            f.write(content.rstrip("\n") + "\n")
            f.write("```\n\n")

        f.write("---\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"- **Total Files**: {file_count}\n")
        f.write(f"- **Skipped**: {skipped}\n")

    try:
        if os.path.exists(".last_response.txt"):
            subprocess.run(["git", "add", ".last_response.txt"], capture_output=True, timeout=5)
    except Exception:
        pass

if __name__ == "__main__":
    last_response = get_last_response(".last_response.txt")
    if last_response == "[No last response available]":
        last_response = None

    main(project_root=".", output_file="project_structure_final.txt", last_response=last_response)
