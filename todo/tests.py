from django.test import TestCase, Client
from django.utils import timezone
from datetime import datetime
from todo.models import Task


# Create your tests here.
class SampleTestCase(TestCase):
    def test_sample1(self):
        self.assertEqual(1 + 2, 3)


class TaskModelTestCase(TestCase):
    def test_create_task1(self):
        due = timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59))
        task = Task(title="task1", due_at=due)
        task.save()

        task = Task.objects.get(pk=task.pk)
        self.assertEqual(task.title, "task1")
        self.assertFalse(task.completed)
        self.assertEqual(task.due_at, due)

    def test_create_task2(self):
        task = Task(title="task2")
        task.save()

        task = Task.objects.get(pk=task.pk)
        self.assertFalse(task.completed)
        self.assertFalse(task.favorite)
        self.assertEqual(task.due_at, None)

    def test_create_task_favorite_default_false(self):
        task = Task(title="task3")
        task.save()

        task = Task.objects.get(pk=task.pk)
        self.assertFalse(task.favorite)
        self.assertEqual(task.priority, Task.PRIORITY_MEDIUM)

    def test_priority_choice_display(self):
        task = Task(title="task-priority", priority=Task.PRIORITY_HIGH)
        task.save()

        task = Task.objects.get(pk=task.pk)
        self.assertEqual(task.get_priority_display(), 'High')

    def test_is_overdue_future(self):
        due = timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59))
        current = timezone.make_aware(datetime(2024, 6, 30, 0, 0, 0))
        task = Task(title="task1", due_at=due)
        task.save()

        self.assertFalse(task.is_overdue(current))

    def test_is_overdue_past(self):
        due = timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59))
        current = timezone.make_aware(datetime(2024, 7, 1, 0, 0, 0))
        task = Task(title="task1", due_at=due)
        task.save()

        self.assertTrue(task.is_overdue(current))

    def test_is_overdue_none(self):
        current = timezone.make_aware(datetime(2024, 7, 1, 0, 0, 0))
        task = Task(title="task1", due_at=None)
        task.save()

        self.assertFalse(task.is_overdue(current))


class TodoViewTestCase(TestCase):
    def test_index_get(self):
        client = Client()
        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "todo/index.html")
        self.assertEqual(len(response.context["tasks"]), 0)

    def test_index_post(self):
        client = Client()
        data = {"title": "Test Task", "due_at": "2024-06-30 23:59:59"}
        response = client.post("/", data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "todo/index.html")
        self.assertEqual(len(response.context["tasks"]), 1)

    def test_index_get_order_post(self):
        task1 = Task(title="task1", due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task1.save()
        task2 = Task(title="task2", due_at=timezone.make_aware(datetime(2024, 8, 1)))
        task2.save()
        client = Client()
        response = client.get("/?order=post")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "todo/index.html")
        self.assertEqual(response.context["tasks"][0], task2)
        self.assertEqual(response.context["tasks"][1], task1)

    def test_index_get_order_priority(self):
        task_low = Task(title="task-low", priority=Task.PRIORITY_LOW)
        task_low.save()
        task_high = Task(title="task-high", priority=Task.PRIORITY_HIGH)
        task_high.save()
        task_med = Task(title="task-med", priority=Task.PRIORITY_MEDIUM)
        task_med.save()
        client = Client()
        response = client.get("/?order=priority")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "todo/index.html")
        self.assertEqual(list(response.context["tasks"]), [task_high, task_med, task_low])

    def test_index_get_order_due(self):
        task1 = Task(title="task1", due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task1.save()
        task2 = Task(title="task2", due_at=timezone.make_aware(datetime(2024, 8, 1)))
        task2.save()
        client = Client()
        response = client.get("/?order=due")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "todo/index.html")
        self.assertEqual(response.context["tasks"][0], task1)
        self.assertEqual(response.context["tasks"][1], task2)

    def test_index_get_favorite_only(self):
        favorite_task = Task(title="favorite", favorite=True)
        favorite_task.save()
        normal_task = Task(title="normal")
        normal_task.save()
        client = Client()
        response = client.get("/?favorite=1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "todo/index.html")
        self.assertEqual(len(response.context["tasks"]), 1)
        self.assertEqual(response.context["tasks"][0], favorite_task)
        self.assertTrue(response.context["show_favorites_only"])

    def test_index_get_search_query_filters_by_title(self):
        target_task = Task(title="Buy milk")
        target_task.save()
        other_task = Task(title="Walk dog")
        other_task.save()
        client = Client()
        response = client.get("/?q=milk")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "todo/index.html")
        self.assertEqual(len(response.context["tasks"]), 1)
        self.assertEqual(response.context["tasks"][0], target_task)

    def test_index_get_search_query_combined_with_favorite_filter(self):
        matching_favorite = Task(title="Milk task", favorite=True)
        matching_favorite.save()
        non_favorite = Task(title="Milk task")
        non_favorite.save()
        unrelated_favorite = Task(title="Bread task", favorite=True)
        unrelated_favorite.save()
        client = Client()
        response = client.get("/?q=Milk&favorite=1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "todo/index.html")
        self.assertEqual(len(response.context["tasks"]), 1)
        self.assertEqual(response.context["tasks"][0], matching_favorite)

    def test_detail_get_shows_favorite_mark(self):
        task = Task(title="task1", favorite=True, due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()
        response = client.get("/{}/".format(task.pk))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "★")

    def test_detail_get_success(self):
        task = Task(title="task1", due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()
        response = client.get("/{}/".format(task.pk))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "todo/detail.html")
        self.assertEqual(response.context["task"], task)

    def test_detail_get_fail(self):
        client = Client()
        response = client.get("/1/")

        self.assertEqual(response.status_code, 404)

    def test_delete_get_success(self):
        task = Task(title="task1", due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()
        response = client.get("/{}/delete".format(task.pk))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())
        self.assertEqual(response.url, "/")

    def test_delete_get_fail(self):
        client = Client()
        response = client.get("/1/delete")

        self.assertEqual(response.status_code, 404)

    def test_update_post_success(self):
        task = Task(title="task1", due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()
        data = {"title": "Updated Task", "due_at": "2024-07-02 12:00:00"}
        response = client.post("/{}/update".format(task.pk), data)

        self.assertEqual(response.status_code, 302)
        updated_task = Task.objects.get(pk=task.pk)
        self.assertEqual(updated_task.title, "Updated Task")
        self.assertEqual(updated_task.due_at, timezone.make_aware(datetime(2024, 7, 2, 12, 0, 0)))

    def test_update_post_fail(self):
        client = Client()
        data = {"title": "Updated Task", "due_at": "2024-07-02 12:00:00"}
        response = client.post("/1/update", data)

        self.assertEqual(response.status_code, 404)

    def test_finish_post_success(self):
        task = Task(title="task1", due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()
        response = client.post("/{}/finish".format(task.pk))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Task.objects.get(pk=task.pk).completed)
        self.assertEqual(response.url, "/{}/".format(task.pk))

    def test_favorite_post_toggle_success(self):
        task = Task(title="task1", due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()

        response = client.post("/{}/favorite".format(task.pk))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Task.objects.get(pk=task.pk).favorite)
        self.assertEqual(response.url, "/{}/".format(task.pk))

        response = client.post("/{}/favorite".format(task.pk))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Task.objects.get(pk=task.pk).favorite)
