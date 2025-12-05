from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from .models import Lesson, LessonMedia, LessonProgress
from courses.models import Course, Module, Enrollment
from .forms import LessonForm, LessonMediaFormSet

# Create your views here.

class LessonListView(LoginRequiredMixin, ListView):
    """Список уроків модуля"""
    model = Lesson
    template_name = 'lessons/lesson_list.html'
    context_object_name = 'lessons'
    
    def get_queryset(self):
        self.module = get_object_or_404(Module, id=self.kwargs['module_id'])
        return Lesson.objects.filter(
            module=self.module,
            is_published=True
        ).order_by('order')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['module'] = self.module
        context['course'] = self.module.course
        
        user = self.request.user
        context['is_enrolled'] = Enrollment.objects.filter(
            student=user,
            course=self.module.course,
            is_active=True
        ).exists()
        
        context['is_teacher'] = (
            user.profile.role in ['teacher', 'admin'] or
            self.module.course.instructor == user
        )
        
        return context

class LessonDetailView(LoginRequiredMixin, DetailView):
    """Детальна інформація про урок"""
    model = Lesson
    template_name = 'lessons/lesson_detail.html'
    context_object_name = 'lesson'
    pk_url_kwarg = 'lesson_id'
    
    def get_object(self, queryset=None):
        lesson = super().get_object(queryset)
        
        user = self.request.user
        course = lesson.module.course
        
        if lesson.is_free:
            return lesson
        
        if user.profile.role in ['teacher', 'admin'] or course.instructor == user:
            return lesson
        
        is_enrolled = Enrollment.objects.filter(
            student=user,
            course=course,
            is_active=True
        ).exists()
        
        if not is_enrolled:
            messages.error(self.request, 'Ви не маєте доступу до цього уроку. Запишіться на курс.')
            return redirect('courses:course_detail', slug=course.slug)
        
        return lesson
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lesson = self.get_object()
        user = self.request.user
        
        context['module'] = lesson.module
        context['course'] = lesson.module.course
        
        context['media_files'] = lesson.media_files.all()
        
        context['previous_lesson'] = lesson.get_previous_lesson()
        context['next_lesson'] = lesson.get_next_lesson()
        
        context['module_lessons'] = lesson.module.lesson_set.filter(
            is_published=True
        ).order_by('order')

        if user.profile.role == 'student':
            progress, created = LessonProgress.objects.get_or_create(
                lesson=lesson,
                student=user
            )
            context['progress'] = progress
        
        context['is_teacher'] = (
            user.profile.role in ['teacher', 'admin'] or
            lesson.module.course.instructor == user
        )
        
        return context

class LessonCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Створення нового уроку"""
    model = Lesson
    form_class = LessonForm
    template_name = 'lessons/lesson_form.html'
    
    def test_func(self):
        """Перевірка прав доступу"""
        module_id = self.kwargs.get('module_id')
        module = get_object_or_404(Module, id=module_id)
        user = self.request.user
        
        return (
            user.profile.role == 'admin' or
            (user.profile.role == 'teacher' and module.course.instructor == user)
        )
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        module_id = self.kwargs.get('module_id')
        module = get_object_or_404(Module, id=module_id)
        kwargs['course'] = module.course
        return kwargs
    
    def form_valid(self, form):
        module_id = self.kwargs.get('module_id')
        form.instance.module = get_object_or_404(Module, id=module_id)
        
        messages.success(self.request, f'✅ Урок "{form.instance.title}" успішно створено!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        module_id = self.kwargs.get('module_id')
        context['module'] = get_object_or_404(Module, id=module_id)
        context['course'] = context['module'].course
        return context
    
    def get_success_url(self):
        return reverse_lazy('lessons:lesson_detail', kwargs={'lesson_id': self.object.id})


class LessonUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редагування уроку"""
    model = Lesson
    form_class = LessonForm
    template_name = 'lessons/lesson_form.html'
    pk_url_kwarg = 'lesson_id'
    
    def test_func(self):
        lesson = self.get_object()
        user = self.request.user
        
        return (
            user.profile.role == 'admin' or
            (user.profile.role == 'teacher' and lesson.module.course.instructor == user)
        )
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['course'] = self.object.module.course
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, f'✅ Урок "{form.instance.title}" успішно оновлено!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['module'] = self.object.module
        context['course'] = self.object.module.course
        return context
    
    def get_success_url(self):
        return reverse_lazy('lessons:lesson_detail', kwargs={'lesson_id': self.object.id})


class LessonDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Видалення уроку"""
    model = Lesson
    template_name = 'lessons/lesson_confirm_delete.html'
    pk_url_kwarg = 'lesson_id'
    
    def test_func(self):
        lesson = self.get_object()
        user = self.request.user
        
        return (
            user.profile.role == 'admin' or
            (user.profile.role == 'teacher' and lesson.module.course.instructor == user)
        )
    
    def get_success_url(self):
        module = self.object.module
        messages.success(self.request, f'🗑️ Урок "{self.object.title}" видалено')
        return reverse_lazy('courses:course_detail', kwargs={'slug': module.course.slug})

@login_required
def manage_lesson_media(request, lesson_id):
    """Управління медіафайлами уроку"""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    user = request.user
    if not (user.profile.role == 'admin' or 
            (user.profile.role == 'teacher' and lesson.module.course.instructor == user)):
        messages.error(request, '❌ У вас немає доступу до редагування цього уроку')
        return redirect('lessons:lesson_detail', lesson_id=lesson_id)
    
    if request.method == 'POST':
        formset = LessonMediaFormSet(request.POST, request.FILES, instance=lesson)
        if formset.is_valid():
            formset.save()
            messages.success(request, '✅ Медіафайли успішно збережено!')
            return redirect('lessons:manage_lesson_media', lesson_id=lesson_id)
    else:
        formset = LessonMediaFormSet(instance=lesson)
    
    context = {
        'lesson': lesson,
        'module': lesson.module,
        'course': lesson.module.course,
        'formset': formset,
    }
    
    return render(request, 'lessons/manage_media.html', context)

@login_required
def mark_lesson_complete(request, lesson_id):
    """Позначити урок як завершений"""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    if request.user.profile.role != 'student':
        messages.error(request, '❌ Тільки студенти можуть позначати уроки як завершені')
        return redirect('lessons:lesson_detail', lesson_id=lesson_id)
    
    is_enrolled = Enrollment.objects.filter(
        student=request.user,
        course=lesson.module.course,
        is_active=True
    ).exists()
    
    if not is_enrolled:
        messages.error(request, '❌ Ви не записані на цей курс')
        return redirect('courses:course_detail', slug=lesson.module.course.slug)
    
    progress, created = LessonProgress.objects.get_or_create(
        lesson=lesson,
        student=request.user
    )
    
    if not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = timezone.now()
        progress.save()
        
        update_course_progress(request.user, lesson.module.course)
        
        messages.success(request, f'✅ Урок "{lesson.title}" позначено як завершений!')
    else:
        messages.info(request, 'ℹ️ Ви вже завершили цей урок')
    
    next_lesson = lesson.get_next_lesson()
    if next_lesson:
        return redirect('lessons:lesson_detail', lesson_id=next_lesson.id)
    else:
        return redirect('lessons:lesson_detail', lesson_id=lesson_id)


def update_course_progress(student, course):
    """Оновити прогрес студента по курсу"""
    try:
        enrollment = Enrollment.objects.get(
            student=student,
            course=course,
            is_active=True
        )
        
        total_lessons = Lesson.objects.filter(
            module__course=course,
            is_published=True
        ).count()
        
        if total_lessons > 0:
            completed_lessons = LessonProgress.objects.filter(
                lesson__module__course=course,
                student=student,
                is_completed=True
            ).count()
            
            progress = int((completed_lessons / total_lessons) * 100)
            enrollment.progress = progress
            enrollment.save()
    except Enrollment.DoesNotExist:
        pass