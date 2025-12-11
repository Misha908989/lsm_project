from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Avg, Count
from .models import Assignment, Submission, Grade, Certificate
from courses.models import Course, Enrollment
from lessons.models import Lesson
from .forms import AssignmentForm, SubmissionForm, GradeForm



class AssignmentListView(LoginRequiredMixin, ListView):
    """Список завдань курсу"""
    model = Assignment
    template_name = 'assignments/assignment_list.html'
    context_object_name = 'assignments'
    paginate_by = 20
    
    def get_queryset(self):
        course_slug = self.kwargs.get('course_slug')
        self.course = get_object_or_404(Course, slug=course_slug)
        
        return Assignment.objects.filter(
            lesson__module__course=self.course
        ).select_related('lesson', 'lesson__module').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.course
        
        user = self.request.user
        
        if user.profile.role == 'student':
            submissions = Submission.objects.filter(
                student=user,
                assignment__lesson__module__course=self.course
            ).select_related('assignment')
            
            context['my_submissions'] = {
                sub.assignment_id: sub for sub in submissions
            }
        
        context['is_teacher'] = (
            user.profile.role in ['teacher', 'admin'] or
            self.course.instructor == user
        )
        
        return context





class AssignmentDetailView(LoginRequiredMixin, DetailView):
    """Детальна інформація про завдання"""
    model = Assignment
    template_name = 'assignments/assignment_detail.html'
    context_object_name = 'assignment'
    pk_url_kwarg = 'assignment_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assignment = self.get_object()
        user = self.request.user
        
        context['course'] = assignment.lesson.module.course
        context['lesson'] = assignment.lesson
        
        if user.profile.role == 'student':
            try:
                submission = Submission.objects.get(
                    assignment=assignment,
                    student=user
                )
                context['my_submission'] = submission
                
                if hasattr(submission, 'grade'):
                    context['my_grade'] = submission.grade
            except Submission.DoesNotExist:
                context['my_submission'] = None
        
        if user.profile.role in ['teacher', 'admin'] or assignment.lesson.module.course.instructor == user:
            context['is_teacher'] = True
            context['submissions_count'] = assignment.submissions.count()
            context['graded_count'] = assignment.submissions.filter(status='graded').count()
            context['pending_count'] = assignment.submissions.filter(status='pending').count()
            
            avg_score = assignment.submissions.filter(
                grade__isnull=False
            ).aggregate(Avg('grade__score'))['grade__score__avg']
            context['average_score'] = round(avg_score, 2) if avg_score else None
        
        return context



class AssignmentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Створення завдання"""
    model = Assignment
    form_class = AssignmentForm
    template_name = 'assignments/assignment_form.html'
    
    def test_func(self):
        lesson_id = self.kwargs.get('lesson_id')
        lesson = get_object_or_404(Lesson, id=lesson_id)
        user = self.request.user
        
        return (
            user.profile.role == 'admin' or
            (user.profile.role == 'teacher' and lesson.module.course.instructor == user)
        )
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        lesson_id = self.kwargs.get('lesson_id')
        lesson = get_object_or_404(Lesson, id=lesson_id)
        kwargs['course'] = lesson.module.course
        return kwargs
    
    def form_valid(self, form):
        lesson_id = self.kwargs.get('lesson_id')
        form.instance.lesson = get_object_or_404(Lesson, id=lesson_id)
        
        messages.success(self.request, f'✅ Завдання "{form.instance.title}" успішно створено!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lesson_id = self.kwargs.get('lesson_id')
        context['lesson'] = get_object_or_404(Lesson, id=lesson_id)
        context['course'] = context['lesson'].module.course
        return context
    
    def get_success_url(self):
        return reverse_lazy('assignments:assignment_detail', kwargs={'assignment_id': self.object.id})


class AssignmentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редагування завдання"""
    model = Assignment
    form_class = AssignmentForm
    template_name = 'assignments/assignment_form.html'
    pk_url_kwarg = 'assignment_id'
    
    def test_func(self):
        assignment = self.get_object()
        user = self.request.user
        
        return (
            user.profile.role == 'admin' or
            (user.profile.role == 'teacher' and assignment.lesson.module.course.instructor == user)
        )
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['course'] = self.object.lesson.module.course
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, f'✅ Завдання "{form.instance.title}" успішно оновлено!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lesson'] = self.object.lesson
        context['course'] = self.object.lesson.module.course
        return context
    
    def get_success_url(self):
        return reverse_lazy('assignments:assignment_detail', kwargs={'assignment_id': self.object.id})


class AssignmentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Видалення завдання"""
    model = Assignment
    template_name = 'assignments/assignment_confirm_delete.html'
    pk_url_kwarg = 'assignment_id'
    
    def test_func(self):
        assignment = self.get_object()
        user = self.request.user
        
        return (
            user.profile.role == 'admin' or
            (user.profile.role == 'teacher' and assignment.lesson.module.course.instructor == user)
        )
    
    def get_success_url(self):
        course = self.object.lesson.module.course
        messages.success(self.request, f'🗑️ Завдання "{self.object.title}" видалено')
        return reverse_lazy('assignments:assignment_list', kwargs={'course_slug': course.slug})





@login_required
def submit_assignment(request, assignment_id):
    """Здача завдання студентом"""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    course = assignment.lesson.module.course
    
    if request.user.profile.role != 'student':
        messages.error(request, '❌ Тільки студенти можуть здавати завдання')
        return redirect('assignments:assignment_detail', assignment_id=assignment_id)
    
    is_enrolled = Enrollment.objects.filter(
        student=request.user,
        course=course,
        is_active=True
    ).exists()
    
    if not is_enrolled:
        messages.error(request, '❌ Ви не записані на цей курс')
        return redirect('courses:course_detail', slug=course.slug)
    
    if assignment.is_overdue() and not assignment.allow_late_submission:
        messages.error(request, '❌ Дедлайн минув. Здача завдання більше неможлива')
        return redirect('assignments:assignment_detail', assignment_id=assignment_id)
    
    try:
        submission = Submission.objects.get(assignment=assignment, student=request.user)
        is_new = False
    except Submission.DoesNotExist:
        submission = None
        is_new = True
    
    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES, instance=submission, assignment=assignment)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.assignment = assignment
            submission.student = request.user
            submission.status = 'pending'
            submission.save()
            
            if is_new:
                messages.success(request, '✅ Завдання успішно здано!')
            else:
                messages.success(request, '✅ Завдання оновлено!')
            
            return redirect('assignments:assignment_detail', assignment_id=assignment_id)
    else:
        form = SubmissionForm(instance=submission, assignment=assignment)
    
    context = {
        'assignment': assignment,
        'course': course,
        'lesson': assignment.lesson,
        'form': form,
        'submission': submission,
        'is_new': is_new,
    }
    
    return render(request, 'assignments/submit_assignment.html', context)




@login_required
def grade_submission(request, submission_id):
    """Оцінювання здачі викладачем"""
    submission = get_object_or_404(Submission, id=submission_id)
    assignment = submission.assignment
    course = assignment.lesson.module.course
    
    user = request.user
    if not (user.profile.role == 'admin' or 
            (user.profile.role == 'teacher' and course.instructor == user)):
        messages.error(request, '❌ У вас немає доступу до оцінювання')
        return redirect('assignments:assignment_detail', assignment_id=assignment.id)
    
    try:
        grade = Grade.objects.get(submission=submission)
        is_new = False
    except Grade.DoesNotExist:
        grade = None
        is_new = True
    
    if request.method == 'POST':
        form = GradeForm(request.POST, instance=grade, assignment=assignment)
        if form.is_valid():
            grade = form.save(commit=False)
            grade.submission = submission
            grade.teacher = request.user
            grade.save()
            
            if is_new:
                messages.success(request, f'✅ Роботу студента {submission.student.username} оцінено!')
            else:
                messages.success(request, f'✅ Оцінку студента {submission.student.username} оновлено!')
            
            return redirect('assignments:submissions_list', assignment_id=assignment.id)
    else:
        form = GradeForm(instance=grade, assignment=assignment)
    
    context = {
        'submission': submission,
        'assignment': assignment,
        'course': course,
        'form': form,
        'is_new': is_new,
    }
    
    return render(request, 'assignments/grade_submission.html', context)

class SubmissionsListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Список здач завдання для викладача"""
    model = Submission
    template_name = 'assignments/submissions_list.html'
    context_object_name = 'submissions'
    
    def test_func(self):
        assignment_id = self.kwargs.get('assignment_id')
        assignment = get_object_or_404(Assignment, id=assignment_id)
        user = self.request.user
        
        return (
            user.profile.role == 'admin' or
            (user.profile.role == 'teacher' and assignment.lesson.module.course.instructor == user)
        )
    
    def get_queryset(self):
        assignment_id = self.kwargs.get('assignment_id')
        self.assignment = get_object_or_404(Assignment, id=assignment_id)
        
        status = self.request.GET.get('status')
        queryset = Submission.objects.filter(
            assignment=self.assignment
        ).select_related('student', 'student__profile')
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-submitted_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assignment'] = self.assignment
        context['course'] = self.assignment.lesson.module.course
        context['selected_status'] = self.request.GET.get('status', '')
        
        context['total_submissions'] = self.assignment.submissions.count()
        context['graded_submissions'] = self.assignment.submissions.filter(status='graded').count()
        context['pending_submissions'] = self.assignment.submissions.filter(status='pending').count()
        
        return context




@login_required
def my_grades(request):
    """Сторінка з оцінками студента"""
    if request.user.profile.role != 'student':
        messages.error(request, '❌ Ця сторінка доступна тільки для студентів')
        return redirect('home')
    
    submissions = Submission.objects.filter(
        student=request.user
    ).select_related(
        'assignment',
        'assignment__lesson',
        'assignment__lesson__module',
        'assignment__lesson__module__course'
    ).prefetch_related('grade').order_by('-submitted_at')
    
    total_submissions = submissions.count()
    graded_submissions = submissions.filter(status='graded').count()
    pending_submissions = submissions.filter(status='pending').count()
    
    grades = Grade.objects.filter(submission__student=request.user)
    if grades.exists():
        avg_score = grades.aggregate(Avg('score'))['score__avg']
        avg_percentage = sum(g.get_percentage() for g in grades) / grades.count()
    else:
        avg_score = None
        avg_percentage = None
    
    context = {
        'submissions': submissions,
        'total_submissions': total_submissions,
        'graded_submissions': graded_submissions,
        'pending_submissions': pending_submissions,
        'avg_score': round(avg_score, 2) if avg_score else None,
        'avg_percentage': round(avg_percentage, 2) if avg_percentage else None,
    }
    
    return render(request, 'assignments/my_grades.html', context)