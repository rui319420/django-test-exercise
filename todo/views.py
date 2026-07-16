from django.shortcuts import render, redirect
from django.http import Http404
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime
from urllib.parse import urlencode
from todo.models import Task


# Create your views here.
def index(request):
    if request.method == "POST":
        task = Task(
            title=request.POST["title"],
            due_at=make_aware(parse_datetime(request.POST["due_at"])),
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
    if order == "due":
        tasks = tasks.order_by("due_at")
    else:
        tasks = tasks.order_by("-posted_at")

    def build_query(include_favorite=True, **overrides):
        params = {}
        if search_query:
            params["q"] = search_query
        if include_favorite and show_favorites_only:
            params["favorite"] = "1"
        if order in ("due", "post"):
            params["order"] = order
        params.update({key: value for key, value in overrides.items() if value is not None})
        return urlencode(params)

    context = {
        "tasks": tasks,
        "current_order": order if order in ("due", "post") else "",
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
        task.due_at = make_aware(parse_datetime(request.POST['due_at']))
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
        task.save()

    return redirect("detail", task_id=task_id)

def minesweeper(request):
    return render(request, "todo/minesweeper.html")
