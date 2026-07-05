"""创建桌面快捷方式

用法：python make_shortcut.py
会在桌面创建「悬浮窗课程表.lnk」快捷方式。
需要 pywin32：pip install pywin32
如果没有 pywin32，会退而创建一个 .bat 启动脚本。
"""
import os
import sys

# 桌面路径
desktop = os.path.join(os.path.expanduser("~"), "Desktop")
shortcut_path = os.path.join(desktop, "悬浮窗课程表.lnk")
workdir = os.path.dirname(os.path.abspath(__file__))

try:
    import win32com.client
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = "pythonw.exe"
    shortcut.Arguments = "main.py"
    shortcut.WorkingDirectory = workdir
    shortcut.WindowStyle = 7  # 最小化窗口
    shortcut.IconLocation = r"C:\Windows\System32\shell32.dll,13"
    shortcut.Description = "悬浮窗课程表 - 粉紫色透明玻璃风格"
    shortcut.save()
    print(f"OK: 桌面快捷方式已创建 -> {shortcut_path}")
except ImportError:
    # 没有 pywin32，用 .bat 方式
    bat_path = os.path.join(desktop, "启动课程表.bat")
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write('@echo off\n')
        f.write('chcp 65001 >nul 2>&1\n')
        f.write(f'cd /d "{workdir}"\n')
        f.write('pythonw main.py\n')
        f.write('if errorlevel 1 (\n')
        f.write('    python main.py\n')
        f.write('    pause\n')
        f.write(')\n')
    print(f"OK: 桌面启动脚本已创建 -> {bat_path}")
    print("提示：安装 pywin32 可创建 .lnk 快捷方式：pip install pywin32")
