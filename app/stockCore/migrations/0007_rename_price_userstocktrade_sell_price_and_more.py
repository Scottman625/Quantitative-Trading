# Generated by Django 4.1.2 on 2022-12-09 07:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stockCore', '0006_kbarstype_alter_stockdayrecommend_type'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userstocktrade',
            old_name='price',
            new_name='sell_price',
        ),
        migrations.RemoveField(
            model_name='userstocktrade',
            name='amount',
        ),
    ]
