@echo off
start "" "G:\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" "%~dp0Unreal\FactoryRaid\FactoryRaid.uproject" -ExecutePythonScript="%~dp0Unreal\FactoryRaid\Tools\play_tactical.py" -nosplash
