# Generated by Django 3.2 on 2022-10-26 18:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('apis_entities', '0004_auto_20200722_1231'),
        ('dubletten_tool', '0002_dublettenlog'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ampel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note', models.TextField(blank=True, max_length=2000, null=True)),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='apis_entities.person')),
            ],
        ),
    ]