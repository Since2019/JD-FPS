@echo off
setlocal
set RAID_ASSET_TRIAL=1
start "" "G:\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" "%~dp0Unreal\FactoryRaid\FactoryRaid.uproject" -ExecutePythonScript="%~dp0Unreal\FactoryRaid\Tools\play_icebreaker.py" -d3d12
endlocal
