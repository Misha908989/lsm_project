from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_CENTER
from django.core.files.base import ContentFile
from io import BytesIO
from datetime import datetime


def generate_certificate_pdf(certificate):
    """
    Генерація PDF сертифіката
    
    Args:
        certificate: об'єкт Certificate
    
    Returns:
        BytesIO об'єкт з PDF
    """
    # Створити BytesIO об'єкт
    buffer = BytesIO()
    
    # Створити canvas в альбомній орієнтації
    page_width, page_height = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    
    # Кольори
    gold = colors.Color(0.85, 0.65, 0.13)
    dark_blue = colors.Color(0.12, 0.24, 0.44)
    
    # Рамка
    c.setStrokeColor(gold)
    c.setLineWidth(3)
    c.rect(30, 30, page_width - 60, page_height - 60, stroke=1, fill=0)
    
    c.setLineWidth(1)
    c.rect(40, 40, page_width - 80, page_height - 80, stroke=1, fill=0)
    
    # Декоративні елементи в кутах
    c.setFillColor(gold)
    for x, y in [(50, page_height - 50), (page_width - 50, page_height - 50), 
                  (50, 50), (page_width - 50, 50)]:
        c.circle(x, y, 10, fill=1, stroke=0)
    
    # Заголовок "CERTIFICATE"
    c.setFillColor(dark_blue)
    c.setFont("Helvetica-Bold", 48)
    text = "CERTIFICATE"
    text_width = c.stringWidth(text, "Helvetica-Bold", 48)
    c.drawString((page_width - text_width) / 2, page_height - 120, text)
    
    # Підзаголовок "OF COMPLETION"
    c.setFont("Helvetica", 24)
    text = "OF COMPLETION"
    text_width = c.stringWidth(text, "Helvetica", 24)
    c.drawString((page_width - text_width) / 2, page_height - 155, text)
    
    # Лінія
    c.setStrokeColor(gold)
    c.setLineWidth(2)
    c.line(150, page_height - 175, page_width - 150, page_height - 175)
    
    # "This is to certify that"
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 16)
    text = "This is to certify that"
    text_width = c.stringWidth(text, "Helvetica", 16)
    c.drawString((page_width - text_width) / 2, page_height - 220, text)
    
    # Ім'я студента
    c.setFillColor(dark_blue)
    c.setFont("Helvetica-Bold", 36)
    student_name = f"{certificate.student.first_name} {certificate.student.last_name}".strip()
    if not student_name:
        student_name = certificate.student.username
    text_width = c.stringWidth(student_name, "Helvetica-Bold", 36)
    c.drawString((page_width - text_width) / 2, page_height - 270, student_name)
    
    # Лінія під іменем
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    name_line_y = page_height - 280
    c.line(150, name_line_y, page_width - 150, name_line_y)
    
    # "has successfully completed"
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 16)
    text = "has successfully completed"
    text_width = c.stringWidth(text, "Helvetica", 16)
    c.drawString((page_width - text_width) / 2, page_height - 320, text)
    
    # Назва курсу
    c.setFillColor(dark_blue)
    c.setFont("Helvetica-Bold", 28)
    course_title = certificate.course.title
    text_width = c.stringWidth(course_title, "Helvetica-Bold", 28)
    c.drawString((page_width - text_width) / 2, page_height - 360, course_title)
    
    # Лінія під курсом
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    course_line_y = page_height - 370
    c.line(150, course_line_y, page_width - 150, course_line_y)
    
    # Оцінка
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 14)
    grade_text = f"Final Grade: {certificate.final_grade}% ({certificate.get_letter_grade()})"
    text_width = c.stringWidth(grade_text, "Helvetica", 14)
    c.drawString((page_width - text_width) / 2, page_height - 410, grade_text)
    
    # Дата та ID
    c.setFont("Helvetica", 12)
    
    # Дата зліва
    date_text = f"Date: {certificate.issued_at.strftime('%B %d, %Y')}"
    c.drawString(100, 120, date_text)
    
    # ID справа
    id_text = f"Certificate ID: {certificate.certificate_id}"
    id_width = c.stringWidth(id_text, "Helvetica", 12)
    c.drawString(page_width - 100 - id_width, 120, id_text)
    
    # Підпис викладача (по центру)
    c.setFont("Helvetica-Bold", 12)
    instructor_name = f"{certificate.course.instructor.first_name} {certificate.course.instructor.last_name}".strip()
    if not instructor_name:
        instructor_name = certificate.course.instructor.username
    
    # Лінія для підпису
    signature_y = 150
    signature_x_center = page_width / 2
    c.line(signature_x_center - 100, signature_y, signature_x_center + 100, signature_y)
    
    # Ім'я викладача
    text_width = c.stringWidth(instructor_name, "Helvetica-Bold", 12)
    c.drawString(signature_x_center - text_width / 2, signature_y - 20, instructor_name)
    
    # Посада
    c.setFont("Helvetica", 10)
    title_text = "Course Instructor"
    text_width = c.stringWidth(title_text, "Helvetica", 10)
    c.drawString(signature_x_center - text_width / 2, signature_y - 35, title_text)
    
    # Завершити PDF
    c.showPage()
    c.save()
    
    # Повернути buffer на початок
    buffer.seek(0)
    return buffer


def issue_certificate(student, course):
    """
    Видати сертифікат студенту за курс
    
    Args:
        student: User об'єкт студента
        course: Course об'єкт курсу
    
    Returns:
        Certificate об'єкт або None
    """
    from .models import Certificate, Grade
    from courses.models import Enrollment
    from lessons.models import Lesson
    
    # Перевірити чи студент записаний на курс
    try:
        enrollment = Enrollment.objects.get(student=student, course=course, is_active=True)
    except Enrollment.DoesNotExist:
        return None
    
    # Перевірити чи курс завершено (прогрес 100%)
    if enrollment.progress < 100:
        return None
    
    # Розрахувати підсумкову оцінку
    lessons = Lesson.objects.filter(module__course=course, is_published=True)
    total_score = 0
    total_max = 0
    
    for lesson in lessons:
        for assignment in lesson.assignments.all():
            try:
                submission = assignment.submissions.get(student=student)
                if hasattr(submission, 'grade'):
                    total_score += submission.grade.score
                    total_max += assignment.max_score
            except:
                pass
    
    # Якщо немає завдань, дати 100%
    if total_max == 0:
        final_grade = 100.0
    else:
        final_grade = round((total_score / total_max) * 100, 2)
    
    # Перевірити чи вже є сертифікат
    certificate, created = Certificate.objects.get_or_create(
        student=student,
        course=course,
        defaults={'final_grade': final_grade}
    )
    
    if not created:
        # Оновити оцінку якщо сертифікат вже існує
        certificate.final_grade = final_grade
        certificate.save()
    
    # Згенерувати PDF
    pdf_buffer = generate_certificate_pdf(certificate)
    
    # Зберегти PDF файл
    filename = f'certificate_{certificate.certificate_id}.pdf'
    certificate.pdf_file.save(filename, ContentFile(pdf_buffer.read()), save=True)
    
    return certificate


def calculate_course_grade(student, course):
    """
    Розрахувати підсумкову оцінку студента за курс
    
    Args:
        student: User об'єкт
        course: Course об'єкт
    
    Returns:
        float: оцінка у відсотках (0-100)
    """
    from .models import Grade
    from lessons.models import Lesson
    
    lessons = Lesson.objects.filter(module__course=course, is_published=True)
    total_score = 0
    total_max = 0
    
    for lesson in lessons:
        for assignment in lesson.assignments.all():
            try:
                submission = assignment.submissions.get(student=student)
                if hasattr(submission, 'grade'):
                    total_score += submission.grade.score
                    total_max += assignment.max_score
            except:
                pass
    
    if total_max == 0:
        return 0.0
    
    return round((total_score / total_max) * 100, 2)