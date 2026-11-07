from django.contrib import admin
from .models import Project, ProjectMember, Column, Label, Task, Comment, Activity

class ProjectMemberInline(admin.TabularInline):
    model = ProjectMember
    extra = 1

class ColumnInline(admin.TabularInline):
    model = Column
    extra = 1

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'color', 'created_at')
    search_fields = ('name', 'description', 'owner__username')
    inlines = [ProjectMemberInline, ColumnInline]

@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'role', 'joined_at')
    list_filter = ('role', 'joined_at')
    search_fields = ('project__name', 'user__username')

@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'order', 'created_at')
    list_filter = ('project',)
    ordering = ('project', 'order')

@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'color')
    list_filter = ('project',)
    search_fields = ('name',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'column', 'assignee', 'priority', 'due_date', 'order')
    list_filter = ('priority', 'project', 'due_date')
    search_fields = ('title', 'description', 'assignee__username')
    ordering = ('column', 'order')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'created_at')
    search_fields = ('content', 'user__username', 'task__title')

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('project', 'task', 'user', 'action', 'created_at')
    list_filter = ('action', 'project')
    search_fields = ('details', 'user__username')
