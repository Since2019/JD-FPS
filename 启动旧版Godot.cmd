@echo off
cd /d "%~dp0"
if exist "%USERPROFILE%\Desktop\Godot_v4.7.2-stable_win64.exe" (
  start "" "%USERPROFILE%\Desktop\Godot_v4.7.2-stable_win64.exe" --path "%~dp0."
  exit /b
)
if exist "%~dp0Godot.exe" (
  start "" "%~dp0Godot.exe" --path "%~dp0."
  exit /b
)
where godot >nul 2>nul
if not errorlevel 1 (
  start "" godot --path "%~dp0."
  exit /b
)
echo Godot was not found. Import project.godot in Godot 4, or copy Godot.exe here.
pause