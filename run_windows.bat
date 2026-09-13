@echo off
chcp 65001 >nul
cd /d "%~dp0"
py -3 -X utf8 -m provider
if errorlevel 1 (
  echo ثبّت Python 3.11 أو أحدث من python.org مع تفعيل Tcl/Tk.
  echo Install Python 3.11 or newer from python.org with Tcl/Tk enabled.
  pause
)
