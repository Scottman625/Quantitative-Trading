# Generated by Django 4.1.2 on 2022-12-08 12:43

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stockCore', '0004_remove_stockrecord_change_remove_stockrecord_dir_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserStock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('buy_at', models.DateTimeField(blank=True, null=True)),
                ('bid_volume', models.DecimalField(decimal_places=0, max_digits=13)),
                ('amount', models.IntegerField(default=0, null=True)),
                ('bid_price', models.DecimalField(decimal_places=2, max_digits=7)),
                ('cost', models.DecimalField(decimal_places=2, max_digits=13)),
                ('is_cover', models.BooleanField(default=False)),
                ('profit', models.DecimalField(decimal_places=2, max_digits=13)),
                ('stock', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stockCore.stock')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserStockTrade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sell_at', models.DateTimeField(blank=True, null=True)),
                ('sell_volume', models.DecimalField(decimal_places=0, max_digits=13)),
                ('amount', models.IntegerField(default=0, null=True)),
                ('sell_money', models.DecimalField(decimal_places=2, max_digits=7)),
                ('price', models.DecimalField(decimal_places=2, max_digits=13)),
                ('profit', models.DecimalField(decimal_places=2, max_digits=13)),
                ('userstock', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stockCore.userstock')),
            ],
        ),
        migrations.CreateModel(
            name='StockDayRecommend',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('type', models.CharField(blank=True, choices=[('0', 'ChildParent'), ('1', 'LongShadeLine')], max_length=100, null=True)),
                ('stock', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stockCore.stock')),
            ],
        ),
    ]
