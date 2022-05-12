# Generated by Django 4.0.4 on 2022-05-11 13:37

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Simulation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('priority_group', models.IntegerField()),
                ('fee_rate', models.FloatField(default=0)),
                ('estimated_waiting_time', models.FloatField(default=0)),
            ],
        ),
    ]