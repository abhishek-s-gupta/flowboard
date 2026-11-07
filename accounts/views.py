from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from .forms import LoginForm, RegisterForm
from .models import Profile

def login_view(request):
    if request.user.is_authenticated:
        return redirect('projects:project_list')

    form = LoginForm(request.POST or None)
    error_message = None

    if request.method == 'POST' and form.is_valid():
        username_or_email = form.cleaned_data['username']
        password = form.cleaned_data['password']

        # Allow login by email or username
        user = authenticate(request, username=username_or_email, password=password)
        if user is None:
            user_obj = User.objects.filter(email__iexact=username_or_email).first()
            if user_obj:
                user = authenticate(request, username=user_obj.username, password=password)

        if user is not None:
            login(request, user)
            next_url = request.GET.get('next') or 'projects:project_list'
            return redirect(next_url)
        else:
            error_message = "Invalid username/email or password."

    return render(request, 'accounts/login.html', {
        'form': form,
        'error_message': error_message
    })

def register_view(request):
    if request.user.is_authenticated:
        return redirect('projects:project_list')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = User.objects.create_user(
            username=form.cleaned_data['username'],
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password']
        )
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.display_name = form.cleaned_data['display_name']
        profile.save()

        login(request, user)
        return redirect('projects:project_list')

    return render(request, 'accounts/register.html', {
        'form': form
    })

def logout_view(request):
    logout(request)
    return redirect('accounts:login')

@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    success_message = None

    if request.method == 'POST':
        display_name = request.POST.get('display_name', '').strip()
        theme_preference = request.POST.get('theme_preference', 'light')
        avatar_file = request.FILES.get('avatar')

        if display_name:
            profile.display_name = display_name
        if theme_preference in ['light', 'dark']:
            profile.theme_preference = theme_preference
        if avatar_file:
            profile.avatar = avatar_file

        profile.save()
        success_message = "Profile updated successfully."

    return render(request, 'accounts/profile.html', {
        'profile': profile,
        'success_message': success_message
    })

@login_required
@require_POST
def api_profile_update(request):
    import json
    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    profile, _ = Profile.objects.get_or_create(user=request.user)

    if 'theme_preference' in data:
        theme = data['theme_preference']
        if theme in ['light', 'dark']:
            profile.theme_preference = theme
            profile.save(update_fields=['theme_preference', 'updated_at'])
            return JsonResponse({'status': 'ok', 'theme': theme})

    if 'display_name' in data:
        name = data['display_name'].strip()
        if name:
            profile.display_name = name
            profile.save(update_fields=['display_name', 'updated_at'])
            return JsonResponse({'status': 'ok', 'display_name': name})

    return JsonResponse({'status': 'error', 'message': 'No valid update field'}, status=400)
