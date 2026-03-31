# 🤖 Robô Assistente PRO v4.0

## ⚡ Instalação rápida
1. Dê duplo clique em **`instalar_windows.bat`**
2. Execute: `python robo.py`

## 📦 Criar executável .exe
1. Dê duplo clique em **`criar_exe.bat`**
2. O arquivo `RoboAssistente.exe` aparece na mesma pasta

## 🚀 Iniciar com o Windows
- Abra o robô → aba **⚙️ CONFIG** → marque "Iniciar com Windows"
- Ou na interface, há o checkbox no cabeçalho

## 🎙 Modo voz contínuo
- Clique em **🎙 VOZ** → botão vira vermelho → fale sem parar!
- Após cada comando ele processa e volta a ouvir automaticamente
- Para desativar: clique no botão novamente

## 🗣 Voz natural (gTTS)
- Usa Google TTS — voz muito mais natural que o pyttsx3
- Precisa de internet
- Fallback automático para voz offline se sem internet

## 🌤 Saudação inteligente
- Bom dia (05h–12h), Boa tarde (12h–18h), Boa noite (18h–05h)

## Exemplos de comandos novos
| Fale | O que faz |
|---|---|
| "previsão do tempo nos próximos 7 dias" | Clima detalhado por wttr.in |
| "clima em Curitiba" | Clima de qualquer cidade |
| "notícias do dia" | Google News RSS |
| "notícias sobre futebol" | Notícias filtradas |
| "traduz 'good morning' para português" | MyMemory API |
| "como se diz obrigado em japonês" | Tradução direta |
| "quanto é 1250 * 3 + 400" | Cálculo instantâneo |
| "converte 50 dólares para reais" | Cotação ao vivo |
| "100°F para celsius" | Conversão de temperatura |
| "o que é fotossíntese" | Resposta da web |
| "quem foi Darwin" | Busca Google snippet |

## Dependências
```
pip install pyautogui speechrecognition pillow pyperclip requests
pip install beautifulsoup4 gtts pygame pyinstaller pyaudio
```
