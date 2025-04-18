# Generated by Django 2.2 on 2022-04-12 21:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('callcenter', '0132_auto_20220214_1157'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calldetail',
            name='session_uuid',
            field=models.UUIDField(db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='campaignschedule',
            name='except_type',
            field=models.CharField(blank=True, choices=[('1', 'Select'), ('3', 'Outbound')], default='', max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='holidays',
            name='except_type',
            field=models.CharField(choices=[('1', 'Select'), ('3', 'Outbound')], default='', max_length=10),
        ),
       # migrations.AlterField(
        #    model_name='uservariable',
         #   name='domain',
          #  field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user_switch', to='callcenter.Switch'),
          #),
    ]
