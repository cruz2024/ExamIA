import json
import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from config import BASE

def normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto.lower())
    return re.sub(r"[^a-z0-9 ]", " ", "".join(c for c in texto if not unicodedata.combining(c)))

@dataclass
class Resultado:
    intencion: str
    puntuacion: float
    entidades: dict
    alternativas: list

class ProcesadorPLN:
    def __init__(self):
        self.ejemplos = json.loads((BASE / "data/intents.json").read_text(encoding="utf-8"))
        self.pistas = {
            "internet": {"internet", "wifi", "router", "red", "redes", "conexion", "navegar"},
            "equipo": {"computadora", "laptop", "pc", "pantalla", "teclado", "mouse", "enciende"},
            "acceso": {"contrasena", "clave", "cuenta", "sesion", "autenticacion", "acceso", "correo"},
            "programacion": {"python", "java", "codigo", "programa", "bucle", "funcion", "traceback", "variable"},
            "solicitud": {"ticket", "incidencia", "solicitud", "reporte", "tecnico"},
        }

    def entidades(self, texto):
        t = normalizar(texto)
        valores = {
            "dispositivo": {"computadora": ["computadora", "pc", "ordenador"], "laptop": ["laptop", "portatil"], "router": ["router", "enrutador"], "telefono": ["telefono", "celular"]},
            "sistema": {"Windows": ["windows"], "Linux": ["linux", "ubuntu"], "Android": ["android"], "macOS": ["macos", "mac"]},
            "prioridad": {"alta": ["urgente", "urgencia", "alta"], "normal": ["normal", "media"], "baja": ["baja", "sin prisa"]},
        }
        out = {}
        for entidad, opciones in valores.items():
            for valor, palabras in opciones.items():
                if any(re.search(r"\b" + re.escape(x) + r"\b", t) for x in palabras):
                    out[entidad] = valor
                    break
        return out

    def analizar(self, texto):
        t = " ".join(normalizar(texto).split())
        tokens = set(t.split())
        scores = []
        for nombre, frases in self.ejemplos.items():
            mejor = 0.0
            for frase in frases:
                f = " ".join(normalizar(frase).split())
                palabras = set(f.split())
                overlap = len(tokens & palabras) / max(1, len(tokens | palabras))
                score = 1.0 if t == f else .55 * overlap + .45 * SequenceMatcher(None, t, f).ratio()
                mejor = max(mejor, score)
            if tokens & self.pistas.get(nombre, set()):
                mejor = max(mejor, .72)
            scores.append((nombre, mejor))
        scores.sort(key=lambda x: x[1], reverse=True)
        nombre, score = scores[0]                                         
        if score < .53:
            nombre = "desconocida"
        elif score < .99 and score - scores[1][1] < .08:
            nombre = "ambigua"
        return Resultado(nombre, round(score, 3), self.entidades(texto), [x[0] for x in scores[:2]])
