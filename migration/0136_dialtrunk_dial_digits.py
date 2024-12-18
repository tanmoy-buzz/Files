# Generated by Django 2.2 on 2023-02-21 13:25

from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('callcenter', '0134_auto_20221207_0438'),
    ]

    operations = [
        migrations.AddField(
            model_name='dialtrunk',
            name='dial_digits',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='uservariable',
            name='domain',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user_switch', to='callcenter.Switch'),
        ),
    ]
