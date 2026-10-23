Option Explicit

Dim fso, shell, scriptDir, launcher, powershell, command
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
launcher = fso.BuildPath(scriptDir, "iniciar-quiqu.ps1")
powershell = shell.ExpandEnvironmentStrings("%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe")

command = """" & powershell & """ -NoProfile -ExecutionPolicy Bypass -File """ & launcher & """"

' 0 = ventana oculta; False = no esperar a que termine.
shell.Run command, 0, False
