import datetime
from django.shortcuts import render


from django.http import HttpResponse , FileResponse

import io 
import os

from django.conf import settings

from .services import CertificateGenerator




def generate_certificate(request):

    student = "Mohamed Hesham"
    track = "Frontend Development"
    date = datetime.datetime.now().strftime("%d/%m/%Y")
    certificate_id = "156412132156"

    template_pdf_path = os.path.join(settings.BASE_DIR , "certificates" , "template" , "certificate_template.pdf")
    certificate = CertificateGenerator(template_pdf_path).generate_certificate(student , track , date , certificate_id)

    return FileResponse(certificate, as_attachment=True, filename='cert.pdf')




