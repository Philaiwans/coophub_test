# chat/urls.py
from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # path('', views.index, name='index'), 
    path('rooms/', views.index, name='rooms_list'), # เปลี่ยนชื่อเป็น rooms_list
    path("upload/", views.upload_chat_file, name="upload_chat_file"),  # ✅ เพิ่ม
    path('<slug:room_slug>/', views.room, name='room'),
]