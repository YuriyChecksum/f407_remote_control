
# Example Python script for exchange data with STM32F407 microcontroller

Пример кода взаимодействия программы на python с контроллером STM32F407 через com port.

## Как установить и запустить
### Clone repo
```bash
git clone https://github.com/YuriyChecksum/f407_remote_control.git
cd f407_remote_control/Python
```

### Если стоит чистый python
```shell
# обновим менеджер пакетов pip
python.exe -m pip install --upgrade pip

# Создадим виртуальное окружение в подпапке .venv
python -m venv .venv

# Активируем виртуальное окружение
.venv\Scripts\activate

# Установим зависимости
python -m pip install -U -r requirements.txt

# Run
python main.py
```

### Если установлен пакетный менеджер UV
```shell
uv sync --no-cache
uv run backend/app/main.py
```

### Установка uv под windows
```shell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Create requirements
```shell
# create requirements.txt
python -m pip freeze > requirements.txt
```
