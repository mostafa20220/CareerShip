from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
import certificates.views

urlpatterns = [
    path('silk/', include('silk.urls', namespace='silk')),
    path('admin/', admin.site.urls),
    path('api/v1/', include([
        path('auth/', include('users.urls')),
        path('projects/', include('projects.urls')),
        path('certificates/', include('certificates.urls')),
    ]) ),

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
