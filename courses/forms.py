from django import forms
from django.forms import inlineformset_factory
from .models import Course, Module
from django.contrib.auth.models import User


class CourseForm(forms.ModelForm):
    """Форма для створення та редагування курсу"""
    
    class Meta:
        model = Course
        fields = [
            'title', 
            'description', 
            'thumbnail', 
            'level', 
            'duration', 
            'price', 
            'max_students',
            'is_published',
            'instructor'  # Буде доступне тільки для адмінів
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введіть назву курсу'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Опишіть курс детально...'
            }),
            'thumbnail': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'level': forms.Select(attrs={
                'class': 'form-select'
            }),
            'duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Тривалість у годинах'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0 = безкоштовно'
            }),
            'max_students': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Залиште порожнім для необмеженої кількості'
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'instructor': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'title': 'Назва курсу',
            'description': 'Опис курсу',
            'thumbnail': 'Обкладинка',
            'level': 'Рівень складності',
            'duration': 'Тривалість (годин)',
            'price': 'Ціна (грн)',
            'max_students': 'Максимум студентів',
            'is_published': 'Опублікувати',
            'instructor': 'Викладач',
        }
    
    def __init__(self, *args, **kwargs):
        # Отримуємо поточного користувача
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Якщо користувач - викладач (не адмін), приховуємо поле instructor
        if self.user and self.user.profile.role == 'teacher':
            self.fields['instructor'].widget = forms.HiddenInput()
            self.fields['instructor'].required = False
        
        # Фільтруємо список викладачів (тільки користувачі з роллю teacher)
        if 'instructor' in self.fields:
            self.fields['instructor'].queryset = User.objects.filter(
                profile__role__in=['teacher', 'admin']
            )


class ModuleForm(forms.ModelForm):
    """Форма для модуля курсу"""
    
    class Meta:
        model = Module
        fields = ['title', 'description', 'order']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Назва модуля'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Опис модуля'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Порядковий номер'
            }),
        }
        labels = {
            'title': 'Назва модуля',
            'description': 'Опис',
            'order': 'Порядок',
        }


# Formset для inline редагування модулів
ModuleFormSet = inlineformset_factory(
    Course,
    Module,
    form=ModuleForm,
    extra=1,  # Кількість порожніх форм
    can_delete=True,  # Можливість видалення
    min_num=0,  # Мінімум модулів
    validate_min=False,
)