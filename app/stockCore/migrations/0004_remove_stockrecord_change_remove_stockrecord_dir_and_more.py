# Generated by Django 4.1.2 on 2022-12-06 22:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stockCore', '0003_alter_stockrecord_transaction'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stockrecord',
            name='Change',
        ),
        migrations.RemoveField(
            model_name='stockrecord',
            name='Dir',
        ),
        migrations.RemoveField(
            model_name='stockrecord',
            name='FinalBuyPrice',
        ),
        migrations.RemoveField(
            model_name='stockrecord',
            name='FinalBuyVolume',
        ),
        migrations.RemoveField(
            model_name='stockrecord',
            name='FinalSellPrice',
        ),
        migrations.RemoveField(
            model_name='stockrecord',
            name='FinalSellVolume',
        ),
        migrations.RemoveField(
            model_name='stockrecord',
            name='Transaction',
        ),
        migrations.RemoveField(
            model_name='stockrecord',
            name='TurnOver',
        ),
    ]
