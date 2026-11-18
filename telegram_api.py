import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

class TelegramError(Exception):
    def __init__(self, codigo=0, espera=0):
        super().__init__(f"Telegram no disponible (código {codigo}).")
        self.codigo=codigo
        self.espera=espera

class TelegramAPI:
    def __init__(self, token): self.base='https://api.telegram.org/bot'+token+'/'
    def llamar(self, metodo, datos=None):
        req=Request(self.base+metodo,data=json.dumps(datos or {}).encode(),headers={'Content-Type':'application/json'})
        try:
            with urlopen(req,timeout=100) as res: payload=json.load(res)
        except HTTPError as exc:
            try: payload=json.loads(exc.read())
            except (ValueError,UnicodeError): payload={}
            raise TelegramError(exc.code,payload.get('parameters',{}).get('retry_after',0)) from None
        except (URLError,TimeoutError,OSError,ValueError):
            raise TelegramError() from None
        if not payload.get('ok'):
            raise TelegramError(payload.get('error_code',0),payload.get('parameters',{}).get('retry_after',0))
        return payload['result']
    def enviar(self, chat, texto):                                                                     
        for i in range(0,len(texto),1800):
            self.llamar('sendMessage',{'chat_id':chat,'text':texto[i:i+1800]})
