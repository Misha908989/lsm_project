from django.db import models
from django.contrib.auth.models import User
from courses.models import Module
from django.core.exceptions import ValidationError

# Create your models here.

class Lesson(models.Model):
    """
    Модель уроку
    """
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Модуль'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Назва уроку'
    )
    content = models.TextField(
        verbose_name='Текстовий контент'
    )
    video_url = models.URLField(
        blank=True,
        verbose_name='Посилання на відео',
        help_text='Посилання на YouTube або інше відео'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок'
    )
    duration_minutes = models.PositiveIntegerField(
        default=30,
        verbose_name='Тривалість (хвилин)'
    )
    is_published = models.BooleanField(
        default=True,
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
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        ordering = ['module', 'order']
        unique_together = ['module', 'order']
    
    def __str__(self):
        return f'{self.module.course.title} - {self.module.title} - Урок {self.order}: {self.title}'
    
    def get_next_lesson(self):
        """Отримати наступний урок"""
        return Lesson.objects.filter(
            module=self.module,
            order__gt=self.order
        ).first()
    
    def get_previous_lesson(self):
        """Отримати попередній урок"""
        return Lesson.objects.filter(
            module=self.module,
            order__lt=self.order
        ).order_by('-order').first()


class LessonMedia(models.Model):
    """
    Модель медіафайлів уроку (зображення, документи)
    """
    FILE_TYPE_CHOICES = [
        ('image', 'Зображення'),
        ('video', 'Відео'),
        ('document', 'Документ'),
    ]
    
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='media_files',
        verbose_name='Урок'
    )
    file = models.FileField(
        upload_to='lessons/media/%Y/%m/%d/',
        verbose_name='Файл'
    )
    file_type = models.CharField(
        max_length=10,
        choices=FILE_TYPE_CHOICES,
        verbose_name='Тип файлу'
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Назва'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Опис'
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата завантаження'
    )
    
    class Meta:
        verbose_name = 'Медіафайл уроку'
        verbose_name_plural = 'Медіафайли уроків'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f'{self.get_file_type_display()} для "{self.lesson.title}"'
    
    def clean(self):
        """Валідація файлу"""
        if self.file:
            if self.file.size > 50 * 1024 * 1024:
                raise ValidationError('Розмір файлу не повинен перевищувати 50 МБ')