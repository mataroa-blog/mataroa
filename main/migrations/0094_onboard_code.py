# Generated by Django 4.2.7 on 2023-11-09 21:11

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0093_alter_onboard_problems_alter_onboard_quality"),
    ]

    operations = [
        migrations.AddField(
            model_name="onboard",
            name="code",
            field=models.UUIDField(default=uuid.uuid4, null=True),
        ),
    ]
