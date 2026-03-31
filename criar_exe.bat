@echo off
title Criando executavel...
color 0E
echo.
echo  Criando robo.exe com PyInstaller...
echo  (pode demorar 1-3 minutos)
echo.
pyinstaller --onefile --windowed --name="RoboAssistente" robo.py
echo.
if exist dist\RoboAssistente.exe (
    echo  ========================================
    echo   SUCESSO! Executavel criado em:
    echo   dist\RoboAssistente.exe
    echo  ========================================
    echo.
    echo  Copiando para pasta atual...
    copy dist\RoboAssistente.exe RoboAssistente.exe
    echo   RoboAssistente.exe criado aqui mesmo!
) else (
    echo  ERRO: Falha ao criar executavel.
    echo  Verifique se o PyInstaller foi instalado.
)
echo.
pause
