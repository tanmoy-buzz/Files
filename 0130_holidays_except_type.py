# Generated by Django 2.2 on 2022-02-08 17:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('callcenter', '0129_auto_20220208_1619'),
    ]

    operations = [
        migrations.AddField(
            model_name='holidays',
            name='except_type',
            field=models.CharField(choices=[('1', 'NoSelect'), ('2', 'Inbound'), ('3', 'Outbound')], default='', max_length=10),
        ),
    ]
