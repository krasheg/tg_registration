from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('', TemplateView.as_view(template_name="profiles/index.html"), name='index'),
    path('profile/<int:pk>/', views.UserDetailView.as_view(), name='profile'),
]
