from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator


class Course(models.Model):
    """Модель курсу"""
    
    LEVEL_CHOICES = [
        ('beginner', 'Початковий'),
        ('intermediate', 'Середній'),
        ('advanced', 'Просунутий'),
    ]
    
    title = models.CharField('Назва курсу', max_length=200)
    slug = models.SlugField('URL', max_length=200, unique=True, blank=True)
    description = models.TextField('Опис курсу')
    thumbnail = models.ImageField('Обкладинка', upload_to='courses/thumbnails/', blank=True, null=True)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Викладач', related_name='courses')
    level = models.CharField('Рівень складності', max_length=20, choices=LEVEL_CHOICES, default='beginner')
    duration = models.PositiveIntegerField('Тривалість (годин)', default=0, help_text='Загальна тривалість курсу в годинах')
    price = models.DecimalField('Ціна', max_digits=10, decimal_places=2, default=0, help_text='0 = безкоштовно')
    max_students = models.PositiveIntegerField('Максимум студентів', blank=True, null=True, help_text='Залиште порожнім для необмеженої кількості')
    is_published = models.BooleanField('Опубліковано', default=False)
    created_at = models.DateTimeField('Дата створення', auto_now_add=True)
    updated_at = models.DateTimeField('Дата оновлення', auto_now=True)
    
    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курси'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            # Перевірка унікальності slug
            original_slug = self.slug
            counter = 1
            while Course.objects.filter(slug=self.slug).exists():
                self.slug = f'{original_slug}-{counter}'
                counter += 1
        super().save(*args, **kwargs)
    
    def get_enrolled_count(self):
        """Кількість записаних студентів"""
        return self.enrollment_set.filter(is_active=True).count()
    
    def get_modules_count(self):
        """Кількість модулів"""
        return self.module_set.count()


class Module(models.Model):
    """Модель модуля курсу"""
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='Курс')
    title = models.CharField('Назва модуля', max_length=200)
    description = models.TextField('Опис модуля', blank=True)
    order = models.PositiveIntegerField('Порядок', default=1)
    created_at = models.DateTimeField('Дата створення', auto_now_add=True)
    updated_at = models.DateTimeField('Дата оновлення', auto_now=True)
    
    class Meta:
        verbose_name = 'Модуль'
        verbose_name_plural = 'Модулі'
        ordering = ['order']
    
    def __str__(self):
        return f'{self.course.title} - {self.title}'


class Enrollment(models.Model):
    """Модель запису студента на курс"""
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Студент')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='Курс')
    enrolled_at = models.DateTimeField('Дата запису', auto_now_add=True)
    is_active = models.BooleanField('Активний', default=True)
    progress = models.PositiveIntegerField('Прогрес (%)', default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    class Meta:
        verbose_name = 'Запис на курс'
        verbose_name_plural = 'Записи на курси'
        ordering = ['-enrolled_at']
        unique_together = ['student', 'course']
    
    def __str__(self):
        return f'{self.student.username} - {self.course.title}'
    
    def update_progress(self):
        """Оновлення прогресу студента"""
        # Буде реалізовано пізніше при додаванні уроків
        pass


class Announcement(models.Model):
    """Модель оголошення"""
    
    TYPE_CHOICES = [
        ('general', 'Загальне'),
        ('important', 'Важливе'),
        ('update', 'Оновлення'),
    ]
    
    title = models.CharField('Заголовок', max_length=200)
    content = models.TextField('Зміст')
    type = models.CharField('Тип', max_length=20, choices=TYPE_CHOICES, default='general')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='Курс', blank=True, null=True, help_text='Залиште порожнім для загального оголошення')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Автор', null=True, blank=True) 
    is_active = models.BooleanField('Активне', default=True)
    is_pinned = models.BooleanField('Закріплене', default=False)
    created_at = models.DateTimeField('Дата створення', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Оголошення'
        verbose_name_plural = 'Оголошення'
        ordering = ['-is_pinned', '-created_at']
    
    def __str__(self):
        return self.title