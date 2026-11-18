import os
from pathlib import Path

BASE = Path(__file__).resolve().parent
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8807077417:AAFOFDL0mcn8IDp1sxLbW9V4TqnzCRZd2os')
OLLAMA_URL = 'http://127.0.0.1:11434'
MODELO = ''
USUARIOS_PERMITIDOS = set()
DB_PATH = BASE / 'data' / 'taskbot.db'
