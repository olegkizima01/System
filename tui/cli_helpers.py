
import sys

def parse_natural_language_args(argv: list[str]) -> list[str]:
    """
    Transforms natural language arguments into a structured command if applicable.
    
    If the first argument is not a known command and doesn't start with '-',
    it treats the arguments as an agent chat message.
    """
    if len(argv) <= 1:
        return argv

    global_flags = {"-v", "--verbose"}
    i = 1
    while i < len(argv) and argv[i] in global_flags:
        i += 1

    if i >= len(argv):
        return argv

    first_arg = argv[i]

    try:
        from tui.cli import get_cli_known_commands
        known_commands = get_cli_known_commands()
    except Exception:
        known_commands = {
            "tui", "list-editors", "list-modules", "run", "enable", "disable",
            "install", "smart-plan", "ask", "agent-chat", "agent-reset",
            "agent-on", "agent-off", "self-healing-status", "self-healing-scan",
            "vibe-status", "vibe-continue", "vibe-cancel", "vibe-help",
            "eternal-engine", "screenshots",
            "-h", "--help", "-v", "--verbose",
        }

    if first_arg not in known_commands and not first_arg.startswith("-"):
        # Treat as agent-chat message
        # Reconstruct argv to: cli.py agent-chat --message "all args joined"
        message = " ".join(argv[i:])
        preserved = argv[1:i]
        return [argv[0], *preserved, "agent-chat", "--message", message]
    
    return argv
