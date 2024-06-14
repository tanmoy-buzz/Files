#import time
import sys,os
import math
import re
import socket
import pycurl
from io import StringIO,BytesIO
import uuid
from concurrent.futures import ThreadPoolExecutor
import xmlrpc.client
from string import Template
from django.conf import settings
from django.db import transaction
from collections import Counter
from scripts.contacts import autodial_num_update,autodial_num_fetch
from callcenter.models import DNC,CallDetail,Switch,Campaign
from crm.models import TempContactInfo, Contact
import json,pickle
from datetime import datetime,timedelta
from callcenter.utility import trunk_channels_count, set_campaign_channel

AGENTS={}
wfh_agents={}
pool = ThreadPoolExecutor(max_workers=20)

def freeswicth_server(switch):
	"""
	This function is defined for creating the freeswitch server connection.
	"""
	rpc_port = Switch.objects.filter(ip_address=switch).first().rpc_port
	SERVER = xmlrpc.client.ServerProxy("http://%s:%s@%s:%s" % (settings.RPC_USERNAME,
			 settings.RPC_PASSWORD,switch,rpc_port))
	return SERVER

def scrub(number):
	""" scrub method to find the NDNC contact through curl """
	try:
		curlout = BytesIO()
		curl = pycurl.Curl()
		curl.setopt(pycurl.URL, settings.NDNC_URL % str(number)[-10:])
		curl.setopt(pycurl.WRITEFUNCTION, curlout.write)
		curl.perform()
		if curlout.getvalue().decode('UTF-8') == '1':
			return True
		if curlout.getvalue().decode('UTF-8') == '0':
			return False
		else:
			print("Problem in fetching data")
			return False
	except Exception as e:
		print(e)
		return False

def fs_voice_blaster(campaign):
	""" 
	Takes campaign as an argument and read freeswitch callcenter
	configuration and then sets dial ratio accordingly. It also
	fetches numbers to dial and update them into database.
	"""
	fs_cust_in_campaign = 0
	fs_cust_in_pd_camapaign = 0
	ftdm_down_count = 0
	initiated_call = 0
	count = 0
	initiated_call = 0
	free_channel = 0
	try:
		if campaign.schedule and campaign.schedule.status == 'Active':
			camp_schedule=campaign.schedule.schedule
			day_now = datetime.today().strftime('%A')
			if day_now in camp_schedule and camp_schedule.get(day_now)['start_time'] != "" and camp_schedule.get(day_now)['stop_time'] != "":
				start_time_obj = datetime.strptime(camp_schedule.get(day_now
					)['start_time'], '%I:%M %p').time()
				stop_time_obj = datetime.strptime(camp_schedule.get(day_now
					)['stop_time'], '%I:%M %p').time()
				if datetime.now().time() > start_time_obj and  datetime.now().time() < stop_time_obj:
					ftdm_down_count , trunkwise_status, trunk_list, allowted_channels,country_code,dial_digits = trunk_channels_count(campaign)
					if trunk_list:
						vb_campaigns = settings.R_SERVER.hget("ad_campaign_status",campaign.name)
						if not vb_campaigns or vb_campaigns.decode('utf-8') == 'True':
							settings.R_SERVER.hset("ad_campaign_status",campaign.name, False)
							try:
								SERVER = freeswicth_server(campaign.switch.ip_address)
								# fs_cust_in_campaign =  trunk_status['chennals'][campaign.name]['c_total_chennals']
								# allowted_channels = campaign.trunk.channel_count
								# ftdm_down_count = allowted_channels - total_cust_in_campaign
								free_channel = allowted_channels - ftdm_down_count
								print("GSM CHANNAL SOFIA :::::: %s" %(ftdm_down_count))
							except socket.error as e:
								print("RPC Error %s: Freeswitch RPC module may not be" \
										  " loaded or properly configured" % (e))
								print("FreeTDM Module may not be loaded")
								settings.R_SERVER.hset("ad_campaign_status",campaign.name, True)
								return None
							except:
								free_channel = 0
								print("FreeTDM Module may not be loaded")
								try:
									if campaign.trunk.dial_string.startswith('freetdm'):
										SERVER.freeswitch.api("load", "mod_freetdm")
								except socket.error as e:
									print("RPC Error %s: Freeswitch RPC module may not be" \
										  " loaded or properly configured" %(e))
							numbers = autodial_num_fetch(campaign, free_channel, True)
							ndnc_numbers = []
							not_ndnc = []
							if int(campaign.vbcampaign.first().vb_data['vb_call_after']) != 0:
								max_last_call_date = datetime.now().date() - timedelta(days=int(campaign.vbcampaign.first().vb_data['vb_call_after']))
								last_call = CallDetail.objects.filter(created__date__gte=max_last_call_date, campaign=campaign, dialed_status__in=['Full Audio Played','Not Played Full Audio'])
							else:
								last_call = CallDetail.objects.none()
							for num in numbers:
								if country_code:
									cn_numeric = country_code + num.numeric
								else:
									cn_numeric = num.numeric
								if last_call.filter(customer_cid=num.numeric).exists():
									Contact.objects.filter(id=num.contact_id).update(status="Dialed")
									TempContactInfo.objects.get(id=num.id).delete()
									continue
								if campaign.campaign_variable.ndnc_scrub:
									response = scrub(num.numeric[-10:])
									if response:
										ndnc_numbers.append(num.contact_id)
										continue
								print("Call Originated to %s Number." % cn_numeric)
								ori_uuid = uuid.uuid4()
								try:
									initiated_call, trunkwise_status, trunk, caller_id = set_campaign_channel(trunk_list, trunkwise_status, initiated_call)
									phonebook_name = None
									if num.phonebook:
										phonebook_name = num.phonebook.name
#									callback_camp = ','.join([f"{key}__{Campaign.objects.get(id=int(value.get('camp'))).name}" for key, value in campaign.vbcampaign.first().vb_data['vb_dtmf'].items() if 'camp' in value])
									callback_camp = ','.join([f"{key}__{Campaign.objects.get(id=int(value.get('camp'))).name}"for key, value in campaign.vbcampaign.first().vb_data['vb_dtmf'].items()if 'camp' in value and value.get('camp')])
									fs_originate = Template(settings.FS_ORIGINATE).safe_substitute(
										dict(campaign_slug=campaign.slug,
											 phonebook_id=phonebook_name,contact_id=num.id,
											 variables="uniqueid='%s',callback_camp='%s',origination_uuid=%s,origination_caller_id_number=%s,trunk_id=%s,cc_customer=%s,usertype='client',call_mode='voice-blaster',disposition='Invalid Number',voice_blaster=True,"\
											 "details=%s".rstrip().rstrip(',') % (num.uniqueid,callback_camp,ori_uuid,caller_id,trunk['id'],str(num),campaign.campaign_variable.variables),
														campaign_extension=campaign.campaign_variable.extension,dial_string=trunk['dial_string']))
									fs_originate_str = Template(fs_originate).safe_substitute(
										dict(destination_number=cn_numeric))
									SERVER.freeswitch.api("bgapi", fs_originate_str)
									not_ndnc.append(num.contact_id)
									# settings.R_SERVER.sadd(campaign_str, ori_uuid)
									if campaign.vbcampaign.first().vb_mode == 1:
										pass
								except socket.error as e:
									print("RPC Error %s: Freeswitch RPC module or Redis may not be" \
											  "loaded or properly configured" %(e))
									settings.R_SERVER.hset("ad_campaign_status",campaign.name, True)
									return None
								except Exception as e:
									print(e)
									exc_type, exc_obj, exc_tb = sys.exc_info()
									fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
									print(exc_type, fname, exc_tb.tb_lineno)
								print("Number : %s updated" % (cn_numeric))
							if numbers:
								# not_ndnc = [x.id for x in numbers]
								pool.submit(autodial_num_update,campaign,not_ndnc)
								if ndnc_numbers != []:
									pool.submit(autodial_num_update, campaign, ndnc_numbers, description="NDNC")
							settings.R_SERVER.hset("ad_campaign_status",campaign.name, True)
	except Exception as e:
		print("campaign object error",e)
		# settings.R_SERVER.hset("ad_campaign_status",campaign.name, True)
		settings.R_SERVER.hset("ad_campaign_status",campaign.name, True)
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print(exc_type, fname, exc_tb.tb_lineno)

def fsdial(campaign):
	"""
	Takes campaign as an argument and read freeswitch callcenter
	configuration and then sets dial ratio accordingly. It also
	fetches numbers to dial and update them into database.
	"""
	fs_cust_in_campaign = 0
	fs_cust_in_pd_camapaign = 0
	ftdm_down_count = 0
	count = 0
	free_channel = 0
	trunkwise_status = {}
	trunk_list = []
	allowted_channels = 0
	initiated_call = 0
	dial_min_val = ''
	dial_max_val = ''
	try:
		ftdm_down_count , trunkwise_status, trunk_list, allowted_channels, country_code, dial_digits = trunk_channels_count(campaign)
		if dial_digits:
			dial_min_val = dial_digits.split(",")[0]
			dial_max_val = dial_digits.split(",")[1]
		if trunk_list:
			pd_campaigns = settings.R_SERVER.hget("ad_campaign_status",campaign.name)
			if not pd_campaigns or pd_campaigns.decode('utf-8') == 'True':
				settings.R_SERVER.hset("ad_campaign_status",campaign.name, False)
				try:
					trunk_status = pickle.loads(settings.R_SERVER.get("trunk_status") or pickle.dumps({}))
					SERVER = freeswicth_server(campaign.switch.ip_address)
					print(campaign.name)
					fs_agent_available1 = SERVER.freeswitch.api("callcenter_config",
																"queue list agents '%s' 'Available (On Demand)'" % campaign.slug)
					fs_agent_available2 = SERVER.freeswitch.api("callcenter_config",
																"queue list agents '%s' 'Available'" % campaign.slug)
					# allowted_channels = campaign.trunk.channel_count
					free_channel = allowted_channels - ftdm_down_count
					# for trunk_obj in trunk_status.keys():
					# 	fs_cust_in_pd_camapaign += trunk_status[str(trunk_obj)]
					# fs_cust_in_pd_camapaign = trunk_status['chennals'][campaign.name]['predictive']
					print("<------------------------------start-------------------------------------------->")
					print("GSM CHANNAL SOFIA :::::: %s" %(ftdm_down_count))
				except socket.error as e:
					print("RPC Error %s: Freeswitch RPC module may not be" \
							  " loaded or properly configured" % (e))
					settings.R_SERVER.hset("ad_campaign_status",campaign.name, True)
					return None
				except Exception as e:
					ftdm_down_count = 0
					exc_type, exc_obj, exc_tb = sys.exc_info()
					fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
					print(exc_type, fname, exc_tb.tb_lineno)
					print("FreeTDM Module may not be loaded")
					try:
						for trunk_obj in trunk_list:
							if trunk_obj['dial_string'].startswith('freetdm'):
								SERVER.freeswitch.api("load", "mod_freetdm")
					except socket.error as e:
						print("RPC Error %s: Freeswitch RPC module may not be" \
							  " loaded or properly configured" %(e))
				agent_available = fs_agent_available1.splitlines()
				agent_available[1:1] = fs_agent_available2.splitlines()[1:-1]
				agent_count = 0
				for i in agent_available[1:]:
					if i.find('Waiting') > 0:
						agent_count += 1
				wait_count = int(math.ceil(agent_count * campaign.campaign_variable.dial_ratio))
				total_pd_agents = 0
				AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
				for i in AGENTS:
					if AGENTS[i]['call_type'] in ['predictive','blended'] and AGENTS[i]['state'] not in ['Idle']:
						if AGENTS[i]['campaign'] == campaign.name:
							total_pd_agents += 1
				print(total_pd_agents, "agents", ftdm_down_count,"campaign used channel", )
				total_dial_count = int(math.ceil(total_pd_agents * campaign.campaign_variable.dial_ratio - ftdm_down_count))
				if total_dial_count < 0:
					if free_channel >= wait_count:
						count = wait_count
					else:
						count = free_channel
				elif wait_count > total_dial_count:
					if free_channel >= wait_count:
						count = wait_count
					else:
						count = free_channel
				elif wait_count <= total_dial_count:
					if free_channel >= wait_count:
						count = wait_count
					else:
						count = free_channel
				else:
					pass
				count = int(math.floor(abs(count)))
				if count < 0:
					count = 0
				print("%s campaign | dial_ratio : %s | agents_wait : %s | \
					Diled_numbers : %s | next_dial_count : %s" % (campaign.name,campaign.campaign_variable.dial_ratio,agent_count,fs_cust_in_pd_camapaign,count))
				numbers = autodial_num_fetch(campaign, count,False)
				ndnc_numbers = []
				not_ndnc = []
				for num in numbers:
					if country_code:
						cn_numeric = country_code + num.numeric
					else:
						cn_numeric = num.numeric
					print("Call Originated to %s Number." % cn_numeric)
					if campaign.campaign_variable.ndnc_scrub:
						response = scrub(num.numeric[-10:])
						if response:
							ndnc_numbers.append(num.contact_id)
							continue
					if DNC.objects.filter(numeric=num.numeric[-10:],status='Active',global_dnc=True).exists():
						Contact.objects.filter(numeric=num.numeric).update(status = 'Dnc')
						TempContactInfo.objects.filter(numeric=num.numeric).delete()
						continue
					elif DNC.objects.filter(numeric=num.numeric[-10:],status='Active',campaign=campaign).exists():
						Contact.objects.filter(numeric = num.numeric).update(status = 'Dnc')
						TempContactInfo.objects.filter(numeric = num.numeric).delete()
						continue
					else:			
						ori_uuid = uuid.uuid4()
						try:
							initiated_call, trunkwise_status, trunk, caller_id = set_campaign_channel(trunk_list, trunkwise_status, initiated_call)
							if len(cn_numeric)-1 >= int(dial_min_val) and len(cn_numeric)-1 <= int(dial_max_val):
								cn_numeric = cn_numeric
							else:
								print("dial number length should be in between "+dial_min_val+" and "+dial_max_val+".please enter valid number")
								cn_numeric=''
							if 'id' in trunk and trunk['id']:
								phonebook_name = None
								if num.phonebook:
									phonebook_name = num.phonebook.name
								fs_originate = Template(settings.FS_ORIGINATE).safe_substitute(
									dict(campaign_slug=campaign.slug,
										 phonebook_id=phonebook_name,contact_id=num.contact_id,
										 variables="uniqueid='%s',origination_uuid=%s,voice_blaster=False,origination_caller_id_number=%s,trunk_id=%s,cc_customer=%s,usertype='client',call_mode='predictive',disposition='Invalid Number'," \
												   "details=%s".rstrip().rstrip(',') % (num.uniqueid,ori_uuid,caller_id,trunk['id'],str(num),campaign.campaign_variable.variables),
													campaign_extension=campaign.campaign_variable.extension,dial_string=trunk['dial_string']))
								fs_originate_str = Template(fs_originate).safe_substitute(
									dict(destination_number=cn_numeric))
								SERVER.freeswitch.api("bgapi", fs_originate_str)
								# settings.R_SERVER.sadd(campaign_str, ori_uuid)
								not_ndnc.append(num.contact_id)
								if campaign.wfh:
									contact_obj = Contact.objects.get(id=num.id)
									wfh_agents = pickle.loads(settings.R_SERVER.get("wfh_agents") or pickle.dumps({}))
									if wfh_agents:
										wfh_agents[str(ori_uuid)]={"c_num":contact_obj.numeric,'c_username':contact_obj.first_name +''+contact_obj.last_name}
									else:
										wfh_agents={str(ori_uuid):{"c_num":contact_obj.numeric,'c_username':contact_obj.first_name +''+contact_obj.last_name}}
									settings.R_SERVER.set("wfh_agents",pickle.dumps(wfh_agents))
							else:
								print("Trunk is not Available")
								settings.R_SERVER.hset("ad_campaign_status",campaign.name, True)
						except socket.error as e:
							print("RPC Error %s: Freeswitch RPC module or Redis may not be" \
									  "loaded or properly configured" %(e))
							settings.R_SERVER.hset("ad_campaign_status",campaign.name, True)
							return None
						except Exception as e:
							print(e)
						print("Number : %s updated" % (cn_numeric))
						print("<------------------------------end-------------------------------------------->")
				if numbers:
					# not_ndnc = [x.id for x in numbers]
					pool.submit(autodial_num_update,campaign,not_ndnc)
					if ndnc_numbers != []:
						pool.submit(autodial_num_update, campaign, ndnc_numbers, description="NDNC")
				settings.R_SERVER.hset("ad_campaign_status",campaign.name, True)
	except Exception as e:
		print("campaign object error",e)
		settings.R_SERVER.hset("ad_campaign_status",campaign.name, True)
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print(exc_type, fname, exc_tb.tb_lineno)
