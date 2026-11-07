import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from projects.models import Project, ProjectMember, Task

def landing_view(request):
    if request.user.is_authenticated:
        return redirect('projects:project_list')
    return render(request, 'core/landing.html')

@login_required
def my_tasks_view(request):
    user = request.user
    today = timezone.now().date()

    # Base query: tasks assigned to me in projects I belong to
    member_project_ids = ProjectMember.objects.filter(user=user).values_list('project_id', flat=True)
    tasks_qs = Task.objects.filter(
        assignee=user
    ).filter(
        Q(project__owner=user) | Q(project_id__in=member_project_ids)
    ).select_related('project', 'column', 'assignee__profile').prefetch_related('labels')

    # Filters
    selected_project = request.GET.get('project')
    if selected_project and selected_project.isdigit():
        tasks_qs = tasks_qs.filter(project_id=int(selected_project))

    selected_priority = request.GET.get('priority')
    if selected_priority in ['low', 'medium', 'high']:
        tasks_qs = tasks_qs.filter(priority=selected_priority)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        tasks_qs = tasks_qs.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )

    tasks_list = list(tasks_qs.order_by('due_date', 'priority', 'title'))

    # Grouping
    overdue = []
    due_today = []
    due_soon = [] # within 7 days
    later = []
    no_date = []

    for t in tasks_list:
        if not t.due_date:
            no_date.append(t)
        elif t.due_date < today:
            overdue.append(t)
        elif t.due_date == today:
            due_today.append(t)
        elif t.due_date <= today + datetime.timedelta(days=7):
            due_soon.append(t)
        else:
            later.append(t)

    # Distinct projects user has tasks in
    user_projects = Project.objects.filter(
        id__in=Task.objects.filter(assignee=user).values_list('project_id', flat=True).distinct()
    ).order_by('name')

    return render(request, 'core/my_tasks.html', {
        'total_count': len(tasks_list),
        'overdue': overdue,
        'due_today': due_today,
        'due_soon': due_soon,
        'later': later,
        'no_date': no_date,
        'user_projects': user_projects,
        'selected_project': selected_project,
        'selected_priority': selected_priority,
        'search_query': search_query,
        'today': today,
    })

@login_required
def global_search_view(request):
    query = request.GET.get('q', '').strip()
    user = request.user

    member_project_ids = ProjectMember.objects.filter(user=user).values_list('project_id', flat=True)
    accessible_projects = Project.objects.filter(
        Q(owner=user) | Q(id__in=member_project_ids)
    ).distinct()

    tasks_results = []
    projects_results = []

    if query:
        projects_results = accessible_projects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )[:10]

        tasks_results = Task.objects.filter(
            project__in=accessible_projects
        ).filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        ).select_related('project', 'column', 'assignee__profile').prefetch_related('labels')[:25]

    return render(request, 'core/search.html', {
        'query': query,
        'tasks_results': tasks_results,
        'projects_results': projects_results,
    })

def custom_403_view(request, exception=None):
    return render(request, '403.html', status=403)

def custom_404_view(request, exception=None):
    return render(request, '404.html', status=404)

def custom_500_view(request):
    return render(request, '500.html', status=500)
