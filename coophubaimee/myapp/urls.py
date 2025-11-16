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
    path('logout/', views.logout_view, name='logout'),
]
