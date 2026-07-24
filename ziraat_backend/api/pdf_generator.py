from io import BytesIO
import os
from xhtml2pdf import pisa
from django.template.loader import render_to_string
from django.conf import settings

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register font for Turkish character support before generating PDFs
try:
    pdfmetrics.registerFont(TTFont('CustomArial', 'C:\\Windows\\Fonts\\arial.ttf'))
except Exception as e:
    print("Warning: Could not load Arial font", e)

def generate_pdf(data_dict):
    """
    Renders an HTML template into a PDF using xhtml2pdf.
    """
    # Load HTML template from the original file path (or we can move it to templates)
    # We will read it directly since it's an ad-hoc template.
    template_path = os.path.join(settings.BASE_DIR, '..', '..', 'e-dekont (2).html')
    template_path = os.path.abspath(template_path)
    
    with open(template_path, 'r', encoding='utf-8') as f:
        html_string = f.read()

    # Simple string replacement for tags (since it's not a proper Django template format)
    for key, value in data_dict.items():
        html_string = html_string.replace(f'{{{{{key}}}}}', str(value))
        
    buffer = BytesIO()
    # Create PDF
    pisa_status = pisa.CreatePDF(
        html_string, dest=buffer, encoding='utf-8'
    )
    
    if pisa_status.err:
        return b''
    
    buffer.seek(0)
    return buffer.getvalue()
