# Generated by Django 3.0.7 on 2020-06-08 21:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0021_image_slug"),
    ]

    operations = [
        migrations.AlterField(
            model_name="image",
            name="slug",
            field=models.CharField(max_length=300, unique=True),
        ),
    ]
