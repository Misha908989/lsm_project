from django import forms
from django.forms import inlineformset_factory
from .models import Lesson, LessonMedia


class LessonForm(forms.ModelForm):
    """Форма для створення та редагування уроку"""
    
    class Meta:
        model = Lesson
        fields = [
            'module',
            'title',
            'content',
            'video_url',
            'order',
            'duration_minutes',
            'is_published',
            'is_free',
        ]
        widgets = {
            'module': forms.Select(attrs={
                'class': 'form-select'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Назва уроку'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Зміст уроку...'
            }),
            'video_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.youtube.com/watch?v=...'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Порядковий номер'
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Тривалість у хвилинах'
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_free': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'module': 'Модуль',
            'title': 'Назва уроку',
            'content': 'Зміст уроку',
            'video_url': 'YouTube відео',
            'order': 'Порядок',
            'duration_minutes': 'Тривалість (хвилин)',
            'is_published': 'Опублікувати',
            'is_free': 'Безкоштовний перегляд',
        }
        help_texts = {
            'video_url': 'Вставте посилання на YouTube відео (необов\'язково)',
            'is_free': 'Дозволити перегляд уроку без запису на курс',
        }
    
    def __init__(self, *args, **kwargs):
        self.course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
        
        if self.course:
            self.fields['module'].queryset = self.course.module_set.all()


class LessonMediaForm(forms.ModelForm):
    """Форма для завантаження медіафайлів"""
    
    class Meta:
        model = LessonMedia
        fields = ['title', 'description', 'file', 'file_type']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Назва файлу'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Опис файлу (необов\'язково)'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'file_type': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'title': 'Назва файлу',
            'description': 'Опис',
            'file': 'Файл',
            'file_type': 'Тип файлу',
        }


LessonMediaFormSet = inlineformset_factory(
    Lesson,
    LessonMedia,
    form=LessonMediaForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)