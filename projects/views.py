import json
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.utils import timezone
from .models import Project, ProjectMember, Column, Label, Task, Comment, Activity
from . import services

# ==========================================
# Helpers / Permission checks
# ==========================================
def get_project_and_membership(project_id, user):
    project = get_object_or_404(Project, id=project_id)
    if not project.is_member(user):
        return None, None
    role = project.get_user_role(user)
    return project, role

# ==========================================
# Views
# ==========================================
@login_required
def project_list_view(request):
    member_project_ids = ProjectMember.objects.filter(user=request.user).values_list('project_id', flat=True)
    projects = Project.objects.filter(
        Q(owner=request.user) | Q(id__in=member_project_ids)
    ).distinct().annotate(
        task_count=Count('tasks', distinct=True),
        member_count=Count('memberships', distinct=True)
    ).order_by('-created_at')

    return render(request, 'projects/project_list.html', {
        'projects': projects,
    })

@login_required
@require_POST
def project_create_view(request):
    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    color = request.POST.get('color', '#2563EB').strip()

    if not name:
        return JsonResponse({'status': 'error', 'message': 'Project name is required.'}, status=400)

    project = Project.objects.create(
        name=name,
        description=description,
        color=color,
        owner=request.user
    )

    # Add owner membership
    ProjectMember.objects.create(project=project, user=request.user, role='owner')

    # Default columns
    default_columns = ['To Do', 'In Progress', 'Review', 'Done']
    for idx, col_name in enumerate(default_columns):
        Column.objects.create(project=project, name=col_name, order=idx)

    # Default labels
    default_labels = [
        ('Frontend', '#2563EB'),
        ('Backend', '#0D9488'),
        ('Bug', '#DC2626'),
        ('Performance', '#D97706'),
    ]
    for lbl_name, lbl_col in default_labels:
        Label.objects.create(project=project, name=lbl_name, color=lbl_col)

    services.record_activity(
        project=project,
        user=request.user,
        action='created',
        details=f"created project \"{project.name}\""
    )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({'status': 'ok', 'project_id': project.id, 'redirect_url': f"/projects/{project.id}/"})

    return redirect('projects:project_board', project_id=project.id)

@login_required
def project_board_view(request, project_id):
    project, role = get_project_and_membership(project_id, request.user)
    if not project:
        return render(request, '403.html', status=403)

    columns = project.columns.prefetch_related(
        'tasks__labels',
        'tasks__assignee__profile',
        'tasks__comments'
    ).order_by('order', 'id')

    memberships = project.memberships.select_related('user__profile').all()
    labels = project.labels.all().order_by('name')

    return render(request, 'projects/board.html', {
        'project': project,
        'user_role': role,
        'is_owner': role == 'owner',
        'columns': columns,
        'memberships': memberships,
        'labels': labels,
    })

@login_required
def project_settings_view(request, project_id):
    project, role = get_project_and_membership(project_id, request.user)
    if not project:
        return render(request, '403.html', status=403)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_project':
            if role != 'owner':
                return HttpResponseForbidden("Only the project owner can edit project settings.")
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            color = request.POST.get('color', '#2563EB').strip()
            if name:
                project.name = name
                project.description = description
                project.color = color
                project.save()
                services.record_activity(project, request.user, 'edited', f"updated project settings")
                return redirect('projects:project_settings', project_id=project.id)

        elif action == 'delete_project':
            if role != 'owner':
                return HttpResponseForbidden("Only the project owner can delete the project.")
            project.delete()
            return redirect('projects:project_list')

        elif action == 'leave_project':
            if role == 'owner':
                return HttpResponseForbidden("Project owner cannot leave the project.")
            ProjectMember.objects.filter(project=project, user=request.user).delete()
            services.record_activity(project, request.user, 'member_removed', f"{request.user.username} left the project")
            return redirect('projects:project_list')

    memberships = project.memberships.select_related('user__profile').all().order_by('role', 'joined_at')
    labels = project.labels.all().order_by('name')

    return render(request, 'projects/project_settings.html', {
        'project': project,
        'user_role': role,
        'is_owner': role == 'owner',
        'memberships': memberships,
        'labels': labels,
    })

# ==========================================
# JSON API Endpoints (100% fetch() driven)
# ==========================================

@login_required
@require_GET
def api_task_detail(request, project_id, task_id):
    project, _ = get_project_and_membership(project_id, request.user)
    if not project:
        return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)

    task = get_object_or_404(
        Task.objects.select_related('assignee__profile', 'creator__profile', 'column')
        .prefetch_related('labels', 'comments__user__profile', 'activities__user__profile'),
        id=task_id, project=project
    )

    comments_data = []
    for c in task.comments.all().order_by('created_at'):
        profile = getattr(c.user, 'profile', None)
        comments_data.append({
            'id': c.id,
            'user_id': c.user.id,
            'username': c.user.username,
            'display_name': profile.name if profile else c.user.username,
            'initials': profile.initials if profile else c.user.username[:2].upper(),
            'avatar_color': profile.avatar_color if profile else '#2563EB',
            'avatar_url': profile.avatar_url if profile else None,
            'content': c.content,
            'created_at': c.created_at.strftime('%b %d, %H:%M'),
            'is_own': c.user_id == request.user.id,
        })

    activities_data = []
    for a in task.activities.all()[:15]:
        profile = getattr(a.user, 'profile', None)
        activities_data.append({
            'id': a.id,
            'action': a.action,
            'details': a.details,
            'user_name': profile.name if profile else a.user.username,
            'created_at': a.created_at.strftime('%b %d, %H:%M'),
        })

    return JsonResponse({
        'status': 'ok',
        'task': services.serialize_task(task),
        'comments': comments_data,
        'activities': activities_data,
    })

@login_required
@require_POST
def api_task_create(request, project_id):
    project, _ = get_project_and_membership(project_id, request.user)
    if not project:
        return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)

    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    title = data.get('title', '').strip()
    if not title:
        return JsonResponse({'status': 'error', 'message': 'Task title is required.'}, status=400)

    column_id = data.get('column_id')
    column = get_object_or_404(Column, id=column_id, project=project)

    description = data.get('description', '').strip()
    priority = data.get('priority', 'medium')
    if priority not in ['low', 'medium', 'high']:
        priority = 'medium'

    due_date_str = data.get('due_date')
    due_date = None
    if due_date_str:
        try:
            due_date = datetime.date.fromisoformat(due_date_str)
        except ValueError:
            pass

    assignee_id = data.get('assignee_id')
    assignee = None
    if assignee_id:
        try:
            assignee_user = User.objects.get(id=assignee_id)
            if project.is_member(assignee_user):
                assignee = assignee_user
        except User.DoesNotExist:
            pass

    # Order at end of column
    last_order = Task.objects.filter(column=column).count()

    task = Task.objects.create(
        project=project,
        column=column,
        title=title,
        description=description,
        assignee=assignee,
        creator=request.user,
        due_date=due_date,
        priority=priority,
        order=last_order,
    )

    label_ids = data.get('label_ids', [])
    if label_ids:
        labels = Label.objects.filter(project=project, id__in=label_ids)
        task.labels.set(labels)

    services.record_activity(
        project=project,
        task=task,
        user=request.user,
        action='created',
        details=f"created task \"{task.title}\""
    )

    if assignee and assignee.id != request.user.id:
        actor_name = request.user.profile.name if hasattr(request.user, 'profile') else request.user.username
        services.notify_user(
            recipient=assignee,
            verb='assigned',
            title=f"Task assigned to you in {project.name}",
            message=f"{actor_name} assigned you to \"{task.title}\"",
            actor=request.user,
            project=project,
            task=task,
        )

    task_data = services.serialize_task(task)
    services.broadcast_board_event(project.id, 'task_created', {'task': task_data}, actor_id=request.user.id)

    return JsonResponse({'status': 'ok', 'task': task_data})

@login_required
@require_POST
def api_task_update(request, project_id, task_id):
    project, _ = get_project_and_membership(project_id, request.user)
    if not project:
        return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)

    task = get_object_or_404(Task, id=task_id, project=project)

    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    updates = []
    if 'title' in data:
        title = data['title'].strip()
        if title and title != task.title:
            updates.append(f"renamed task to \"{title}\"")
            task.title = title

    if 'description' in data:
        task.description = data['description'].strip()

    if 'priority' in data:
        p = data['priority']
        if p in ['low', 'medium', 'high'] and p != task.priority:
            updates.append(f"changed priority to {p.capitalize()}")
            task.priority = p

    if 'due_date' in data:
        d_str = data['due_date']
        new_due_date = None
        if d_str:
            try:
                new_due_date = datetime.date.fromisoformat(d_str)
            except ValueError:
                pass
        if new_due_date != task.due_date:
            formatted = new_due_date.strftime('%b %d') if new_due_date else 'none'
            updates.append(f"changed due date to {formatted}")
            task.due_date = new_due_date

    if 'assignee_id' in data:
        a_id = data['assignee_id']
        old_assignee = task.assignee
        if not a_id:
            if old_assignee:
                task.assignee = None
                updates.append("unassigned task")
        else:
            try:
                target_user = User.objects.get(id=a_id)
                if project.is_member(target_user) and target_user != old_assignee:
                    task.assignee = target_user
                    target_name = target_user.profile.name if hasattr(target_user, 'profile') else target_user.username
                    updates.append(f"assigned task to {target_name}")

                    # Send notification to new assignee
                    if target_user.id != request.user.id:
                        actor_name = request.user.profile.name if hasattr(request.user, 'profile') else request.user.username
                        services.notify_user(
                            recipient=target_user,
                            verb='assigned',
                            title=f"Task assigned in {project.name}",
                            message=f"{actor_name} assigned you to \"{task.title}\"",
                            actor=request.user,
                            project=project,
                            task=task,
                        )
            except User.DoesNotExist:
                pass

    if 'label_ids' in data:
        labels = Label.objects.filter(project=project, id__in=data['label_ids'])
        task.labels.set(labels)

    task.save()

    if updates:
        services.record_activity(
            project=project,
            task=task,
            user=request.user,
            action='edited',
            details="; ".join(updates)
        )

    task_data = services.serialize_task(task)
    services.broadcast_board_event(project.id, 'task_updated', {'task': task_data}, actor_id=request.user.id)

    return JsonResponse({'status': 'ok', 'task': task_data})

@login_required
@require_POST
def api_task_delete(request, project_id, task_id):
    project, _ = get_project_and_membership(project_id, request.user)
    if not project:
        return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)

    task = get_object_or_404(Task, id=task_id, project=project)
    task_id_saved = task.id
    column_id_saved = task.column_id
    task_title_saved = task.title

    task.delete()

    services.record_activity(
        project=project,
        task=None,
        user=request.user,
        action='deleted',
        details=f"deleted task \"{task_title_saved}\""
    )

    services.broadcast_board_event(
        project.id,
        'task_deleted',
        {'task_id': task_id_saved, 'column_id': column_id_saved},
        actor_id=request.user.id
    )

    return JsonResponse({'status': 'ok', 'task_id': task_id_saved})

@login_required
@require_POST
def api_task_move(request, project_id, task_id):
    project, _ = get_project_and_membership(project_id, request.user)
    if not project:
        return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)

    task = get_object_or_404(Task, id=task_id, project=project)

    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    target_column_id = data.get('target_column_id')
    new_order = int(data.get('new_order', 0))

    target_column = get_object_or_404(Column, id=target_column_id, project=project)

    services.move_task_card(task, target_column, new_order, request.user)

    return JsonResponse({'status': 'ok'})

@login_required
@require_POST
def api_comment_add(request, project_id, task_id):
    project, _ = get_project_and_membership(project_id, request.user)
    if not project:
        return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)

    task = get_object_or_404(Task, id=task_id, project=project)

    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    content = data.get('content', '').strip()
    if not content:
        return JsonResponse({'status': 'error', 'message': 'Comment content cannot be empty.'}, status=400)

    comment = Comment.objects.create(
        task=task,
        user=request.user,
        content=content
    )

    services.record_activity(
        project=project,
        task=task,
        user=request.user,
        action='commented',
        details=f"commented on \"{task.title}\""
    )

    # Mentions handling
    services.handle_mentions(comment, request.user)

    # Notify task assignee or creator if they are not the author
    actor_name = request.user.profile.name if hasattr(request.user, 'profile') else request.user.username
    targets_to_notify = set()
    if task.assignee and task.assignee.id != request.user.id:
        targets_to_notify.add(task.assignee)
    if task.creator and task.creator.id != request.user.id:
        targets_to_notify.add(task.creator)

    for target in targets_to_notify:
        services.notify_user(
            recipient=target,
            verb='commented',
            title=f"New comment on {task.title}",
            message=f"{actor_name}: \"{comment.content[:80]}\"",
            actor=request.user,
            project=project,
            task=task,
            comment=comment,
        )

    profile = getattr(request.user, 'profile', None)
    comment_data = {
        'id': comment.id,
        'user_id': request.user.id,
        'username': request.user.username,
        'display_name': profile.name if profile else request.user.username,
        'initials': profile.initials if profile else request.user.username[:2].upper(),
        'avatar_color': profile.avatar_color if profile else '#2563EB',
        'avatar_url': profile.avatar_url if profile else None,
        'content': comment.content,
        'created_at': comment.created_at.strftime('%b %d, %H:%M'),
        'is_own': True,
    }

    services.broadcast_board_event(
        project.id,
        'comment_added',
        {'task_id': task.id, 'comment': comment_data, 'comments_count': task.comments.count()},
        actor_id=request.user.id
    )

    return JsonResponse({'status': 'ok', 'comment': comment_data})

@login_required
@require_POST
def api_comment_delete(request, project_id, comment_id):
    project, role = get_project_and_membership(project_id, request.user)
    if not project:
        return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)

    comment = get_object_or_404(Comment, id=comment_id, task__project=project)
    if comment.user_id != request.user.id and role != 'owner':
        return JsonResponse({'status': 'error', 'message': 'You can only delete your own comments.'}, status=403)

    task = comment.task
    comment_id_saved = comment.id
    comment.delete()

    services.broadcast_board_event(
        project.id,
        'comment_deleted',
        {'task_id': task.id, 'comment_id': comment_id_saved, 'comments_count': task.comments.count()},
        actor_id=request.user.id
    )

    return JsonResponse({'status': 'ok', 'comment_id': comment_id_saved})

@login_required
@require_POST
def api_column_create(request, project_id):
    project, _ = get_project_and_membership(project_id, request.user)
    if not project:
        return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)

    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    name = data.get('name', '').strip()
    if not name:
        return JsonResponse({'status': 'error', 'message': 'Column name is required.'}, status=400)

    order = Column.objects.filter(project=project).count()
    col = Column.objects.create(project=project, name=name, order=order)

    services.record_activity(project, request.user, 'column_created', f"added column \"{col.name}\"")

    col_data = services.serialize_column(col)
    services.broadcast_board_event(project.id, 'column_created', {'column': col_data}, actor_id=request.user.id)

    return JsonResponse({'status': 'ok', 'column': col_data})

@login_required
@require_POST
def api_column_rename(request, project_id, column_id):
    project, _ = get_project_and_membership(project_id, request.user)
    if not project:
        return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)

    col = get_object_or_404(Column, id=column_id, project=project)

    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    name = data.get('name', '').strip()
    if not name:
        return JsonResponse({'status': 'error', 'message': 'Column name is required.'}, status=400)

    old_name = col.name
    col.name = name
    col.save(update_fields=['name'])

    services.record_activity(project, request.user, 'column_renamed', f"renamed column from \"{old_name}\" to \"{name}\"")

    services.broadcast_board_event(
        project.id,
        'column_renamed',
        {'column_id': col.id, 'name': col.name},
        actor_id=request.user.id
    )

    return JsonResponse({'status': 'ok', 'column_id': col.id, 'name': col.name})

@login_required
@require_POST
def api_column_delete(request, project_id, column_id):
    project, role = get_project_and_membership(project_id, request.user)
    if not project:
        return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)

    col = get_object_or_404(Column, id=column_id, project=project)
    col_id_saved = col.id
    col_name_saved = col.name

    col.delete()

    services.record_activity(project, request.user, 'column_deleted', f"deleted column \"{col_name_saved}\"")

    services.broadcast_board_event(
        project.id,
        'column_deleted',
        {'column_id': col_id_saved},
        actor_id=request.user.id
    )

    return JsonResponse({'status': 'ok', 'column_id': col_id_saved})

@login_required
@require_POST
def api_column_reorder(request, project_id):
    project, _ = get_project_and_membership(project_id, request.user)
    if not project:
        return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)

    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    order_map = data.get('column_orders', []) # list of column_id in order
    for idx, col_id in enumerate(order_map):
        Column.objects.filter(project=project, id=col_id).update(order=idx)

    services.broadcast_board_event(
        project.id,
        'columns_reordered',
        {'column_orders': order_map},
        actor_id=request.user.id
    )

    return JsonResponse({'status': 'ok'})

@login_required
@require_POST
def api_member_invite(request, project_id):
    project, role = get_project_and_membership(project_id, request.user)
    if not project:
        return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)

    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    query = data.get('query', '').strip()
    target_role = data.get('role', 'member')
    if target_role not in ['owner', 'member']:
        target_role = 'member'

    target_user = User.objects.filter(Q(username__iexact=query) | Q(email__iexact=query)).first()
    if not target_user:
        return JsonResponse({'status': 'error', 'message': f'No user found with username or email "{query}".'}, status=404)

    if project.is_member(target_user):
        return JsonResponse({'status': 'error', 'message': f'{target_user.username} is already a member of this project.'}, status=400)

    membership = ProjectMember.objects.create(
        project=project,
        user=target_user,
        role=target_role
    )

    actor_name = request.user.profile.name if hasattr(request.user, 'profile') else request.user.username
    target_name = target_user.profile.name if hasattr(target_user, 'profile') else target_user.username

    services.record_activity(project, request.user, 'member_added', f"added {target_name} as {target_role}")

    # Notify invited user
    services.notify_user(
        recipient=target_user,
        verb='project_added',
        title=f"Added to {project.name}",
        message=f"{actor_name} added you as {target_role} in {project.name}",
        actor=request.user,
        project=project,
    )

    profile = getattr(target_user, 'profile', None)
    member_data = {
        'id': target_user.id,
        'username': target_user.username,
        'display_name': profile.name if profile else target_user.username,
        'initials': profile.initials if profile else target_user.username[:2].upper(),
        'avatar_color': profile.avatar_color if profile else '#2563EB',
        'avatar_url': profile.avatar_url if profile else None,
        'role': target_role,
    }

    services.broadcast_board_event(project.id, 'member_added', {'member': member_data}, actor_id=request.user.id)

    return JsonResponse({'status': 'ok', 'member': member_data})

@login_required
@require_POST
def api_member_remove(request, project_id, user_id):
    project, role = get_project_and_membership(project_id, request.user)
    if not project or role != 'owner':
        return JsonResponse({'status': 'error', 'message': 'Only project owner can remove members.'}, status=403)

    if int(user_id) == project.owner_id:
        return JsonResponse({'status': 'error', 'message': 'Cannot remove project owner.'}, status=400)

    target_user = get_object_or_404(User, id=user_id)
    ProjectMember.objects.filter(project=project, user=target_user).delete()

    target_name = target_user.profile.name if hasattr(target_user, 'profile') else target_user.username
    services.record_activity(project, request.user, 'member_removed', f"removed {target_name} from project")

    services.broadcast_board_event(
        project.id,
        'member_removed',
        {'user_id': target_user.id},
        actor_id=request.user.id
    )

    return JsonResponse({'status': 'ok', 'user_id': target_user.id})

@login_required
@require_POST
def api_label_create(request, project_id):
    project, _ = get_project_and_membership(project_id, request.user)
    if not project:
        return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)

    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    name = data.get('name', '').strip()
    color = data.get('color', '#64748B').strip()

    if not name:
        return JsonResponse({'status': 'error', 'message': 'Label name is required.'}, status=400)

    label, created = Label.objects.get_or_create(
        project=project,
        name=name,
        defaults={'color': color}
    )

    return JsonResponse({
        'status': 'ok',
        'label': {'id': label.id, 'name': label.name, 'color': label.color}
    })

@login_required
@require_GET
def api_project_activity(request, project_id):
    project, _ = get_project_and_membership(project_id, request.user)
    if not project:
        return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)

    activities = project.activities.select_related('user__profile')[:30]
    data = []
    for a in activities:
        profile = getattr(a.user, 'profile', None)
        data.append({
            'id': a.id,
            'action': a.action,
            'details': a.details,
            'user_name': profile.name if profile else a.user.username,
            'created_at': a.created_at.strftime('%b %d, %H:%M'),
        })
    return JsonResponse({'status': 'ok', 'activities': data})
