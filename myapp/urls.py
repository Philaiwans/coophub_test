#urls.py
from django.urls import path
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

def home_redirect(request):
    return redirect('login')

urlpatterns = [
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='password_reset.html',
            email_template_name='password_reset_email.html',
            html_email_template_name='password_reset_email.html',
            subject_template_name='password_reset_subject.txt',
            success_url=reverse_lazy('password_reset_done'),
        ),
        name='password_reset',
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='password_reset_done.html'
        ),
        name='password_reset_done',
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='password_reset_confirm.html',
            success_url=reverse_lazy('password_reset_complete'),
        ),
        name='password_reset_confirm',
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='password_reset_complete.html'
        ),
        name='password_reset_complete',
    ),

    path('', home_redirect),

    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),

    # Home by role
    path('student/', views.student_home, name='student_home'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),  # ⭐ ใหม่
    path('teacher/', views.teacher_home, name='teacher_home'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
path('management-dashboard/', views.management_dashboard, name='management_dashboard'),
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
    
    path('bookmarks/', views.bookmark_list, name='bookmark_list'),
    path('bookmark/toggle/<int:post_id>/', views.toggle_bookmark, name='toggle_bookmark'),
    
    # Activity / การแจ้งเตือน (ครู + แอดมิน)
    path('activity/', views.activity_view, name='activity'),

    # Activity สำหรับนักศึกษา
    path('activity-student/', views.activity_student_view, name='activity_student'),

    path('activity-history/', views.activity_history, name='activity_history'),

    # ⭐ หน้าแก้ไขโพสต์
    path('post/edit/<int:post_id>/', views.edit_post, name='edit_post'),
    path('members/', views.member_list, name='member_list'),

    path('trash/empty/', views.empty_trash, name='empty_trash'),
   
    path("accounts/manage/", views.manage_accounts, name="manage_accounts"),
    path("accounts/delete/<int:user_id>/", views.delete_user, name="delete_user"),
]
