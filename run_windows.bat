@echo off
cd /d "%~dp0"
py -3 -m provider
if errorlevel 1 (
  echo Install Python 3.11 or newer from python.org with Tcl/Tk enabled.
  pause
)
