import oauth2_provider.views as oauth2_views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include, re_path

urlpatterns = [re_path(r'^oauth/authorize/$', oauth2_views.AuthorizationView.as_view(), name="authorize"),
               re_path(r'^oauth/token/$', oauth2_views.TokenView.as_view(), name="token"),
               re_path(r'^oauth/revoke-token/$', oauth2_views.RevokeTokenView.as_view(), name="revoke-token"),

               path('users/', include('api.users.urls')),
               path("symptoms/", include('api.symptoms.urls')),
               path('medicine/', include('api.medicine.urls')),
               path("calendar/", include('api.calendars.urls')),
               path('dashboard',include('api.dashboard.urls'))

               ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
