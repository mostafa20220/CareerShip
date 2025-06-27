from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('silk/', include('silk.urls', namespace='silk')),
    path('admin/', admin.site.urls),
    path('api/v1/', include([
        path('', include('projects.urls')),
        path('teams/' , include('teams.urls')),
        path('auth/', include([
            path('', include('users.urls')),
            path('accounts/', include('allauth.urls')),
        ])),
        path('certificates/', include('certificates.urls')),
    ]) ),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += [path('i18n/', include('django.conf.urls.i18n'))]