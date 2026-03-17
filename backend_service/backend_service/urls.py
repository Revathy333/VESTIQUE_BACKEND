"""
URL configuration for backend_service project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
# from backend_service.swagger import AdminSchemaView, AdminSwaggerView
from backend_service.swagger import PublicSchemaView, PublicSwaggerView, PublicRedocView


urlpatterns = [

    path('admin/', admin.site.urls),
    # Authentication API
    path('api/auth/', include('auth_app.urls')),
    path('api/admin/', include('admin_panel.urls')), 

   
    path("api/schema/",  PublicSchemaView.as_view(),                    name="schema"),
    path("api/swagger/", PublicSwaggerView.as_view(url_name="schema"),  name="swagger-ui"),
    path("api/redoc/",   PublicRedocView.as_view(url_name="schema"),    name="redoc"),

    path('api/posts/', include('posts_app.urls')),
    path('api/reviews/', include('reviews_app.urls')),

    path("api/notifications/", include("notifications_app.urls")),

    
    ]

