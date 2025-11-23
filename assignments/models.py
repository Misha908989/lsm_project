from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from lessons.models import Lesson
from courses.models import Course
from django.utils import timezone
import uuid

# Create your models here.
class Assignment(models.Model):
    """
    Модель завдання
    """
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name='Урок'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Назва завдання'
    )
    description = models.TextField(
        verbose_name='Опис завдання'
    )
    max_score = models.PositiveIntegerField(
        default=100,
        verbose_name='Максимальний бал'
    )
    due_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Термін здачі'
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
        verbose_name = 'Завдання'
        verbose_name_plural = 'Завдання'
        ordering = ['lesson', '-created_at']
    
    def __str__(self):
        return f'{self.lesson.title} - {self.title}'
    
    def is_overdue(self):
        """Чи прострочене завдання"""
        if self.due_date:
            return timezone.now() > self.due_date
        return False


class Submission(models.Model):
    """
    Модель здачі завдання студентом
    """
    STATUS_CHOICES = [
        ('pending', 'На перевірці'),
        ('graded', 'Оцінено'),
        ('returned', 'Повернено на доопрацювання'),
    ]
    
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name='Завдання'
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name='Студент'
    )
    content = models.TextField(
        verbose_name='Текст відповіді'
    )
    file = models.FileField(
        upload_to='assignments/submissions/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name='Прикріплений файл'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата здачі'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата оновлення'
    )
    
    class Meta:
        verbose_name = 'Здача завдання'
        verbose_name_plural = 'Здачі завдань'
        unique_together = ['assignment', 'student']
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f'{self.student.username} - {self.assignment.title}'
    
    def is_late(self):
        """Чи здано із запізненням"""
        if self.assignment.due_date:
            return self.submitted_at > self.assignment.due_date
        return False


class Grade(models.Model):
    """
    Модель оцінки за завдання
    """
    submission = models.OneToOneField(
        Submission,
        on_delete=models.CASCADE,
        related_name='grade',
        verbose_name='Здача'
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='grades_given',
        verbose_name='Викладач'
    )
    score = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        verbose_name='Бал'
    )
    feedback = models.TextField(
        blank=True,
        verbose_name='Коментар викладача'
    )
    graded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата оцінювання'
    )
    
    class Meta:
        verbose_name = 'Оцінка'
        verbose_name_plural = 'Оцінки'
        ordering = ['-graded_at']
    
    def __str__(self):
        return f'{self.submission.student.username} - {self.score}/{self.submission.assignment.max_score}'
    
    def get_percentage(self):
        """Отримати оцінку у відсотках"""
        max_score = self.submission.assignment.max_score
        if max_score > 0:
            return round((self.score / max_score) * 100, 2)
        return 0
    
    def save(self, *args, **kwargs):
        """Автоматично змінювати статус submission на 'graded'"""
        super().save(*args, **kwargs)
        self.submission.status = 'graded'
        self.submission.save()


class Certificate(models.Model):
    """
    Модель сертифіката про завершення курсу
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='certificates',
        verbose_name='Студент'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='certificates',
        verbose_name='Курс'
    )
    certificate_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Номер сертифіката'
    )
    issued_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата видачі'
    )
    
    class Meta:
        verbose_name = 'Сертифікат'
        verbose_name_plural = 'Сертифікати'
        unique_together = ['student', 'course']
        ordering = ['-issued_at']
    
    def __str__(self):
        return f'Сертифікат #{self.certificate_id} - {self.student.username} - {self.course.title}'
    
    def save(self, *args, **kwargs):
        """Автоматично генерувати номер сертифіката"""
        if not self.certificate_id:
            self.certificate_id = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)