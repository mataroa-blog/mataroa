# Generated by Django 4.2.4 on 2023-08-12 16:02

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0086_alter_user_blog_byline"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="is_approved",
            field=models.BooleanField(default=False),
        ),
    ]
