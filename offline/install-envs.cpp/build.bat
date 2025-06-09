@echo off
::call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"

echo Compiling install_envs.cpp...

:: Check if Visual Studio compiler is available
where cl.exe >nul 2>nul
if %errorlevel% neq 0 (
    if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" (
        call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
    ) else (
        echo Visual Studio compiler not found. Please run this from a Visual Studio Developer Command Prompt.
        echo Or install Build Tools for Visual Studio 2019/2022.
        pause
        exit /b 1
    )
)

:: Compile the C++ application
cl.exe /EHsc /std:c++17 install_envs.cpp /link comctl32.lib shell32.lib gdi32.lib user32.lib kernel32.lib /SUBSYSTEM:WINDOWS /OUT:../install_envs.exe

if %errorlevel% equ 0 (
    echo Compilation successful! ../install_envs.exe has been created.
) else (
    echo Compilation failed. Please check for errors above.
)

