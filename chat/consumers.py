from email.mime import base
import json
import paho.mqtt.client as mqtt
from channels.generic.websocket import AsyncWebsocketConsumer
from autobahn.exception import Disconnected
from asgiref.sync import async_to_sync
import base64
import ssl
from PIL import Image
from io import BytesIO
import constants
import os
import asyncio
import cv2
import numpy as np

class MQTTConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Obtener información del usuario desde el alcance (scope)
        user = self.scope.get('user')
        # Conectar al broker MQTT
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect  # Definir callback para cuando se conecte al broker
        self.client.on_message = self.on_message  # Definir callback para cuando llegue un mensaje
        self.client.tls_set(
            ca_certs=os.path.join(os.getcwd(), constants.BROKER_CA_CERT),
            certfile=os.path.join(os.getcwd(), constants.BROKER_CERT),
            keyfile=os.path.join(os.getcwd(), constants.BROKER_KEY),
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLS,
            ciphers=None
        )
        self.client.connect(constants.BROKER_URL, constants.BROKER_PORT, 60)
        self.client.loop_start()
        await self.accept()

    async def disconnect(self, close_code):
        self.client.loop_stop()
        self.client.disconnect()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Conectado al broker MQTT")
            # Suscribirse a un tópico
            self.client.subscribe(constants.TOPIC_CAMERA['CAMERA'])
            self.client.subscribe(constants.TOPIC_CAMERA['CONTROL_CLIENT'])
            self.client.subscribe(constants.TOPIC_CAMERA['CONTROL_SERVER'])
        else:
            print(f"Error al conectarse al broker. Código de error: {rc}")

    def on_message(self, client, userdata, msg):
        if msg.topic == constants.TOPIC_CAMERA['CONTROL_SERVER']:
            print("publicando mensaje en esp32/control")
            if msg.payload.decode("utf-8") == "true":
                self.client.publish(constants.TOPIC_CAMERA['CONTROL_CLIENT'], 'conectar')
            else:
                self.client.publish(constants.TOPIC_CAMERA['CONTROL_CLIENT'], 'desconectar')

        elif msg.topic.startswith(constants.TOPIC_CAMERA['CAMERA']) and type(msg.payload) == bytes:
            compressed_image = self.compress_image(msg.payload, quality=85)
            img_base64 = base64.b64encode(compressed_image).decode('ascii')
            async_to_sync(self.send)(text_data=json.dumps({
                'topic': msg.topic,
                'message': f'data:image/jpeg;base64,{img_base64}'
            }))

    def compress_image(self, image_bytes, quality=85):
        img = Image.open(BytesIO(image_bytes))
        compressed_buffer = BytesIO()
        img.save(compressed_buffer, format="JPEG", quality=quality)
        compressed_image = compressed_buffer.getvalue()
        compressed_buffer.close()

        return compressed_image

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            # Enviar el mensaje al broker MQTT
            self.client.publish(constants.TOPIC_CAMERA['CONTROL_SERVER'], text_data)
            print(f"Sent message: {text_data}")
        elif bytes_data:
            # Enviar el mensaje al broker MQTT
            self.client.publish(constants.TOPIC_CAMERA['CONTROL_SERVER'], bytes_data)
            print(f"Sent message: {bytes_data}")

class CameraConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.group_name = 'camera_group'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        if bytes_data:
            print("Received bytes data", bytes_data)
            # Comprime la imagen usando JPEG antes de enviarla
            _, image = await asyncio.get_event_loop().run_in_executor(None, cv2.imencode, '.jpg', cv2.imdecode(np.frombuffer(bytes_data, dtype=np.uint8), 1))
            compressed_image_bytes = image.tobytes()

            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'camera_message',
                    'message': compressed_image_bytes,
                }
            )
        elif text_data:
            print("Received text data", text_data)
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'camera_message',
                    'message': text_data,
                }
            )
        
        else:
            print("No data received")

    async def camera_message(self, event):
        try: 
            message = event['message']
            await self.send(bytes_data=message)
        except Disconnected:
            print("Client disconnected")


class ClientCameraConsumer(AsyncWebsocketConsumer):        
    async def connect(self):
        self.image_chunks = []
        self.group_name = 'camera_group'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        message = text_data
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'camera_message',
                'message': message
            }
        )

    async def camera_message(self, event):
        try:
            message = event['message']

            # Envía cada fragmento de imagen al cliente tan pronto como se reciba
            await self.send(bytes_data=message)
            
        except Disconnected:
            print("Client disconnected")
