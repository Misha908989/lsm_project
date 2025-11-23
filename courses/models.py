from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse
from django.utils import timezone

# Create your models here.

class Course(models.Model):
    """
    Модель курсу
    """
    LEVEL_CHOICES = [
        ('beginner', 'Початковий'),
        ('intermediate', 'Середній'),
        ('advanced', 'Просунутий'),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name='Назва курсу'
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        blank=True,
        verbose_name='URL'
    )
    description = models.TextField(
        verbose_name='Опис курсу'
    )
    instructor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='courses_taught',
        verbose_name='Викладач'
    )
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default='beginner',
        verbose_name='Рівень'
    )
    duration_weeks = models.PositiveIntegerField(
        default=4,
        verbose_name='Тривалість (тижнів)'
    )
    thumbnail = models.ImageField(
        upload_to='courses/thumbnails/',
        blank=True,
        null=True,
        verbose_name='Обкладинка'
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name='Опублікований'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата створення'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата оновлення'
    )
    
    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курси'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('courses:detail', kwargs={'slug': self.slug})
    
    def get_students_count(self):
        """Кількість студентів на курсі"""
        return self.enrollments.filter(is_active=True).count()
    
    def get_modules_count(self):
        """Кількість модулів у курсі"""
        return self.modules.count()
    
    def get_lessons_count(self):
        """Загальна кількість уроків у курсі"""
        return sum(module.lessons.count() for module in self.modules.all())


class Module(models.Model):
    """
    Модель модуля курсу
    """
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='modules',
        verbose_name='Курс'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Назва модуля'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Опис модуля'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата створення'
    )
    
    class Meta:
        verbose_name = 'Модуль'
        verbose_name_plural = 'Модулі'
        ordering = ['course', 'order']
        unique_together = ['course', 'order']
    
    def __str__(self):
        return f'{self.course.title} - Модуль {self.order}: {self.title}'
    
    def get_lessons_count(self):
        """Кількість уроків у модулі"""
        return self.lessons.count()


class Enrollment(models.Model):
    """
    Модель запису студента на курс
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='Студент'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='Курс'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активний'
    )
    enrolled_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата запису'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата завершення'
    )
    progress = models.PositiveIntegerField(
        default=0,
        verbose_name='Прогрес (%)'
    )
    
    class Meta:
        verbose_name = 'Запис на курс'
        verbose_name_plural = 'Записи на курси'
        unique_together = ['student', 'course']
        ordering = ['-enrolled_at']
    
    def __str__(self):
        return f'{self.student.username} - {self.course.title}'
    
    def is_completed(self):
        """Чи завершений курс"""
        return self.completed_at is not None
    
    def complete_course(self):
        """Відмітити курс як завершений"""
        self.completed_at = timezone.now()
        self.progress = 100
        self.save()


class Announcement(models.Model):
    """
    Модель оголошення
    """
    TYPE_CHOICES = [
        ('info', 'Інформація'),
        ('warning', 'Попередження'),
        ('success', 'Успіх'),
        ('danger', 'Важливе'),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name='Заголовок'
    )
    content = models.TextField(
        verbose_name='Текст оголошення'
    )
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='info',
        verbose_name='Тип'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='announcements',
        verbose_name='Курс'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активне'
    )
    is_pinned = models.BooleanField(
        default=False,
        verbose_name='Закріплене'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='announcements',
        verbose_name='Створив'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата створення'
    )
    
    class Meta:
        verbose_name = 'Оголошення'
        verbose_name_plural = 'Оголошення'
        ordering = ['-is_pinned', '-created_at']
    
    def __str__(self):
        return self.title