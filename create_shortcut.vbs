Set WshShell = WScript.CreateObject("WScript.Shell")
strDesktop = WshShell.SpecialFolders("Desktop")
Set shortcut = WshShell.CreateShortcut(strDesktop & "\悬浮窗课程表.lnk")
shortcut.TargetPath = "pythonw.exe"
shortcut.Arguments = "main.py"
shortcut.WorkingDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
shortcut.WindowStyle = 7
shortcut.IconLocation = "C:\Windows\System32\shell32.dll,13"
shortcut.Description = "悬浮窗课程表 - 粉紫色透明玻璃风格"
shortcut.Save
WScript.Echo "Desktop shortcut created!"
