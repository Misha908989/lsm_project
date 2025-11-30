from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Count
from django.contrib.auth.models import User
from .models import Course, Module, Enrollment, Announcement
from .forms import CourseForm, ModuleFormSet
from assignments.models import Assignment, Certificate

def home_view(request):
    """Головна сторінка з статистикою та новими курсами"""
    context = {
        'total_courses': Course.objects.filter(is_published=True).count(),
        'total_students': User.objects.filter(profile__role='student').count(),
        'total_teachers': User.objects.filter(profile__role='teacher').count(),
        'total_certificates': Certificate.objects.count(),
        'new_courses': Course.objects.filter(is_published=True).order_by('-created_at')[:6],
        'announcements': Announcement.objects.filter(
            is_active=True
        ).order_by('-is_pinned', '-created_at')[:4],
    }
    
    return render(request, 'home.html', context)


class CourseListView(ListView):
    """Список всіх опублікованих курсів з пошуком та фільтрами"""
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 9
    
    def get_queryset(self):
        queryset = Course.objects.filter(is_published=True).select_related('instructor')
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search)
            )
        
        level = self.request.GET.get('level')
        if level:
            queryset = queryset.filter(level=level)
        
        instructor = self.request.GET.get('instructor')
        if instructor:
            queryset = queryset.filter(instructor__id=instructor)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_level'] = self.request.GET.get('level', '')
        
        context['instructors'] = User.objects.filter(
            profile__role__in=['teacher', 'admin']
        ).distinct()
        
        return context


class CourseDetailView(DetailView):
    """Детальна інформація про курс"""
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        
        context['modules'] = course.module_set.all().prefetch_related('lesson_set').order_by('order')
        
        context['modules_count'] = context['modules'].count()
        context['lessons_count'] = sum(module.lesson_set.count() for module in context['modules'])
        context['assignments_count'] = Assignment.objects.filter(
            lesson__module__course=course
        ).count()
        context['enrollments_count'] = course.enrollment_set.filter(is_active=True).count()
        
        if self.request.user.is_authenticated:
            context['is_enrolled'] = Enrollment.objects.filter(
                student=self.request.user,
                course=course,
                is_active=True
            ).exists()
            
            if context['is_enrolled']:
                context['enrollment'] = Enrollment.objects.get(
                    student=self.request.user,
                    course=course,
                    is_active=True
                )
        
        context['announcements'] = course.announcement_set.filter(
            is_active=True
        ).order_by('-is_pinned', '-created_at')[:3]
        
        return context


class CourseCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Створення нового курсу (викладачі та адміни)"""
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'
    
    def test_func(self):
        """Тільки викладачі та адміни можуть створювати курси"""
        return self.request.user.profile.role in ['teacher', 'admin']
    
    def get_form_kwargs(self):
        """Передаємо користувача в форму"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """Автоматично встановлюємо викладача при створенні"""
        if self.request.user.profile.role == 'teacher':
            form.instance.instructor = self.request.user
        elif not form.instance.instructor:
            form.instance.instructor = self.request.user
        
        messages.success(self.request, f'✅ Курс "{form.instance.title}" успішно створено!')
        return super().form_valid(form)
    
    def get_success_url(self):
        """Перенаправлення після успішного створення"""
        return reverse_lazy('courses:course_detail', kwargs={'slug': self.object.slug})


class CourseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редагування курсу (адміни та викладачі-власники)"""
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'
    
    def test_func(self):
        """Адмін може редагувати всі, викладач - тільки свої"""
        course = self.get_object()
        user = self.request.user
        return (
            user.profile.role == 'admin' or 
            (user.profile.role == 'teacher' and course.instructor == user)
        )
    
    def get_form_kwargs(self):
        """Передаємо користувача в форму"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, f'✅ Курс "{form.instance.title}" успішно оновлено!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('courses:course_detail', kwargs={'slug': self.object.slug})


class CourseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Видалення курсу (тільки адміни)"""
    model = Course
    template_name = 'courses/course_confirm_delete.html'
    success_url = reverse_lazy('courses:course_list')
    
    def test_func(self):
        """Тільки адміни можуть видаляти курси"""
        return self.request.user.profile.role == 'admin'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        
        context['modules_count'] = course.module_set.count()
        context['lessons_count'] = sum(
            module.lesson_set.count() 
            for module in course.module_set.all()
        )
        context['assignments_count'] = Assignment.objects.filter(
            lesson__module__course=course
        ).count()
        context['enrollments_count'] = course.enrollment_set.filter(
            is_active=True
        ).count()
        
        return context
    
    def delete(self, request, *args, **kwargs):
        course = self.get_object()
        messages.success(request, f'🗑️ Курс "{course.title}" видалено')
        return super().delete(request, *args, **kwargs)



@login_required
def course_enroll(request, slug):
    """Запис студента на курс"""
    course = get_object_or_404(Course, slug=slug, is_published=True)
    
    if request.user.profile.role != 'student':
        messages.error(request, '❌ Тільки студенти можуть записуватися на курси')
        return redirect('courses:course_detail', slug=slug)
    
    if course.max_students:
        current_enrollments = course.enrollment_set.filter(is_active=True).count()
        if current_enrollments >= course.max_students:
            messages.error(request, '❌ Досягнуто максимальної кількості студентів на курсі')
            return redirect('courses:course_detail', slug=slug)
    
    enrollment, created = Enrollment.objects.get_or_create(
        student=request.user,
        course=course,
        defaults={'is_active': True}
    )
    
    if created:
        messages.success(request, f'✅ Ви успішно записались на курс "{course.title}"!')
    else:
        if not enrollment.is_active:
            enrollment.is_active = True
            enrollment.save()
            messages.success(request, f'✅ Ви знову активували курс "{course.title}"!')
        else:
            messages.info(request, 'ℹ️ Ви вже записані на цей курс')
    
    return redirect('courses:course_detail', slug=slug)


@login_required
def course_unenroll(request, slug):
    """Відпис студента від курсу"""
    course = get_object_or_404(Course, slug=slug)
    
    try:
        enrollment = Enrollment.objects.get(
            student=request.user,
            course=course
        )
        enrollment.is_active = False
        enrollment.save()
        messages.success(request, f'✅ Ви відписались від курсу "{course.title}"')
    except Enrollment.DoesNotExist:
        messages.error(request, '❌ Ви не записані на цей курс')
    
    return redirect('courses:course_detail', slug=slug)

class MyCoursesView(LoginRequiredMixin, ListView):
    """Список курсів, на які записаний студент"""
    model = Enrollment
    template_name = 'courses/my_courses.html'
    context_object_name = 'enrollments'
    paginate_by = 12
    
    def get_queryset(self):
        return Enrollment.objects.filter(
            student=self.request.user,
            is_active=True
        ).select_related('course', 'course__instructor').order_by('-enrolled_at')

class TeacherCoursesView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Список курсів викладача"""
    model = Course
    template_name = 'courses/teacher_courses.html'
    context_object_name = 'courses'
    paginate_by = 12
    
    def test_func(self):
        """Тільки викладачі та адміни"""
        return self.request.user.profile.role in ['teacher', 'admin']
    
    def get_queryset(self):
        user = self.request.user
        if user.profile.role == 'admin':
            return Course.objects.all().select_related('instructor').order_by('-created_at')
        else:
            return Course.objects.filter(
                instructor=user
            ).select_related('instructor').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.profile.role == 'admin':
            courses = Course.objects.all()
        else:
            courses = Course.objects.filter(instructor=user)
        
        context['total_courses'] = courses.count()
        context['published_courses'] = courses.filter(is_published=True).count()
        context['draft_courses'] = courses.filter(is_published=False).count()
        context['total_students'] = Enrollment.objects.filter(
            course__in=courses,
            is_active=True
        ).count()
        
        return context




@login_required
def manage_modules(request, slug):
    """Управління модулями курсу"""
    course = get_object_or_404(Course, slug=slug)
    
    if not (request.user.profile.role == 'admin' or 
            (request.user.profile.role == 'teacher' and course.instructor == request.user)):
        messages.error(request, '❌ У вас немає доступу до редагування цього курсу')
        return redirect('courses:course_detail', slug=slug)
    
    if request.method == 'POST':
        formset = ModuleFormSet(request.POST, instance=course)
        if formset.is_valid():
            formset.save()
            messages.success(request, '✅ Модулі успішно збережено!')
            return redirect('courses:manage_modules', slug=slug)
    else:
        formset = ModuleFormSet(instance=course)
    
    context = {
        'course': course,
        'formset': formset,
    }
    
    return render(request, 'courses/manage_modules.html', context)



@login_required
def teacher_statistics(request, slug):
    """Статистика курсу для викладача"""
    course = get_object_or_404(Course, slug=slug)
    
    if not (request.user.profile.role == 'admin' or 
            (request.user.profile.role == 'teacher' and course.instructor == request.user)):
        messages.error(request, '❌ У вас немає доступу до цієї сторінки')
        return redirect('courses:course_detail', slug=slug)
    
    enrollments = Enrollment.objects.filter(
        course=course,
        is_active=True
    ).select_related('student', 'student__profile').order_by('-enrolled_at')
    
    modules = course.module_set.all().prefetch_related('lesson_set')
    
    context = {
        'course': course,
        'enrollments': enrollments,
        'modules': modules,
        'total_students': enrollments.count(),
        'modules_count': modules.count(),
        'lessons_count': sum(module.lesson_set.count() for module in modules),
        'assignments_count': Assignment.objects.filter(
            lesson__module__course=course
        ).count(),
    }
    
    return render(request, 'courses/teacher_statistics.html', context)

@login_required
def dashboard(request):
    """Дашборд користувача залежно від ролі"""
    user = request.user
    role = user.profile.role
    
    context = {
        'role': role,
    }
    
    if role == 'student':
        context['enrolled_courses'] = Enrollment.objects.filter(
            student=user,
            is_active=True
        ).select_related('course')[:5]
        context['total_courses'] = Enrollment.objects.filter(
            student=user,
            is_active=True
        ).count()
        
        return render(request, 'users/student_dashboard.html', context)
    
    elif role == 'teacher':
        from courses.models import Course
        courses = user.courses.all() 
        
        context['my_courses'] = courses[:5]
        context['total_courses'] = courses.count()
        context['total_students'] = Enrollment.objects.filter(
            course__in=courses,
            is_active=True
        ).count()
        
        return render(request, 'users/teacher_dashboard.html', context)
    
    elif role == 'admin':
        from courses.models import Course
        from django.contrib.auth.models import User
        
        context['total_courses'] = Course.objects.count()
        context['total_students'] = User.objects.filter(profile__role='student').count()
        context['total_teachers'] = User.objects.filter(profile__role='teacher').count()
        context['recent_enrollments'] = Enrollment.objects.select_related(
            'student', 'course'
        ).order_by('-enrolled_at')[:5]
        
        return render(request, 'users/admin_dashboard.html', context)
    
    return redirect('home')