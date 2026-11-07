from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import hashlib

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    theme_preference = models.CharField(
        max_length=10,
        choices=[('light', 'Light'), ('dark', 'Dark')],
        default='light'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} Profile"

    @property
    def name(self):
        return self.display_name.strip() or self.user.username

    @property
    def initials(self):
        name = self.name.strip()
        parts = name.split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[1][0]}".upper()
        elif parts:
            return parts[0][:2].upper()
        return "FB"

    @property
    def avatar_color(self):
        # Deterministic calm color palette based on username
        colors = [
            '#2563EB', '#475569', '#0D9488', '#4F46E5', '#0284C7',
            '#64748B', '#059669', '#334155', '#3B82F6', '#1E293B'
        ]
        hash_val = int(hashlib.md5(self.user.username.encode('utf-8')).hexdigest(), 16)
        return colors[hash_val % len(colors)]

    @property
    def avatar_url(self):
        if self.avatar:
            try:
                return self.avatar.url
            except Exception:
                pass
        return None
