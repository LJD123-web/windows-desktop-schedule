@echo off
chcp 65001 >nul 2>&1
title 悬浮窗课程表
cd /d "%~dp0"
"C:\Users\LENOVO\.workbuddy\binaries\python\envs\schedule\Scripts\pythonw.exe" main.py
if errorlevel 1 (
    echo.
    echo 启动失败！请检查 PySide6 是否已安装。
    echo 正在尝试用备用 Python 启动...
    "C:\Users\LENOVO\.workbuddy\binaries\python\envs\schedule\Scripts\python.exe" main.py
    pause
)
