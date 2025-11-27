#urls.py
from django.urls import path
from django.shortcuts import redirect
from . import views

def home_redirect(request):
    return redirect('login')

urlpatterns = [
    path('', home_redirect),

    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),

    # Home by role
    path('student/', views.student_home, name='student_home'),
    path('teacher/', views.teacher_home, name='teacher_home'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    # Posts
    path('post/create/', views.create_post, name='create_post'),
    path('post/success/', views.post_success, name='post_success'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),

    path('post/approve/<int:post_id>/', views.approve_post, name='approve_post'),
    path('post/reject/<int:post_id>/', views.reject_post, name='reject_post'),

    # Comments
    path('comment/add/<int:post_id>/', views.add_comment, name='add_comment'),

    # Approval for teachers (students' post)
    path('post/approval/', views.post_approval_list, name='post_approval_list'),
    path('post/review/<int:post_id>/', views.post_review_detail, name='post_review_detail'),

    # Teacher approval page (fix)
    path('teacher-approval/', views.Teacher_approval, name='teacher_approval'),
    path('post/delete/<int:post_id>/', views.delete_post, name='delete_post'),
    path('trash/', views.trash_bin, name='trash_bin'),
    path('post/restore/<int:post_id>/', views.restore_post, name='restore_post'),
    path('trash/', views.trash_bin, name='trash_bin'),
    path('post/restore/<int:post_id>/', views.restore_post, name='restore_post'),

]
