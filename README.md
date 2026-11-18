# Taskbot - Telegram con Ollama local

Esta versión corrige la anterior. Todas las preguntas normales llegan a Ollama,
incluso saludos y temas fuera de soporte técnico. No existe modo consola ni modo
solo reglas. La terminal sirve para iniciar el programa y ver su estado.
El código no contiene comentarios ni docstrings, según la solicitud del autor.

## Actualizar
1. Detén la versión anterior con Ctrl+C. Guarda una copia de esa carpeta.
2. Extrae TODO el ZIP en una carpeta nueva.
3. Abre config.py y pega tu token en TELEGRAM_TOKEN.
4. MODELO = '' selecciona un modelo local conocido que ya esté instalado:
   qwen3:1.7b, qwen2.5:1.5b, qwen2.5:3b o qwen3:0.6b.
   Para otro modelo de texto escribe su nombre exacto, por ejemplo:
   MODELO = 'qwen2.5:3b'
5. No copies tu config.py anterior entero: contiene opciones que ya no se usan.
   Copia solo el token y, si quieres, el nombre de MODELO.
6. Si quieres conservar sesiones y tickets anteriores, con los programas cerrados
   copia data/taskbot.db en data/ de esta carpeta. No copies una .venv antigua.

## Ejecutar en Windows / Git Bash
Abre Ollama desde Inicio. No necesitas descargarlo de nuevo ni pagar una API.
Comprueba tus modelos:

```bash
ollama list
```

Dentro de la carpeta que contiene main.py:

```bash
py -3.12 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -u main.py
```

Solo la primera vez se crea el entorno. En las siguientes ejecuciones:

```bash
.venv/Scripts/python.exe -u main.py
```

También puedes usar instalar.bat e iniciar.bat. No hay paquetes pip externos.
En Telegram abre tu bot y envía /start. Después haz una pregunta.
La primera generación puede tardar mientras el modelo carga en memoria.
No uses --consola ni --solo-reglas: ya no existen en esta versión.

## Para mantenerlo disponible
Deja Ollama y el programa abiertos; evita que el PC entre en suspensión.
Necesitas electricidad e internet para Telegram. Ollama genera el texto en tu PC
con el modelo descargado; no necesita saldo ni una API de IA externa.
No se configura inicio automático ni disponibilidad garantizada 24/7.
Ctrl+C apaga Taskbot. Si apagas el PC, el bot deja de responder.
Cierra programas pesados: tu equipo de 8 GB comparte memoria con Windows.

## Comandos de Telegram
/start, /ayuda, /ticket, /tickets, /cancelar, /reiniciar, /borrar, /estado, /privacidad.
Los mensajes de control son textos del programa. Las respuestas a preguntas
normales se generan mediante Ollama y no se seleccionan de una lista de frases.
/ticket inicia un registro guiado y /cancelar vuelve al chat general.
Los tickets solo se almacenan localmente, no se envían a un técnico.
/reiniciar elimina el contexto del usuario, conservando tickets.
/borrar elimina su sesión y sus tickets locales; no Telegram ni respaldos.

## Arquitectura
main.py: Telegram, polling, indicador escribiendo y control de errores.
ia.py: comprueba Ollama y modelos locales; genera respuestas por /api/chat.
dialogo.py: comandos, sesiones y consultas generales al modelo.
pln.py: clasifica intenciones técnicas y extrae entidades como metadatos.
memoria.py: SQLite, sesiones, tickets y offset.
telegram_api.py: API HTTPS de Telegram y división de mensajes largos.
config.py: token, modelo, acceso y base de datos.

La matriz técnica de 7 intenciones, 70 expresiones y 3 entidades se conserva para
el proyecto académico. Una intención desconocida o ambigua no bloquea la pregunta:
Ollama la recibe y puede pedir aclaración. No hay respuestas fijas de soporte.
El alcance es más amplio que el dominio especializado de la rúbrica original.
El PDF explica esa diferencia y la eliminación de comentarios solicitada.

## Verificar
```bash
.venv/Scripts/python.exe -m unittest discover -s tests -v
```
15 pruebas locales aprobadas. Telegram y Ollama se simularon; no se probaron tus
credenciales ni la velocidad del modelo real en tu computadora.
Prueba en Telegram: pregunta de Java, pregunta de ciencia, pregunta de seguimiento,
/reiniciar, una nueva pregunta y /ticket. Si Ollama se cierra, se informa del error;
no se reemplaza la respuesta por una orientación prefabricada.

## Errores frecuentes
- Token: completa TELEGRAM_TOKEN en config.py. No lo compartas.
- Sin Ollama: abre la aplicación. Si no inicia su servidor, ejecuta ollama serve
  en otra terminal. Si el puerto está ocupado, puede estar abierto ya.
- Sin modelo: usa ollama list y coloca el nombre exacto en MODELO.
- Respuesta lenta: la primera carga tarda más. Espera o usa un modelo menor.
- 409 de Telegram: cierra otras versiones con el mismo token.
- Webhook: este bot no lo elimina automáticamente. Si usas este proyecto por
  polling y quieres retirar un webhook anterior, ejecuta deliberadamente:
  .venv/Scripts/python.exe -c "from config import TELEGRAM_TOKEN; from telegram_api import TelegramAPI; TelegramAPI(TELEGRAM_TOKEN).llamar('deleteWebhook')"
- El nombre visible se cambia en BotFather con /setname.

El bot trabaja con texto y sin búsqueda web. Puede equivocarse; un modelo pequeño
no garantiza calidad en cualquier pregunta. El procesamiento es secuencial.
Los datos locales no están cifrados. No compartas tokens, contraseñas o códigos.

## Repositorio académico
.gitignore excluye config.py, .venv y bases de datos. Sube config.example.py,
y copia esa plantilla como config.py después de clonar. Completa el enlace real
del repositorio, el segundo integrante y evidencias de avances antes de entregar.
