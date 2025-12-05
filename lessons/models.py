from django.db import models
from courses.models import Module
from django.core.validators import FileExtensionValidator

# Create your models here.

class Lesson(models.Model):
    """Модель уроку"""
    
    module = models.ForeignKey(Module, on_delete=models.CASCADE, verbose_name='Модуль')
    title = models.CharField('Назва уроку', max_length=200)
    content = models.TextField('Зміст уроку', help_text='Текстовий опис уроку')
    video_url = models.URLField('YouTube відео', blank=True, null=True, help_text='Посилання на YouTube відео')
    order = models.PositiveIntegerField('Порядок', default=1)
    duration_minutes = models.PositiveIntegerField('Тривалість (хвилин)', default=0, blank=True)
    is_published = models.BooleanField('Опубліковано', default=True)
    is_free = models.BooleanField('Безкоштовний перегляд', default=False, help_text='Дозволити перегляд без запису на курс')
    created_at = models.DateTimeField('Дата створення', auto_now_add=True)
    updated_at = models.DateTimeField('Дата оновлення', auto_now=True)
    
    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        ordering = ['order']
    
    def __str__(self):
        return f'{self.module.course.title} - {self.module.title} - {self.title}'
    
    def get_youtube_embed_url(self):
        """Отримати URL для вбудовування YouTube відео"""
        if not self.video_url:
            return None
        
        # Перетворити звичайний URL YouTube на embed URL
        # https://www.youtube.com/watch?v=VIDEO_ID -> https://www.youtube.com/embed/VIDEO_ID
        # https://youtu.be/VIDEO_ID -> https://www.youtube.com/embed/VIDEO_ID
        
        if 'youtube.com/watch?v=' in self.video_url:
            video_id = self.video_url.split('watch?v=')[1].split('&')[0]
            return f'https://www.youtube.com/embed/{video_id}'
        elif 'youtu.be/' in self.video_url:
            video_id = self.video_url.split('youtu.be/')[1].split('?')[0]
            return f'https://www.youtube.com/embed/{video_id}'
        
        return self.video_url
    
    def get_next_lesson(self):
        """Отримати наступний урок"""
        return Lesson.objects.filter(
            module=self.module,
            order__gt=self.order
        ).order_by('order').first()
    
    def get_previous_lesson(self):
        """Отримати попередній урок"""
        return Lesson.objects.filter(
            module=self.module,
            order__lt=self.order
        ).order_by('-order').first()


class LessonMedia(models.Model):
    """Модель медіафайлів уроку"""
    
    FILE_TYPE_CHOICES = [
        ('image', 'Зображення'),
        ('document', 'Документ'),
        ('video', 'Відео'),
        ('other', 'Інше'),
    ]
    
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, verbose_name='Урок', related_name='media_files')
    title = models.CharField('Назва файлу', max_length=200)
    description = models.TextField('Опис', blank=True)
    file = models.FileField(
        'Файл',
        upload_to='lessons/media/%Y/%m/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'doc', 'docx', 'ppt', 'pptx', 'jpg', 'jpeg', 'png', 'gif', 'mp4', 'avi', 'zip']
            )
        ]
    )
    file_type = models.CharField('Тип файлу', max_length=20, choices=FILE_TYPE_CHOICES, default='document')
    file_size = models.PositiveIntegerField('Розмір файлу (bytes)', default=0, blank=True)
    uploaded_at = models.DateTimeField('Дата завантаження', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Медіафайл уроку'
        verbose_name_plural = 'Медіафайли уроків'
        ordering = ['uploaded_at']
    
    def __str__(self):
        return f'{self.lesson.title} - {self.title}'
    
    def save(self, *args, **kwargs):
        """Автоматично визначити розмір файлу"""
        if self.file and not self.file_size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    def get_file_size_display(self):
        """Відобразити розмір файлу в зручному форматі"""
        size = self.file_size
        if size < 1024:
            return f'{size} B'
        elif size < 1024 * 1024:
            return f'{size / 1024:.2f} KB'
        elif size < 1024 * 1024 * 1024:
            return f'{size / (1024 * 1024):.2f} MB'
        else:
            return f'{size / (1024 * 1024 * 1024):.2f} GB'
    
    def get_file_icon(self):
        """Отримати іконку для типу файлу"""
        extension = self.file.name.split('.')[-1].lower()
        
        icons = {
            'pdf': 'fa-file-pdf text-danger',
            'doc': 'fa-file-word text-primary',
            'docx': 'fa-file-word text-primary',
            'ppt': 'fa-file-powerpoint text-warning',
            'pptx': 'fa-file-powerpoint text-warning',
            'jpg': 'fa-file-image text-info',
            'jpeg': 'fa-file-image text-info',
            'png': 'fa-file-image text-info',
            'gif': 'fa-file-image text-info',
            'mp4': 'fa-file-video text-success',
            'avi': 'fa-file-video text-success',
            'zip': 'fa-file-archive text-secondary',
        }
        
        return icons.get(extension, 'fa-file text-muted')


class LessonProgress(models.Model):
    """Модель прогресу проходження уроку студентом"""
    
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, verbose_name='Урок')
    student = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name='Студент')
    is_completed = models.BooleanField('Завершено', default=False)
    completed_at = models.DateTimeField('Дата завершення', null=True, blank=True)
    time_spent = models.PositiveIntegerField('Час перегляду (секунд)', default=0)
    
    class Meta:
        verbose_name = 'Прогрес уроку'
        verbose_name_plural = 'Прогрес уроків'
        unique_together = ['lesson', 'student']
    
    def __str__(self):
        return f'{self.student.username} - {self.lesson.title}'