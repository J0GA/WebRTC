@echo off
:: Установка без компиляции (только бинарные пакеты)
python -m pip install --upgrade pip
python -m pip install --only-binary -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo Установка бинарных пакетов не удалась, пробуем альтернативный метод...
    python -m pip install aiohttp==3.11.18 --no-cache-dir
)
start python server.py
pause