# Generated by Django 4.1.2 on 2022-12-06 04:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stockCore', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
