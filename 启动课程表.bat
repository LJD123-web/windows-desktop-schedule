@echo off
chcp 65001 >nul 2>&1
title 悬浮窗课程表
cd /d "%~dp0"
pythonw main.py
if errorlevel 1 (
    echo.
    echo 启动失败！请检查 PySide6 是否已安装。
    echo 正在尝试用 python 启动...
    python main.py
    pause
)
