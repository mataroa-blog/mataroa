# Generated by Django 4.1.5 on 2023-05-18 00:45

import django.contrib.postgres.indexes
import django.contrib.postgres.search
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0086_alter_user_blog_byline"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="search_post",
            field=django.contrib.postgres.search.SearchVectorField(
                blank=True, null=True
            ),
        ),
        migrations.AddIndex(
            model_name="post",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["search_post"], name="main_post_search__b3a77b_gin"
            ),
        ),
    ]
