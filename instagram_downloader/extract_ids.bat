@echo off
setlocal enabledelayedexpansion

:: Clear the output file first
> id.txt (
    for /f "usebackq tokens=*" %%A in ("url.txt") do (
        set "line=%%A"
        setlocal enabledelayedexpansion
        :: Remove trailing slash if it exists
        if "!line:~-1!"=="/" set "line=!line:~0,-1!"
        :: Check for /p/ or /reel/ in the URL and extract the ID
        for /f "tokens=1,2,3,4,5,6,7 delims=/" %%B in ("!line!") do (
            if /i "%%E"=="p" (
                echo %%F
            ) else if /i "%%E"=="reel" (
                echo %%F
            )
        )
        endlocal
    )
)

echo Post and Reel IDs extracted to id.txt
pause
