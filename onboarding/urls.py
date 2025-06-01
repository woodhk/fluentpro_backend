from django.urls import path
from . import views

urlpatterns = [
    path('phase1/set-native-language/', views.set_native_language, name='set_native_language'),
    path('phase1/available-languages/', views.get_available_languages, name='get_available_languages'),
    path('phase1/set-industry/', views.set_industry, name='set_industry'),
    path('phase1/available-industries/', views.get_available_industries, name='get_available_industries'),
]