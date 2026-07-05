"""创建桌面快捷方式"""
import os
import sys

# 桌面路径
desktop = os.path.join(os.path.expanduser("~"), "Desktop")
shortcut_path = os.path.join(desktop, "悬浮窗课程表.lnk")
target = os.path.join(os.path.dirname(os.path.abspath(__file__)), "启动课程表.bat")
workdir = os.path.dirname(os.path.abspath(__file__))

try:
    import win32com.client
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = target
    shortcut.WorkingDirectory = workdir
    shortcut.WindowStyle = 7  # 最小化窗口
    shortcut.IconLocation = r"C:\Windows\System32\shell32.dll,13"
    shortcut.Description = "悬浮窗课程表 - 粉紫色透明玻璃风格"
    shortcut.save()
    print(f"OK: 桌面快捷方式已创建 -> {shortcut_path}")
except ImportError:
    # 没有 pywin32，用 ctypes 方式
    import ctypes
    import ctypes.wintypes
    import struct

    # IShellLink + IPersistFile 方式太复杂，退而求其次用 .bat
    bat_path = os.path.join(desktop, "启动课程表.bat")
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write('@echo off\n')
        f.write('chcp 65001 >nul 2>&1\n')
        f.write(f'cd /d "{workdir}"\n')
        f.write(f'""C:\\Users\\LENOVO\\.workbuddy\\binaries\\python\\envs\\schedule\\Scripts\\pythonw.exe" main.py"\n')
        f.write('if errorlevel 1 (\n')
        f.write('    "C:\\Users\\LENOVO\\.workbuddy\\binaries\\python\\envs\\schedule\\Scripts\\python.exe" main.py\n')
        f.write('    pause\n')
        f.write(')\n')
    print(f"OK: 桌面启动脚本已创建 -> {bat_path}")
