from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.utils import timezone
from lessons.models import Lesson
from courses.models import Course
import uuid


class Assignment(models.Model):
    """Модель завдання"""
    
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, verbose_name='Урок', related_name='assignments')
    title = models.CharField('Назва завдання', max_length=200)
    description = models.TextField('Опис завдання')
    max_score = models.PositiveIntegerField('Максимальний бал', default=100, validators=[MinValueValidator(1), MaxValueValidator(1000)])
    due_date = models.DateTimeField('Дедлайн', null=True, blank=True)
    allow_late_submission = models.BooleanField('Дозволити здачу після дедлайну', default=True)
    submission_type = models.CharField(
        'Тип здачі',
        max_length=20,
        choices=[
            ('text', 'Текст'),
            ('file', 'Файл'),
            ('both', 'Текст + Файл'),
        ],
        default='both'
    )
    created_at = models.DateTimeField('Дата створення', auto_now_add=True)
    updated_at = models.DateTimeField('Дата оновлення', auto_now=True)
    
    class Meta:
        verbose_name = 'Завдання'
        verbose_name_plural = 'Завдання'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.lesson.title} - {self.title}'
    
    def is_overdue(self):
        """Перевірка чи минув дедлайн"""
        if not self.due_date:
            return False
        return timezone.now() > self.due_date
    
    def get_submission_count(self):
        """Кількість здач"""
        return self.submissions.count()
    
    def get_graded_count(self):
        """Кількість оцінених здач"""
        return self.submissions.filter(status='graded').count()


class Submission(models.Model):
    """Модель здачі завдання студентом"""
    
    STATUS_CHOICES = [
        ('pending', 'На перевірці'),
        ('graded', 'Оцінено'),
        ('returned', 'Повернуто на доопрацювання'),
    ]
    
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, verbose_name='Завдання', related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Студент', related_name='submissions')
    content = models.TextField('Текст відповіді', blank=True)
    file = models.FileField(
        'Файл',
        upload_to='submissions/%Y/%m/',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'doc', 'docx', 'txt', 'zip', 'jpg', 'jpeg', 'png']
            )
        ]
    )
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField('Дата здачі', auto_now_add=True)
    updated_at = models.DateTimeField('Дата оновлення', auto_now=True)
    
    class Meta:
        verbose_name = 'Здача завдання'
        verbose_name_plural = 'Здачі завдань'
        ordering = ['-submitted_at']
        unique_together = ['assignment', 'student']
    
    def __str__(self):
        return f'{self.student.username} - {self.assignment.title}'
    
    def is_late(self):
        """Перевірка чи здано після дедлайну"""
        if not self.assignment.due_date:
            return False
        return self.submitted_at > self.assignment.due_date
    
    def get_file_size(self):
        """Розмір файлу в зручному форматі"""
        if not self.file:
            return None
        
        size = self.file.size
        if size < 1024:
            return f'{size} B'
        elif size < 1024 * 1024:
            return f'{size / 1024:.2f} KB'
        elif size < 1024 * 1024 * 1024:
            return f'{size / (1024 * 1024):.2f} MB'
        else:
            return f'{size / (1024 * 1024 * 1024):.2f} GB'


class Grade(models.Model):
    """Модель оцінки за завдання"""
    
    submission = models.OneToOneField(Submission, on_delete=models.CASCADE, verbose_name='Здача', related_name='grade')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Викладач', related_name='grades_given')
    score = models.PositiveIntegerField('Бал')
    feedback = models.TextField('Відгук', blank=True)
    graded_at = models.DateTimeField('Дата оцінювання', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Оцінка'
        verbose_name_plural = 'Оцінки'
        ordering = ['-graded_at']
    
    def __str__(self):
        return f'{self.submission.student.username} - {self.submission.assignment.title} - {self.score}'
    
    def get_percentage(self):
        """Відсоток виконання"""
        max_score = self.submission.assignment.max_score
        if max_score > 0:
            return round((self.score / max_score) * 100, 2)
        return 0
    
    def get_letter_grade(self):
        """Буквена оцінка"""
        percentage = self.get_percentage()
        if percentage >= 90:
            return 'A'
        elif percentage >= 80:
            return 'B'
        elif percentage >= 70:
            return 'C'
        elif percentage >= 60:
            return 'D'
        else:
            return 'F'
    
    def save(self, *args, **kwargs):
        """Автоматично оновити статус здачі при оцінюванні"""
        super().save(*args, **kwargs)
        self.submission.status = 'graded'
        self.submission.save()


class Certificate(models.Model):
    """Модель сертифіката про завершення курсу"""
    
    certificate_id = models.CharField('ID сертифіката', max_length=100, unique=True, editable=False)
    student = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Студент', related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='Курс')
    issued_at = models.DateTimeField('Дата видачі', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Сертифікат'
        verbose_name_plural = 'Сертифікати'
        ordering = ['-issued_at']
        unique_together = ['student', 'course']
    
    def __str__(self):
        return f'{self.student.username} - {self.course.title}'
    
    def save(self, *args, **kwargs):
        """Автоматично генерувати ID сертифіката"""
        if not self.certificate_id:
            self.certificate_id = f'CERT-{uuid.uuid4().hex[:12].upper()}'
        super().save(*args, **kwargs)