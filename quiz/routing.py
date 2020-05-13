from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from channels.auth import AuthMiddlewareStack

from .consumers import QuizConsumer

#application = AuthMiddlewareStack({
#    "websocket": URLRouter([
#        path("ws/", QuizConsumer),
#    ]),
#})