Set WshShell = WScript.CreateObject("WScript.Shell")
strDesktop = WshShell.SpecialFolders("Desktop")
Set shortcut = WshShell.CreateShortcut(strDesktop & "\悬浮窗课程表.lnk")
shortcut.TargetPath = "C:\Users\LENOVO\WorkBuddy\2026-07-05-12-14-18\floating-schedule\启动课程表.bat"
shortcut.WorkingDirectory = "C:\Users\LENOVO\WorkBuddy\2026-07-05-12-14-18\floating-schedule"
shortcut.WindowStyle = 7
shortcut.IconLocation = "C:\Windows\System32\shell32.dll,13"
shortcut.Description = "悬浮窗课程表 - 粉紫色透明玻璃风格"
shortcut.Save
WScript.Echo "Desktop shortcut created!"
