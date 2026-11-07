from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from .models import Notification

@login_required
def notification_list_view(request):
    notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related('actor__profile', 'project', 'task').order_by('-created_at')

    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'unread':
        notifications = notifications.filter(is_read=False)

    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()

    return render(request, 'notifications/list.html', {
        'notifications': notifications,
        'filter_type': filter_type,
        'unread_count': unread_count,
    })

@login_required
@require_GET
def api_notifications_dropdown(request):
    notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related('actor__profile', 'project', 'task').order_by('-created_at')[:10]

    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()

    data = []
    for n in notifications:
        actor_name = n.actor.profile.name if (n.actor and hasattr(n.actor, 'profile')) else (n.actor.username if n.actor else 'System')
        data.append({
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'verb': n.verb,
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%b %d, %H:%M'),
            'project_id': n.project_id,
            'task_id': n.task_id,
            'actor_name': actor_name,
        })

    return JsonResponse({
        'status': 'ok',
        'unread_count': unread_count,
        'notifications': data,
    })

@login_required
@require_POST
def api_mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save(update_fields=['is_read'])

    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()

    return JsonResponse({
        'status': 'ok',
        'notification_id': notification.id,
        'unread_count': unread_count,
    })

@login_required
@require_POST
def api_mark_all_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)

    return JsonResponse({
        'status': 'ok',
        'unread_count': 0,
    })
