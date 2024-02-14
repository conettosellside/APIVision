from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    #re_path(r"ws/chat/(?P<room_name>\w+)/$", consumers.ChatConsumer.as_asgi()),
    re_path(r"ws/mqtt/$", consumers.MQTTConsumer.as_asgi()),
    re_path(r"ws/camera/$", consumers.CameraConsumer.as_asgi()),
    re_path(r"ws/camera/client/$", consumers.ClientCameraConsumer.as_asgi()),
]