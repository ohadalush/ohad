@echo off
rem Keeps C:\claude\nta in sync with the git repo (branch below).
rem First run clones; every later run pulls. Requires Git for Windows.
rem To make it automatic, run once:  tools\sync-local.bat --install
chcp 65001 >nul
set REPO=https://github.com/ohadalush/ohad.git
set BRANCH=claude/optimistic-fermat-vvlc0b
set DEST=C:\claude\nta

if /i "%~1"=="--install" (
  schtasks /create /f /tn "nta-sync" /sc minute /mo 15 /tr "\"%~f0\"" >nul && echo scheduled every 15 minutes: nta-sync
)

if not exist "%DEST%\.git" (
  if not exist C:\claude mkdir C:\claude
  git clone --branch %BRANCH% %REPO% "%DEST%"
) else (
  git -C "%DEST%" pull --ff-only origin %BRANCH%
)
