from django.urls import path
from . import views
from .views import ChatPage

urlpatterns = [
    path('', ChatPage, name='chat'),
    path('prompt/', views.prompt, name='prompt'),
]
