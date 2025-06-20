import datetime
from django.shortcuts import render


from django.http import HttpResponse , FileResponse

import io 
import os

from django.conf import settings

from .services import CertificateGenerator

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Certificate
from .serializers import CertificateSerializer
from django.shortcuts import get_object_or_404
from rest_framework import generics





class CertificateListView(generics.ListAPIView):
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Certificate.objects.filter(user=self.request.user)


class CertificateDetailView(generics.RetrieveAPIView):
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'no'  # Instead of pk
    lookup_url_kwarg = 'certificate_id'

    def get_queryset(self):
        return Certificate.objects.filter(user=self.request.user)
      

class CertificateDownloadView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    lookup_field = 'no'  # Instead of pk
    lookup_url_kwarg = 'certificate_id'

    def post(self, request, certificate_id):
        certificate = get_object_or_404(Certificate, no=certificate_id, user=request.user)
        student = f"{request.user.first_name} {request.user.last_name}"
        track = certificate.project.name
        date = certificate.created_at.strftime("%d/%m/%Y")
        certificate_id_str = str(certificate.no)

        template_pdf_path = os.path.join(
            settings.BASE_DIR, "certificates", "template", "template_1.pdf"
        )
        pdf_buffer = CertificateGenerator(template_pdf_path).generate_certificate(
            student, track, date, certificate_id_str
        )

        return FileResponse(pdf_buffer, as_attachment=True, filename=f'certificate_{certificate_id_str}.pdf')

