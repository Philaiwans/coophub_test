from django.urls import path
from django.shortcuts import redirect
from . import views


def home_redirect(request):
    return redirect('login')

urlpatterns = [
    path('', home_redirect),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('student/', views.student_home, name='student_home'),
    path('teacher/', views.teacher_home, name='teacher_home'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # ⭐⭐ เพิ่มสองอันนี้ ⭐⭐
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    path('logout/', views.logout_view, name='logout'),
      # โปรไฟล์
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    # ระบบโพสต์
    path('post/create/', views.create_post, name='create_post'),
    path('post/success/', views.post_success, name='post_success'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),

    path('post/approve/<int:post_id>/', views.approve_post, name='approve_post'),
    path('post/reject/<int:post_id>/', views.reject_post, name='reject_post'),

    # ความคิดเห็น
    path('comment/add/<int:post_id>/', views.add_comment, name='add_comment'),
]