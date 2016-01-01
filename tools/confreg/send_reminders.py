#!/usr/bin/env python

#
# Send reminders to speakers and attendees that have their
# sessions or registration in an unconfirmed state.
#
# Intended to run on a daily basis, as each reminder has it's
# own check for when the user was last notified.
#

import sys
import os
from StringIO import StringIO
from datetime import datetime, timedelta

# Set up to run in django environment
from django.core.management import setup_environ
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), '../../postgresqleu'))
import settings
setup_environ(settings)

from django.db import transaction
from django.template import Context
from django.template.loader import get_template

from postgresqleu.mailqueue.util import send_simple_mail

from postgresqleu.confreg.models import Conference, Speaker, ConferenceSession
from postgresqleu.confreg.models import ConferenceRegistration

def remind_pending_speakers(whatstr, conference):
	# Remind speakers that are in pending status. But only the ones
	# where we've actually sent the status emails, meaning the
	# lastsent is the same as the current.
	speakers = Speaker.objects.filter(conferencesession__conference=conference,
									  conferencesession__status=3,
									  conferencesession__lastnotifiedstatus=3,
									  conferencesession__lastnotifiedtime__lt=datetime.now()-timedelta(days=7)).distinct()
	if speakers:
		whatstr.write("Found {0} unconfirmed talks:\n".format(len(speakers)))
		template = get_template('confreg/mail/speaker_remind_confirm.txt')

		for speaker in speakers:
			sessions = speaker.conferencesession_set.filter(conference=conference, status=3)
			for s in sessions:
				s.lastnotifiedtime = datetime.now()
				s.save()

			send_simple_mail(conference.contactaddr,
							 speaker.user.email,
							 "Your submissions to {0}".format(conference),
							 template.render(Context({
								 'conference': conference,
								 'sessions': sessions,
								 'SITEBASE': settings.SITEBASE_SSL,
							 })),
							 sendername = conference.conferencename,
							 receivername = speaker.fullname,
						 )

			whatstr.write(u"Reminded speaker {0} to confirm {1} talks\n".format(speaker, len(sessions)))

		whatstr.write("\n\n")


def remind_unregistered_speakers(whatstr, conference):
	# Get speakers that are approved but not registered
	speakers = list(Speaker.objects.raw("SELECT s.* FROM confreg_speaker s WHERE EXISTS (SELECT 1 FROM confreg_conferencesession sess INNER JOIN confreg_conferencesession_speaker css ON css.conferencesession_id=sess.id WHERE sess.conference_id=%s AND css.speaker_id=s.id AND sess.status=1 AND sess.lastnotifiedtime<%s) AND NOT EXISTS (SELECT 1 FROM confreg_conferenceregistration r WHERE r.conference_id=%s AND r.attendee_id=s.user_id AND r.payconfirmedat IS NOT NULL)",
										[conference.id, datetime.now()-timedelta(days=7), conference.id]))
	if speakers:
		whatstr.write("Found {0} unregistered speakers:\n".format(len(speakers)))
		template = get_template('confreg/mail/speaker_remind_register.txt')
		for speaker in speakers:
			# Update the last notified date on all sessions that are in
			# status approved, to make sure we don't send a second
			# reminder tomorrow.
			ConferenceSession.objects.filter(conference=conference,
											 speaker=speaker,
											 status=1
			).update(
				lastnotifiedtime=datetime.now()
			)

			send_simple_mail(conference.contactaddr,
							 speaker.user.email,
							 "Your registration to {0}".format(conference),
							 template.render(Context({
								 'conference': conference,
								 'SITEBASE': settings.SITEBASE_SSL,
							 })),
							 sendername = conference.conferencename,
							 receivername = speaker.fullname,
						 )

			whatstr.write(u"Reminded speaker {0} to register\n".format(speaker))

		whatstr.write("\n\n")


def remind_pending_registrations(whatstr, conference):
	# Get registrations made which have no invoice, no bulk registration,
	# and are not completed. We look at registrations created more than 5
	# days ago and also unmodified for 5 days. This is intentionally not 7
	# days in order to "rotate the day of week" the reminders go out on.
	regs = ConferenceRegistration.objects.filter(conference=conference,
												 payconfirmedat__isnull=True,
												 invoice__isnull=True,
												 bulkpayment__isnull=True,
												 registrationwaitlistentry__isnull=True,
												 created__lt=datetime.now()-timedelta(days=5),
												 lastmodified__lt=datetime.now()-timedelta(days=5))

	if regs:
		whatstr.write("Found {0} unconfirmed registrations that are stalled:\n".format(len(regs)))
		template = get_template('confreg/mail/attendee_stalled_registration.txt')
		for reg in regs:
			send_simple_mail(conference.contactaddr,
							 reg.email,
							 "Your registration to {0}".format(conference),
							 template.render(Context({
								 'conference': conference,
								 'reg': reg,
								 'SITEBASE': settings.SITEBASE_SSL,
							 })),
							 sendername = conference.conferencename,
							 receivername = reg.fullname,
						 )
			reg.lastmodified = datetime.now()
			reg.save()

			whatstr.write(u"Reminded attendee {0} that their registration is not confirmed\n".format(reg.fullname))

		whatstr.write("\n\n")

def remind_empty_submissions(whatstr, conference):
	# Get all sessions with empty abstract (they forgot to hit save), if they have not been touched in
	# 3 days (this will also make the reminder show up every 3 days, and not every day, since we touch
	# the lastmodified timestemp when a reminder is sent).

	template = get_template('confreg/mail/speaker_empty_submission.txt')

	for sess in conference.conferencesession_set.filter(abstract='',
														lastmodified__lt=datetime.now()-timedelta(days=3)):
		for spk in sess.speaker.all():
			send_simple_mail(conference.contactaddr,
							 spk.email,
							 "Your submission to {0}".format(conference),
							 template.render(Context({
								 'conference': conference,
								 'session': sess,
								 'SITEBASE': settings.SITEBASE_SSL,
							 })),
							 sendername = conference.conferencename,
							 receivername = spk.name,
						 )
			whatstr.write(u"Reminded speaker {0} that they have made an empty submission\n".format(spk.name))
		sess.lastmodified = datetime.now()
		sess.save()


if __name__ == "__main__":
	for conference in Conference.objects.filter(active=True):
		# One transaction for each open conference that has registration
		# open. If registration isn't open then there is nowhere to
		# register, so don't even try.
		with transaction.commit_on_success():
			whatstr = StringIO()

			if conference.registrationtype_set.filter(specialtype='spk').exists():
				remind_pending_speakers(whatstr, conference)
				remind_unregistered_speakers(whatstr, conference)

			remind_pending_registrations(whatstr, conference)

			# Do we need to send a central mail?
			if whatstr.tell():
				# More than one character, so we have done something. Send
				# a report to the conference organizers about it.
				send_simple_mail(conference.contactaddr,
								 conference.contactaddr,
								 "Reminders sent",
								 whatstr.getvalue(),
								 sendername = conference.conferencename,
								 receivername = conference.conferencename,
								 )

	for conference in Conference.objects.filter(callforpapersopen=True):
		# One transaction for each conference with call for papers open, to send reminders
		# for things related to the cfp.
		with transaction.commit_on_success():
			whatstr = StringIO()
			remind_empty_submissions(whatstr, conference)

			if whatstr.tell():
				send_simple_mail(conference.contactaddr,
								 conference.contactaddr,
								 "CfP reminders sent",
								 whatstr.getvalue(),
								 sendername = conference.conferencename,
								 receivername = conference.conferencename,
							 )