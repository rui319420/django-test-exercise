from django.shortcuts import render, redirect
from django.http import Http404
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime
from todo.models import Task


# Create your views here.
def index(request):
    if request.method == "POST":
        due_at_value = request.POST.get("due_at")
        due_at = make_aware(parse_datetime(due_at_value)) if due_at_value else None
        task = Task(
            title=request.POST["title"],
            priority=int(request.POST.get("priority", Task.PRIORITY_MEDIUM)),
            due_at=due_at,
        )
        task.save()

    tasks = Task.objects.all()
    if request.GET.get("favorite") == "1":
        tasks = tasks.filter(favorite=True)

    if request.GET.get("order") == "priority":
        tasks = tasks.order_by("-priority", "-posted_at")
    elif request.GET.get("order") == "due":
        tasks = tasks.order_by("due_at")
    else:
        tasks = tasks.order_by("-posted_at")

    context = {
        "tasks": tasks,
        "show_favorites_only": request.GET.get("favorite") == "1",
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
