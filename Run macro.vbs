Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get path to this folder
currentFolder = fso.GetParentFolderName(WScript.ScriptFullName)

' Target .bat path
batPath = currentFolder & "\(dont touch)internal macro launcher.bat"

' Mark .bat file as hidden (File Explorer visibility only)
If fso.FileExists(batPath) Then
    fso.GetFile(batPath).Attributes = fso.GetFile(batPath).Attributes Or 2
End If

' Run the .bat file hidden (0 = hidden window)
shell.Run Chr(34) & batPath & Chr(34), 0, False
