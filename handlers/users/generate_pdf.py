import os
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
from textwrap import wrap
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

async def generate_pdf_with_qr( link, full_name, level, speciality_name, semestr_name):
    input_pdf_path= "files/shablon.pdf"
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(link)
    qr.make(fit=True)

    qr_img = qr.make_image(fill='black', back_color='white')
    qr_io = BytesIO()
    qr_img.save(qr_io, format="PNG")
    qr_io.seek(0)

    # Create a new PDF with modifications
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    x, y, width, height = 350, 0, 400, 50  # Position and size for the rectangle
    can.setFillColorRGB(1, 1, 1)  # White color for the rectangle
    can.rect(x, y, width, height, stroke=0, fill=1)


    qr_code_x, qr_code_y = 350, 10  # Position of the QR code
    qr_code_size = 3 * cm  # Size of the QR code (3cm x 3cm)
    qr_image = ImageReader(qr_io)
    can.drawImage(qr_image, qr_code_x, qr_code_y, qr_code_size, qr_code_size)

    # Cover the marked text area with a white rectangle
    x, y, width, height = 50, 520, 500, 155  # Position and size for the rectangle
    can.setFillColorRGB(1, 1, 1)  # White color for the rectangle
    can.rect(x, y, width, height, stroke=0, fill=1)

    # Define the new text and handle text wrapping
    new_text = (
        f"Buxoro Psixologiya va xorijiy tillar instituti sirtqi ta`lim shakli “{speciality_name}” yo’nalishining {level} talabasi {full_name.title()} {semestr_name} o`quv mashg`ulotlari va sessiya sinovlarida ishtirok etish uchun 2024-yil «14»-oktabrdan 2024-yil «16»-noyabrgacha O`zbekiston Respublikasi Vazirlar Mahkamasining 2017-yil 21-noyabrdagi 930-sonli qarori 1-ilovasining 6-bob 38-bandiga asosan talabaga o`rtacha oylik maoshi saqlangan qo`shimcha ta`til berilsin."
    )

    max_line_width = width - 20  # Leave some margin within the rectangle
    can.setFont("Helvetica", 14)
    can.setFillColor(colors.black)

    wrapped_text = wrap(new_text, width=75)  # Adjust this if necessary
    text_y = y + height - 20  # Starting Y position
    line_height = 20  # Line spacing

    for line in wrapped_text:
        can.drawString(x + 14, text_y, line)  # Adjust X for left margin
        text_y -= line_height  # Move to next line

    can.save()
    packet.seek(0)

    # Read the input PDF and merge the new content
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()
    page = reader.pages[0]

    new_pdf = PdfReader(packet)
    new_page = new_pdf.pages[0]

    page.merge_page(new_page)
    writer.add_page(page)

    # Store the result in a BytesIO object to return
    output_pdf_io = BytesIO()
    writer.write(output_pdf_io)
    output_pdf_io.seek(0)

    return output_pdf_io
