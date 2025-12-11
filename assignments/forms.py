from django import forms
from .models import Assignment, Submission, Grade


class AssignmentForm(forms.ModelForm):
    """Форма для створення та редагування завдання"""
    
    class Meta:
        model = Assignment
        fields = [
            'lesson',
            'title',
            'description',
            'max_score',
            'due_date',
            'allow_late_submission',
            'submission_type',
        ]
        widgets = {
            'lesson': forms.Select(attrs={
                'class': 'form-select'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Назва завдання'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Детальний опис завдання, вимоги, критерії оцінювання...'
            }),
            'max_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '100'
            }),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'allow_late_submission': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'submission_type': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'lesson': 'Урок',
            'title': 'Назва завдання',
            'description': 'Опис завдання',
            'max_score': 'Максимальний бал',
            'due_date': 'Дедлайн',
            'allow_late_submission': 'Дозволити здачу після дедлайну',
            'submission_type': 'Тип здачі',
        }
    
    def __init__(self, *args, **kwargs):
        # Отримуємо курс для фільтрації уроків
        self.course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
        
        # Якщо курс передано, фільтруємо уроки
        if self.course:
            from lessons.models import Lesson
            self.fields['lesson'].queryset = Lesson.objects.filter(
                module__course=self.course
            ).select_related('module')


class SubmissionForm(forms.ModelForm):
    """Форма для здачі завдання студентом"""
    
    class Meta:
        model = Submission
        fields = ['content', 'file']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Введіть вашу відповідь...'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'content': 'Текст відповіді',
            'file': 'Файл (необов\'язково)',
        }
    
    def __init__(self, *args, **kwargs):
        self.assignment = kwargs.pop('assignment', None)
        super().__init__(*args, **kwargs)
        
        # Налаштувати обов'язковість полів залежно від типу здачі
        if self.assignment:
            submission_type = self.assignment.submission_type
            
            if submission_type == 'text':
                self.fields['content'].required = True
                self.fields['file'].required = False
                self.fields['file'].widget = forms.HiddenInput()
            elif submission_type == 'file':
                self.fields['content'].required = False
                self.fields['content'].widget = forms.HiddenInput()
                self.fields['file'].required = True
            else:  # both
                self.fields['content'].required = False
                self.fields['file'].required = False


class GradeForm(forms.ModelForm):
    """Форма для оцінювання завдання викладачем"""
    
    class Meta:
        model = Grade
        fields = ['score', 'feedback']
        widgets = {
            'score': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введіть бал'
            }),
            'feedback': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Відгук для студента (необов\'язково)...'
            }),
        }
        labels = {
            'score': 'Бал',
            'feedback': 'Відгук',
        }
    
    def __init__(self, *args, **kwargs):
        self.assignment = kwargs.pop('assignment', None)
        super().__init__(*args, **kwargs)
        
        # Встановити максимальний бал як підказку
        if self.assignment:
            self.fields['score'].widget.attrs['max'] = self.assignment.max_score
            self.fields['score'].help_text = f'Максимальний бал: {self.assignment.max_score}'
    
    def clean_score(self):
        """Валідація балу"""
        score = self.cleaned_data.get('score')
        
        if self.assignment and score > self.assignment.max_score:
            raise forms.ValidationError(
                f'Бал не може перевищувати максимальний ({self.assignment.max_score})'
            )
        
        if score < 0:
            raise forms.ValidationError('Бал не може бути від\'ємним')
        
        return score