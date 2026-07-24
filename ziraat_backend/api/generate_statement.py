import os
import sys
import json
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 1. Register Turkish TrueType Fonts
def register_turkish_font():
    # Candidates for Arial on different platforms
    font_paths = [
        # Windows
        (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf"),
        # macOS
        ("/Library/Fonts/Arial.ttf", "/Library/Fonts/Arial Bold.ttf"),
        ("/Library/Fonts/Microsoft/Arial.ttf", "/Library/Fonts/Microsoft/Arial Bold.ttf"),
        ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
        # Linux
        ("/usr/share/fonts/truetype/msttcorefonts/Arial.ttf", "/usr/share/fonts/truetype/msttcorefonts/Arial_Bold.ttf"),
        ("/usr/share/fonts/truetype/msttcorefonts/arial.ttf", "/usr/share/fonts/truetype/arialbd.ttf"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]
    
    for normal_path, bold_path in font_paths:
        if os.path.exists(normal_path) and os.path.exists(bold_path):
            try:
                pdfmetrics.registerFont(TTFont('ArialTR', normal_path))
                pdfmetrics.registerFont(TTFont('ArialTR-Bold', bold_path))
                return 'ArialTR', 'ArialTR-Bold'
            except Exception as e:
                print(f"Error registering font {normal_path}: {e}")
                continue
                
    # Fallback to standard Helvetica if no TTF found
    print("Warning: No suitable TrueType font found. Falling back to Helvetica.")
    return 'Helvetica', 'Helvetica-Bold'



# Helper function to recolor white elements to Ziraat Red/Black
def recolor_logo_image(img_path):
    try:
        im = PILImage.open(img_path).convert("RGBA")
        width, height = im.size
        pixels = im.load()
        
        # emblem split point: emblem is a square on the left, so width of emblem is roughly height
        split_x = int(height * 1.1)
        
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                if a > 30:  # If not transparent
                    # If it's light colored (white/gray)
                    if r > 150 and g > 150 and b > 150:
                        if x < split_x:
                            # Recolor left side (emblem) to Ziraat Red (225, 5, 20)
                            pixels[x, y] = (225, 5, 20, a)
                        else:
                            # Recolor right side (text) to Dark Gray/Black (30, 30, 30)
                            pixels[x, y] = (30, 30, 30, a)
        im.save(img_path)
        print("Recolored logo to red/black successfully using PIL.")
    except Exception as e:
        print(f"Error recoloring logo with PIL: {e}")

# 2. Convert WebP logo to PNG using Pillow
def convert_webp_logo():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    webp_path = os.path.join(script_dir, "assets", "images", "logo.webp")
    png_path = os.path.join(script_dir, "assets", "images", "logo.png")
    
    # Try alternate path if script run from outside root
    if not os.path.exists(webp_path):
        webp_path = os.path.abspath("assets/images/logo.webp")
        png_path = os.path.abspath("assets/images/logo.png")
        
    if not os.path.exists(webp_path):
        # Fallback to absolute project dir
        webp_path = r"c:\Users\nefise\Desktop\ziraat\assets\images\logo.webp"
        png_path = r"c:\Users\nefise\Desktop\ziraat\assets\images\logo.png"

    if os.path.exists(webp_path):
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(png_path), exist_ok=True)
            im = PILImage.open(webp_path).convert("RGBA")
            im.save(png_path, "PNG")
            
            # Recolor the logo to red/black so it stands out on white background
            recolor_logo_image(png_path)
            
            return png_path
        except Exception as e:
            print(f"Error converting webp logo to png: {e}")
            return None
    else:
        print(f"Warning: Logo not found at {webp_path}")
    return None

# 3. Default Mock Data (Exactly matching the user's template image)
DEFAULT_DATA = {
    "customer": {
        "name": "MURAT YILDIRIM",
        "address": "BAĞLIK MAH. HASAN TUNA KÖY SOKAĞI NO:\n74 / 8 07740\nKUMLUCA ANTALYA"
    },
    "account": {
        "branch": "FİNİKE/ANTALYA ŞUBESİ",
        "number": "85778078-5001",
        "iban": "TR910001000040857780785001",
        "currency": "TRY",
        "period": "21.06.2026-22.07.2026"
    },
    "transactions": [
        {
            "date": "22.07.2026",
            "receipt_no": "F02539",
            "description": "MESAJ ÜCRETİ",
            "amount": "-0,37",
            "balance": "61.400,56"
        },
        {
            "date": "22.07.2026",
            "receipt_no": "F02538",
            "description": "BSMV TUTARI",
            "amount": "-0,38",
            "balance": "61.400,93"
        },
        {
            "date": "22.07.2026",
            "receipt_no": "F02537",
            "description": "KOMİSYON ÜCRETİ",
            "amount": "-7,62",
            "balance": "61.401,31"
        },
        {
            "date": "22.07.2026",
            "receipt_no": "F02530",
            "description": "Türkiye Garanti Bankası A.Ş./TR120006200114500006617164-Muhammed Emir Küçük/FAST işlemi",
            "amount": "-10.000,00",
            "balance": "61.408,93"
        },
        {
            "date": "15.07.2026",
            "receipt_no": "F02303",
            "description": "MESAJ ÜCRETİ",
            "amount": "-0,37",
            "balance": "71.408,93"
        },
        {
            "date": "15.07.2026",
            "receipt_no": "F02302",
            "description": "BSMV TUTARI",
            "amount": "-0,38",
            "balance": "71.409,30"
        },
        {
            "date": "15.07.2026",
            "receipt_no": "F02301",
            "description": "KOMİSYON ÜCRETİ",
            "amount": "-7,62",
            "balance": "71.409,68"
        },
        {
            "date": "15.07.2026",
            "receipt_no": "F02300",
            "description": "TÜRKİYE İŞ BANKASI A.Ş./TR560006400000000000000000-FATMA DEMİR/FAST işlemi",
            "amount": "-3.000,00",
            "balance": "71.417,30"
        },
        {
            "date": "10.07.2026",
            "receipt_no": "F02153",
            "description": "MESAJ ÜCRETİ",
            "amount": "-0,37",
            "balance": "74.417,30"
        },
        {
            "date": "10.07.2026",
            "receipt_no": "F02152",
            "description": "BSMV TUTARI",
            "amount": "-0,38",
            "balance": "74.417,67"
        },
        {
            "date": "10.07.2026",
            "receipt_no": "F02151",
            "description": "KOMİSYON ÜCRETİ",
            "amount": "-7,62",
            "balance": "74.418,05"
        },
        {
            "date": "10.07.2026",
            "receipt_no": "F02150",
            "description": "QNB FİNANSBANK A.Ş./TR340011100000000000000000-AYŞE YILDIZ/FAST işlemi",
            "amount": "-5.000,00",
            "balance": "74.425,67"
        },
        {
            "date": "03.07.2026",
            "receipt_no": "F02003",
            "description": "MESAJ ÜCRETİ",
            "amount": "-0,37",
            "balance": "79.425,67"
        },
        {
            "date": "03.07.2026",
            "receipt_no": "F02002",
            "description": "BSMV TUTARI",
            "amount": "-0,38",
            "balance": "79.426,04"
        },
        {
            "date": "03.07.2026",
            "receipt_no": "F02001",
            "description": "KOMİSYON ÜCRETİ",
            "amount": "-7,62",
            "balance": "79.426,42"
        },
        {
            "date": "03.07.2026",
            "receipt_no": "F02000",
            "description": "AKBANK T.A.Ş./TR120004600000000000000000-MEHMET YILMAZ/FAST işlemi",
            "amount": "-8.000,00",
            "balance": "79.434,04"
        },
        {
            "date": "25.06.2026",
            "receipt_no": "F01973",
            "description": "MESAJ ÜCRETİ",
            "amount": "-0,37",
            "balance": "87.434,04"
        },
        {
            "date": "25.06.2026",
            "receipt_no": "F01972",
            "description": "BSMV TUTARI",
            "amount": "-0,38",
            "balance": "87.434,41"
        },
        {
            "date": "25.06.2026",
            "receipt_no": "F01971",
            "description": "KOMİSYON ÜCRETİ",
            "amount": "-7,62",
            "balance": "87.434,79"
        },
        {
            "date": "25.06.2026",
            "receipt_no": "F01970",
            "description": "YAPI VE KREDİ BANKASI A.Ş./TR450006700000000000000000-AHMET CAN/FAST işlemi",
            "amount": "-9.000,00",
            "balance": "87.442,41"
        },
        {
            "date": "21.06.2026",
            "receipt_no": "F01928",
            "description": "MESAJ ÜCRETİ",
            "amount": "-0,37",
            "balance": "96.442,41"
        },
        {
            "date": "21.06.2026",
            "receipt_no": "F01927",
            "description": "BSMV TUTARI",
            "amount": "-0,38",
            "balance": "96.442,78"
        },
        {
            "date": "21.06.2026",
            "receipt_no": "F01926",
            "description": "KOMİSYON ÜCRETİ",
            "amount": "-7,62",
            "balance": "96.443,16"
        },
        {
            "date": "21.06.2026",
            "receipt_no": "F01925",
            "description": "T.İŞ BANKASI A.Ş./TR690006400000162020839001-HASAN HÜSEYİN BEYTÜZÜN/FAST işlemi",
            "amount": "-13.000,00",
            "balance": "96.450,78"
        }
    ],
    "totals": {
        "debit": "-48.050,22",
        "credit": "0,00"
    }
}




# 4. Main PDF Generation Function
def generate_pdf(data_dict, output_pdf_path="receipt.pdf"):
    # Register fonts
    font_normal, font_bold = register_turkish_font()
    
    # Page dimensions and printable width setup
    # A4: 595.27 x 841.89 points. With 36pt margins, printable width is 523.27pt.
    margin = 36
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=A4,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Paragraph Styles
    style_normal = ParagraphStyle(
        'NormalTR',
        parent=styles['Normal'],
        fontName=font_normal,
        fontSize=9.2,
        leading=12.0,
        textColor=colors.black
    )
    
    style_bold = ParagraphStyle(
        'BoldTR',
        parent=styles['Normal'],
        fontName=font_bold,
        fontSize=9.2,
        leading=12.0,
        textColor=colors.black
    )
    
    style_cell_normal = ParagraphStyle(
        'CellNormalTR',
        parent=styles['Normal'],
        fontName=font_normal,
        fontSize=8.2,
        leading=10.5,
        textColor=colors.black
    )
    
    style_cell_bold = ParagraphStyle(
        'CellBoldTR',
        parent=styles['Normal'],
        fontName=font_bold,
        fontSize=8.2,
        leading=10.5,
        textColor=colors.black
    )

    
    style_cell_normal_right = ParagraphStyle(
        'CellNormalRightTR',
        parent=style_cell_normal,
        alignment=2 # Right aligned
    )
    
    style_cell_bold_right = ParagraphStyle(
        'CellBoldRightTR',
        parent=style_cell_bold,
        alignment=2 # Right aligned
    )
    
    style_footer = ParagraphStyle(
        'FooterTR',
        parent=styles['Normal'],
        fontName=font_normal,
        fontSize=7.0,
        leading=9.5,
        textColor=colors.HexColor('#333333')
    )


    story = []
    
    # --- HEADER SECTION (Logo) ---
    logo_file = convert_webp_logo()
    if logo_file and os.path.exists(logo_file):
        try:
            with PILImage.open(logo_file) as img:
                w, h = img.size
                aspect = w / h
                # Target height of 28pt matches the visual scale of the template
                logo_height = 28
                logo_width = logo_height * aspect
                logo_flowable = RLImage(logo_file, width=logo_width, height=logo_height)
                
                # Wrap logo in a Table to left-align cleanly within margins
                logo_table = Table([[logo_flowable]], colWidths=[523])
                logo_table.setStyle(TableStyle([
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('LEFTPADDING', (0,0), (-1,-1), 0),
                    ('RIGHTPADDING', (0,0), (-1,-1), 0),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                    ('TOPPADDING', (0,0), (-1,-1), 0),
                ]))
                story.append(logo_table)
        except Exception as e:
            print(f"Error drawing logo: {e}")
            story.append(Spacer(1, 28))
    else:
        story.append(Spacer(1, 28))
        
    story.append(Spacer(1, 18))
    
    # --- CUSTOMER & ACCOUNT INFORMATION BOX ---
    customer = data_dict.get("customer", {})
    account = data_dict.get("account", {})
    
    # Format Address with HTML break tags for rendering in Paragraph
    address_raw = customer.get("address", "")
    address_html = address_raw.replace("\n", "<br/>")
    
    # Left Sub-Table (Widths: Label=38, Colon=10, Value=187 -> Sum=235)
    left_data = [
        [Paragraph("Sayın", style_bold), Paragraph(":", style_bold), Paragraph(customer.get("name", ""), style_normal)],
        [Paragraph("Adres", style_bold), Paragraph(":", style_bold), Paragraph(address_html, style_normal)]
    ]
    left_sub_table = Table(left_data, colWidths=[38, 10, 187])
    left_sub_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 4.0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4.0),
    ]))
    
    # Right Sub-Table (Widths: Label=88, Colon=10, Value=166 -> Sum=264)
    right_data = [
        [Paragraph("Şube Kodu", style_bold), Paragraph(":", style_bold), Paragraph(account.get("branch", ""), style_normal)],
        [Paragraph("Müşteri/Hesap No", style_bold), Paragraph(":", style_bold), Paragraph(account.get("number", ""), style_normal)],
        [Paragraph("IBAN", style_bold), Paragraph(":", style_bold), Paragraph(account.get("iban", ""), style_normal)],
        [Paragraph("Döviz Cinsi", style_bold), Paragraph(":", style_bold), Paragraph(account.get("currency", ""), style_normal)],
        [Paragraph("Dönem", style_bold), Paragraph(":", style_bold), Paragraph(account.get("period", ""), style_normal)]
    ]
    right_sub_table = Table(right_data, colWidths=[88, 10, 166])
    right_sub_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 4.0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4.0),
    ]))
    
    # Main parent table (Left main col=247, Right main col=276 -> Sum=523)
    # The left sub-table occupies 235pt width. With 6pt left/right padding, it takes exactly 247pt.
    # The right sub-table occupies 264pt width. With 6pt left/right padding, it takes exactly 276pt.
    main_info_data = [[left_sub_table, right_sub_table]]
    main_info_table = Table(main_info_data, colWidths=[247, 276])
    main_info_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#444444')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    
    story.append(main_info_table)
    story.append(Spacer(1, 22))
    
    # --- TRANSACTIONS HISTORY TABLE ---
    # Column Widths sum to 523pt:
    # Tarih (60), Fiş No (43), Açıklama (298), Tutar (61), Bakiye (61)
    tx_cols = [60, 43, 298, 61, 61]


    
    tx_rows = [
        # Table Header
        [
            Paragraph("Tarih", style_cell_bold),
            Paragraph("Fiş No", style_cell_bold),
            Paragraph("Açıklama", style_cell_bold),
            Paragraph("Tutar", style_cell_bold_right),
            Paragraph("Bakiye", style_cell_bold_right)
        ]
    ]
    
    # Add transaction items
    for tx in data_dict.get("transactions", []):
        tx_rows.append([
            Paragraph(tx.get("date", ""), style_cell_normal),
            Paragraph(tx.get("receipt_no", ""), style_cell_normal),
            Paragraph(tx.get("description", ""), style_cell_normal),
            Paragraph(tx.get("amount", ""), style_cell_normal_right),
            Paragraph(tx.get("balance", ""), style_cell_normal_right)
        ])
        
    # Add summary totals (Borç, Alacak)
    totals = data_dict.get("totals", {})
    tx_rows.append([
        "",
        Paragraph("Borç:", style_cell_bold),
        "",
        Paragraph(totals.get("debit", ""), style_cell_bold_right),
        ""
    ])
    tx_rows.append([
        "",
        Paragraph("Alacak:", style_cell_bold),
        "",
        Paragraph(totals.get("credit", ""), style_cell_bold_right),
        ""
    ])
    
    tx_table = Table(tx_rows, colWidths=tx_cols)
    
    # Define table styles matching the image
    tx_style = TableStyle([
        # Header background color
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E5E5E5')),
        
        # Alignments
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        
        # Table Borders
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#444444')),      # Outer border box
        ('LINEBELOW', (0,0), (-1,0), 0.5, colors.HexColor('#444444')),  # Line below header
        
        # Line below last transaction row (which is at index -3 since -2 and -1 are totals)
        ('LINEBELOW', (0, -3), (-1, -3), 0.5, colors.HexColor('#444444')),
        
        # Paddings
        ('TOPPADDING', (0,0), (-1,-1), 5.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5.5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ])
    
    tx_table.setStyle(tx_style)
    story.append(tx_table)
    story.append(Spacer(1, 45))
    
    # --- FOOTER SECTION (Legal and Contact Info) ---
    footer_text = (
        "Taraflar arasında tüm uyuşmazlıklarda, Bankanın defter kayıtları ve belgeleri, müstenitli olsun olmasın, "
        "kesin ve aksi ileri sürülemez delil niteliğindedir.<br/>"
        "Merkez: Finanskent Mahallesi Finans Caddesi No: 44A Ümraniye İstanbul<br/>"
        "Ticaret Sicil No: 475225-5<br/>"
        "www.ziraatbank.com.tr"
    )
    story.append(Paragraph(footer_text, style_footer))

    
    # Build the document
    doc.build(story)
    print(f"Successfully generated PDF: {output_pdf_path}")

if __name__ == "__main__":
    statement_data = DEFAULT_DATA
    
    targets = [
        "receipt.pdf",
        "Hesap_Hareketleri_22072026.pdf",
        os.path.join("assets", "receipt.pdf")
    ]
    
    for target in targets:
        try:
            generate_pdf(statement_data, target)
        except Exception as e:
            print(f"Error generating {target}: {e}")

