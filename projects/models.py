from django.db import models
from django.contrib.auth.models import User

class Project(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=20, default='#2563EB')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def is_owner(self, user):
        if not user or not user.is_authenticated:
            return False
        return self.owner_id == user.id

    def is_member(self, user):
        if not user or not user.is_authenticated:
            return False
        if self.is_owner(user):
            return True
        return self.memberships.filter(user=user).exists()

    def get_user_role(self, user):
        if not user or not user.is_authenticated:
            return None
        if self.owner_id == user.id:
            return 'owner'
        membership = self.memberships.filter(user=user).first()
        return membership.role if membership else None


class ProjectMember(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('member', 'Member'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'user')
        ordering = ['joined_at']

    def __str__(self):
        return f"{self.user.username} in {self.project.name} ({self.role})"


class Column(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='columns')
    name = models.CharField(max_length=80)
    order = models.PositiveIntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['project', 'order']),
        ]

    def __str__(self):
        return f"{self.name} ({self.project.name})"


class Label(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='labels')
    name = models.CharField(max_length=40)
    color = models.CharField(max_length=20, default='#64748B')

    class Meta:
        unique_together = ('project', 'name')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.project.name})"


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks', db_index=True)
    column = models.ForeignKey(Column, on_delete=models.CASCADE, related_name='tasks', db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    assignee = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_tasks', db_index=True
    )
    creator = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='created_tasks'
    )
    due_date = models.DateField(null=True, blank=True, db_index=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', db_index=True)
    order = models.PositiveIntegerField(default=0, db_index=True)
    labels = models.ManyToManyField(Label, blank=True, related_name='tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['column', 'order']),
            models.Index(fields=['project', 'column', 'order']),
            models.Index(fields=['assignee', 'due_date']),
        ]

    def __str__(self):
        return self.title


class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments', db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.task.title}"


class Activity(models.Model):
    ACTION_CHOICES = [
        ('created', 'created'),
        ('moved', 'moved'),
        ('assigned', 'assigned'),
        ('unassigned', 'unassigned'),
        ('commented', 'commented'),
        ('due_date_changed', 'due_date_changed'),
        ('priority_changed', 'priority_changed'),
        ('edited', 'edited'),
        ('deleted', 'deleted'),
        ('column_created', 'column_created'),
        ('column_renamed', 'column_renamed'),
        ('column_deleted', 'column_deleted'),
        ('member_added', 'member_added'),
        ('member_removed', 'member_removed'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='activities', db_index=True)
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, null=True, blank=True,
        related_name='activities', db_index=True
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=40, choices=ACTION_CHOICES)
    details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', '-created_at']),
            models.Index(fields=['task', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} {self.action}: {self.details[:40]}"
