# Generated manually to add the favorite flag to Task.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("todo", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="favorite",
            field=models.BooleanField(default=False),
        ),
    ]