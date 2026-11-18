import logging
import threading
import time
from config import TELEGRAM_TOKEN, DB_PATH, USUARIOS_PERMITIDOS
from memoria import Memoria
from dialogo import GestorDialogo
from ia import MotorIA, IAError
from telegram_api import TelegramAPI, TelegramError


def escribir(api, chat, detener):
    while not detener.is_set():
        try:
            api.llamar('sendChatAction', {'chat_id': chat, 'action': 'typing'})
        except TelegramError:
            pass
        detener.wait(4)


def responder_mensaje(api, gestor, uid, chat, texto):
    detener = threading.Event()
    hilo = threading.Thread(target=escribir, args=(api, chat, detener), daemon=True)
    hilo.start()
    try:
        api.enviar(chat, gestor.responder(uid, texto))
    finally:
        detener.set()
        hilo.join(timeout=1)


def ejecutar():
    if 'PEGA_AQUI' in TELEGRAM_TOKEN or ':' not in TELEGRAM_TOKEN:
        raise SystemExit('Agrega tu token de BotFather en config.py.')
    motor = MotorIA()
    print('Comprobando Ollama local...', flush=True)
    modelo = motor.verificar()
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    memoria = Memoria(DB_PATH)
    gestor = GestorDialogo(memoria, motor)
    api = TelegramAPI(TELEGRAM_TOKEN)
    info = api.llamar('getMe')
    if api.llamar('getWebhookInfo').get('url'):
        raise SystemExit('Este token tiene un webhook activo. Consulta README antes de cambiarlo.')
    comandos = [('start', 'Iniciar'), ('ayuda', 'Ayuda'), ('ticket', 'Crear solicitud'),
                ('tickets', 'Ver solicitudes'), ('cancelar', 'Cancelar registro'),
                ('reiniciar', 'Nueva conversación'), ('borrar', 'Borrar datos'),
                ('estado', 'Ver modelo'), ('privacidad', 'Uso de datos')]
    try:
        api.llamar('setMyCommands', {'commands': [{'command': c, 'description': d} for c,d in comandos]})
    except TelegramError:
        print('No pude actualizar el menú; los comandos siguen disponibles.', flush=True)
    print(f'Taskbot @{info["username"]} listo. Modelo local: {modelo}. Usa Telegram para conversar.', flush=True)
    offset = memoria.offset()
    while True:
        try:
            updates = api.llamar('getUpdates', {'offset': offset, 'timeout': 30, 'allowed_updates': ['message']})
            for update in updates:
                mensaje = update.get('message', {})
                chat = mensaje.get('chat', {})
                uid = mensaje.get('from', {}).get('id')
                if uid is not None and chat.get('type') == 'private':
                    try:
                        if USUARIOS_PERMITIDOS and uid not in USUARIOS_PERMITIDOS:
                            api.enviar(chat['id'], 'Acceso restringido.')
                        elif 'text' not in mensaje:
                            api.enviar(chat['id'], 'En esta versión solo puedo leer mensajes de texto.')
                        else:
                            responder_mensaje(api, gestor, uid, chat['id'], mensaje['text'])
                    except TelegramError as error:
                        if error.codigo in (401, 409):
                            raise
                        print(f'No pude entregar una respuesta. Telegram: {error.codigo}.', flush=True)
                        if error.espera:
                            time.sleep(min(60, error.espera))
                    except Exception as error:
                        logging.error('Procesamiento: %s', type(error).__name__)
                        try:
                            api.enviar(chat['id'], 'No pude completar la consulta. Inténtalo de nuevo.')
                        except TelegramError:
                            pass
                offset = update['update_id'] + 1
                memoria.offset(offset)
        except TelegramError as error:
            if error.codigo in (401, 409):
                raise SystemExit('Token inválido o hay otra copia del bot funcionando.') from None
            print('Telegram sin conexión. Reintentando...', flush=True)
            time.sleep(min(60, max(5, error.espera)))


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING, format='%(message)s')
    try:
        ejecutar()
    except KeyboardInterrupt:
        print('\nTaskbot detenido.')
    except (IAError, TelegramError) as error:
        print(str(error))
