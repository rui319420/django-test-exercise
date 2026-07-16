from django.db import models
from django.utils import timezone


# Create your models here.
class Group(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
    
class Task(models.Model):
    PRIORITY_LOW = 0
    PRIORITY_MEDIUM = 1
    PRIORITY_HIGH = 2
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
    ]

    title = models.CharField(max_length=100)
    tags = models.CharField(max_length=255, blank=True, default="")
    completed = models.BooleanField(default=False)
    favorite = models.BooleanField(default=False)
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    posted_at = models.DateTimeField(default=timezone.now)
    due_at = models.DateTimeField(null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)

    def is_overdue(self, dt):
        if self.due_at is None:
            return False
        return self.due_at < dt
