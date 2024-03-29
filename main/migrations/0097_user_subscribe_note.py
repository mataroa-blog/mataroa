# Generated by Django 5.0.1 on 2024-01-03 16:34

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0096_auto_20231109_2111"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="subscribe_note",
            field=models.TextField(
                blank=True,
                default="Subscribe via [RSS](/rss/) / [via Email](/newsletter/).",
                help_text="Supports markdown. Default: Subscribe via [RSS](/rss/) / [via Email](/newsletter/).",
                null=True,
            ),
        ),
    ]
