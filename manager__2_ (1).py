import sys, os
import pickle
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from django.conf import settings
from django.db import transaction
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from django.db import connections
from callcenter.models import (Campaign,CallDetail,AgentActivity,User,
	CdrFeedbck, CSS, CallBackContact, Abandonedcall,CurrentCallBack,
	Notification,PhonebookBucketCampaign, DiallerEventLog,AdminLogEntry, Switch, DataUploadLog)
from crm.models import Contact,TempContactInfo,Phonebook,DownloadReports, PhoneBookUpload
from django.db.models import Q, Count, F,OuterRef, Subquery
from callcenter.utility import (get_current_users, download_call_detail_report, download_agent_perforance_report, campaignwise_performance_report, 
	download_agent_mis, download_agent_activity_report, download_campaignmis_report, download_callbackcall_report,
	download_abandonedcall_report,set_download_progress_redis, download_call_recordings, download_contactinfo_report, download_phonebookinfo_report,
	download_billing_report, camp_list_users, DownloadCssQuery, download_call_recording_feedback_report,download_management_performance_report,download_alternate_contact_report, download_ic_report,
	download_lan_report, freeswicth_server)
from dialer.dialersession import fs_administration_hangup
ENABLE = False
job_defaults = {
	'coalesce': True,
	'max_instances': 15
}
sched = BlockingScheduler()
sched.configure(job_defaults=job_defaults)
CAMPAIGNS={}

def return_last_activity(user,select_cols):
	start_of_today = datetime.strptime(str(date.today()) + " 00:00:00", "%Y-%m-%d %H:%M:%S")
	return AgentActivity.objects.filter(event_time__gte=start_of_today,user=user).values(*select_cols).first()

def create_tempcontact_data(contacts, status, keep_user_none=False):
	""" Creating the Temp contact info without portfolio"""
	try:
		if len(contacts) != 0:
			data_list = []
			temp_contact_ids = set(TempContactInfo.objects.values_list('id',flat=True))
			for contact in contacts:
#				print('contact of id----------',contact.id)
				if contact.id not in temp_contact_ids:
					print('----------***********--id-------------',contact.id,'------campaign--------',contact.campaign,'---phonebook-------',contact.phonebook,'--numeric---',contact.numeric,'---alt---',contact.alt_numeric,'----priority--',contact.priority)
					uniqueval=None
					if isinstance(contact,dict):
						uniqueval=contact.get("uniqueid")
					else:
						uniqueval=getattr(contact,"uniqueid",None)
					if uniqueval is not None:
						print('========uniqueval------',uniqueval)
					if keep_user_none:
						data_list.append(TempContactInfo(id =contact.id, campaign=contact.campaign,phonebook=contact.phonebook,
							user=None, numeric=contact.numeric,alt_numeric=contact.alt_numeric,status='NotDialed',
							contact_id=contact.id,priority=contact.priority,uniqueid=uniqueval, previous_status=contact.status))
					else:
						data_list.append(TempContactInfo(id =contact.id, campaign=contact.campaign,phonebook=contact.phonebook,
							user=contact.user, numeric=contact.numeric,alt_numeric=contact.alt_numeric,status='NotDialed',
							contact_id=contact.id,priority=contact.priority,uniqueid=uniqueval, previous_status=contact.status))
					contact.status=status
					contact.modified_date = datetime.now()
			print('4444444---------',len(data_list),'------',len(contacts))
			if len(data_list)>0 and contacts:
				TempContactInfo.objects.bulk_create(data_list,ignore_conflicts=True)
				Contact.objects.bulk_update(contacts,['status','modified_date'])
	except Exception as e:
		print("Exception occures from create_tempcontact_data",e)
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print(exc_type, fname, exc_tb.tb_lineno)
	finally:
		transaction.commit()
		connections["crm"].close()
		connections["default"].close()
 
def create_tempcontact_data_with_pandas(contacts, status, keep_user_none=False):
	""" Creating the Temp contact info with portfolio"""
	try:
		data_list = []
		temp_contact_ids = list(TempContactInfo.objects.values_list('id',flat=True))
		contacts = contacts.where(pd.notnull(contacts), None)
		for index,contact in contacts.iterrows():
			if contact.contact_id not in temp_contact_ids:
				if keep_user_none:
					data_list.append(TempContactInfo(id =contact.contact_id, campaign=contact.campaign,phonebook_id=contact.phonebook_id,
						user=None, numeric=contact.numeric,alt_numeric=contact.alt_numeric,status='NotDialed',
						contact_id=contact.contact_id,priority=contact.priority,uniqueid=contact.uniqueid, previous_status=contact.status))
				else:
					data_list.append(TempContactInfo(id =contact.contact_id, campaign=contact.campaign,phonebook_id=contact.phonebook_id,
						user=contact.user, numeric=contact.numeric,alt_numeric=contact.alt_numeric,status='NotDialed',
						contact_id=contact.contact_id,priority=contact.priority,uniqueid=contact.uniqueid, previous_status=contact.status))
		TempContactInfo.objects.bulk_create(data_list)
		Contact.objects.filter(id__in=contacts['contact_id'].tolist()).update(status=status,modified_date=datetime.now())
	except Exception as e:
		print("Exception occures from create_tempcontact_data",e)
	finally:
		transaction.commit()
		connections["crm"].close()
		connections["default"].close()

def fetch_callback_contact(campaign,fetch_count):
	""" fetching the callback contacts and displaying to the user"""
	try:
		if campaign['auto_qcb_dial']:
			callback_contact = CallBackContact.objects.filter(Q(campaign=campaign['name'], schedule_time__lte = datetime.now(), 
				callback_type='queue'),Q(user=None)|Q(user=''))
			c_unique_numbers = callback_contact.order_by('numeric','id').distinct('numeric').values('id','contact_id','numeric')[:fetch_count]
			if c_unique_numbers:
				cb_contact_list = Contact.objects.none()
				for cb_contact in c_unique_numbers:
					if cb_contact['contact_id']:
						cb_contact_list = cb_contact_list | Contact.objects.filter(id=cb_contact['contact_id'])
					else:
						contact = Contact.objects.filter(campaign=campaign['name'], numeric=cb_contact['numeric']).order_by('-id')[:1]
						if contact.exists():
							cb_contact_list = cb_contact_list | contact
						elif Contact.objects.filter(campaign=campaign['name'], alt_numeric=cb_contact['numeric']).exists():
							contact = Contact.objects.filter(alt_numeric=cb_contact['numeric']).order_by('-id')[:1]
							cb_contact_list = cb_contact_list | contact
						else:
							crt_contact = Contact.objects.create(numeric=cb_contact['numeric'],campaign=campaign['name'],customer_raw_data={})
							contact = Contact.objects.filter(id=crt_contact.id)
							cb_contact_list = cb_contact_list | contact
					current_cb = CurrentCallBack.objects.filter(callbackcontact_id=cb_contact['id'])
					noti_id = current_cb.values_list('notification_id',flat=True)
					Notification.objects.filter(id__in=noti_id).delete()
					current_cb.delete()
					fetch_count -= 1
					callback_contact.filter(numeric=cb_contact['numeric']).delete()
				create_tempcontact_data(cb_contact_list,'Queued-Callback', True)
		if fetch_count >= 1:
			if campaign['auto_ac_dial']:
				auto_ac_contact = Abandonedcall.objects.filter(Q(campaign=campaign['name']),Q(user=None)|Q(user=''))
				a_unique_numbers = auto_ac_contact.order_by('numeric','id').distinct('numeric').values_list('numeric',flat=True)[:fetch_count]
				if a_unique_numbers:
					ac_contact_list = Contact.objects.none()
					for num in a_unique_numbers:
						contact = Contact.objects.filter(campaign=campaign['name'], numeric=num).order_by('-id')[:1]
						if contact.exists():
							ac_contact_list = ac_contact_list | contact
						elif Contact.objects.filter(campaign=campaign['name'], alt_numeric=num).exists():
							contact = Contact.objects.filter(alt_numeric=num).order_by('-id')[:1]
							ac_contact_list = ac_contact_list | contact
						else:
							crt_contact = Contact.objects.create(numeric=num,campaign=campaign['name'],customer_raw_data={})
							contact = Contact.objects.filter(id=crt_contact.id)
							ac_contact_list = ac_contact_list | contact
						Notification.objects.filter(Q(numeric = num, notification_type = "campaign_abandonedcall"),Q(user=None)|Q(user='')).delete()
						fetch_count -= 1
						auto_ac_contact.filter(numeric=num).delete()
					create_tempcontact_data(ac_contact_list,'Queued-Abandonedcall', True)
		return fetch_count
	except Exception as e:
		print("Exception occures from fetch_callback_contact",e)
	finally:
		transaction.commit()
		connections["crm"].close()
		connections["default"].close()
  
# def generate_report():
# 	""" Downloading the reports """

# 	data = DownloadReports.objects.filter(is_start=False, status=True).distinct('user').order_by('user','start_date')
# 	print(data)
# 	for i in data:

# 		if not DownloadReports.objects.filter(is_start=True, user=i.user):
# 			i.status = False
# 			i.is_start = True
# 			i.save()
# 			set_download_progress_redis(i.id,0)
# 			if i.report=='Call Details':
# 				print(i.report,'thi is')
# 				download_call_detail_report(filters=i.filters, user=i.user, col_list=i.col_list, serializer_class=i.serializers, download_report_id=i.id)
# 			if i.report=='Agent Performance':
# 				download_agent_perforance_report(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
# 			if i.report=='Campaign Wise Performance':
# 				campaignwise_performance_report(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
# 			if i.report=='Agent Mis Report':
# 				download_agent_mis(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
# 			if i.report=='Agent Activity':
# 				download_agent_activity_report(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
# 			if i.report=='Campaign Mis':
# 				download_campaignmis_report(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
# 			if i.report=='CallBack':
# 				download_callbackcall_report(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
# 			if i.report=='Abandoned Call':
# 				download_abandonedcall_report(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
# 			if i.report=='Call Recordings':
# 				download_call_recordings(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
# 			if i.report=='Contact Info':
# 				download_contactinfo_report(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
# 			if i.report=='Billing Report':
# 				download_billing_report(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
# 			if i.report=='Css Query':
# 				DownloadCssQuery(filters=i.filters, user=i.user, download_report_id=i.id)
# 			if i.report=='call recording feedback':
# 				download_call_recording_feedback_report(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
# 			if i.report=='Alternate Contact':
# 				download_alternate_contact_report(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
# 			if i.report == 'Management Performance':
# 				download_management_performance_report(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
# 			if i.report == 'Lan Report':
# 				download_lan_report(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
# 			if i.report == 'IC4 Report':
# 				download_ic_report(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)
# 			if "Lead List" in i.report:
# 				download_phonebookinfo_report(filters=i.filters, user=i.user, col_list=i.col_list,download_report_id=i.id)

def phonebook_data_bucket():
	"""
	This function is use to reach the campaign hopper level of contacts in tempcontact_info table. 
	"""
	try:
		order_campaigns = list(PhonebookBucketCampaign.objects.raw("select * from callcenter_phonebookbucketcampaign where is_contact = True order by agent_login_count DESC"))
		for camp in order_campaigns:
			campaign = Campaign.objects.filter(id=camp.id, status="Active").values('id','name','hopper_level','css','auto_qcb_dial','auto_ac_dial','dial_method','portifolio').first()
			if campaign:
			# if campaign['portifolio']:
				pb_campaigns = settings.R_SERVER.hget("pb_campaign_status",campaign['id'])
				if not pb_campaigns or pb_campaigns.decode('utf-8') == 'True':
					settings.R_SERVER.hset("pb_campaign_status",campaign['id'], False)
					temp_data_count = TempContactInfo.objects.filter(campaign=campaign['name'], status="NotDialed").count()
					phonebook_list = Phonebook.objects.filter(campaign=campaign['id'],status='Active').order_by('priority')
					if campaign['hopper_level'] and (temp_data_count <= int(campaign['hopper_level']) or campaign['portifolio']):
						fetch_data_count = int(campaign['hopper_level']) - int(temp_data_count)
						if fetch_data_count >= 1:
							if campaign['auto_qcb_dial'] or campaign['auto_ac_dial']:
								fetch_data_count = fetch_callback_contact(campaign,fetch_data_count)
						if fetch_data_count >= 1 or campaign['portifolio']:
							if campaign['css']: 
								camp_css = CSS.objects.filter(campaign=campaign['name'],status='Active')
								if camp_css.exists():
									css_query = sorted(camp_css.first().raw_query, key = lambda i: i['priority'])
									if campaign['portifolio']:
										camp_users = camp_list_users(campaign['name'])
										usernames = User.objects.filter(id__in=camp_users, is_active=True).values_list('username',flat=True)
										if len(camp_users) > campaign['hopper_level']:
											campaign['hopper_level'] = len(camp_users)
										count = usernames.count()
										data_count = 0
										if count>0:
											data_count = round(campaign['hopper_level']/count)
										default_hopper = {ext:data_count for ext in usernames}
										temp_hopper_count = list(TempContactInfo.objects.filter(campaign=campaign['name']).values('user').annotate(user_count=Count('user')))
										temp_hopper_count = {v['user']:v['user_count'] for v in temp_hopper_count}
										non_portfolio_count = 0
										if '' in temp_hopper_count:
											non_portfolio_count = temp_hopper_count.pop('')
										if temp_hopper_count:
											user_hopper_fetch_count = {s:(data_count-v if v<=data_count else 0) for s,v in temp_hopper_count.items()}
											default_hopper.update(user_hopper_fetch_count)
										default_hopper = {key:val for key,val in default_hopper.items() if data_count>=val>0}
										for index, c_query in enumerate(css_query):
											if c_query["status"] == "Active":
												contacts_raw = pd.read_sql_query(c_query['query_string'], connections['crm'])
												if not contacts_raw.empty:
													user_data_list = [contacts_raw.loc[contacts_raw.user == x][:m] for x,m in default_hopper.items()]
													if user_data_list:
														new_data = pd.concat(user_data_list)
														if not new_data.empty:
															fetched_count = new_data.groupby('user').size().to_dict()
															default_hopper = { key:(value - fetched_count[key] if key in fetched_count.keys() and value - fetched_count[key]>= 0 else value) for key,value in default_hopper.items()}
															default_hopper = {key:val for key,val in default_hopper.items() if val>0}
															create_tempcontact_data_with_pandas(new_data,'Queued')
															non_hopper_fetch = sum(default_hopper.values()) - non_portfolio_count
															new_data = contacts_raw.loc[contacts_raw.user == ''][:non_hopper_fetch]
															if not new_data.empty:
																non_port_fetch_count = len(new_data)
																update_non_port_count = round(non_port_fetch_count/len(default_hopper.keys()))
																default_hopper = { key:value - update_non_port_count for key,value in default_hopper.items() if value - update_non_port_count >= 0 }
																default_hopper = {key:val for key,val in default_hopper.items() if val>0}
																create_tempcontact_data_with_pandas(new_data,'Queued')
															if not default_hopper:
																break
									else:
										for index, c_query in enumerate(css_query):
											contacts = []
											if c_query["status"] == "Active":
												contacts_raw = Contact.objects.raw(c_query['query_string'] + " limit "+ str(fetch_data_count))
												contacts = list(contacts_raw)
											contacts_count = len(contacts)
											create_tempcontact_data(contacts, 'Queued')	
											if contacts_count > fetch_data_count:
												break
											else:
												fetch_data_count = fetch_data_count - contacts_count
											if index+1 == len(css_query) and fetch_data_count > 0:
												camp.is_contact = False
												camp.save()
								else:
									camp.is_contact = False
									camp.save() 
							else:
								count = len(camp_list_users(campaign['name']))
								phonebook_count = phonebook_list.count()
								if campaign['portifolio']:
									camp_users = camp_list_users(campaign['name'])
									usernames = User.objects.filter(id__in=camp_users, is_active=True).values_list('username',flat=True)
									count = usernames.count()
									if count > campaign['hopper_level']:
										campaign['hopper_level'] = count
									data_count = 0
									if count>0:
										data_count = round(campaign['hopper_level']/count)
									default_hopper = {ext:data_count for ext in usernames}
									temp_hopper_count = list(TempContactInfo.objects.filter(campaign=campaign['name']).values('user').annotate(user_count=Count('user')))
									temp_hopper_count = {v['user']:v['user_count'] for v in temp_hopper_count}
									non_portfolio_count = 0
									if '' in temp_hopper_count:
										non_portfolio_count = temp_hopper_count.pop('')
									if temp_hopper_count:
										user_hopper_fetch_count = {s:(data_count-v if v<=data_count else 0) for s,v in temp_hopper_count.items()}
										default_hopper.update(user_hopper_fetch_count)
									default_hopper = {key:val for key,val in default_hopper.items() if data_count>=val>0}
									for index, phone in enumerate(phonebook_list):
										if phone.order_by in ['Asc','Desc']:
											contacts_raw = pd.read_sql_query("select *, id as contact_id from crm_contact where phonebook_id='%s' and  status='NotDialed' order by id %s, priority"%(phone.id, phone.order_by), connections['crm'])
										else:
											contacts_raw = pd.read_sql_query("select *, id as contact_id from crm_contact where phonebook_id='%s' and status='NotDialed' order by priority"%(phone.id), connections['crm'])
										if not contacts_raw.empty:
											user_data_list = [contacts_raw.loc[contacts_raw.user == x][:m] for x,m in default_hopper.items()]
											if user_data_list:
												new_data = pd.concat(user_data_list)
												if not new_data.empty:
													fetched_count = new_data.groupby('user').size().to_dict()
													default_hopper = { key:(value - fetched_count[key] if key in fetched_count.keys() and value - fetched_count[key]>= 0 else value) for key,value in default_hopper.items()}
													default_hopper = {key:val for key,val in default_hopper.items() if val>0}
													create_tempcontact_data_with_pandas(new_data,'Queued')
													non_hopper_fetch = sum(default_hopper.values()) - non_portfolio_count
													new_data = contacts_raw.loc[contacts_raw.user == ''][:non_hopper_fetch]
													if not new_data.empty:
														non_port_fetch_count = len(new_data)
														update_non_port_count = round(non_port_fetch_count/len(default_hopper.keys()))
														default_hopper = { key:value - update_non_port_count for key,value in default_hopper.items() if value - update_non_port_count >= 0 }
														default_hopper = {key:val for key,val in default_hopper.items() if val>0}
														create_tempcontact_data_with_pandas(new_data,'Queued')
													if not default_hopper:
														break
								else:
									for index, phone in enumerate(phonebook_list):
										order_by = ''
										if phone.order_by == "Asc":
											order_by = "id"
										elif phone.order_by == "Desc":
											order_by = "-id"
										if order_by:
											contacts = phone.contacts.filter(status="NotDialed").order_by(order_by,'priority')[:fetch_data_count]
										else:
											contacts = phone.contacts.filter(status="NotDialed").order_by('?','priority')[:fetch_data_count]
										contacts_count = contacts.count()
										create_tempcontact_data(contacts, 'Queued')	
										if contacts_count > fetch_data_count:
											break
										else:
											fetch_data_count = fetch_data_count - contacts_count
										if index+1 == phonebook_count and fetch_data_count > 0:
											camp.is_contact = False
											camp.save()
					phonebook_ids = list(phonebook_list.values_list('id',flat=True))
					phonebook_ids = list(map(str,phonebook_ids))
					PHONEBOOK_STATUS = pickle.loads(settings.R_SERVER.get("phonebook") or pickle.dumps(PHONEBOOK_STATUS))
					if not set(phonebook_ids) & set(PHONEBOOK_STATUS.keys()):
						settings.R_SERVER.hset("pb_campaign_status",campaign['id'], True)
	except Exception as e:
		settings.R_SERVER.hset("pb_campaign_status",campaign['id'], True)
		print("Exception occures from phonebook_data_bucket",e)
	finally:
		transaction.commit()
		connections["crm"].close()
		connections["default"].close()
  
def create_logout_entry(extension):
	""" Creating the logout entry of the user"""
	try:
		user = User.objects.filter(properties__extension=extension)
		if user.exists():
			user = user.first()
			AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps({}))
			if AGENTS:
				if AGENTS[extension]['screen'] == 'AgentScreen':
					actvity_dict = {}
					actvity_dict['user'] = user
					last_activity = return_last_activity(user,['event_time','event'])
					last_activity_time = last_activity['event_time']
					last_activity_event = last_activity['event']
					now_date = datetime.now()
					time_diff = datetime.strptime(str(now_date - last_activity_time).split('.')[0], '%H:%M:%S').time()
					actvity_dict['event_time'] = now_date
					actvity_dict['tos'] = time_diff
					actvity_dict['event'] = 'Session Expired (Poor Connectivity)'
					actvity_dict['campaign_name'] = last_activity['campaign_name']
					if last_activity_event == 'Start Break':
						actvity_dict['break_time'] = time_diff
						actvity_dict['break_type'] = last_activity['break_type']
					elif last_activity_event in ['Agent-Answered','MANUAL','PROGRESSIVE','PREVIEW','MUTE CALL','RESUME CALL','PARK CALL','Merge Call']:
						actvity_dict['spoke_time'] = time_diff
					elif last_activity_event in ['LOGIN','DIALER LOGOUT']:
						actvity_dict['idle_time'] = time_diff
					else:
						actvity_dict['idle_time'] = time_diff
					AgentActivity(**actvity_dict).save()
					AgentActivity(**{'user':user,'event':'LOGOUT','event_time':now_date}).save()
					print('Logout(Poor Connectivity)')
				else: 
					if user.is_superuser or user.user_role.access_level in ['Admin','Manager','Supervisor']:
						last_event_time = AdminLogEntry.objects.filter(created_by=user,event_type='LOGIN').last()
						if last_event_time:
							log_time = last_event_time.created
							login_activity_time = datetime.now() - log_time
							login_duration_time = (datetime.min + login_activity_time).time()
							AdminLogEntry.objects.create(created_by=user, change_message=user.username+" session experied logout to application",
									action_name='4',event_type='LOGOUT', login_duration=login_duration_time)
	except Exception as e:
		print("create_logout_entry :", e)
	finally:
		transaction.commit()
		connections["crm"].close()
		connections["default"].close()
def session_expire_check():
	""" checking the session expry for an agents"""
	try:
		session_extension = [agent.extension for agent in get_current_users()]
		AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or
					pickle.dumps(AGENTS))
		r_campaigns = pickle.loads(settings.R_SERVER.get("campaign_status") or pickle.dumps(CAMPAIGNS))
		Agents = [i for i,k in AGENTS.items() if 'wfh' not in k or k['wfh'] == False]
		for reddis_ext in Agents:
			if reddis_ext not in session_extension:
				try:
					fs_administration_hangup(AGENTS[reddis_ext]['dialerSession_switch'],uuids=AGENTS[reddis_ext]['dialerSession_uuid'])
				except:
					pass
				create_logout_entry(reddis_ext)
				if AGENTS[reddis_ext]['campaign']:
					campaign=Campaign.objects.get(name=AGENTS[reddis_ext]['campaign'])
					pbc_obj = PhonebookBucketCampaign.objects.filter(id=campaign.id)
					if pbc_obj.exists():
						if pbc_obj.first().agent_login_count > 0:
							pbc_obj.update(agent_login_count=F('agent_login_count')-1)
				updated_agent_dict = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
				del updated_agent_dict[reddis_ext]
				settings.R_SERVER.set("agent_status", pickle.dumps(updated_agent_dict))
				for r_campaign in r_campaigns:
					unique_extensions = list(set(r_campaigns[r_campaign]))
					if reddis_ext in unique_extensions:
						unique_extensions.remove(reddis_ext)
					r_campaigns[r_campaign]=unique_extensions
		settings.R_SERVER.set("campaign_status",pickle.dumps(r_campaigns))
		locked_tmp_data = TempContactInfo.objects.filter(Q(status='Locked')&Q(modified_date__lte = datetime.now() - timedelta(hours=2)))
		if locked_tmp_data:
			locked_tmp_data.update(status="NotDialed")
	except Exception as e:
		print("Exception occures from session_expire_check",e)
	finally:
		transaction.commit()
		connections["crm"].close()
		connections["default"].close()

def create_calldetial_from_diallereventlog(d_obj, uniqueid=None):
	""" will create missing call details from the dialler eventlog"""
	try:
		del d_obj['transfer_history']
		del d_obj['info']
		del d_obj['channel']
		del d_obj['id']
		d_obj["uniqueid"] = uniqueid
		c_obj = CallDetail.objects.create(**d_obj)
		c_obj.hangup_source = 'System'
		c_obj.created = d_obj['created']
		c_obj.updated = d_obj['updated']
		c_obj.save()
		if not CdrFeedbck.objects.filter(session_uuid = d_obj['session_uuid']).exists():
			cdr_feedback = CdrFeedbck.objects.create(feedback={},relation_tag=[],session_uuid=d_obj['session_uuid'],contact_id=d_obj['contact_id'],comment='',calldetail=c_obj)
			if d_obj['dialed_status'] == 'Connected':
				cdr_feedback.primary_dispo = 'AutoFeedback'
				cdr_feedback.save()
	except Exception as e:
		print('Exception from create_calldetial_from_diallereventlog', e)
	finally:
		transaction.commit()
		connections["crm"].close()
		connections["default"].close()

def update_queued_contact():
	""" updating the queued contacts"""
	try:
		time_before_onehr = datetime.now() - timedelta(hours=1)
		tempcontact = TempContactInfo.objects.values_list('contact_id',flat=True)
		contacts = Contact.objects.filter(status='Queued',modified_date__lt=time_before_onehr).exclude(id__in=tempcontact)
		for contact in contacts:
			calldetail = CallDetail.objects.filter(contact_id=contact.id, created__gte=contact.modified_date)
			if not calldetail.exists():
				diallerevent = DiallerEventLog.objects.filter(contact_id=contact.id, created__gte=contact.modified_date)
				if diallerevent.exists():
					if diallerevent.first().created < datetime.now() - timedelta(minutes=15):
						d_obj = diallerevent.values().first()
						if not d_obj['phonebook'] and contact.phonebook:
							d_obj['phonebook'] = contact.phonebook.name
						create_calldetial_from_diallereventlog(d_obj,contact.uniqueid)
						if d_obj['dialed_status'] == 'Connected':
							contact.status = 'Dialed'
						else:
							contact.status = d_obj['dialed_status']
						if diallerevent.first().user:
							contact.last_connected_user = diallerevent.first().user.extension
						contact.last_dialed_date = d_obj.get('init_time', None)
						contact.dial_count = contact.dial_count + 1
						contact.save()
			else:
				if calldetail.first().dialed_status == 'Connected':
					contact.status = 'Dialed'
				else:
					contact.status = calldetail.first().dialed_status
				if calldetail.first().user:
					contact.last_connected_user = calldetail.first().user.extension
				contact.last_dialed_date = calldetail.first().init_time
				contact.dial_count = contact.dial_count + 1
				contact.save()
	except Exception as e:
		print("update_queued_contact :", e)		
	finally:
		transaction.commit()
		connections["crm"].close()
		connections["default"].close()
 
def create_calldetial_missing_contact():
	""" creating the missing calldetails from diallervent log"""
	try:
		half_hour = datetime.now() - timedelta(minutes=30)
		CallDetail.objects.filter(session_uuid=None, created__lt=half_hour, created__date=date.today()).delete()
		# calldetail_session = CallDetail.objects.filter(created__lt=half_hour, created__date=date.today()).exclude(session_uuid=None).values_list('session_uuid',flat=True)
		
		calldetail_session = CallDetail.objects.filter(created__lt=half_hour,created__gte=date.today(),session_uuid=OuterRef('session_uuid')).values('session_uuid')
	
		# diallerlog_entry = DiallerEventLog.objects.filter(created__lt=half_hour, created__date=date.today()).exclude(session_uuid__in=calldetail_session).values()
	
		diallerlog_entry = DiallerEventLog.objects.filter(created__lt=half_hour,created__gte=date.today()).exclude(session_uuid__in=Subquery(calldetail_session)).values()

		for d_obj in diallerlog_entry:
			uniqueid = None
			if 'contact_id' in d_obj and d_obj['contact_id']:
				contact_obj = Contact.objects.filter(id=d_obj['contact_id'])
				if contact_obj.exists():
					uniqueid = contact_obj.first().uniqueid
					if not d_obj['phonebook'] and contact_obj.first().phonebook:
						d_obj['phonebook'] = contact_obj.first().phonebook.name
			create_calldetial_from_diallereventlog(d_obj,uniqueid)
	except Exception as e:
		print('Exception in create_calldetial_missing_contact', e)
	finally:
		transaction.commit()
		connections["crm"].close()


def phonebook_upload(reupload=None):
	"""
	This function is use to schedule dial process recursively.
	"""
	try:
		from callcenter.signals import aps_phonebook_upload
		if reupload is not None:
			phonebook = PhoneBookUpload.objects.filter(phone_inst_id=reupload)
		else:
			phonebook = PhoneBookUpload.objects.filter(is_start=False)
		for phn_inst in phonebook:
			PHONEBOOK_STATUS = pickle.loads(settings.R_SERVER.get("phonebook") or pickle.dumps({}))
			if str(phn_inst.phone_inst.id) in PHONEBOOK_STATUS:
				if PHONEBOOK_STATUS[str(phn_inst.phone_inst.id)] < 100:
					del PHONEBOOK_STATUS[''+str(phn_inst.phone_inst.id)+'']
			if str(phn_inst.phone_inst.id) not in PHONEBOOK_STATUS:
				phn_inst.is_start=True
				phn_inst.save()
				PHONEBOOK_STATUS = pickle.loads(settings.R_SERVER.get("phonebook") or pickle.dumps(PHONEBOOK_STATUS))
				PHONEBOOK_STATUS[str(phn_inst.phone_inst.id)] = 0
				settings.R_SERVER.set("phonebook", pickle.dumps(PHONEBOOK_STATUS))
				# filename = phn_inst.phonebook_file.name
				# filename, file_extension = os.path.splitext(filename)
				is_xls = False
				if phn_inst.phonebook_file.name.endswith('.csv'):
					data = pd.read_csv(phn_inst.phonebook_file, na_filter=False, encoding = "unicode_escape", escapechar='\\',
						dtype = {"numeric" : "str", "alt_numeric": "str","customer_info:loan_account_number": "str"},)
				else:
					data = pd.read_excel(phn_inst.phonebook_file, converters={'numeric': str,'customer_info:loan_account_number':str})
					data = data.fillna('')
					is_xls = True
				if is_xls:
					file_extension = '.xls'
				else:
					file_extension = '.csv'
				aps_phonebook_upload(data=data,phone_inst_id=phn_inst.phone_inst.id, phone_inst=phn_inst.phone_inst, duplicate_check=phn_inst.duplicate_check, action_type=phn_inst.action_type, search_type=phn_inst.search_type, column_names=phn_inst.column_names, file_extension=file_extension)
	except Exception as e:
		print("phonebook_upload error ", e)
	finally:
		transaction.commit()
		connections['default'].close()

def kill_unused_fs_channel():
	""" killing unused channels in the freewitch"""
	try:
		kill_uuid = []
		server_ip = Switch.objects.filter(status="Active").first().ip_address
		SERVER = freeswicth_server(server_ip)
		channels = SERVER.freeswitch.api("show","channels")
		channel_df = pd.DataFrame([x.split(',') for x in channels.split('\n')[:-3]])
		if not channel_df.empty:
			channel_df.columns = channel_df.iloc[0]
			channel_df = channel_df[1:]
			channel_df = channel_df.loc[channel_df.state.isin(['CS_EXCHANGE_MEDIA','CS_EXECUTE']) & (channel_df.cid_num.str.len() <5)]['uuid']

		AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps({}))
		if not channel_df.empty and AGENTS.values():
			agent_redis_df = pd.DataFrame.from_dict(AGENTS.values())
			agent_redis_df = agent_redis_df[agent_redis_df.dialerSession_uuid.astype(bool)] #To remove blank uuids from redis
			uuid_in_redis = agent_redis_df.dialerSession_uuid.values

			kill_uuid = channel_df[~channel_df.isin(uuid_in_redis)].values
		elif not channel_df.empty:
			kill_uuid = channel_df.values
		for uuid in kill_uuid:
			SERVER.freeswitch.api("uuid_kill",uuid)
	except Exception as e:
		print('Exception from kill_unused_fs_channel', e)

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
	sched.add_job(phonebook_upload,'interval',seconds=10, start_date=execution_time,
						   id='phonebook_upload', jobstore='list')
	sched.add_job(phonebook_data_bucket,'interval', seconds=60, start_date=execution_time,
						   id='phonebook_data_bucket', jobstore='list')
	# sched.add_job(generate_report,'interval', seconds=5, start_date=execution_time,
	# 					   id='generate_report', jobstore='list')
	sched.add_job(session_expire_check,'interval', minutes=1.5, start_date=execution_time,
						   id='session_expire_check', jobstore='list')
	sched.add_job(update_queued_contact,'interval', hours=1, start_date=execution_time,
						   id='update_queued_contact', jobstore='list')
	sched.add_job(create_calldetial_missing_contact,'interval', minutes=30, start_date=execution_time,
					   id='create_calldetial_missing_contact', jobstore='list')

	if sched.state == 0:
		sched.start()

if __name__ == '__main__':
	Execute()
