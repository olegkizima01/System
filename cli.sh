#!/bin/zsh

# Визначаємо realpath скрипта (працює з будь-якого місця)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Prefer local .venv if present; otherwise use global/pyenv Python.
if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
  source "$SCRIPT_DIR/.venv/bin/activate"
  PYTHON_EXE="$SCRIPT_DIR/.venv/bin/python"
else
  if command -v python3.11 >/dev/null 2>&1; then
    PYTHON_EXE="python3.11"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_EXE="python3"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_EXE="python"
  else
    echo "❌ Python не знайдено в PATH." >&2
    exit 1
  fi
fi

# Verify version (require 3.11+)
PY_VER=$($PYTHON_EXE -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
if [ "$PY_VER" != "3.11" ] && [ "$PY_VER" != "3.12" ] && [ "$PY_VER" != "3.13" ]; then
  echo "❌ Потрібен Python 3.11+. Зараз: ${PY_VER:-unknown}." >&2
  exit 1
fi


# Завантажуємо .env, якщо є (включаючи SUDO_PASSWORD)
if [ -f "$SCRIPT_DIR/.env" ]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${line// }" ]] && continue
    line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    if [[ "$line" =~ ^[[:alpha:]_][[:alnum:]_]*= ]]; then
      key="${line%%=*}"
      value="${line#*=}"
      value=$(echo "$value" | sed 's/^"//;s/"$//;s/^'\''//;s/'\''$//')
      export "$key=$value"
    fi
  done < "$SCRIPT_DIR/.env"
fi

# Створюємо директорію для налаштувань, якщо її немає
mkdir -p "$HOME/.system_cli"

# Якщо потрібні sudo-права (наприклад для fs_usage/dtrace), перевіряємо наявність пароля
if [ -n "$SUDO_PASSWORD" ]; then
  # Тихо перевіряємо, чи пароль працює (без інтерактивного запиту)
  echo "$SUDO_PASSWORD" | sudo -S -k true 2>/dev/null
  if [ $? -eq 0 ]; then
    export SUDO_ASKPASS="$HOME/.system_cli/.sudo_askpass"
    cat > "$SUDO_ASKPASS" <<EOF
#!/bin/bash
echo "$SUDO_PASSWORD"
EOF
    chmod 700 "$SUDO_ASKPASS"
    
    # Видаляємо старий .sudo_askpass з кореня, якщо він там лишився
    [ -f "$SCRIPT_DIR/.sudo_askpass" ] && rm "$SCRIPT_DIR/.sudo_askpass"
  else
    echo "Попередження: пароль sudo не дійсний. sudo-команди можуть не працювати." >&2
  fi
fi

export TOKENIZERS_PARALLELISM=false

# Запускаємо cli.py з усіма аргументами
"$PYTHON_EXE" "$SCRIPT_DIR/cli.py" "$@"

# Очищення при виході
if [ -f "$HOME/.system_cli/.sudo_askpass" ]; then
  rm "$HOME/.system_cli/.sudo_askpass"
fi