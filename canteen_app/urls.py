from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('order/', views.order_page, name='order'),
    path('api/recommend/', views.api_recommend, name='api_recommend'),
    path('api/place_order/', views.api_place_order, name='api_place_order'),
]
