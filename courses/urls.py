from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.CourseListView.as_view(), name='course_list'),
    
    path('create/', views.CourseCreateView.as_view(), name='course_create'),
    path('<slug:slug>/edit/', views.CourseUpdateView.as_view(), name='course_update'),
    path('<slug:slug>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),
    
    path('<slug:slug>/enroll/', views.course_enroll, name='course_enroll'),
    path('<slug:slug>/unenroll/', views.course_unenroll, name='course_unenroll'),
    
    path('my/courses/', views.MyCoursesView.as_view(), name='my_courses'),
    
    path('teacher/my-courses/', views.TeacherCoursesView.as_view(), name='teacher_courses'),
    path('teacher/<slug:slug>/modules/', views.manage_modules, name='manage_modules'),
    path('teacher/<slug:slug>/statistics/', views.teacher_statistics, name='teacher_statistics'),
    
    path('<slug:slug>/', views.CourseDetailView.as_view(), name='course_detail'),
]