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
        """Автоматична генерація slug при збереженні"""
        if not self.slug:
            # Згенерувати базовий slug з title
            base_slug = slugify(self.title)
            
            # Якщо title не латиницею (кирилиця), використати транслітерацію або ID
            if not base_slug:
                # Імпорт для транслітерації (опціонально)
                try:
                    from transliterate import translit
                    base_slug = slugify(translit(self.title, reversed=True))
                except:
                    # Якщо транслітерація не доступна, використати course-id
                    # Спочатку зберігаємо щоб отримати ID
                    if not self.pk:
                        super().save(*args, **kwargs)
                    base_slug = f"course-{self.pk}"
            
            # Перевірити унікальність slug
            slug = base_slug
            counter = 1
            while Course.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            
            self.slug = slug
        
        super().save(*args, **kwargs)
    
    def get_enrolled_count(self):
        """Кількість записаних студентів"""
        return self.enrollment_set.filter(is_active=True).count()
    
    def get_modules_count(self):
        """Кількість модулів"""
        return self.module_set.count()
    
    def get_lessons_count(self):
        """Загальна кількість уроків у курсі"""
        from lessons.models import Lesson
        return Lesson.objects.filter(module__course=self).count()
    
    def get_duration_display(self):
        """Відображення тривалості"""
        if self.duration < 1:
            return "Менше години"
        elif self.duration == 1:
            return "1 година"
        elif self.duration < 5:
            return f"{self.duration} години"
        else:
            return f"{self.duration} годин"


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
        unique_together = ['course', 'order']
    
    def __str__(self):
        return f'{self.course.title} - {self.title}'
    
    def get_lessons_count(self):
        """Кількість уроків у модулі"""
        return self.lesson_set.count()
    
    def get_total_duration(self):
        """Загальна тривалість уроків модуля в хвилинах"""
        from lessons.models import Lesson
        total = Lesson.objects.filter(module=self).aggregate(
            total=models.Sum('duration_minutes')
        )['total']
        return total or 0


class Enrollment(models.Model):
    """Модель запису студента на курс"""
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Студент')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='Курс')
    enrolled_at = models.DateTimeField('Дата запису', auto_now_add=True)
    is_active = models.BooleanField('Активний', default=True)
    progress = models.PositiveIntegerField('Прогрес (%)', default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    completed_at = models.DateTimeField('Дата завершення', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Запис на курс'
        verbose_name_plural = 'Записи на курси'
        ordering = ['-enrolled_at']
        unique_together = ['student', 'course']
    
    def __str__(self):
        return f'{self.student.username} - {self.course.title}'
    
    def update_progress(self):
        """Оновлення прогресу студента на основі завершених уроків"""
        from lessons.models import Lesson, LessonProgress
        
        # Отримати всі уроки курсу
        total_lessons = Lesson.objects.filter(
            module__course=self.course,
            is_published=True
        ).count()
        
        if total_lessons == 0:
            self.progress = 0
        else:
            # Отримати кількість завершених уроків
            completed_lessons = LessonProgress.objects.filter(
                lesson__module__course=self.course,
                student=self.student,
                is_completed=True
            ).count()
            
            # Розрахувати прогрес
            self.progress = int((completed_lessons / total_lessons) * 100)
        
        # Якщо прогрес 100%, встановити дату завершення
        if self.progress >= 100 and not self.completed_at:
            from django.utils import timezone
            self.completed_at = timezone.now()
        
        self.save()
        return self.progress


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
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        verbose_name='Курс', 
        blank=True, 
        null=True, 
        help_text='Залиште порожнім для загального оголошення'
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name='Автор', 
        null=True, 
        blank=True
    )
    is_active = models.BooleanField('Активне', default=True)
    is_pinned = models.BooleanField('Закріплене', default=False)
    created_at = models.DateTimeField('Дата створення', auto_now_add=True)
    updated_at = models.DateTimeField('Дата оновлення', auto_now=True)
    
    class Meta:
        verbose_name = 'Оголошення'
        verbose_name_plural = 'Оголошення'
        ordering = ['-is_pinned', '-created_at']
    
    def __str__(self):
        return self.title
    
    def get_type_badge_class(self):
        """Клас Bootstrap badge залежно від типу"""
        badges = {
            'general': 'bg-secondary',
            'important': 'bg-danger',
            'update': 'bg-info',
        }
        return badges.get(self.type, 'bg-secondary')