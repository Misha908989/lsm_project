from django.urls import path
from . import views

app_name = 'lessons'

urlpatterns = [
    # Список уроків модуля
    path('module/<int:module_id>/', views.LessonListView.as_view(), name='lesson_list'),
    
    # Деталі уроку
    path('<int:lesson_id>/', views.LessonDetailView.as_view(), name='lesson_detail'),
    
    # CRUD уроків (викладачі)
    path('module/<int:module_id>/create/', views.LessonCreateView.as_view(), name='lesson_create'),
    path('<int:lesson_id>/edit/', views.LessonUpdateView.as_view(), name='lesson_update'),
    path('<int:lesson_id>/delete/', views.LessonDeleteView.as_view(), name='lesson_delete'),
    
    # Медіафайли
    path('<int:lesson_id>/media/', views.manage_lesson_media, name='manage_lesson_media'),
    
    # Прогрес
    path('<int:lesson_id>/complete/', views.mark_lesson_complete, name='mark_complete'),
]