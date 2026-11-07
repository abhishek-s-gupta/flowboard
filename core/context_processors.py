from django.db.models import Q
from projects.models import Project, ProjectMember
from notifications.models import Notification

def global_context(request):
    if not request.user.is_authenticated:
        return {
            'global_projects': [],
            'unread_notifications_count': 0,
            'active_theme': 'light',
        }

    # Fetch projects where user is owner or member
    member_project_ids = ProjectMember.objects.filter(user=request.user).values_list('project_id', flat=True)
    projects = Project.objects.filter(
        Q(owner=request.user) | Q(id__in=member_project_ids)
    ).distinct().order_by('name')

    unread_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()

    theme = 'light'
    if hasattr(request.user, 'profile'):
        theme = request.user.profile.theme_preference

    return {
        'global_projects': projects,
        'unread_notifications_count': unread_count,
        'active_theme': theme,
    }
