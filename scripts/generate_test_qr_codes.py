#!/usr/bin/env python3
"""Generate test QR codes PDF for barcode scanner testing."""

import base64
import tempfile
from io import BytesIO
from pathlib import Path
from typing import List, Dict, Any

import jinja2
import qrcode
from weasyprint import HTML


class QRTestData:
    """Test data for QR code generation."""
    
    def __init__(self, content: str, description: str, page_title: str):
        self.content = content
        self.description = description
        self.page_title = page_title


def generate_qr_code_base64(content: str) -> str:
    """Generate a QR code and return as base64 data URL."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=15,  # Large QR code
        border=4,
    )
    qr.add_data(content)
    qr.make(fit=True)

    # Create QR code image
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffered = BytesIO()
    qr_img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"


def create_test_data() -> List[QRTestData]:
    """Create test data for QR codes."""
    return [
        # Potting lot IDs (pages 1-4)
        QRTestData("20012", "Potting Lot ID: 20012", "Potting Lot 20012"),
        QRTestData("1980", "Potting Lot ID: 1980", "Potting Lot 1980"), 
        QRTestData("2009", "Potting Lot ID: 2009", "Potting Lot 2009"),
        QRTestData("2010", "Potting Lot ID: 2010", "Potting Lot 2010"),
        
        # URLs (pages 5-6)
        QRTestData("https://nicegui.io/", "URL: https://nicegui.io/", "NiceGUI Website"),
        QRTestData("https://vine.serraict.com/", "URL: https://vine.serraict.com/", "Vine Website"),
        
        # Email (page 7)
        QRTestData("marijn@serraict.com", "Email: marijn@serraict.com", "Email Address"),
        
        # Plain text (page 8)
        QRTestData("hello world!", "Plain text: hello world!", "Plain Text"),
    ]


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>QR Code Test PDF</title>
    <style>
        @page {
            size: A4;
            margin: 20mm;
        }
        
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
        }
        
        .page {
            page-break-after: always;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            text-align: center;
        }
        
        .page:last-child {
            page-break-after: auto;
        }
        
        .page-title {
            font-size: 24pt;
            font-weight: bold;
            margin-bottom: 30px;
            color: #333;
        }
        
        .qr-code {
            margin: 30px 0;
        }
        
        .qr-code img {
            width: 300px;
            height: 300px;
            border: 2px solid #ddd;
        }
        
        .content-text {
            font-size: 18pt;
            margin-top: 30px;
            padding: 20px;
            background-color: #f5f5f5;
            border-radius: 8px;
            border: 1px solid #ddd;
            max-width: 80%;
            word-break: break-all;
        }
        
        .description {
            font-size: 14pt;
            color: #666;
            margin-bottom: 10px;
        }
        
        .footer {
            position: fixed;
            bottom: 10mm;
            right: 10mm;
            font-size: 10pt;
            color: #999;
        }
    </style>
</head>
<body>
    {% for test_item in test_data %}
    <div class="page">
        <div class="page-title">{{ test_item.page_title }}</div>
        
        <div class="description">{{ test_item.description }}</div>
        
        <div class="qr-code">
            <img src="{{ test_item.qr_code_base64 }}" alt="QR Code" />
        </div>
        
        <div class="content-text">
            {{ test_item.content }}
        </div>
    </div>
    {% endfor %}
    
    <div class="footer">
        Test QR Codes - Generated for barcode scanner testing
    </div>
</body>
</html>
"""


def generate_test_pdf(output_path: str = "test_qr_codes.pdf") -> str:
    """Generate PDF with test QR codes."""
    # Create test data
    test_data = create_test_data()
    
    # Generate QR codes for each test item
    for item in test_data:
        item.qr_code_base64 = generate_qr_code_base64(item.content)
    
    # Render HTML template
    template = jinja2.Template(HTML_TEMPLATE)
    html_content = template.render(test_data=test_data)
    
    # Generate PDF
    html_obj = HTML(string=html_content)
    html_obj.write_pdf(output_path)
    
    return output_path


if __name__ == "__main__":
    import sys
    
    # Get output path from command line or use default
    output_path = sys.argv[1] if len(sys.argv) > 1 else "test_qr_codes.pdf"
    
    print(f"Generating test QR codes PDF: {output_path}")
    
    try:
        result_path = generate_test_pdf(output_path)
        print(f"✅ Successfully generated: {result_path}")
        
        # Print summary of what was generated
        test_data = create_test_data()
        print("\n📄 Generated QR codes:")
        for i, item in enumerate(test_data, 1):
            print(f"  Page {i}: {item.description}")
            
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        sys.exit(1)