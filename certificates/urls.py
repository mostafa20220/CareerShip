from django.urls import path
from .views import *

urlpatterns = [
    path('', CertificateListView.as_view(), name='list_certificates'),
    path('<uuid:certificate_id>/', CertificateDetailView.as_view(), name='retrieve_certificate'),
    path('<uuid:certificate_id>/download/', CertificateDownloadView.as_view(), name='download_certificate'),
]
