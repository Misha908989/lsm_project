from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import (PasswordResetView, PasswordResetDoneView,PasswordResetConfirmView,PasswordResetCompleteView)
from django.urls import reverse_lazy
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm, UserLoginForm


# Create your views here.
def register(request):
    """
    Реєстрація нового користувача
    """
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Акаунт {username} успішно створено! Тепер ви можете увійти.')
            login(request, user)
            return redirect('home')
    else:
        form = UserRegisterForm()
    
    return render(request, 'users/register.html', {'form': form})


def user_login(request):
    """
    Вхід користувача
    """
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Ласкаво просимо, {username}!')
                
                next_page = request.GET.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect('home')
            else:
                messages.error(request, "Невірне ім'я користувача або пароль")
    else:
        form = UserLoginForm()
    
    return render(request, 'users/login.html', {'form': form})


def user_logout(request):
    """
    Вихід користувача
    """
    logout(request)
    messages.info(request, 'Ви успішно вийшли з системи')
    return redirect('home')


@login_required
def profile(request):
    """
    Профіль користувача з можливістю редагування
    """
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=request.user.profile
        )
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Ваш профіль успішно оновлено!')
            return redirect('users:profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    
    return render(request, 'users/profile.html', context)


@login_required
def dashboard(request):
    """Дашборд користувача залежно від ролі"""
    from courses.models import Course, Enrollment
    from assignments.models import Submission
    
    user = request.user
    role = user.profile.role
    
    context = {
        'role': role,
    }
    
    if role == 'student':
        enrollments = Enrollment.objects.filter(
            student=user,
            is_active=True
        ).select_related('course')
        
        context['enrolled_courses'] = enrollments[:5]
        context['total_courses'] = enrollments.count()
        
        submissions = Submission.objects.filter(
            student=user
        ).select_related('assignment')
        
        context['total_submissions'] = submissions.count()
        context['pending_submissions'] = submissions.filter(status='pending').count()
        context['graded_submissions'] = submissions.filter(status='graded').count()
        
        return render(request, 'users/student_dashboard.html', context)
    
    elif role == 'teacher':
        courses = user.courses.all() 
        
        context['my_courses'] = courses[:5]
        context['total_courses'] = courses.count()
        context['total_students'] = Enrollment.objects.filter(
            course__in=courses,
            is_active=True
        ).count()
        
        from assignments.models import Assignment
        pending_count = Submission.objects.filter(
            assignment__lesson__module__course__in=courses,
            status='pending'
        ).count()
        context['pending_submissions'] = pending_count
        
        return render(request, 'users/teacher_dashboard.html', context)
    
    elif role == 'admin':
        from django.contrib.auth.models import User
        
        context['total_courses'] = Course.objects.count()
        context['total_students'] = User.objects.filter(profile__role='student').count()
        context['total_teachers'] = User.objects.filter(profile__role='teacher').count()
        context['recent_enrollments'] = Enrollment.objects.select_related(
            'student', 'course'
        ).order_by('-enrolled_at')[:5]
        
        return render(request, 'users/admin_dashboard.html', context)
    
    return redirect('home')


class CustomPasswordResetView(PasswordResetView):
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    success_url = reverse_lazy('users:password_reset_done')


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'users/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('users:password_reset_complete')


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'users/password_reset_complete.html'