
# chat/routing.py
from django.urls import re_path
from .consumers import ChatConsumer, ChatbotConsumer

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<room_slug>[-\w]+)/$", ChatConsumer.as_asgi()),
    re_path(r"ws/chatbot/(?P<slug>[-\w]+)/$", ChatbotConsumer.as_asgi()),
]
