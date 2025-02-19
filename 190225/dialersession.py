from django.conf import settings
from django.db.models import Q, F
from callcenter.models import UserVariable,Campaign,Switch,AudioFile,DNC,CampaignVariable,PhonebookBucketCampaign, DialTrunk, CallDetail, CdrFeedbck,Holidays
from callcenter.utility import customer_detials, create_agentactivity,get_temp_contact, channel_trunk_single_call, trunk_with_agent_call_id
from crm.models import TempContactInfo, Contact, ContactInfo, Phonebook, AlternateContact
from crm.serializers import ContactSerializer
import xmlrpc.client
import uuid,pickle
import uuid
from scripts.contacts import num_update, delete_lead_priority
import json
import sys,os
import time
from datetime import datetime, date
from string import Template
from gtts import gTTS
CAMPAIGNS={}
r_campaigns={}
AGENTS={}
from scripts.fsautodial import scrub

def freeswicth_server(func):
	"""
	This function is defined for creating the freeswitch server connection.
	"""
	def wrap(*args,**kwargs):
		rpc_port = 8080
		rpc_port_obj = Switch.objects.filter(ip_address=args[0]).first()
		if rpc_port_obj:
			rpc_port = rpc_port_obj.rpc_port
		SERVER = xmlrpc.client.ServerProxy("http://%s:%s@%s:%s" % (settings.RPC_USERNAME,
			 settings.RPC_PASSWORD,args[0],rpc_port))
		kwargs['SERVER'] = SERVER
		return func(*args,**kwargs)
	return wrap

@freeswicth_server
def twinkle_session(*args,**kwargs):
	"""
	This function is defined for creating the sip session at freeswitch server side.
	"""
	try:
		user = UserVariable.objects.get(extension=kwargs['extension'])
		kwargs['SERVER'].freeswitch.api("callcenter_config",
			"agent set contact %s %s/%s@%s" % (user.extension, user.contact,
				user.extension, user.domain.ip_address))
		hold_music = "local_stream://moh"
		ori_uuid = uuid.uuid4()
		campvar_inst = CampaignVariable.objects.get(campaign__name=kwargs['campaign_name']).hold_music
		if kwargs['call_type'] =='softcall':
			registered_session = kwargs['SERVER'].freeswitch.api("show","registrations")
			user_ext = [i.split(',')[0] for i in registered_session.splitlines()[1:-2]]
			if kwargs['extension'] in user_ext:
				if campvar_inst:
					hold_music = campvar_inst.audio_file.path				
				status = kwargs['SERVER'].freeswitch.api("originate","{usertype='agent',origination_uuid=%s,origination_caller_id_number=%s,cc_agent=%s,hold_music=%s,campaign=%s}user/%s 11119916" %(ori_uuid,kwargs['extension'],kwargs['extension'],hold_music,kwargs['campaign_name'],kwargs['extension']))
				if '-ERR' in status:
					return {"error":"session is not intiated..., please coordinate your administrator."}
			else:
				return {"error":"user is not registered..., please coordinate your administrator."}
		elif kwargs['call_type'] =='2':
			if campvar_inst:
					hold_music = campvar_inst.audio_file.path
			if user and user.wfh_numeric:
				camp_obj = Campaign.objects.get(name=kwargs['campaign_name'])
				dial_string = Template(camp_obj.trunk.dial_string).safe_substitute(destination_number=user.wfh_numeric)				
				status = kwargs['SERVER'].freeswitch.api("originate","{usertype='agent',wfh_app='true',origination_uuid=%s,origination_caller_id_number=%s,cc_agent=%s,hold_music=%s,campaign=%s,cc_export_vars=wfh_app,cc_agent,campaign}%s 11119916" %(ori_uuid,kwargs['extension'],kwargs['extension'],hold_music,kwargs['campaign_name'],dial_string))
				if '-ERR' in status:
					return {"error":"user mobile number is not rechable.."}
			else:
				return {"error":"user does not having Wfh mobile number.."}
		campaigns = user.campaign
		for campaign in campaigns:
			if campaign.name == kwargs['campaign_name']:
				kwargs['SERVER'].freeswitch.api("callcenter_config","tier add %s %s %s %s" % (kwargs['campaign_name'], user.extension,
				user.level, user.position))
			else:
				kwargs['SERVER'].freeswitch.api("callcenter_config","tier del %s %s" % (campaign.name, kwargs['extension']))
		r_campaigns = pickle.loads(settings.R_SERVER.get("campaign_status") or pickle.dumps(CAMPAIGNS))
		if kwargs['campaign_name'] in r_campaigns:
			unique_extensions = list(set(r_campaigns[kwargs['campaign_name']]))
			if kwargs['extension'] not in unique_extensions: 
				unique_extensions.append(kwargs['extension'])
				r_campaigns[kwargs['campaign_name']]=unique_extensions
		else:
			r_campaigns[kwargs['campaign_name']]=[kwargs['extension']]
		settings.R_SERVER.set("campaign_status", pickle.dumps(r_campaigns))
		return {"success":"session is intiated successfully", "ori_uuid":str(ori_uuid)}

	except Exception as e:
		print("something went wrong while sip intialization...%s"%(e))
		return {"error":"something went wrong while sip intialization...%s"%(e)}

@freeswicth_server
def start_sip_session(*args, **kwargs):
	############
	#### This Function created twinkle_session again when break is ends ###
	##########################
	try:
		campvar_inst = CampaignVariable.objects.get(campaign__name=kwargs['campaign_name']).hold_music
		ori_uuid = uuid.uuid4()
		hold_music = "local_stream://moh"
		user = UserVariable.objects.get(extension=kwargs['extension'])
		if kwargs['call_type'] =='softcall':
			registered_session = kwargs['SERVER'].freeswitch.api("show","registrations")
			user = [i.split(',')[0] for i in registered_session.splitlines()[1:-2]]
			if kwargs['extension'] in user:
				if campvar_inst:
					hold_music = campvar_inst.audio_file.path
				status = kwargs['SERVER'].freeswitch.api("originate","{usertype='agent',origination_uuid=%s,origination_caller_id_number=%s,cc_agent=%s,hold_music=%s}user/%s 11119916" %(ori_uuid,kwargs['extension'],kwargs['extension'],kwargs['extension'],hold_music))
				if '-ERR' in status:
					return {"error":"session is not intiated..., please coordinate your administrator.",'ori_uuid':''}
			else:
				return {"error":"user is not registered..., please coordinate your administrator.",'ori_uuid':ori_uuid}
		elif kwargs['call_type'] =='2':
			if campvar_inst:
					hold_music = campvar_inst.audio_file.path
			if user and user.wfh_numeric:
				camp_obj = Campaign.objects.get(name=kwargs['campaign_name'])
				dial_string = Template(camp_obj.trunk.dial_string).safe_substitute(destination_number=user.wfh_numeric)				
				status = kwargs['SERVER'].freeswitch.api("originate","{usertype='agent',origination_uuid=%s,origination_caller_id_number=%s,cc_agent=%s,hold_music=%s}%s 11119916" %(ori_uuid,kwargs['extension'],kwargs['extension'],hold_music,dial_string))
				if '-ERR' in status:
					return {"error":"user mobile number is not rechable.."}
			else:
				return {"error":"user does not having Wfh mobile number.."}

		return {"success":"session is intiated successfully", "ori_uuid":str(ori_uuid)}

	except Exception as e:
		return {"error":"%s, please coordinate your administrator."%(e)}		

@freeswicth_server
def fs_administration_session(*args,**kwargs):
	"""
	This function is defined for creating the sip session at freeswitch server side.
	"""
	try:
		ori_uuid = ''
		registered_session = kwargs['SERVER'].freeswitch.api("show","registrations")
		user = [i.split(',')[0] for i in registered_session.splitlines()[1:-2]]
		if kwargs['extension'] in user:
			ori_uuid = uuid.uuid4()
			status = kwargs['SERVER'].freeswitch.api("originate","{usertype='agent',origination_uuid=%s,origination_caller_id_number=%s,cc_agent=%s}user/%s 11119916" %(ori_uuid,kwargs['extension'],kwargs['extension'],kwargs['extension']))
			if '-ERR' in status:
				return {"error":"session is not intiated...,Coordinate your administrator."}
		else:
			return {"error":"user is not registered...,Coordinate your administrator."}
		return {"success":"session is intiated successfully", "ori_uuid":str(ori_uuid)}

	except Exception as e:
		print("something went wrong while sip intialization...%s"%(e))
		return {"error":"something went wrong while sip intialization...%s"%(e)}		

@freeswicth_server
def dial(*args,**kwargs):
	"""
	This function is defined for dialling the customer number through freeswitch.
	"""
	try:
		campaign_obj = Campaign.objects.get(name=kwargs['campaign'])
		if DNC.objects.filter(numeric=kwargs['dial_number'][-10:],status='Active',global_dnc=True).exists():
			return {"info":"this number is blocked globally,Coordinate your administrator."}    
		elif DNC.objects.filter(numeric=kwargs['dial_number'][-10:],status='Active',campaign=campaign_obj).exists():
			return {"info":"this number is blocked in this campaign, Coordinate your administrator."}
		if campaign_obj.campaignvariable_set.all().first().ndnc_scrub:
			response = scrub(kwargs['dial_number']) 
			if response:
				ndnc_temp_contacts = TempContactInfo.objects.filter(numeric=kwargs['dial_number'][-10:]).values_list('contact_id',flat=True)
				if ndnc_temp_contacts:
					ndnc_contacts = Contact.objects.filter(id__in=list(ndnc_temp_contacts))
					ndnc_contacts.update(status='NDNC')
					TempContactInfo.objects.filter(contact_id__in=ndnc_temp_contacts).delete()
				return {"info":"this number is an NDNC Scrub for this campaign , Coordinate your administrator."}
		if kwargs['user_trunk_id'] and kwargs['caller_id']:
			trunk_id , dial_string, caller_id, country_code = trunk_with_agent_call_id(kwargs['user_trunk_id'], kwargs['caller_id'], campaign_obj)
		else:
			trunk_id , dial_string, caller_id, country_code = channel_trunk_single_call(campaign_obj)
		if trunk_id:
			number_status = TempContactInfo.objects.filter(status='Locked', numeric=kwargs['dial_number']).exists()
			if kwargs['call_type'] == "manual" and number_status:
				return {"info":"This number is already been locked, please dial another number."}
			contact_info, contact_count = get_contact_information(dial_number=kwargs['dial_number'],
				contact_id=kwargs['contact_id'],callmode=kwargs['callmode'],lead_preview=kwargs['lead_preview'], campaign_obj=campaign_obj)
			if contact_count == 1 and not kwargs['contact_id']:
				kwargs['contact_id'] = contact_info["id"]
			phonebook_name = ''
			uniqueid = kwargs["man_unique_id"]
			if contact_info:
				if 'phonebook' in contact_info and Phonebook.objects.filter(id=contact_info['phonebook']).exists():
					phonebook_name = Phonebook.objects.get(id=contact_info['phonebook']).name
				if "uniqueid" in contact_info and contact_info["uniqueid"]:
					uniqueid = contact_info["uniqueid"]
			ori_uuid = uuid.uuid4()
			if country_code:
				cn_numeric = country_code+kwargs['dial_number'][-10:]
			else:
				cn_numeric = kwargs['dial_number'][-10:] 
			fs_originate = Template(settings.FS_MANUAL_ORIGINATE).safe_substitute(dict(variables="usertype='client',cc_agent=%s,trunk_id=%s,origination_caller_id_number=%s,"\
				"origination_uuid=%s,disposition='Invalid Number',campaign_name=%s,dialed_number=%s,call_mode=%s,phonebook=%s,unique_id='%s',agent-Unique-ID='%s'"%(kwargs['extension'],trunk_id,caller_id,ori_uuid,kwargs['campaign'],
					kwargs['dial_number'][-10:],kwargs['callmode'],phonebook_name,uniqueid,kwargs['session_details']['Unique-ID'])),
				transfer_extension ='000312951420',dial_string=dial_string)
			fs_originate_str = Template(fs_originate).safe_substitute(dict(contact_id=kwargs['contact_id'],destination_number=cn_numeric))
			init_time = datetime.now()
			# dial_status = kwargs['SERVER'].freeswitch.api("originate","%s"%(fs_originate_str))
			dial_status = kwargs['SERVER'].freeswitch.api("bgapi","%s"%(fs_originate_str))
			# kwargs['SERVER'].freeswitch.api("uuid_pre_answer","%s" %(ori_uuid))
			print(kwargs['extension'], cn_numeric, kwargs['contact_id'], dial_status, phonebook_name)
			hangup_time = datetime.now()
			if kwargs['contact_id']:
				TempContactInfo.objects.filter(id=kwargs['contact_id']).delete()
				contacts = TempContactInfo.objects.filter(id=kwargs['contact_id'])
				delete_lead_priority(campaign_obj, contacts)
			if '+OK' in dial_status:
				# kwargs['SERVER'].freeswitch.api("uuid_bridge","%s %s" %(ori_uuid,kwargs['session_details']['Unique-ID']))
				settings.R_SERVER.sadd(str(kwargs['campaign']), ori_uuid)
				return {"success":"Number is dialedsuccessfully","dialed_uuid":ori_uuid,"dialed_number":kwargs['dial_number'],
						"contact_info":contact_info, "contact_count":contact_count}
			else:
				kwargs['contact_id'] = None if not kwargs['contact_id'] else kwargs['contact_id']
				ring_duration = time.strftime('%H:%M:%S', time.gmtime((hangup_time-init_time).total_seconds()))
				calldetail_id = CallDetail.objects.create(phonebook=phonebook_name,contact_id=kwargs['contact_id'], session_uuid=ori_uuid, b_leg_uuid=ori_uuid, init_time=init_time, ring_time=init_time, callflow='outbound', callmode=kwargs['callmode'], customer_cid=kwargs['dial_number'][-10:], destination_extension=kwargs['extension'], hangup_time=hangup_time, dialed_status='NC', hangup_cause='NOT_FOUND',hangup_cause_code='502',user_id=kwargs['user_id'],hangup_source='System',uniqueid=uniqueid,campaign_name=kwargs['campaign'], ring_duration=ring_duration,call_duration=ring_duration)
				CdrFeedbck.objects.create(primary_dispo='AutoFeedback', session_uuid = ori_uuid, contact_id = kwargs['contact_id'], calldetail=calldetail_id,feedback={}, relation_tag={})
				Contact.objects.filter(id=kwargs['contact_id']).update(status='NC')
				return {"error":"Call is not able to initiate","dialed_uuid":ori_uuid,"dialed_number":kwargs['dial_number'],
						"contact_info":contact_info, "contact_count":contact_count, "calldetail_id":calldetail_id.id}
		else:
			return {"info":"channel is not available, please coordinate your administrator."}
	except  Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print(exc_type, fname, exc_tb.tb_lineno)
		print("dial functioned error::",e)
		return {"info":"%s, please coordinate your administrator."%e}

@freeswicth_server
def inbound_call(*args,**kwargs):
	""" 
		This method is used for picking the inbound call 
	"""
	try:
		inbound_uuids = pickle.loads(settings.R_SERVER.get("inbound_status") or pickle.dumps({}))
		if kwargs['dialed_uuid'] in inbound_uuids:
			del inbound_uuids[kwargs['dialed_uuid']]
			settings.R_SERVER.set("inbound_status", pickle.dumps(inbound_uuids))
			kwargs['SERVER'].freeswitch.api("uuid_setvar_multi","%s cc_agent=%s;disposition=Connected;"%(kwargs['dialed_uuid'],kwargs['extension']))
			answer_status = kwargs['SERVER'].freeswitch.api("uuid_answer","%s" %(kwargs['dialed_uuid']))
			if '+OK' in answer_status:
				bridge_status = kwargs['SERVER'].freeswitch.api("uuid_bridge","%s %s" %(kwargs['dialed_uuid'],kwargs['unique_uuid']))
				if '+OK' in bridge_status:
					settings.R_SERVER.sadd(kwargs['campaign'], kwargs['dialed_uuid'])
					AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
					AGENTS[kwargs['extension']]['state'] = 'InCall'
					AGENTS[kwargs['extension']]['event_time'] = datetime.now().strftime('%H:%M:%S')
					AGENTS[kwargs['extension']]['call_type'] = 'inbound'
					AGENTS[kwargs['extension']]['dial_number'] = kwargs['inbound_number']
					settings.R_SERVER.set("agent_status", pickle.dumps(AGENTS))
					campaign_object = Campaign.objects.get(name=kwargs['campaign'])
					data=customer_detials(kwargs['campaign'],kwargs['inbound_number'],campaign_object)
					data["success"] = "answered successfully"
					return data
				else:
					return {"error":"someone is accepted this call."}
			else:
				return {"error":"someone is accepted this call."}			
		else:
			return {"error":"someone is accepted this call."}
	except Exception as e:
		print("inbound bridge error %s"%(e))

@freeswicth_server
def inbound_stiky_agent_bridge(*args,**kwargs):
	"""
		This method is to patch the contact to the sticky agent 
	"""
	if kwargs['dialed_uuid'] and kwargs['unique_uuid']:
		answer_status = kwargs['SERVER'].freeswitch.api("uuid_answer","%s" %(kwargs['dialed_uuid']))
		kwargs['SERVER'].freeswitch.api("callcenter_config","agent set state %s 'In a queue call'"%(kwargs['extension']))
		if '+OK' in answer_status:
			bridge_status = kwargs['SERVER'].freeswitch.api("uuid_bridge","%s %s" %(kwargs['dialed_uuid'],kwargs['unique_uuid']))
			if '+OK' in bridge_status:
				return {"success":"answered successfully"}
			else:
				return {"error":"something went wrong."}		
		else:
			return {"error":"something went wrong."}
	else:
		return {"error":"something went wrong."}		


@freeswicth_server		
def autodial_session(*args,**kwargs):
	"""
	This is the function using for creating the sip available to accept autodial calls.
	"""
	try:
		if kwargs['sip_error'] != 'true':
			kwargs['SERVER'].freeswitch.api("callcenter_config","agent set uuid %s '%s'"%(kwargs['extension'],kwargs['uuid']))
			kwargs['SERVER'].freeswitch.api("callcenter_config","agent set type %s 'uuid-standby'"%(kwargs['extension']))
			kwargs['SERVER'].freeswitch.api("callcenter_config","agent set status %s 'Available (On Demand)'"%(kwargs['extension']))
			kwargs['SERVER'].freeswitch.api("callcenter_config","agent set state %s 'Waiting'"%(kwargs['extension']))
			return {"success":"autodial start successfully"}
		else:
			print("sip_error true")
			kwargs['SERVER'].freeswitch.api("callcenter_config","agent set status %s 'Logged Out'"%(kwargs['extension']))
			return {"success":"autodial stop successfully"}
	except Exception as e:
		print("error from autodial_session : ",e)
		return {"error":"%s, please coordinate your administrator."%(e)}

@freeswicth_server
def autodial_session_hangup(*args,**kwargs):
	"""
	This is the function using for make autodial sip session logged Out.
	"""	
	try:
		kwargs['SERVER'].freeswitch.api("callcenter_config","agent set status %s 'Logged Out'"%(kwargs['extension']))
		return {"success":"autodial stoped successfully"}
	except Exception as e:
		print(e)
		return {"error":"%s, please coordinate your administrator."%(e)}

@freeswicth_server
def play_fake_ring_agent(*args,**kwargs):
	"""
	This is the function using for play fake ring to agent when session in progress.
	"""	
	try:
		if kwargs['play_status'] == 'play':
			kwargs['SERVER'].freeswitch.api("uuid_setvar_multi","%s fake_ring='%s';"%(kwargs['Unique-ID'],'true'))
			kwargs['SERVER'].freeswitch.api("uuid_displace","%s start /usr/local/src/flexydial/static/audio_files/Phone_Ringing_8x.mp3 24"%(kwargs['agent_unique_id']))
		elif kwargs['play_status'] == 'dnp':
			kwargs['SERVER'].freeswitch.api("uuid_setvar_multi","%s fake_ring='%s';"%(kwargs['Unique-ID'],'false'))
			if kwargs.get('fake_ring','') == 'true':
				kwargs['SERVER'].freeswitch.api("uuid_displace","%s stop /usr/local/src/flexydial/static/audio_files/Phone_Ringing_8x.mp3"%(kwargs['agent_unique_id']))
				print(kwargs['agent_unique_id'],"------------",kwargs['Unique-ID'])
				kwargs['SERVER'].freeswitch.api("uuid_transfer","%s %s@sla"%(kwargs['Unique-ID'],kwargs['agent_unique_id']))
		else:
			kwargs['SERVER'].freeswitch.api("uuid_displace","%s stop /usr/local/src/flexydial/static/audio_files/Phone_Ringing_8x.mp3"%(kwargs['agent_unique_id']))	
		return {"success":"autodial stoped successfully"}
	except Exception as e:
		print(e)
		return {"error":"%s, please coordinate your administrator."%(e)}

@freeswicth_server
def hangup(*args,**kwargs):
	"""
	This function is defined for hangup the customer number.
	"""
	try:
		if kwargs.get('agent_uuid_id',None):
			kwargs['SERVER'].freeswitch.api("uuid_displace","%s stop /usr/local/src/flexydial/static/audio_files/Phone_Ringing_8x.mp3"%(kwargs['agent_uuid_id']))
		hangup_status=kwargs['SERVER'].freeswitch.api("uuid_kill",kwargs['uuid'])
		settings.R_SERVER.srem(kwargs['campaign'], kwargs['uuid'])
		AGENTS = {}
		AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or
				pickle.dumps(AGENTS))
		campaign_id = Campaign.objects.get(name=kwargs['campaign'])
		pbc_obj = PhonebookBucketCampaign.objects.filter(id=campaign_id.id)
		if '+OK' in hangup_status:
			if kwargs['hangup_type'] == "sip_agent":
				r_campaigns = pickle.loads(settings.R_SERVER.get("campaign_status") or pickle.dumps(CAMPAIGNS))
				if kwargs['campaign'] in r_campaigns:
					unique_extensions = list(set(r_campaigns[kwargs['campaign']]))
					unique_extensions.remove(kwargs['extension'])
					r_campaigns[kwargs['campaign']]=unique_extensions
				settings.R_SERVER.set("campaign_status", pickle.dumps(r_campaigns))	
				kwargs['SERVER'].freeswitch.api("callcenter_config","agent set status %s 'Logged Out'"%(kwargs['extension']))			
				kwargs['SERVER'].freeswitch.api("callcenter_config","tier del %s %s" % (kwargs['campaign'], kwargs['extension']))
				AGENTS[kwargs['extension']]['campaign'] = ''
				AGENTS[kwargs['extension']]['dialer_login_status'] = False
				AGENTS[kwargs['extension']]['dialer_login_time'] = ''
				AGENTS[kwargs['extension']]['status'] = 'NotReady'
				AGENTS[kwargs['extension']]['state'] = ''
				AGENTS[kwargs['extension']]['event_time'] = ''
				AGENTS[kwargs['extension']]['dialerSession_uuid'] = ''
				updated_agent_dict = pickle.loads(settings.R_SERVER.get("agent_status"))
				updated_agent_dict[kwargs['extension']] = AGENTS[kwargs['extension']]
				settings.R_SERVER.set("agent_status", pickle.dumps(updated_agent_dict))
				if pbc_obj.first().agent_login_count > 0:
					pbc_obj.update(agent_login_count=F('agent_login_count')-1)
			return {"success":"successfully"}
		else:
			if pbc_obj.first().agent_login_count > 0:
				pbc_obj.update(agent_login_count=F('agent_login_count')-1)
			return {"error":"something went wrong, please coordinate your administrator."}
	except Exception as e:
		return {"error":"%s, please coordinate your administrator."%(e)}

@freeswicth_server
def on_break(*args,**kwargs):
	"""
	This function is defined for hangup the customer number.
	"""
	try:
		hangup_status=kwargs['SERVER'].freeswitch.api("uuid_kill",kwargs['uuid'])
		if '+OK' in hangup_status:
			return {"success":"successfully"}
		else:
			return {"error":"something went wrong, please coordinate your administrator."}
	except Exception as e:
		return {"error":"%s, please coordinate your administrator."%(e)}

@freeswicth_server
def fs_administration_hangup(*args,**kwargs):
	"""
	This function is defined for hangup the administartion number.
	"""
	try:
		if isinstance(kwargs['uuid'], list):
			for dialed_uuid in kwargs['uuid']:
				hangup_status=kwargs['SERVER'].freeswitch.api("uuid_kill",dialed_uuid)
			return {"success":"successfully"}					
		else:
			hangup_status=kwargs['SERVER'].freeswitch.api("uuid_kill",kwargs['uuid'])
		return {"success":"successfully"}
	except Exception as e:
		return {"error":"%s, please coordinate your administrator."%(e)}

@freeswicth_server
def fs_set_variables(*args,**kwargs):
	"""
	This is the function using for make autodial sip session logged Out.
	"""	
	try:
		cust_status = 'false'
		audio_moh_sound = None
		c_max_wait_time = 25
		no_agent_audio = False
		holiday_obj = Holidays.objects.filter(status="Active",holiday_date=datetime.today())
		if not holiday_obj.exists():
			if 'call_type' not in kwargs:
				cust_status = kwargs['SERVER'].freeswitch.api('uuid_exists',kwargs['dialed_uuid'])
				if not kwargs['skill_routed_status']:
					if kwargs["campaign_obj"][0].dial_method["ibc_popup"]:
						if kwargs["campaign_obj"][0].dial_method["no_agent_audio"]:
							no_agent_audio = kwargs["campaign_obj"][0].dial_method["no_agent_audio"]
							if kwargs["campaign_obj"][0].campaign_variable.max_wait_time > 0:
								c_max_wait_time = kwargs["campaign_obj"][0].campaign_variable.max_wait_time
							if kwargs["campaign_obj"][0].campaign_variable.moh_sound:
								audio_moh_sound = kwargs["campaign_obj"][0].campaign_variable.moh_sound.audio_file.name
				kwargs['SERVER'].freeswitch.api("uuid_setvar_multi","%s usertype='client';cc_agent=%s;campaign_name=%s;ibc_popup=%s;queue_call=%s;"%(kwargs['dialed_uuid'],kwargs['extension'],kwargs['campaign'],kwargs["ibc_popup"],kwargs['queue_call']))
			else:
				campvar_inst = CampaignVariable.objects.get(campaign__name=kwargs['campaign']).hold_music
				hold_music = "local_stream://moh"
				if campvar_inst:
					hold_music = campvar_inst.audio_file.path
				kwargs['SERVER'].freeswitch.api("uuid_setvar_multi","%s usertype='agent';cc_agent=%s;campaign_name=%s;origination_caller_id_number=%s;hold_music=%s;"%(kwargs['dialed_uuid'],kwargs['extension'],kwargs['campaign'],kwargs['extension'],hold_music))
			if "campaign_obj" in kwargs and kwargs['campaign_obj']:
				"""
				this if condition is used for checking the campaign scheduled time...
				"""
				if kwargs["campaign_obj"][0].schedule and kwargs["campaign_obj"][0].schedule.status == 'Active':
					camp_schedule=kwargs["campaign_obj"][0].schedule.schedule
					day_now = datetime.today().strftime('%A')
					if day_now in camp_schedule and camp_schedule.get(day_now)['start_time'] != "" and camp_schedule.get(day_now)['stop_time'] != "":
						start_time_obj = datetime.strptime(camp_schedule.get(day_now
							)['start_time'], '%I:%M %p').time()
						stop_time_obj = datetime.strptime(camp_schedule.get(day_now
							)['stop_time'], '%I:%M %p').time()
						if datetime.now().time() < start_time_obj or datetime.now().time() > stop_time_obj:
							kwargs['SERVER'].freeswitch.api('uuid_answer',"%s"%(kwargs['dialed_uuid']))
							audiofile_obj=AudioFile.objects.filter(name=kwargs["campaign_obj"][0].schedule.schedule
								[datetime.today().strftime('%A')]['audio_file_name'])
							if audiofile_obj:
								audiofile = settings.MEDIA_ROOT +"/"+ str(audiofile_obj[0].audio_file)
								kwargs['SERVER'].freeswitch.api('uuid_broadcast',"%s %s"%(kwargs['dialed_uuid'],audiofile))
								return {'non_office_hrs':True,'cust_status':cust_status,'no_agent_audio':no_agent_audio,'c_max_wait_time':c_max_wait_time,'audio_moh_sound':audio_moh_sound}
							else:
								return {'non_office_hrs':True,'cust_status':cust_status,'no_agent_audio':no_agent_audio,'c_max_wait_time':c_max_wait_time,'audio_moh_sound':audio_moh_sound}		
					else:
						audiofile_obj=AudioFile.objects.filter(name=kwargs["campaign_obj"][0].schedule.schedule
							[day_now]['audio_file_name'])
						if audiofile_obj:
							kwargs['SERVER'].freeswitch.api('uuid_answer',"%s"%(kwargs['dialed_uuid']))
							audiofile = settings.MEDIA_ROOT +"/"+ str(audiofile_obj[0].audio_file)
							kwargs['SERVER'].freeswitch.api('uuid_broadcast',"%s %s"%(kwargs['dialed_uuid'],audiofile))
							return {'non_office_hrs':True,'cust_status':cust_status,'no_agent_audio':no_agent_audio,'c_max_wait_time':c_max_wait_time,'audio_moh_sound':audio_moh_sound}
						else:
							return {'non_office_hrs':True,'cust_status':cust_status,'no_agent_audio':no_agent_audio,'c_max_wait_time':c_max_wait_time,'audio_moh_sound':audio_moh_sound}
			return {'cust_status':cust_status,'no_agent_audio':no_agent_audio,'c_max_wait_time':c_max_wait_time,'audio_moh_sound':audio_moh_sound}
		else:
			audiofile_obj = AudioFile.objects.none()
			if holiday_obj.first().holiday_audio:
				audiofile_obj=AudioFile.objects.filter(name=holiday_obj.first().holiday_audio.name)
			if audiofile_obj:
				kwargs['SERVER'].freeswitch.api('uuid_answer',"%s"%(kwargs['dialed_uuid']))
				audiofile = settings.MEDIA_ROOT +"/"+ str(audiofile_obj[0].audio_file)
				kwargs['SERVER'].freeswitch.api('uuid_broadcast',"%s %s"%(kwargs['dialed_uuid'],audiofile))
				return {'non_office_hrs':True,'cust_status':cust_status,'no_agent_audio':no_agent_audio,'c_max_wait_time':c_max_wait_time,'audio_moh_sound':audio_moh_sound}
			else:
				return {'non_office_hrs':True,'cust_status':cust_status,'no_agent_audio':no_agent_audio,'c_max_wait_time':c_max_wait_time,'audio_moh_sound':audio_moh_sound}
		return {'cust_status':cust_status,'no_agent_audio':no_agent_audio,'c_max_wait_time':c_max_wait_time,'audio_moh_sound':audio_moh_sound}		
	except Exception as e:
		print('Exception in fs_set_variables : ',e)
		return {'cust_status':cust_status,'no_agent_audio':no_agent_audio,'c_max_wait_time':c_max_wait_time,'audio_moh_sound':audio_moh_sound}

@freeswicth_server
def fs_set_ibc_contact_id(*args,**kwargs):
	try:
		contact_info, contact_count = get_contact_information(dial_number=kwargs['ic_number'],contact_id=kwargs['contact_id'],callmode='inbound',lead_preview=False, campaign_obj=kwargs['campaign_obj'])
		status = {'success':'successfully'}
		status['contact_info'] = contact_info
		kwargs['SERVER'].freeswitch.api("uuid_setvar_multi","%s cc_agent=%s;contact_id=%s;uniqueid=%s"%(kwargs['dialed_uuid'],kwargs['extension'],kwargs['contact_id'],contact_info["uniqueid"]))
		return status
	except Exception as e:
		print({"error":"from fs_set_ibc_contact_id %s,Coordinate your administrator."%(e)})
		return {}	

@freeswicth_server
def check_ibc_cust_status(*args,**kwargs):
	""" 
	Checking the ibc popup custom status 
	"""
	cust_status = 'false'
	audio_moh_sound = None
	c_max_wait_time = 25
	no_agent_audio = False  
	try:
		cust_status = kwargs['SERVER'].freeswitch.api('uuid_exists',kwargs['dialed_uuid'])
		if kwargs["campaign_obj"][0].dial_method["ibc_popup"]:
			if kwargs["campaign_obj"][0].dial_method["no_agent_audio"]:
				no_agent_audio = kwargs["campaign_obj"][0].dial_method["no_agent_audio"]
				if kwargs["campaign_obj"][0].campaign_variable.max_wait_time > 0:
					c_max_wait_time = kwargs["campaign_obj"][0].campaign_variable.max_wait_time
				if kwargs["campaign_obj"][0].campaign_variable.moh_sound:
					audio_moh_sound = kwargs["campaign_obj"][0].campaign_variable.moh_sound.audio_file.name
		return {'cust_status':cust_status,'no_agent_audio':no_agent_audio,'c_max_wait_time':c_max_wait_time,'audio_moh_sound':audio_moh_sound}
	except Exception as e:
		print({"error":"from check_ibc_cust_status %s."%(e)})
		return {'cust_status':cust_status,'no_agent_audio':no_agent_audio,'c_max_wait_time':c_max_wait_time,'audio_moh_sound':audio_moh_sound}



@freeswicth_server
def fs_park_call(*args,**kwargs):
	""" 
	Putting the call on the park/mute
	"""
	try:
		if kwargs['park_status'] == 'true':
			kwargs['SERVER'].freeswitch.api("uuid_hold","%s"%(kwargs['session_uuid']))
			return ({"success": "call mute"})
		else:
			kwargs['SERVER'].freeswitch.api("uuid_hold"," off %s"%(kwargs['session_uuid']))
		return ({"success": "call unmute"})
	except Exception as e:
		print({"error":"from fs_mute_call %s,Coordinate your administrator."%(e)})
		return {"error":"from fs_mute_call %s,Coordinate your administrator."%(e)}

@freeswicth_server
def fs_send_dtmf(*args,**kwargs):
	"""
	sending dtmf to the freeswitch 
	"""
	try:
		if kwargs['dtmf_digit']:
			kwargs['SERVER'].freeswitch.api("uuid_send_dtmf","%s %s"%(kwargs['dialed_uuid'],str(kwargs['dtmf_digit'])))
			return ({"success": "Dtmf send successfully"})
	except Exception as e:
		print("from fs_send_dtmf %s,Coordinate your administrator."%(e))
		return {"error":"from fs_send_dtmf %s,Coordinate your administrator."%(e)}

@freeswicth_server
def fs_transfer_agent_call(*args,**kwargs):
	""" 
	Tranfer the call from one agent to another agent
	"""
	try:
		dial_status = ''
		if kwargs['transfer_type'] == 'external':
			ori_uuid = uuid.uuid4()
			campaign_obj = Campaign.objects.get(name=kwargs['campaign'])
			trunk_id , dial_string, caller_id, country_code = channel_trunk_single_call(campaign_obj)
			if country_code:
				cn_numeric = country_code+kwargs['dial_number']
			else:
				cn_numeric = kwargs['dial_number']
			if trunk_id:
				usertype='transfer_client'
				if kwargs["transfer_mode"] == "three-way-calling":
					usertype = 'conference_client'
				fs_originate = Template(settings.FS_MANUAL_ORIGINATE).safe_substitute(dict(variables="usertype=%s,cc_agent=%s,trunk_id=%s,origination_caller_id_number=%s,"\
				"origination_uuid=%s,campaign_name=%s,dialed_number=%s,agent-Unique-ID='%s'"%(usertype,kwargs['extension'], trunk_id,caller_id,ori_uuid,kwargs['campaign'],kwargs['dial_number'],kwargs['unique_uuid'])),
				transfer_extension ='000312951420',dial_string=dial_string)
				fs_originate_str = Template(fs_originate).safe_substitute(dict(destination_number=cn_numeric))
				dial_status = kwargs['SERVER'].freeswitch.api("bgapi","%s"%(fs_originate_str))
				if '+OK' in dial_status:
					chennals = pickle.loads(settings.R_SERVER.get("trunk_status") or pickle.dumps({}))
					chennals[str(trunk_id)] += 1
					settings.R_SERVER.set("trunk_status", pickle.dumps(chennals))
			else:
				return {"error":"Trunk configurations error, please coordinate your administrator."}					
		elif kwargs['transfer_type'] == 'internal':
			transfer_uuids = json.loads(settings.R_SERVER.get("transfer_agents").decode("utf-8"))
			if kwargs['transfer_from_agent_uuid'] in transfer_uuids:
				del transfer_uuids[kwargs['transfer_from_agent_uuid']]
				transfer_uuid = json.dumps(transfer_uuids)
				settings.R_SERVER.set("transfer_agents",transfer_uuid)
				ori_uuid = kwargs['transfer_from_agent_uuid'] 
				dial_status='+OK'
			else:
				return {"error":"someone is accepted this call."}	
		else:
			pass 	
		if '+OK' in dial_status:
			# kwargs['SERVER'].freeswitch.api("uuid_bridge","%s %s" %(ori_uuid,kwargs['unique_uuid']))	
			return {"success":"successfully","transfer_from_agent_uuid":kwargs['unique_uuid'],"transfer_number":kwargs['dial_number'],
			'transfer_from_agent_number': kwargs['transfer_from_agent_number'],'transfer_to_agent_uuid':ori_uuid}
		else:
			return {"error":"number is not dialedsuccessfully, please try agian.","transfer_uuid":''}
	except Exception as e:
		print("fs_transfer_agent_call %s"%(e))
		return {"error":"number is not dialedsuccessfully, please try agian.","transfer_uuid":''}

@freeswicth_server
def fs_transferpark_call(*args,**kwargs):
	""" 
	Putting the transfer call on the park/mute
	"""
	try:
		if kwargs['transfer_call_status'] == 'true':
			kwargs['SERVER'].freeswitch.api("uuid_park","%s"%(kwargs['dialed_uuid']))
			if kwargs.get('conf_uuids',''):
				conf_uuids = kwargs['conf_uuids'].split(',')
				for uuid in conf_uuids:
					kwargs['SERVER'].freeswitch.api("uuid_park","%s"%(uuid))
		else:
			kwargs['SERVER'].freeswitch.api("uuid_transfer","%s %s@sla"%(kwargs['dialed_uuid'],kwargs['session_uuid']))
			if kwargs.get('conf_uuids',''):
				conf_uuids = kwargs['conf_uuids'].split(',')
				for uuid in conf_uuids:
					kwargs['SERVER'].freeswitch.api("uuid_transfer","%s %s@sla"%(uuid,kwargs['session_uuid']))
		return ({"success": "call parked"})
	except Exception as e:
		print({"error":"from fs_park_call %s, please try agian."%(e)})
		return {"error":"from fs_park_call %s, please try agian."%(e)}

@freeswicth_server
def fs_transfer_call(*args,**kwargs):
	"""
	Transfering the calls  
	"""
	try:
		if kwargs["transfer_mode"] == "attr-transfer":
			bridge_status=kwargs['SERVER'].freeswitch.api("uuid_bridge","%s %s"%(kwargs['dialed_uuid'],kwargs['transfer_uuid']))
			kwargs['SERVER'].freeswitch.api("uuid_setvar_multi","%s transfer_agent=%s;transfer_status='true';call_mode='transfer';"%(kwargs['dialed_uuid'],kwargs['transfer_number']))
			return {"success":"successfully"}
		else:
			kwargs['SERVER'].freeswitch.api("uuid_transfer","%s %s@sla"%(kwargs['dialed_uuid'],kwargs['session_uuid']))
			if kwargs.get('conf_uuids',''):
				conf_uuids = kwargs['conf_uuids'].split(',')
				for uuid in conf_uuids:
					kwargs['SERVER'].freeswitch.api("uuid_transfer","%s %s@sla"%(uuid,kwargs['session_uuid']))
			kwargs['SERVER'].freeswitch.api("uuid_setvar_multi","%s cc_agent=%s;conference_status='true';call_mode='conference';"%(kwargs['conference_num_uuid'],kwargs['extension']))
			return {"success":"successfully"}
	except Exception as e:
		print({"error":"fs_transferhangup_call %s"%(e)})
		return {"error":"fs_transferhangup_call %s"%(e)}

@freeswicth_server
def fs_transferhangup_call(*args,**kwargs):
	"""
	Hangup the transfered call
	"""
	try:
		if kwargs['transfer_uuid'] != '':
			hangup_status=kwargs['SERVER'].freeswitch.api("uuid_kill",kwargs['transfer_uuid'])
			if '+OK' in hangup_status:
				return {"success":"successfully"}
			else:
				return {"error":"something went wrong, please try again."}
		else:
			return {'success':'successfully'}
	except Exception as e:
		print({"error":"fs_transferhangup_call %s"%(e)})
		return {"error":"fs_transferhangup_call %s"%(e)}

@freeswicth_server
def fs_internal_transferhangup_call(*args,**kwargs):
	""" 
	Internal transfer hangup call
	""" 
	try:
		transfer_hangup_status=kwargs['SERVER'].freeswitch.api("uuid_transfer","%s 00019916"%(kwargs['uuid']))
		return {"success":"successfully"}
	except Exception as e:
		print({"error":"fs_internal_transferhangup_call %s"%(e)})
		return {"error":"fs_internal_transferhangup_call %s"%(e)}

@freeswicth_server
def fs_eavesdrop_activity(*args,**kwargs):
	""" 
	For listen and wishper and barge functionality
	"""
	try:
		if kwargs['isModelshow'] == 'false':
			kwargs['SERVER'].freeswitch.api("uuid_transfer","%s 000%s"%(kwargs['Unique_ID'],kwargs['dialerSession_uuid']))
		if kwargs['title'] != 'dissconnect':
			if kwargs['title'] == 'whisper':
				kwargs['SERVER'].freeswitch.api("uuid_recv_dtmf","%s 2"%(kwargs['Unique_ID']))
			elif kwargs['title'] == 'barge':
				kwargs['SERVER'].freeswitch.api("uuid_recv_dtmf","%s 3"%(kwargs['Unique_ID']))
			elif kwargs['title'] == 'listen':
				kwargs['SERVER'].freeswitch.api("uuid_recv_dtmf","%s 0"%(kwargs['Unique_ID']))
		else:
			kwargs['SERVER'].freeswitch.api("uuid_transfer","%s 00019916"%(kwargs['Unique_ID']))
		return {'title':kwargs['title'],'isModelshow':kwargs['isModelshow']}		
	except Exception as e:
		print({"error":"fs_eavesdrop_activity %s"%(e)})

@freeswicth_server
def enable_wfh_user(*args,**kwargs):
	""" 
	Enabling the workfrom home functionality
	"""
	try:
		camp_obj = Campaign.objects.get(name=kwargs['campaign'])
		call_type, state = get_calltype_state(camp_obj.dial_method)
		if 'wfh_agent_req_dial' in kwargs:
			trunk_id , dial_string, caller_id, country_code = channel_trunk_single_call(camp_obj)
			if country_code:
				cn_numeric = country_code+kwargs['customer_number'][-10:]
			else:
				cn_numeric = kwargs['customer_number'][-10:]
			if trunk_id:
				import time
				ori_uuid = uuid.uuid4()
				time.sleep(8)
				dial_string = Template(dial_string).safe_substitute(destination_number=cn_numeric)
				status = kwargs['SERVER'].freeswitch.api("originate","{usertype='wfh-agent-req-dial',trunk_id=%s,wfh='true',origination_uuid=%s,origination_caller_id_number=%s,cc_agent=%s,campaign=%s,caller_id=%s,outbound_dial_method=%s}%s 12345 xml default" %(trunk_id, ori_uuid,caller_id,kwargs['extension'],kwargs['campaign'],caller_id,camp_obj.dial_method['outbound'],dial_string))
				kwargs['session_uuid'] = ori_uuid
				if '-ERR' in status:
					return {"error":"user mobile number is not rechable.."}
				else:
					chennals = pickle.loads(settings.R_SERVER.get("trunk_status") or pickle.dumps({}))
					chennals[str(trunk_id)] += 1
					settings.R_SERVER.set("trunk_status", pickle.dumps(chennals))
		AGENTS = {}
		event_time = datetime.now().strftime('%H:%M:%S')
		AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or
			pickle.dumps(AGENTS))
		user = UserVariable.objects.get(extension=kwargs['extension'])
		AGENTS[kwargs['extension']] = {}
		AGENTS[kwargs['extension']]['username'] = user.user.username
		AGENTS[kwargs['extension']]['login_status'] = True
		AGENTS[kwargs['extension']]['login_time'] = datetime.now().strftime('%H:%M:%S')
		AGENTS[kwargs['extension']]['campaign'] = kwargs['campaign']
		AGENTS[kwargs['extension']]['dialer_login_status'] = True
		AGENTS[kwargs['extension']]['dialer_login_time'] = event_time
		AGENTS[kwargs['extension']]['status'] = 'Ready'
		AGENTS[kwargs['extension']]['state'] = state
		AGENTS[kwargs['extension']]['event_time'] = event_time
		AGENTS[kwargs['extension']]['call_type'] = call_type
		AGENTS[kwargs['extension']]['dial_number'] = ''
		AGENTS[kwargs['extension']]['call_timestamp'] = ''
		AGENTS[kwargs['extension']]['dialerSession_switch'] = args[0]
		AGENTS[kwargs['extension']]['dialerSession_uuid'] = kwargs['session_uuid']
		AGENTS[kwargs['extension']]['wfh'] = True
		updated_agent_dict = pickle.loads(settings.R_SERVER.get("agent_status"))
		updated_agent_dict[kwargs['extension']] = AGENTS[kwargs['extension']]
		settings.R_SERVER.set("agent_status", pickle.dumps(updated_agent_dict))
		campaigns = user.campaign			
		for campaign in campaigns:
			if campaign.name == kwargs['campaign']:
				kwargs['SERVER'].freeswitch.api("callcenter_config","tier add %s %s %s %s" % (kwargs['campaign'],kwargs['extension'],
				user.level, user.position))
			else:
				kwargs['SERVER'].freeswitch.api("callcenter_config","tier del %s %s" % (campaign.name, kwargs['extension']))			
		activity_dict = {}
		activity_dict["user"] = user.user
		activity_dict["event"] = "WFH AGENT LOGIN"
		activity_dict["event_time"] = datetime.now()
		activity_dict["campaign_name"] = kwargs['campaign']
		activity_dict["break_type"] = None
		create_agentactivity(activity_dict)
		return
	except Exception as e:
		print({"error":"enable_wfh_user %s"%(e)})
		return

def get_contact_information(dial_number,contact_id,callmode,lead_preview=False, campaign_obj={}):
	""" 
	Get the contact information of the contact
	"""
	contact_info = {'id':0,'numeric':dial_number,'alt_numeric':{},'status':'NewContact','uniqueid':''}
	contact_count = 1
	if not lead_preview:
		if contact_id:
			contact_info_obj = Contact.objects.filter(id=contact_id)
			if contact_info_obj.exists():
				contact_info = ContactSerializer(contact_info_obj.first()).data
		else:
			####### This will call when manual and inbound call phonebook_none is to get data from contact without phonebook #######			
			phonebook =[]
			contact_info_data = []
			phonebook = Phonebook.objects.filter(campaign=campaign_obj.id).values('id')
			query = Q(phonebook_id__in=phonebook)|Q(campaign=campaign_obj.name)
			contact_info_obj = Contact.objects.filter(query).filter(numeric=dial_number)
			phonebook_none = contact_info_obj.exclude(phonebook=None)
			if phonebook_none.exists():
				contact_info_data = ContactSerializer(contact_info_obj, many=True).data
			if not phonebook_none.exists():
				contact_number = []
				alt_query = Q(numeric=dial_number)
				if campaign_obj.search_alternate:
					contact_number = TempContactInfo.objects.filter(campaign=campaign_obj.name, alt_numeric__values__contains=[dial_number],status='Locked').values_list("id", flat=True)
					alt_contact_list = AlternateContact.objects.filter(alt_numeric__values__contains=[dial_number]).values_list('uniqueid',flat=True)
					alt_query = Q(uniqueid__in=list(alt_contact_list)) | Q(numeric=dial_number)
				contact_number_data = Contact.objects.filter(query).filter(alt_query).exclude(id__in=contact_number)
				contact_info_data = ContactSerializer(contact_number_data, many=True).data
			if contact_info_data and len(contact_info_data) == 1:
				contact_info = contact_info_data[0]
				contact_count = 1
			elif contact_info_data:
				contact_info = contact_info_data
				contact_count = len(contact_info)
	else:
		if callmode in ['progressive','preview']:
			contact_info_obj = TempContactInfo.objects.filter(numeric=dial_number,
				id=contact_id,status='Locked')
			if contact_info_obj.exists():
				contact_info = contact_info_obj.values('phonebook').first()
	if type(contact_info) == dict and 'status' in contact_info and contact_info['status'] == 'NewContact':
		alt_number_val = AlternateContact.objects.filter(numeric=dial_number).values('alt_numeric').first()
		if alt_number_val:
			contact_info['alt_numeric'] = alt_number_val['alt_numeric']
	return contact_info, contact_count

@freeswicth_server
def click_to_call_initiate(*args,**kwargs):
	""" 
	click to call functionality 
	"""
	try:
		campaign_obj = Campaign.objects.get(name=kwargs['campaign'])
		trunk_id , dial_string, caller_id, country_code = channel_trunk_single_call(campaign_obj)
		if trunk_id:
			ori_uuid1 = uuid.uuid4()
			if country_code:
				agent_numeric = country_code+str(kwargs['agent_num'])
			else:
				agent_numeric = kwargs['agent_num']
			dial_string = Template(dial_string).safe_substitute(destination_number=agent_numeric)
			status = kwargs['SERVER'].freeswitch.api("originate","{usertype='ctc_agent',trunk_id=%s,origination_uuid=%s,origination_caller_id_number=%s}%s &park()" %(trunk_id, ori_uuid1,caller_id,dial_string))
			if '+OK' in status:
				trunk_id , dial_string, caller_id, country_code = channel_trunk_single_call(campaign_obj)
				if country_code:
					cn_numeric = country_code+str(kwargs['customer_num'])
				else:
					cn_numeric = kwargs['customer_num']
				if trunk_id:
					ori_uuid2 = uuid.uuid4()
					dial_string = Template(dial_string).safe_substitute(destination_number=cn_numeric)
					status = kwargs['SERVER'].freeswitch.api("originate","{usertype='client',trunk_id=%s,origination_uuid=%s,origination_caller_id_number=%s,cc_agent=%s,campaign=%s,call_mode='click-to-call',disposition='Invalid Number'}%s &park()" %(trunk_id,ori_uuid2,caller_id,kwargs['extension'],kwargs['campaign'],dial_string))
					kwargs['SERVER'].freeswitch.api("uuid_bridge","%s %s" %(ori_uuid2,ori_uuid1))
					if '+OK' in status:
						chennals = pickle.loads(settings.R_SERVER.get("trunk_status") or pickle.dumps({}))
						chennals[str(trunk_id)] += 1
						settings.R_SERVER.set("trunk_status", pickle.dumps(chennals))
					return {"success":"Number is dialedsuccessfully","dialed_uuid":ori_uuid2}
				else:
					return {"error":"channel is not available","dialed_uuid":None}
			else:
				return {"error":"user mobile number is not rechable..","dialed_uuid":None}
		else:
			return {"error":"channel is not available","dialed_uuid":None}
	except Exception as e:
		print("error from click-to-call : ",e)

@freeswicth_server
def wfh_progressive_call(*args,**kwargs):
	""" 
	progressive calling with work from home
	"""
	try:
		user_obj = UserVariable.objects.get(extension=kwargs.get('extension')).user
		username = user_obj.username
		temp_contact = get_temp_contact(username,kwargs.get('campaign'))
		if temp_contact:
			contact_obj = Contact.objects.get(id = temp_contact.id)
			speech_text = "dialed customer name %s %s and number is %s"%(contact_obj.first_name,contact_obj.last_name,",".join(contact_obj.numeric))
			language = 'en'
			myobj = gTTS(text=speech_text, lang=language, slow=False)
			file = settings.MEDIA_ROOT+'/'+kwargs['session_uuid']+".mp3"
			myobj.save(file)
			kwargs['SERVER'].freeswitch.api('uuid_broadcast',"%s %s"%(kwargs['session_uuid'],file))
			os.chmod(file, 0o777)
			agent_status = kwargs['SERVER'].freeswitch.api('uuid_exists',kwargs['session_uuid'])
			if agent_status != 'false':
				wfh_agents = pickle.loads(settings.R_SERVER.get("wfh_agents") or pickle.dumps({}))
				ori_uuid = uuid.uuid4()
				if wfh_agents:
					wfh_agents[str(ori_uuid)]={"c_num":contact_obj.numeric,'c_username':contact_obj.first_name +''+contact_obj.last_name}
				else:
					wfh_agents={str(ori_uuid):{"c_num":contact_obj.numeric,'c_username':contact_obj.first_name +''+contact_obj.last_name}}
				settings.R_SERVER.set("wfh_agents",pickle.dumps(wfh_agents))
				campaign_obj = Campaign.objects.get(name=kwargs['campaign'])
				trunk_id , dial_string, caller_id, country_code = channel_trunk_single_call(campaign_obj)
				if country_code:
					cn_numeric = country_code+temp_contact.numeric
				else:
					cn_numeric = temp_contact.numeric
				if trunk_id:
					fs_originate = Template(settings.FS_WFH_PROGRESSIVE_ORIGINATE).safe_substitute(dict(variables="usertype='client',trunk_id=%s,cc_agent=%s,return_ring_ready=true,origination_caller_id_number=%s,origination_uuid=%s,disposition='Invalid Number',campaign=%s,"\
						"dialed_number=%s,call_mode='progressive',wfh_call=True,phonebook=%s,uniqueid=%s"%(trunk_id, kwargs['extension'],caller_id,
							ori_uuid,kwargs['campaign'],temp_contact.numeric,temp_contact.phonebook.name,temp_contact.uniqueid)),
						transfer_extension ='000312951420',dial_string=dial_string)
					fs_originate_str = Template(fs_originate).safe_substitute(dict(contact_id=temp_contact.contact_id,destination_number=cn_numeric))
					time.sleep(10)
					dial_status = kwargs['SERVER'].freeswitch.api("originate","%s"%(fs_originate_str))
					if '+OK' in dial_status:
						kwargs['SERVER'].freeswitch.api("uuid_setvar_multi"," %s cc_customer=%s;phonebook=%s;contact_id=%s,caller_id=%s,uniqueid=%s" %(kwargs['session_uuid'],cn_numeric,temp_contact.phonebook.name,temp_contact.contact_id,caller_id,temp_contact.uniqueid))
						kwargs['SERVER'].freeswitch.api("uuid_bridge","%s %s" %(ori_uuid,kwargs['session_uuid']))
						TempContactInfo.objects.get(contact_id = temp_contact.contact_id).delete()
						return {"success":"Number is dialedsuccessfully"}
					else:
						return {"error":"user mobile number is not rechable.."}
				else:
					return {"error":"Chennals is not available"}
		else:
			return {"error":"customer data is completed....."}

	except Exception as e:
		print("error from wfh_progressive_call : ",e)

def get_calltype_state(dial_method):
	""" 
	based on dial method will give the call type 
	"""
	state ='Idle'
	call_type = ''
	if dial_method['inbound'] and dial_method['outbound'] =='Predictive' and not dial_method['ibc_popup']:
		call_type = 'blended'
		state = 'Blended Wait'
	elif dial_method['inbound'] and not dial_method['outbound']:
		call_type = 'inbound'
		state = 'Inbound Wait'
	elif dial_method['outbound'] =='Predictive':
		call_type = 'predictive'
		state = 'Predictive Wait'
	return call_type, state
