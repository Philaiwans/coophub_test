# chat/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Room

# chat/views.py
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.files.storage import default_storage
from django.utils import timezone
from django.contrib.auth.decorators import login_required



@login_required
def index(request):
    user = request.user

    community_room = Room.objects.filter(slug='coophub-community').first()

    major_room = None
    if user.major:
        major_room = Room.objects.filter(is_major_chat=True, major_name=user.major).first()

    chatbot_room = Room.objects.filter(slug=f'chatbot-{user.role}'.lower()).first()

    rooms_for_user = []
    if community_room:
        rooms_for_user.append({'label': 'Community', 'room': community_room})

    if major_room:
        rooms_for_user.append({'label': f'Major Chat ({user.major})', 'room': major_room})

    if chatbot_room:
        rooms_for_user.append({'label': 'Chat Bot', 'room': chatbot_room})

    return render(request, 'chat/index.html', {'rooms_for_user': rooms_for_user})


@login_required
def room(request, room_slug):
    room = get_object_or_404(Room, slug=room_slug)

    # Major Chat: ต้อง major ตรง
    if room.is_major_chat and room.major_name != request.user.major:
        return redirect('chat:rooms_list')

    # Chatbot: ต้อง role ตรง
    if room.slug.startswith('chatbot-'):
        expected_role = room.slug.split('-', 1)[1]
        if expected_role != request.user.role:
            return redirect('chat:rooms_list')

    return render(request, 'chat/room.html', {'room': room, 'username': request.user.username})

# chat/views.py
@login_required
def room(request, room_slug):
    room = get_object_or_404(Room, slug=room_slug)

    if room.is_major_chat and room.major_name != request.user.major:
        return redirect('chat:rooms_list')

    if room.slug.startswith('chatbot-'):
        expected_role = room.slug.split('-', 1)[1]
        if expected_role != request.user.role:
            return redirect('chat:rooms_list')
        return render(request, 'chat/chatbot.html', {'room': room})

    return render(request, 'chat/room.html', {'room': room, 'username': request.user.username})


@require_POST
@login_required
def upload_chat_file(request):
    """
    รับไฟล์จากฟรอนท์ -> เซฟลง MEDIA -> คืน URL กลับไปให้ JS
    """
    f = request.FILES.get("file")
    if not f:
        return JsonResponse({"ok": False, "error": "no file"}, status=400)

    # ตั้ง path เก็บไฟล์
    ts = timezone.now().strftime("%Y%m%d_%H%M%S")
    path = f"chat_uploads/{request.user.id}/{ts}_{f.name}"
    saved_path = default_storage.save(path, f)

    url = default_storage.url(saved_path)

    # เดาว่าเป็นรูปไหม
    is_image = (f.content_type or "").startswith("image/")
    return JsonResponse({
        "ok": True,
        "url": url,
        "name": f.name,
        "kind": "image" if is_image else "file",
    })
