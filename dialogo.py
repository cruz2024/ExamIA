from pln import ProcesadorPLN, normalizar
from ia import MotorIA, IAError

AYUDA = '''Taskbot responde tus preguntas.
/start - Iniciar
/ayuda - Ayuda
/ticket - Registrar una solicitud técnica
/tickets - Ver tus solicitudes
/cancelar - Cancelar el registro de un ticket
/reiniciar - Borrar el contexto, conservando tickets
/borrar - Borrar tus datos locales
/estado - Consultar el modelo y el contexto
/privacidad - Consultar el uso de datos
Escribe una pregunta de cualquier tema. No tengo búsqueda web en tiempo real.'''


class GestorDialogo:
    def __init__(self, memoria, motor=None):
        self.memoria = memoria
        self.pln = ProcesadorPLN()
        self.motor = motor or MotorIA()

    def responder(self, usuario, texto):
        texto = texto.strip()
        if not texto:
            return 'Escribe tu pregunta.'
        if len(texto) > 4000:
            return 'Divide tu pregunta en mensajes de hasta 4000 caracteres.'
        sesion = self.memoria.cargar(usuario)
        comando = texto.split()[0].split('@')[0].lower()
        if comando in ('/start', '/ayuda', '/help'):
            return AYUDA
        if comando == '/privacidad':
            return ('Guardo tu ID, contexto reciente, entidades y tickets en SQLite local. '
                    'Los mensajes pasan por Telegram y las respuestas se generan en tu PC con Ollama. '
                    '/borrar elimina datos de esta base, pero no Telegram ni respaldos. No envíes credenciales.')
        if comando == '/borrar':
            self.memoria.borrar(usuario)
            return 'Tus datos locales fueron eliminados.'
        if comando in ('/reiniciar', '/nuevo'):
            self.memoria.guardar(usuario, {'historial': [], 'entidades': {}, 'paso': None})
            return 'Comenzamos una conversación nueva. Tus tickets se conservan.'
        if comando == '/cancelar':
            sesion['paso'] = None
            sesion.pop('borrador', None)
            self.memoria.guardar(usuario, sesion)
            return 'Registro cancelado. Ya puedes hacer una pregunta.'
        if comando == '/estado':
            return (f'Modelo: {self.motor.modelo or "pendiente de verificar"}. '
                    f'Paso: {sesion.get("paso") or "conversación"}. '
                    f'Mensajes de contexto: {len(sesion.get("historial", []))}. '
                    f'Última intención: {sesion.get("ultima_intencion", "sin clasificar")}. '
                    f'Entidades: {sesion.get("entidades", {})}.')
        if comando == '/tickets':
            filas = self.memoria.tickets(usuario)
            return '\n'.join(f'#{i} | {p} | {e} | {d}' for i,p,e,d in filas) or 'No tienes tickets.'
        if comando == '/ticket':
            sesion['paso'] = 'descripcion'
            sesion.pop('borrador', None)
            self.memoria.guardar(usuario, sesion)
            return 'Describe la solicitud técnica con al menos 10 caracteres. /cancelar para salir.'
        if comando.startswith('/'):
            return 'Comando desconocido. Usa /ayuda.'
        if sesion.get('paso'):
            respuesta = self.procesar_ticket(usuario, texto, sesion)
            self.memoria.guardar(usuario, sesion)
            return respuesta
        resultado = self.pln.analizar(texto)
        sesion.setdefault('entidades', {}).update(resultado.entidades)
        sesion['ultima_intencion'] = resultado.intencion
        try:
            respuesta = self.motor.responder(texto, sesion.get('historial', []), sesion['entidades'])
        except IAError as error:
            self.memoria.guardar(usuario, sesion)
            return str(error)
        sesion['historial'] = (sesion.get('historial', []) + [
            {'role': 'user', 'content': texto}, {'role': 'assistant', 'content': respuesta}
        ])[-8:]
        self.memoria.guardar(usuario, sesion)
        return respuesta

    def procesar_ticket(self, usuario, texto, sesion):
        paso = sesion['paso']
        if paso == 'descripcion':
            if len(texto) < 10:
                return 'Describe la solicitud con al menos 10 caracteres.'
            sesion['borrador'] = {'descripcion': texto}
            sesion['paso'] = 'prioridad'
            return 'Prioridad: alta, normal o baja.'
        if paso == 'prioridad':
            prioridad = normalizar(texto).strip()
            if prioridad not in ('alta', 'normal', 'baja'):
                return 'Escribe alta, normal o baja.'
            sesion['borrador']['prioridad'] = prioridad
            sesion['paso'] = 'confirmacion'
            return f'Descripción: {sesion["borrador"]["descripcion"]}\nPrioridad: {prioridad}. ¿Confirmas? Sí o no.'
        if paso == 'confirmacion':
            confirmacion = normalizar(texto).strip()
            if confirmacion not in ('si', 'no'):
                return 'Responde sí o no, o usa /cancelar.'
            sesion['paso'] = None
            borrador = sesion.pop('borrador')
            if confirmacion == 'no':
                return 'Solicitud cancelada.'
            numero = self.memoria.ticket(usuario, borrador['descripcion'], borrador['prioridad'])
            return f'Ticket #{numero} guardado localmente. Consulta /tickets. No se envió a un técnico.'
        sesion['paso'] = None
        sesion.pop('borrador', None)
        return 'Restablecí el registro. Escribe /ticket para empezar o haz una pregunta.'
