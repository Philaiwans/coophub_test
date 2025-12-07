from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.index, name='index'),
    path('<slug:room_slug>/', views.room, name='room'),
]
