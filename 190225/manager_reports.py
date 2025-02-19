from datetime import datetime, timedelta
from django.conf import settings
from django.db import transaction
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from django.db import connections
from callcenter.models import (Campaign)
from crm.models import DownloadReports
from callcenter.utility import (download_call_detail_report, download_agent_perforance_report, campaignwise_performance_report, 
	download_agent_mis, download_agent_activity_report, download_campaignmis_report, download_callbackcall_report,
	download_abandonedcall_report,set_download_progress_redis, download_call_recordings, download_contactinfo_report, download_phonebookinfo_report,
	download_billing_report, DownloadCssQuery, download_call_recording_feedback_report,download_management_performance_report,download_alternate_contact_report, download_ic_report,
	download_lan_report)

ENABLE = False
job_defaults = {
	'coalesce': True,
	'max_instances': 15
}
sched = BlockingScheduler()
sched.configure(job_defaults=job_defaults)
CAMPAIGNS={}
  
def generate_report():
	""" Downloading the reports """

	data = DownloadReports.objects.filter(is_start=False, status=True).distinct('user').order_by('user','start_date')
	print(data)
	for i in data:

		if not DownloadReports.objects.filter(is_start=True, user=i.user):
			i.status = False
			i.is_start = True
			i.save()
			set_download_progress_redis(i.id,0)
			if i.report=='Call Details':
				print(i.report,'thi is')
				download_call_detail_report(filters=i.filters, user=i.user, col_list=i.col_list, serializer_class=i.serializers, download_report_id=i.id)
			if i.report=='Agent Performance':
				download_agent_perforance_report(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
			if i.report=='Campaign Wise Performance':
				campaignwise_performance_report(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
			if i.report=='Agent Mis Report':
				download_agent_mis(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
			if i.report=='Agent Activity':
				download_agent_activity_report(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
			if i.report=='Campaign Mis':
				download_campaignmis_report(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
			if i.report=='CallBack':
				download_callbackcall_report(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
			if i.report=='Abandoned Call':
				download_abandonedcall_report(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
			if i.report=='Call Recordings':
				download_call_recordings(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
			if i.report=='Contact Info':
				download_contactinfo_report(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
			if i.report=='Billing Report':
				download_billing_report(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
			if i.report=='Css Query':
				DownloadCssQuery(filters=i.filters, user=i.user, download_report_id=i.id)
			if i.report=='call recording feedback':
				download_call_recording_feedback_report(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
			if i.report=='Alternate Contact':
				download_alternate_contact_report(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
			if i.report == 'Management Performance':
				download_management_performance_report(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
			if i.report == 'Lan Report':
				download_lan_report(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
			if i.report == 'IC4 Report':
				download_ic_report(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
			if "Lead List" in i.report:
				download_phonebookinfo_report(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)


def set_pb_campaign_status():
	""" setting true all the pb campaigns in redis"""
	try:
		campaign = Campaign.objects.values('id','name')
		for camp in campaign:
			settings.R_SERVER.hset("pb_campaign_status",camp['id'], True)
		print('all campaign set to true in redis for progressive')
	except Exception as e:
		print('exception set_pb_campaign_status',e)
	finally:
		transaction.commit()
		connections["default"].close()

def Execute():
	"""
	Start APSchedular for autodialing.
	"""
	global ENABLE
	sched.add_jobstore(MemoryJobStore(), 'list')
	set_pb_campaign_status()
	execution_time = datetime.now() + timedelta(minutes=0.1)
	sched.add_job(generate_report,'interval', seconds=5, start_date=execution_time,
						   id='generate_report', jobstore='list')
	print(sched.state)
	if sched.state == 0:
		sched.start()

if __name__ == '__main__':
	Execute()
