# Generated by Django 3.1.14 on 2022-05-17 06:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('apis_entities', '0004_auto_20200722_1231'),
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=600)),
                ('status', models.CharField(choices=[('unchecked', 'unchecked'), ('checked group', 'checked group'), ('checked for other groups', 'checked for other groups'), ('checked all members', 'checked all members'), ('ready to merge', 'ready to merge'), ('merged', 'merged')], default='unchecked', max_length=300)),
                ('_gender', models.CharField(blank=True, max_length=255, null=True)),
                ('marked', models.BooleanField(default=False)),
                ('note', models.TextField(blank=True, max_length=2000, null=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='PersonProxy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('candidate', 'Candidate'), ('single', 'Single'), ('merged', 'Merged')], default='single', max_length=300)),
                ('marked', models.BooleanField(default=False)),
                ('note', models.TextField(blank=True, max_length=2000, null=True)),
                ('_names', models.JSONField(null=True)),
                ('_first_names', models.JSONField(null=True)),
                ('person', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='apis_entities.person')),
            ],
            options={
                'ordering': ['person__name'],
            },
        ),
        migrations.CreateModel(
            name='StatusButtonGroupType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=600)),
                ('short', models.CharField(default='BT', max_length=4)),
            ],
        ),
        migrations.CreateModel(
            name='StatusButtonProxyType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=600)),
            ],
        ),
        migrations.CreateModel(
            name='Suggestions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.JSONField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='StatusButtonProxy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.BooleanField(default=False)),
                ('kind', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dubletten_tool.statusbuttonproxytype')),
                ('related_instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dubletten_tool.personproxy')),
            ],
        ),
        migrations.CreateModel(
            name='StatusButtonGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.BooleanField(default=False)),
                ('kind', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dubletten_tool.statusbuttongrouptype')),
                ('related_instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dubletten_tool.group')),
            ],
        ),
        migrations.AddField(
            model_name='group',
            name='members',
            field=models.ManyToManyField(blank=True, to='dubletten_tool.PersonProxy'),
        ),
    ]