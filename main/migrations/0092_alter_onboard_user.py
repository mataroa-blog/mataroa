# Generated by Django 4.2.7 on 2023-11-09 20:07

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0091_onboard_created_at"),
    ]

    operations = [
        migrations.AlterField(
            model_name="onboard",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
