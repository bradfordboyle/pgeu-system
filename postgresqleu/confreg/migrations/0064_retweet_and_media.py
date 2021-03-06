# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-10-11 14:16
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('confreg', '0063_incoming_tweets'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConferenceIncomingTweetMedia',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sequence', models.IntegerField()),
                ('mediaurl', models.URLField(max_length=1024)),
            ],
        ),
        migrations.AddField(
            model_name='conferenceincomingtweet',
            name='retweetstate',
            field=models.IntegerField(choices=[(0, 'No retweet'), (1, 'Scheduled'), (2, 'Retweeted')], default=0),
        ),
        migrations.AddField(
            model_name='conferenceincomingtweetmedia',
            name='incomingtweet',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='confreg.ConferenceIncomingTweet'),
        ),
    ]
