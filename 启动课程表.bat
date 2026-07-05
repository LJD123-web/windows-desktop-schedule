@echo off
chcp 65001 >nul 2>&1
title 悬浮窗课程表
cd /d "%~dp0"

REM 优先尝试 WorkBuddy 管理的 Python 虚拟环境
set "PYTHONW=pythonw.exe"
if exist "%USERPROFILE%\.workbuddy\binaries\python\envs\schedule\Scripts\pythonw.exe" (
    set "PYTHONW=%USERPROFILE%\.workbuddy\binaries\python\envs\schedule\Scripts\pythonw.exe"
    echo [检测到 venv，使用 %PYTHONW%]
)

%PYTHONW% main.py
if errorlevel 1 (
    echo.
    echo 启动失败！请检查 PySide6 是否已安装。
    echo 正在尝试用 python 启动...
    python main.py
    pause
)
