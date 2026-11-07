from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('my-tasks/', views.my_tasks_view, name='my_tasks'),
    path('search/', views.global_search_view, name='search'),
]
