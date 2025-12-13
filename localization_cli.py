#!/usr/bin/env python3
"""legacy wrapper

Цей файл залишений для сумісності.
Основний єдиний інтерфейс тепер: cli.py
"""

import os
import subprocess
import sys


def main() -> None:
    script_dir = os.path.abspath(os.path.dirname(__file__))
    target = os.path.join(script_dir, "cli.py")
    if not os.path.exists(target):
        print("cli.py не знайдено поруч з localization_cli.py", file=sys.stderr)
        raise SystemExit(1)
    raise SystemExit(subprocess.call([sys.executable, target] + sys.argv[1:], cwd=script_dir))


if __name__ == "__main__":
    main()
