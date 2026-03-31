"""
╔══════════════════════════════════════════════════════════╗
║         🤖 ROBÔ ASSISTENTE PRO v4.0                      ║
║  Voz contínua · gTTS · IA web · Clima · Notícias         ║
║  Executável · Inicialização automática · 100% grátis     ║
╚══════════════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading, time, subprocess, webbrowser
import json, os, re, sys, tempfile, shutil, math
from datetime import datetime
from difflib import SequenceMatcher
import urllib.parse, urllib.request, urllib.error
import winreg                          # inicialização automática Windows

import pyautogui, pyperclip
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3

# ── Reconhecimento de voz ────────────────────────────────────────────────────
try:
    import speech_recognition as sr
    VOZ_OK = True
except ImportError:
    VOZ_OK = False

# ── gTTS (voz natural) ───────────────────────────────────────────────────────
try:
    from gtts import gTTS
    import pygame
    pygame.mixer.init()
    GTTS_OK = True
except Exception:
    GTTS_OK = False

# ── pyttsx3 fallback offline ─────────────────────────────────────────────────
try:
    import pyttsx3
    _tts_offline = pyttsx3.init()
    _tts_offline.setProperty('rate', 162)
    for v in _tts_offline.getProperty('voices'):
        if any(x in v.id.lower() for x in ['pt', 'brazil', 'portuguese']):
            _tts_offline.setProperty('voice', v.id)
            break
    TTS_OFFLINE_OK = True
except Exception:
    TTS_OFFLINE_OK = False

# ── BeautifulSoup ────────────────────────────────────────────────────────────
try:
    from bs4 import BeautifulSoup
    BS4_OK = True
except ImportError:
    BS4_OK = False

# ── Requests ─────────────────────────────────────────────────────────────────
try:
    import requests
    REQ_OK = True
except ImportError:
    REQ_OK = False

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
HIST_FILE   = os.path.join(BASE_DIR, "historico.json")
MACROS_FILE = os.path.join(BASE_DIR, "macros.json")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
NOTAS_FILE  = os.path.join(BASE_DIR, "notas.txt")
APP_NAME    = "RoboAssistentePRO"
APP_EXE     = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_CFG = {
    "voz_continua": True,
    "resposta_voz": True,
    "idioma_voz": "pt-BR",
    "iniciar_com_windows": False,
    "usar_gtts": True,
    "cidade_clima": "São Paulo",
}

def load_cfg():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return {**DEFAULT_CFG, **json.load(f)}
        except Exception: pass
    return dict(DEFAULT_CFG)

def save_cfg(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

CFG = load_cfg()

# ══════════════════════════════════════════════════════════════════════════════
#  SÍNTESE DE VOZ — gTTS (natural) + pyttsx3 (offline fallback)
# ══════════════════════════════════════════════════════════════════════════════

_fala_lock = threading.Lock()

def falar(texto: str, forcar_offline=False):
    if not CFG.get("resposta_voz", True):
        return
    def _run():
        with _fala_lock:
            # Limpa texto para fala
            texto_limpo = re.sub(r'[╔╗╚╝║╠╣═─►●⬤▶📝🎵🌐🔍⌨️🖱️🎬⏰📸✅❌⚠️📋💬🎙🔴🗑]', '', texto)
            texto_limpo = re.sub(r'\[.*?\]', '', texto_limpo).strip()
            if not texto_limpo or len(texto_limpo) < 2:
                return
            if GTTS_OK and CFG.get("usar_gtts", True) and not forcar_offline:
                try:
                    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                    tmp.close()
                    tts = gTTS(text=texto_limpo[:500], lang='pt', slow=False)
                    tts.save(tmp.name)
                    pygame.mixer.music.load(tmp.name)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.05)
                    pygame.mixer.music.unload()
                    os.unlink(tmp.name)
                    return
                except Exception:
                    pass
            # Fallback offline
            if TTS_OFFLINE_OK:
                try:
                    _tts_offline.say(texto_limpo[:300])
                    _tts_offline.runAndWait()
                except Exception: pass
    threading.Thread(target=_run, daemon=True).start()

# ══════════════════════════════════════════════════════════════════════════════
#  SAUDAÇÃO INTELIGENTE
# ══════════════════════════════════════════════════════════════════════════════

def saudacao() -> str:
    h = datetime.now().hour
    if 5 <= h < 12:
        periodo = "Bom dia"
    elif 12 <= h < 18:
        periodo = "Boa tarde"
    else:
        periodo = "Boa noite"
    return f"{periodo}! Sou seu Robô Assistente PRO. Em que posso ajudar?"

# ══════════════════════════════════════════════════════════════════════════════
#  INICIALIZAÇÃO AUTOMÁTICA COM WINDOWS
# ══════════════════════════════════════════════════════════════════════════════

def toggle_autostart(ativar: bool):
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        if ativar:
            cmd = f'pythonw "{APP_EXE}"' if not getattr(sys, 'frozen', False) else f'"{APP_EXE}"'
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try: winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError: pass
        winreg.CloseKey(key)
        CFG["iniciar_com_windows"] = ativar
        save_cfg(CFG)
        return True
    except Exception as e:
        return False

def check_autostart() -> bool:
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False

# ══════════════════════════════════════════════════════════════════════════════
#  BUSCA WEB INTELIGENTE — clima, notícias, traduções, perguntas gerais
# ══════════════════════════════════════════════════════════════════════════════

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9"
}

def _fetch(url, timeout=8) -> str | None:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception:
        return None

def _soup(html: str):
    if BS4_OK:
        return BeautifulSoup(html, "html.parser")
    return None

# ── Clima ─────────────────────────────────────────────────────────────────────

def buscar_clima(cidade: str, dias: int = 1) -> str:
    """Busca clima via wttr.in (sem API key)."""
    try:
        cidade_enc = urllib.parse.quote(cidade)
        if dias <= 1:
            url = f"https://wttr.in/{cidade_enc}?format=3&lang=pt"
            html = _fetch(url)
            if html:
                return f"🌤️ {html.strip()}"
        # Previsão de vários dias
        url = f"https://wttr.in/{cidade_enc}?format=j1"
        html = _fetch(url)
        if html:
            data = json.loads(html)
            weather = data.get("weather", [])
            linhas = [f"📅 Previsão para {cidade} ({min(dias, len(weather))} dias):"]
            cond_map = {
                "Sunny": "☀️ Ensolarado", "Clear": "☀️ Limpo",
                "Partly cloudy": "⛅ Parcialmente nublado",
                "Cloudy": "☁️ Nublado", "Overcast": "☁️ Encoberto",
                "Rain": "🌧️ Chuva", "Light rain": "🌦️ Chuva leve",
                "Heavy rain": "⛈️ Chuva forte", "Thundery outbreaks": "⛈️ Trovoadas",
                "Snow": "❄️ Neve", "Fog": "🌫️ Neblina",
                "Mist": "🌫️ Névoa", "Blizzard": "🌨️ Nevasca",
            }
            for i, day in enumerate(weather[:min(dias, 7)]):
                dt = day.get("date", "")
                try:
                    dt_fmt = datetime.strptime(dt, "%Y-%m-%d").strftime("%d/%m (%a)")
                except Exception:
                    dt_fmt = dt
                tmax = day.get("maxtempC", "?")
                tmin = day.get("mintempC", "?")
                desc_en = day.get("hourly", [{}])[4].get("weatherDesc", [{}])[0].get("value", "")
                desc = cond_map.get(desc_en, desc_en or "–")
                chuva = day.get("hourly", [{}])[4].get("chanceofrain", "0")
                linhas.append(f"  {dt_fmt}: {desc} {tmin}°C–{tmax}°C 🌧️{chuva}%")
            return "\n".join(linhas)
    except Exception as e:
        pass
    return f"❌ Não consegui buscar o clima de '{cidade}'. Verifique a conexão."

# ── Notícias ──────────────────────────────────────────────────────────────────

def buscar_noticias(tema: str = "") -> str:
    """Busca notícias via Google News RSS."""
    try:
        query = urllib.parse.quote(tema if tema else "brasil")
        url = f"https://news.google.com/rss/search?q={query}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        html = _fetch(url)
        if not html:
            return "❌ Não consegui buscar notícias."
        titulos = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', html)
        if not titulos:
            titulos = re.findall(r'<title>(.*?)</title>', html)
        titulos = [t for t in titulos if t and "Google News" not in t][:6]
        if not titulos:
            return "❌ Nenhuma notícia encontrada."
        header = f"📰 Notícias{' sobre ' + tema if tema else ' do dia'}:"
        return header + "\n" + "\n".join(f"  • {t}" for t in titulos)
    except Exception as e:
        return f"❌ Erro ao buscar notícias: {e}"

# ── Tradução ──────────────────────────────────────────────────────────────────

def traduzir(texto: str, para: str = "en") -> str:
    """Tradução via MyMemory API (gratuita, sem chave)."""
    try:
        de = "pt"
        texto_enc = urllib.parse.quote(texto[:500])
        url = f"https://api.mymemory.translated.net/get?q={texto_enc}&langpair={de}|{para}"
        html = _fetch(url)
        if html:
            data = json.loads(html)
            trad = data.get("responseData", {}).get("translatedText", "")
            if trad:
                lang_nomes = {
                    "en": "inglês", "es": "espanhol", "fr": "francês",
                    "de": "alemão", "it": "italiano", "ja": "japonês",
                    "zh": "chinês", "ru": "russo", "ar": "árabe",
                    "pt": "português"
                }
                nome_lang = lang_nomes.get(para, para)
                return f"🌐 Tradução para {nome_lang}:\n  \"{trad}\""
    except Exception: pass
    return "❌ Não consegui traduzir."

def detectar_idioma_alvo(cmd: str) -> str:
    mapa = {
        "inglês": "en", "ingles": "en", "english": "en",
        "espanhol": "es", "español": "es",
        "francês": "fr", "frances": "fr",
        "alemão": "de", "alemao": "de",
        "italiano": "it",
        "japonês": "ja", "japones": "ja",
        "chinês": "zh", "chines": "zh",
        "russo": "ru", "árabe": "ar",
        "português": "pt", "portugues": "pt",
    }
    cmd_l = cmd.lower()
    for palavra, codigo in mapa.items():
        if palavra in cmd_l:
            return codigo
    return "en"

# ── Cálculos ──────────────────────────────────────────────────────────────────

def calcular(expr: str) -> str:
    """Avalia expressão matemática segura."""
    try:
        # Substitui palavras
        expr_clean = expr.lower()
        expr_clean = re.sub(r'[^\d\+\-\*\/\(\)\.\,\s\%]', ' ', expr_clean)
        expr_clean = expr_clean.replace(',', '.').replace(' x ', '*').replace(' por ', '/')
        expr_clean = expr_clean.strip()
        # Segurança: apenas números e operadores
        if re.match(r'^[\d\s\+\-\*\/\(\)\.\%]+$', expr_clean):
            resultado = eval(expr_clean, {"__builtins__": {}}, {})
            if isinstance(resultado, float) and resultado == int(resultado):
                resultado = int(resultado)
            return f"🧮 {expr} = {resultado}"
    except Exception: pass
    return f"❌ Não consegui calcular '{expr}'"

# Conversões de unidades
def converter_unidade(expr: str) -> str | None:
    expr_l = expr.lower()
    # Temperatura
    m = re.search(r'([\d\.,]+)\s*(?:graus\s*)?(celsius|°c|graus c)\s*(?:para|em)\s*(fahrenheit|°f|farenheit)', expr_l)
    if m:
        c = float(m.group(1).replace(',', '.'))
        f = c * 9/5 + 32
        return f"🌡️ {c}°C = {f:.1f}°F"
    m = re.search(r'([\d\.,]+)\s*(?:graus\s*)?(fahrenheit|°f)\s*(?:para|em)\s*(celsius|°c)', expr_l)
    if m:
        f = float(m.group(1).replace(',', '.'))
        c = (f - 32) * 5/9
        return f"🌡️ {f}°F = {c:.1f}°C"
    # Moeda simples (cotação do dia via API pública)
    m = re.search(r'([\d\.,]+)\s*(dolar|dólar|usd|euro|eur|real|brl)\s*(?:para|em|=|é quanto em)\s*(dolar|dólar|usd|euro|eur|real|brl|reais)', expr_l)
    if m:
        return _converter_moeda(m.group(1), m.group(2), m.group(3))
    # km/milhas
    m = re.search(r'([\d\.,]+)\s*km\s*(?:para|em)\s*milhas', expr_l)
    if m:
        km = float(m.group(1).replace(',', '.'))
        return f"📏 {km} km = {km * 0.621371:.2f} milhas"
    m = re.search(r'([\d\.,]+)\s*milhas?\s*(?:para|em)\s*km', expr_l)
    if m:
        mi = float(m.group(1).replace(',', '.'))
        return f"📏 {mi} milhas = {mi * 1.60934:.2f} km"
    # kg/lb
    m = re.search(r'([\d\.,]+)\s*kg\s*(?:para|em)\s*(libras|lb)', expr_l)
    if m:
        kg = float(m.group(1).replace(',', '.'))
        return f"⚖️ {kg} kg = {kg * 2.20462:.2f} lb"
    return None

def _converter_moeda(valor_str, de, para) -> str:
    mapa = {"dolar": "USD", "dólar": "USD", "usd": "USD",
            "euro": "EUR", "eur": "EUR", "real": "BRL",
            "brl": "BRL", "reais": "BRL"}
    de_c  = mapa.get(de.lower(), "USD")
    para_c = mapa.get(para.lower(), "BRL")
    valor = float(valor_str.replace(',', '.'))
    try:
        url = f"https://api.frankfurter.app/latest?amount={valor}&from={de_c}&to={para_c}"
        html = _fetch(url)
        if html:
            data = json.loads(html)
            resultado = data.get("rates", {}).get(para_c)
            if resultado:
                return f"💱 {valor} {de_c} = {resultado:.2f} {para_c}"
    except Exception: pass
    return f"❌ Não consegui converter moeda agora."

# ── Pergunta geral (Google snippet) ──────────────────────────────────────────

def perguntar_web(pergunta: str) -> str:
    """Extrai resposta direta do Google (featured snippet)."""
    try:
        q = urllib.parse.quote(pergunta)
        url = f"https://www.google.com.br/search?q={q}&hl=pt-BR"
        html = _fetch(url)
        if not html:
            return None
        if BS4_OK:
            soup = BeautifulSoup(html, "html.parser")
            # Tenta featured snippet
            for sel in ["div.BNeawe.s3v9rd.AP7Wnd", "div.BNeawe.iBp4i.AP7Wnd",
                        "div[data-attrid='wa:/description']", "span.hgKElc",
                        "div.ILfuVd", "div.ayRjaf"]:
                el = soup.select_one(sel)
                if el and len(el.get_text(strip=True)) > 10:
                    txt = el.get_text(strip=True)[:400]
                    return f"🔎 {txt}"
            # Fallback: primeiro parágrafo de resultado
            for el in soup.select("div.VwiC3b, div.s3v9rd"):
                txt = el.get_text(strip=True)
                if len(txt) > 20:
                    return f"🔎 {txt[:400]}"
        else:
            # Sem BS4: regex simples
            m = re.search(r'class="BNeawe[^"]*"[^>]*>(.*?)</div>', html)
            if m:
                txt = re.sub(r'<[^>]+>', '', m.group(1)).strip()[:400]
                if txt:
                    return f"🔎 {txt}"
    except Exception: pass
    return None

# ── YouTube: primeiro vídeo ──────────────────────────────────────────────────

def buscar_primeiro_yt(termo: str) -> str | None:
    try:
        q = urllib.parse.quote(termo)
        html = _fetch(f"https://www.youtube.com/results?search_query={q}")
        if html:
            ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
            if ids:
                return f"https://www.youtube.com/watch?v={ids[0]}"
    except Exception: pass
    return None

# ══════════════════════════════════════════════════════════════════════════════
#  HISTÓRICO & MACROS
# ══════════════════════════════════════════════════════════════════════════════

class Historico:
    def __init__(self):
        self.dados = self._load()
    def _load(self):
        if os.path.exists(HIST_FILE):
            try:
                with open(HIST_FILE, "r", encoding="utf-8") as f: return json.load(f)
            except: pass
        return []
    def salvar(self, cmd):
        self.dados = [x for x in self.dados if x["cmd"].lower() != cmd.lower()]
        self.dados.insert(0, {"cmd": cmd, "ts": datetime.now().strftime("%d/%m %H:%M")})
        self.dados = self.dados[:100]
        try:
            with open(HIST_FILE, "w", encoding="utf-8") as f: json.dump(self.dados, f, ensure_ascii=False, indent=2)
        except: pass
    def limpar(self):
        self.dados = []
        try: os.remove(HIST_FILE)
        except: pass
    def recentes(self, n=30): return self.dados[:n]

class Macros:
    def __init__(self):
        self.dados = self._load()
    def _load(self):
        if os.path.exists(MACROS_FILE):
            try:
                with open(MACROS_FILE, "r", encoding="utf-8") as f: return json.load(f)
            except: pass
        return {}
    def _save(self):
        with open(MACROS_FILE, "w", encoding="utf-8") as f: json.dump(self.dados, f, ensure_ascii=False, indent=2)
    def adicionar(self, nome, cmds): self.dados[nome.lower()] = cmds; self._save()
    def remover(self, nome):
        if nome.lower() in self.dados: del self.dados[nome.lower()]; self._save(); return True
        return False
    def listar(self): return self.dados

# ══════════════════════════════════════════════════════════════════════════════
#  MOTOR DE INTENÇÕES
# ══════════════════════════════════════════════════════════════════════════════

def _n(t): 
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', t.lower()) if unicodedata.category(c) != 'Mn')

INTENCOES = [
    # ── Perguntas inteligentes (prioridade alta) ──────────────────────────────
    (["previsao do tempo", "previsão do tempo", "clima de", "tempo em",
      "como esta o tempo", "como está o tempo", "vai chover",
      "temperatura em", "clima amanha", "clima hoje"],                 "clima",          True),
    (["noticias", "notícias", "o que aconteceu", "novidades",
      "manchetes", "noticias do dia", "noticias sobre"],               "noticias",       True),
    (["traduz", "traduzir", "traduza", "como se diz",
      "como fala", "em ingles", "em espanhol", "em frances",
      "tradução de", "traducao de"],                                   "traduzir",       True),
    (["quanto e", "quanto é", "calcul", "quanto da",
      "quanto dá", "resultado de", "quanto fica"],                    "calcular",        True),
    (["converte", "converter", "converta", "em fahrenheit",
      "em celsius", "em miles", "em km", "dolar para",
      "euro para", "quantos reais", "cotacao", "cotação"],             "converter",      True),
    (["que horas sao", "que horas são", "horas", "hora atual",
      "que horas", "agora sao"],                                       "hora_atual",     False),
    (["que dia e hoje", "que dia é hoje", "data de hoje",
      "data atual", "qual e a data"],                                  "data_atual",     False),
    # ── YouTube & mídia ───────────────────────────────────────────────────────
    (["toca ", "play ", "reproduz ", "abre a musica ", "abre o video ",
      "coloca ", "passa a musica ", "quero ouvir ", "quero ver ",
      "bota ", "me mostra "],                                          "play_video",     True),
    (["pesquisa no youtube", "busca no youtube", "procura no youtube"],"pesquisar_yt",   True),
    # ── Sites ─────────────────────────────────────────────────────────────────
    (["abre o google", "vai no google", "entra no google",
      "vai pro google", "acessa o google"],                            "abrir_google",   False),
    (["abre o youtube", "vai no youtube", "entra no youtube",
      "vai pro youtube", "acessa o youtube"],                          "abrir_youtube",  False),
    (["twitter", "abrir twitter"],                                     "abrir_twitter",  False),
    (["whatsapp"],                                                     "abrir_whatsapp", False),
    (["gmail"],                                                        "abrir_gmail",    False),
    (["spotify"],                                                      "abrir_spotify",  False),
    (["netflix"],                                                      "abrir_netflix",  False),
    (["instagram"],                                                    "abrir_instagram",False),
    (["github"],                                                       "abrir_github",   False),
    (["chatgpt", "chat gpt"],                                         "abrir_chatgpt",  False),
    (["abre o site ", "vai para o site ", "abre o link "],            "abrir_site",     True),
    # ── Pesquisa ──────────────────────────────────────────────────────────────
    (["pesquisa", "busca", "procura", "pesquise", "googla"],          "pesquisar",      True),
    # ── Teclado / mouse ───────────────────────────────────────────────────────
    (["digita ", "escreve ", "digite ", "escreva "],                  "digitar",        True),
    (["clica em", "clique em", "clica no", "clique no",
      "clica na", "clique na"],                                        "clicar",         True),
    (["duplo clique", "clique duplo", "clica duas vezes"],            "duplo_clique",   False),
    (["clique direito", "botao direito"],                             "clique_direito",  False),
    (["aperta enter", "pressiona enter", "da enter"],                 "tecla_enter",    False),
    (["aperta espaco", "pressiona espaco"],                           "tecla_espaco",   False),
    (["aperta esc", "pressiona escape"],                              "tecla_esc",      False),
    (["copia tudo", "seleciona tudo"],                                "selecionar_tudo",False),
    (["copia", "ctrl c"],                                             "copiar",         False),
    (["cola", "ctrl v"],                                              "colar",          False),
    (["desfaz", "ctrl z"],                                            "desfazer",       False),
    (["salva", "ctrl s"],                                             "salvar",         False),
    # ── Janelas ───────────────────────────────────────────────────────────────
    (["fecha janela"],                                                "fechar_janela",  False),
    (["nova aba", "nova tab"],                                        "nova_aba",       False),
    (["fecha aba", "fecha tab"],                                      "fechar_aba",     False),
    (["atualiza", "recarrega", "refresh"],                            "atualizar",      False),
    (["minimiza"],                                                    "minimizar",      False),
    (["maximiza"],                                                    "maximizar",      False),
    (["alt tab", "troca janela"],                                     "alt_tab",        False),
    # ── Scroll ────────────────────────────────────────────────────────────────
    (["rola para baixo", "desce", "scroll down"],                     "rolar_baixo",    False),
    (["rola para cima", "sobe", "scroll up"],                         "rolar_cima",     False),
    (["fim da pagina", "fim da página"],                              "fim_pagina",     False),
    (["topo da pagina", "topo da página"],                            "topo_pagina",    False),
    # ── Print ─────────────────────────────────────────────────────────────────
    (["tira print", "screenshot", "printscreen", "captura tela"],     "print",          False),
    # ── Mouse ─────────────────────────────────────────────────────────────────
    (["posicao do mouse", "onde o mouse", "onde esta o mouse"],       "pos_mouse",      False),
    (["move o mouse para", "move mouse"],                             "mover_mouse",    True),
    # ── Apps Windows ──────────────────────────────────────────────────────────
    (["calculadora"],                                                 "app_calc",       False),
    (["bloco de notas", "notepad"],                                   "app_notepad",    False),
    (["explorador", "gerenciador de arquivos"],                       "app_explorer",   False),
    (["gerenciador de tarefas", "task manager"],                      "app_taskmgr",    False),
    (["configuracoes do windows", "painel de controle"],              "app_config",     False),
    (["cmd", "terminal", "prompt"],                                   "app_cmd",        False),
    (["paint"],                                                       "app_paint",      False),
    # ── Volume / mídia ────────────────────────────────────────────────────────
    (["aumenta o volume", "sobe o volume"],                           "vol_up",         False),
    (["diminui o volume", "baixa o volume"],                          "vol_down",       False),
    (["proxima musica", "próxima música", "avanca musica"],           "midia_prox",     False),
    (["volta a musica", "musica anterior"],                           "midia_ant",      False),
    (["pausa", "pausar", "play pause"],                               "midia_pause",    False),
    # ── Notas ─────────────────────────────────────────────────────────────────
    (["anota ", "salva nota ", "lembra "],                            "anotar",         True),
    (["mostra notas", "ver notas", "minhas notas"],                   "ver_notas",      False),
    (["limpa notas", "apaga notas"],                                  "limpar_notas",   False),
    # ── Macros ────────────────────────────────────────────────────────────────
    (["cria macro ", "nova macro "],                                  "criar_macro",    True),
    (["executa macro ", "roda macro ", "macro "],                     "executar_macro", True),
    (["lista macros", "ver macros"],                                  "listar_macros",  False),
    (["remove macro "],                                               "remover_macro",  True),
    # ── Sistema ───────────────────────────────────────────────────────────────
    (["desliga o pc", "desligar computador"],                         "desligar",       False),
    (["reinicia o pc", "reiniciar"],                                  "reiniciar",      False),
    (["bloqueia o pc", "travar tela", "bloquear"],                    "bloquear",       False),
    # ── Meta ──────────────────────────────────────────────────────────────────
    (["historico", "meus comandos"],                                  "ver_historico",  False),
    (["limpa historico"],                                             "limpar_hist",    False),
    (["ajuda", "help", "comandos", "o que voce faz"],                 "ajuda",          False),
    (["sair", "fechar robo", "tchau", "ate logo", "exit"],            "sair",           False),
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
                    param = cmd[idx + len(p):].strip()
                    param = re.sub(r'^(o |a |os |as |um |uma |de |da |do )', '', param, flags=re.I).strip()
                return acao, param or None
    # Fuzzy
    melhor, sc = None, 0.0
    for padroes, acao, _ in INTENCOES:
        for p in padroes:
            s = SequenceMatcher(None, cn, _n(p)).ratio()
            if s > sc: sc, melhor = s, acao
    if sc > 0.65: return melhor, None
    # Fallback: tenta responder como pergunta geral
    if any(cn.startswith(w) for w in ["o que e", "o que é", "quem e", "quem é",
                                       "como funciona", "por que", "para que",
                                       "quando foi", "onde fica", "qual e", "qual é",
                                       "me fala", "me conta", "me explica"]):
        return "pergunta_geral", cmd
    return None, None

# ══════════════════════════════════════════════════════════════════════════════
#  ROBÔ
# ══════════════════════════════════════════════════════════════════════════════

class Robo:
    def __init__(self, log_cb, hist_ui_cb, status_cb):
        self.log        = log_cb
        self.hist_ui    = hist_ui_cb
        self.set_status = status_cb
        self.hist       = Historico()
        self.macros     = Macros()
        self._macro_gravando = None
        self._macro_cmds     = []

    def executar(self, cmd: str):
        cmd = cmd.strip()
        if not cmd: return
        # Gravando macro?
        if self._macro_gravando:
            if _n(cmd) in ["fim macro", "termina macro", "para macro", "stop macro"]:
                self.macros.adicionar(self._macro_gravando, self._macro_cmds)
                msg = f"✅ Macro '{self._macro_gravando}' salva ({len(self._macro_cmds)} comandos)!"
                self.log(msg, "sucesso"); falar(msg)
                self._macro_gravando = None; self._macro_cmds = []
                self.hist_ui(); return
            self._macro_cmds.append(cmd)
            self.log(f"  [gravando] {cmd}", "info"); return

        self.log(f"Você » {cmd}", "usuario")
        self.hist.salvar(cmd); self.hist_ui()

        acao, param = detectar_intencao(cmd)
        dispatch = {
            # IA / web
            "clima":           lambda: self._clima(param, cmd),
            "noticias":        lambda: self._noticias(param),
            "traduzir":        lambda: self._traduzir(cmd, param),
            "calcular":        lambda: self._calcular(param or cmd),
            "converter":       lambda: self._converter(param or cmd),
            "pergunta_geral":  lambda: self._pergunta_geral(param or cmd),
            # YouTube
            "play_video":      lambda: self._play(param),
            "pesquisar_yt":    lambda: self._pesquisar_yt(param),
            # Sites
            "abrir_google":    lambda: self._site("https://www.google.com.br", "Google"),
            "abrir_youtube":   lambda: self._site("https://www.youtube.com", "YouTube"),
            "abrir_twitter":   lambda: self._site("https://x.com", "Twitter/X"),
            "abrir_whatsapp":  lambda: self._site("https://web.whatsapp.com", "WhatsApp Web"),
            "abrir_gmail":     lambda: self._site("https://mail.google.com", "Gmail"),
            "abrir_spotify":   lambda: self._site("https://open.spotify.com", "Spotify"),
            "abrir_netflix":   lambda: self._site("https://www.netflix.com", "Netflix"),
            "abrir_instagram": lambda: self._site("https://www.instagram.com", "Instagram"),
            "abrir_github":    lambda: self._site("https://github.com", "GitHub"),
            "abrir_chatgpt":   lambda: self._site("https://chat.openai.com", "ChatGPT"),
            "abrir_site":      lambda: self._site_generico(param),
            "pesquisar":       lambda: self._pesquisar(param),
            # Teclado
            "digitar":         lambda: self._digitar(param),
            "clicar":          lambda: pyautogui.click(),
            "duplo_clique":    lambda: pyautogui.doubleClick(),
            "clique_direito":  lambda: pyautogui.rightClick(),
            "tecla_enter":     lambda: pyautogui.press("enter"),
            "tecla_espaco":    lambda: pyautogui.press("space"),
            "tecla_esc":       lambda: pyautogui.press("escape"),
            "selecionar_tudo": lambda: pyautogui.hotkey("ctrl", "a"),
            "copiar":          lambda: pyautogui.hotkey("ctrl", "c"),
            "colar":           lambda: pyautogui.hotkey("ctrl", "v"),
            "desfazer":        lambda: pyautogui.hotkey("ctrl", "z"),
            "salvar":          lambda: pyautogui.hotkey("ctrl", "s"),
            # Janelas
            "fechar_janela":   lambda: pyautogui.hotkey("alt", "F4"),
            "nova_aba":        lambda: pyautogui.hotkey("ctrl", "t"),
            "fechar_aba":      lambda: pyautogui.hotkey("ctrl", "w"),
            "atualizar":       lambda: pyautogui.press("F5"),
            "minimizar":       lambda: pyautogui.hotkey("win", "down"),
            "maximizar":       lambda: pyautogui.hotkey("win", "up"),
            "alt_tab":         lambda: pyautogui.hotkey("alt", "tab"),
            # Scroll
            "rolar_baixo":     lambda: pyautogui.scroll(-6),
            "rolar_cima":      lambda: pyautogui.scroll(6),
            "fim_pagina":      lambda: pyautogui.press("end"),
            "topo_pagina":     lambda: pyautogui.press("home"),
            # Print
            "print":           lambda: self._print(),
            # Mouse
            "pos_mouse":       lambda: self._pos_mouse(),
            "mover_mouse":     lambda: self._mover_mouse(param),
            # Apps
            "app_calc":        lambda: self._app("calc.exe","Calculadora"),
            "app_notepad":     lambda: self._app("notepad.exe","Bloco de notas"),
            "app_explorer":    lambda: self._app("explorer.exe","Explorador"),
            "app_taskmgr":     lambda: self._app("taskmgr.exe","Gerenciador de tarefas"),
            "app_config":      lambda: self._app("ms-settings:","Configurações"),
            "app_cmd":         lambda: self._app("cmd.exe","Terminal"),
            "app_paint":       lambda: self._app("mspaint.exe","Paint"),
            # Volume
            "vol_up":          lambda: [pyautogui.press("volumeup") for _ in range(5)],
            "vol_down":        lambda: [pyautogui.press("volumedown") for _ in range(5)],
            "midia_prox":      lambda: pyautogui.press("nexttrack"),
            "midia_ant":       lambda: pyautogui.press("prevtrack"),
            "midia_pause":     lambda: pyautogui.press("playpause"),
            # Notas
            "anotar":          lambda: self._anotar(param),
            "ver_notas":       lambda: self._ver_notas(),
            "limpar_notas":    lambda: self._limpar_notas(),
            # Macros
            "criar_macro":     lambda: self._iniciar_macro(param),
            "executar_macro":  lambda: self._executar_macro(param),
            "listar_macros":   lambda: self._listar_macros(),
            "remover_macro":   lambda: self._remover_macro(param),
            # Utilitários
            "hora_atual":      lambda: self._hora(),
            "data_atual":      lambda: self._data(),
            "desligar":        lambda: self._desligar(),
            "reiniciar":       lambda: self._reiniciar(),
            "bloquear":        lambda: self._bloquear(),
            # Meta
            "ver_historico":   lambda: self._ver_hist(),
            "limpar_hist":     lambda: self._limpar_hist(),
            "ajuda":           lambda: self._ajuda(),
            "sair":            lambda: self._sair(),
        }
        if acao and acao in dispatch:
            try: dispatch[acao]()
            except Exception as e: self.log(f"Robô » ❌ Erro: {e}", "erro")
        else:
            # Tenta como pergunta geral
            self._pergunta_geral(cmd)

    # ══ AÇÕES IA / WEB ════════════════════════════════════════════════════════

    def _clima(self, param, cmd_original):
        # Detecta número de dias
        dias = 1
        m = re.search(r'(\d+)\s*dias?', _n(cmd_original))
        if m: dias = int(m.group(1))
        elif "semana" in _n(cmd_original): dias = 7
        # Detecta cidade
        cidade = CFG.get("cidade_clima", "São Paulo")
        # Tenta extrair cidade do comando
        for prep in ["em ", "de ", "para ", "do ", "da "]:
            if prep in _n(cmd_original):
                partes = _n(cmd_original).split(prep, 1)
                candidato = partes[-1].strip().split()[0] if partes[-1].strip() else ""
                if len(candidato) > 2 and candidato not in ["hoje","amanha","semana","dias","tempo"]:
                    cidade = candidato.capitalize()
                    break
        if param and len(param) > 2:
            cidade = param.split()[0].capitalize()

        self.set_status(f"Buscando clima de {cidade}...")
        self.log(f"Robô » 🌤️ Buscando clima de {cidade} ({dias} dia{'s' if dias>1 else ''})...", "robo")

        def _run():
            resp = buscar_clima(cidade, dias)
            self.log(f"Robô » {resp}", "robo")
            # Fala versão resumida
            linhas = resp.split("\n")
            falar(linhas[0] + (". " + linhas[1] if len(linhas) > 1 else ""))
            self.set_status("Pronto.")
        threading.Thread(target=_run, daemon=True).start()

    def _noticias(self, param):
        tema = param or ""
        self.log(f"Robô » 📰 Buscando notícias{' sobre ' + tema if tema else ''}...", "robo")
        self.set_status("Buscando notícias...")
        def _run():
            resp = buscar_noticias(tema)
            self.log(f"Robô » {resp}", "robo")
            linhas = resp.split("\n")
            falar(linhas[0] + (". " + linhas[1] if len(linhas) > 1 else ""))
            self.set_status("Pronto.")
        threading.Thread(target=_run, daemon=True).start()

    def _traduzir(self, cmd_orig, param):
        # Extrai texto entre aspas, ou após "traduz"
        m = re.search(r'["\'](.+?)["\']', cmd_orig)
        texto = m.group(1) if m else (param or "")
        # Remove o idioma alvo do texto
        for w in ["para o ingles","para ingles","para o espanhol","para espanhol",
                  "para o frances","para frances","para o alemao","para alemao",
                  "para italiano","para japones","para chines","para russo",
                  "para portugues"]:
            texto = re.sub(w, "", _n(texto), flags=re.I).strip()
        if not texto:
            self.log("Robô » O que você quer traduzir? Ex: traduz 'olá mundo' para inglês", "robo"); return
        lang = detectar_idioma_alvo(cmd_orig)
        self.log(f"Robô » 🌐 Traduzindo...", "robo")
        def _run():
            resp = traduzir(texto, lang)
            self.log(f"Robô » {resp}", "robo")
            falar(resp.replace("🌐 Tradução para inglês:\n  ", "Tradução: "))
        threading.Thread(target=_run, daemon=True).start()

    def _calcular(self, expr):
        # Extrai expressão numérica
        m = re.search(r'[\d\s\+\-\*\/\(\)\.\,\%]+', expr)
        if m:
            resp = calcular(m.group().strip())
        else:
            resp = calcular(expr)
        self.log(f"Robô » {resp}", "robo")
        falar(resp.replace("🧮 ", ""))

    def _converter(self, expr):
        resp = converter_unidade(expr)
        if resp:
            self.log(f"Robô » {resp}", "robo")
            falar(resp)
        else:
            self._pergunta_geral(expr)

    def _pergunta_geral(self, pergunta):
        self.log(f"Robô » 🔎 Buscando resposta...", "robo")
        self.set_status("Pesquisando...")
        def _run():
            resp = perguntar_web(pergunta)
            if resp:
                self.log(f"Robô » {resp}", "robo")
                # Fala resumo (primeiros 200 chars)
                falar(re.sub(r'🔎\s*', '', resp)[:220])
            else:
                msg = "Não encontrei uma resposta direta. Vou abrir o Google."
                self.log(f"Robô » {msg}", "robo")
                falar(msg)
                webbrowser.open(f"https://www.google.com.br/search?q={urllib.parse.quote(pergunta)}")
            self.set_status("Pronto.")
        threading.Thread(target=_run, daemon=True).start()

    # ══ AÇÕES PC ══════════════════════════════════════════════════════════════

    def _site(self, url, nome):
        self.log(f"Robô » 🌐 Abrindo {nome}...", "robo")
        falar(f"Abrindo {nome}"); webbrowser.open(url)

    def _site_generico(self, param):
        if not param: self.log("Robô » Qual site?", "robo"); return
        url = param if param.startswith("http") else f"https://{param}"
        self.log(f"Robô » 🌐 Abrindo {url}...", "robo")
        falar(f"Abrindo"); webbrowser.open(url)

    def _pesquisar(self, termo):
        if not termo: self.log("Robô » O que pesquisar?", "robo"); return
        self.log(f"Robô » 🔍 Pesquisando '{termo}'...", "robo")
        falar(f"Pesquisando {termo}")
        webbrowser.open(f"https://www.google.com.br/search?q={urllib.parse.quote(termo)}")

    def _pesquisar_yt(self, termo):
        if not termo: self.log("Robô » O que pesquisar?", "robo"); return
        self.log(f"Robô » 🎬 YouTube: '{termo}'...", "robo")
        falar(f"Pesquisando {termo} no YouTube")
        webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote(termo)}")

    def _play(self, termo):
        if not termo: self.log("Robô » Qual música ou vídeo?", "robo"); return
        self.log(f"Robô » 🎵 Procurando '{termo}' no YouTube...", "robo")
        falar(f"Procurando {termo}")
        self.set_status(f"Buscando: {termo}...")
        def _run():
            url = buscar_primeiro_yt(termo)
            if url:
                self.log(f"Robô » ▶ Abrindo vídeo!", "sucesso")
                webbrowser.open(url)
            else:
                webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote(termo)}")
            self.set_status("Pronto.")
        threading.Thread(target=_run, daemon=True).start()

    def _digitar(self, texto):
        if not texto: return
        self.log(f"Robô » ⌨️ Digitando...", "robo")
        time.sleep(0.3); pyperclip.copy(texto); pyautogui.hotkey('ctrl','v')

    def _print(self):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        os.makedirs(desktop, exist_ok=True)
        p = os.path.join(desktop, f"screenshot_{int(time.time())}.png")
        pyautogui.screenshot(p)
        self.log(f"Robô » 📸 Screenshot: {p}", "sucesso")
        falar("Screenshot salvo na área de trabalho")

    def _pos_mouse(self):
        x, y = pyautogui.position()
        msg = f"Mouse em X={x}, Y={y}"
        self.log(f"Robô » 🖱️ {msg}", "robo"); falar(msg)

    def _mover_mouse(self, param):
        if param:
            nums = re.findall(r'\d+', param)
            if len(nums) >= 2:
                pyautogui.moveTo(int(nums[0]), int(nums[1]), duration=0.4)
                self.log(f"Robô » 🖱️ Mouse → ({nums[0]}, {nums[1]})", "robo"); return
        self.log("Robô » Informe coordenadas. Ex: move o mouse para 500 300", "robo")

    def _app(self, exe, nome):
        try:
            subprocess.Popen(exe, shell=True)
            self.log(f"Robô » ✅ Abrindo {nome}...", "sucesso"); falar(f"Abrindo {nome}")
        except Exception as e:
            self.log(f"Robô » ❌ Erro: {e}", "erro")

    def _anotar(self, texto):
        if not texto: self.log("Robô » O que anotar?", "robo"); return
        ts = datetime.now().strftime("%d/%m/%Y %H:%M")
        with open(NOTAS_FILE, "a", encoding="utf-8") as f: f.write(f"[{ts}] {texto}\n")
        self.log(f"Robô » 📝 Anotado!", "sucesso"); falar("Nota salva")

    def _ver_notas(self):
        if not os.path.exists(NOTAS_FILE): self.log("Robô » Nenhuma nota.", "robo"); return
        with open(NOTAS_FILE, "r", encoding="utf-8") as f: notas = f.read().strip()
        if notas:
            self.log("── NOTAS ──", "info")
            for l in notas.split("\n")[-15:]: self.log(l, "info")
        else: self.log("Robô » Nenhuma nota.", "robo")

    def _limpar_notas(self):
        try: os.remove(NOTAS_FILE)
        except: pass
        self.log("Robô » ✅ Notas apagadas.", "sucesso")

    def _iniciar_macro(self, nome):
        if not nome: self.log("Robô » Qual nome da macro?","robo"); return
        self._macro_gravando = nome.strip(); self._macro_cmds = []
        msg = f"Gravando macro '{nome}'. Digite comandos. Diga 'fim macro' para terminar."
        self.log(f"Robô » 🔴 {msg}", "info"); falar(f"Gravando macro {nome}")

    def _executar_macro(self, nome):
        if not nome: return
        cmds = self.macros.listar().get(nome.strip().lower())
        if not cmds: self.log(f"Robô » ❌ Macro '{nome}' não encontrada.", "erro"); return
        self.log(f"Robô » ▶ Executando macro '{nome}'...", "sucesso")
        falar(f"Executando macro {nome}")
        for c in cmds: time.sleep(0.3); self.executar(c)

    def _listar_macros(self):
        m = self.macros.listar()
        if not m: self.log("Robô » Nenhuma macro.", "robo"); return
        self.log("── MACROS ──", "info")
        for nome, cmds in m.items(): self.log(f"  • {nome}: {len(cmds)} comandos", "info")

    def _remover_macro(self, nome):
        if nome and self.macros.remover(nome.strip()):
            self.log(f"Robô » ✅ Macro '{nome}' removida.", "sucesso")
        else: self.log(f"Robô » ❌ Macro não encontrada.", "erro")

    def _hora(self):
        h = datetime.now().strftime("%H:%M:%S")
        msg = f"São {h}"
        self.log(f"Robô » ⏰ {msg}", "robo"); falar(msg)

    def _data(self):
        d = datetime.now().strftime("%d/%m/%Y, %A")
        msg = f"Hoje é {d}"
        self.log(f"Robô » 📅 {msg}", "robo"); falar(msg)

    def _desligar(self):
        self.log("Robô » ⚠️ Desligando em 30s... (shutdown /a no CMD para cancelar)", "aviso")
        falar("Desligando em 30 segundos")
        subprocess.run("shutdown /s /t 30", shell=True)

    def _reiniciar(self):
        self.log("Robô » ⚠️ Reiniciando em 30s...", "aviso")
        falar("Reiniciando em 30 segundos")
        subprocess.run("shutdown /r /t 30", shell=True)

    def _bloquear(self):
        self.log("Robô » 🔒 Bloqueando tela...", "robo"); falar("Bloqueando")
        import ctypes; ctypes.windll.user32.LockWorkStation()

    def _ver_hist(self):
        r = self.hist.recentes(15)
        if not r: self.log("Robô » Histórico vazio.","robo"); return
        self.log("── HISTÓRICO ──", "info")
        for i, e in enumerate(r, 1): self.log(f"  {i:2}. [{e['ts']}] {e['cmd']}", "info")

    def _limpar_hist(self):
        self.hist.limpar(); self.hist_ui()
        self.log("Robô » ✅ Histórico apagado.", "sucesso")

    def _ajuda(self):
        self.log("""
╔══════════════════════════════════════════════════════╗
║          🤖 ROBÔ ASSISTENTE PRO v4.0                 ║
╠══════════════════════════════════════════════════════╣
║ 🌤️  CLIMA & TEMPO                                    ║
║   "previsão do tempo em São Paulo"                   ║
║   "clima nos próximos 7 dias"                        ║
║   "vai chover amanhã?"                               ║
║                                                      ║
║ 📰 NOTÍCIAS                                          ║
║   "notícias do dia"                                  ║
║   "notícias sobre tecnologia"                        ║
║                                                      ║
║ 🌐 TRADUÇÃO                                          ║
║   "traduz 'bom dia' para inglês"                     ║
║   "como se diz obrigado em espanhol"                 ║
║                                                      ║
║ 🧮 CÁLCULOS & CONVERSÕES                             ║
║   "quanto é 25 * 4 + 10"                             ║
║   "converte 100 dólares para reais"                  ║
║   "converte 37°C para fahrenheit"                    ║
║   "100 km para milhas"                               ║
║                                                      ║
║ ❓ PERGUNTAS GERAIS                                  ║
║   "o que é fotossíntese"                             ║
║   "quem foi Einstein"                                ║
║   "me fala sobre a lua"                              ║
║                                                      ║
║ 🎵 MÚSICA & VÍDEO                                    ║
║   "toca november rain"                               ║
║   "quero ouvir lofi hip hop"                         ║
║   "bota uma música do Metallica"                     ║
║                                                      ║
║ 🌐 SITES: Google/YouTube/Gmail/Netflix/Spotify       ║
║ ⌨️  TECLADO: digita/aperta Enter/copia/cola/salva    ║
║ 🖥️  APPS: calculadora/notepad/explorador/terminal   ║
║ 📝 NOTAS: anota [texto] / mostra notas               ║
║ 🎬 MACROS: cria macro [nome] / executa macro [nome]  ║
║ ⚙️  CONFIG: ver config.json para alterar cidade/voz  ║
╚══════════════════════════════════════════════════════╝""", "info")
        falar("Mostrando todos os comandos disponíveis")

    def _sair(self):
        self.log("Robô » Até logo! 👋", "robo"); falar("Até logo!")
        time.sleep(1); os._exit(0)


# ══════════════════════════════════════════════════════════════════════════════
#  MODO VOZ CONTÍNUO
# ══════════════════════════════════════════════════════════════════════════════

class VozContinua:
    def __init__(self, robo, log_cb, status_cb, btn_cb):
        self.robo      = robo
        self.log       = log_cb
        self.set_status= status_cb
        self.set_btn   = btn_cb
        self.ativo     = False
        self._thread   = None
        self._rec      = sr.Recognizer() if VOZ_OK else None

    def toggle(self):
        if self.ativo: self.parar()
        else: self.iniciar()

    def iniciar(self):
        if not VOZ_OK: self.log("Robô » ❌ SpeechRecognition não instalado.", "erro"); return
        self.ativo = True
        self.set_btn("🔴 VOZ ATIVA", "#aa0022")
        self.set_status("🎙 Modo voz contínuo — pode falar!")
        falar("Modo voz ativado. Pode falar.")
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def parar(self):
        self.ativo = False
        self.set_btn("🎙 VOZ", "#0050bb")
        self.set_status("Pronto.")
        falar("Modo voz desativado.")

    def _loop(self):
        if not self._rec: return
        while self.ativo:
            try:
                with sr.Microphone() as src:
                    self._rec.adjust_for_ambient_noise(src, duration=0.3)
                    self.set_status("🎙 Ouvindo...")
                    audio = self._rec.listen(src, timeout=4, phrase_time_limit=10)
                txt = self._rec.recognize_google(audio, language=CFG.get("idioma_voz","pt-BR"))
                if txt:
                    self.set_status("⚙️ Processando...")
                    self.robo.executar(txt)
            except sr.WaitTimeoutError:
                pass  # Silêncio — continua ouvindo
            except sr.UnknownValueError:
                pass  # Não entendeu — continua
            except sr.RequestError:
                self.log("Robô » ⚠️ Erro de conexão no reconhecimento de voz.", "aviso")
                time.sleep(3)
            except Exception as e:
                time.sleep(1)
            if self.ativo:
                self.set_status("🎙 Ouvindo...")


# ══════════════════════════════════════════════════════════════════════════════
#  INTERFACE PRO v4
# ══════════════════════════════════════════════════════════════════════════════

C = {
    "bg":       "#080c14", "panel":    "#0d1220", "panel2":   "#111827",
    "borda":    "#1a2d55", "acento":   "#00e5ff", "acento2":  "#0050bb",
    "verde":    "#00ff99", "amarelo":  "#ffd600", "vermelho": "#ff3355",
    "laranja":  "#ff8800", "texto":    "#ccd8f0", "dim":      "#3a5070",
    "usuario":  "#00e5ff", "robo":     "#00ff99", "info":     "#ffd600",
    "sucesso":  "#00ff99", "erro":     "#ff3355", "aviso":    "#ff8800",
    "hist_bg":  "#060a12", "hist_item":"#0c1020", "hist_hov": "#152040",
    "tab_sel":  "#0d1a35",
}
FM = ("Consolas", 11)
FT = ("Consolas", 13, "bold")
FS = ("Consolas", 9)
FB = ("Consolas", 10, "bold")
FH = ("Consolas", 8)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 Robô Assistente PRO v4.0")
        self.root.geometry("1040x700")
        self.root.configure(bg=C["bg"])
        self.root.resizable(True, True)
        self.root.minsize(800, 520)
        self._hist_idx  = -1
        self._icon_f    = 0
        self._aba_atual = "chat"

        self._build()

        self.robo = Robo(self._log, self._refresh_hist, self._set_status)
        self.voz  = VozContinua(self.robo, self._log, self._set_status, self._set_btn_voz)

        # Saudação inicial
        msg = saudacao()
        self._log(f"Robô » {msg}", "sucesso")
        threading.Thread(target=lambda: falar(msg), daemon=True).start()

        self._log("💡 Dica: 'previsão do tempo 7 dias', 'toca uma música', 'notícias do dia'", "info")
        self._log("💡 Clique em '🎙 VOZ' para modo contínuo — sem precisar clicar toda vez!", "info")

        if CFG.get("voz_continua", False):
            self.root.after(1500, self.voz.iniciar)

        self._anim_icon()
        self._refresh_hist()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        # Header
        hdr = tk.Frame(self.root, bg=C["panel"])
        hdr.grid(row=0, column=0, sticky="ew")
        tk.Frame(hdr, bg=C["acento"], height=2).pack(fill="x")
        hi = tk.Frame(hdr, bg=C["panel"], padx=16, pady=9)
        hi.pack(fill="x")

        self.cv = tk.Canvas(hi, width=36, height=36, bg=C["panel"], highlightthickness=0)
        self.cv.pack(side="left", padx=(0,12))
        tk.Label(hi, text="ROBÔ ASSISTENTE", font=FT, fg=C["acento"], bg=C["panel"]).pack(side="left")
        tk.Label(hi, text=" PRO v4.0", font=FS, fg=C["dim"], bg=C["panel"]).pack(side="left", pady=(4,0))

        # Botões header direita
        bframe = tk.Frame(hi, bg=C["panel"])
        bframe.pack(side="right")

        # Toggle autostart
        self.var_auto = tk.BooleanVar(value=check_autostart())
        tk.Checkbutton(bframe, text="Iniciar com Windows",
                       font=FS, fg=C["dim"], bg=C["panel"],
                       activebackground=C["panel"], selectcolor=C["panel2"],
                       variable=self.var_auto,
                       command=self._toggle_autostart).pack(side="right", padx=(8,0))

        # Toggle voz resposta
        self.var_resp_voz = tk.BooleanVar(value=CFG.get("resposta_voz", True))
        tk.Checkbutton(bframe, text="Voz",
                       font=FS, fg=C["dim"], bg=C["panel"],
                       activebackground=C["panel"], selectcolor=C["panel2"],
                       variable=self.var_resp_voz,
                       command=self._toggle_voz_resp).pack(side="right", padx=(8,0))

        self.lbl_online = tk.Label(bframe, text="● ONLINE", font=FS, fg=C["verde"], bg=C["panel"])
        self.lbl_online.pack(side="right")
        tk.Frame(hdr, bg=C["borda"], height=1).pack(fill="x")

        # Corpo
        corpo = tk.Frame(self.root, bg=C["bg"])
        corpo.grid(row=1, column=0, sticky="nsew")
        corpo.columnconfigure(0, weight=3)
        corpo.columnconfigure(1, weight=1, minsize=200)
        corpo.rowconfigure(0, weight=1)

        # Esquerda
        left = tk.Frame(corpo, bg=C["bg"])
        left.grid(row=0, column=0, sticky="nsew", padx=(10,0), pady=8)
        left.rowconfigure(1, weight=1); left.columnconfigure(0, weight=1)

        # Abas
        abas = tk.Frame(left, bg=C["bg"])
        abas.grid(row=0, column=0, sticky="ew", pady=(0,4))
        self.btn_tab_chat  = self._mk_tab(abas, "💬 CHAT",  "chat")
        self.btn_tab_notas = self._mk_tab(abas, "📝 NOTAS", "notas")
        self.btn_tab_macro = self._mk_tab(abas, "🎬 MACROS","macros")
        self.btn_tab_cfg   = self._mk_tab(abas, "⚙️ CONFIG", "config")
        for b in (self.btn_tab_chat, self.btn_tab_notas,
                  self.btn_tab_macro, self.btn_tab_cfg):
            b.pack(side="left", padx=(0,2))

        # Frames de conteúdo
        self.fr_chat  = self._mk_frame(left)
        self.fr_notas = self._mk_frame(left)
        self.fr_macro = self._mk_frame(left)
        self.fr_cfg   = self._mk_frame(left)

        # Chat
        self.chat = scrolledtext.ScrolledText(
            self.fr_chat, font=FM, bg=C["panel2"], fg=C["texto"],
            insertbackground=C["acento"], relief="flat", bd=0,
            wrap="word", state="disabled",
            selectbackground=C["borda"], padx=10, pady=8)
        self.chat.grid(sticky="nsew")
        for t, cor, extra in [
            ("usuario", C["usuario"], {"font":("Consolas",11,"bold")}),
            ("robo",    C["robo"],    {}), ("info",    C["amarelo"], {}),
            ("sucesso", C["verde"],   {}), ("erro",    C["vermelho"],{}),
            ("aviso",   C["laranja"], {}), ("dim_ts",  C["dim"],     {}),
        ]:
            self.chat.tag_config(t, foreground=cor, **extra)

        # Notas
        self.txt_notas = scrolledtext.ScrolledText(
            self.fr_notas, font=FM, bg=C["panel2"], fg=C["texto"],
            insertbackground=C["acento"], relief="flat", bd=0, padx=10, pady=8)
        self.txt_notas.grid(sticky="nsew")
        nr = tk.Frame(self.fr_notas, bg=C["bg"])
        nr.grid(row=1, column=0, sticky="e", pady=(4,0))
        for txt, cmd in [("💾 Salvar", self._salvar_notas), ("🔄 Recarregar", self._carregar_notas)]:
            tk.Button(nr, text=txt, font=FS, bg=C["acento2"], fg="white",
                      relief="flat", bd=0, padx=10, pady=4, cursor="hand2",
                      command=cmd).pack(side="left", padx=(0,4))

        # Macros
        self.txt_macro = scrolledtext.ScrolledText(
            self.fr_macro, font=FM, bg=C["panel2"], fg=C["texto"],
            insertbackground=C["acento"], relief="flat", bd=0,
            state="disabled", padx=10, pady=8)
        self.txt_macro.grid(sticky="nsew")

        # Config
        self._build_config(self.fr_cfg)

        self._trocar_aba("chat")

        # Direita: histórico
        right = tk.Frame(corpo, bg=C["bg"], pady=8)
        right.grid(row=0, column=1, sticky="nsew", padx=(4,10))
        right.rowconfigure(2, weight=1); right.columnconfigure(0, weight=1)

        tk.Label(right, text="HISTÓRICO RÁPIDO", font=FH, fg=C["dim"], bg=C["bg"]
                 ).grid(row=0, column=0, sticky="w")

        self.hist_busca = tk.Entry(right, font=FS, bg=C["hist_item"], fg=C["texto"],
                                   insertbackground=C["acento"], relief="flat", bd=3,
                                   highlightthickness=1, highlightcolor=C["acento"],
                                   highlightbackground=C["borda"])
        self.hist_busca.grid(row=1, column=0, sticky="ew", pady=(4,4))
        self.hist_busca.insert(0, "🔎 filtrar...")
        self.hist_busca.bind("<FocusIn>",  lambda e: self._busca_focus(True))
        self.hist_busca.bind("<FocusOut>", lambda e: self._busca_focus(False))
        self.hist_busca.bind("<KeyRelease>", lambda e: self._refresh_hist())

        hcf = tk.Frame(right, bg=C["hist_bg"])
        hcf.grid(row=2, column=0, sticky="nsew")
        hcf.rowconfigure(0, weight=1); hcf.columnconfigure(0, weight=1)
        self.hist_canvas = tk.Canvas(hcf, bg=C["hist_bg"], highlightthickness=0)
        hsb = tk.Scrollbar(hcf, orient="vertical", command=self.hist_canvas.yview)
        self.hist_inner = tk.Frame(self.hist_canvas, bg=C["hist_bg"])
        self.hist_inner.bind("<Configure>", lambda e: self.hist_canvas.configure(
            scrollregion=self.hist_canvas.bbox("all")))
        self.hist_canvas.create_window((0,0), window=self.hist_inner, anchor="nw")
        self.hist_canvas.configure(yscrollcommand=hsb.set)
        self.hist_canvas.grid(row=0, column=0, sticky="nsew")
        hsb.grid(row=0, column=1, sticky="ns")

        tk.Button(right, text="🗑 limpar", font=FH, fg=C["dim"],
                  bg=C["hist_bg"], relief="flat", bd=0, cursor="hand2",
                  command=lambda: threading.Thread(
                      target=self.robo.executar, args=("limpa histórico",), daemon=True).start()
                  ).grid(row=3, column=0, sticky="e", pady=(4,0))

        # Entrada
        bot = tk.Frame(self.root, bg=C["panel"], padx=12, pady=8)
        bot.grid(row=2, column=0, sticky="ew")
        tk.Frame(bot, bg=C["borda"], height=1).pack(fill="x", pady=(0,8))
        ir = tk.Frame(bot, bg=C["panel"])
        ir.pack(fill="x")

        tk.Label(ir, text="▶", font=("Consolas",14,"bold"),
                 fg=C["acento"], bg=C["panel"]).pack(side="left", padx=(0,6))

        self.entrada = tk.Entry(ir, font=("Consolas",13),
                                bg=C["hist_item"], fg=C["texto"],
                                insertbackground=C["acento"], relief="flat", bd=4,
                                highlightthickness=1, highlightcolor=C["acento"],
                                highlightbackground=C["borda"])
        self.entrada.pack(side="left", fill="x", expand=True, ipady=7, padx=(0,8))
        self.entrada.bind("<Return>", self._enviar)
        self.entrada.bind("<Up>",     self._nav_up)
        self.entrada.bind("<Down>",   self._nav_down)
        self.entrada.focus()

        tk.Button(ir, text="ENVIAR", font=FB,
                  bg=C["acento2"], fg="white", activebackground=C["acento"],
                  relief="flat", bd=0, padx=16, pady=8, cursor="hand2",
                  command=self._enviar).pack(side="left", padx=(0,5))

        self.btn_voz = tk.Button(ir, text="🎙 VOZ", font=FB,
                                  bg=C["acento2"] if VOZ_OK else C["dim"],
                                  fg="white", activebackground=C["acento"],
                                  relief="flat", bd=0, padx=14, pady=8,
                                  cursor="hand2" if VOZ_OK else "arrow",
                                  command=self._toggle_voz)
        self.btn_voz.pack(side="left")

        self.status_var = tk.StringVar(value="Pronto.")
        tk.Label(self.root, textvariable=self.status_var, font=FS,
                 fg=C["dim"], bg=C["bg"], anchor="w", padx=12
                 ).grid(row=3, column=0, sticky="ew", pady=(0,4))

    def _mk_frame(self, parent):
        f = tk.Frame(parent, bg=C["bg"])
        f.rowconfigure(0, weight=1); f.columnconfigure(0, weight=1)
        return f

    def _mk_tab(self, parent, label, aba_id):
        return tk.Button(parent, text=label, font=FS,
                         bg=C["panel2"], fg=C["texto"],
                         activebackground=C["tab_sel"], relief="flat", bd=0,
                         padx=14, pady=5, cursor="hand2",
                         command=lambda: self._trocar_aba(aba_id))

    # ── Config tab ────────────────────────────────────────────────────────────

    def _build_config(self, parent):
        pad = {"padx": 20, "pady": 8}
        tk.Label(parent, text="⚙️  CONFIGURAÇÕES", font=("Consolas",11,"bold"),
                 fg=C["acento"], bg=C["bg"]).pack(anchor="w", **pad)

        # Cidade clima
        row = tk.Frame(parent, bg=C["bg"])
        row.pack(fill="x", padx=20)
        tk.Label(row, text="🌤️ Cidade padrão para clima:", font=FS, fg=C["texto"],
                 bg=C["bg"]).pack(side="left")
        self.entrada_cidade = tk.Entry(row, font=FS, width=20,
                                       bg=C["hist_item"], fg=C["texto"],
                                       insertbackground=C["acento"], relief="flat", bd=3)
        self.entrada_cidade.insert(0, CFG.get("cidade_clima", "São Paulo"))
        self.entrada_cidade.pack(side="left", padx=(8,0))
        tk.Button(row, text="Salvar", font=FS, bg=C["acento2"], fg="white",
                  relief="flat", bd=0, padx=8, pady=3, cursor="hand2",
                  command=self._salvar_cidade).pack(side="left", padx=(6,0))

        # Voz contínua ao iniciar
        row2 = tk.Frame(parent, bg=C["bg"])
        row2.pack(fill="x", padx=20, pady=(8,0))
        self.var_voz_auto = tk.BooleanVar(value=CFG.get("voz_continua", False))
        tk.Checkbutton(row2, text="Ativar modo voz contínuo ao iniciar",
                       font=FS, fg=C["texto"], bg=C["bg"],
                       activebackground=C["bg"], selectcolor=C["panel2"],
                       variable=self.var_voz_auto,
                       command=lambda: self._salvar_cfg("voz_continua", self.var_voz_auto.get())
                       ).pack(side="left")

        # Info criar exe
        tk.Label(parent, text="──────────────────────────────────", font=FS,
                 fg=C["dim"], bg=C["bg"]).pack(anchor="w", padx=20, pady=(16,0))
        tk.Label(parent, text="📦 CRIAR EXECUTÁVEL (.exe)", font=("Consolas",10,"bold"),
                 fg=C["amarelo"], bg=C["bg"]).pack(anchor="w", padx=20)
        instrucoes = (
            "1. Abra o terminal (CMD) na pasta do robo.py\n"
            "2. Execute o comando abaixo:\n\n"
            "   pyinstaller --onefile --windowed --icon=NONE robo.py\n\n"
            "3. O .exe estará em:  dist\\robo.exe\n"
            "4. Copie para onde quiser e execute!"
        )
        tk.Label(parent, text=instrucoes, font=FS, fg=C["texto"], bg=C["panel2"],
                 justify="left", padx=12, pady=10).pack(anchor="w", padx=20, pady=(4,0))

        tk.Button(parent, text="📋 Copiar comando de build", font=FS,
                  bg=C["acento2"], fg="white", relief="flat", bd=0,
                  padx=12, pady=5, cursor="hand2",
                  command=lambda: pyperclip.copy(
                      "pyinstaller --onefile --windowed --icon=NONE robo.py"
                  ) or messagebox.showinfo("Copiado!", "Comando copiado para a área de transferência!")
                  ).pack(anchor="w", padx=20, pady=(8,0))

    # ── Abas ─────────────────────────────────────────────────────────────────

    def _trocar_aba(self, aba_id):
        self._aba_atual = aba_id
        mapa = {"chat": self.fr_chat, "notas": self.fr_notas,
                "macros": self.fr_macro, "config": self.fr_cfg}
        for f in mapa.values(): f.grid_remove()
        mapa[aba_id].grid(row=1, column=0, sticky="nsew")
        tabs = {"chat": self.btn_tab_chat, "notas": self.btn_tab_notas,
                "macros": self.btn_tab_macro, "config": self.btn_tab_cfg}
        for aid, btn in tabs.items():
            btn.config(bg=C["tab_sel"] if aid==aba_id else C["panel2"],
                       fg=C["acento"] if aid==aba_id else C["texto"])
        if aba_id == "notas":  self._carregar_notas()
        if aba_id == "macros": self._refresh_macros()

    def _carregar_notas(self):
        self.txt_notas.delete("1.0","end")
        if os.path.exists(NOTAS_FILE):
            with open(NOTAS_FILE,"r",encoding="utf-8") as f:
                self.txt_notas.insert("1.0", f.read())

    def _salvar_notas(self):
        with open(NOTAS_FILE,"w",encoding="utf-8") as f:
            f.write(self.txt_notas.get("1.0","end-1c"))
        self._log("Notas salvas.", "sucesso")

    def _refresh_macros(self):
        self.txt_macro.config(state="normal")
        self.txt_macro.delete("1.0","end")
        m = self.robo.macros.listar() if hasattr(self,"robo") else {}
        if not m:
            self.txt_macro.insert("end",
                "Nenhuma macro ainda.\n\nComo criar:\n"
                "  1. Digite: cria macro [nome]\n"
                "  2. Digite comandos um a um\n  3. Digite: fim macro")
        else:
            for nome, cmds in m.items():
                self.txt_macro.insert("end", f"▶ {nome.upper()}\n")
                for i,c in enumerate(cmds,1): self.txt_macro.insert("end", f"  {i}. {c}\n")
                self.txt_macro.insert("end", "\n")
        self.txt_macro.config(state="disabled")

    # ── Config helpers ────────────────────────────────────────────────────────

    def _toggle_autostart(self):
        ok = toggle_autostart(self.var_auto.get())
        estado = "ativado" if self.var_auto.get() else "desativado"
        if ok: self._log(f"Robô » ✅ Inicialização automática {estado}.", "sucesso")
        else:  self._log("Robô » ❌ Erro ao alterar. Tente como administrador.", "erro")

    def _toggle_voz_resp(self):
        CFG["resposta_voz"] = self.var_resp_voz.get()
        save_cfg(CFG)

    def _toggle_voz(self):
        self.voz.toggle()

    def _salvar_cidade(self):
        cidade = self.entrada_cidade.get().strip()
        if cidade:
            CFG["cidade_clima"] = cidade
            save_cfg(CFG)
            self._log(f"Robô » ✅ Cidade padrão: {cidade}", "sucesso")

    def _salvar_cfg(self, chave, valor):
        CFG[chave] = valor
        save_cfg(CFG)

    # ── Ícone animado ────────────────────────────────────────────────────────

    def _anim_icon(self):
        f = self._icon_f
        self.cv.delete("all")
        p = 15 + (f % 5)
        # Pulso exterior
        self.cv.create_oval(18-p, 18-p, 18+p, 18+p, outline=C["acento"], width=1)
        # Cabeça
        self.cv.create_oval(10,10,26,26, fill=C["acento2"], outline=C["acento"], width=2)
        # Olhos piscam
        ey = 15 + (1 if f % 7 == 0 else 0)
        self.cv.create_oval(12,ey,14,ey+2, fill="white")
        self.cv.create_oval(22,ey,24,ey+2, fill="white")
        # Boca
        self.cv.create_arc(12,17,24,24, start=200, extent=140,
                           outline="white", width=1, style="arc")
        # Antena
        self.cv.create_line(18,10,18,6, fill=C["acento"], width=1)
        self.cv.create_oval(16,4,20,8, fill=C["acento"], outline="")
        # Indicador voz contínua
        if hasattr(self,"voz") and self.voz.ativo:
            self.cv.create_oval(29,5,35,11, fill=C["vermelho"], outline="")
        self._icon_f = (f+1) % 10
        self.root.after(180, self._anim_icon)

    # ── Histórico ────────────────────────────────────────────────────────────

    def _refresh_hist(self):
        for w in self.hist_inner.winfo_children(): w.destroy()
        filtro = ""
        if hasattr(self,"hist_busca"):
            t = self.hist_busca.get()
            if t and t != "🔎 filtrar...": filtro = _n(t)
        recs = self.robo.hist.recentes(30) if hasattr(self,"robo") else []
        if filtro: recs = [e for e in recs if filtro in _n(e["cmd"])]
        if not recs:
            tk.Label(self.hist_inner, text="vazio", font=FS,
                     fg=C["dim"], bg=C["hist_bg"]).pack(padx=8, pady=8); return
        for e in recs:
            row = tk.Frame(self.hist_inner, bg=C["hist_item"], cursor="hand2", pady=3)
            row.pack(fill="x", padx=2, pady=1)
            txt = e["cmd"][:24]+("…" if len(e["cmd"])>24 else "")
            lbl = tk.Label(row, text=txt, font=FS, fg=C["texto"],
                           bg=C["hist_item"], anchor="w", padx=5)
            lbl.pack(side="left", fill="x", expand=True)
            ts = tk.Label(row, text=e["ts"], font=FH, fg=C["dim"], bg=C["hist_item"], padx=3)
            ts.pack(side="right")
            cmd = e["cmd"]
            for w in (row,lbl,ts):
                w.bind("<Enter>",    lambda ev,r=row,l=lbl,t=ts: self._hov(r,l,t,True))
                w.bind("<Leave>",    lambda ev,r=row,l=lbl,t=ts: self._hov(r,l,t,False))
                w.bind("<Button-1>", lambda ev,c=cmd: self._repetir(c))

    def _hov(self, r, l, t, on):
        bg = C["hist_hov"] if on else C["hist_item"]
        r.config(bg=bg); l.config(bg=bg); t.config(bg=bg)

    def _repetir(self, cmd):
        self.entrada.delete(0,"end"); self.entrada.insert(0,cmd); self._enviar()

    def _busca_focus(self, on):
        if on and self.hist_busca.get()=="🔎 filtrar...": self.hist_busca.delete(0,"end")
        elif not on and not self.hist_busca.get(): self.hist_busca.insert(0,"🔎 filtrar...")

    # ── Nav ──────────────────────────────────────────────────────────────────

    def _nav_up(self, _=None):
        r = self.robo.hist.recentes(30) if hasattr(self,"robo") else []
        if not r: return
        self._hist_idx = min(self._hist_idx+1, len(r)-1)
        self.entrada.delete(0,"end"); self.entrada.insert(0, r[self._hist_idx]["cmd"])

    def _nav_down(self, _=None):
        if self._hist_idx <= 0:
            self._hist_idx = -1; self.entrada.delete(0,"end"); return
        self._hist_idx -= 1
        r = self.robo.hist.recentes(30)
        self.entrada.delete(0,"end"); self.entrada.insert(0, r[self._hist_idx]["cmd"])

    # ── Envio ────────────────────────────────────────────────────────────────

    def _enviar(self, _=None):
        txt = self.entrada.get().strip()
        if not txt: return
        self._hist_idx = -1
        self.entrada.delete(0,"end")
        self._trocar_aba("chat")
        threading.Thread(target=self.robo.executar, args=(txt,), daemon=True).start()

    # ── Log ──────────────────────────────────────────────────────────────────

    def _log(self, texto, tag="info"):
        def _ins():
            self.chat.config(state="normal")
            ts = datetime.now().strftime("%H:%M:%S")
            self.chat.insert("end", f"[{ts}] ", "dim_ts")
            self.chat.insert("end", texto+"\n", tag)
            self.chat.see("end")
            self.chat.config(state="disabled")
        self.root.after(0, _ins)

    def _set_status(self, txt):
        self.root.after(0, lambda: self.status_var.set(txt))

    def _set_btn_voz(self, txt, cor):
        self.root.after(0, lambda: self.btn_voz.config(text=txt, bg=cor))


# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    root = tk.Tk()
    app  = App(root)
    root.mainloop()
