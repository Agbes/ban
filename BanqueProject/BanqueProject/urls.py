from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.utils.translation import gettext_lazy as _


# urlpatterns = [
#     path("i18n/", include("django.conf.urls.i18n")),
# ]

# Wrap your localized URL patterns with i18n_patterns
urlpatterns = i18n_patterns(
    path("i18n/", include("django.conf.urls.i18n")),
    path('rosetta/', include('rosetta.urls')),
    path('admin/', admin.site.urls),
    path('', include('banque_app.urls')),
    prefix_default_language=False
)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)