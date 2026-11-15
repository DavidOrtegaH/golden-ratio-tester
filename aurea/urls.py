from django.urls import path
from lab import views

urlpatterns = [
    path('', views.index, name='home'),
    path('language/', views.language, name='language'),
    path('result/<str:token>/', views.result, name='result'),
    path('image/<str:token>/<str:variant>/', views.image, name='image'),
    path('delete/<str:token>/', views.delete, name='delete'),
]
