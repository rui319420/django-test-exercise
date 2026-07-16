from django.shortcuts import render, redirect
from django.http import Http404
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime
from urllib.parse import urlencode
from todo.models import Task


def normalize_tags(raw_tags):
    return ", ".join(tag.strip() for tag in raw_tags.split(",") if tag.strip())


# Create your views here.
def index(request):
    if request.method == "POST":
        due_at_value = request.POST.get("due_at")
        due_at = make_aware(parse_datetime(due_at_value)) if due_at_value else None
        task = Task(
            title=request.POST["title"],
            priority=int(request.POST.get("priority", Task.PRIORITY_MEDIUM)),
            due_at=due_at,
            due_at=make_aware(parse_datetime(request.POST["due_at"])),
            tags=normalize_tags(request.POST.get("tags", "")),
        )
        task.save()

    tasks = Task.objects.all()
    search_query = request.GET.get("q", "").strip()
    if search_query:
        tasks = tasks.filter(title__icontains=search_query)

    show_favorites_only = request.GET.get("favorite") == "1"
    if show_favorites_only:
        tasks = tasks.filter(favorite=True)

    order = request.GET.get("order")
    if order == "priority":
        tasks = tasks.order_by("-priority", "-posted_at")
    elif order == "due":
        tasks = tasks.order_by("due_at")
    else:
        tasks = tasks.order_by("-posted_at")

    def build_query(include_favorite=True, **overrides):
        params = {}
        if search_query:
            params["q"] = search_query
        if include_favorite and show_favorites_only:
            params["favorite"] = "1"
        if order in ("due", "post", "priority"):
            params["order"] = order
        params.update({key: value for key, value in overrides.items() if value is not None})
        return urlencode(params)

    context = {
        "tasks": tasks,
        "current_order": order if order in ("due", "post", "priority") else "",
        "search_query": search_query,
        "show_favorites_only": show_favorites_only,
        "search_form_query": build_query(),
        "sort_by_due_query": build_query(order="due"),
        "sort_by_post_query": build_query(order="post"),
        "show_favorites_query": build_query(favorite="1"),
        "show_all_query": build_query(include_favorite=False),
    }
    return render(request, "todo/index.html", context)


def detail(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")

    context = {
        "task": task,
    }
    return render(request, "todo/detail.html", context)

def update(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")
    if request.method == 'POST':
        task.title = request.POST['title']
        task.priority = int(request.POST.get('priority', Task.PRIORITY_MEDIUM))
        due_at_value = request.POST.get('due_at')
        task.due_at = make_aware(parse_datetime(due_at_value)) if due_at_value else None
        task.due_at = make_aware(parse_datetime(request.POST['due_at']))
        task.tags = normalize_tags(request.POST.get("tags", ""))
        task.save()
        return redirect(detail, task_id)

    context = {
        'task' : task
    }
    return render(request, "todo/edit.html", context)

def delete(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task dose not exist")
    task.delete()
    return redirect("index")

def finish(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")
    if request.method == "POST":
        task.completed = True
        task.save()
    return redirect("detail", task_id=task_id)


def favorite(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")

    if request.method == "POST":
        task.favorite = not task.favorite