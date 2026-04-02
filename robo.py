"""
╔══════════════════════════════════════════════════════════════╗
║          🤖 ROBÔ ASSISTENTE PRO v5.0                         ║
║  Wake word · Agenda · OCR · Clipboard · Stats · Auto-click   ║
║  Ditado · Senhas · Arquivos · Apps · Monitor · Web summary   ║
╚══════════════════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
import threading, time, subprocess, webbrowser
import json, os, re, sys, tempfile, shutil, math, string, secrets
import random, glob, winreg, ctypes
from datetime import datetime, timedelta
from difflib import SequenceMatcher
import urllib.parse, urllib.request
from collections import deque

import pyautogui, pyperclip
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3

# ── Dependências opcionais ─────────────────────────────────────────────────
try:
    import speech_recognition as sr
    VOZ_OK = True
except ImportError:
    VOZ_OK = False

try:
    from gtts import gTTS
    import pygame
    pygame.mixer.init()
    GTTS_OK = True
except Exception:
    GTTS_OK = False

try:
    import pyttsx3
    _tts_off = pyttsx3.init()
    _tts_off.setProperty('rate', 162)
    for v in _tts_off.getProperty('voices'):
        if any(x in v.id.lower() for x in ['pt','brazil','portuguese']):
            _tts_off.setProperty('voice', v.id); break
    TTS_OFF_OK = True
except Exception:
    TTS_OFF_OK = False

try:
    import psutil
    PSUTIL_OK = True
except ImportError:
    PSUTIL_OK = False

try:
    import pytesseract
    from PIL import Image, ImageGrab
    OCR_OK = True
except Exception:
    OCR_OK = False

try:
    from PIL import Image, ImageGrab
    PIL_OK = True
except Exception:
    PIL_OK = False

try:
    from bs4 import BeautifulSoup
    BS4_OK = True
except ImportError:
    BS4_OK = False

try:
    import pygetwindow as gw
    PYGW_OK = True
except Exception:
    PYGW_OK = False

try:
    from plyer import notification
    PLYER_OK = True
except Exception:
    PLYER_OK = False

try:
    import requests
    REQ_OK = True
except ImportError:
    REQ_OK = False

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
HIST_FILE   = os.path.join(BASE_DIR, "historico.json")
MACROS_FILE = os.path.join(BASE_DIR, "macros.json")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
NOTAS_FILE  = os.path.join(BASE_DIR, "notas.txt")
AGENDA_FILE = os.path.join(BASE_DIR, "agenda.json")
APP_NAME    = "RoboAssistentePRO"
APP_EXE     = sys.executable if getattr(sys,'frozen',False) else os.path.abspath(__file__)

# ══════════════════════════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════════════════════════
DEFAULT_CFG = {
    "voz_continua": False, "resposta_voz": True, "idioma_voz": "pt-BR",
    "iniciar_com_windows": False, "usar_gtts": True,
    "cidade_clima": "São Paulo", "wake_word": "hey robô",
    "wake_word_ativo": False,
}

def load_cfg():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE,"r",encoding="utf-8") as f:
                return {**DEFAULT_CFG, **json.load(f)}
        except: pass
    return dict(DEFAULT_CFG)

def save_cfg(c):
    with open(CONFIG_FILE,"w",encoding="utf-8") as f:
        json.dump(c, f, ensure_ascii=False, indent=2)

CFG = load_cfg()

# ══════════════════════════════════════════════════════════════════════════
#  VOZ — gTTS natural + pyttsx3 fallback
# ══════════════════════════════════════════════════════════════════════════
_fala_lock = threading.Lock()

def falar(texto: str):
    if not CFG.get("resposta_voz", True): return
    def _run():
        with _fala_lock:
            limpo = re.sub(r'[╔╗╚╝║╠╣═─►●⬤▶📝🎵🌐🔍⌨️🖱️🎬⏰📸✅❌⚠️📋💬🎙🔴🗑🧮💱🌤📅📰🔎⚙️🔒🖥️📦📋🔑]','',texto)
            limpo = re.sub(r'\[.*?\]','',limpo).strip()
            if not limpo or len(limpo) < 2: return
            if GTTS_OK and CFG.get("usar_gtts",True):
                try:
                    tmp = tempfile.NamedTemporaryFile(suffix=".mp3",delete=False)
                    tmp.close()
                    gTTS(text=limpo[:500],lang='pt',slow=False).save(tmp.name)
                    pygame.mixer.music.load(tmp.name)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy(): time.sleep(0.05)
                    pygame.mixer.music.unload()
                    os.unlink(tmp.name)
                    return
                except: pass
            if TTS_OFF_OK:
                try: _tts_off.say(limpo[:300]); _tts_off.runAndWait()
                except: pass
    threading.Thread(target=_run, daemon=True).start()

# ══════════════════════════════════════════════════════════════════════════
#  SAUDAÇÃO
# ══════════════════════════════════════════════════════════════════════════
def saudacao():
    h = datetime.now().hour
    p = "Bom dia" if 5<=h<12 else "Boa tarde" if 12<=h<18 else "Boa noite"
    return f"{p}! Sou seu Robô Assistente PRO v5. Em que posso ajudar?"

# ══════════════════════════════════════════════════════════════════════════
#  AUTOSTART
# ══════════════════════════════════════════════════════════════════════════
def toggle_autostart(ativar):
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        if ativar:
            cmd = f'pythonw "{APP_EXE}"' if not getattr(sys,'frozen',False) else f'"{APP_EXE}"'
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try: winreg.DeleteValue(key, APP_NAME)
            except: pass
        winreg.CloseKey(key)
        CFG["iniciar_com_windows"] = ativar
        save_cfg(CFG)
        return True
    except: return False

def check_autostart():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_READ)
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except: return False

# ══════════════════════════════════════════════════════════════════════════
#  HELPERS HTTP
# ══════════════════════════════════════════════════════════════════════════
HEADERS = {
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language":"pt-BR,pt;q=0.9"
}

def _fetch(url, timeout=8):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="ignore")
    except: return None

# ══════════════════════════════════════════════════════════════════════════
#  MÓDULOS NOVOS v5
# ══════════════════════════════════════════════════════════════════════════

# ── 1. GERENCIADOR DE CLIPBOARD ───────────────────────────────────────────
class ClipboardManager:
    def __init__(self):
        self.historico = deque(maxlen=20)
        self._ultimo   = ""
        self._monitor  = True
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while self._monitor:
            try:
                atual = pyperclip.paste()
                if atual and atual != self._ultimo and len(atual.strip()) > 0:
                    self._ultimo = atual
                    if not self.historico or self.historico[-1] != atual:
                        self.historico.append(atual)
            except: pass
            time.sleep(0.8)

    def listar(self, n=5):
        itens = list(self.historico)
        itens.reverse()
        return itens[:n]

    def colar_idx(self, idx: int):
        itens = list(self.historico)
        itens.reverse()
        if 0 <= idx < len(itens):
            pyperclip.copy(itens[idx])
            pyautogui.hotkey('ctrl','v')
            return itens[idx]
        return None

CLIPBOARD = ClipboardManager()

# ── 2. AGENDA / LEMBRETES ─────────────────────────────────────────────────
class Agenda:
    def __init__(self, notif_cb):
        self.lembretes  = self._load()
        self.notif_cb   = notif_cb
        self._ativo     = True
        threading.Thread(target=self._loop, daemon=True).start()

    def _load(self):
        if os.path.exists(AGENDA_FILE):
            try:
                with open(AGENDA_FILE,"r",encoding="utf-8") as f:
                    return json.load(f)
            except: pass
        return []

    def _save(self):
        with open(AGENDA_FILE,"w",encoding="utf-8") as f:
            json.dump(self.lembretes, f, ensure_ascii=False, indent=2)

    def adicionar(self, texto: str, quando: str) -> str:
        """quando = 'HH:MM' ou '30 minutos' ou 'X horas'"""
        agora = datetime.now()
        try:
            if re.match(r'\d{1,2}:\d{2}', quando):
                h, m = map(int, quando.split(':'))
                dt = agora.replace(hour=h, minute=m, second=0, microsecond=0)
                if dt < agora: dt += timedelta(days=1)
            elif 'minuto' in quando:
                mins = int(re.search(r'\d+', quando).group())
                dt = agora + timedelta(minutes=mins)
            elif 'hora' in quando:
                horas = int(re.search(r'\d+', quando).group())
                dt = agora + timedelta(hours=horas)
            elif 'segundo' in quando:
                segs = int(re.search(r'\d+', quando).group())
                dt = agora + timedelta(seconds=segs)
            else:
                return "❌ Não entendi o horário. Ex: 'às 15:30' ou 'em 30 minutos'"
        except:
            return "❌ Formato de horário inválido."

        lembrete = {"texto": texto, "dt": dt.strftime("%Y-%m-%d %H:%M:%S"), "disparado": False}
        self.lembretes.append(lembrete)
        self._save()
        diff = dt - agora
        mins = int(diff.total_seconds() // 60)
        return f"✅ Lembrete criado para {dt.strftime('%H:%M')} ({mins} min)"

    def _loop(self):
        while self._ativo:
            agora = datetime.now()
            mudou = False
            for lem in self.lembretes:
                if not lem["disparado"]:
                    dt = datetime.strptime(lem["dt"], "%Y-%m-%d %H:%M:%S")
                    if agora >= dt:
                        lem["disparado"] = True
                        mudou = True
                        self.notif_cb(lem["texto"])
            if mudou: self._save()
            # Limpa disparados há mais de 1h
            self.lembretes = [
                l for l in self.lembretes
                if not l["disparado"] or
                   (datetime.now() - datetime.strptime(l["dt"],"%Y-%m-%d %H:%M:%S")).seconds < 3600
            ]
            time.sleep(10)

    def listar(self):
        ativos = [l for l in self.lembretes if not l["disparado"]]
        return ativos

    def limpar(self):
        self.lembretes = []
        self._save()

# ── 3. STATUS DO SISTEMA ─────────────────────────────────────────────────
def status_sistema() -> str:
    if not PSUTIL_OK:
        return "❌ Instale psutil: pip install psutil"
    cpu  = psutil.cpu_percent(interval=0.5)
    ram  = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    try:
        net = psutil.net_io_counters()
        net_str = f"↑{net.bytes_sent//1024//1024}MB ↓{net.bytes_recv//1024//1024}MB"
    except: net_str = "N/A"
    linhas = [
        f"🖥️  STATUS DO SISTEMA",
        f"  CPU:   {cpu:.1f}%  ({'OK' if cpu<80 else '⚠️ alto'})",
        f"  RAM:   {ram.percent:.1f}%  ({ram.used//1024//1024}MB / {ram.total//1024//1024}MB)",
        f"  DISCO: {disk.percent:.1f}%  ({disk.free//1024//1024//1024}GB livres)",
        f"  REDE:  {net_str}",
    ]
    try:
        bat = psutil.sensors_battery()
        if bat:
            st = "🔌 carregando" if bat.power_plugged else "🔋 bateria"
            linhas.append(f"  BATT:  {bat.percent:.0f}% {st}")
    except: pass
    return "\n".join(linhas)

def status_resumo() -> str:
    if not PSUTIL_OK: return "psutil não instalado"
    cpu = psutil.cpu_percent(interval=0.3)
    ram = psutil.virtual_memory()
    return f"CPU em {cpu:.0f}% e memória em {ram.percent:.0f}%"

# ── 4. OCR — LER TEXTO DA TELA ───────────────────────────────────────────
def ler_tela_ocr(area=None) -> str:
    if not OCR_OK:
        return ("❌ Para OCR instale: pip install pytesseract pillow\n"
                "   E também Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")
    try:
        img = ImageGrab.grab(bbox=area)
        texto = pytesseract.image_to_string(img, lang='por+eng')
        texto = texto.strip()
        if texto:
            return f"📄 Texto lido da tela:\n{texto}"
        return "❌ Nenhum texto encontrado na tela."
    except Exception as e:
        return f"❌ Erro no OCR: {e}"

# ── 5. BUSCA DE APPS INSTALADOS ───────────────────────────────────────────
_APPS_CACHE: dict[str,str] = {}

def _scan_apps():
    """Varre Start Menu e Program Files por .exe e .lnk"""
    global _APPS_CACHE
    encontrados = {}
    pastas = [
        os.path.join(os.environ.get("ProgramFiles","C:\\Program Files")),
        os.path.join(os.environ.get("ProgramFiles(x86)","C:\\Program Files (x86)")),
        os.path.join(os.environ.get("APPDATA",""),r"Microsoft\Windows\Start Menu\Programs"),
        os.path.join(os.environ.get("ProgramData",""),r"Microsoft\Windows\Start Menu\Programs"),
        os.path.join(os.path.expanduser("~"), "Desktop"),
    ]
    for pasta in pastas:
        if not os.path.exists(pasta): continue
        for raiz, dirs, arqs in os.walk(pasta):
            for arq in arqs:
                if arq.lower().endswith(('.exe','.lnk')):
                    nome = os.path.splitext(arq)[0].lower()
                    caminho = os.path.join(raiz, arq)
                    encontrados[nome] = caminho
    _APPS_CACHE = encontrados

def abrir_app_por_nome(nome: str) -> str:
    nome_n = _n(nome.lower().strip())
    # Busca exata
    if nome_n in _APPS_CACHE:
        try: subprocess.Popen(_APPS_CACHE[nome_n], shell=True); return f"✅ Abrindo {nome}!"
        except: pass
    # Busca parcial
    for chave, caminho in _APPS_CACHE.items():
        if nome_n in _n(chave) or _n(chave) in nome_n:
            try: subprocess.Popen(caminho, shell=True); return f"✅ Abrindo {chave}!"
            except: pass
    # Tenta direto
    try: subprocess.Popen(nome, shell=True); return f"✅ Tentando abrir {nome}..."
    except: pass
    return f"❌ App '{nome}' não encontrado. Verifique o nome."

threading.Thread(target=_scan_apps, daemon=True).start()

# ── 6. BUSCA DE ARQUIVOS ─────────────────────────────────────────────────
def buscar_arquivo(nome: str) -> list[str]:
    resultados = []
    pastas = [
        os.path.expanduser("~"),
        os.path.join(os.path.expanduser("~"), "Desktop"),
        os.path.join(os.path.expanduser("~"), "Documents"),
        os.path.join(os.path.expanduser("~"), "Downloads"),
    ]
    nome_n = _n(nome.lower())
    for pasta in pastas:
        for raiz, dirs, arqs in os.walk(pasta):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for arq in arqs:
                if nome_n in _n(arq.lower()):
                    resultados.append(os.path.join(raiz, arq))
                if len(resultados) >= 10: return resultados
    return resultados

# ── 7. GERADOR DE SENHAS ─────────────────────────────────────────────────
def gerar_senha(comprimento=16, simbolos=True, numeros=True, maiusculas=True) -> str:
    chars = string.ascii_lowercase
    obrigatorios = []
    if maiusculas:
        chars += string.ascii_uppercase
        obrigatorios.append(secrets.choice(string.ascii_uppercase))
    if numeros:
        chars += string.digits
        obrigatorios.append(secrets.choice(string.digits))
    if simbolos:
        sym = "!@#$%^&*()-_=+[]{}|;:,.<>?"
        chars += sym
        obrigatorios.append(secrets.choice(sym))
    resto = [secrets.choice(chars) for _ in range(comprimento - len(obrigatorios))]
    senha_lista = obrigatorios + resto
    secrets.SystemRandom().shuffle(senha_lista)
    return ''.join(senha_lista)

# ── 8. AUTO-CLICKER ──────────────────────────────────────────────────────
class AutoClicker:
    def __init__(self):
        self._ativo = False
        self._thread = None

    def iniciar(self, vezes=10, intervalo=1.0, botao='left'):
        if self._ativo: return
        self._ativo = True
        def _run():
            for i in range(vezes):
                if not self._ativo: break
                pyautogui.click(button=botao)
                time.sleep(intervalo)
            self._ativo = False
        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def parar(self):
        self._ativo = False

AUTO_CLICKER = AutoClicker()

# ── 9. RESUMO DE PÁGINA WEB ──────────────────────────────────────────────
def resumir_pagina(url: str) -> str:
    html = _fetch(url, timeout=10)
    if not html: return "❌ Não consegui acessar a página."
    if BS4_OK:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script","style","nav","footer","header","aside"]): tag.decompose()
        paragrafos = [p.get_text(strip=True) for p in soup.find_all('p') if len(p.get_text(strip=True)) > 60]
        titulo = soup.title.string.strip() if soup.title else "Sem título"
        texto = " ".join(paragrafos[:6])[:800]
        if texto:
            return f"📄 {titulo}\n\n{texto}..."
    # Fallback sem BS4
    texto = re.sub(r'<[^>]+>','', html)
    texto = re.sub(r'\s+',' ', texto).strip()[:600]
    return f"📄 Conteúdo:\n{texto}..."

def pegar_url_ativa() -> str | None:
    """Tenta pegar a URL da barra de endereços do Chrome/Edge/Firefox via clipboard hack"""
    try:
        pyautogui.hotkey('ctrl','l')
        time.sleep(0.3)
        pyautogui.hotkey('ctrl','c')
        time.sleep(0.2)
        url = pyperclip.paste()
        pyautogui.press('escape')
        if url and url.startswith('http'):
            return url
    except: pass
    return None

# ── 10. CLIMA ─────────────────────────────────────────────────────────────
def buscar_clima(cidade: str, dias: int = 1) -> str:
    try:
        cidade_enc = urllib.parse.quote(cidade)
        if dias <= 1:
            html = _fetch(f"https://wttr.in/{cidade_enc}?format=3&lang=pt")
            if html: return f"🌤️ {html.strip()}"
        url = f"https://wttr.in/{cidade_enc}?format=j1"
        html = _fetch(url)
        if html:
            data = json.loads(html)
            weather = data.get("weather", [])
            linhas = [f"📅 Previsão para {cidade} ({min(dias,len(weather))} dias):"]
            cmap = {"Sunny":"☀️ Ensolarado","Clear":"☀️ Limpo","Partly cloudy":"⛅ Nublado",
                    "Cloudy":"☁️ Nublado","Rain":"🌧️ Chuva","Heavy rain":"⛈️ Chuva forte",
                    "Thundery outbreaks":"⛈️ Trovoadas","Snow":"❄️ Neve","Fog":"🌫️ Névoa"}
            for day in weather[:min(dias,7)]:
                dt = day.get("date","")
                try: dt_fmt = datetime.strptime(dt,"%Y-%m-%d").strftime("%d/%m")
                except: dt_fmt = dt
                tmax = day.get("maxtempC","?"); tmin = day.get("mintempC","?")
                desc_en = day.get("hourly",[{}])[4].get("weatherDesc",[{}])[0].get("value","")
                desc = cmap.get(desc_en, desc_en or "–")
                chuva = day.get("hourly",[{}])[4].get("chanceofrain","0")
                linhas.append(f"  {dt_fmt}: {desc} {tmin}–{tmax}°C 🌧{chuva}%")
            return "\n".join(linhas)
    except: pass
    return f"❌ Não consegui buscar clima de '{cidade}'."

# ── 11. NOTÍCIAS ──────────────────────────────────────────────────────────
def buscar_noticias(tema="") -> str:
    try:
        q = urllib.parse.quote(tema if tema else "brasil")
        url = f"https://news.google.com/rss/search?q={q}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        html = _fetch(url)
        if not html: return "❌ Sem notícias."
        titulos = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>',html)
        if not titulos: titulos = re.findall(r'<title>(.*?)</title>',html)
        titulos = [t for t in titulos if t and "Google News" not in t][:6]
        if not titulos: return "❌ Nenhuma notícia."
        header = f"📰 Notícias{' sobre '+tema if tema else ' do dia'}:"
        return header + "\n" + "\n".join(f"  • {t}" for t in titulos)
    except: return "❌ Erro ao buscar notícias."

# ── 12. TRADUÇÃO ──────────────────────────────────────────────────────────
def traduzir(texto: str, para="en") -> str:
    try:
        url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(texto[:500])}&langpair=pt|{para}"
        html = _fetch(url)
        if html:
            data = json.loads(html)
            trad = data.get("responseData",{}).get("translatedText","")
            if trad:
                nomes = {"en":"inglês","es":"espanhol","fr":"francês","de":"alemão",
                         "it":"italiano","ja":"japonês","zh":"chinês","ru":"russo","ar":"árabe"}
                return f"🌐 {nomes.get(para,para)}: \"{trad}\""
    except: pass
    return "❌ Não consegui traduzir."

def detectar_lang(cmd): 
    m = {"inglês":"en","ingles":"en","espanhol":"es","frances":"fr","francês":"fr",
         "alemão":"de","alemao":"de","italiano":"it","japonês":"ja","japones":"ja",
         "chinês":"zh","chines":"zh","russo":"ru","árabe":"ar","portugues":"pt","português":"pt"}
    cl = cmd.lower()
    for p,c in m.items():
        if p in cl: return c
    return "en"

# ── 13. CÁLCULO / CONVERSÃO ───────────────────────────────────────────────
def calcular(expr: str) -> str:
    try:
        e = re.sub(r'[^\d\+\-\*\/\(\)\.\%\s]',' ',expr).replace(',','.').strip()
        if re.match(r'^[\d\s\+\-\*\/\(\)\.\%]+$', e):
            r = eval(e, {"__builtins__":{}}, {})
            if isinstance(r,float) and r==int(r): r=int(r)
            return f"🧮 {expr.strip()} = {r}"
    except: pass
    return f"❌ Não consegui calcular."

def converter_unidade(expr: str):
    el = expr.lower()
    m = re.search(r'([\d\.,]+)\s*(?:graus\s*)?(celsius|°c)\s*(?:para|em)\s*(fahrenheit|°f)',el)
    if m:
        c=float(m.group(1).replace(',','.')); return f"🌡️ {c}°C = {c*9/5+32:.1f}°F"
    m = re.search(r'([\d\.,]+)\s*(fahrenheit|°f)\s*(?:para|em)\s*(celsius|°c)',el)
    if m:
        f2=float(m.group(1).replace(',','.')); return f"🌡️ {f2}°F = {(f2-32)*5/9:.1f}°C"
    m = re.search(r'([\d\.,]+)\s*km\s*(?:para|em)\s*milhas',el)
    if m: km=float(m.group(1).replace(',','.')); return f"📏 {km} km = {km*0.621371:.2f} mi"
    m = re.search(r'([\d\.,]+)\s*milhas?\s*(?:para|em)\s*km',el)
    if m: mi=float(m.group(1).replace(',','.')); return f"📏 {mi} mi = {mi*1.60934:.2f} km"
    m = re.search(r'([\d\.,]+)\s*kg\s*(?:para|em)\s*(libras|lb)',el)
    if m: kg=float(m.group(1).replace(',','.')); return f"⚖️ {kg}kg = {kg*2.20462:.2f}lb"
    # Moeda
    mc = re.search(r'([\d\.,]+)\s*(dolar|dólar|usd|euro|eur|real|brl)\s*(?:para|em|é quanto em|em)\s*(dolar|dólar|usd|euro|eur|real|brl|reais)',el)
    if mc:
        mapa = {"dolar":"USD","dólar":"USD","usd":"USD","euro":"EUR","eur":"EUR",
                "real":"BRL","brl":"BRL","reais":"BRL"}
        v=float(mc.group(1).replace(',','.')); de=mapa.get(mc.group(2),"USD"); pa=mapa.get(mc.group(3),"BRL")
        try:
            html = _fetch(f"https://api.frankfurter.app/latest?amount={v}&from={de}&to={pa}")
            if html:
                r2 = json.loads(html).get("rates",{}).get(pa)
                if r2: return f"💱 {v} {de} = {r2:.2f} {pa}"
        except: pass
    return None

# ── 14. PERGUNTA GERAL (Google snippet) ──────────────────────────────────
def perguntar_web(q: str):
    try:
        html = _fetch(f"https://www.google.com.br/search?q={urllib.parse.quote(q)}&hl=pt-BR")
        if not html: return None
        if BS4_OK:
            soup = BeautifulSoup(html,"html.parser")
            for sel in ["div.BNeawe.s3v9rd.AP7Wnd","div.BNeawe.iBp4i.AP7Wnd",
                        "span.hgKElc","div.ILfuVd","div.ayRjaf"]:
                el = soup.select_one(sel)
                if el:
                    t = el.get_text(strip=True)[:400]
                    if len(t)>15: return f"🔎 {t}"
            for el in soup.select("div.VwiC3b,div.s3v9rd"):
                t = el.get_text(strip=True)
                if len(t)>20: return f"🔎 {t[:400]}"
    except: pass
    return None

# ── 15. YouTube ───────────────────────────────────────────────────────────
def buscar_yt(termo):
    try:
        html = _fetch(f"https://www.youtube.com/results?search_query={urllib.parse.quote(termo)}")
        if html:
            ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"',html)
            if ids: return f"https://www.youtube.com/watch?v={ids[0]}"
    except: pass
    return None

# ══════════════════════════════════════════════════════════════════════════
#  HISTÓRICO & MACROS
# ══════════════════════════════════════════════════════════════════════════
class Historico:
    def __init__(self):
        self.dados = self._load()
    def _load(self):
        if os.path.exists(HIST_FILE):
            try:
                with open(HIST_FILE,"r",encoding="utf-8") as f: return json.load(f)
            except: pass
        return []
    def salvar(self,cmd):
        self.dados = [x for x in self.dados if x["cmd"].lower()!=cmd.lower()]
        self.dados.insert(0,{"cmd":cmd,"ts":datetime.now().strftime("%d/%m %H:%M")})
        self.dados = self.dados[:100]
        try:
            with open(HIST_FILE,"w",encoding="utf-8") as f: json.dump(self.dados,f,ensure_ascii=False,indent=2)
        except: pass
    def limpar(self):
        self.dados=[]
        try: os.remove(HIST_FILE)
        except: pass
    def recentes(self,n=30): return self.dados[:n]

class Macros:
    def __init__(self):
        self.dados=self._load()
    def _load(self):
        if os.path.exists(MACROS_FILE):
            try:
                with open(MACROS_FILE,"r",encoding="utf-8") as f: return json.load(f)
            except: pass
        return {}
    def _save(self):
        with open(MACROS_FILE,"w",encoding="utf-8") as f: json.dump(self.dados,f,ensure_ascii=False,indent=2)
    def adicionar(self,nome,cmds): self.dados[nome.lower()]=cmds; self._save()
    def remover(self,nome):
        if nome.lower() in self.dados: del self.dados[nome.lower()]; self._save(); return True
        return False
    def listar(self): return self.dados

# ══════════════════════════════════════════════════════════════════════════
#  MOTOR DE INTENÇÕES
# ══════════════════════════════════════════════════════════════════════════
def _n(t):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD',t.lower())
                   if unicodedata.category(c)!='Mn')

INTENCOES = [
    # ── Novidades v5 ──────────────────────────────────────────────────────
    (["status do pc","como esta o pc","uso de cpu","uso de memoria",
      "uso de ram","status do sistema","como ta o computador"],       "status_pc",      False),
    (["le o texto da tela","le a tela","leia a tela","ocr",
      "copia o texto da imagem","texto da tela","lê a tela",
      "lê o texto","transcreve a tela"],                              "ocr_tela",       False),
    (["lembra me","lembra eu","cria lembrete","adiciona lembrete",
      "me avisa","cria alarme","coloca um lembrete"],                  "criar_lembrete", True),
    (["mostra lembretes","ver lembretes","meus lembretes",
      "agenda","o que tenho"],                                         "ver_lembretes",  False),
    (["limpa lembretes","apaga lembretes"],                           "limpar_lembretes",False),
    (["mostra clipboard","historico de copia","o que copiei",
      "historico clipboard","o que esta no clipboard"],                "ver_clipboard",  False),
    (["cola o","cola item","cola o segundo","cola o primeiro",
      "cola o terceiro","cola o ultimo"],                             "colar_clipboard", True),
    (["clica automatico","auto clicker","auto-clicker",
      "clica vezes","clica automaticamente"],                          "auto_click",     True),
    (["para de clicar","stop auto clicker","para o auto clicker",
      "cancela o clique"],                                             "stop_click",     False),
    (["gera senha","criar senha","gere uma senha","nova senha",
      "senha segura","senha forte"],                                   "gerar_senha",    True),
    (["começa a ditar","inicia ditado","modo ditado",
      "comecar a ditar","quero ditar"],                               "iniciar_ditado", False),
    (["termina o ditado","fim do ditado","parar ditado",
      "terminar ditado","finaliza ditado"],                           "parar_ditado",   False),
    (["resume essa pagina","resume a pagina","resumo da pagina",
      "do que se trata esse artigo","resume o site",
      "resume essa aba"],                                              "resumir_pagina", False),
    (["resume o site","resume o link","resume a url"],                "resumir_url",    True),
    (["move a janela para outro monitor","outro monitor",
      "passa para o segundo monitor","muda de monitor"],              "mover_monitor",   False),
    (["lista apps","apps instalados","quais apps tenho"],             "listar_apps",    False),
    (["abre o app","abrir o app","abre o programa","abre o aplicativo",
      "inicia o","executa o"],                                         "abrir_app",      True),
    (["encontra o arquivo","abre o arquivo","procura o arquivo",
      "busca o arquivo","encontra o arquivo"],                        "buscar_arquivo", True),
    # ── v4 mantidos ───────────────────────────────────────────────────────
    (["previsao do tempo","previsão do tempo","clima de","tempo em",
      "como esta o tempo","vai chover","temperatura em"],             "clima",          True),
    (["noticias","notícias","manchetes","o que aconteceu"],           "noticias",       True),
    (["traduz","traduzir","como se diz","como fala",
      "em ingles","em espanhol","traducao de"],                       "traduzir",       True),
    (["quanto e","quanto é","calcul","resultado de"],                 "calcular",       True),
    (["converte","converter","em fahrenheit","em celsius",
      "dolar para","euro para","cotacao"],                            "converter",      True),
    (["que horas sao","que horas são","horas","hora atual"],         "hora_atual",     False),
    (["que dia e hoje","que dia é hoje","data de hoje"],             "data_atual",     False),
    (["toca ","play ","reproduz ","abre a musica ","quero ouvir ",
      "quero ver ","bota ","me mostra ","coloca "],                   "play_video",     True),
    (["pesquisa no youtube","busca no youtube"],                      "pesquisar_yt",   True),
    (["abre o google","vai no google","entra no google"],             "abrir_google",   False),
    (["abre o youtube","vai no youtube","entra no youtube"],          "abrir_youtube",  False),
    (["twitter","abrir twitter"],                                     "abrir_twitter",  False),
    (["whatsapp"],                                                    "abrir_whatsapp", False),
    (["gmail"],                                                       "abrir_gmail",    False),
    (["spotify"],                                                     "abrir_spotify",  False),
    (["netflix"],                                                     "abrir_netflix",  False),
    (["instagram"],                                                   "abrir_instagram",False),
    (["github"],                                                      "abrir_github",   False),
    (["chatgpt","chat gpt"],                                         "abrir_chatgpt",  False),
    (["abre o site ","vai para o site "],                            "abrir_site",     True),
    (["pesquisa","busca","procura","googla"],                        "pesquisar",      True),
    (["digita ","escreve ","digite ","escreva "],                    "digitar",        True),
    (["clica em","clique em","clica no","clique no",
      "clica na","clique na"],                                        "clicar",         True),
    (["duplo clique","clique duplo"],                                "duplo_clique",   False),
    (["clique direito","botao direito"],                             "clique_direito", False),
    (["aperta enter","pressiona enter","da enter"],                  "tecla_enter",    False),
    (["aperta espaco","pressiona espaco"],                           "tecla_espaco",   False),
    (["aperta esc","pressiona escape"],                              "tecla_esc",      False),
    (["copia tudo","seleciona tudo"],                                "selecionar_tudo",False),
    (["copia","ctrl c"],                                             "copiar",         False),
    (["cola","ctrl v"],                                              "colar",          False),
    (["desfaz","ctrl z"],                                            "desfazer",       False),
    (["salva","ctrl s"],                                             "salvar",         False),
    (["fecha janela"],                                               "fechar_janela",  False),
    (["nova aba","nova tab"],                                        "nova_aba",       False),
    (["fecha aba","fecha tab"],                                      "fechar_aba",     False),
    (["atualiza","recarrega","refresh"],                             "atualizar",      False),
    (["minimiza"],                                                   "minimizar",      False),
    (["maximiza"],                                                   "maximizar",      False),
    (["alt tab","troca janela"],                                     "alt_tab",        False),
    (["rola para baixo","desce","scroll down"],                      "rolar_baixo",    False),
    (["rola para cima","sobe","scroll up"],                          "rolar_cima",     False),
    (["tira print","screenshot","printscreen","captura tela"],       "print",          False),
    (["posicao do mouse","onde o mouse"],                            "pos_mouse",      False),
    (["move o mouse para","move mouse"],                             "mover_mouse",    True),
    (["calculadora"],                                                "app_calc",       False),
    (["bloco de notas","notepad"],                                   "app_notepad",    False),
    (["explorador","gerenciador de arquivos"],                       "app_explorer",   False),
    (["gerenciador de tarefas"],                                     "app_taskmgr",    False),
    (["cmd","terminal","prompt"],                                    "app_cmd",        False),
    (["paint"],                                                      "app_paint",      False),
    (["aumenta o volume","sobe o volume"],                           "vol_up",         False),
    (["diminui o volume","baixa o volume"],                          "vol_down",       False),
    (["proxima musica","próxima música"],                            "midia_prox",     False),
    (["volta a musica","musica anterior"],                           "midia_ant",      False),
    (["pausa","pausar","play pause"],                                "midia_pause",    False),
    (["anota ","salva nota ","lembra "],                             "anotar",         True),
    (["mostra notas","ver notas","minhas notas"],                    "ver_notas",      False),
    (["cria macro ","nova macro "],                                  "criar_macro",    True),
    (["executa macro ","roda macro ","macro "],                      "executar_macro", True),
    (["lista macros","ver macros"],                                  "listar_macros",  False),
    (["historico","meus comandos"],                                  "ver_historico",  False),
    (["limpa historico"],                                            "limpar_hist",    False),
    (["desliga o pc"],                                               "desligar",       False),
    (["reinicia o pc","reiniciar"],                                  "reiniciar",      False),
    (["bloqueia o pc","travar tela"],                               "bloquear",       False),
    (["ajuda","help","comandos","o que voce faz"],                   "ajuda",          False),
    (["sair","fechar robo","tchau","ate logo","exit"],               "sair",           False),
]

def detectar_intencao(cmd: str):
    cn = _n(cmd)
    for padroes, acao, tem_param in INTENCOES:
        for p in padroes:
            pn = _n(p)
            if pn in cn:
                param = None
                if tem_param:
                    idx = cn.find(pn)
                    param = cmd[idx+len(p):].strip()
                    param = re.sub(r'^(o |a |os |as |um |uma |de |da |do )','',param,flags=re.I).strip()
                return acao, param or None
    # Fuzzy
    melhor,sc = None,0.0
    for padroes,acao,_ in INTENCOES:
        for p in padroes:
            s = SequenceMatcher(None,cn,_n(p)).ratio()
            if s>sc: sc,melhor=s,acao
    if sc>0.65: return melhor,None
    # Pergunta geral
    if any(cn.startswith(w) for w in ["o que e","o que é","quem e","quem é",
                                       "como funciona","por que","para que",
                                       "quando foi","onde fica","qual e","qual é",
                                       "me fala","me conta","me explica"]):
        return "pergunta_geral",cmd
    return None,None

# ══════════════════════════════════════════════════════════════════════════
#  ROBÔ
# ══════════════════════════════════════════════════════════════════════════
class Robo:
    def __init__(self, log_cb, hist_ui_cb, status_cb, notif_cb):
        self.log        = log_cb
        self.hist_ui    = hist_ui_cb
        self.set_status = status_cb
        self.notif_cb   = notif_cb
        self.hist       = Historico()
        self.macros     = Macros()
        self.agenda     = Agenda(self._disparar_lembrete)
        self._macro_gravando = None
        self._macro_cmds     = []
        self._ditando        = False
        self._ditado_partes  = []

    def _disparar_lembrete(self, texto):
        msg = f"⏰ LEMBRETE: {texto}"
        self.log(msg, "aviso")
        falar(f"Lembrete: {texto}")
        self.notif_cb(msg)

    def executar(self, cmd: str):
        cmd = cmd.strip()
        if not cmd: return

        # Macro gravação
        if self._macro_gravando:
            if _n(cmd) in ["fim macro","termina macro","para macro"]:
                self.macros.adicionar(self._macro_gravando, self._macro_cmds)
                msg = f"✅ Macro '{self._macro_gravando}' salva ({len(self._macro_cmds)} cmds)!"
                self.log(msg,"sucesso"); falar(msg)
                self._macro_gravando=None; self._macro_cmds=[]; self.hist_ui(); return
            self._macro_cmds.append(cmd)
            self.log(f"  [gravando] {cmd}","info"); return

        # Ditado
        if self._ditando:
            if _n(cmd) in ["termina o ditado","fim do ditado","parar ditado",
                           "terminar ditado","finaliza ditado","para ditado"]:
                texto_final = " ".join(self._ditado_partes)
                self._ditando = False
                self._ditado_partes = []
                self.log(f"Robô » ⌨️ Digitando texto ditado ({len(texto_final)} chars)...","robo")
                time.sleep(0.3)
                pyperclip.copy(texto_final)
                pyautogui.hotkey('ctrl','v')
                falar("Texto digitado com sucesso")
                return
            self._ditado_partes.append(cmd)
            self.log(f"  [ditando] {cmd}","info"); return

        self.log(f"Você » {cmd}","usuario")
        self.hist.salvar(cmd); self.hist_ui()

        acao, param = detectar_intencao(cmd)
        dispatch = {
            # ── Novidades v5 ──────────────────────────────────────────────
            "status_pc":        lambda: self._status_pc(),
            "ocr_tela":         lambda: self._ocr_tela(),
            "criar_lembrete":   lambda: self._criar_lembrete(param, cmd),
            "ver_lembretes":    lambda: self._ver_lembretes(),
            "limpar_lembretes": lambda: self._limpar_lembretes(),
            "ver_clipboard":    lambda: self._ver_clipboard(),
            "colar_clipboard":  lambda: self._colar_clipboard(param or cmd),
            "auto_click":       lambda: self._auto_click(param or cmd),
            "stop_click":       lambda: self._stop_click(),
            "gerar_senha":      lambda: self._gerar_senha(param or cmd),
            "iniciar_ditado":   lambda: self._iniciar_ditado(),
            "parar_ditado":     lambda: self._parar_ditado_cmd(),
            "resumir_pagina":   lambda: self._resumir_pagina_ativa(),
            "resumir_url":      lambda: self._resumir_url(param),
            "mover_monitor":    lambda: self._mover_monitor(),
            "listar_apps":      lambda: self._listar_apps(),
            "abrir_app":        lambda: self._abrir_app(param),
            "buscar_arquivo":   lambda: self._buscar_arquivo(param),
            # ── v4 ────────────────────────────────────────────────────────
            "clima":            lambda: self._clima(param, cmd),
            "noticias":         lambda: self._noticias(param),
            "traduzir":         lambda: self._traduzir(cmd, param),
            "calcular":         lambda: self._calcular(param or cmd),
            "converter":        lambda: self._converter(param or cmd),
            "pergunta_geral":   lambda: self._pergunta_geral(param or cmd),
            "hora_atual":       lambda: self._hora(),
            "data_atual":       lambda: self._data(),
            "play_video":       lambda: self._play(param),
            "pesquisar_yt":     lambda: self._pesquisar_yt(param),
            "abrir_google":     lambda: self._site("https://www.google.com.br","Google"),
            "abrir_youtube":    lambda: self._site("https://www.youtube.com","YouTube"),
            "abrir_twitter":    lambda: self._site("https://x.com","Twitter"),
            "abrir_whatsapp":   lambda: self._site("https://web.whatsapp.com","WhatsApp"),
            "abrir_gmail":      lambda: self._site("https://mail.google.com","Gmail"),
            "abrir_spotify":    lambda: self._site("https://open.spotify.com","Spotify"),
            "abrir_netflix":    lambda: self._site("https://www.netflix.com","Netflix"),
            "abrir_instagram":  lambda: self._site("https://www.instagram.com","Instagram"),
            "abrir_github":     lambda: self._site("https://github.com","GitHub"),
            "abrir_chatgpt":    lambda: self._site("https://chat.openai.com","ChatGPT"),
            "abrir_site":       lambda: self._site_gen(param),
            "pesquisar":        lambda: self._pesquisar(param),
            "digitar":          lambda: self._digitar(param),
            "clicar":           lambda: pyautogui.click(),
            "duplo_clique":     lambda: pyautogui.doubleClick(),
            "clique_direito":   lambda: pyautogui.rightClick(),
            "tecla_enter":      lambda: pyautogui.press("enter"),
            "tecla_espaco":     lambda: pyautogui.press("space"),
            "tecla_esc":        lambda: pyautogui.press("escape"),
            "selecionar_tudo":  lambda: pyautogui.hotkey("ctrl","a"),
            "copiar":           lambda: pyautogui.hotkey("ctrl","c"),
            "colar":            lambda: pyautogui.hotkey("ctrl","v"),
            "desfazer":         lambda: pyautogui.hotkey("ctrl","z"),
            "salvar":           lambda: pyautogui.hotkey("ctrl","s"),
            "fechar_janela":    lambda: pyautogui.hotkey("alt","F4"),
            "nova_aba":         lambda: pyautogui.hotkey("ctrl","t"),
            "fechar_aba":       lambda: pyautogui.hotkey("ctrl","w"),
            "atualizar":        lambda: pyautogui.press("F5"),
            "minimizar":        lambda: pyautogui.hotkey("win","down"),
            "maximizar":        lambda: pyautogui.hotkey("win","up"),
            "alt_tab":          lambda: pyautogui.hotkey("alt","tab"),
            "rolar_baixo":      lambda: pyautogui.scroll(-6),
            "rolar_cima":       lambda: pyautogui.scroll(6),
            "print":            lambda: self._print(),
            "pos_mouse":        lambda: self._pos_mouse(),
            "mover_mouse":      lambda: self._mover_mouse(param),
            "app_calc":         lambda: self._app("calc.exe","Calculadora"),
            "app_notepad":      lambda: self._app("notepad.exe","Bloco de notas"),
            "app_explorer":     lambda: self._app("explorer.exe","Explorador"),
            "app_taskmgr":      lambda: self._app("taskmgr.exe","Ger. de Tarefas"),
            "app_cmd":          lambda: self._app("cmd.exe","Terminal"),
            "app_paint":        lambda: self._app("mspaint.exe","Paint"),
            "vol_up":           lambda: [pyautogui.press("volumeup") for _ in range(5)],
            "vol_down":         lambda: [pyautogui.press("volumedown") for _ in range(5)],
            "midia_prox":       lambda: pyautogui.press("nexttrack"),
            "midia_ant":        lambda: pyautogui.press("prevtrack"),
            "midia_pause":      lambda: pyautogui.press("playpause"),
            "anotar":           lambda: self._anotar(param),
            "ver_notas":        lambda: self._ver_notas(),
            "criar_macro":      lambda: self._iniciar_macro(param),
            "executar_macro":   lambda: self._executar_macro(param),
            "listar_macros":    lambda: self._listar_macros(),
            "ver_historico":    lambda: self._ver_hist(),
            "limpar_hist":      lambda: self._limpar_hist(),
            "desligar":         lambda: self._desligar(),
            "reiniciar":        lambda: self._reiniciar(),
            "bloquear":         lambda: self._bloquear(),
            "ajuda":            lambda: self._ajuda(),
            "sair":             lambda: self._sair(),
        }

        if acao and acao in dispatch:
            try: dispatch[acao]()
            except Exception as e: self.log(f"Robô » ❌ Erro: {e}","erro")
        else:
            self._pergunta_geral(cmd)

    # ══ NOVIDADES v5 ═════════════════════════════════════════════════════

    def _status_pc(self):
        self.log("Robô » 🖥️ Verificando sistema...","robo")
        def _r():
            resp = status_sistema()
            self.log(f"Robô »\n{resp}","robo")
            falar(status_resumo())
        threading.Thread(target=_r,daemon=True).start()

    def _ocr_tela(self):
        self.log("Robô » 📸 Lendo texto da tela em 3 segundos...","robo")
        falar("Preparando leitura da tela")
        def _r():
            time.sleep(3)
            resp = ler_tela_ocr()
            self.log(f"Robô » {resp}","robo")
            if "Texto lido" in resp:
                linhas = resp.split("\n")
                falar("Texto lido: " + " ".join(linhas[1:3]))
        threading.Thread(target=_r,daemon=True).start()

    def _criar_lembrete(self, param, cmd_orig):
        # Detecta texto e horário no comando
        # Ex: "lembra eu às 15:30 de ligar" ou "me avisa em 30 minutos de tomar remédio"
        texto = "Lembrete!"
        quando = ""
        # Tenta extrair horário HH:MM
        m = re.search(r'(\d{1,2}[h:]\d{2})', cmd_orig)
        if m:
            quando = m.group(1).replace('h',':')
        else:
            m2 = re.search(r'em\s+(\d+)\s*(minutos?|horas?|segundos?)',_n(cmd_orig))
            if m2: quando = f"{m2.group(1)} {m2.group(2)}"
        # Extrai texto do lembrete
        texto_m = re.search(r'(?:de|para|lembrar de|lembrar que|sobre)\s+(.+)',_n(cmd_orig))
        if texto_m:
            parte = texto_m.group(1).strip()
            # Remove o horário do texto
            parte = re.sub(r'\d{1,2}[h:]\d{2}','',parte).strip()
            parte = re.sub(r'em \d+ (minutos?|horas?|segundos?)','',parte).strip()
            if parte and len(parte) > 2: texto = parte
        elif param: texto = param
        if not quando:
            self.log("Robô » Não entendi o horário. Ex: 'me avisa às 15:30 de reunião' ou 'em 30 minutos'","robo"); return
        resp = self.agenda.adicionar(texto, quando)
        self.log(f"Robô » {resp}","robo")
        falar(resp.replace("✅ ",""))

    def _ver_lembretes(self):
        ativos = self.agenda.listar()
        if not ativos: self.log("Robô » Nenhum lembrete ativo.","robo"); return
        self.log("── LEMBRETES ──","info")
        for i,l in enumerate(ativos,1):
            dt = datetime.strptime(l["dt"],"%Y-%m-%d %H:%M:%S").strftime("%d/%m %H:%M")
            self.log(f"  {i}. [{dt}] {l['texto']}","info")

    def _limpar_lembretes(self):
        self.agenda.limpar()
        self.log("Robô » ✅ Lembretes apagados.","sucesso")

    def _ver_clipboard(self):
        itens = CLIPBOARD.listar(8)
        if not itens: self.log("Robô » Clipboard vazio.","robo"); return
        self.log("── CLIPBOARD (mais recentes) ──","info")
        for i,item in enumerate(itens,1):
            preview = item[:60].replace("\n"," ")
            self.log(f"  {i}. {preview}{'…' if len(item)>60 else ''}","info")
        self.log("💡 Diga 'cola o segundo' para colar o item 2","info")

    def _colar_clipboard(self, param):
        idx = 0
        ordinals = {"primeiro":0,"segundo":1,"terceiro":2,"quarto":3,"quinto":4,
                    "ultimo":0,"último":0,"1":0,"2":1,"3":2,"4":3,"5":4}
        pn = _n(param)
        for palavra,i in ordinals.items():
            if palavra in pn: idx=i; break
        m = re.search(r'\d+',param)
        if m: idx = int(m.group())-1
        resultado = CLIPBOARD.colar_idx(idx)
        if resultado:
            preview = resultado[:50].replace("\n"," ")
            self.log(f"Robô » ✅ Colado: '{preview}...'","sucesso")
        else:
            self.log(f"Robô » ❌ Item {idx+1} não encontrado no clipboard.","erro")

    def _auto_click(self, param):
        vezes = 10; intervalo = 1.0
        m = re.search(r'(\d+)\s*(?:vezes?|cliques?|clicks?)',_n(param))
        if m: vezes = int(m.group(1))
        m2 = re.search(r'(?:a cada|cada|intervalo de)\s*([\d\.]+)\s*(?:segundo|seg)',_n(param))
        if m2: intervalo = float(m2.group(1))
        self.log(f"Robô » 🖱️ Auto-clicker: {vezes}x a cada {intervalo}s. Diga 'para de clicar' para parar.","robo")
        falar(f"Iniciando {vezes} cliques")
        time.sleep(2)  # Tempo para o usuário posicionar o mouse
        AUTO_CLICKER.iniciar(vezes, intervalo)

    def _stop_click(self):
        AUTO_CLICKER.parar()
        self.log("Robô » ✅ Auto-clicker parado.","sucesso")
        falar("Auto clicker parado")

    def _gerar_senha(self, param):
        comprimento = 16; simbolos = True
        m = re.search(r'(\d+)',param)
        if m: comprimento = max(8,min(64,int(m.group(1))))
        sem_simbolos = any(w in _n(param) for w in ["sem simbolo","sem caractere especial","apenas letras","so letras"])
        if sem_simbolos: simbolos = False
        senha = gerar_senha(comprimento, simbolos)
        pyperclip.copy(senha)
        self.log(f"Robô » 🔑 Senha gerada ({comprimento} chars):\n  {senha}","sucesso")
        self.log("  ✅ Já copiada para a área de transferência!","sucesso")
        falar(f"Senha de {comprimento} caracteres gerada e copiada")

    def _iniciar_ditado(self):
        self._ditando = True
        self._ditado_partes = []
        self.log("Robô » 🎙️ Modo ditado ativo! Fale o texto. Diga 'termina o ditado' para finalizar.","info")
        falar("Modo ditado ativo. Pode falar. Diga termina o ditado quando terminar.")

    def _parar_ditado_cmd(self):
        if not self._ditando:
            self.log("Robô » Ditado não estava ativo.","robo"); return
        texto = " ".join(self._ditado_partes)
        self._ditando = False; self._ditado_partes = []
        if texto:
            pyperclip.copy(texto); pyautogui.hotkey('ctrl','v')
            self.log(f"Robô » ✅ Texto digitado: {texto[:100]}","sucesso")
        else:
            self.log("Robô » Nenhum texto foi ditado.","robo")

    def _resumir_pagina_ativa(self):
        self.log("Robô » 📄 Capturando URL da aba ativa...","robo")
        def _r():
            url = pegar_url_ativa()
            if url:
                self.log(f"Robô » 🌐 Resumindo: {url[:60]}...","robo")
                self.set_status("Resumindo página...")
                resp = resumir_pagina(url)
                self.log(f"Robô » {resp[:600]}","robo")
                falar("Resumo: " + re.sub(r'📄.*?\n','',resp)[:200])
            else:
                self.log("Robô » ❌ Não consegui capturar a URL. Abra o navegador primeiro.","erro")
            self.set_status("Pronto.")
        threading.Thread(target=_r,daemon=True).start()

    def _resumir_url(self, url):
        if not url: self.log("Robô » Qual URL resumir?","robo"); return
        if not url.startswith("http"): url = "https://" + url
        self.log(f"Robô » 📄 Resumindo {url[:50]}...","robo")
        def _r():
            resp = resumir_pagina(url)
            self.log(f"Robô » {resp[:600]}","robo")
            falar("Resumo pronto. Veja no chat.")
        threading.Thread(target=_r,daemon=True).start()

    def _mover_monitor(self):
        if not PYGW_OK:
            self.log("Robô » ❌ Instale pygetwindow: pip install pygetwindow","erro"); return
        try:
            janelas = gw.getActiveWindow()
            if not janelas:
                self.log("Robô » ❌ Nenhuma janela ativa encontrada.","erro"); return
            # Move para o segundo monitor (deslocamento de 1920px)
            x_atual = janelas.left
            largura_monitor = 1920
            novo_x = 0 if x_atual >= largura_monitor else largura_monitor
            janelas.moveTo(novo_x, janelas.top)
            self.log(f"Robô » ✅ Janela movida para {'monitor 1' if novo_x==0 else 'monitor 2'}","sucesso")
            falar("Janela movida para o outro monitor")
        except Exception as e:
            self.log(f"Robô » ❌ Erro: {e}","erro")

    def _listar_apps(self):
        total = len(_APPS_CACHE)
        self.log(f"Robô » 📱 {total} apps encontrados no sistema.","robo")
        exemplos = list(_APPS_CACHE.keys())[:15]
        self.log("  Alguns: " + ", ".join(exemplos),"info")
        falar(f"{total} aplicativos encontrados")

    def _abrir_app(self, nome):
        if not nome: self.log("Robô » Qual app abrir?","robo"); return
        self.log(f"Robô » 🔍 Procurando '{nome}'...","robo")
        resp = abrir_app_por_nome(nome)
        self.log(f"Robô » {resp}","sucesso" if "✅" in resp else "erro")
        falar(resp.replace("✅ ","").replace("❌ ",""))

    def _buscar_arquivo(self, nome):
        if not nome: self.log("Robô » Qual arquivo buscar?","robo"); return
        self.log(f"Robô » 🗂️ Buscando '{nome}'...","robo")
        self.set_status(f"Buscando arquivo: {nome}...")
        def _r():
            resultados = buscar_arquivo(nome)
            if not resultados:
                self.log(f"Robô » ❌ Arquivo '{nome}' não encontrado.","erro"); return
            self.log(f"Robô » 📁 {len(resultados)} arquivo(s) encontrado(s):","sucesso")
            for i,p in enumerate(resultados[:5],1):
                self.log(f"  {i}. {p}","info")
            if resultados:
                os.startfile(resultados[0])
                self.log("  ✅ Abrindo o primeiro...","sucesso")
                falar(f"Arquivo {nome} encontrado e abrindo")
            self.set_status("Pronto.")
        threading.Thread(target=_r,daemon=True).start()

    # ══ v4 actions (kept) ════════════════════════════════════════════════

    def _clima(self, param, cmd_orig):
        dias=1
        m=re.search(r'(\d+)\s*dias?',_n(cmd_orig))
        if m: dias=int(m.group(1))
        elif "semana" in _n(cmd_orig): dias=7
        cidade=CFG.get("cidade_clima","São Paulo")
        for prep in ["em ","de ","para "]:
            if prep in _n(cmd_orig):
                partes=_n(cmd_orig).split(prep,1)
                cand=partes[-1].strip().split()[0] if partes[-1].strip() else ""
                if len(cand)>2 and cand not in ["hoje","amanha","semana","dias","tempo"]:
                    cidade=cand.capitalize(); break
        if param and len(param)>2: cidade=param.split()[0].capitalize()
        self.log(f"Robô » 🌤️ Buscando clima de {cidade} ({dias}d)...","robo")
        self.set_status(f"Clima {cidade}...")
        def _r():
            resp=buscar_clima(cidade,dias)
            self.log(f"Robô » {resp}","robo")
            falar(resp.split("\n")[0])
            self.set_status("Pronto.")
        threading.Thread(target=_r,daemon=True).start()

    def _noticias(self,param):
        self.log(f"Robô » 📰 Buscando notícias...","robo")
        def _r():
            resp=buscar_noticias(param or "")
            self.log(f"Robô » {resp}","robo")
            falar(resp.split("\n")[0])
        threading.Thread(target=_r,daemon=True).start()

    def _traduzir(self,cmd_orig,param):
        m=re.search(r'["\'](.+?)["\']',cmd_orig)
        texto=m.group(1) if m else (param or "")
        if not texto: self.log("Robô » O que traduzir? Ex: traduz 'olá' para inglês","robo"); return
        lang=detectar_lang(cmd_orig)
        def _r():
            resp=traduzir(texto,lang)
            self.log(f"Robô » {resp}","robo"); falar(resp)
        threading.Thread(target=_r,daemon=True).start()

    def _calcular(self,expr):
        m=re.search(r'[\d\s\+\-\*\/\(\)\.\,\%]+',expr)
        resp=calcular(m.group().strip() if m else expr)
        self.log(f"Robô » {resp}","robo"); falar(resp.replace("🧮 ",""))

    def _converter(self,expr):
        resp=converter_unidade(expr)
        if resp: self.log(f"Robô » {resp}","robo"); falar(resp)
        else: self._pergunta_geral(expr)

    def _pergunta_geral(self,pergunta):
        self.log("Robô » 🔎 Buscando resposta...","robo")
        self.set_status("Pesquisando...")
        def _r():
            resp=perguntar_web(pergunta)
            if resp:
                self.log(f"Robô » {resp}","robo")
                falar(re.sub(r'🔎\s*','',resp)[:220])
            else:
                self.log("Robô » Não encontrei. Abrindo Google...","robo")
                webbrowser.open(f"https://www.google.com.br/search?q={urllib.parse.quote(pergunta)}")
            self.set_status("Pronto.")
        threading.Thread(target=_r,daemon=True).start()

    def _hora(self):
        h=datetime.now().strftime("%H:%M:%S")
        self.log(f"Robô » ⏰ São {h}","robo"); falar(f"São {h}")

    def _data(self):
        d=datetime.now().strftime("%d/%m/%Y")
        self.log(f"Robô » 📅 Hoje é {d}","robo"); falar(f"Hoje é {d}")

    def _site(self,url,nome):
        self.log(f"Robô » 🌐 Abrindo {nome}...","robo")
        falar(f"Abrindo {nome}"); webbrowser.open(url)

    def _site_gen(self,param):
        if not param: return
        url=param if param.startswith("http") else f"https://{param}"
        webbrowser.open(url)

    def _pesquisar(self,termo):
        if not termo: return
        webbrowser.open(f"https://www.google.com.br/search?q={urllib.parse.quote(termo)}")

    def _pesquisar_yt(self,termo):
        if not termo: return
        webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote(termo)}")

    def _play(self,termo):
        if not termo: return
        self.log(f"Robô » 🎵 Procurando '{termo}'...","robo")
        falar(f"Procurando {termo}")
        def _r():
            url=buscar_yt(termo)
            if url: webbrowser.open(url)
            else: webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote(termo)}")
        threading.Thread(target=_r,daemon=True).start()

    def _digitar(self,texto):
        if not texto: return
        time.sleep(0.3); pyperclip.copy(texto); pyautogui.hotkey('ctrl','v')

    def _print(self):
        desk=os.path.join(os.path.expanduser("~"),"Desktop")
        os.makedirs(desk,exist_ok=True)
        p=os.path.join(desk,f"screenshot_{int(time.time())}.png")
        pyautogui.screenshot(p)
        self.log(f"Robô » 📸 Screenshot: {p}","sucesso")
        falar("Screenshot salvo")

    def _pos_mouse(self):
        x,y=pyautogui.position()
        self.log(f"Robô » 🖱️ Mouse em X={x}, Y={y}","robo"); falar(f"Mouse em x {x}, y {y}")

    def _mover_mouse(self,param):
        if param:
            nums=re.findall(r'\d+',param)
            if len(nums)>=2:
                pyautogui.moveTo(int(nums[0]),int(nums[1]),duration=0.4)
                self.log(f"Robô » 🖱️ Mouse → ({nums[0]},{nums[1]})","robo"); return
        self.log("Robô » Informe coordenadas. Ex: move o mouse para 500 300","robo")

    def _app(self,exe,nome):
        try:
            subprocess.Popen(exe,shell=True)
            self.log(f"Robô » ✅ Abrindo {nome}...","sucesso"); falar(f"Abrindo {nome}")
        except Exception as e: self.log(f"Robô » ❌ {e}","erro")

    def _anotar(self,texto):
        if not texto: return
        ts=datetime.now().strftime("%d/%m/%Y %H:%M")
        with open(NOTAS_FILE,"a",encoding="utf-8") as f: f.write(f"[{ts}] {texto}\n")
        self.log("Robô » 📝 Anotado!","sucesso"); falar("Nota salva")

    def _ver_notas(self):
        if not os.path.exists(NOTAS_FILE): self.log("Robô » Nenhuma nota.","robo"); return
        with open(NOTAS_FILE,"r",encoding="utf-8") as f: notas=f.read().strip()
        if notas:
            self.log("── NOTAS ──","info")
            for l in notas.split("\n")[-15:]: self.log(l,"info")

    def _iniciar_macro(self,nome):
        if not nome: return
        self._macro_gravando=nome.strip(); self._macro_cmds=[]
        self.log(f"Robô » 🔴 Gravando macro '{nome}'... diga 'fim macro'","info")
        falar(f"Gravando macro {nome}")

    def _executar_macro(self,nome):
        if not nome: return
        cmds=self.macros.listar().get(nome.strip().lower())
        if not cmds: self.log(f"Robô » ❌ Macro '{nome}' não encontrada.","erro"); return
        self.log(f"Robô » ▶ Executando macro '{nome}'...","sucesso")
        for c in cmds: time.sleep(0.3); self.executar(c)

    def _listar_macros(self):
        m=self.macros.listar()
        if not m: self.log("Robô » Nenhuma macro.","robo"); return
        self.log("── MACROS ──","info")
        for n2,c2 in m.items(): self.log(f"  • {n2}: {len(c2)} cmds","info")

    def _ver_hist(self):
        r=self.hist.recentes(15)
        self.log("── HISTÓRICO ──","info")
        for i,e in enumerate(r,1): self.log(f"  {i:2}. [{e['ts']}] {e['cmd']}","info")

    def _limpar_hist(self):
        self.hist.limpar(); self.hist_ui()
        self.log("Robô » ✅ Histórico apagado.","sucesso")

    def _desligar(self):
        self.log("Robô » ⚠️ Desligando em 30s...","aviso")
        falar("Desligando em 30 segundos")
        subprocess.run("shutdown /s /t 30",shell=True)

    def _reiniciar(self):
        self.log("Robô » ⚠️ Reiniciando em 30s...","aviso")
        subprocess.run("shutdown /r /t 30",shell=True)

    def _bloquear(self):
        self.log("Robô » 🔒 Bloqueando...","robo"); falar("Bloqueando")
        ctypes.windll.user32.LockWorkStation()

    def _ajuda(self):
        self.log("""
╔══════════════════════════════════════════════════════════╗
║         🤖 ROBÔ ASSISTENTE PRO v5.0  — COMANDOS          ║
╠══════════════════════════════════════════════════════════╣
║ 🖥️  SISTEMA                                               ║
║   "como está o PC" / "uso de CPU" / "status do sistema"  ║
║   "bloqueia o PC" / "desliga" / "reinicia"               ║
║                                                           ║
║ 📸 OCR — LER TEXTO DA TELA                               ║
║   "lê o texto da tela" / "leia a tela"                   ║
║                                                           ║
║ ⏰ AGENDA & LEMBRETES                                     ║
║   "me avisa às 15:30 de reunião"                         ║
║   "lembra eu em 30 minutos de tomar remédio"             ║
║   "mostra lembretes"                                     ║
║                                                           ║
║ 📋 CLIPBOARD INTELIGENTE                                  ║
║   "mostra clipboard" / "cola o segundo"                  ║
║                                                           ║
║ 🖱️  AUTO-CLICKER                                          ║
║   "clica 50 vezes a cada 2 segundos"                     ║
║   "para de clicar"                                       ║
║                                                           ║
║ 🔑 SENHAS                                                 ║
║   "gera uma senha de 20 caracteres"                      ║
║   "gera senha sem símbolos"                              ║
║                                                           ║
║ 🎙️  DITADO DE TEXTO                                       ║
║   "começa a ditar" → fala o texto → "termina o ditado"  ║
║                                                           ║
║ 📄 RESUMO DE PÁGINA                                       ║
║   "resume essa página" (captura a aba ativa)             ║
║   "resume o site exemplo.com"                            ║
║                                                           ║
║ 🖥️  MÚLTIPLOS MONITORES                                   ║
║   "move a janela para outro monitor"                     ║
║                                                           ║
║ 📱 APPS INSTALADOS                                        ║
║   "abre o Discord" / "abre o Photoshop"                  ║
║   "lista apps"                                           ║
║                                                           ║
║ 📁 ARQUIVOS                                               ║
║   "abre o arquivo relatorio.pdf"                         ║
║   "encontra o arquivo planilha.xlsx"                     ║
║                                                           ║
║ 🌤  CLIMA · 📰 NOTÍCIAS · 🌐 TRADUÇÃO · 🧮 CÁLCULO        ║
║ 🎵 MÚSICA · 🌐 SITES · ⌨️ TECLADO · 📝 NOTAS · 🎬 MACROS  ║
╚══════════════════════════════════════════════════════════╝""","info")
        falar("Mostrando todos os comandos")

    def _sair(self):
        self.log("Robô » Até logo! 👋","robo"); falar("Até logo!")
        time.sleep(1); os._exit(0)


# ══════════════════════════════════════════════════════════════════════════
#  WAKE WORD — escuta em background
# ══════════════════════════════════════════════════════════════════════════
class WakeWord:
    def __init__(self, robo_cb, log_cb, status_cb):
        self.robo_cb    = robo_cb
        self.log        = log_cb
        self.set_status = status_cb
        self._ativo     = False
        self._rec       = sr.Recognizer() if VOZ_OK else None
        self._esperando_cmd = False

    def iniciar(self):
        if not VOZ_OK or self._ativo: return
        self._ativo = True
        threading.Thread(target=self._loop, daemon=True).start()

    def parar(self):
        self._ativo = False

    def _loop(self):
        if not self._rec: return
        wake = _n(CFG.get("wake_word","hey robô"))
        while self._ativo:
            try:
                with sr.Microphone() as src:
                    self._rec.adjust_for_ambient_noise(src, duration=0.3)
                    audio = self._rec.listen(src, timeout=3, phrase_time_limit=5)
                txt = _n(self._rec.recognize_google(audio, language=CFG.get("idioma_voz","pt-BR")))
                if wake in txt:
                    self.log(f"Robô » 👂 Wake word detectada! Ouvindo...","sucesso")
                    falar("Oi! Pode falar.")
                    self.set_status("👂 Ouvindo comando...")
                    # Aguarda o comando
                    with sr.Microphone() as src:
                        self._rec.adjust_for_ambient_noise(src, duration=0.2)
                        audio2 = self._rec.listen(src, timeout=6, phrase_time_limit=10)
                    cmd = self._rec.recognize_google(audio2, language=CFG.get("idioma_voz","pt-BR"))
                    if cmd:
                        threading.Thread(target=self.robo_cb, args=(cmd,), daemon=True).start()
                    self.set_status("👂 Wake word ativa...")
            except sr.WaitTimeoutError: pass
            except sr.UnknownValueError: pass
            except sr.RequestError: time.sleep(3)
            except Exception: time.sleep(1)


# ══════════════════════════════════════════════════════════════════════════
#  MODO VOZ CONTÍNUO
# ══════════════════════════════════════════════════════════════════════════
class VozContinua:
    def __init__(self, robo_cb, log_cb, status_cb, btn_cb):
        self.robo_cb    = robo_cb
        self.log        = log_cb
        self.set_status = status_cb
        self.set_btn    = btn_cb
        self.ativo      = False
        self._rec       = sr.Recognizer() if VOZ_OK else None

    def toggle(self):
        if self.ativo: self.parar()
        else: self.iniciar()

    def iniciar(self):
        if not VOZ_OK: return
        self.ativo = True
        self.set_btn("🔴 VOZ ATIVA","#aa0022")
        self.set_status("🎙 Modo voz contínuo — pode falar!")
        falar("Modo voz ativado")
        threading.Thread(target=self._loop, daemon=True).start()

    def parar(self):
        self.ativo = False
        self.set_btn("🎙 VOZ","#0050bb")
        self.set_status("Pronto.")

    def _loop(self):
        if not self._rec: return
        while self.ativo:
            try:
                with sr.Microphone() as src:
                    self._rec.adjust_for_ambient_noise(src,duration=0.3)
                    self.set_status("🎙 Ouvindo...")
                    audio = self._rec.listen(src,timeout=4,phrase_time_limit=10)
                txt = self._rec.recognize_google(audio,language=CFG.get("idioma_voz","pt-BR"))
                if txt:
                    self.set_status("⚙️ Processando...")
                    self.robo_cb(txt)
            except sr.WaitTimeoutError: pass
            except sr.UnknownValueError: pass
            except sr.RequestError: time.sleep(3)
            except Exception: time.sleep(1)
            if self.ativo: self.set_status("🎙 Ouvindo...")


# ══════════════════════════════════════════════════════════════════════════
#  INTERFACE
# ══════════════════════════════════════════════════════════════════════════
C={
    "bg":"#080c14","panel":"#0d1220","panel2":"#111827",
    "borda":"#1a2d55","acento":"#00e5ff","acento2":"#0050bb",
    "verde":"#00ff99","amarelo":"#ffd600","vermelho":"#ff3355",
    "laranja":"#ff8800","texto":"#ccd8f0","dim":"#3a5070",
    "usuario":"#00e5ff","robo":"#00ff99","info":"#ffd600",
    "sucesso":"#00ff99","erro":"#ff3355","aviso":"#ff8800",
    "hist_bg":"#060a12","hist_item":"#0c1020","hist_hov":"#152040","tab_sel":"#0d1a35",
}
FM=("Consolas",11); FT=("Consolas",13,"bold"); FS=("Consolas",9); FB=("Consolas",10,"bold"); FH=("Consolas",8)

class App:
    def __init__(self,root):
        self.root=root
        self.root.title("🤖 Robô Assistente PRO v5.0")
        self.root.geometry("1060x720")
        self.root.configure(bg=C["bg"])
        self.root.resizable(True,True)
        self.root.minsize(820,540)
        self._hist_idx=-1; self._icon_f=0; self._aba="chat"
        self._build()
        self.robo = Robo(self._log, self._refresh_hist, self._set_status, self._notif)
        self.voz  = VozContinua(self.robo.executar, self._log, self._set_status, self._set_btn_voz)
        self.wake = WakeWord(self.robo.executar, self._log, self._set_status)
        msg=saudacao()
        self._log(f"Robô » {msg}","sucesso")
        threading.Thread(target=lambda: falar(msg), daemon=True).start()
        self._log("💡 Novidades v5: 'status do PC', 'gera senha', 'me avisa às 15h', 'lê a tela'","info")
        self._log("💡 Wake word: ative em CONFIG e fale 'Hey Robô' de qualquer lugar!","info")
        if CFG.get("voz_continua"): self.root.after(1500, self.voz.iniciar)
        if CFG.get("wake_word_ativo"): self.root.after(2000, self.wake.iniciar)
        self._anim_icon()
        self._refresh_hist()

    def _build(self):
        self.root.columnconfigure(0,weight=1)
        self.root.rowconfigure(1,weight=1)
        # Header
        hdr=tk.Frame(self.root,bg=C["panel"])
        hdr.grid(row=0,column=0,sticky="ew")
        tk.Frame(hdr,bg=C["acento"],height=2).pack(fill="x")
        hi=tk.Frame(hdr,bg=C["panel"],padx=16,pady=9)
        hi.pack(fill="x")
        self.cv=tk.Canvas(hi,width=36,height=36,bg=C["panel"],highlightthickness=0)
        self.cv.pack(side="left",padx=(0,12))
        tk.Label(hi,text="ROBÔ ASSISTENTE",font=FT,fg=C["acento"],bg=C["panel"]).pack(side="left")
        tk.Label(hi,text=" PRO v5.0",font=FS,fg=C["dim"],bg=C["panel"]).pack(side="left",pady=(4,0))
        bf=tk.Frame(hi,bg=C["panel"]); bf.pack(side="right")
        self.var_auto=tk.BooleanVar(value=check_autostart())
        tk.Checkbutton(bf,text="Win startup",font=FS,fg=C["dim"],bg=C["panel"],
                       activebackground=C["panel"],selectcolor=C["panel2"],
                       variable=self.var_auto,command=self._toggle_auto).pack(side="right",padx=(8,0))
        self.var_voz_resp=tk.BooleanVar(value=CFG.get("resposta_voz",True))
        tk.Checkbutton(bf,text="Voz",font=FS,fg=C["dim"],bg=C["panel"],
                       activebackground=C["panel"],selectcolor=C["panel2"],
                       variable=self.var_voz_resp,
                       command=lambda:(CFG.update({"resposta_voz":self.var_voz_resp.get()}),save_cfg(CFG))).pack(side="right",padx=(8,0))
        tk.Label(bf,text="● ONLINE",font=FS,fg=C["verde"],bg=C["panel"]).pack(side="right")
        tk.Frame(hdr,bg=C["borda"],height=1).pack(fill="x")
        # Corpo
        corpo=tk.Frame(self.root,bg=C["bg"])
        corpo.grid(row=1,column=0,sticky="nsew")
        corpo.columnconfigure(0,weight=3); corpo.columnconfigure(1,weight=1,minsize=200)
        corpo.rowconfigure(0,weight=1)
        # Esquerda
        left=tk.Frame(corpo,bg=C["bg"])
        left.grid(row=0,column=0,sticky="nsew",padx=(10,0),pady=8)
        left.rowconfigure(1,weight=1); left.columnconfigure(0,weight=1)
        # Abas
        abas=tk.Frame(left,bg=C["bg"])
        abas.grid(row=0,column=0,sticky="ew",pady=(0,4))
        self.tabs={}
        for label,aba_id in [("💬 CHAT","chat"),("📝 NOTAS","notas"),
                              ("🎬 MACROS","macros"),("⏰ AGENDA","agenda"),("⚙️ CONFIG","config")]:
            b=tk.Button(abas,text=label,font=FS,bg=C["panel2"],fg=C["texto"],
                        activebackground=C["tab_sel"],relief="flat",bd=0,padx=12,pady=5,
                        cursor="hand2",command=lambda a=aba_id:self._trocar_aba(a))
            b.pack(side="left",padx=(0,2))
            self.tabs[aba_id]=b
        # Frames
        self.frs={}
        for aba_id in ["chat","notas","macros","agenda","config"]:
            f=tk.Frame(left,bg=C["bg"])
            f.rowconfigure(0,weight=1); f.columnconfigure(0,weight=1)
            self.frs[aba_id]=f
        # Chat
        self.chat=scrolledtext.ScrolledText(self.frs["chat"],font=FM,bg=C["panel2"],fg=C["texto"],
            insertbackground=C["acento"],relief="flat",bd=0,wrap="word",state="disabled",
            selectbackground=C["borda"],padx=10,pady=8)
        self.chat.grid(sticky="nsew")
        for t,cor,ex in [("usuario",C["usuario"],{"font":("Consolas",11,"bold")}),
                          ("robo",C["robo"],{}),("info",C["amarelo"],{}),
                          ("sucesso",C["verde"],{}),("erro",C["vermelho"],{}),
                          ("aviso",C["laranja"],{}),("dim_ts",C["dim"],{})]:
            self.chat.tag_config(t,foreground=cor,**ex)
        # Notas
        self.txt_notas=scrolledtext.ScrolledText(self.frs["notas"],font=FM,bg=C["panel2"],fg=C["texto"],
            insertbackground=C["acento"],relief="flat",bd=0,padx=10,pady=8)
        self.txt_notas.grid(sticky="nsew")
        nr=tk.Frame(self.frs["notas"],bg=C["bg"]); nr.grid(row=1,column=0,sticky="e",pady=(4,0))
        tk.Button(nr,text="💾 Salvar",font=FS,bg=C["acento2"],fg="white",relief="flat",bd=0,
                  padx=10,pady=4,cursor="hand2",command=self._salvar_notas).pack(side="left",padx=(0,4))
        tk.Button(nr,text="🔄 Recarregar",font=FS,bg=C["panel2"],fg=C["texto"],relief="flat",bd=0,
                  padx=10,pady=4,cursor="hand2",command=self._carregar_notas).pack(side="left")
        # Macros
        self.txt_macro=scrolledtext.ScrolledText(self.frs["macros"],font=FM,bg=C["panel2"],fg=C["texto"],
            insertbackground=C["acento"],relief="flat",bd=0,state="disabled",padx=10,pady=8)
        self.txt_macro.grid(sticky="nsew")
        # Agenda
        self.txt_agenda=scrolledtext.ScrolledText(self.frs["agenda"],font=FM,bg=C["panel2"],fg=C["texto"],
            insertbackground=C["acento"],relief="flat",bd=0,state="disabled",padx=10,pady=8)
        self.txt_agenda.grid(sticky="nsew")
        ar=tk.Frame(self.frs["agenda"],bg=C["bg"]); ar.grid(row=1,column=0,sticky="e",pady=(4,0))
        tk.Button(ar,text="🔄 Atualizar",font=FS,bg=C["panel2"],fg=C["texto"],relief="flat",bd=0,
                  padx=10,pady=4,cursor="hand2",command=self._refresh_agenda).pack(side="left",padx=(0,4))
        tk.Button(ar,text="🗑 Limpar",font=FS,bg=C["panel2"],fg=C["texto"],relief="flat",bd=0,
                  padx=10,pady=4,cursor="hand2",
                  command=lambda:threading.Thread(target=self.robo.executar,args=("limpa lembretes",),daemon=True).start()).pack(side="left")
        # Config
        self._build_config(self.frs["config"])
        self._trocar_aba("chat")
        # Direita
        right=tk.Frame(corpo,bg=C["bg"],pady=8)
        right.grid(row=0,column=1,sticky="nsew",padx=(4,10))
        right.rowconfigure(2,weight=1); right.columnconfigure(0,weight=1)
        tk.Label(right,text="HISTÓRICO RÁPIDO",font=FH,fg=C["dim"],bg=C["bg"]).grid(row=0,column=0,sticky="w")
        self.hist_busca=tk.Entry(right,font=FS,bg=C["hist_item"],fg=C["texto"],
            insertbackground=C["acento"],relief="flat",bd=3,
            highlightthickness=1,highlightcolor=C["acento"],highlightbackground=C["borda"])
        self.hist_busca.grid(row=1,column=0,sticky="ew",pady=(4,4))
        self.hist_busca.insert(0,"🔎 filtrar...")
        self.hist_busca.bind("<FocusIn>",lambda e:self._bf(True))
        self.hist_busca.bind("<FocusOut>",lambda e:self._bf(False))
        self.hist_busca.bind("<KeyRelease>",lambda e:self._refresh_hist())
        hcf=tk.Frame(right,bg=C["hist_bg"]); hcf.grid(row=2,column=0,sticky="nsew")
        hcf.rowconfigure(0,weight=1); hcf.columnconfigure(0,weight=1)
        self.hist_canvas=tk.Canvas(hcf,bg=C["hist_bg"],highlightthickness=0)
        hsb=tk.Scrollbar(hcf,orient="vertical",command=self.hist_canvas.yview)
        self.hist_inner=tk.Frame(self.hist_canvas,bg=C["hist_bg"])
        self.hist_inner.bind("<Configure>",lambda e:self.hist_canvas.configure(
            scrollregion=self.hist_canvas.bbox("all")))
        self.hist_canvas.create_window((0,0),window=self.hist_inner,anchor="nw")
        self.hist_canvas.configure(yscrollcommand=hsb.set)
        self.hist_canvas.grid(row=0,column=0,sticky="nsew"); hsb.grid(row=0,column=1,sticky="ns")
        tk.Button(right,text="🗑 limpar",font=FH,fg=C["dim"],bg=C["hist_bg"],relief="flat",bd=0,
                  cursor="hand2",
                  command=lambda:threading.Thread(target=self.robo.executar,args=("limpa histórico",),daemon=True).start()
                  ).grid(row=3,column=0,sticky="e",pady=(4,0))
        # Entrada
        bot=tk.Frame(self.root,bg=C["panel"],padx=12,pady=8)
        bot.grid(row=2,column=0,sticky="ew")
        tk.Frame(bot,bg=C["borda"],height=1).pack(fill="x",pady=(0,8))
        ir=tk.Frame(bot,bg=C["panel"]); ir.pack(fill="x")
        tk.Label(ir,text="▶",font=("Consolas",14,"bold"),fg=C["acento"],bg=C["panel"]).pack(side="left",padx=(0,6))
        self.entrada=tk.Entry(ir,font=("Consolas",13),bg=C["hist_item"],fg=C["texto"],
            insertbackground=C["acento"],relief="flat",bd=4,
            highlightthickness=1,highlightcolor=C["acento"],highlightbackground=C["borda"])
        self.entrada.pack(side="left",fill="x",expand=True,ipady=7,padx=(0,8))
        self.entrada.bind("<Return>",self._enviar)
        self.entrada.bind("<Up>",self._nav_up)
        self.entrada.bind("<Down>",self._nav_down)
        self.entrada.focus()
        tk.Button(ir,text="ENVIAR",font=FB,bg=C["acento2"],fg="white",
                  activebackground=C["acento"],relief="flat",bd=0,padx=16,pady=8,
                  cursor="hand2",command=self._enviar).pack(side="left",padx=(0,5))
        self.btn_voz=tk.Button(ir,text="🎙 VOZ",font=FB,
            bg=C["acento2"] if VOZ_OK else C["dim"],fg="white",
            activebackground=C["acento"],relief="flat",bd=0,padx=14,pady=8,
            cursor="hand2" if VOZ_OK else "arrow",command=self._toggle_voz)
        self.btn_voz.pack(side="left")
        self.status_var=tk.StringVar(value="Pronto.")
        tk.Label(self.root,textvariable=self.status_var,font=FS,fg=C["dim"],
                 bg=C["bg"],anchor="w",padx=12).grid(row=3,column=0,sticky="ew",pady=(0,4))

    def _build_config(self,parent):
        tk.Label(parent,text="⚙️  CONFIGURAÇÕES",font=("Consolas",11,"bold"),
                 fg=C["acento"],bg=C["bg"]).pack(anchor="w",padx=20,pady=(12,4))
        # Cidade
        r=tk.Frame(parent,bg=C["bg"]); r.pack(fill="x",padx=20,pady=4)
        tk.Label(r,text="🌤️ Cidade padrão:",font=FS,fg=C["texto"],bg=C["bg"]).pack(side="left")
        self.ent_cidade=tk.Entry(r,font=FS,width=18,bg=C["hist_item"],fg=C["texto"],
            insertbackground=C["acento"],relief="flat",bd=3)
        self.ent_cidade.insert(0,CFG.get("cidade_clima","São Paulo")); self.ent_cidade.pack(side="left",padx=(8,0))
        tk.Button(r,text="Salvar",font=FS,bg=C["acento2"],fg="white",relief="flat",bd=0,
                  padx=8,pady=3,cursor="hand2",command=self._salvar_cidade).pack(side="left",padx=(6,0))
        # Wake word
        r2=tk.Frame(parent,bg=C["bg"]); r2.pack(fill="x",padx=20,pady=4)
        tk.Label(r2,text="👂 Wake word:",font=FS,fg=C["texto"],bg=C["bg"]).pack(side="left")
        self.ent_wake=tk.Entry(r2,font=FS,width=14,bg=C["hist_item"],fg=C["texto"],
            insertbackground=C["acento"],relief="flat",bd=3)
        self.ent_wake.insert(0,CFG.get("wake_word","hey robô")); self.ent_wake.pack(side="left",padx=(8,0))
        self.var_wake=tk.BooleanVar(value=CFG.get("wake_word_ativo",False))
        tk.Checkbutton(r2,text="Ativar",font=FS,fg=C["texto"],bg=C["bg"],
            activebackground=C["bg"],selectcolor=C["panel2"],variable=self.var_wake,
            command=self._toggle_wake).pack(side="left",padx=(8,0))
        tk.Button(r2,text="Salvar",font=FS,bg=C["acento2"],fg="white",relief="flat",bd=0,
                  padx=8,pady=3,cursor="hand2",command=self._salvar_wake).pack(side="left",padx=(6,0))
        # Voz contínua auto
        r3=tk.Frame(parent,bg=C["bg"]); r3.pack(fill="x",padx=20,pady=4)
        self.var_voz_auto=tk.BooleanVar(value=CFG.get("voz_continua",False))
        tk.Checkbutton(r3,text="Ativar modo voz contínuo ao iniciar",font=FS,fg=C["texto"],bg=C["bg"],
            activebackground=C["bg"],selectcolor=C["panel2"],variable=self.var_voz_auto,
            command=lambda:(CFG.update({"voz_continua":self.var_voz_auto.get()}),save_cfg(CFG))).pack(side="left")
        # EXE
        tk.Label(parent,text="──────────────────────────────────",font=FS,fg=C["dim"],bg=C["bg"]).pack(anchor="w",padx=20,pady=(12,0))
        tk.Label(parent,text="📦 CRIAR EXECUTÁVEL",font=("Consolas",10,"bold"),fg=C["amarelo"],bg=C["bg"]).pack(anchor="w",padx=20)
        tk.Label(parent,text="No CMD da pasta do arquivo:\npyinstaller --onefile --windowed --name=RoboAssistente robo.py\nO .exe ficará em: dist\\RoboAssistente.exe",
            font=FS,fg=C["texto"],bg=C["panel2"],justify="left",padx=12,pady=8).pack(anchor="w",padx=20,pady=(4,0))
        tk.Button(parent,text="📋 Copiar comando",font=FS,bg=C["acento2"],fg="white",
            relief="flat",bd=0,padx=12,pady=5,cursor="hand2",
            command=lambda:pyperclip.copy("pyinstaller --onefile --windowed --name=RoboAssistente robo.py") or
                           messagebox.showinfo("Copiado!","Comando copiado!")).pack(anchor="w",padx=20,pady=(8,0))

    def _trocar_aba(self,aba_id):
        self._aba=aba_id
        for f in self.frs.values(): f.grid_remove()
        self.frs[aba_id].grid(row=1,column=0,sticky="nsew")
        for aid,btn in self.tabs.items():
            btn.config(bg=C["tab_sel"] if aid==aba_id else C["panel2"],
                       fg=C["acento"] if aid==aba_id else C["texto"])
        if aba_id=="notas": self._carregar_notas()
        if aba_id=="macros": self._refresh_macros()
        if aba_id=="agenda": self._refresh_agenda()

    def _carregar_notas(self):
        self.txt_notas.delete("1.0","end")
        if os.path.exists(NOTAS_FILE):
            with open(NOTAS_FILE,"r",encoding="utf-8") as f: self.txt_notas.insert("1.0",f.read())

    def _salvar_notas(self):
        with open(NOTAS_FILE,"w",encoding="utf-8") as f: f.write(self.txt_notas.get("1.0","end-1c"))
        self._log("Notas salvas.","sucesso")

    def _refresh_macros(self):
        self.txt_macro.config(state="normal"); self.txt_macro.delete("1.0","end")
        m=self.robo.macros.listar() if hasattr(self,"robo") else {}
        if not m: self.txt_macro.insert("end","Nenhuma macro.\n\nCrie com: cria macro [nome]")
        else:
            for nome,cmds in m.items():
                self.txt_macro.insert("end",f"▶ {nome.upper()}\n")
                for i,c in enumerate(cmds,1): self.txt_macro.insert("end",f"  {i}. {c}\n")
                self.txt_macro.insert("end","\n")
        self.txt_macro.config(state="disabled")

    def _refresh_agenda(self):
        self.txt_agenda.config(state="normal"); self.txt_agenda.delete("1.0","end")
        if not hasattr(self,"robo"): return
        ativos=self.robo.agenda.listar()
        if not ativos:
            self.txt_agenda.insert("end","Nenhum lembrete ativo.\n\nCrie com:\n  'me avisa às 15:30 de reunião'\n  'lembra eu em 30 minutos de tomar remédio'")
        else:
            self.txt_agenda.insert("end",f"📅 {len(ativos)} lembrete(s) ativo(s):\n\n")
            for i,l in enumerate(ativos,1):
                dt=datetime.strptime(l["dt"],"%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
                self.txt_agenda.insert("end",f"  {i}. [{dt}] {l['texto']}\n")
        self.txt_agenda.config(state="disabled")

    def _anim_icon(self):
        f=self._icon_f
        self.cv.delete("all")
        p=15+(f%5)
        self.cv.create_oval(18-p,18-p,18+p,18+p,outline=C["acento"],width=1)
        self.cv.create_oval(10,10,26,26,fill=C["acento2"],outline=C["acento"],width=2)
        ey=15+(1 if f%7==0 else 0)
        self.cv.create_oval(12,ey,14,ey+2,fill="white")
        self.cv.create_oval(22,ey,24,ey+2,fill="white")
        self.cv.create_arc(12,17,24,24,start=200,extent=140,outline="white",width=1,style="arc")
        self.cv.create_line(18,10,18,6,fill=C["acento"],width=1)
        self.cv.create_oval(16,4,20,8,fill=C["acento"],outline="")
        if hasattr(self,"voz") and self.voz.ativo:
            self.cv.create_oval(29,5,35,11,fill=C["vermelho"],outline="")
        if hasattr(self,"wake") and self.wake._ativo:
            self.cv.create_oval(29,14,35,20,fill=C["amarelo"],outline="")
        self._icon_f=(f+1)%10
        self.root.after(200,self._anim_icon)

    def _refresh_hist(self):
        for w in self.hist_inner.winfo_children(): w.destroy()
        filtro=""
        if hasattr(self,"hist_busca"):
            t=self.hist_busca.get()
            if t and t!="🔎 filtrar...": filtro=_n(t)
        recs=self.robo.hist.recentes(30) if hasattr(self,"robo") else []
        if filtro: recs=[e for e in recs if filtro in _n(e["cmd"])]
        if not recs:
            tk.Label(self.hist_inner,text="vazio",font=FS,fg=C["dim"],bg=C["hist_bg"]).pack(padx=8,pady=8); return
        for e in recs:
            row=tk.Frame(self.hist_inner,bg=C["hist_item"],cursor="hand2",pady=3)
            row.pack(fill="x",padx=2,pady=1)
            txt=e["cmd"][:24]+("…" if len(e["cmd"])>24 else "")
            lbl=tk.Label(row,text=txt,font=FS,fg=C["texto"],bg=C["hist_item"],anchor="w",padx=5)
            lbl.pack(side="left",fill="x",expand=True)
            ts=tk.Label(row,text=e["ts"],font=FH,fg=C["dim"],bg=C["hist_item"],padx=3)
            ts.pack(side="right")
            cmd=e["cmd"]
            for w in (row,lbl,ts):
                w.bind("<Enter>",lambda ev,r=row,l=lbl,t=ts:self._hov(r,l,t,True))
                w.bind("<Leave>",lambda ev,r=row,l=lbl,t=ts:self._hov(r,l,t,False))
                w.bind("<Button-1>",lambda ev,c=cmd:self._repetir(c))

    def _hov(self,r,l,t,on):
        bg=C["hist_hov"] if on else C["hist_item"]
        r.config(bg=bg); l.config(bg=bg); t.config(bg=bg)

    def _repetir(self,cmd):
        self.entrada.delete(0,"end"); self.entrada.insert(0,cmd); self._enviar()

    def _bf(self,on):
        if on and self.hist_busca.get()=="🔎 filtrar...": self.hist_busca.delete(0,"end")
        elif not on and not self.hist_busca.get(): self.hist_busca.insert(0,"🔎 filtrar...")

    def _nav_up(self,_=None):
        r=self.robo.hist.recentes(30) if hasattr(self,"robo") else []
        if not r: return
        self._hist_idx=min(self._hist_idx+1,len(r)-1)
        self.entrada.delete(0,"end"); self.entrada.insert(0,r[self._hist_idx]["cmd"])

    def _nav_down(self,_=None):
        if self._hist_idx<=0:
            self._hist_idx=-1; self.entrada.delete(0,"end"); return
        self._hist_idx-=1
        r=self.robo.hist.recentes(30)
        self.entrada.delete(0,"end"); self.entrada.insert(0,r[self._hist_idx]["cmd"])

    def _enviar(self,_=None):
        txt=self.entrada.get().strip()
        if not txt: return
        self._hist_idx=-1; self.entrada.delete(0,"end")
        self._trocar_aba("chat")
        threading.Thread(target=self.robo.executar,args=(txt,),daemon=True).start()

    def _toggle_voz(self):
        self.voz.toggle()

    def _toggle_auto(self):
        ok=toggle_autostart(self.var_auto.get())
        self._log(f"Robô » {'✅ Inicialização automática ativada.' if self.var_auto.get() else '✅ Desativada.'}","sucesso" if ok else "erro")

    def _toggle_wake(self):
        if self.var_wake.get():
            CFG["wake_word_ativo"]=True; save_cfg(CFG)
            self.wake.iniciar()
            self._log(f"Robô » 👂 Wake word '{CFG['wake_word']}' ativada!","sucesso")
            falar(f"Wake word ativada. Diga {CFG['wake_word']} para me chamar.")
        else:
            CFG["wake_word_ativo"]=False; save_cfg(CFG)
            self.wake.parar()
            self._log("Robô » Wake word desativada.","robo")

    def _salvar_cidade(self):
        c=self.ent_cidade.get().strip()
        if c: CFG["cidade_clima"]=c; save_cfg(CFG); self._log(f"Robô » ✅ Cidade: {c}","sucesso")

    def _salvar_wake(self):
        w=self.ent_wake.get().strip()
        if w: CFG["wake_word"]=w.lower(); save_cfg(CFG); self._log(f"Robô » ✅ Wake word: '{w}'","sucesso")

    def _log(self,texto,tag="info"):
        def _ins():
            self.chat.config(state="normal")
            ts=datetime.now().strftime("%H:%M:%S")
            self.chat.insert("end",f"[{ts}] ","dim_ts")
            self.chat.insert("end",texto+"\n",tag)
            self.chat.see("end")
            self.chat.config(state="disabled")
        self.root.after(0,_ins)

    def _set_status(self,txt):
        self.root.after(0,lambda:self.status_var.set(txt))

    def _set_btn_voz(self,txt,cor):
        self.root.after(0,lambda:self.btn_voz.config(text=txt,bg=cor))

    def _notif(self,msg):
        if PLYER_OK:
            try:
                notification.notify(title="🤖 Robô Assistente",message=msg[:200],
                                   app_name="Robô Assistente PRO",timeout=8)
            except: pass
        # Também aparece no chat
        self.root.after(0,lambda:messagebox.showinfo("⏰ LEMBRETE",msg))


# ══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    root = tk.Tk()
    app  = App(root)
    root.mainloop()
