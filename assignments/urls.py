from django.urls import path
from . import views

app_name = 'assignments'

urlpatterns = [
    # Список завдань курсу
    path('course/<slug:course_slug>/', views.AssignmentListView.as_view(), name='assignment_list'),
    
    # Деталі завдання
    path('<int:assignment_id>/', views.AssignmentDetailView.as_view(), name='assignment_detail'),
    
    # CRUD завдань (викладачі)
    path('lesson/<int:lesson_id>/create/', views.AssignmentCreateView.as_view(), name='assignment_create'),
    path('<int:assignment_id>/edit/', views.AssignmentUpdateView.as_view(), name='assignment_update'),
    path('<int:assignment_id>/delete/', views.AssignmentDeleteView.as_view(), name='assignment_delete'),
    
    # Здача завдання (студенти)
    path('<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
    
    # Оцінювання (викладачі)
    path('submission/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'),
    path('<int:assignment_id>/submissions/', views.SubmissionsListView.as_view(), name='submissions_list'),
    
    # Мої оцінки (студенти)
    path('my-grades/', views.my_grades, name='my_grades'),

    # Сертифікати
    path('certificates/my/', views.my_certificates, name='my_certificates'),
    path('certificates/generate/<slug:course_slug>/', views.generate_certificate, name='generate_certificate'),
    path('certificates/<str:certificate_id>/', views.certificate_detail, name='certificate_detail'),
    path('certificates/<str:certificate_id>/download/', views.download_certificate, name='download_certificate'),
    path('certificates/course/<slug:course_slug>/', views.course_certificates, name='course_certificates'),
]