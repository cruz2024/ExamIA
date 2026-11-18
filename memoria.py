import json
from contextlib import contextmanager
import sqlite3
from datetime import datetime, timezone

class Memoria:
    def __init__(self, ruta):
        self.ruta = str(ruta)
        with self.conectar() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS sesiones (usuario INTEGER PRIMARY KEY, datos TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS tickets (id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario INTEGER NOT NULL, descripcion TEXT NOT NULL, prioridad TEXT NOT NULL,
                creado TEXT NOT NULL, estado TEXT NOT NULL DEFAULT 'abierto');
            CREATE TABLE IF NOT EXISTS meta (clave TEXT PRIMARY KEY, valor TEXT NOT NULL);
            """)
    @contextmanager
    def conectar(self):
        conexion = sqlite3.connect(self.ruta, timeout=15)
        try:
            with conexion:
                yield conexion
        finally:
            conexion.close()
    def cargar(self, usuario):
        with self.conectar() as db:
            fila = db.execute("SELECT datos FROM sesiones WHERE usuario=?", (usuario,)).fetchone()
        return json.loads(fila[0]) if fila else {"historial": [], "entidades": {}, "paso": None}
    def guardar(self, usuario, datos):
        with self.conectar() as db:
            db.execute("INSERT OR REPLACE INTO sesiones VALUES (?,?)", (usuario, json.dumps(datos,ensure_ascii=False)))
    def borrar(self, usuario):
        with self.conectar() as db:
            db.execute("DELETE FROM sesiones WHERE usuario=?", (usuario,))
            db.execute("DELETE FROM tickets WHERE usuario=?", (usuario,))
    def ticket(self, usuario, descripcion, prioridad):
        with self.conectar() as db:
            cursor = db.execute("INSERT INTO tickets(usuario,descripcion,prioridad,creado) VALUES(?,?,?,?)",
                (usuario, descripcion, prioridad, datetime.now(timezone.utc).isoformat()))
            return cursor.lastrowid
    def tickets(self, usuario):
        with self.conectar() as db:
            return db.execute("SELECT id,prioridad,estado,descripcion FROM tickets WHERE usuario=? ORDER BY id DESC LIMIT 10",(usuario,)).fetchall()
    def offset(self, nuevo=None):
        with self.conectar() as db:
            if nuevo is not None:
                db.execute("INSERT OR REPLACE INTO meta VALUES ('offset',?)", (str(nuevo),))
            fila = db.execute("SELECT valor FROM meta WHERE clave='offset'").fetchone()
        return int(fila[0]) if fila else 0
