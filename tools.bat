@echo off
setlocal enabledelayedexpansion

set DIR=%~dp0
set DIR=%DIR:~0,-1%
set VENV=%DIR%\.venv
set PYTHON=%VENV%\Scripts\python.exe

if not exist "%VENV%" (
    echo Creating virtual environment...
    python -m venv "%VENV%"
)

"%PYTHON%" -m pip install --quiet -e .

if not exist "%DIR%\config.json" (
    echo(
    echo Config not found. Enter your Elite Dangerous journal directory path.
    set /p JRNL_PATH="Journal path: "
    if "!JRNL_PATH!"=="" (
        echo Path cannot be empty.
        exit /b 1
    )
    echo(
    set /p INARA_KEY="Optional: Inara API key (press Enter to skip): "
    echo(
    set /p EDSM_KEY="Optional: EDSM API key (press Enter to skip): "

    > "%TEMP%\spectr_setup.py" echo import json, os
    >> "%TEMP%\spectr_setup.py" echo cfg = {'journal_path': os.environ.get('JRNL_PATH', '')}
    >> "%TEMP%\spectr_setup.py" echo inara = os.environ.get('INARA_KEY', '')
    >> "%TEMP%\spectr_setup.py" echo if inara:
    >> "%TEMP%\spectr_setup.py" echo     cfg['inara'] = {'api_key': inara, 'api_url': 'https://api.inara.cz/v1/'}
    >> "%TEMP%\spectr_setup.py" echo edsm = os.environ.get('EDSM_KEY', '')
    >> "%TEMP%\spectr_setup.py" echo if edsm:
    >> "%TEMP%\spectr_setup.py" echo     cfg['edsm'] = {'api_key': edsm, 'api_url': 'https://www.edsm.net/api/'}
    >> "%TEMP%\spectr_setup.py" echo with open(r'%DIR%\config.json', 'w') as f:
    >> "%TEMP%\spectr_setup.py" echo     json.dump(cfg, f, indent=2)
    "%PYTHON%" "%TEMP%\spectr_setup.py"
    del "%TEMP%\spectr_setup.py"
    echo Config saved to config.json
)

rem Auto-populate database
if not exist "%DIR%\blackbox.db" if exist "%DIR%\config.json" (
    for /f "delims=" %%a in ('%PYTHON% -c "import json; p=json.load(open(r'%DIR%/config.json')).get('journal_path',''); print(p)"') do set JRNL=%%a
    if not "!JRNL!"=="" (
        echo No blackbox.db found. Scanning journals...
        "%PYTHON%" -m blackbox record --once --journal-dir "!JRNL!"
    )
)

if not "%~1"=="" (
    if /i "%~1"=="blackbox" "%PYTHON%" -m blackbox %2 %3 %4 %5 %6 %7 %8 %9 & exit /b
    if /i "%~1"=="lrs" "%PYTHON%" -m long_range_sensor %2 %3 %4 %5 %6 %7 %8 %9 & exit /b
    if /i "%~1"=="web" "%VENV%\Scripts\uvicorn" webui.server:app --host 0.0.0.0 --port 8000 %2 %3 %4 %5 %6 %7 %8 %9 & exit /b
    if /i "%~1"=="ship" "%PYTHON%" -m ship_status %2 %3 %4 %5 %6 %7 %8 %9 & exit /b
    if /i "%~1"=="missions" "%PYTHON%" -m missions %2 %3 %4 %5 %6 %7 %8 %9 & exit /b
    echo Unknown tool: %~1
    echo Available: blackbox, lrs, web, ship, missions
    exit /b 1
)

for /f %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"

:menu
cls
setlocal DISABLEDELAYEDEXPANSION
echo %ESC%[90m@@@@@@   @@@@@@@   @@@@@@@@   @@@@@@@  @@@@@@@  @@@@@@@%ESC%[0m
echo %ESC%[90m@@@@@@@   @@@@@@@@  @@@@@@@@  @@@@@@@@  @@@@@@@  @@@@@@@@%ESC%[0m
echo %ESC%[90m!@@       @@!  @@@  @@!       !@@         @@!    @@!  @@@%ESC%[0m
echo %ESC%[90m!@!       !@!  @!@  !@!       !@!         !@!    !@!  @!@%ESC%[0m
echo %ESC%[90m!!@@!!    @!@@!@!   @!!!:!    !@!         @!!    @!@!!@!%ESC%[0m
echo %ESC%[90m !!@!!!   !!@!!!    !!!!!:    !!!         !!!    !!@!@!%ESC%[0m
echo %ESC%[90m     !:!  !!:       !!:       :!!         !!:    !!: :!!%ESC%[0m
echo %ESC%[90m    !:!   :!:       :!:       :!:         :!:    :!:  !:!%ESC%[0m
echo %ESC%[90m:::: ::    ::        :: ::::   ::: :::     ::    ::   :::%ESC%[0m
echo %ESC%[90m:: : :     :        : :: ::    :: :: :     :      :   : :%ESC%[0m
endlocal
echo(
echo %ESC%[1;33mSPECTR — Elite Dangerous Tool Suite%ESC%[0m
echo(
echo   1)  %ESC%[36mblackbox%ESC%[0m  — Black Box flight recorder
echo   2)  %ESC%[32mlrs%ESC%[0m       — Long Range Sensor: nearby services
echo   3)  %ESC%[33mweb%ESC%[0m        — Web UI server (cockpit + blackbox + ship + missions)
echo   4)  %ESC%[34mship%ESC%[0m       — Ship status: hull, shields, module health
echo   5)  %ESC%[35mmissions%ESC%[0m   — Mission monitor: active, failed, completed
echo   q)  %ESC%[31mQuit%ESC%[0m
echo(
set /p choice="Select tool: "

if /i "!choice!"=="q" echo Bye. & exit /b
if "!choice!"=="1" "%PYTHON%" -m blackbox & goto menu
if "!choice!"=="2" "%PYTHON%" -m long_range_sensor & goto menu
if "!choice!"=="3" "%VENV%\Scripts\uvicorn" webui.server:app --host 0.0.0.0 --port 8000 & goto menu
if "!choice!"=="4" "%PYTHON%" -m ship_status & goto menu
if "!choice!"=="5" "%PYTHON%" -m missions & goto menu
echo Invalid choice.
goto menu
