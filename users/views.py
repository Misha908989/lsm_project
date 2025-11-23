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
    """
    Особистий кабінет користувача (дашборд)
    """
    user = request.user
    
    if user.profile.is_student():
        enrollments = user.enrollments.filter(is_active=True).select_related('course')
        submissions = user.submissions.all()[:5]
        certificates = user.certificates.all()
        
        context = {
            'enrollments': enrollments,
            'submissions': submissions,
            'certificates': certificates,
        }
        return render(request, 'users/student_dashboard.html', context)
    
    elif user.profile.is_teacher():
        courses = user.courses_taught.all()
        pending_submissions = []
        for course in courses:
            for module in course.modules.all():
                for lesson in module.lessons.all():
                    for assignment in lesson.assignments.all():
                        pending_submissions.extend(
                            assignment.submissions.filter(status='pending')
                        )
        
        context = {
            'courses': courses,
            'pending_submissions': pending_submissions[:10],
        }
        return render(request, 'users/teacher_dashboard.html', context)
    
    else:
        from courses.models import Course, Enrollment
        from django.contrib.auth.models import User
        
        total_users = User.objects.count()
        total_courses = Course.objects.count()
        total_enrollments = Enrollment.objects.count()
        
        context = {
            'total_users': total_users,
            'total_courses': total_courses,
            'total_enrollments': total_enrollments,
        }
        return render(request, 'users/admin_dashboard.html', context)


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