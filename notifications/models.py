from django.db import models
from django.contrib.auth.models import User
from projects.models import Project, Task, Comment

class Notification(models.Model):
    VERB_CHOICES = [
        ('assigned', 'assigned'),
        ('mentioned', 'mentioned'),
        ('commented', 'commented'),
        ('project_added', 'project_added'),
        ('due_soon', 'due_soon'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', db_index=True)
    actor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='triggered_notifications'
    )
    verb = models.CharField(max_length=30, choices=VERB_CHOICES)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', '-created_at']),
        ]

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.title}"
