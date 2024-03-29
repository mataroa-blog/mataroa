# Generated by Django 5.0.1 on 2024-01-03 16:43

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0097_user_subscribe_note"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="notifications_on",
            field=models.BooleanField(
                default=True,
                help_text="Allow/disallow people subscribing for email newsletter for new posts.",
                verbose_name="Newsletter",
            ),
        ),
    ]
