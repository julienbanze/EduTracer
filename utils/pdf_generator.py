from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def generate_pdf(student_name):
    filename = f"{student_name}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    c.drawString(100, 750, f"Bulletin scolaire - {student_name}")
    c.save()
    return filename