# Generated by Django 2.2 on 2022-02-14 11:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('callcenter', '0131_auto_20220208_1752'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calldetail',
            name='session_uuid',
            field=models.UUIDField(db_index=True, null=True, unique=True),
        ),
    ]