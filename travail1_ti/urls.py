"""
URL configuration for travail1_ti project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny

from rest_framework_simplejwt.views import (
                    TokenObtainPairView,
                    TokenRefreshView,)
from api.graphql_views import graphql_view

urlpatterns =[
    path("", RedirectView.as_view(url="/travelHub/", permanent=False), name="home"),
    path('admin/', admin.site.urls),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("travelHub/", include("travelhub.urls")),


    path("api/v1/", include("api.urls")),
    path("api/schema/", SpectacularAPIView.as_view(permission_classes=[AllowAny]), name="api-schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="api-schema", permission_classes=[AllowAny]), name="api-docs"),
    path("graphql/", graphql_view, name="graphql"),

    path("api/token/", TokenObtainPairView.as_view(), name="api-token-obtain"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="api-token-refresh"),
]
