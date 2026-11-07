from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list_view, name='project_list'),
    path('create/', views.project_create_view, name='project_create'),
    path('<int:project_id>/', views.project_board_view, name='project_board'),
    path('<int:project_id>/settings/', views.project_settings_view, name='project_settings'),

    # JSON API endpoints
    path('api/<int:project_id>/tasks/create/', views.api_task_create, name='api_task_create'),
    path('api/<int:project_id>/tasks/<int:task_id>/', views.api_task_detail, name='api_task_detail'),
    path('api/<int:project_id>/tasks/<int:task_id>/update/', views.api_task_update, name='api_task_update'),
    path('api/<int:project_id>/tasks/<int:task_id>/delete/', views.api_task_delete, name='api_task_delete'),
    path('api/<int:project_id>/tasks/<int:task_id>/move/', views.api_task_move, name='api_task_move'),
    path('api/<int:project_id>/tasks/<int:task_id>/comments/', views.api_comment_add, name='api_comment_add'),
    path('api/<int:project_id>/comments/<int:comment_id>/delete/', views.api_comment_delete, name='api_comment_delete'),

    path('api/<int:project_id>/columns/create/', views.api_column_create, name='api_column_create'),
    path('api/<int:project_id>/columns/<int:column_id>/rename/', views.api_column_rename, name='api_column_rename'),
    path('api/<int:project_id>/columns/<int:column_id>/delete/', views.api_column_delete, name='api_column_delete'),
    path('api/<int:project_id>/columns/reorder/', views.api_column_reorder, name='api_column_reorder'),

    path('api/<int:project_id>/members/invite/', views.api_member_invite, name='api_member_invite'),
    path('api/<int:project_id>/members/<int:user_id>/remove/', views.api_member_remove, name='api_member_remove'),

    path('api/<int:project_id>/labels/create/', views.api_label_create, name='api_label_create'),
    path('api/<int:project_id>/activities/', views.api_project_activity, name='api_project_activity'),
]
