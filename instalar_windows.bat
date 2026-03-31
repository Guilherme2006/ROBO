@echo off
title Instalando Robo Assistente PRO v4.0
color 0B
echo.
echo  ========================================
echo    ROBO ASSISTENTE PRO v4.0 - INSTALACAO
echo  ========================================
echo.
echo [1/3] Instalando dependencias principais...
pip install pyautogui speechrecognition pillow pyperclip requests beautifulsoup4 gtts pygame pyinstaller
echo.
echo [2/3] Instalando PyAudio para microfone...
pip install pyaudio
if errorlevel 1 (
    echo  Tentando pipwin para PyAudio...
    pip install pipwin
    pipwin install pyaudio
)
echo.
echo [3/3] Pronto!
echo.
echo  ========================================
echo    Para RODAR:     python robo.py
echo    Para criar EXE: criar_exe.bat
echo  ========================================
echo.
pause
