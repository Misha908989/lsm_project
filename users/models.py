from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class Profile(models.Model):
    """
    Модель профілю користувача - розширення стандартної моделі User
    """
    ROLE_CHOICES = [
        ('student', 'Студент'),
        ('teacher', 'Викладач'),
        ('admin', 'Адміністратор'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile',
        verbose_name='Користувач'
    )
    bio = models.TextField(
        max_length=500, 
        blank=True, 
        verbose_name='Біографія'
    )
    avatar = models.ImageField(
        upload_to='avatars/', 
        blank=True, 
        null=True,
        verbose_name='Аватар'
    )
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='student',
        verbose_name='Роль'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата реєстрації'
    )
    
    class Meta:
        verbose_name = 'Профіль'
        verbose_name_plural = 'Профілі'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Профіль {self.user.username}'
    
    def is_student(self):
        """Перевірка чи користувач є студентом"""
        return self.role == 'student'
    
    def is_teacher(self):
        """Перевірка чи користувач є викладачем"""
        return self.role in ['teacher', 'admin']
    
    def is_admin(self):
        """Перевірка чи користувач є адміністратором"""
        return self.role == 'admin'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Створити профіль при створенні користувача"""
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Зберегти профіль при збереженні користувача"""
    if hasattr(instance, 'profile'):
        instance.profile.save()