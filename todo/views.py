from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.utils import timezone

from .models import TodoItem, TodoCategory, TodoTag
from .forms import TodoItemForm, TodoCategoryForm, TodoFilterForm


@login_required
def todo_list(request):
    """Display user's to-do list with filtering options"""
    
    todos = TodoItem.objects.filter(user=request.user)
    categories = TodoCategory.objects.filter(user=request.user)
    
    # Filtering
    status_filter = request.GET.get('status', 'all')
    priority_filter = request.GET.get('priority', 'all')
    search_query = request.GET.get('search', '')
    
    if status_filter != 'all':
        todos = todos.filter(status=status_filter)
    
    if priority_filter != 'all':
        todos = todos.filter(priority=priority_filter)
    
    if search_query:
        todos = todos.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Statistics
    stats = {
        'total': TodoItem.objects.filter(user=request.user).count(),
        'pending': TodoItem.objects.filter(user=request.user, status='pending').count(),
        'in_progress': TodoItem.objects.filter(user=request.user, status='in_progress').count(),
        'completed': TodoItem.objects.filter(user=request.user, status='completed').count(),
    }
    
    form = TodoFilterForm(request.GET)
    
    context = {
        'todos': todos,
        'categories': categories,
        'form': form,
        'stats': stats,
        'search_query': search_query,
    }
    
    return render(request, 'todo/todo_list.html', context)


@login_required
def create_todo(request):
    """Create a new to-do item"""
    
    if request.method == 'POST':
        form = TodoItemForm(request.POST)
        if form.is_valid():
            todo = form.save(commit=False)
            todo.user = request.user
            todo.save()
            return redirect('todo:todo_list')
    else:
        form = TodoItemForm()
    
    context = {'form': form, 'title': 'Create New Task'}
    return render(request, 'todo/create_todo.html', context)


@login_required
def update_todo(request, pk):
    """Update an existing to-do item"""
    
    todo = get_object_or_404(TodoItem, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = TodoItemForm(request.POST, instance=todo)
        if form.is_valid():
            form.save()
            return redirect('todo:todo_list')
    else:
        form = TodoItemForm(instance=todo)
    
    context = {'form': form, 'todo': todo, 'title': f'Edit: {todo.title}'}
    return render(request, 'todo/create_todo.html', context)


@login_required
def delete_todo(request, pk):
    """Delete a to-do item"""
    
    todo = get_object_or_404(TodoItem, pk=pk, user=request.user)
    
    if request.method == 'POST':
        todo.delete()
        return redirect('todo:todo_list')
    
    context = {'todo': todo}
    return render(request, 'todo/delete_confirm.html', context)


@login_required
@require_http_methods(["POST"])
def toggle_todo_status(request, pk):
    """Toggle to-do status via AJAX"""
    
    todo = get_object_or_404(TodoItem, pk=pk, user=request.user)
    
    # Cycle through statuses: pending -> in_progress -> completed -> pending
    status_cycle = {
        'pending': 'in_progress',
        'in_progress': 'completed',
        'completed': 'pending',
    }
    
    todo.status = status_cycle.get(todo.status, 'pending')
    
    if todo.status == 'completed':
        todo.completed_at = timezone.now()
    else:
        todo.completed_at = None
    
    todo.save()
    
    return JsonResponse({
        'success': True,
        'status_key': todo.status,
        'status': todo.get_status_display(),
        'completed_at': todo.completed_at.isoformat() if todo.completed_at else None,
    })


@login_required
def category_list(request):
    """Display user's categories"""
    
    categories = TodoCategory.objects.filter(user=request.user)
    
    context = {'categories': categories}
    return render(request, 'todo/category_list.html', context)


@login_required
def create_category(request):
    """Create a new category"""
    
    if request.method == 'POST':
        form = TodoCategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            return redirect('todo:category_list')
    else:
        form = TodoCategoryForm()
    
    context = {'form': form, 'title': 'Create Category'}
    return render(request, 'todo/create_category.html', context)


@login_required
@require_http_methods(["GET"])
def export_todos_json(request):
    """Export todos as JSON for local storage"""
    
    todos = TodoItem.objects.filter(user=request.user)
    
    todos_data = []
    for todo in todos:
        todos_data.append({
            'id': todo.id,
            'title': todo.title,
            'description': todo.description,
            'priority': todo.priority,
            'status': todo.status,
            'due_date': todo.due_date.isoformat() if todo.due_date else None,
            'created_at': todo.created_at.isoformat(),
            'completed_at': todo.completed_at.isoformat() if todo.completed_at else None,
        })
    
    return JsonResponse({
        'user': request.user.username,
        'exported_at': timezone.now().isoformat(),
        'todos': todos_data,
    })
