from channels.routing import ProtocolTypeRouter, URLRouter
from django.conf.urls import url
from django.urls import path
from channels.auth import AuthMiddlewareStack

from quiz.consumers import QuizConsumer, AdminQuizConsumer

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter([
            url(r"^ws/quiz/lobby/(?P<stream>\w+)/$", QuizConsumer),
            url("quiz/admin/", AdminQuizConsumer),
        ]),
    ),
})
