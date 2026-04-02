@echo off
title Instalando Robo Assistente PRO v5.0
color 0B
echo.
echo  ================================================
echo    ROBO ASSISTENTE PRO v5.0 — INSTALACAO
echo  ================================================
echo.
echo [1/4] Pacotes principais...
pip install pyautogui speechrecognition pillow pyperclip
pip install requests beautifulsoup4 gtts pygame psutil
pip install pygetwindow plyer pyinstaller

echo.
echo [2/4] PyAudio para microfone...
pip install pyaudio
if errorlevel 1 (
    pip install pipwin && pipwin install pyaudio
)

echo.
echo [3/4] Tesseract OCR (opcional, para ler texto da tela)
echo  Baixe e instale em:
echo  https://github.com/UB-Mannheim/tesseract/wiki
echo  Depois instale: pip install pytesseract

echo.
echo [4/4] Pronto!
echo.
echo  ================================================
echo   Rodar:       python robo.py
echo   Criar .exe:  criar_exe.bat
echo  ================================================
pause
