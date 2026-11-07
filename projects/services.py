import re
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F
from .models import Project, ProjectMember, Column, Label, Task, Comment, Activity
from notifications.models import Notification

def get_layer():
    return get_channel_layer()

def broadcast_board_event(project_id, event_name, data, actor_id=None):
    layer = get_layer()
    if layer:
        async_to_sync(layer.group_send)(
            f"board_{project_id}",
            {
                'type': 'board_event',
                'event': event_name,
                'data': data,
                'actor_id': actor_id,
            }
        )

def notify_user(recipient, verb, title, message, actor=None, project=None, task=None, comment=None):
    if not recipient or (actor and recipient.id == actor.id):
        return None

    notification = Notification.objects.create(
        recipient=recipient,
        actor=actor,
        verb=verb,
        project=project,
        task=task,
        comment=comment,
        title=title,
        message=message,
        is_read=False,
    )

    unread_count = Notification.objects.filter(recipient=recipient, is_read=False).count()
    layer = get_layer()
    if layer:
        async_to_sync(layer.group_send)(
            f"user_notifications_{recipient.id}",
            {
                'type': 'notification_event',
                'unread_count': unread_count,
                'notification': {
                    'id': notification.id,
                    'title': notification.title,
                    'message': notification.message,
                    'verb': notification.verb,
                    'is_read': False,
                    'created_at': notification.created_at.strftime('%b %d, %H:%M'),
                    'project_id': project.id if project else None,
                    'task_id': task.id if task else None,
                    'actor_name': actor.profile.name if (actor and hasattr(actor, 'profile')) else (actor.username if actor else 'System'),
                }
            }
        )
    return notification

def record_activity(project, user, action, details, task=None):
    return Activity.objects.create(
        project=project,
        task=task,
        user=user,
        action=action,
        details=details,
    )

def handle_mentions(comment, actor):
    pattern = r'@([A-Za-z0-9_]+)'
    usernames = set(re.findall(pattern, comment.content))
    if not usernames:
        return

    task = comment.task
    project = task.project
    from django.db.models import Q
    valid_users = User.objects.filter(
        username__in=usernames
    ).filter(
        Q(id=project.owner_id) | Q(project_memberships__project=project)
    ).distinct()

    actor_name = actor.profile.name if hasattr(actor, 'profile') else actor.username
    for target in valid_users:
        if target.id != actor.id:
            notify_user(
                recipient=target,
                verb='mentioned',
                title=f"Mentioned in {project.name}",
                message=f"{actor_name} mentioned you on task \"{task.title}\": \"{comment.content[:80]}\"",
                actor=actor,
                project=project,
                task=task,
                comment=comment,
            )

def serialize_task(task):
    assignee_data = None
    if task.assignee:
        profile = getattr(task.assignee, 'profile', None)
        assignee_data = {
            'id': task.assignee.id,
            'username': task.assignee.username,
            'display_name': profile.name if profile else task.assignee.username,
            'initials': profile.initials if profile else task.assignee.username[:2].upper(),
            'avatar_color': profile.avatar_color if profile else '#2563EB',
            'avatar_url': profile.avatar_url if profile else None,
        }

    labels_data = [
        {'id': lbl.id, 'name': lbl.name, 'color': lbl.color}
        for lbl in task.labels.all()
    ]

    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'project_id': task.project_id,
        'column_id': task.column_id,
        'priority': task.priority,
        'order': task.order,
        'due_date': task.due_date.isoformat() if task.due_date else None,
        'due_date_formatted': task.due_date.strftime('%b %d') if task.due_date else None,
        'assignee': assignee_data,
        'labels': labels_data,
        'comments_count': task.comments.count(),
        'created_at': task.created_at.strftime('%b %d, %Y'),
    }

def serialize_column(col):
    return {
        'id': col.id,
        'project_id': col.project_id,
        'name': col.name,
        'order': col.order,
        'tasks_count': col.tasks.count(),
    }

def move_task_card(task, target_column, new_order, user):
    old_column = task.column
    old_order = task.order

    with transaction.atomic():
        if old_column.id == target_column.id:
            # Moving within same column
            tasks = list(Task.objects.filter(column=old_column).exclude(id=task.id).order_by('order', 'id'))
            tasks.insert(new_order, task)
            for idx, t in enumerate(tasks):
                if t.order != idx:
                    Task.objects.filter(id=t.id).update(order=idx)
            task.order = new_order
            task.save(update_fields=['order', 'updated_at'])
            details = f"reordered task \"{task.title}\" in {old_column.name}"
        else:
            # Moving across columns
            # Shift old column tasks
            Task.objects.filter(column=old_column, order__gt=old_order).update(order=F('order') - 1)
            # Make room in new column
            Task.objects.filter(column=target_column, order__gte=new_order).update(order=F('order') + 1)
            task.column = target_column
            task.order = new_order
            task.save(update_fields=['column', 'order', 'updated_at'])
            details = f"moved task \"{task.title}\" from {old_column.name} to {target_column.name}"

        record_activity(
            project=task.project,
            task=task,
            user=user,
            action='moved',
            details=details,
        )

    # Broadcast real-time event
    broadcast_board_event(
        task.project_id,
        'task_moved',
        {
            'task_id': task.id,
            'source_column_id': old_column.id,
            'target_column_id': target_column.id,
            'new_order': new_order,
            'task': serialize_task(task),
        },
        actor_id=user.id
    )
