import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.error import URLError
from dialogo import GestorDialogo
from memoria import Memoria
from ia import MotorIA, IAError
from telegram_api import TelegramAPI
from pln import ProcesadorPLN
from config import BASE


class Pruebas(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.memoria = Memoria(Path(self.tmp.name) / 'prueba.db')
        self.motor = Mock()
        self.motor.modelo = 'qwen3:1.7b'
        self.motor.responder.return_value = 'Respuesta generada por el modelo.'
        self.gestor = GestorDialogo(self.memoria, self.motor)

    def tearDown(self):
        self.tmp.cleanup()

    def test_preguntas_generales_llegan_al_modelo(self):
        for texto in ['hola', 'Cómo aprender Java', 'Qué es la fotosíntesis', 'wifi y contrasena', 'zzzzzzzzzz', 'quiero crear un ticket']:
            self.assertEqual(self.gestor.responder(1, texto), 'Respuesta generada por el modelo.')
        self.assertEqual(self.motor.responder.call_count, 6)
        self.assertEqual(self.memoria.tickets(1), [])

    def test_contexto_persistente(self):
        self.gestor.responder(1, 'Explica Java')
        nueva = GestorDialogo(Memoria(self.memoria.ruta), self.motor)
        nueva.responder(1, 'Dame un ejemplo')
        historial = self.motor.responder.call_args.args[1]
        self.assertEqual(historial[0]['content'], 'Explica Java')
        self.assertEqual(self.memoria.cargar(2)['historial'], [])

    def test_error_no_inventa_respuesta(self):
        self.motor.responder.side_effect = IAError('Abre Ollama.')
        self.assertEqual(self.gestor.responder(1, 'Explica Java'), 'Abre Ollama.')
        self.assertEqual(self.memoria.cargar(1)['historial'], [])

    def test_ticket_explicito(self):
        for texto in ['/ticket', 'Mi laptop no enciende', 'alta', 'sí']:
            respuesta = self.gestor.responder(1, texto)
        self.assertIn('#1', respuesta)
        self.assertEqual(len(self.memoria.tickets(1)), 1)
        self.assertEqual(self.memoria.tickets(2), [])
        self.motor.responder.assert_not_called()

    def test_validacion_y_cancelacion(self):
        self.gestor.responder(1, '/ticket')
        self.assertIn('10', self.gestor.responder(1, 'corto'))
        self.gestor.responder(1, 'Mi computadora falla')
        self.assertIn('alta', self.gestor.responder(1, 'invalida'))
        self.gestor.responder(1, '/cancelar')
        self.gestor.responder(1, 'Qué es Python')
        self.motor.responder.assert_called_once()

    def test_reiniciar_y_borrar(self):
        self.gestor.responder(1, 'Qué es Java')
        self.memoria.ticket(1, 'Prueba de solicitud', 'normal')
        self.gestor.responder(1, '/reiniciar')
        self.assertEqual(self.memoria.cargar(1)['historial'], [])
        self.assertEqual(len(self.memoria.tickets(1)), 1)
        self.gestor.responder(1, '/borrar')
        self.assertEqual(self.memoria.tickets(1), [])

    def test_limites(self):
        self.assertIn('Escribe', self.gestor.responder(1, ' '))
        self.assertIn('4000', self.gestor.responder(1, 'a' * 4001))
        self.assertIn('desconocido', self.gestor.responder(1, '/inventado'))
        self.motor.responder.assert_not_called()

    def test_matriz_y_entidades(self):
        matriz = json.loads((BASE/'data/intents.json').read_text())
        self.assertEqual(len(matriz), 7)
        pln = ProcesadorPLN()
        for nombre, frases in matriz.items():
            self.assertGreaterEqual(len(frases), 10)
            for frase in frases:
                self.assertEqual(pln.analizar(frase).intencion, nombre)
        self.assertEqual(pln.entidades('Laptop Windows urgente'),
                         {'dispositivo': 'laptop', 'sistema': 'Windows', 'prioridad': 'alta'})

    def test_seleccion_modelo_local(self):
        motor = MotorIA()
        motor.modelo = ''
        motor.solicitar = Mock(return_value={'models': [{'name': 'qwen3:1.7b'}]})
        self.assertEqual(motor.verificar(), 'qwen3:1.7b')

    def test_sin_modelo_no_arranca(self):
        motor = MotorIA()
        motor.modelo = ''
        motor.solicitar = Mock(return_value={'models': [{'name': 'qwen3:1.7b', 'remote_host': 'cloud'}]})
        with self.assertRaises(IAError):
            motor.verificar()

    def test_solicitud_real_formada(self):
        motor = MotorIA()
        motor.modelo = 'qwen3:1.7b'
        motor.solicitar = Mock(return_value={'message': {'content': 'Respuesta de prueba'}})
        self.assertEqual(motor.responder('Qué es Java', [], {}), 'Respuesta de prueba')
        ruta, datos = motor.solicitar.call_args.args
        self.assertEqual(ruta, '/api/chat')
        self.assertEqual(datos['messages'][-1]['content'], 'Qué es Java')
        self.assertFalse(datos['think'])
        self.assertEqual(datos['options']['num_ctx'], 4096)

    def test_red_caida(self):
        motor = MotorIA()
        motor.abrir = Mock(side_effect=URLError('fallo'))
        with self.assertRaises(IAError):
            motor.verificar()

    def test_respuesta_invalida(self):
        motor = MotorIA()
        motor.modelo = 'qwen3:1.7b'
        motor.solicitar = Mock(return_value={'message': {}})
        with self.assertRaises(IAError):
            motor.responder('Hola', [], {})

    def test_division_mensajes(self):
        api = TelegramAPI('prueba')
        with patch.object(api, 'llamar') as llamada:
            api.enviar(1, 'a' * 4000)
            self.assertEqual(llamada.call_count, 3)

    def test_offset(self):
        self.memoria.offset(50)
        self.assertEqual(Memoria(self.memoria.ruta).offset(), 50)


if __name__ == '__main__':
    unittest.main()
