from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Room

def index(request):
    rooms = Room.objects.all()
    return render(request, 'chat/index.html', {'rooms': rooms})

@login_required  # ⭐ บังคับ login
def room(request, room_slug):
    room = get_object_or_404(Room, slug=room_slug)
    return render(request, 'chat/room.html', {
        'room': room,
        'username': request.user.username
    })