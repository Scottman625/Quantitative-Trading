# Generated by Django 4.1.2 on 2022-12-27 05:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stockCore', '0015_stockrecord_dif_stockrecord_ema_12_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='n_font_type_stock',
            name='red_sign_start_at',
            field=models.DateField(blank=True, null=True),
        ),
    ]