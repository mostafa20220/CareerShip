import io
import os

from reportlab.pdfgen import canvas

from reportlab.lib.pagesizes import A4  , landscape
from reportlab.lib.pagesizes import letter
import reportlab.rl_config
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader, PdfWriter , Transformation
from django.conf import settings
from utils.logging_utils import get_logger

logger = get_logger(__name__)


class CertificateGenerator:

    def __init__(self, template_path):
        self.orange = (254 / 255, 200 / 255, 70 / 255)
        self.black = (1 / 255, 1 / 255, 1 / 255)
        self.page_width, self.page_height = landscape(A4)  # Landscape A4
        self.template_path = template_path
        self.buffer = io.BytesIO()
        logger.info(f"CertificateGenerator initialized with template: {template_path}")

        # Register fonts
        # self._register_fonts()

    def _register_fonts(self):
        """Register custom fonts used in the certificate."""
        # pdfmetrics.registerFont(TTFont('Vera', 'Vera.ttf'))
        # pdfmetrics.registerFont(TTFont('VeraBI', 'VeraBI.ttf'))
        # pdfmetrics.registerFont(TTFont('VeraBd', 'VeraBd.ttf'))
        # pdfmetrics.registerFont(TTFont('TTBlueScreen', 'VeraBd.ttf'))

    def _draw_text(self, c, text, x, y, font, size, color):
        """Helper method to draw centered or regular text on the canvas."""
        c.setFillColorRGB(*color)
        c.setFont(font, size)
        c.drawString(x, y, text)

    def _draw_centered_text(self, c, text, y, font, size, color):
        """Helper method to draw centered text horizontally on the canvas."""
        text_width = c.stringWidth(text, font, size)
        x = (self.page_width - text_width) / 2
        self._draw_text(c, text, x, y, font, size, color)

    def _create_certificate_canvas(self, student, track, date, certificate_id):
        """Creates the certificate with dynamic content."""
        logger.info(f"Creating certificate for {student} in track {track}")
        c = canvas.Canvas(self.buffer, pagesize=landscape(A4), bottomup=0)

        # Draw student name (centered)
        self._draw_centered_text(c, student, 280, 'Helvetica-BoldOblique', 50, self.black)

        # Draw track name (centered)
        self._draw_centered_text(c, track, 420, 'Courier-BoldOblique', 25, self.orange)

        # Draw certificate ID and Date
        lines = [
            f'Certificate ID: {certificate_id}',
            f'Date: {date}'
        ]
        textobject = c.beginText()
        textobject.setTextOrigin(self.page_width - 350, 500)
        textobject.setFont('Courier-BoldOblique', 10)
        textobject.setFillColorRGB(*self.black)

        for line in lines:
            textobject.textLine(line)

        c.drawText(textobject)

        # Save the certificate canvas
        c.save()
        self.buffer.seek(0)
        logger.info("Certificate canvas created successfully.")

    def _merge_with_template(self):
        """Merge the generated certificate with the template."""
        logger.info("Merging certificate with template.")
        try:
            reader_template = PdfReader(self.template_path)
            writer = PdfWriter()

            # Add the template page
            template_page = reader_template.pages[0]
            writer.add_page(template_page)

            # Add the generated certificate page
            dynamic_pdf = PdfReader(self.buffer)
            dynamic_page = dynamic_pdf.pages[0]  # Since we're using one page
            writer.pages[0].merge_page(dynamic_page)

            # Write the final PDF to the buffer
            final_buffer = io.BytesIO()
            writer.write(final_buffer)
            final_buffer.seek(0)
            logger.info("Certificate merged with template successfully.")

            return final_buffer
        except Exception as e:
            logger.error(f"Error merging certificate with template: {e}", exc_info=True)
            raise

    def generate_certificate(self, student_name, track, date, certificate_id):
        """Generate the certificate and return the final PDF as a buffer."""
        logger.info(f"Generating certificate for {student_name}, track {track}, date {date}, id {certificate_id}")
        try:
            self._create_certificate_canvas(student_name, track, date, certificate_id)
            final_pdf_buffer = self._merge_with_template()
            logger.info("Certificate generated successfully.")
            return final_pdf_buffer
        except Exception as e:
            logger.error(f"Failed to generate certificate: {e}", exc_info=True)
            raise
