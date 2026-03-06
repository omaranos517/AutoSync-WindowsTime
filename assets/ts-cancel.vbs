Set objShell = CreateObject("WScript.Shell")
objShell.Run Chr(34) & WScript.ScriptFullName & "\..\timesync-gui.exe" & Chr(34) & " cancel", 0, True