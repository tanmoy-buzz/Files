import os,sys
import ntpath
from django.shortcuts import render
from django.http import HttpResponseRedirect,HttpResponse, StreamingHttpResponse, JsonResponse
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import utc
from django.views.decorators.cache import never_cache, cache_page
from django.conf import settings
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.core.cache import cache
from django.db.models import Q, F, Sum, TimeField, Value, Count, Prefetch, CharField, DateField, DateTimeField, Func, ExpressionWrapper, When, Case, TextField
from django.db.models.functions import Cast, Coalesce, Concat, Substr, NullIf
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
import csv
import itertools
from django.contrib.sessions.models import Session
from django.utils import timezone
import pandas as pd
import numpy as np
import json
import pickle
import random
from datetime import datetime, date,timedelta
import time
from dateutil.relativedelta import relativedelta
import re
import glob
import requests
from operator import itemgetter
from django.core.files import File
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework import pagination
from scripts.pagination import DatatablesPageNumberPagination
from scripts.renderers import DatatablesRenderer
from scripts.filters import DatatablesFilterBackend
from scripts.fsautodial import scrub
from .serializers import *
from .models import (
	User,UserRole,Group,Campaign,CampaignVariable, RelationTag,
	USER_TIMEZONE,DiallerEventLog,
	CurrentCallBack, CallBackContact, Abandonedcall,Notification,
	CdrFeedbck, SnoozedCallback,SkilledRouting, CSS, StickyAgent,ThirdPartyApi,PhonebookBucketCampaign, AdminLogEntry,
	InGroupCampaign,CampaignPriority, EmailTemplate, Daemons, FullertonTempData,PasswordChangeLogs

)
from flexydial.constants import (Status, REPORTS_LIST, TRUNK_TYPE, UserStatus, DIAL_KEY_OPTIONS, PROTOCOL_CHOICES, CALL_MODE,
	CALL_TYPE, OPERATORS_CHOICES, LOGICAL_OPERATOR_CHOICES, TRANSFER_MODE, ACCESS_LEVEL, OUTBOUND, API_MODE, FIELD_TYPE,
	DISPO_FIELD_TYPE, TIMER_SEC, PAGINATE_BY_LIST, CONTACT_STATUS, MONTHS, Gateway_Mode, MODULES as flexydial_modules,PasswordChangeType,
	STRATEGY_CHOICES,COUNTRY_CODES,SHOW_DISPOS_TYPE)

from crm.models import (CrmField, TempContactInfo, Phonebook,
			Contact,CrmField,ContactInfo, DownloadReports, LeadBucket, AlternateContact)
from crm.serializers import (AgentCrmFieldSerializer,TempContactInfoSerializer, ContactSerializer,CssContactSerializer, AssignedContactInfoSerializer, ContactListSerializer, LeadBucketSerializer, AlternateContactSerializer)
from crm.utility import crm_field_value_schema, get_customizable_crm_fields,get_customizable_crm_fields_for_template
from flexydial.views import (check_permission, get_paginated_object, data_for_pagination, get_active_campaign,
	data_for_vue_pagination, sendSMS, csvDownloadTemplate, create_admin_log_entry, sendsmsparam)
from callcenter.signals import (fs_pre_del_user)
from callcenter.schedulejobs import (leadrecycle_add,leadrecycle_del,schedulereports_download,sched,remove_scheduled_job)
from .utility import (agentactivity_data,redirect_user,convert_timedelta_hrs ,action_agent_performance_report, get_object, get_pre_campaign_edit_info,
	get_pre_campaign_create_info, validate_data, filter_queryset, paginate_queryset, get_paginated_response,
	validate_uploaded_users_file, upload_users, get_current_users, set_agentReddis,
	create_agentactivity, get_formatted_agent_activities, get_campaign_users, get_agent_mis,get_campaign_mis,
	dummy_agent_activity,group_add_user_rpc, get_user_group, get_user_role, get_user_switch,
	get_user_dialtrunk, get_user_disposition, get_user_pausebreak, get_user_campaignschedule,
	get_model_data, validate_uploaded_dnc,upload_dnc_nums,submit_feedback, customer_detials, convert_into_timedelta,
	total_list_users,camp_list_users,user_hierarchy, user_hierarchy_object, update_contact_on_css, get_transform_key, update_contact_on_portifolio, 
	validate_third_party_token,get_temp_contact,get_contact_data, upload_template_sms,get_crm_fields_dict, channel_trunk_single_call, DownloadCssQuery,get_campaign_did, get_group_did,DownloadCssQuery,diff_time_in_seconds,
	save_report_column_visibility, get_report_visible_column,save_email_log, get_used_did, get_used_did_by_pk,convert_into_timeformat, email_connection, check_non_admin_user, getDaemonsStatus,upload_holiday_dates,delete_all_unexpired_sessions_for_user)

from .decorators import (user_validation, group_validation,campaign_validation,
	campaign_edit_validation, phone_validation, dispo_validation, relationtag_validation,
	pausebreak_validation, call_time_validation, script_validation,
	audio_file_validation, user_role_validation, switch_validation, trunk_validation,
	check_read_permission, check_create_permission, check_update_permission,skill_validation,
	skill_edit_validation,thirdparty_validation,thirdparty_edit_validation,voiceblaster_validation,
	voiceblaster_edit_validation,holiday_validation,edit_third_party_token)
from dialer.dialersession import (dial,twinkle_session,hangup,autodial_session,autodial_session_hangup,
	inbound_call,fs_set_variables,fs_park_call,fs_transfer_agent_call,fs_transferpark_call,
	fs_transferhangup_call,fs_transfer_call,fs_internal_transferhangup_call,fs_administration_session,
	fs_administration_hangup,fs_eavesdrop_activity,fs_set_ibc_contact_id,inbound_stiky_agent_bridge,click_to_call_initiate,on_break,check_ibc_cust_status,fs_send_dtmf)

from .constants import four_digit_number, three_digits_list
CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)
cwd = os.path.join(settings.BASE_DIR, 'static/')
AGENTS = {}
CAMPAIGNS = {}
import uuid
from shutil import make_archive, rmtree
import calendar
import base64
import subprocess
from gtts import gTTS
import csv

def save_csv(file_name, list):
	"""
	Saving the list values into the csv file
	"""
	try:
		with open(file_name, 'w+', encoding='utf-8') as file:
			for row in list:
				row.to_csv(file, index=False, header=file.tell() == 0,encoding='utf-8')
	except Exception as e:
		print(e)

@csrf_exempt
# @cache_page(CACHE_TTL)
def curl_addsip(request,domain):
	"""
	Adding the information into the directory html 
	for generating the xml files 
	"""
	domain = Switch.objects.filter(name=domain)
	if domain:
		user_ids = total_list_users(domain[0].ip_address)
		agent_profile = UserVariable.objects.filter(user__id__in = user_ids,user__is_active=True).values('domain__ip_address',
			'user__username','user__caller_id','extension','user__id','device_pass','user__call_type').order_by('domain__ip_address','user__username','extension').prefetch_related()
	else:
		agent_profile={}
	context = {'profile' : agent_profile}
	return render(request,'fsconfig/directory.html',context,content_type='application/xml')

@csrf_exempt
# @cache_page(CACHE_TTL)
def curl_loadcc(request,domain):
	""" 
	Adding the information into ccconf.html 
	for generating the xml file 
	"""
	domain = Switch.objects.filter(name=domain)
	if domain:
		cc_mod = CampaignVariable.objects.filter(campaign__switch__ip_address = domain[0].ip_address).select_related()
		user_ids = total_list_users(domain[0].ip_address)
		cc_user = User.objects.filter(Q(id__in = user_ids) & Q(is_active=True))
		r_campaigns = pickle.loads(settings.R_SERVER.get("campaign_status") or pickle.dumps(CAMPAIGNS))
		context = {'Campaign' : cc_mod, 'User' : cc_user,'r_campaigns':r_campaigns}
	else:
		context={}
	return render(request,'fsconfig/ccconf.html', context,content_type='application/xml')

class Echo(object):
	""" 
	Echoing the csv values back again 
	"""
	def write(self, value):
		return value

def convert_to_zip(result):
	"""
	Converting into the zip file the list of contacts
	"""
	if result:
		path = settings.MEDIA_ROOT+'/'+str(uuid.uuid4())
		os.mkdir(path)
		for detail in result:
			current_file = '/var/spool/freeswitch/default/'+detail.ring_time.strftime('%d-%m-%Y-%H-%M')+'_'+detail.customer_cid+'_'+str(detail.session_uuid)+'.mp3'
			if os.path.isfile(current_file):
				os.system('cp '+current_file+' '+path)
				path_to_zip = make_archive(path, "zip", path)
			else:
				pass
		rmtree(path)
		return open(path_to_zip,'rb')
	return ''

def common_functionality_to_store_data(data, user):
	"""
	Common data while submiting the feedback 
	"""
	status = {}
	campaign_name = data.get('campaign','')
	call_type = data.get('call_type', '')
	switch_ip = data.get('switch_ip', '')
	autodial_status = data.get('autodial_status','')
	agent_state = data.get('agent_state','')
	# Track agent activities
	agent_data = get_formatted_agent_activities(data)
	agent_data["user"] = user
	agent_data["campaign_name"] = campaign_name
	agent_data["event"] = data.get("event", "")
	agent_data["event_time"] = datetime.now()
	if data.get("break_type",'') not in ["Ready","NotReady"]:
		agent_data["break_type"] = data.get("break_type",'')
	agent_data["break_time"] =  datetime.strptime(data.get("break_time",'0:0:0'), '%H:%M:%S').time()
	if autodial_status == 'false' or agent_state in ['InCall','Feedback']:
		agent_data["predictive_wait_time"] = "0:0:0"
	if call_type == 'autodial':
		if autodial_status != 'false':
			autodial_session(switch_ip, extension=user.extension,
				uuid=data.get('uuid', ''),sip_error=data.get('sip_error','true'))
	if campaign_name:
		campaign = Campaign.objects.get(name=campaign_name)
		pbc_obj = PhonebookBucketCampaign.objects.filter(id=campaign.id)
		if pbc_obj.first().agent_login_count > 0:
			pbc_obj.update(agent_login_count=F('agent_login_count')-1)
	create_agentactivity(agent_data)
	if data.get("event", "") != "Duplicate window" and not "Force Logout" in data.get("event", "") and not "Internet connection failure" in data.get("event",""):
		AGENTS = {}
		AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or
			pickle.dumps(AGENTS))
		set_agentReddis(AGENTS,user)
		updated_agent_dict = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
		updated_agent_dict[user.extension]= AGENTS[user.extension]
		settings.R_SERVER.set("agent_status", pickle.dumps(updated_agent_dict))
	status = {}
	if agent_state in ['InCall','Feedback']:
		status = submit_feedback(user,data)
	return status

class LoginAPIView(APIView):
	"""
	This view is used to validate user credentials and
	redirect user according to his permission
	"""
	renderer_classes = [TemplateHTMLRenderer]
	template_name = 'login.html'
	permission_classes = [AllowAny]

	def get(self, request):
		forgot_password = False
		if not request.user.is_anonymous:
			return redirect_user(request,request.user)
		ps_obj = PasswordManagement.objects.filter().first()
		if ps_obj:
			forgot_password =ps_obj.forgot_password
		return Response({"forgot_password":forgot_password})

	def post(self, request):
		## Data for login validation 
		serializer = LoginSerializer(data=request.data)
		AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps({}))
		PASSWORD_ATTEMPTS = pickle.loads(settings.R_SERVER.get("password_attempt_status") or pickle.dumps({}))
		forgot_password = False
		password_obj = PasswordManagement.objects.filter().first()
		today = date.today()  # Get today's date
		# Calculate start and end times
		start_date = today  # Midnight at the beginning of the day
		end_date = today + timedelta(days=1)  # Midnight at the beginning of the next day
		start_end_date_filter = Q(created__gte=start_date)&Q(created__lte=end_date)
		if password_obj:
			forgot_password = password_obj.forgot_password
		if serializer.is_valid():
			username = request.data["username"].strip(" ")
			password = base64.b64decode(request.data["password"]).decode('utf-8')
			user = authenticate(username=username, password=password)
			if user is not None:
				if user.is_active:
					stats = delete_all_unexpired_sessions_for_user(user)
					session_extension = [agent.extension for agent in get_current_users()
							if agent.extension == user.extension]
					if session_extension:
						return Response({"error": "You are already LogIn"})
					elif user.user_role == None and not user.is_superuser:
						return Response({"error": "User Role is not defined to this user.Please Contact To your admin",'forgot_password':forgot_password})
					else:
						AGENTS[user.extension] = {}
					login(request, user)
					AGENTS = set_agentReddis(AGENTS,user)
					AGENTS[user.extension]['name'] = user.first_name + ' ' + user.last_name
					AGENTS[user.extension]['screen'] = 'AgentScreen'
					AGENTS[user.extension]['login_time'] = datetime.now().strftime('%H:%M:%S')
					AGENTS[user.extension]['call_count'] = CallDetail.objects.filter(user__username=user.username).filter(start_end_date_filter).count()
					updated_agent_dict = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
					updated_agent_dict[user.extension] = AGENTS[user.extension]
					settings.R_SERVER.set("agent_status", pickle.dumps(updated_agent_dict))
					#set password attempt count to zero 
					PASSWORD_ATTEMPTS[username] = 0
					settings.R_SERVER.set('password_attempt_status',pickle.dumps(PASSWORD_ATTEMPTS))
					# store login time to agent activity
					time = datetime.strptime("0:0:0", '%H:%M:%S').time()
					login_time = datetime.now()

					request.session['login_time'] = login_time.isoformat()

					#### Set enabled modules into sesssion ####
					modules_queryset = Modules.objects.filter(parent=None, status='Active', is_menu=True).order_by('sequence')
					request.session['modules'] = ModulesSerializer(modules_queryset, many=True).data
					request.session['login_time'] = login_time.isoformat() 

					#Track agent activity
					if request.user.user_role and request.user.user_role.access_level == 'Agent': 
						activity_list = ['tos', 'app_time', 'dialer_time', 'wait_time',
						'media_time', 'spoke_time', 'preview_time',
						'predictive_time', 'feedback_time', 'break_time']
						activity_dict = dict.fromkeys(activity_list, time)
						activity_dict["user"] = request.user
						activity_dict["event"] = "LOGIN"
						activity_dict["event_time"] = login_time
						activity_dict["campaign_name"] = ""
						activity_dict["break_type"] = ""
						create_agentactivity(activity_dict)
					#Track supervisors  login activity 
					login_activity = False
					if request.user.is_superuser or (request.user.user_role and request.user.user_role.access_level in ['Admin','Manager','Supervisor']):
						AGENTS[user.extension]['screen'] = 'AdminScreen'
						updated_agent_dict = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
						print(updated_agent_dict,'---------------------@@@@@@----------------')
						if user.extension not in  updated_agent_dict:
							updated_agent_dict[user.extensioin]={}
						updated_agent_dict[user.extension].update(AGENTS[user.extension])
						settings.R_SERVER.set("agent_status", pickle.dumps(updated_agent_dict))
						login_activity = True
					if request.user.is_superuser:
						login_activity = True
					if login_activity:
						AdminLogEntry.objects.create(created_by=request.user, change_message=request.user.username+" login to application",
						action_name='4',event_type='LOGIN')
					return redirect_user(request,user)
				else:
					if username in PASSWORD_ATTEMPTS:
						if password_obj:
							if PASSWORD_ATTEMPTS[username] >= password_obj.max_password_attempt:
								error_dict = {"error": "This account is Locked Please Try to User Forgot Password or Contact Administrator",'forgot_password':forgot_password}
						else:	
							error_dict = {"error": "This account is not active ,please contact Administrator",'forgot_password':forgot_password}
					return Response(error_dict)
			else:
				user_obj = User.objects.filter(username=username)
				if user_obj.exists():
					if password_obj:
						if username in PASSWORD_ATTEMPTS:
							if PASSWORD_ATTEMPTS[username] >= password_obj.max_password_attempt:
								error_dict = {"error": "This account is Locked Please Try to User Forgot Password or Contact Administrator",'forgot_password':forgot_password}
								user_int = User.objects.get(username=username)
								user_int.is_active = False
								user_int.save()
								return Response(error_dict)
							else:
								PASSWORD_ATTEMPTS[username] += 1
						else: 
							PASSWORD_ATTEMPTS[username] = 1 
						settings.R_SERVER.set('password_attempt_status',pickle.dumps(PASSWORD_ATTEMPTS))
		error_dict = {"error": "Username or Password is incorrect",'forgot_password':forgot_password}
		return Response(error_dict)
class LogoutAPIView(LoginRequiredMixin, APIView):
	"""
	This will logout the user from application
	"""
	login_url = '/'
	def get(self,request,makeInactive=''):
		logout_activity =  False
		AGENTS = {}
		AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or
				pickle.dumps(AGENTS))
		if request.user.extension in AGENTS.keys():
			del AGENTS[request.user.extension]
			settings.R_SERVER.set("agent_status", pickle.dumps(AGENTS))
		r_campaigns = pickle.loads(settings.R_SERVER.get("campaign_status") or pickle.dumps(CAMPAIGNS))
		for campaign in r_campaigns:
			unique_extensions = list(set(r_campaigns[campaign]))
			if request.user.extension in unique_extensions:
				unique_extensions.remove(request.user.extension)
				r_campaigns[campaign]=unique_extensions
		settings.R_SERVER.set("campaign_status", pickle.dumps(r_campaigns))
		if makeInactive:
			request.user.is_active = False
			request.user.save()
		
		la_count = agent_count= dl_count = 0
		if request.user.is_superuser or request.user.user_role.access_level in ['Admin','Manager','Supervisor']:
			logout_activity = True
		if logout_activity:
			last_event_time = AdminLogEntry.objects.filter(created_by=request.user,event_type='LOGIN').last()
			if last_event_time:
				log_time = last_event_time.created  
				login_activity_time = datetime.now() - log_time
				login_duration_time = (datetime.min + login_activity_time).time()
				AdminLogEntry.objects.create(created_by=request.user, change_message=request.user.username+" logout to application",
							action_name='4',event_type='LOGOUT', login_duration=login_duration_time)
		logout(request)
		if request.is_ajax():
			fs_administration_hangup(request.GET.get('variable_sip_from_host'),uuid=request.GET.get('Unique-ID'))
			return JsonResponse({'Success':"successfully loggedout."})
		return HttpResponseRedirect(reverse('login'))
		
class ResetPasswordApiView(LoginRequiredMixin, APIView):
	"""
	This view is to reset agent password
	"""
	def post(self,request):
		userId = request.POST.get('agentId','')
		password = base64.b64decode(request.data["new_password"]).decode('utf-8')
		PASSWORD_ATTEMPTS = pickle.loads(settings.R_SERVER.get("password_attempt_status") or pickle.dumps({}))
		if User.objects.filter(pk=userId).exists():
			user = User.objects.get(pk=userId)
			user.set_password(password)
			user.password_date = date.today()
			user.save()
			PASSWORD_ATTEMPTS[user.username] = 0
			settings.R_SERVER.set('password_attempt_status',pickle.dumps(PASSWORD_ATTEMPTS))
			PasswordChangeLogs.objects.create(username=user.username,changed_by=request.user,change_type=PasswordChangeType[0][0])
			return Response({"msg":"Password Updated Successfully for user "+user.username})
		return JsonResponse({"error":"User not found"},status=404)

class ResetWfhPasswordApiView(LoginRequiredMixin, APIView):
	"""
	This view is to reset agent wfh password
	"""
	def post(self,request):
		userId = request.POST.get('agentId','')
		if UserVariable.objects.filter(user_id=userId).exists():
			user_var = UserVariable.objects.get(user_id=userId)
			user_var.wfh_password = request.POST.get('wfh_newpassword')
			user_var.save()
			return Response({"msg":"Password Updated Successfully for user "})
		return JsonResponse({"error":"User not found"},status=404)

class EmergencyLogoutApiView(LoginRequiredMixin, APIView):
	"""
	This view is to emergancy logout use
	"""
	def post(self,request):
		agent_activity_data = {}
		AGENTS = {}
		extension = request.POST.get('extension','')
		role_name = request.POST.get('role_name','')
		user = UserVariable.objects.get(extension=extension).user
		userId = user.id
		active_sessions = Session.objects.filter(expire_date__gte=datetime.now())
		for session in active_sessions:
			if session.get_decoded().get('_auth_user_id') == str(userId):
				last_request = datetime.fromtimestamp(session.get_decoded().get('last_request'))
				now = datetime.now()
				if role_name != "agent" or (now-last_request).seconds>=30:
					agent_activity_data['user'] = user
					agent_activity_data["event"] = "Force logout by "+request.user.role_name+" "+request.user.username
					agent_activity_data["event_time"] = datetime.now()
					create_agentactivity(agent_activity_data)
					session.delete()
					AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
					del AGENTS[extension]
					settings.R_SERVER.set("agent_status", pickle.dumps(AGENTS))
					return JsonResponse({"success":"Force logout is successfull"})
				else:
					return JsonResponse({"user_logged_in":"True"})
		return JsonResponse({"error": "User is already in logout state"})

class EmergencyLogoutAllUserApiView(LoginRequiredMixin, APIView):
	"""
	This view is to emergancy logout use
	"""
	def post(self,request):
		agent_activity_data = {}
		AGENTS = {}
		extension = request.POST.get('extension','')
		role_name = request.POST.get('role_name','')
		userId = request.user.id
		all_user = request.POST.get('all_user','')
		active_sessions = Session.objects.filter(expire_date__gte=datetime.now())
		user_list = []
		for session in active_sessions:
			if session.get_decoded().get('_auth_user_id') != str(userId):
				user = User.objects.get(id=session.get_decoded().get('_auth_user_id'))
				if user.is_superuser:
					role_name = "admin"
				else:
					role_name = user.user_role.name
				last_request = datetime.fromtimestamp(session.get_decoded().get('last_request'))
				now = datetime.now()
				if role_name == "agent" and (now-last_request).seconds>=30:
					agent_activity_data['user'] = user
					agent_activity_data["event"] = "Force logout by "+request.user.role_name+" "+request.user.username
					agent_activity_data["event_time"] = datetime.now()
					create_agentactivity(agent_activity_data)
					AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
					if user.extension in AGENTS:
						del AGENTS[user.extension]
						settings.R_SERVER.set("agent_status", pickle.dumps(AGENTS))
					session.delete()
				elif role_name != "agent":
					create_admin_log_entry(request.user, "","7",'LOGOUT',user.username)
					session.delete()
					AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
					if user.extension in AGENTS:
						del AGENTS[user.extension]
						settings.R_SERVER.set("agent_status", pickle.dumps(AGENTS))
				else:
					user_list.append(user.extension)
		return JsonResponse({"user_list": user_list})

@method_decorator(check_read_permission, name='get')
class DashBoardApiView(LoginRequiredMixin, APIView):
	"""
	This view is used to gives a graphical and overall telephony
	status  
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "admin/dashboard.html"

	def get(self, request, **kwargs):
		AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
		camp_name, active_camp, noti_count = get_active_campaign(request)
		team_extensions = user_hierarchy(request,camp_name)
		agent_count = UserVariable.objects.filter(extension__in=team_extensions).values_list('user_id',flat=True).count()
		la_count = lo_count = dl_count = pg_count = pd_count = pv_count = ic_count = mu_count = 0
		ac_camp_count = lead_list_count = al_list_count = ll_data_count = 0
		bridge_call = {}
		# agent related counts and bridge call data
		total_agents_df = pd.DataFrame.from_dict(AGENTS,orient='index')
		c_agents_df = total_agents_df.index.isin(team_extensions)
		agents_df = total_agents_df[c_agents_df]
		brk_count = len(agents_df[agents_df['state'].str.lower() == 'onbreak'])
		dl_count = len(agents_df[(agents_df['dialer_login_status'] == True) & (agents_df['state'].str.lower() != 'onbreak')])
		la_count = len(agents_df[(agents_df['dialer_login_status'] == False) & (agents_df['state'].str.lower() != 'onbreak')])
		on_call_agent = agents_df[(agents_df['state']=='InCall') & (agents_df['dial_number'])]
		pg_count = len(on_call_agent[on_call_agent['call_type'].str.lower() =='progressive'])
		ic_count = len(on_call_agent[on_call_agent['call_type'].str.lower() =='inbound'])
		pd_count = len(on_call_agent[on_call_agent['call_type'].str.lower() =='predictive'])
		pv_count = len(on_call_agent[on_call_agent['call_type'].str.lower() =='preview'])
		mu_count = len(on_call_agent[on_call_agent['call_type'].str.lower() =='manual'])
		lo_count = agent_count - la_count - dl_count - brk_count
		live_agent_count = la_count + dl_count + brk_count
		ac_camp_count = len(active_camp)
		ll_count_dict = Phonebook.objects.filter(campaign__in=active_camp).aggregate(lead_list_count = Count('id'),
			al_list_count = Count('id',filter=Q(status='Active')))
		ll_data_count = Contact.objects.filter(phonebook__status="Active", campaign__in=list(camp_name)).count()
		down_count = DownloadReports.objects.filter(status=False,view=False).count()
		trunk_status = pickle.loads(settings.R_SERVER.get("trunk_status") or pickle.dumps(AGENTS))
		trunks_data = list(DialTrunk.objects.filter(status='Active').values('id','name','channel_count',free_channels=F('channel_count')))
		for trunk in trunks_data:
			trunk['consumed_channels'] = 0
			if str(trunk['id']) in trunk_status:
				trunk['consumed_channels'] = trunk_status[str(trunk['id'])]
				trunk['free_channels'] = trunk['free_channels'] - trunk_status[str(trunk['id'])]
		context = {"login_count":la_count, "total_agent_c":agent_count, 'dialer_count':dl_count,
				"logout_count":lo_count, 'bridge_call':json.dumps(bridge_call), "live_agent_count":live_agent_count,
				"inbound_count":ic_count, "preview_count":pv_count, "progressive_count":pg_count,
				"predictive_count":pd_count,"manual_count":mu_count, "a_camp_count": ac_camp_count,
				"ll_data_count":ll_data_count,"noti_count":noti_count,'web_socket_host':settings.WEB_SOCKET_HOST,
				"break_count":brk_count,"down_count":down_count,"server_ip":settings.WEB_SOCKET_HOST, 'trunks_data':trunks_data}
		context['can_switch'] = kwargs['permissions']['can_switch']
		context['can_boot'] = kwargs['permissions']['can_boot']
		context.update(ll_count_dict)
		if request.is_ajax():
			return JsonResponse(context)
		context['request'] = request
		return Response(context)

class EavesdropSessionApiView(LoginRequiredMixin, APIView):
	"""
	this view is for eavesdrop session for dashboard
	"""
	login_url = '/'

	def post(self, request):
		domain_ip = request.POST.get('domain_ip','')
		extension = request.POST.get('extension','')
		session_details = json.loads(request.POST.get('session_data',"{}"))
		if not session_details:
			if request.user.is_superuser or request.user.user_role.access_level != 'Agent':
				status = fs_administration_session(domain_ip,extension=extension)
				if "error" in status:
					print(status,"error")
				return Response(status)
		else:
			status = fs_administration_hangup(session_details['variable_sip_from_host'],uuid=session_details['Unique-ID'])
		return Response(status)

class PieChartLiveData(APIView):
	"""
			This Class contains the count shown in the Pie chart on Dashboard 
	"""
	def get(self,request):
		final_dict = {}
		if request.user.is_superuser or request.user.user_role.access_level == 'Admin':
			active_camps = Campaign.objects.filter(status="Active")
			camp = active_camps.values_list("name", flat=True)
			final_dict = Contact.objects.filter(phonebook__status="Active", campaign__in=list(camp)).aggregate(contact_count=Count('id'),
				dialed_count=Count('status',filter=Q(status="Dialed")),
				notdialed_count=Count('status',filter=Q(status="NotDialed")),
				queuecall_count=Count('status',filter=Q(status="Queued")),
				dropcall_count=Count('status',filter=Q(status="Drop")),
				InvalidNumber_count=Count('status',filter=Q(status="Invalid Number")),
				cbr_count =Count('status',filter=Q(status="CBR")),
				nc_count=Count('status',filter=Q(status="NC")))
			final_dict["abandoned_count"] = Abandonedcall.objects.all().count()
			final_dict["callback_count"] = CallBackContact.objects.filter(status="Queued").count()
			final_dict["dnc_count"] = DNC.objects.all().count()
		return Response(final_dict)

class OnCallAgentData(LoginRequiredMixin, APIView):
	"""
	This views used to show the oncalldata 
	"""
	login_url = '/'

	def get(self, request):
		bridge_call = {}
		AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or
				pickle.dumps(AGENTS))
		camp, active_camp, noti_count = get_active_campaign(request)
		team_extensions = user_hierarchy(request,camp)
		for agent, data in AGENTS.items():
			if agent in team_extensions and data['state']=='InCall' and data['dial_number']:
				if data['call_timestamp']=='' or data['call_timestamp'] == None:
					call_timestamp = int(str(round(time.time() * 1000))[:13])
					AGENTS[agent].update({'call_timestamp':call_timestamp})
					updated_agent_dict = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
					updated_agent_dict[agent].update(AGENTS[agent])
					settings.R_SERVER.set("agent_status", pickle.dumps(updated_agent_dict))
				if 'name' not in data:
					data['name'] = ''
				bridge_call[agent] = data
		return Response(bridge_call)

class LoginAgentLiveDataView(LoginRequiredMixin, APIView):
	"""
	This view is to get login agent live data on dashboard
	"""
	login_url = '/'

	def get(self, request):
		la_data = []
		AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or
				pickle.dumps(AGENTS))
		camp, active_camp, noti_count = get_active_campaign(request)
		team_extensions = user_hierarchy(request,camp)
		for agent, data in AGENTS.items():
			if agent in team_extensions:
				if "event_time" in data and data["event_time"]:
					tdelta = datetime.strptime(datetime.now().strftime('%H:%M:%S'), '%H:%M:%S') - datetime.strptime(data['event_time'], '%H:%M:%S')
					data["event_time"] = ':'.join(str(tdelta).split(':')[:3])
				if 'login_time' in data and data["login_time"]:
					tdelta = datetime.strptime(datetime.now().strftime('%H:%M:%S'), '%H:%M:%S') - datetime.strptime(data['login_time'], '%H:%M:%S')
					data["login_duration"] = ':'.join(str(tdelta).split(':')[:3])
				if 'name' not in data:
					data['name'] = ''
				if 'call_count' not in data:
					data['call_count'] = 0
				data['extension'] = agent
				data['role_name'] = ''
				la_data.append(data)
		return JsonResponse({"la_data":la_data})

#PredictiveDashBoardAPIView
from .utility import get_data_from_agent_redis,get_predictive_campaign,get_pd_dialing
class PredictiveDashBoardAPIView(LoginRequiredMixin,APIView):
	"""
	This view  to get data of live predictive campaign on dashboard for predictive
	call mode
	"""
	login_url = '/'
	def get(self, request):
		page = int(request.GET.get('page' ,1))
		paginate_by = int(request.GET.get('paginate_by', 10))
		pd_lv_camps=get_predictive_campaign()
		data={}
		lp_data=[]
		for pd_camp in pd_lv_camps:
			data['count_user_logged_in'],data['count_wait'],data['wrap_up'],data['talking'],data['count_hold'] = get_data_from_agent_redis(pd_camp)
			data['count_total_data']=Contact.objects.filter(campaign=pd_camp).count()
			data['count_dialed']=Contact.objects.filter(campaign=pd_camp,status__in=["Dialed", "NC", "Drop", "Invalid Number", "Queued-Callback", "Queued-Abandonedcall"]).count()
			data['count_connected']= CallDetail.objects.filter(dialed_status="Connected",campaign_name=pd_camp).count()
			data['count_nc']=Contact.objects.filter(campaign=pd_camp,status="NC").count()
			data['count_drop']=Contact.objects.filter(campaign=pd_camp,status="Drop").count() #abort
			data['campaign']=pd_camp
			data['dialing']=get_pd_dialing(pd_camp)
			lp_data.append(data)
		return JsonResponse({"lp_data":lp_data})


class ActiveAgentLiveDataAPIView(LoginRequiredMixin, APIView):
	"""
	This view is to get login agent live data on dashboard
	"""
	login_url = '/'

	def get(self, request):
		camp = []
		active_agents_data= []
		page = int(request.GET.get('page' ,1))
		paginate_by = int(request.GET.get('paginate_by', 10))
		if not request.user.is_superuser:
			camp, active_camp, noti_count = get_active_campaign(request)
		users = user_hierarchy_object(request.user, camp)
		queryset = users.filter(is_active=True).order_by(F('last_login').desc(nulls_last=True)).annotate(name=Concat('first_name', Value(' '),'last_name', output_field=CharField())).annotate(supervisor=Concat(F('reporting_to__username'),Value(' '), output_field=CharField())).values('id','username','name','supervisor')
		# queryset = get_paginated_object(queryset, page, paginate_by)
		# pagination_dict = data_for_vue_pagination(queryset)
		# df_user = pd.DataFrame(list(queryset.object_list))
		df_user = pd.DataFrame(list(queryset))
		contact_count = list(Contact.objects.filter(user__in=list(queryset.values_list('username',flat=True))).annotate(username=F('user')).values('username').annotate(assign_data_count=Count('id'),dialed_data_count=Count('id', filter=~Q(status__in=['NotDialed','Queued'])), notdialed_data_count=Count('id', filter=Q(status__in=['NotDialed','Queued']))))
		if not contact_count:
			contact_count = [{'username':'','assign_data_count':0,'dialed_data_count':0,'notdialed_data_count':0}]
		df_contact = pd.DataFrame(list(contact_count))
		data = pd.merge(df_user, df_contact, on='username', how='right').fillna(0).astype({"assign_data_count":'int', "dialed_data_count":'int',"notdialed_data_count":'int'})
		AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
		login_agents = pd.DataFrame.from_dict(AGENTS,orient='index')
		data = pd.merge(data, login_agents[['username','state','call_count','extension']], on='username', how='left').fillna({'state':'Logout','call_count':0, 'extension':''}).astype({'call_count':int})
		active_agents_data = list(data.T.to_dict().values())
		return JsonResponse({'active_agent_data':active_agents_data})


class CampaignLiveDataView(LoginRequiredMixin, APIView):
	"""
	this view is to get live data of on call agents
	"""
	login_url = "/"

	def get(self, request):
		page = int(request.GET.get('page' ,1))
		paginate_by = int(request.GET.get('paginate_by', 10))
		filter_by_camp = request.GET.get('campaign',None)
		r_campaigns = pickle.loads(settings.R_SERVER.get("campaign_status") or pickle.dumps({}))
		lc_data = []            #live campaign data
		if request.user.is_superuser or request.user.user_role.access_level == 'Admin':
			active_campaign = Campaign.objects.filter(status="Active").values("id","name")
		else:
			active_campaign = Campaign.objects.filter(Q(users=request.user)|Q(group__in=request.user.group.all().filter(status="Active")
				)).filter(status="Active").distinct().values("id","name")
		if filter_by_camp:
			active_campaign = active_campaign.filter(name__icontains=filter_by_camp)
		queryset = get_paginated_object(active_campaign, page, paginate_by)
		pagination_dict = data_for_vue_pagination(queryset)
		for campaign in queryset:
			campaign_dict = {}
			phonebooks = Phonebook.objects.filter(campaign=campaign['id'])
			phonebook_ids = phonebooks.filter(status='Active').values_list("id",flat=True)
			campaign_dict = Contact.objects.filter(campaign=campaign['name'], phonebook_id__in=phonebook_ids).aggregate(ll_total_data=Count('id'),
				ll_dialed_count=Count('status',filter=Q(status__in=["Dialed", "NC", "Drop", "Invalid Number", "Queued-Callback", "Queued-Abandonedcall"])),
				ll_notdialed_count=Count('status',filter=Q(status="NotDialed")),
				ll_queuecall_count=Count('status',filter=Q(status="Queued"))
				)
			campaign_dict["campaign"] = campaign['name']
			phonebook_data = phonebooks.aggregate(total_ll_count = Count('id'),
				active_ll_count=Count('id',filter=Q(status='Active')))
			campaign_dict.update(phonebook_data)
			
			# campaign_dict['totalcalls_today'] = CallDetail.objects.filter(campaign_name=campaign['name'] ,updated__date=datetime.now().date(),
			# 	dialed_status='Connected').count()
			
			campaign_dict['totalcalls_today'] = CallDetail.objects.filter(campaign_name=campaign['name'] ,updated__gte=datetime.now().date(),
				dialed_status='Connected').count()
			
			campaign_dict['queueLoginagents_count'] = 0
			if campaign['name'] in r_campaigns:
				campaign_dict['queueLoginagents_count'] = len(r_campaigns[campaign['name']])
			lc_data.append(campaign_dict)
		return JsonResponse({'liveCamp_data': lc_data, 'pagination_data': pagination_dict})

class AdminLiveCountApiView(LoginRequiredMixin, APIView):
	"""
	This view is used to get Live data count for admin of notifiction messages events
	"""
	login_url = '/'

	def get(self,request):
		return JsonResponse({'status':'live count go here'})


@method_decorator(check_read_permission, name='get')
class UsersListApiView(LoginRequiredMixin, ListAPIView):
	"""
	GET method of this view is used to list all users of application
	and the POST method is used to create new user in app
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "users/users.html"
	def get(self, request, **kwargs):
		page = int(request.GET.get('page' ,1))
		paginate_by = int(request.GET.get('paginate_by', 10))
		search_by = request.GET.get('search_by','')
		column_name = request.GET.get('column_name', '')
		camp_name, active_camp, noti_count = get_active_campaign(request)
		team_extensions = user_hierarchy(request,camp_name)
		queryset = User.objects.filter(Q(properties__extension__in=team_extensions)|Q(created_by=request.user)|Q(id=request.user.id))
		if search_by:
			try:
				if column_name=='status':
					search_value = False
					if search_by.lower()=='active':
						search_value = True
					queryset = queryset.filter(is_active=search_value)
				else:
					queryset = queryset.filter(**{column_name+"__istartswith": search_by})
			except:
				queryset = User.objects.none()
		id_list = list(queryset.values_list("id",flat=True))
		queryset = get_paginated_object(queryset, page, paginate_by)
		pagination_dict = data_for_vue_pagination(queryset)
		user_group = list(UserRole.objects.values("id", "name"))
		paginate_by_columns = (('username', 'username'),
			('properties__extension', 'extension'),
			('user_role__name', 'role'),
			('group__name','group'),
			('status', 'status'))
		context = {'user_group': user_group,'paginate_by':paginate_by,
			'paginate_by_list':PAGINATE_BY_LIST, 'paginate_by_columns':paginate_by_columns,
			'search_by':search_by, 'column_name':column_name, 'id_list':id_list,"server_ip":settings.WEB_SOCKET_HOST}
		if request.is_ajax():
			result = UserPaginationSerializer(queryset, many=True).data
			pagination_dict["table_data"] = result
			context = {**context, **kwargs['permissions'], **pagination_dict}
			return JsonResponse(context)
		else:
			context = {**context, **kwargs['permissions'], **pagination_dict}
			context['request'] = request
			context['server_ip'] = settings.WEB_SOCKET_HOST
			return Response(context)
	
@method_decorator(user_validation, name='post')
class UsersCreateApiView(LoginRequiredMixin, APIView):
	"""
	This view is used to create users
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "users/user_create.html"
	serializer_class = UserSerializer

	def get(self, request):
		all_users = User.objects.values("id", "username").exclude(
			id=request.user.id)
		users = User.objects.filter(Q(user_role__isnull=False)| Q(is_superuser=True)).exclude(
			user_role__access_level="Agent").prefetch_related(
			'user_role', 'group')
		user_role = UserRole.objects.values("id", "name", "access_level")
		group_obj = Group.objects.all()
		if check_non_admin_user(request.user):
			group_obj = group_obj.filter(Q(user_group=request.user)|Q(created_by=request.user)).distinct()
		groups = group_obj.values("id", "name", 'color_code')
		extension_exist = UserVariable.objects.all().values_list('extension',flat=True)
		latest_extension = sorted(list(set(four_digit_number) - set(extension_exist)))[0]
		user_timezone = USER_TIMEZONE
		enable_wfh = pickle.loads(settings.R_SERVER.get('enable_wfh') or pickle.dumps(False))
		switch_list = Switch.objects.filter().values("id","name")
		default_switch = Switch.objects.filter().first()
		user_variables_default_values = {'device_pass':'1234','level':1,'position':1,
		'default_switch':default_switch,'default_agent_type':UserVariable.AGENT_TYPE[0][0], 'contact':'[call_timeout=10]user',
		'dial_status':UserVariable.AGENT_STATUS_CHOICES[0][0], 'max_no_answer':3 , 'wrap_up_time':10, 'reject_delay_time':10,
		'busy_delay_time':60, 'protocol':PROTOCOL_CHOICES[0][0], 'default_call_type':CALL_TYPE[0][0]}
		context = {**user_variables_default_values,'available_users': users,'request': request,
			'user_role': user_role,'groups': groups,'user_timezone': user_timezone,
			'user_status': UserStatus, 'can_create':True, 'all_users': all_users,'extension':latest_extension, 'enable_wfh': enable_wfh,
			'switch_list':switch_list, 'agent_type':UserVariable.AGENT_TYPE, 'agent_status_choice':UserVariable.AGENT_STATUS_CHOICES,
			'call_type':CALL_TYPE,
			}
		return Response(context)

	def post(self, request):
		existing_user = request.POST.get("existing_user", "")
		user_serializer = self.serializer_class(data=request.POST)
		user_variable_serializer = UserVariableCreateSerializer(data=request.POST) 
		if user_serializer.is_valid():
			if user_variable_serializer.is_valid():
				user = user_serializer.save(created_by=request.user)
				user.set_password(request.POST["password"])
				user.save()
				user_variable = user_variable_serializer.save()
				user_variable.user = user
				if request.POST.get("wfh_numeric",'') == '':
					user_variable.wfh_numeric = None
				else:
					user_variable.wfh_numeric = request.POST["wfh_numeric"]
				if request.POST.get('wfh_password',None):
					user_variable.wfh_password = request.POST['wfh_password']
				if 'w_req_callback' in request.POST:
					user_variable.w_req_callback = request.POST['w_req_callback']
				user_variable.save()
				create_admin_log_entry(request.user, "user","1",'CREATED',user.username)
				return Response({"msg":"User created successfully"})
			return JsonResponse({"errors":user_variable_serializer.errors}, status=500)
		return JsonResponse({"errors": user_serializer.errors, "errors":user_variable_serializer.errors}, status=500)

@method_decorator(check_update_permission, name='get')
@method_decorator(user_validation, name='put')
class UsersEditApiView(LoginRequiredMixin, APIView):
	"""
	This api is used to edit user basic detail and some additional
	settings related to telephony
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "users/user_edit.html"
	serializer = UpdateUserSerializer

	def get(self, request, pk, format=None,**kwargs):
		user_detail = get_object(pk, "callcenter", "User")
		users = User.objects.filter(user_role__isnull=False).exclude(
			user_role__access_level="Agent").exclude(id=user_detail.id).prefetch_related(
			'user_role', 'group')
		dept = user_detail.group.all().values_list("id", flat=True)
		groups = Group.objects.all().exclude(id__in=dept).values("name", "id")
		user_role =  UserRole.objects.values("id", "name", "access_level")
		enable_wfh = pickle.loads(settings.R_SERVER.get('enable_wfh') or pickle.dumps(False))
		agent_type = ""
		if user_detail.is_superuser or user_detail.properties:
			agent_type = user_detail.properties.AGENT_TYPE
		switch_list = Switch.objects.filter().values("id","name")
		campaign = Campaign.objects.filter(Q(users=user_detail)|Q(group__in=user_detail.group.all())).filter(status='Active').distinct()
		trunk_group = campaign.filter(is_trunk_group=True).values_list('trunk_group__trunks__trunk',flat=True)
		camp_trunk = campaign.filter(is_trunk_group=False).values_list('trunk',flat=True)
		trunk_list = DialTrunk.objects.filter(Q(id__in=camp_trunk)|Q(id__in=trunk_group)).values('id','name','did_range')
		# used_did_list = User.objects.exclude(id=pk).exclude(caller_id=None).exclude(caller_id='').values_list('caller_id',flat=True)
		used_did_list =get_used_did_by_pk(pk,'user')
		context = {'request': request, 'user_status': UserStatus, 'groups': groups,
			'user_role': user_role, 'user_detail': user_detail, 'agent_type': agent_type,
			'agent_status_choice': user_detail.properties.AGENT_STATUS_CHOICES,
			'call_type':CALL_TYPE, 'user_timezone': USER_TIMEZONE, 'available_users':users,
			'enable_wfh': enable_wfh,"switch_list":switch_list, 'trunk_list':trunk_list, 'used_did_list':list(used_did_list)}
		context = {**context, **kwargs['permissions']}
		return Response(context)

	def put(self, request, pk, format=None):
		'''
		This method will validate and update user detail
		'''
		user = get_object(pk, "callcenter", "User")
		serializer = self.serializer(user, data=request.data)
		user_variable_serializer = UserVariableSerializer(
			user.properties, data=request.data)
		if serializer.is_valid():
			serializer.save()
			if user_variable_serializer.is_valid():
				user_variable_serializer.save() 
				create_admin_log_entry(request.user, "user","2",'UPDATED',user.username)
			else:
				print({"errors": user_variable_serializer.errors})
		else:
			return JsonResponse({"errors": serializer.errors}, status=500)
		return JsonResponse({"success": "User updated successfully"})

class CheckUserApiView(APIView):
	'''
	This view is used to validate user fields alredy exist or not
	'''
	def post(self, request):
		username = request.POST.get("username", "")
		email = request.POST.get("email", "")
		extension = request.POST.get("extension", "")
		data = validate_data(username, email, extension)
		return Response(data)

class ValidateUserUploadApiView(APIView):
	# This view is used to validate bulk user upload
	def post(self, request):
		user_file = request.FILES.get("uploaded_file", "")
		data = {}
		if user_file.size <= 1:
			data["empty_file"] = 'File must not be empty'
		else:
			if user_file.name.endswith('.csv'):
				data = pd.read_csv(user_file, na_filter=False, dtype={"extension" : "str"})
			else:
				data = pd.read_excel(user_file, dtype={"extension" : "str"})
			user_columns = ['username', 'password','group', 'role']
			column_names = data.columns.tolist()
			valid = all(elem in column_names for elem in user_columns)
			if valid:
				data = validate_uploaded_users_file(data)
			else:
				data = {}
				data["column_err_msg"] = 'File must contains these ' + \
					','.join(user_columns)+' columns'
				data["column_id"] = "#upload-file-error"
		return Response(data)

class UserUploadApiView(APIView):
	def post(self, request):
		proper_file = request.POST.get("proper_file", "")
		improper_file = request.POST.get("improper_file", "")
		cwd = settings.BASE_DIR
		if request.POST.get("perform_upload", ""):
			if proper_file.endswith('.csv'):
				data = pd.read_csv(cwd+proper_file, na_filter=False)
			else:
				data = pd.read_excel(cwd+proper_file)
			upload_users(data, request.user)
			create_admin_log_entry(request.user, "user","6",'UPLOADED')
		if proper_file:
			os.remove(cwd+proper_file)
		if improper_file:
			os.remove(cwd+improper_file)
		return Response({"msg": "file removed successfully"})

@method_decorator(check_read_permission, name='get')
@method_decorator(group_validation, name='post')
class GroupListApiView(LoginRequiredMixin, APIView):
	"""
	This view is used to display list of groups and also for
	creating new groups
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "users/groups.html"
	serializer_class = GroupSerializer

	def get(self, request, **kwargs):
		page = int(request.GET.get('page' ,1))
		paginate_by = int(request.GET.get('paginate_by', 10))
		search_by = request.GET.get('search_by','')
		column_name = request.GET.get('column_name', '')
		queryset = Group.objects.all()
		if check_non_admin_user(request.user):
			queryset = queryset.filter(Q(user_group=request.user)|Q(created_by=request.user)).distinct()
		if search_by and column_name:
			queryset = queryset.filter(**{column_name+"__istartswith": search_by.lower()})
		queryset_list = list(queryset.values_list("id", flat=True))
		queryset = get_paginated_object(queryset, page, paginate_by)
		paginate_by_columns = (('name', 'Group Name'),
			('status', 'status'))
		user_querysets = User.objects.all().exclude(is_superuser=True).values_list("id","username")
		camp_name, active_camp, noti_count = get_active_campaign(request)
		context = {
			'group_status':Status, 'id_list': queryset_list,'paginate_by':paginate_by,
			'paginate_by_list':PAGINATE_BY_LIST, 'paginate_by_columns':paginate_by_columns,
			'search_by':search_by, 'column_name':column_name, 'noti_count':noti_count}
		context = {**context, **kwargs['permissions']}
		pagination_dict = data_for_vue_pagination(queryset)
		if request.is_ajax():
			result = list(GroupPaginationSerializer(queryset, many=True).data)
			pagination_dict["table_data"] = result
			context = {**context, **kwargs['permissions'], **pagination_dict}
			return JsonResponse(context)
		else:
			context = {**context, **kwargs['permissions'], **pagination_dict}
			context['request']: request
			context['user_queryset'] = user_querysets
			return Response(context)

	def post(self, request):
		group = self.serializer_class(data=request.POST)
		if group.is_valid():
			group_obj = group.save(created_by=request.user)
			if request.data['add_users_save']:
				user_save_list = request.data['add_users_save'].split(",")
				user_save_queryset = User.objects.filter(id__in=user_save_list)
				for user in user_save_queryset:
					user.group.add(group_obj)
			create_admin_log_entry(request.user, "group","1",'CREATED',group_obj.name)
		return JsonResponse({"msg": "Group Saved Successfully"})

@method_decorator(group_validation, name='put')
class GroupModifyApiView(APIView):
	"""
	This class is for group edit and saving 
	"""
	serializer_class = GroupSerializer
	def post(self, request, pk, format=None):
		group = get_object(pk, "callcenter", "Group")
		serializer = self.serializer_class(group)
		serializer.data['id'] = pk
		return JsonResponse({'querysets': serializer.data, 'queryset':group.users, 
			'allusers':group.allusers})

	def put(self, request, pk, format=None):
		user_remove_list = user_add_list = []
		group = get_object(pk, "callcenter", "Group")
		serializer = self.serializer_class(group, data=request.data)
		if serializer.is_valid():
			serializer.save()
			if request.data['user_add_list']:
				user_add_list = request.data['user_add_list'].split(",")
			if request.data['user_remove_list']:
				user_remove_list = request.data['user_remove_list'].split(",")
			user_add_queryset = User.objects.filter(id__in=user_add_list)
			if user_add_queryset:
				for user in user_add_queryset:
					user.group.add(group)
			user_remove_queryset = User.objects.filter(id__in=user_remove_list)
			if user_remove_queryset:
				for user_remove in user_remove_queryset:
					user_remove.group.remove(group)
			create_admin_log_entry(request.user, "group","2",'UPDATED',group.name)
			group_add_user_rpc(user_add_queryset=user_add_queryset,user_remove_queryset=user_remove_queryset,group_id=pk)       
			return Response()
		return JsonResponse(serializer.errors, status=500)


@method_decorator(check_read_permission, name='get')
@method_decorator(switch_validation, name='put')
class SwitchListApiView(LoginRequiredMixin, APIView):
	"""
	This view is used to show list of servers to user
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "campaign/switch.html"
	serializer_class = SwitchSerializer

	def get(self, request, **kwargs):
		page_info = data_for_pagination(request)
		if page_info["search_by"] and page_info["column_name"]:
			queryset = Switch.objects.filter(**{page_info["column_name"]+"__istartswith": page_info["search_by"]})
		else:
			queryset = Switch.objects.all()
		switch_list = list(queryset.values_list("id", flat=True))
		queryset = get_paginated_object(queryset, page_info["page"], page_info["paginate_by"])
		pagination_dict = data_for_vue_pagination(queryset)
		paginate_by_columns = (('name', 'Switch Name'),
		('ip_address', 'IP Address'),
		('status', 'status'),
		)
		PORT_DETAILS = {'sip_udp_port':40506,'rpc_port':8080,'wss_port':7443,'event_socket_port':8021}
		camp_name, active_camp, noti_count = get_active_campaign(request)
		context = {'id_list': switch_list, 'default_port':PORT_DETAILS,
		 "paginate_by_columns": paginate_by_columns, "noti_count":noti_count}
		context = {**context, **kwargs['permissions'], **page_info}
		if request.is_ajax():
			result = list(SwitchPaginationSerializer(queryset, many=True).data)
			pagination_dict["table_data"] = result
			context = {**context, **kwargs['permissions'], **pagination_dict}
			return JsonResponse(context)
		else:
			context = {**context, **kwargs['permissions'], **pagination_dict}
			context['request']: request
			return Response(context)

	def post(self, request, pk=None, format=None):
		object_data = get_object(pk, "callcenter", "Switch")
		serializer = self.serializer_class(object_data)
		serializer.data['id'] = pk
		return JsonResponse({'querysets': serializer.data})

	def put(self, request, pk=None, format=None):
		if pk:
			object_data = get_object(pk, "callcenter", "Switch")
			serializer = self.serializer_class(object_data, data=request.data)
		else:
			serializer = self.serializer_class(data=request.POST)

		if serializer.is_valid():
			serializer.save()
			#create admin log entry
			if pk:
				create_admin_log_entry(request.user, 'Switch','2','UPDATED', request.POST["name"])
			else:
				create_admin_log_entry(request.user, 'Switch', '1','CREATED', request.POST["name"]) 
			return Response()
		return JsonResponse(serializer.errors, status=500)

@method_decorator(check_read_permission, name='get')
@method_decorator(dispo_validation, name='post')
class DisposListApiView(LoginRequiredMixin, APIView):
	"""
	this view class is for dispositions create and 
	check the existing dispositions.
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "campaign/disposition.html"
	serializer_class = DispositionSerializer

	def get(self, request, **kwargs):
		page_info = data_for_pagination(request)
		
		if page_info["search_by"] and page_info["column_name"]:
			queryset = Disposition.objects.exclude(status="Delete").filter(**{page_info["column_name"]+"__istartswith": page_info["search_by"]})
		else:
			queryset = Disposition.objects.exclude(status="Delete").all()
		dispo_list = list(queryset.values_list("id", flat=True))

		queryset = get_paginated_object(queryset, page_info["page"], page_info["paginate_by"])
		pagination_dict = data_for_vue_pagination(queryset)
		paginate_by_columns = (('name', 'Disposition Name'),
			('status', 'Status'),
			)
		exclude_dispo_list = ['Dnc', 'Not Connected', 'Connected', 'Callback', 'Busy', 'Transfer']
		camp_name, active_camp, noti_count = get_active_campaign(request)
		context = {
		'id_list': dispo_list, 'default_disp':exclude_dispo_list,
		"paginate_by_columns":paginate_by_columns, "noti_count":noti_count}
		context = {**context, **kwargs['permissions'], **page_info}
		if request.is_ajax():
			result = list(DispositionPaginationSerializer(queryset, many=True).data)
			pagination_dict["table_data"] = result
			context = {**context, **kwargs['permissions'], **pagination_dict}
			return JsonResponse(context)
		else:
			context = {**context, **kwargs['permissions'], **pagination_dict}
			context['request']: request
			return Response(context)

	def post(self, request):
		dispos = Disposition.objects.filter(status="Delete",name=request.POST.get('name'))
		if dispos.exists():
			dispos.delete()
		disposition = self.serializer_class(data=request.POST)
		if disposition.is_valid():
			disposition.save(created_by=request.user)
		return JsonResponse({"msg": "Disposition Saved Successfully"})

@method_decorator(dispo_validation, name='post')
@method_decorator(check_create_permission, name='get')
class DispositionsCreateApiView(LoginRequiredMixin, generics.CreateAPIView):
	"""
	This view is used to create N number of Dispotions. 
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = 'campaign/dispo_create.html'
	# template_name = 'campaign/disposition_create.html'
	serializer_class = DispositionSerializer

	def get(self, request, **kwargs):
		ext_disposition = Disposition.objects.all().values("id","name")
		context = {'request': request, 'field_types': FIELD_TYPE, 'subdispo':[],
			'dispo_status':Status, 'dispo_field_type':DISPO_FIELD_TYPE,
			"ext_disposition":ext_disposition, "is_edit":True}
		context = {**context, **kwargs['permissions']}
		return Response(context)

	def post(self, request):
		dispo_serializer = DispositionSerializer(data=request.POST)
		if dispo_serializer.is_valid():
			dispo_serializer.save(created_by=request.user)
			create_admin_log_entry(request.user, 'Disposition', '1','CREATED', request.POST["name"])

		return JsonResponse({"success": "Dispositions created successfully"})

@method_decorator(dispo_validation, name='post')
@method_decorator(check_update_permission, name='get')
class DispositionsEditApiView(LoginRequiredMixin, generics.CreateAPIView):
	"""
	This view is used to create N number of Dispotions. 
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = 'campaign/dispo_create.html'
	serializer_class = DispositionSerializer

	def get(self, request, pk, format=None, **kwargs):
		ext_disposition = Disposition.objects.all().values("id","name")
		disposition = get_object(pk, "callcenter", "Disposition")
		subdispo = disposition.dispos
		agent_logged_in_campaign = get_login_campaign()
		dispo_entries = list(Campaign.objects.filter(name__in=agent_logged_in_campaign).values_list("disposition__id",flat=True))
		is_edit = True
		if disposition.id in dispo_entries:
			is_edit=False
		context = {'request': request, 'field_types': FIELD_TYPE, 'disposition':disposition,
			'dispo_status':Status, 'subdispo':subdispo, 'dispo_field_type':DISPO_FIELD_TYPE,
			"ext_disposition":ext_disposition, "is_edit":is_edit}
		context = {**context, **kwargs['permissions']}
		return Response(context)

	def post(self, request, pk):
		disposition = get_object(pk, "callcenter", "Disposition")
		dispo_serializer = DispositionSerializer(disposition, data=request.POST)
		if dispo_serializer.is_valid():
			dispo_serializer.save()
			create_admin_log_entry(request.user, 'Disposition', '2','UPDATED', request.POST["name"])
		return JsonResponse({"success": "Dispositions updated successfully"})

class GetExistingDisposition(LoginRequiredMixin, APIView):
	"""
	This views is to get the exisitng dispostions based on  id 
	"""
	def post(self, request, pk):
		disposition = get_object(pk, "callcenter", "Disposition")
		subdispo = disposition.dispos
		return JsonResponse({'subdispo':subdispo, 'dispo_type':disposition.dispo_type})

@method_decorator(check_read_permission, name='get')
class RelationTagListApiView(LoginRequiredMixin,APIView):
	"""
	this view class is for view existing relation Tagging
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "campaign/relation_tags.html"

	def get(self, request, **kwargs):
		page_info = data_for_pagination(request)
		if page_info["search_by"] and page_info["column_name"]:
			queryset = RelationTag.objects.filter(**{page_info["column_name"]+"__istartswith": page_info["search_by"]})
		else:
			queryset = RelationTag.objects.all()
		relationtag_list = list(queryset.values_list("id", flat=True))

		queryset = get_paginated_object(queryset, page_info["page"], page_info["paginate_by"])
		pagination_dict = data_for_vue_pagination(queryset)
		paginate_by_columns = (('name', 'Disposition Name'),
			('status', 'Status'),
			)
		camp_name, active_camp, noti_count = get_active_campaign(request)
		context = {
		'id_list': relationtag_list,
		"paginate_by_columns":paginate_by_columns, 'noti_count':noti_count}
		context = {**context, **kwargs['permissions'], **page_info}
		
		if request.is_ajax():
			result = list(RelationTagPaginationSerializer(queryset, many=True).data)
			pagination_dict["table_data"] = result
			context = {**context, **kwargs['permissions'], **pagination_dict}
			return JsonResponse(context)
		else:
			context = {**context, **kwargs['permissions'], **pagination_dict}
			context['request']: request
			return Response(context)

@method_decorator(relationtag_validation, name='post')
@method_decorator(check_create_permission, name='get')
class RelationTagCreateApiView(LoginRequiredMixin, generics.CreateAPIView):
	"""
	This view is used to create N number of Relation Tag
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = 'campaign/relationtag_create_edit.html'

	def get(self, request, **kwargs):
		context = {'request': request, 'field_types': FIELD_TYPE, 'relation_field':[],
			'relationtag_status':Status, 'dispo_field_type':DISPO_FIELD_TYPE}
		context = {**context, **kwargs['permissions']}
		return Response(context)

	def post(self, request):
		relationtag_serializer = RelationTagSerializer(data=request.POST)
		if relationtag_serializer.is_valid():
			relationtag_serializer.save(created_by=request.user)
			create_admin_log_entry(request.user, 'RelationTag', '1','CREATED', request.POST["name"])
		else:
			print(relationtag_serializer.errors)
		return JsonResponse({"success": "RelationTag created successfully"})

@method_decorator(relationtag_validation, name='post')
@method_decorator(check_update_permission, name='get')
class RelationTagEditApiView(LoginRequiredMixin, generics.CreateAPIView):
	"""
	This view is used to create N number of Dispotions. 
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = 'campaign/relationtag_create_edit.html'

	def get(self, request, pk, format=None, **kwargs):
		relationtag = get_object(pk, "callcenter", "RelationTag")
		relation_field = relationtag.relation_fields
		context = {'request': request, 'field_types': FIELD_TYPE, 'relationtag':relationtag,
			'relationtag_status':Status, 'relation_field':relation_field, 'dispo_field_type':DISPO_FIELD_TYPE}
		context = {**context, **kwargs['permissions']}
		return Response(context)

	def post(self, request, pk):
		relationtag = get_object(pk, "callcenter", "RelationTag")
		relationtag_serializer = RelationTagSerializer(relationtag, data=request.POST)
		if relationtag_serializer.is_valid():
			relationtag_serializer.save(created_by=request.user)
			create_admin_log_entry(request.user, 'RelationTag', '2','UPDATED', request.POST["name"])
		return JsonResponse({"success": "RelationTag updated successfully"})

@method_decorator(check_read_permission, name='get')
@method_decorator(pausebreak_validation, name='post')
class PausebreaksListApiView(LoginRequiredMixin, APIView):
	"""
	This view is used to show list and create pausebreaks
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "campaign/pausebreaks.html"
	serializer_class = PauseBreakSerializer

	def get(self, request, **kwargs):
		page_info = data_for_pagination(request)
		if page_info["search_by"] and page_info["column_name"]:
			queryset = PauseBreak.objects.filter(**{page_info["column_name"]+"__istartswith": page_info["search_by"]})
		else:
			queryset = PauseBreak.objects.all()
		pause_break_list = list(queryset.values_list("id", flat=True))
		queryset = get_paginated_object(queryset, page_info["page"], page_info["paginate_by"])
		pagination_dict = data_for_vue_pagination(queryset)
		paginate_by_columns = (('name', 'Break Name'),
			('status', 'status'),
			)
		default_ex_lists = ['Breakfast Break', 'Tea Break','Lunch Break', 'Meeting', 'Dinner Break']
		camp_name, active_camp, noti_count = get_active_campaign(request)
		context = { 
		'id_list':pause_break_list,
		'default_list':default_ex_lists,
		"paginate_by_columns":paginate_by_columns, "noti_count":noti_count,'break_status': Status,}
		context = {**context, **kwargs['permissions'], **page_info}

		if request.is_ajax():
			result = list(PauseBreakPaginationSerializer(queryset, many=True).data)
			pagination_dict["table_data"] = result
			context = {**context, **kwargs['permissions'], **pagination_dict}
			return JsonResponse(context)
		else:
			context = {**context, **kwargs['permissions'], **pagination_dict}
			context['request']: request
			return Response(context)

	def post(self, request, format=None):
		serializer = self.serializer_class(data=request.data)
		if serializer.is_valid():
			serializer.save()
			### Admin Log ####
			create_admin_log_entry(request.user, 'PauseBreak', str(1),'CREATED', request.POST["name"])
			return JsonResponse({"msg":"break saved"})
		return JsonResponse(serializer.errors, status=500)

@method_decorator(pausebreak_validation, name='put')
class PausebreaksModifyApiView(APIView):
	"""
	This view is used to edit and get saved pause breaks
	"""
	serializer_class = PauseBreakSerializer

	def post(self, request, pk, format=None):
		object_data = get_object(pk, "callcenter", "PauseBreak")
		serializer = self.serializer_class(object_data)
		serializer.data['id'] = pk
		return Response({'querysets': serializer.data})

	def put(self, request, pk, format=None):
		object_data = get_object(pk, "callcenter", "PauseBreak")
		serializer = self.serializer_class(object_data, data=request.data)
		if serializer.is_valid():
			serializer.save()
			create_admin_log_entry(request.user, 'PauseBreak', '2','UPDATED', request.POST["name"])
			return Response()
		return Response(serializer.errors, status=500)

@method_decorator(check_read_permission, name='get')
@method_decorator(trunk_validation, name='post')
class DialTrunkListApiView(LoginRequiredMixin, APIView):
	"""
	This view is used to show list of Dial Trunk
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "campaign/dialtrunk.html"
	serializer_class = DialTrunkSerializer

	def get(self, request, **kwargs):
		page_info = data_for_pagination(request)
		
		if page_info["search_by"] and page_info["column_name"]:
			if page_info["column_name"] == "switch":
				queryset = DialTrunk.objects.filter(switch__name__istartswith=page_info["search_by"])
			else:
				queryset = DialTrunk.objects.filter(**{page_info["column_name"]+"__istartswith": page_info["search_by"]})
		else:
			queryset = DialTrunk.objects.all().select_related("switch")
		trunk_list = list(queryset.values_list("id", flat=True))
		queryset = get_paginated_object(queryset, page_info["page"], page_info["paginate_by"])
		pagination_dict = data_for_vue_pagination(queryset)
		paginate_by_columns = (('name', 'Name'),
			('trunk_type', 'Type'),
			('switch', 'switch'),
			('status', 'status'),
			)

		switches = list(Switch.objects.filter().values("id", "name"))
		dial_trunk_id_list = list(DialTrunk.objects.filter().values_list("id", flat=True))
		camp_name, active_camp, noti_count = get_active_campaign(request)
		context = {'id_list': dial_trunk_id_list,
		'trunk_type': TRUNK_TYPE, 'trunk_status': Status,
		'trunk_list':trunk_list, 'paginate_by_columns':paginate_by_columns,
		'noti_count':noti_count, "switches":switches, 'country_codes':COUNTRY_CODES }
		context = {**context, **kwargs['permissions'], **page_info}

		if request.is_ajax():
			result = list(DialTrunkPaginationSerializer(queryset, many=True).data)
			pagination_dict["table_data"] = result
			context = {**context, **kwargs['permissions'], **pagination_dict}
			return JsonResponse(context)
		else:
			context = {**context, **kwargs['permissions'], **pagination_dict}
			context['request']: request
			return Response(context)
	def post(self, request, format=None):
		serializer = self.serializer_class(data=request.data)
		if serializer.is_valid():
			serializer.save()
			create_admin_log_entry(request.user, 'DialTrunk','1','CREATED', request.POST["name"])
			return Response()
		return Response(serializer.errors, status=500)

@method_decorator(user_role_validation, name='put')
class DialTrunkModifyApiView(APIView):
	""" 
	This view s used to save the modified dialtrunk
	"""
	serializer_class = DialTrunkSerializer

	def post(self, request, pk, format=None):
		object_data = get_object(pk, "callcenter", "DialTrunk")
		serializer = self.serializer_class(object_data)
		serializer.data['id'] = pk
		return Response({'querysets': serializer.data})

	def put(self, request, pk, format=None):
		object_data = get_object(pk, "callcenter", "DialTrunk")
		serializer = self.serializer_class(object_data, data=request.data)
		if serializer.is_valid():
			updated_obj = serializer.save()
			if DiaTrunkGroup.objects.filter(trunks__trunk_id=pk).exists():
				dial_trunk_group = DiaTrunkGroup.objects.filter(trunks__trunk_id=pk).first()
				trunk_ids = list(dial_trunk_group.trunks.all().values_list('trunk_id', flat=True))
				dial_trunks = DialTrunk.objects.filter(id__in = trunk_ids).aggregate(Sum('channel_count'))
				dial_trunk_group.total_channel_count = dial_trunks['channel_count__sum']
				dial_trunk_group.save()
			if User.objects.filter(trunk_id=pk).exists():
				did_range = updated_obj.did_range
				users = User.objects.filter(trunk_id=pk)
				for user in users:
					if user.caller_id:
						if not int(did_range.split(',')[0]) <= int(user.caller_id) <= int(did_range.split(',')[1]):
							user.caller_id = ''
							user.save()
			create_admin_log_entry(request.user, 'DialTrunk','2','UPDATED', request.POST["name"])
			return Response()
		return Response(serializer.errors, status=500)


@method_decorator(check_read_permission, name='get')
class DialTrunkGroupListApiView(LoginRequiredMixin, APIView):
	"""
	This view is used to show list of Dial Trunk
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "campaign/dial_trunk_group.html"

	def get(self, request, **kwargs):
		page_info = data_for_pagination(request)
		
		if page_info["search_by"] and page_info["column_name"]:
			dial_trunk_group = DiaTrunkGroup.objects.filter(**{page_info["column_name"]+"__istartswith": page_info["search_by"]})
		else:
			dial_trunk_group = DiaTrunkGroup.objects.all()
		trunk_group_list = list(dial_trunk_group.values_list("id", flat=True))
		dial_trunk_group = get_paginated_object(dial_trunk_group, page_info["page"], page_info["paginate_by"])
		pagination_dict = data_for_vue_pagination(dial_trunk_group)
		paginate_by_columns = (('name', 'Trunk Group Name'),('status','status'),
			)
		camp_name, active_camp, noti_count = get_active_campaign(request)
		context = {"id_list": trunk_group_list,
		"paginate_by_columns":paginate_by_columns,"noti_count":noti_count
		}
		context = {**context, **kwargs['permissions'], **page_info}
		if request.is_ajax():
			result = list(DialTrunkGroupPaginationSerializer(dial_trunk_group, many=True).data)
			pagination_dict["table_data"] = result
			context = {**context, **kwargs['permissions'], **pagination_dict}
			return JsonResponse(context)
		else:
			context = {**context, **kwargs['permissions'], **pagination_dict}
			context['request']: request
			return Response(context)

class TrunkGroupCreateEditApiView(LoginRequiredMixin,APIView):
	""" 
	This views is for creating and edit the trunkgroup
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "campaign/trunk_group_create.html"
	serializer_class = DialTrunkGroupSerializer

	def get(self, request, pk=None, format=None):
		all_trunk = DialTrunk.objects.filter(status="Active")
		trunk_list = list(all_trunk.annotate(text=F('name')).values("text","id","did_range"))
		trunk_channel_count = list(all_trunk.values("id","channel_count"))
		context = {'trunk_list': trunk_list, "trunk_status":Status, "trunk_channel_count":trunk_channel_count}
		if pk:
			object_data = get_object(pk, "callcenter", "DiaTrunkGroup")
			context["trunk_group"] = object_data
			context["can_edit"] = True
			context["trunks"] = list(object_data.trunks.all().values("did","trunk","priority"))
			agent_logged_in_campaign = get_login_campaign()
			trunk_entries = list(Campaign.objects.filter(name__in=agent_logged_in_campaign).values_list("trunk_group__id",flat=True))
			context["is_edit"]=True
			if object_data.id in trunk_entries:
				context["is_edit"]=False
		else:
			context["can_create"] =True
		return Response(context)

	def post(self, request, pk=None, format=None):
		trunk_details = request.POST.get("trunk_details")
		if pk:
			object_data = get_object(pk, "callcenter", "DiaTrunkGroup")
			serializer = self.serializer_class(object_data, data=request.POST)
		else:
			serializer = self.serializer_class(data=request.POST)
		if serializer.is_valid():
			trunk_group = serializer.save()
			trunk_group.created_by = request.user
			if trunk_details:
				trunk_details = json.loads(trunk_details)
				trunk_group.trunks.clear()
				did = {}
				for trunk in trunk_details:
					did["type_of_did"] = trunk['did_type']
					if str(trunk['did_type']) == 'single':
						did["did"] = [trunk['did']]
					elif str(trunk['did_type']) == 'multiple':
						did['did'] = trunk['did']
					elif str(trunk['did_type']) == 'range':
						did["start"] = trunk['did_start']
						did["end"] = trunk['did_end']
					trunk_priority = DialTrunkPriority.objects.create(priority=trunk["trunk_priority"], trunk_id=trunk["trunk_id"],
						did=did) 
					trunk_group.trunks.add(trunk_priority)
					trunk_group.save()
			campaigns = Campaign.objects.filter(trunk_group=trunk_group)
			for campaign in campaigns:
				trunks = trunk_group.trunks.all()
				did_list = []
				for trunk in trunks:
					did_list.extend(get_group_did(trunk))
				campaign.all_caller_id = did_list
				campaign.save()
			return Response({'msg': 'group created'})
		return Response({'errors': 'name already exists'},status=500)

class TrunkGroupCheckApiView(APIView):
	"""
	This view to check trunk group exists or not bsed on id
	"""
	def post(self, request, format=None):
		trunk_group_id = request.POST.get("trunk_group_id","")
		exists = False
		if request.POST.get("trunk_id"):
			if DiaTrunkGroup.objects.filter(trunks__trunk_id=request.POST.get("trunk_id")).exists():
				if trunk_group_id:
					if DiaTrunkGroup.objects.filter(trunks__trunk_id=request.POST.get("trunk_id")).exclude(id=trunk_group_id).exists():
						exists = True
				else:
					exists = True
		return Response({'exists': exists})

@method_decorator(check_read_permission, name='get')
class CampaignScheduleListApiView(LoginRequiredMixin, APIView):
	"""
	This view is used to display list of call times
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "campaign/camapign_schedule.html"

	def get(self, request, **kwargs):
		page_info = data_for_pagination(request)
		if page_info["search_by"] and page_info["column_name"]:
			queryset = CampaignSchedule.objects.filter(**{page_info["column_name"]+"__iexact": page_info["search_by"]})
		else:
			queryset = CampaignSchedule.objects.all()
		schedule_list = list(queryset.values_list("id", flat=True))
		queryset = get_paginated_object(queryset, page_info["page"], page_info["paginate_by"])
		pagination_dict = data_for_vue_pagination(queryset)
		paginate_by_columns = (('name', 'Name'),
			('status', 'Status'),
			('description', 'Description'),
			)
		camp_name, active_camp, noti_count = get_active_campaign(request)
		context = {
		'id_list':schedule_list,
		"paginate_by_columns":paginate_by_columns, "noti_count":noti_count}
		context = {**context, **kwargs['permissions'], **page_info}
		if request.is_ajax():
			result = list(CampaignSchedulePaginationSerializer(queryset, many=True).data)
			pagination_dict["table_data"] = result
			context = {**context, **kwargs['permissions'], **pagination_dict}
			return JsonResponse(context)
		else:
			context = {**context, **kwargs['permissions'], **pagination_dict}
			context['request']: request
			return Response(context)

@method_decorator(check_create_permission, name='get')
@method_decorator(call_time_validation, name='post')
class CamapignScheduleCreateApiView(LoginRequiredMixin, generics.CreateAPIView):
	"""
	This view is used to create call times
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = 'campaign/campaign_schedule_create.html'
	serializer_class = CampaignScheduleSerializer

	def get(self, request, **kwargs):
		audio_files = AudioFile.objects.all()
		campaign_schedule = CampaignSchedule.objects.filter(status="Active").values("id", "name")
		context = {'request': request, "audio_files": audio_files, 'campaign_schedule_list': campaign_schedule}
		context = {**context, **kwargs['permissions']}
		return Response(context)

	def post(self, request):
		calltime_serializer = self.serializer_class(data=request.POST)
		if calltime_serializer.is_valid():
			calltime_serializer.save(created_by=request.user)
			### Admin Log ####
			create_admin_log_entry(request.user, 'CampaignSchedule', str(1),'CREATED', request.POST["name"])
			return JsonResponse({"success": "Campaign Schedule created successfully"})
		return JsonResponse({"errors": calltime_serializer.errors}, status=500)

@method_decorator(check_update_permission, name='get')
@method_decorator(call_time_validation, name='put')
class CampaignScheduleEditApiView(LoginRequiredMixin, APIView):
	"""
	This api is used to edit shift
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "campaign/campaign_schedule_edit.html"
	serializer = CampaignScheduleSerializer

	def get(self, request, pk, format=None, **kwargs):
		campaign_schedule = get_object(pk, "callcenter", "CampaignSchedule")
		audio_files = AudioFile.objects.all()
		context = {'request': request, "campaign_schedule": campaign_schedule, "audio_files": audio_files}
		context = {**context, **kwargs['permissions']}
		return Response(context)

	def put(self, request, pk, format=None):
		campaign_schedule = get_object(pk, "callcenter", "CampaignSchedule")
		serializer = self.serializer(campaign_schedule, data=request.data)
		if serializer.is_valid():
			serializer.save()
			create_admin_log_entry(request.user, 'CampaignSchedule', str(2),'UPDATED', request.POST["name"])
			return JsonResponse({"success": "Campaign Schedule updated successfully"})
		return JsonResponse({"errors": serializer.errors}, status=500)

@method_decorator(check_create_permission, name='get')
@method_decorator(campaign_validation, name='post')
class CampaignCreateApiView(LoginRequiredMixin, generics.CreateAPIView):
	"""
	This view is used to create campaign. In get method we are
	getting necessory information for pre-campaign creation
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = 'campaign/campaign_create.html'
	serializer_class = CampaignSerializer

	def get(self, request,**kwargs):
		data = get_pre_campaign_create_info(request)
		all_trunk = DialTrunk.objects.filter(status="Active")
		data["trunk_list"] = list(all_trunk.annotate(text=F('name')).values("text","id","did_range"))
		data["request"] = request
		data["can_create"] = True
		data["outbound_type"] = OUTBOUND
		data["timer_sec"] = TIMER_SEC
		data["transfer_options"] = TRANSFER_MODE
		data["all_campaign"] = Campaign.objects.values("id", "name")
		data['api_modes'] = API_MODE
		data['enable_wfh'] = pickle.loads(settings.R_SERVER.get('enable_wfh') or pickle.dumps(False))
		extension_exist = CampaignVariable.objects.all().values_list('extension',flat=True)
		latest_extension = sorted(list(set(three_digits_list) - set(extension_exist)))[0]
		data['extension'] = latest_extension
		data['trunk_group'] = list(DiaTrunkGroup.objects.all().values("id","name"))
		data = {**data, **kwargs['permissions']}
		return Response(data)

	def post(self, request):
		campaign_serializer = self.serializer_class(data=request.POST)
		lead_data = json.loads(request.POST.get("lead_recycle", ""))
		existing_campaign = request.POST.get("existing_campaign", "")
		trunk_detail = request.POST.get("trunk_detail","")
		trunk_did_data = request.POST.get("trunk_did_data","")
		if campaign_serializer.is_valid():
			campaign = campaign_serializer.save(created_by=request.user)
			if not existing_campaign:
				camp = CampaignVariable()
			else:
				camp = CampaignVariable.objects.get(campaign__id=existing_campaign)
				camp.pk = None
			camp.campaign = campaign
			camp.extension = request.POST["extension"]
			# camp.caller_id = request.POST["caller_id"]
			camp.dial_ratio = request.POST["dial_ratio"]
			camp.wfh_caller_id = request.POST["wfh_caller_id"]
			camp.save()
			if request.POST.get("trunk_type","") == "trunk_group":
				campaign.is_trunk_group = True
			else:
				trunk_did_data = json.loads(trunk_did_data)
				campaign.trunk_did = {"did":trunk_did_data["did"],"type_of_did":trunk_did_data["did_type"],
				"did_start":trunk_did_data["did_start"],"did_end":trunk_did_data["did_end"]}
				campaign.is_trunk_group = False
			campaign.save() 
			if lead_data :
				for lead in lead_data:
					lead_serializer = LeadRecycleSerializer(data=lead)
					if lead_serializer.is_valid():
						lead = lead_serializer.save()
						lead.campaign = campaign
						lead.save()
						if lead.status == 'Active':
							leadrecycle_add(instance=lead)
			if trunk_detail:
				trunk_detail = json.loads(trunk_detail)
				campaign.trunk.clear()
				for trunk in trunk_detail:
					if "exist_error" in trunk:
						del trunk["exist_error"]
					if "required_error" in trunk:
						del trunk["required_error"]
					dial_trunk_priority = DialTrunkPriority.objects.create(**trunk)
					campaign.trunk.add(dial_trunk_priority)
					campaign.save()
			if campaign.is_trunk_group:
				trunks = campaign.trunk_group.trunks.all()
				did_list = []
				for trunk in trunks:
					did_list.extend(get_group_did(trunk))
			else:
				did_list = get_campaign_did(campaign)
			campaign.all_caller_id = did_list
			campaign.save()
			### Admin Log ####
			create_admin_log_entry(request.user, 'campaign', '1','CREATED', request.POST["name"])
		else:
			print(campaign_serializer.errors)
		return JsonResponse({"success": "Campaign created successfully"})

@method_decorator(check_update_permission, name='get')
@method_decorator(campaign_edit_validation, name='put')
class CampaignEditApiView(LoginRequiredMixin, APIView):
	"""
	This api is used to edit campaign with additional
	settings which are related to telephony
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "campaign/campaign_edit.html"
	serializer = CampaignSerializer

	def get(self, request, pk, format=None, **kwargs):
		data = get_pre_campaign_edit_info(pk, request)
		print(data['campaign'])
		all_trunk = DialTrunk.objects.filter(status="Active")
		data["trunk_list"] = list(all_trunk.annotate(text=F('name')).values("text","id","did_range"))
		data["request"] = request
		data['is_edit'] = True
		data["outbound_type"] = OUTBOUND
		data["timer_sec"] = TIMER_SEC
		data['api_modes'] = API_MODE
		data["transfer_options"] = TRANSFER_MODE
		data['enable_wfh'] = pickle.loads(settings.R_SERVER.get('enable_wfh') or pickle.dumps(False))
		data['enable_vb'] = pickle.loads(settings.R_SERVER.get('enable_vb') or pickle.dumps(False))
		AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
		if AGENTS:
			all_agents = list(AGENTS.keys())
			for extension in all_agents:
								try:
										if str(extension) in AGENTS and AGENTS[str(extension)]['campaign']==data['campaign'].name:
												data['is_edit'] = False
												break
								except  Exception as e:
										print('Error is',e)
										pass                            
#				if str(extension) in AGENTS and AGENTS[str(extension)]['campaign']==data['campaign'].name:
#					data['is_edit'] = False
#					break
		all_trunk = DialTrunk.objects.filter(status="Active")
		data["trunk_list"] = list(all_trunk.annotate(text=F('name')).values("text","id","did_range"))
		data = {**data, **kwargs['permissions']}
		return Response(data)

	def put(self, request, pk, format=None):
		object_data = get_object(pk, "callcenter", "Campaign")
		serializer = self.serializer(object_data, data=request.data)
		lead_data = json.loads(request.POST.get("lead_recycle", ""))
		delete_lead = request.POST.getlist("delete_lead_id", "")
		dial_method = json.loads(request.data.get('dial_method'))
		trunk_did_data = request.POST.get("trunk_did_data","")
		if serializer.is_valid():
			css_val = request.data.get('css',False)
			if css_val == 'on':
				css_val = True
			if object_data.css != css_val:
				update_contact_on_css(object_data.name)
			portifolio_val = request.data.get('portifolio',False)
			if portifolio_val == 'on':
				portifolio_val = True
			if object_data.portifolio != portifolio_val:
				update_contact_on_portifolio(object_data)
			campaign = serializer.save()
			if request.POST.get("trunk_type","") == "trunk_group":
				campaign.is_trunk_group = True
			else:
				campaign.is_trunk_group = False
				trunk_did_data = json.loads(trunk_did_data)
				campaign.trunk_did = {"did":trunk_did_data["did"],"type_of_did":trunk_did_data["did_type"],
				"did_start":trunk_did_data["did_start"],"did_end":trunk_did_data["did_end"]}
			campaign.save()
			if campaign.status == 'Inactive':
				PhonebookBucketCampaign.objects.filter(id=campaign.id).update(is_contact=False)
			else:
				PhonebookBucketCampaign.objects.filter(id=campaign.id).update(is_contact=True)
			camp_var = CampaignVariable.objects.get(campaign=campaign)
			camp_variable_serializer = UpdateCampaignSerializer(camp_var, data=request.data)
			if camp_variable_serializer.is_valid():
				camp_variable_serializer.save()
			if delete_lead:
				LeadRecycle.objects.filter(id__in=delete_lead).delete()
				for lead_id in delete_lead:
					leadrecycle_del(job_id=campaign.name+"_"+str(lead_id))
			if lead_data :
				for lead in lead_data:
					lead_inst = LeadRecycle.objects.filter(campaign=campaign, id=lead.get("lead_id",0))
					if lead_inst.exists():
						created = False
						lead_serializer = LeadRecycleSerializer(lead_inst[0], data=lead)
					else:
						lead_serializer = LeadRecycleSerializer(data=lead)
						created = True
					if lead_serializer.is_valid():
						temp_lead = lead_serializer.save(campaign=campaign)
					
					if temp_lead.status == 'Active':
						leadrecycle_add(instance=temp_lead)
					else:
						leadrecycle_del(job_id=campaign.name+"_"+str(temp_lead.id))
			if campaign.is_trunk_group:
				trunks = campaign.trunk_group.trunks.all()
				did_list = []
				for trunk in trunks:
					did_list.extend(get_group_did(trunk))
			else:
				did_list = get_campaign_did(campaign)
			campaign.all_caller_id = did_list
			campaign.save()
			### Admin Log ####
			create_admin_log_entry(request.user, 'campaign', '2','UPDATED', request.POST["name"])
			return JsonResponse({"success": "Campaign updated successfully"})
		return JsonResponse({"errors": serializer.errors}, status=500)

@method_decorator(check_read_permission, name='get')
class CampaignListApiView(LoginRequiredMixin, APIView):
	"""
	This view is used to display list of campaign with
	brief info
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "campaign/campaign.html"

	def get(self, request, **kwargs):
		page_info = data_for_pagination(request)
		campaign = Campaign.objects.all()
		if check_non_admin_user(request.user):
			campaign = campaign.filter(Q(users=request.user)|Q(group__in=request.user.group.all())|Q(created_by=request.user)).distinct()
		if page_info["search_by"] and page_info["column_name"]:
			if page_info["column_name"] == "switch":
				campaign = campaign.filter(switch__name__istartswith=page_info["search_by"])
			elif page_info["column_name"] == "extension":
				campaignVar = CampaignVariable.objects.filter(
					extension=page_info["search_by"]).values_list("id", flat=True)
				campaign = campaign.filter(id__in=campaignVar)
			else:
				campaign = campaign.filter(**{page_info["column_name"]+"__istartswith": page_info["search_by"]})
		campaign = campaign.prefetch_related('group', 'trunk', 'switch')
		campaign_ids = list(campaign.values_list("id", flat=True))
		campaign = get_paginated_object(campaign, page_info["page"], page_info["paginate_by"])
		pagination_dict = data_for_vue_pagination(campaign)
		paginate_by_columns = (('name', 'Camapign Name'),
			('extension', 'Extension'),
			('switch', 'switch'),
			('status','status')
			)
		camp_name, active_camp, noti_count = get_active_campaign(request)
		context = {"id_list": campaign_ids,
		"paginate_by_columns":paginate_by_columns,"noti_count":noti_count
		}
		context = {**context, **kwargs['permissions'], **page_info}
		if request.is_ajax():
			result = list(CampaignPaginationSerializer(campaign, many=True).data)
			pagination_dict["table_data"] = result
			context = {**context, **kwargs['permissions'], **pagination_dict}
			return JsonResponse(context)
		else:
			context = {**context, **kwargs['permissions'], **pagination_dict}
			context['request']: request
			return Response(context)

@method_decorator(check_read_permission, name='get')
class InGroupCampaignListApiView(LoginRequiredMixin, APIView):
	"""
	This view is used to display list of campaign with
	brief info
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "campaign/ingroup_campaign.html"

	def get(self, request, **kwargs):
		page_info = data_for_pagination(request)
		ingroup_campaign = InGroupCampaign.objects.all()
		if check_non_admin_user(request.user):
			campaigns = Campaign.objects.filter(Q(users=request.user)|Q(group__in=request.user.group.all())|Q(created_by=request.user)).distinct()
			campaign_priority = CampaignPriority.objects.filter(campaign__in=campaigns)
			ingroup_campaign = ingroup_campaign.filter(ingroup_campaign__in=campaign_priority)
		if page_info["search_by"] and page_info["column_name"]:
			ingroup_campaign = ingroup_campaign.filter(**{page_info["column_name"]+"__istartswith": page_info["search_by"]})
		ingroup_campaign = ingroup_campaign.prefetch_related('ingroup_campaign')
		ingroup_ids = list(ingroup_campaign.values_list("id", flat=True))
		ingroup_campaign = get_paginated_object(ingroup_campaign, page_info["page"], page_info["paginate_by"])
		pagination_dict = data_for_vue_pagination(ingroup_campaign)
		paginate_by_columns = (('name', 'InGroup Name'),
			('ingroup_campaign__campaign__name', 'Camapign Name'),
			('status','status')
			)
		context = {"id_list": ingroup_ids,
		"paginate_by_columns":paginate_by_columns,
		}
		context = {**context, **kwargs['permissions'], **page_info}
		if request.is_ajax():
			result = list(InGroupCampaignPaginationSerializer(ingroup_campaign, many=True).data)
			pagination_dict["table_data"] = result
			context = {**context, **kwargs['permissions'], **pagination_dict}
			return JsonResponse(context)
		else:
			context = {**context, **kwargs['permissions'], **pagination_dict}
			context['request']: request
			return Response(context)

@method_decorator(check_read_permission, name='get')
class InGroupCampaignCreateApiView(LoginRequiredMixin, APIView):
	"""
	This view is used to create campaign. In get method we are
	getting necessory information for pre-campaign creation
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = 'campaign/ingroup_create.html'
	serializer_class = IngroupCampaignSerializer

	def get(self, request, pk=None, format=None, **kwargs):
		data = {}
		ingroup_campaigns = []
		non_user_campaign = []
		non_admin_user = check_non_admin_user(request.user)
		data["is_campaign"] = True
		if pk:
			data["can_edit"] = True
			data["ingroup_campaign"] = InGroupCampaign.objects.get(id=pk)
			if not data["ingroup_campaign"].ingroup_campaign.exists():
				data["is_campaign"] = False
			elif non_admin_user:
				ingroup_campaigns = data["ingroup_campaign"].ingroup_campaign.values_list('campaign__name',flat=True)
				non_user_campaign = data["ingroup_campaign"].ingroup_campaign.exclude(Q(campaign__users=request.user)|Q(campaign__group__in=request.user.group.all())|Q(campaign__created_by=request.user)).distinct().values_list('campaign__id',flat=True)
		else:
			data["can_create"] = True
		data["used_did"] = []
		data["ingroup_status"] = Status
		data["ingroup_strategy"] =STRATEGY_CHOICES
		all_trunk = DialTrunk.objects.filter(status="Active")
		data["trunk_list"] = list(all_trunk.annotate(text=F('name')).values("text","id","did_range"))
		if pk:
			data["used_did"] = get_used_did_by_pk(pk, 'ingroup')
		else:
			data["used_did"] = get_used_did('ingroup')
		campaigns = Campaign.objects.filter(dial_method__contains={"inbound":True}).annotate(text=F('name')).values("text","id")
		if non_admin_user:
			campaigns = campaigns.filter(Q(users=request.user)|Q(group__in=request.user.group.all())|Q(created_by=request.user)|Q(name__in=ingroup_campaigns)).distinct()
		data["campaign_list"] = list(campaigns)
		data["non_user_campaign"] = list(non_user_campaign)
		return Response(data)

	def post(self, request, pk=None, format=None):
		campaign_details = request.POST.get("campaign_data")
		if pk:
			object_data = get_object(pk, "callcenter", "InGroupCampaign")
			serializer = self.serializer_class(object_data, data=request.POST)
		else:
			serializer = self.serializer_class(data=request.POST)
		if serializer.is_valid():
			ingroup = serializer.save()
			if campaign_details:
				campaign_details = json.loads(campaign_details)
				camp_priority_list = []
				for camp in campaign_details:
					if camp["campaign_id"] !="":
						camp_priority_list.append(CampaignPriority.objects.create(**camp))
				ingroup.ingroup_campaign.clear()
				ingroup.ingroup_campaign.add(*camp_priority_list)
				ingroup.created_by = request.user
				ingroup.save()
			return Response({'msg': 'group created'})
		return Response({'msg': 'Name already exists'}, status=500)

	def put(self, request, format=None):
		ingroup_id = request.POST.get("in_group_id","")
		exists = False
		if request.POST.get("campaign_id"):
			ingroup_inst = InGroupCampaign.objects.filter(ingroup_campaign__campaign_id=request.POST.get("campaign_id"))
			if ingroup_inst.exists():
				if ingroup_id:
					if ingroup_inst.exclude(id=ingroup_id).exists():
						exists = True
				else:
					exists = True
		return JsonResponse({'exists': exists})

@method_decorator(check_read_permission, name='get')
class ScriptListApiView(LoginRequiredMixin, generics.ListAPIView):
	"""
	This view is used to show users all types of script they have
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "admin/script_list.html"
	
	def get(self, request, **kwargs):
		page_info = data_for_pagination(request)
		script = Script.objects.all()
		if check_non_admin_user(request.user):
			user_campaigns = Campaign.objects.filter(Q(users=request.user)|Q(group__in=request.user.group.all())|Q(created_by=request.user)).distinct()
			script = script.filter(campaign__in=user_campaigns)
		if page_info["search_by"] and page_info["column_name"]:
			script = Script.objects.filter(**{page_info["column_name"]+"__iexact": page_info["search_by"]})
		script = script.select_related("campaign")
		script_list = list(script.values_list("id", flat=True))
		script = get_paginated_object(script, page_info["page"], page_info["paginate_by"])
		pagination_dict = data_for_vue_pagination(script)
		paginate_by_columns = (('name', 'Camapign Name'),
			('status', 'status'),
			)
		camp_name, active_camp, noti_count = get_active_campaign(request)
		context = {
		"id_list":script_list,
		"paginate_by_columns":paginate_by_columns, "noti_count":noti_count}
		context = {**context, **kwargs['permissions'], **page_info}

		if request.is_ajax():
			result = list(ScriptPaginationSerializer(script, many=True).data)
			pagination_dict["table_data"] = result
			context = {**context, **kwargs['permissions'], **pagination_dict}
			return JsonResponse(context)
		else:
			context = {**context, **kwargs['permissions'], **pagination_dict}
			context['request']: request
			return Response(context)

@method_decorator(check_read_permission, name='get')
@method_decorator(script_validation, name='post')
class ScriptCreateEditApiView(LoginRequiredMixin, APIView):
	"""
	This view is used to create and edit script also validating
	script with given name already exist or not
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "admin/script.html"
	serializer = ScriptSerializer

	def get(self, request, pk="", **kwargs):
		can_view= False
		campaigns = Campaign.objects.values('id','slug')
		if check_non_admin_user(request.user):
			campaigns =campaigns.filter(Q(users=request.user)|Q(group__in=request.user.group.all())|Q(created_by=request.user)).distinct()
		permission_dict = kwargs['permissions']
		contact_fields = ['numeric', 'alt_numeric', 'first_name', 'last_name', 'email']
		if pk:
			script = get_object(pk, "callcenter", "Script")
			crm_fields = get_customizable_crm_fields(script.campaign.slug)
			contact_fields = contact_fields + crm_fields
			if permission_dict['can_update']:
				can_view = True
		else:
			if permission_dict['can_create']:
				can_view = True
			script = ""
		return Response({"request": request,'campaign_list':campaigns,"script_status": Status,
						"script": script,'can_view':can_view,'contact_fields':contact_fields})

	def post(self, request):
		log_type = 1
		if request.POST.get("script_id", ""):
			pk = request.POST.get("script_id", "")
			script = get_object(pk, "callcenter", "Script")
			script_exist = Script.objects.filter(name=request.POST["name"]).exclude(
				id=script.id).exists()
			script_serializer = self.serializer(script, data=request.data)
			log_type = 2
		else:
			script_serializer = self.serializer(data=request.data)
			script_exist = Script.objects.filter(name=request.POST["name"]).exists()

		if script_serializer.is_valid():
			script_serializer.save(created_by=request.user)
			### Admin Log ####
			create_admin_log_entry(request.user, 'Script', str(log_type),'CREATED', request.POST["name"])
		return Response()

class ScriptGetCrmFieldsApiView(APIView):
	"""
	Get the crm fields that are going to defined in the script
	"""
	def post(self, request, **kwargs):
		field_list = []
		campaign_id = request.POST.get("campaign_id","0")
		campaign_name = request.POST.get("campaign_name", "")
		script_id = request.POST.get("script_id", "0")
		if not script_id:
			script_id = 0
		script_obj = Script.objects.filter(campaign=campaign_id).exclude(id=script_id)
		if script_obj.exists():
			return JsonResponse({'script_exists':'Selected campaign already have a Script'})
		crm_fields = get_customizable_crm_fields(campaign_name)
		contact_fields = ['numeric', 'alt_numeric', 'first_name', 'last_name', 'email']
		contact_fields = contact_fields + crm_fields
		context = {'contact_fields':contact_fields}
		return JsonResponse(context)    

@method_decorator(check_read_permission, name='get')
class AudioListApiView(LoginRequiredMixin, generics.ListAPIView):
	'''
	This view is used to show list of audio files
	'''
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "campaign/audio.html"

	def get(self, request, **kwargs):
		page_info = data_for_pagination(request)
		
		if page_info["search_by"] and page_info["column_name"]:
			queryset = AudioFile.objects.filter(**{page_info["column_name"]+"__iexact": page_info["search_by"]})
		else:
			queryset = AudioFile.objects.all()
		audio_list = list(queryset.values_list("id", flat=True))
		queryset = get_paginated_object(queryset, page_info["page"], page_info["paginate_by"])
		pagination_dict = data_for_vue_pagination(queryset)
		paginate_by_columns = (('name', 'Name'),
			('description', 'Description'),
			('status', 'Status'),
			)
		camp_name, active_camp, noti_count = get_active_campaign(request)
		context = {"id_list":audio_list,
					"audio_status": Status, "audio_list": audio_list,
					"paginate_by_columns":paginate_by_columns,
					"noti_count":noti_count}
		context = {**context, **kwargs['permissions'], **page_info}

		if request.is_ajax():
			result = list(AudioPaginationSerializer(queryset, many=True).data)
			pagination_dict["table_data"] = result
			context = {**context, **kwargs['permissions'], **pagination_dict}
			return JsonResponse(context)
		else:
			context = {**context, **kwargs['permissions'], **pagination_dict}
			context['request']: request
			return Response(context)

@method_decorator(check_read_permission, name='get')
class UserRoleView(LoginRequiredMixin, generics.ListAPIView):
	"""
	This View is used to show user role list
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "users/user_role.html"
	permissions = {"Dashboard": ["all"]}
	
	def get(self, request, *args, **kwargs):
		page = int(request.GET.get('page' ,1))
		paginate_by = int(request.GET.get('paginate_by', 10))
		search_by = request.GET.get('search_by','')
		column_name = request.GET.get('column_name', '')
		if search_by and column_name:
			user_roles = UserRole.objects.filter(**{column_name+"__istartswith": search_by})
		else:
			user_roles = UserRole.objects.all()
		role_list = list(user_roles.values_list("id", flat=True))
		user_roles = get_paginated_object(user_roles, page, paginate_by)
		paginate_by_columns = (('name', 'role'),
			('access_level', 'Access Level'),
			('status', 'status'),
			)
		camp_name, active_camp, noti_count = get_active_campaign(request)
		context = {
		'paginate_by':paginate_by,
		'id_list': role_list, 'paginate_by_list':PAGINATE_BY_LIST, 
		'search_by':search_by, 'column_name':column_name, 
		'paginate_by_columns':paginate_by_columns,
		'noti_count':noti_count}
		context = {**context, **kwargs['permissions']}
		pagination_dict = data_for_vue_pagination(user_roles)
		if request.is_ajax():
			result = list(UserRolePaginationSerializer(user_roles, many=True).data)
			pagination_dict["table_data"] = result
			context = {**context, **kwargs['permissions'], **pagination_dict}
			return JsonResponse(context)
		else:
			context = {**context, **kwargs['permissions'], **pagination_dict}
			context['request']: request
			return Response(context)

@method_decorator(check_create_permission, name='get')
@method_decorator(user_role_validation, name='post')
class UserRoleCreateApiView(LoginRequiredMixin,APIView):
	"""
	This view is to create user role and permissions.
	"""
	login_url = "/"
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "users/user_role_create.html"

	def get(self, request, **kwargs):
		queryset = Modules.objects.filter(parent=None, status='Active').order_by('sequence')
		modules = ModuleSerializer(queryset,many=True).data
		context = {'modules':modules, 'access_levels':ACCESS_LEVEL}
		context = {**context, **kwargs['permissions']}
		return Response(context)

	def post(self, request):
		serializer_class = UserRoleSerializer(data=request.POST)
		if serializer_class.is_valid():
			serializer_class.save(created_by=request.user)
			create_admin_log_entry(request.user, "user role","1",'CREATED',request.POST["name"])
		return Response()

@method_decorator(check_update_permission, name='get')
@method_decorator(user_role_validation, name='put')
class UserRoleModifyView(LoginRequiredMixin, APIView):
	"""
	Retrieve, update or delete a UserRoleModifyView instance.
	"""
	login_url = "/"
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "users/user_role_edit.html"
	serializer = UserRoleSerializer

	def get(self, request, pk, format=None, **kwargs):
		exclude_modules = []
		for module_name in flexydial_modules:
			enabled = pickle.loads(settings.R_SERVER.get(module_name) or pickle.dumps(False))
			if not enabled:
				exclude_modules.append(module_name)
		modules = ModuleSerializer(Modules.objects.filter(parent=None, status='Active').exclude(name__in=exclude_modules),many=True).data
		object_data = get_object(pk, "callcenter", "UserRole")
		context = {'modules':modules, 'querysets': object_data,
			'permissions': object_data.permissions,'request': request,
			'access_levels':ACCESS_LEVEL}
		context = {**context, **kwargs['permissions']}
		return Response(context)

	def put(self, request, pk, format=None):
		object_data = get_object(pk, "callcenter", "UserRole")
		serializer = self.serializer(object_data, data=request.data)
		if serializer.is_valid():
			serializer.save()
			create_admin_log_entry(request.user, "user role","2",'UPDATED',request.POST["name"])
			return Response()
		return Response(serializer.errors, status=500)

@method_decorator(audio_file_validation, name='post')
class UploadAudioFileApiView(LoginRequiredMixin, APIView):
	'''
	This view is used to upload audio and edit audio files
	'''
	login_url = "/"
	serializer = AudioSerializer

	def get(self, request, pk, format=None):
		audio_file = get_object(pk, "callcenter", "AudioFile")
		serializer = self.serializer(audio_file)
		return Response(serializer.data)

	def post(self, request, pk="", format=None):
		log_type = 1
		if pk:
			audio_file = get_object(pk, "callcenter", "AudioFile")
			audio_serializer = self.serializer(
					audio_file, data=request.data)
			log_type = 2
		else:
			audio_serializer = self.serializer(data=request.data)
		if audio_serializer.is_valid():
			audio_serializer.save(created_by=request.user)
			### Admin Log ####
			create_admin_log_entry(request.user, 'AudioFile', str(log_type),'UPLOADED', request.POST["name"])
			return Response()
		else:
			return Response()

@method_decorator(check_read_permission, name='post')
@method_decorator(check_read_permission, name='get')
class CallDetailReportView(LoginRequiredMixin,APIView):
	"""
	This View is used to show call detail with recordings
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer,DatatablesRenderer]
	template_name = "reports/call-detail-report.html"
	permissions = {"Dashboard": ["all"]}
	serializer_class = CallDetailReportSerializer
	paginator = DatatablesPageNumberPagination

	def get(self, request, *args, **kwargs):
		user_list = campaign_list = camp_id = disposition = uniquefields = []
		admin = False
		report_visible_cols = get_report_visible_column("1",request.user)
		if request.user.user_role and request.user.user_role.access_level == 'Admin':
			admin = True
		if request.user.is_superuser or admin:
			camp = Campaign.objects.all().prefetch_related(
				'users', 'group', 'disposition').distinct()
			campaign_list = camp.values("id", "name")
			camp_id = list(camp.values_list("id",flat=True))
			user_list = User.objects.all().exclude(
				user_role__access_level="Admin").prefetch_related(
				'group', 'reporting_to', 'user_role').values("id", "username")
			disposition = Disposition.objects.all()
			dispo_keys = list(disposition.values_list('dispo_keys',flat=True))
			dispo_keys = set([item for sublist in dispo_keys for item in sublist])
		else:
			camp = Campaign.objects.filter(Q(users=request.user, users__isnull=False)|
				Q( group__in=request.user.group.all(), group__isnull=False)).prefetch_related(
				'users', 'group', 'disposition').distinct()
			campaign_list = camp.values("id", "name")
			camp_id = list(camp.values_list("id",flat=True))
			c_user  = []
			c_group = []
			for campaign in camp:
				c_user.extend(list(campaign.users.all().values_list("id", flat=True)))
				c_group.extend(list(campaign.group.all().values_list("id", flat=True)))
			c_group_user = User.objects.filter(group__id__in=c_group).prefetch_related(
				'group', 'reporting_to', 'user_role')
			c_users = User.objects.filter(id__in=c_user).prefetch_related(
				'group', 'reporting_to', 'user_role')
			total_camp_users = c_group_user | c_users

			#reporting users
			users = User.objects.filter(reporting_to = request.user).prefetch_related(
				'group', 'reporting_to', 'user_role')
			if request.user.user_role.access_level == 'Manager':
				team = User.objects.filter(reporting_to__in = users)
				users = users | team
			final_camp_users = total_camp_users | users
			final_camp_users = final_camp_users.exclude(user_role__access_level="Admin").exclude(is_superuser=True)
			user_list = final_camp_users.values("id", "username")

			dispo = camp.values_list("disposition__id", flat=True)
			disposition = Disposition.objects.filter(id__in=dispo)
			dispo_keys = list(disposition.values_list('dispo_keys',flat=True))
			dispo_keys = set([item for sublist in dispo_keys for item in sublist])
		uniquefields = list(CrmField.objects.filter(campaign__in=camp_id).distinct().values_list('unique_fields',flat=True))
		uniquefields = sorted(set(itertools.chain.from_iterable(uniquefields)))
		show_result = request.GET.get("show_result", "")
		context = {'request': request, 'campaign_list': campaign_list}
		all_fields = {'diallereventlog':['hangup_cause','hangup_cause_code','dialed_status'],'smslog':['sms_sent','sms_message'],
		"calldetail":['campaign_name','user','full_name','phonebook','customer_cid','contact_id','lan','product',
		'session_uuid','init_time','ring_time','connect_time','hangup_time','wait_time','ring_duration','hold_time','callflow','callmode',
		'bill_sec','ivr_duration','call_duration','feedback_time','call_length','hangup_source','internal_tc_number','external_tc_number','progressive_time','preview_time','predictive_wait_time','inbound_wait_time','blended_wait_time'],
		'cdrfeedback':['primary_dispo','feedback','relationtag']}
		context['users'] = list(user_list)
		context['disposition'] = disposition.values("id", "name")
		context['dispo_keys'] = dispo_keys
		context['all_fields'] = all_fields
		context['uniquefields'] = uniquefields
		camp_name, active_camp, noti_count = get_active_campaign(request)
		context["noti_count"] = noti_count
		context['report_visible_cols'] = report_visible_cols
		context = {**context, **kwargs['permissions']}
		return Response(context)

	def post(self,request, *args, **kwargs):
		paginator = self.paginator()
		admin = False
		query = {}
		if request.user.user_role and request.user.user_role.access_level == 'Admin':
			admin = True
		download_report = request.POST.get("agent_reports_download", "")
		if download_report:
			col_name = request.POST.get("column_name", "")
			col_list = col_name.split(",")
			filters = request.POST.dict()
			filters['all_campaigns'] = request.POST.get("all_campaigns", "").split(',')
			filters['all_users'] = request.POST.get("all_users", "").split(',')
			filters['selected_campaign'] = request.POST.getlist("selected_campaign", [])
			filters['selected_disposition'] = request.POST.getlist("selected_disposition", [])
			filters['selected_user'] = request.POST.getlist("selected_user", [])
			filters['download_type'] = request.POST.get("agent_reports_download_type",'csv')
			filters['unique_id'] = request.POST.get("unique_id", '')
			filters['uniquefields'] = request.POST.get("uniquefields","")
			#DownloadReports.objects.create(report='Call Details',filters=filters, user=request.user.id, serializers=self.serializer_class, col_list=col_list, status=True)
			return JsonResponse({"message":"Your Download request is created, will notify in download notification once completed."})
		else:
			all_campaigns = request.POST.getlist("all_campaigns[]", [])
			all_users = request.POST.getlist("all_users[]", [])
			selected_campaign = request.POST.getlist("selected_campaign[]", "")
			selected_disposition = request.POST.getlist("selected_disposition[]", "")
			selected_user = request.POST.getlist("selected_user[]", "")
			unique_id = request.POST.get("unique_id", '')
		numeric = request.POST.get("numeric", "")
		start_date = request.POST.get("start_date", "")
		end_date = request.POST.get("end_date", "")
		uniquefields = request.POST.get("uniquefields","")
		if uniquefields:
			uniquefields = uniquefields.split(',')
		else:
			uniquefields = []
		crmfield_context = get_transform_key(uniquefields)
		start_date = datetime.strptime(start_date,"%Y-%m-%d %H:%M").isoformat()
		end_date = datetime.strptime(end_date,"%Y-%m-%d %H:%M").isoformat()         
		start_end_date_filter = Q(created__gte=start_date)&Q(created__lte=end_date)
		if selected_user:
			all_users = selected_user
		if selected_disposition:
			query['cdrfeedback__primary_dispo__in']  = selected_disposition
		if numeric:
			query['customer_cid'] = numeric
		if unique_id:
			query["uniqueid"] = unique_id
		if selected_campaign:
			query_string = Q(campaign_name__in = selected_campaign,user_id__in=all_users)|Q(campaign_name__in = selected_campaign,user=None)
		else:
			query_string = Q(user_id__in=all_users)|Q(user=None)
		if selected_user and selected_campaign:
			query_string = Q(campaign_name__in=list(selected_campaign), user_id__in=list(all_users))
		elif selected_user:
			query_string = Q(user_id__in=all_users)
		elif selected_campaign:
			query_string = Q(campaign_name__in=selected_campaign)
			if not (request.user.is_superuser or admin):
				get_camp_users = list(get_campaign_users(selected_campaign, 
				request.user).values_list("id",flat=True))
				query_string=Q(campaign_name__in = selected_campaign,user__in=get_camp_users)|Q(campaign_name__in = selected_campaign,user=None)
		queryset = CallDetail.objects.filter(start_end_date_filter).filter(query_string).filter(**query).select_related("campaign", "user")
		if request.POST.get('format', None) == 'datatables':
			paginator.is_datatable_request = True
		else:
			paginator.is_datatable_request = False
			
		page = paginate_queryset(request, queryset, paginator)
		if page is not None:
			serializer = self.serializer_class(page, many=True)
			return get_paginated_response(serializer.data, paginator)
		serializer = self.serializer_class(queryset, many=True)
		return Response(serializer.data)


@method_decorator(check_read_permission, name='post')
@method_decorator(check_read_permission, name='get')
class LanReportView(LoginRequiredMixin,APIView):
	"""
	This View is used to show call detail with recordings
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer,DatatablesRenderer]
	template_name = "reports/lan_report.html"
	permissions = {"Dashboard": ["all"]}
	paginator = DatatablesPageNumberPagination
	def get(self, request, *args, **kwargs):
		user_list = campaign_list = camp_id = disposition = uniquefields = []
		admin = False
		report_visible_cols = get_report_visible_column("16",request.user)
		if request.user.user_role and request.user.user_role.access_level == 'Admin':
			admin = True
		if request.user.is_superuser or admin:
			camp = Campaign.objects.all().prefetch_related(
				'users', 'group', 'disposition').distinct()
			campaign_list = camp.values("id", "name")
			camp_id = list(camp.values_list("id",flat=True))
			user_list = User.objects.all().exclude(
				user_role__access_level="Admin").prefetch_related(
				'group', 'reporting_to', 'user_role').values("id", "username")
			disposition = Disposition.objects.all()
			dispo_keys = list(disposition.values_list('dispo_keys',flat=True))
			dispo_keys = set([item for sublist in dispo_keys for item in sublist])
			
		else:
			camp = Campaign.objects.filter(Q(users=request.user, users__isnull=False)|
				Q( group__in=request.user.group.all(), group__isnull=False)).prefetch_related(
				'users', 'group', 'disposition').distinct()
			campaign_list = camp.values("id", "name")
			camp_id = list(camp.values_list("id",flat=True))
			c_user  = []
			c_group = []
			for campaign in camp:
				c_user.extend(list(campaign.users.all().values_list("id", flat=True)))
				c_group.extend(list(campaign.group.all().values_list("id", flat=True)))
			c_group_user = User.objects.filter(group__id__in=c_group).prefetch_related(
				'group', 'reporting_to', 'user_role')
			c_users = User.objects.filter(id__in=c_user).prefetch_related(
				'group', 'reporting_to', 'user_role')
			total_camp_users = c_group_user | c_users
			#reporting users
			users = User.objects.filter(reporting_to = request.user).prefetch_related(
				'group', 'reporting_to', 'user_role')
			if request.user.user_role.access_level == 'Manager':
				team = User.objects.filter(reporting_to__in = users)
				users = users | team
			final_camp_users = total_camp_users | users
			final_camp_users = final_camp_users.exclude(user_role__access_level="Admin").exclude(is_superuser=True)
			user_list = final_camp_users.values("id", "username")
			dispo = camp.values_list("disposition__id", flat=True)
			disposition = Disposition.objects.filter(id__in=dispo)
			dispo_keys = list(disposition.values_list('dispo_keys',flat=True))
			dispo_keys = set([item for sublist in dispo_keys for item in sublist])
		uniquefields = list(CrmField.objects.filter(campaign__in=camp_id).distinct().values_list('unique_fields',flat=True))
		uniquefields = sorted(set(itertools.chain.from_iterable(uniquefields)))
		show_result = request.GET.get("show_result", "")
		context = {'request': request, 'campaign_list': campaign_list}
		all_fields =  ['lan','primary_dispo','created_on','customer_cid','username','comment']
		context['all_fields'] = all_fields
		context['users'] = list(user_list)
		context['disposition'] = disposition.values("id", "name")
		context['dispo_keys'] = dispo_keys
		context['uniquefields'] = uniquefields
		camp_name, active_camp, noti_count = get_active_campaign(request)
		context["noti_count"] = noti_count
		context['report_visible_cols'] = report_visible_cols
		context = {**context, **kwargs['permissions']}
		return Response(context)
	def post(self,request, *args, **kwargs):
		admin = False
		query = {}
		if request.user.user_role and request.user.user_role.access_level == 'Admin':
			admin = True
		download_report = request.POST.get("agent_reports_download", "")
		if download_report:
			col_name = request.POST.get("column_name", "")
			col_list = col_name.split(",")
			original_col = request.POST.get('original_col','').split(',')
			filters = request.POST.dict()
			filters['all_campaigns'] = request.POST.get("all_campaigns", "").split(',')
			filters['all_users'] = request.POST.get("all_users", "").split(',')
			filters['selected_campaign'] = request.POST.getlist("selected_campaign", [])
			filters['selected_disposition'] = request.POST.getlist("selected_disposition", [])
			filters['selected_user'] = request.POST.getlist("selected_user", [])
			filters['unique_id'] = request.POST.get("unique_id", '')
			DownloadReports.objects.create(report='Lan Report',filters=filters, user=request.user.id, serializers=None, col_list=col_list, status=True)
			return JsonResponse({"message":"Your Download request is created, will notify in download notification once completed."})
		else:
			all_campaigns = request.POST.getlist("all_campaigns[]", [])
			all_users = request.POST.getlist("all_users[]", [])
			selected_campaign = request.POST.getlist("selected_campaign[]", "")
			selected_disposition = request.POST.getlist("selected_disposition[]", "")
			selected_user = request.POST.getlist("selected_user[]", "")
			unique_id = request.POST.get("unique_id", '')
		numeric = request.POST.get("numeric", "")
		start_date = request.POST.get("start_date", "")
		end_date = request.POST.get("end_date", "")
		start_date = datetime.strptime(start_date,"%Y-%m-%d %H:%M").isoformat()
		end_date = datetime.strptime(end_date,"%Y-%m-%d %H:%M").isoformat()      
		start_end_date_filter = Q(created__gte=start_date)&Q(created__lte=end_date)
		if selected_user:
			all_users = selected_user
		if selected_disposition:
			query['cdrfeedback__primary_dispo__in']  = selected_disposition
		if numeric:
			query['customer_cid'] = numeric
		if unique_id:
			query["uniqueid"] = unique_id
		if selected_user:
			query_string = Q(user_id__in=all_users)
		else:
			query_string = Q(user_id__in=all_users)|Q(user=None)
		exclude_nonuser_dispo = ['Redialled','Alternate Dial','Primary Dial','Auto Feedback', '']
		queryset = CallDetail.objects.filter(start_end_date_filter).filter(**query).exclude(uniqueid=None).prefetch_related('cdrfeedback').exclude(cdrfeedback__primary_dispo=None).exclude(cdrfeedback__primary_dispo__in=exclude_nonuser_dispo).values_list('uniqueid',flat=True).distinct('uniqueid').order_by('uniqueid')
		page = int(request.POST.get('page' ,1))
		paginate_by = int(request.POST.get('paginate_by', 10))
		
		queryset = get_paginated_object(queryset, page, paginate_by)
		c_list = []
		for lan in queryset:
			final_dict ={}
			final_dict['lan'] =lan
			uni_list = list(CallDetail.objects.filter(uniqueid = lan).exclude(uniqueid=None)
				.prefetch_related('cdrfeedback')
				.exclude(cdrfeedback__primary_dispo=None)
				.exclude(cdrfeedback__primary_dispo__in=exclude_nonuser_dispo)
				.annotate(username=F('user__username'))
				.annotate(primary_dispo=F('cdrfeedback__primary_dispo'))
				.annotate(comment=F('cdrfeedback__comment'))
				.annotate(created_on=F('init_time'))
				.annotate(lan=F('uniqueid'))
				.values('lan','primary_dispo','customer_cid','created_on','comment','username').order_by('-id')[:10])
			if uni_list:
				final_dict['last_ten_data']=uni_list
				c_list.append(final_dict)
		return JsonResponse({'total_records': queryset.paginator.count, 'total_pages': queryset.paginator.num_pages, 
			'page': queryset.number, 'has_next': queryset.has_next(), 'has_prev': queryset.has_previous(),
			'start_index':queryset.start_index(), 'end_index':queryset.end_index(),
			'table_data':c_list})


@method_decorator(check_read_permission, name='get')
class CallRecordingView(LoginRequiredMixin, generics.ListAPIView):
	"""
	This View is used to show call detail with recordings
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "reports/call-recordings.html"
	permissions = {"Dashboard": ["all"]}

	def get(self, request, *args, **kwargs):
		user_list = campaign_list = []
		admin = False
		report_visible_cols = get_report_visible_column("2",request.user)
		if request.user.user_role and request.user.user_role.access_level == 'Admin':
			admin = True
		if request.user.is_superuser or admin:
			can_qc_update = "true"
			campaign_list = Campaign.objects.all().prefetch_related(
				'users', 'group', 'disposition').distinct().values("id", "name")
			user_list = User.objects.all().exclude(
				user_role__access_level="Admin").exclude(is_superuser=True).prefetch_related(
				'group', 'reporting_to', 'user_role').values("id", "username")
		else:
			permissions = request.user.user_role.permissions
			can_qc_update = "false"
			if 'qc_feedback' in permissions and 'C' in permissions['qc_feedback'] :
				can_qc_update = "true"
			camp = Campaign.objects.filter(Q(users=request.user, users__isnull=False)|
				Q( group__in=request.user.group.all(), group__isnull=False)).prefetch_related(
				'users', 'group', 'disposition').distinct()
			campaign_list = camp.values("id", "name")
			c_user  = c_group = []
			for campaign in camp:
				c_user.extend(list(campaign.users.all().values_list("id", flat=True)))
				c_group.extend(list(campaign.group.all().values_list("id", flat=True)))
			c_group_user = User.objects.filter(group__id__in=c_group).prefetch_related(
				'group', 'reporting_to', 'user_role')
			c_users = User.objects.filter(id__in=c_user).prefetch_related(
				'group', 'reporting_to', 'user_role')
			total_camp_users = c_group_user | c_users
			#reporting users
			users = User.objects.filter(reporting_to = request.user).prefetch_related(
				'group', 'reporting_to', 'user_role')
			if request.user.user_role.access_level == 'Manager':
				team = User.objects.filter(reporting_to__in = users)
				users = users | team
			final_camp_users = total_camp_users | users
			final_camp_users = final_camp_users.exclude(user_role__access_level="Admin").exclude(is_superuser=True)
			user_list = final_camp_users.values("id", "username")
		context = {'request': request, 'campaign_list': campaign_list}
		all_fields = {"diallereventlog":['campaign_name','user','full_name','phonebook','uniqueid','customer_cid',
		'session_uuid','init_time','ring_time','connect_time','wait_time','ring_duration','hold_time',
		'callflow','callmode','dialed_status','hangup_cause','hangup_cause_code','bill_sec','call_duration','hangup_time']}
		context['users'] = list(user_list)
		context['can_qc_update']=can_qc_update
		context['all_fields'] = all_fields
		camp_name, active_camp, noti_count = get_active_campaign(request)
		context["noti_count"] = noti_count
		context['report_visible_cols'] = report_visible_cols
		context = {**context, **kwargs['permissions']}
		return Response(context)

	def post(self,request):
		admin = False
		if request.user.user_role and request.user.user_role.access_level == 'Admin':
			admin = True
		all_campaigns = request.POST.getlist("all_campaigns[]", []) if 'all_campaigns[]' in request.POST else request.POST.get("all_campaigns", "").split(',')
		all_users = request.POST.getlist("all_users[]", []) if 'all_users[]' in request.POST else request.POST.get("all_users", "").split(',')
		customer_cid = request.POST.get("customer_cid","") 
		selected_campaign = request.POST.getlist("selected_campaign[]", []) if 'selected_campaign[]' in request.POST else request.POST.getlist("selected_campaign", [])
		selected_user = request.POST.getlist("selected_user[]", []) if 'selected_user[]' in request.POST else request.POST.getlist("selected_user",[])
		unique_id = request.POST.get("unique_id","") 
		filters = {}
		download_report = request.POST.get("agent_reports_download", "")
		if download_report:
			col_name = request.POST.get("column_name", "")
			col_list = col_name.split(",")
			filters = request.POST.dict()
			filters['all_campaigns'] = all_campaigns
			filters['all_users'] = all_users
			filters['selected_campaign'] = selected_campaign
			filters['selected_user'] = selected_user
			filters['unique_id'] = unique_id
			filters['selected_records'] = request.POST.get("selected_records",'').split(',')
			DownloadReports.objects.create(report='Call Recordings',filters=filters, user=request.user.id, serializers=self.serializer_class, col_list=col_list, status=True)
			return JsonResponse({"message":"Your Download request is created, will notify in download notification once completed."})
		
		if selected_user:
			if selected_user[0]=='':
				selected_user = []
		if selected_campaign:
			if selected_campaign[0]=='':
				selected_campaign = []
		start_date = request.POST.get("start_date", "")
		end_date = request.POST.get("end_date", "")
		start_duration = request.POST.get("start_duration","")
		end_duration = request.POST.get("end_duration","")
		order_col = request.POST.get('order_col','')
		order_by = request.POST.get('order_by','desc')
		if start_date:
			queryset = DiallerEventLog.objects.filter(created__gte=start_date,dialed_status='Connected').select_related("campaign", "user")
			if end_date:
				queryset = queryset.filter(created__lte=end_date)
		else:
			queryset = DiallerEventLog.objects.filter(dialed_status='Connected').select_related("campaign", "user")
		if start_duration and end_duration:
			queryset = queryset.filter(call_duration__range=(start_duration,end_duration))
		elif start_duration:
			queryset = queryset.filter(call_duration__gte=start_duration)
		elif end_duration:
			queryset = queryset.filter(call_duration__lte=end_duration)
		# queryset = 
		queryset =  queryset.filter(Q(campaign_name__in=list(all_campaigns),
				user__id__in=list(all_users))|Q(user__id__in=list(all_users))| 
				Q(campaign_name__in=list(all_campaigns) ,user=None)|Q(campaign=None)|Q(user=None))
		page = int(request.POST.get('page' ,1))
		paginate_by = int(request.POST.get('paginate_by', 10))
		id_list = []
		if queryset:
			id_list = list(queryset.values_list("id", flat=True))
			if customer_cid:
				queryset = queryset.filter(customer_cid=customer_cid)
			if selected_campaign:
				if not (request.user.is_superuser or admin):
					get_camp_users = list(get_campaign_users(selected_campaign, 
					request.user).values_list("id",flat=True))
					queryset = queryset.filter(Q(campaign_name__in = selected_campaign), 
						Q(user__in=get_camp_users)|Q(user=None))
				else:
					queryset = queryset.filter(campaign_name__in = selected_campaign)
			if selected_user:
				queryset = queryset.filter(user__id__in=selected_user)
			if unique_id:
				queryset = queryset.filter(uniqueid=unique_id)
		if order_col:
			if order_by == 'asc':
				queryset = queryset.order_by(order_col)
			else:
				queryset = queryset.order_by('-'+order_col)
		queryset = get_paginated_object(queryset, page, paginate_by)
		result = DiallerEventLogSerializer(queryset, many=True).data
		return JsonResponse({'total_records': queryset.paginator.count, 'total_pages': queryset.paginator.num_pages, 
			'page': queryset.number, 'has_next': queryset.has_next(), 'has_prev': queryset.has_previous(),
			'start_index':queryset.start_index(), 'end_index':queryset.end_index(),
			'table_data':result})

class CallRecordingDetailView(LoginRequiredMixin, APIView):
	"""
	This View is used to show call detail with recordings
	"""
	def get(self, request, pk=None, **kwargs):
		dialler_obj = DiallerEventLog.objects.filter(pk=pk)
		if dialler_obj.exists():
			dialler_event_data = dialler_obj.values("customer_cid","user__username","campaign_name","call_duration","session_uuid").first()
			dialler_obj = dialler_obj.first()
			cdr_feedback = CdrFeedbck.objects.get(session_uuid=dialler_obj.session_uuid)
			dialler_event_data["primary_dispo"] = cdr_feedback.primary_dispo
			# dialler_event_data["feedback"] = cdr_feedback.feedback
			dialler_event_data["comment"] = cdr_feedback.comment
			dialler_event_data['calldetail_id'] = CallDetail.objects.get(session_uuid=dialler_obj.session_uuid).id
			user = User.objects.filter(username=dialler_obj.user.username)
			dialler_event_data["supervisor"] = ""
			if user.exists() and user.first().reporting_to:
				dialler_event_data["supervisor"]=user.first().reporting_to.username
			reco_feedback = CallRecordingFeedback.objects.filter(calldetail__session_uuid=dialler_obj.session_uuid)
			dialler_event_data["prev_feedback"] = ""
			if reco_feedback.exists():
				dialler_event_data["prev_feedback"] = reco_feedback.first().feedback
		return JsonResponse({"dialler_event_data":dialler_event_data})

	def post(self,request,pk=None):
		calldetail = CallDetail.objects.get(session_uuid=request.POST["session_uuid"]).id
		if CallRecordingFeedback.objects.filter(user=request.user, calldetail_id=calldetail).exists():
			CallRecordingFeedback.objects.filter(user=request.user, calldetail_id=calldetail).update(feedback=request.POST["feedback"])
		else:
			CallRecordingFeedback.objects.create(user_id=request.user.id,feedback=request.POST["feedback"], calldetail_id=calldetail)
		return Response({"msg":"feedback saved successfully"}, status=200)

@method_decorator(check_read_permission, name='get')
class PendingCallbackCallView(LoginRequiredMixin, generics.ListAPIView):
	"""
	This View is used to show call detail with recordings
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer,DatatablesRenderer]
	template_name = "reports/pending_callback_call.html"
	permissions = {"Dashboard": ["all"]}

	def get(self, request, *args, **kwargs):
		context = {}
		user_list = campaign_list =[]
		admin = False
		report_visible_cols = get_report_visible_column("8",request.user)
		if request.user.user_role and request.user.user_role.access_level == 'Admin':
			admin = True
		if request.user.is_superuser or admin:
			campaign_list = Campaign.objects.all().distinct().values("id", "name")
			user_list = User.objects.all().exclude(
				user_role__access_level="Admin").exclude(is_superuser=True).values("id", "username")
		else:
			camp = Campaign.objects.filter(Q(users=request.user, users__isnull=False)|
				Q( group__in=request.user.group.all(), group__isnull=False)).distinct()
			campaign_list = camp.values("id", "name")
			c_user  = c_group = []
			for campaign in camp:
				c_user.extend(list(campaign.users.all().values_list("id", flat=True)))
				c_group.extend(list(campaign.group.all().values_list("id", flat=True)))
			temp_id = c_user + c_group
			c_group_user = User.objects.filter(group__id__in=c_group)
			c_users = User.objects.filter(id__in=c_user)
			total_camp_users = c_group_user | c_users
			#reporting users
			users = User.objects.filter(reporting_to = request.user)
			if request.user.user_role.access_level == 'Manager':
				supervisors = users.exclude(user_role__access_level="Agent")
				team = User.objects.filter(reporting_to__in = supervisors)
				users = users | team
			final_camp_users = total_camp_users | users
			final_camp_users = final_camp_users.exclude(user_role__access_level="Admin").exclude(is_superuser=True)
			user_list = final_camp_users.values("id", "username")
		context["campaign_list"] =campaign_list
		context['all_fields'] =  ('campaign', 'phonebook', 'user','full_name','numeric', 'status', 'callback_title',
			'callback_type', 'schedule_date', 'disposition', 'comment')
		context["user_list"] = user_list
		context['report_visible_cols'] = report_visible_cols
		context = {**context, **kwargs['permissions']}
		return Response(context)

	def post(self,request):
		context = {}
		download_report = request.POST.get("agent_reports_download", "")
		if download_report:
			context = {}
			col_name = request.POST.get("column_name", "")
			col_list = col_name.split(",")
			filters = request.POST.dict()
			filters['selected_campaign'] = request.POST.getlist("selected_campaign", [])
			filters['selected_user'] = request.POST.getlist("selected_user", [])
			filters['download_type'] = request.POST.get("agent_reports_download_type",'csv')
			DownloadReports.objects.create(report='CallBack', filters=filters, user=request.user.id, serializers=None, col_list=col_list, status=True)
			return JsonResponse({"message":"Your Download request is created, will notify in download notification once completed."})
		admin = False
		if request.user.user_role and request.user.user_role.access_level == 'Admin':
			admin = True
		selected_user = request.POST.getlist("selected_user", [])
		selected_campaign = request.POST.get("selected_campaign", "")
		all_users = request.POST.get("all_users","")
		all_users = all_users.split(',')
		start_date = request.POST.get("start_date", "")
		end_date = request.POST.get("end_date", "")
		start_date = datetime.strptime(start_date,"%Y-%m-%d %H:%M").isoformat()
		end_date = datetime.strptime(end_date,"%Y-%m-%d %H:%M").isoformat()
		queryset = CurrentCallBack.objects.filter(schedule_time__gte=start_date, schedule_time__lte=end_date).order_by("-id")
		if selected_campaign:
			camp = Campaign.objects.filter(name=selected_campaign)[0]
			threshold = camp.callback_threshold
			queryset = queryset.filter(schedule_time__date__lte=date.today()-timedelta(days=threshold), campaign=camp.name)
		if selected_user:
			username = User.objects.filter(id__in=selected_user).values_list("username", flat=True)
			queryset = queryset.filter(user__in=list(username))
		page = int(request.POST.get('page' ,1))
		paginate_by = int(request.POST.get('paginate_by', 10))
		queryset = get_paginated_object(queryset, page, paginate_by)
		result = CurrentCallBackSerializer(queryset,many=True).data
		return JsonResponse({'total_records': queryset.paginator.count, 'total_pages': queryset.paginator.num_pages, 
			'page': queryset.number, 'has_next': queryset.has_next(), 'has_prev': queryset.has_previous(),
			'start_index':queryset.start_index(), 'end_index':queryset.end_index(),
			'table_data':result})

@method_decorator(check_read_permission, name='get')
class PendingAbandonedCallView(LoginRequiredMixin, generics.ListAPIView):
	"""
	This View is used to show call detail with recordings
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer,DatatablesRenderer]
	template_name = "reports/pending_abandoned_call.html"
	permissions = {"Dashboard": ["all"]}

	def get(self, request, *args, **kwargs):
		context = {}
		user_list = campaign_list =[]
		admin = False
		report_visible_cols = get_report_visible_column("9",request.user)
		if request.user.user_role and request.user.user_role.access_level == 'Admin':
			admin = True
		if request.user.is_superuser or admin:
			campaign_list = Campaign.objects.all().distinct().values("id", "name")
			user_list = User.objects.all().exclude(user_role__access_level="Admin").exclude(is_superuser=True).exclude(properties__extension=None).values("username",extension=F('properties__extension'))
		else:
			camp = Campaign.objects.filter(Q(users=request.user, users__isnull=False)|
				Q( group__in=request.user.group.all(), group__isnull=False)).distinct()
			campaign_list = camp.values("id", "name")
			c_user  = c_group = []
			for campaign in camp:
				c_user.extend(list(campaign.users.all().values_list("id", flat=True)))
				c_group.extend(list(campaign.group.all().values_list("id", flat=True)))
			temp_id = c_user + c_group
			c_group_user = User.objects.filter(group__id__in=c_group)
			c_users = User.objects.filter(id__in=c_user)
			total_camp_users = c_group_user | c_users
			#reporting users
			users = User.objects.filter(reporting_to = request.user)
			if request.user.user_role.access_level == 'Manager':
				supervisors = users.exclude(user_role__access_level="Agent")
				team = User.objects.filter(reporting_to__in = supervisors)
				users = users | team
			final_camp_users = total_camp_users | users
			final_camp_users = final_camp_users.exclude(user_role__access_level="Admin").exclude(is_superuser=True)
			user_list = final_camp_users.values("username",extension=F('properties__extension'))
		context["campaign_list"] =campaign_list
		context['all_fields'] =  ('campaign', 'username','full_name','numeric', 'call_date', 'status',)
		context["user_list"] = user_list
		context['report_visible_cols'] = report_visible_cols
		context = {**context, **kwargs['permissions']}
		return Response(context)

	def post(self,request):
		context = {}
		admin = False
		download_report = request.POST.get("agent_reports_download", "")
		if download_report:
			context = {}
			col_name = request.POST.get("column_name", "")
			col_list = col_name.split(",")
			filters = request.POST.dict()
			filters['selected_campaign'] = request.POST.getlist("selected_campaign", [])
			filters['selected_user'] = request.POST.getlist("selected_user", [])
			filters['download_type'] = request.POST.get("agent_reports_download_type",'csv')
			DownloadReports.objects.create(report='Abandoned Call',filters=filters, user=request.user.id, serializers=None, col_list=col_list, status=True)
			return JsonResponse({"message":"Your Download request is created, will notify in download notification once completed."})

		if request.user.user_role and request.user.user_role.access_level == 'Admin':
			admin = True
		selected_user = request.POST.getlist("selected_user", [])
		if "''" in selected_user:
			selected_user.remove("")
		selected_campaign = request.POST.get("selected_campaign", "")
		all_users = request.POST.get("all_users","")
		all_users = all_users.split(',')
		start_date = request.POST.get("start_date", "")
		end_date = request.POST.get("end_date", "")
		start_date = datetime.strptime(start_date,"%Y-%m-%d %H:%M").isoformat()
		end_date = datetime.strptime(end_date,"%Y-%m-%d %H:%M").isoformat()
		queryset = Abandonedcall.objects.filter(created_date__gte=start_date, created_date__lte=end_date)
		if selected_campaign:
			camp = Campaign.objects.filter(name=selected_campaign)[0]
			threshold = camp.inbound_threshold
			queryset = queryset.filter(created_date__date__lte=date.today()-timedelta(days=threshold), campaign=camp.name)
		if selected_user:
			queryset = queryset.filter(user__in=selected_user)
		page = int(request.POST.get('page' ,1))
		paginate_by = int(request.POST.get('paginate_by', 10))
		queryset = get_paginated_object(queryset, page, paginate_by)
		result = AbandonedcallSerializer(queryset,many=True).data
		return JsonResponse({'total_records': queryset.paginator.count, 'total_pages': queryset.paginator.num_pages,
			'page': queryset.number, 'has_next': queryset.has_next(), 'has_prev': queryset.has_previous(),
			'start_index':queryset.start_index(), 'end_index':queryset.end_index(), 'table_data':result})


@method_decorator(check_read_permission, name='get')
class CallRecordingFeedbackView(LoginRequiredMixin, generics.ListAPIView):
	"""
	This View is used to show call detail with recordings
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer,DatatablesRenderer]
	template_name = "reports/call_recording_feedback.html"
	permissions = {"Dashboard": ["all"]}

	def get(self, request, *args, **kwargs):
		context = {}
		user_list = campaign_list =[]
		admin = False
		if request.user.user_role and request.user.user_role.access_level == 'Admin':
			admin = True
		if request.user.is_superuser or admin:
			user_list = list(User.objects.all().exclude(user_role__access_level='Agent').values("id", "username"))
			context["user_list"] = user_list
			agent_list = User.objects.all().exclude(
				user_role__access_level="Admin").exclude(is_superuser=True).values("id", "username")
		else:
			camp = Campaign.objects.filter(Q(users=request.user, users__isnull=False)|
				Q( group__in=request.user.group.all(), group__isnull=False)).distinct()
			c_user  = c_group = []
			for campaign in camp:
				c_user.extend(list(campaign.users.all().values_list("id", flat=True)))
				c_group.extend(list(campaign.group.all().values_list("id", flat=True)))
			temp_id = c_user + c_group
			c_group_user = User.objects.filter(group__id__in=c_group)
			c_users = User.objects.filter(id__in=c_user)
			total_camp_users = c_group_user | c_users
			#reporting users
			users = User.objects.filter(reporting_to = request.user)
			if request.user.user_role.access_level == 'Manager':
				supervisors = users.exclude(user_role__access_level="Agent")
				team = User.objects.filter(reporting_to__in = supervisors)
				users = users | team
			final_camp_users = total_camp_users | users
			final_camp_users = final_camp_users.exclude(user_role__access_level="Admin").exclude(is_superuser=True)
			agent_list = final_camp_users.values("id", "username")
			context["user_list"] = final_camp_users.exclude(user_role__access_level="Agent").values("id", "username")
		context["agent_list"] = agent_list
		report_visible_cols = get_report_visible_column("13",request.user)
		context['all_fields'] =  ('agent','cli','session_uuid','primary_dispo','uniqueid','feedback','submitted_by')
		context['report_visible_cols'] = report_visible_cols
		context = {**context, **kwargs['permissions']}
		return Response(context)

	def post(self,request):
		context = {}
		admin = False
		download_report = request.POST.get("agent_reports_download", "")
		if download_report:
			context = {}
			col_name = request.POST.get("column_name", "")
			col_list = col_name.split(",")
			filters = request.POST.dict()
			filters['selected_user'] = request.POST.getlist("selected_user", [])
			filters['selected_agent'] = request.POST.getlist("selected_agent", [])
			filters['download_type'] = request.POST.get("agent_reports_download_type",'csv')
			DownloadReports.objects.create(report='call recording feedback',filters=filters, user=request.user.id, serializers=None, col_list=col_list, status=True)
			return JsonResponse({"message":"Your Download request is created, will notify in download notification once completed."})

		if request.user.user_role and request.user.user_role.access_level == 'Admin':
			admin = True
		selected_user = request.POST.getlist("selected_user", [])
		if "''" in selected_user:
			selected_user.remove("")
		selected_agent = request.POST.getlist("selected_agent", [])
		if "''" in selected_agent:
			selected_agent.remove("")
		all_users = request.POST.get("all_users","")
		if all_users:
			all_users = all_users.split(',')
		else:
			all_users = []
		customer_cid = request.POST.get("cli","")
		start_date = request.POST.get("start_date", "")
		end_date = request.POST.get("end_date", "")
		start_date = datetime.strptime(start_date,"%Y-%m-%d %H:%M").isoformat()
		end_date = datetime.strptime(end_date,"%Y-%m-%d %H:%M").isoformat()
		queryset = CallRecordingFeedback.objects.filter(created__gte=start_date, created__lte=end_date, user_id__in=all_users)
		if selected_user:
			username = User.objects.filter(id__in=selected_user).values_list("username", flat=True)
			queryset = queryset.filter(user__username__in=username)
		if selected_agent:
			username = User.objects.filter(id__in=selected_agent).values_list("username", flat=True)
			queryset = queryset.filter(calldetail__user__username__in=username)
		if customer_cid:
			queryset = queryset.filter(calldetail__customer_cid=customer_cid)
		page = int(request.POST.get('page' ,1))
		paginate_by = int(request.POST.get('paginate_by', 10))
		queryset = get_paginated_object(queryset, page, paginate_by)

		result = CallRecordingFeedbackSerializer(queryset,many=True).data
		
		return JsonResponse({'total_records': queryset.paginator.count, 'total_pages': queryset.paginator.num_pages,
			'page': queryset.number, 'has_next': queryset.has_next(), 'has_prev': queryset.has_previous(),
			'start_index':queryset.start_index(), 'end_index':queryset.end_index(), 'table_data':result})
	
def get_current_balance(contact_id):
	""" Thsi method to get the crm field current balance in customer info section """
	contact_info = ContactInfo.objects.filter(contact__id__in=list(contact_id))
	current_bal = 0
	for info in contact_info:
		if "Customer Info" in info.customer_raw_data and "CURR_BAL" in info.customer_raw_data["Customer Info"]:
			temp_bal = info.customer_raw_data["Customer Info"].get("CURR_BAL", 0)
			if not temp_bal:
				temp_bal = 0
			current_bal = current_bal + int(temp_bal)
	return current_bal

@method_decorator(check_read_permission, name='get')
class AgentActivityReportView(LoginRequiredMixin, ListAPIView):
	"""
	This View is used to show agent
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer,DatatablesRenderer]
	template_name = "reports/agent-activity-report.html"
	permissions = {"Dashboard": ["all"]}
	serializer_class = AgentActivityReportSerializer
	paginator = DatatablesPageNumberPagination

	def get(self, request, *args, **kwargs):
		context = {}
		agent_activity = []
		user_list = campaign_list = user_id = camp_name = []
		admin = False
		report_visible_cols = get_report_visible_column("5",request.user)
		if request.user.user_role and request.user.user_role.access_level == 'Admin':
			admin = True
		if request.user.is_superuser or admin:
			campaign_list = Campaign.objects.all().distinct().values("id", "name")
			user_list = User.objects.all().values("id", "username")
			disposition = Disposition.objects.all().values("id", "name")
		else:
			camp = Campaign.objects.filter(Q(users=request.user, users__isnull=False)|
				Q( group__in=request.user.group.all(), group__isnull=False)).distinct()
			campaign_list = camp.values("id", "name")

			c_user  = c_group = []
			for campaign in camp:
				c_user.extend(list(campaign.users.all().values_list("id", flat=True)))
				c_group.extend(list(campaign.group.all().values_list("id", flat=True)))
			temp_id = c_user + c_group
			c_group_user = User.objects.filter(group__id__in=c_group)
			c_users = User.objects.filter(id__in=c_user)
			total_camp_users = c_group_user | c_users
			#reporting users
			users = User.objects.filter(reporting_to = request.user)
			if request.user.user_role.access_level == 'Manager':
				team = User.objects.filter(reporting_to__in = users)
				users = users | team
			final_camp_users = total_camp_users | users
			final_camp_users = final_camp_users.exclude(user_role__access_level="Admin").exclude(is_superuser=True)
			user_list = final_camp_users.values("id", "username")
			user_id = final_camp_users.values_list("id", flat=True)
			camp_name = camp.values_list("name", flat=True)
		context["campaign_list"] =campaign_list
		context["all_fields"] = ['user','full_name','event','event_time','tos','app_time','campaign_name','dialer_time','idle_time',
		'media_time','hold_time','spoke_time','preview_time','progressive_time','pause_progressive_time',
		'predictive_time','predictive_wait_time','inbound_time','inbound_wait_time','blended_time',
		'blended_wait_time','transfer_time','feedback_time','break_type','break_time']
		context["user_list"] = list(user_list)
		context['report_visible_cols'] = report_visible_cols
		context = {**context, **kwargs['permissions']}
		return Response(context)

	def post(self,request):
		download_report = request.POST.get("agent_reports_download", "")
		if download_report:
			context = {}
			col_name = request.POST.get("column_name", "")
			col_list = col_name.split(",")
			filters = request.POST.dict()
			filters['all_users'] = request.POST.get("all_users", "").split(',')
			filters['selected_campaign'] = request.POST.getlist("selected_campaign", [])
			filters['selected_user'] = request.POST.getlist("selected_user", [])
			filters['all_campaigns'] = request.POST.get("all_campaigns", "").split(',')
			filters['download_type'] = request.POST.get("agent_reports_download_type",'csv')
			#DownloadReports.objects.create(report='Agent Activity', filters=filters, user=request.user.id, serializers=None, col_list=col_list, status=True)
			return JsonResponse({"message":"Your Download request is created, will notify in download notification once completed."})

		paginator = self.paginator()
		admin = False
		if request.user.user_role and request.user.user_role.access_level == 'Admin':
			admin = True
		all_campaigns = request.POST.getlist("all_campaigns[]", [])
		all_users = request.POST.getlist("all_users[]", [])
		selected_campaign = request.POST.getlist("selected_campaign[]", [])
		selected_user = request.POST.getlist("selected_user[]", [])
		start_date = request.POST.get("start_date", "")
		end_date = request.POST.get("end_date", "")
		start_date = datetime.strptime(start_date,"%Y-%m-%d %H:%M").isoformat()
		end_date = datetime.strptime(end_date,"%Y-%m-%d %H:%M").isoformat()
		start_end_date_filter = Q(created__gte=start_date)&Q(created__lte=end_date)
		queryset = AgentActivity.objects.filter(start_end_date_filter).select_related("user")
		queryset = queryset.filter(Q(campaign_name__in=list(all_campaigns),
				user__id__in=list(all_users))|Q(user__id__in=list(all_users))|
				Q(campaign_name__in=list(all_campaigns)))
		if request.POST.get('format', None) == 'datatables':
			paginator.is_datatable_request = True
		else:
			paginator.is_datatable_request = False
		
		if selected_campaign:
			if not (request.user.is_superuser or admin):
				get_camp_users = list(get_campaign_users(selected_campaign,
					request.user).values_list("id",flat=True))
				queryset = queryset.filter(Q(campaign_name__in = selected_campaign),
					Q(user__in=get_camp_users)|Q(user=None))
			else:
				queryset = queryset.filter(campaign_name__in = selected_campaign)
		if selected_user:
			queryset = queryset.filter(user__id__in=selected_user)
		page = paginate_queryset(request, queryset, paginator)
		if page is not None:
			serializer = self.serializer_class(page, many=True)
			return get_paginated_response(serializer.data, paginator)
		serializer = self.serializer_class(queryset, many=True)
		return Response(serializer.data)

@method_decorator(check_read_permission, name='get')
class AgentPerformanceReportView(LoginRequiredMixin,APIView):
	"""
	This View is used to show agent
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer,]
	template_name = "reports/agent-performance.html"
	permissions = {"Dashboard": ["all"]}

	def get(self, request, *args, **kwargs):
		context = {}
		user_list = campaign_list =[]
		admin = False
		report_visible_cols = get_report_visible_column("3",request.user)		
		if request.user.user_role and request.user.user_role.access_level == 'Admin':
			admin = True
		if request.user.is_superuser or admin:
			campaign_list = Campaign.objects.all().distinct().values("id", "name")
			user_list = User.objects.all().exclude(
					user_role__access_level="Admin").exclude(is_superuser=True).values("id", "username")
		else:
			camp = Campaign.objects.filter(Q(users=request.user, users__isnull=False)|
					Q( group__in=request.user.group.all(), group__isnull=False)).distinct()
			campaign_list = camp.values("id", "name")
			c_user  = c_group = []
			for campaign in camp:
				c_user.extend(list(campaign.users.all().values_list("id", flat=True)))
				c_group.extend(list(campaign.group.all().values_list("id", flat=True)))
			temp_id = c_user + c_group
			c_group_user = User.objects.filter(group__id__in=c_group)
			c_users = User.objects.filter(id__in=c_user)
			total_camp_users = c_group_user | c_users
			#reporting users
			users = User.objects.filter(reporting_to = request.user)
			if request.user.user_role.access_level == 'Manager':
				supervisors = users.exclude(user_role__access_level="Agent")
				team = User.objects.filter(reporting_to__in = supervisors)
				users = users | team
			final_camp_users = total_camp_users | users
			final_camp_users = final_camp_users.exclude(user_role__access_level="Admin").exclude(is_superuser=True)
			user_list = final_camp_users.values("id", "username")
		pause_breaks = tuple(PauseBreak.objects.values_list('name',flat=True))
		context["report_visible_cols"] = report_visible_cols
		context["campaign_list"] = campaign_list
		context['all_fields'] =  ('username','full_name','supervisor_name','campaign','app_idle_time','dialer_idle_time','pause_progressive_time','progressive_time','preview_time',
				'predictive_wait_time','inbound_wait_time','blended_wait_time','ring_duration','ring_duration_avg','hold_time','media_time','predictive_wait_time_avg','talk','talk_avg','bill_sec','bill_sec_avg','call_duration','feedback_time','feedback_time_avg','break_time','break_time_avg','app_login_time'
				) + pause_breaks + ('dialer_login_time','total_login_time','first_login_time','last_logout_time','total_calls','total_unique_connected_calls')
		context["user_list"] = list(user_list)
		# context["user_list"] = user_in_hirarchy_level(request.user.id)
		context = {**context, **kwargs['permissions']}
		return Response(context)
	
	def post(self, request, *args, **kwargs):
		context = {}
		call_result= []
		row = []
		writer = {}
		admin = False
		download_report = request.POST.get("agent_reports_download", "")
		start_date = request.POST.get("start_date", "")
		start_date = start_date[:10]
		end_date = request.POST.get("end_date", "")
		end_date = end_date[:10]
		filters = request.POST.dict()
		filters['all_users'] = request.POST.get("all_users", "").split(',')
		filters['selected_campaign'] = request.POST.getlist("selected_campaign", [])
		filters['selected_user'] = request.POST.getlist("selected_user", [])
		if download_report:
			context = {}
			col_name = request.POST.get("column_name", "")
			col_list = col_name.split(",")
			filters['download_type'] = request.POST.get("agent_reports_download_type",'csv')
			DownloadReports.objects.create(report='Agent Performance', filters=filters, user=request.user.id, serializers=None, col_list=col_list, status=True)
			return JsonResponse({"message":"Your Download request is created, will notify in download notification once completed."})

		if request.user.user_role and request.user.user_role.access_level == 'Admin':
			admin = True
		selected_user = request.POST.getlist("selected_user", [])
		selected_campaign = request.POST.getlist("selected_campaign", [])
		all_users = request.POST.get("all_users",[])
		all_users = all_users.split(',')
		filters['paginate_by'] = int(request.POST.get('paginate_by', 10))
		filters['page'] = int(request.POST.get('page', 10))
		filters['start_date_ui'] = start_date
		filters['end_date_ui'] = end_date
		
		call_result,users =action_agent_performance_report(filters)
		return JsonResponse({'total_records': users.paginator.count,
						'total_pages': users.paginator.num_pages,
						'page': users.number,'start_index':users.start_index(), 'end_index':users.end_index(),
						'has_next': users.has_next(),
						'has_prev': users.has_previous(),'table_data':call_result})

	# def old_post(self, request, *args, **kwargs):
	# 	context = {}
	# 	call_result= []
	# 	row = []
	# 	writer = {}
	# 	admin = False
	# 	download_report = request.POST.get("agent_reports_download", "")
	# 	start_date = request.POST.get("start_date", "")
	# 	start_date = start_date[:10]				
	# 	if download_report:
	# 		context = {}
	# 		col_name = request.POST.get("column_name", "")
	# 		col_list = col_name.split(",")
	# 		filters = request.POST.dict()
	# 		filters['all_users'] = request.POST.get("all_users", "").split(',')
	# 		filters['selected_campaign'] = request.POST.getlist("selected_campaign", [])
	# 		filters['selected_user'] = request.POST.getlist("selected_user", [])
	# 		filters['download_type'] = request.POST.get("agent_reports_download_type",'csv')
	# 		DownloadReports.objects.create(report='Agent Performance', filters=filters, user=request.user.id, serializers=None, col_list=col_list, status=True)
	# 		return JsonResponse({"message":"Your Download request is created, will notify in download notification once completed."})
	# 	if start_date != str(date.today()):
	# 		data = agentactivity_data(start_date,request)
	# 		return JsonResponse(data)

	# 	if request.user.user_role and request.user.user_role.access_level == 'Admin':
	# 		admin = True
	# 	selected_user = request.POST.getlist("selected_user", [])
	# 	selected_campaign = request.POST.getlist("selected_campaign", [])
	# 	all_users = request.POST.get("all_users",[])
	# 	all_users = all_users.split(',')
	# 	# users_agentactivity = list(AgentActivity.objects.filter(created__date=date.today()).order_by().distinct("user").values_list("user",flat=True))
	# 	queryset = User.objects.filter(last_login__date=start_date)
	# 	if selected_user:
	# 		# required_users = list(set(user_hierarchy_func(request.user.id,selected_user) + users_agentactivity))
	# 		queryset = queryset.filter(id__in=selected_user)
	# 	queryset = queryset.order_by("username")
	# 	page = int(request.POST.get('page' ,1))
	# 	paginate_by = int(request.POST.get('paginate_by', 10))
	# 	users = get_paginated_object(queryset, page, paginate_by)
	# 	start_end_date_filter = Q(created__date=start_date)
	# 	app_idle_time_filter = Q(campaign_name='')|Q(event='DIALER LOGIN')
	# 	dialler_idle_time_filter = ~Q(campaign_name="")&~Q(event__in=["DIALER LOGIN","LOGOUT"])
	# 	default_time = timedelta(seconds=0)

	# 	for user in users:
	# 		user = queryset.filter(id=user.id).prefetch_related(Prefetch('calldetail_set',queryset=CallDetail.objects.filter(start_end_date_filter).filter(user=user)),Prefetch('agentactivity_set',queryset=AgentActivity.objects.filter(start_end_date_filter).filter(user=user))).first()
	# 		if selected_campaign:
	# 			calldetail = user.calldetail_set.filter(campaign_name__in=selected_campaign)
	# 			agentactivity = user.agentactivity_set.filter(Q(campaign_name__in=selected_campaign)|Q(
	# 					event="DIALER LOGIN")|Q(campaign_name=''))
	# 		else:
	# 			calldetail = user.calldetail_set
	# 			agentactivity = user.agentactivity_set
	# 		calldetail_cal = calldetail.aggregate(media_time=Cast(Coalesce(Sum('media_time'),default_time),TextField()),
	# 				ring_duration=Cast(Coalesce(Sum('ring_duration'),default_time),TextField()),
	# 				hold_time=Cast(Coalesce(Sum('hold_time'),default_time),TextField()),
	# 				call_duration=Cast(Coalesce(Sum('call_duration'),default_time),TextField()),
	# 				bill_sec=Cast(Coalesce(Sum('bill_sec'),default_time),TextField()),
	# 				feedback_time=Cast(Coalesce(Sum('feedback_time'),default_time),TextField()),
	# 				)
	# 		activity_cal = agentactivity.aggregate(break_time=Cast(Coalesce(Sum('break_time'),default_time),TextField()),
	# 				pause_progressive_time=Cast(Coalesce(Sum('pause_progressive_time'),default_time),TextField()),
	# 				predictive_time=Cast(Coalesce(Sum('predictive_time'),default_time),TextField()),
	# 				progressive_time=Cast(Coalesce(Sum('progressive_time'),default_time),TextField()),
	# 				preview_time=Cast(Coalesce(Sum('preview_time'),default_time),TextField()),
	# 				predictive_wait_time=Cast(Coalesce(Sum('predictive_wait_time'),default_time),TextField()),
	# 				inbound_time=Cast(Coalesce(Sum('inbound_time'),default_time),TextField()),
	# 				blended_time=Cast(Coalesce(Sum('blended_time'),default_time),TextField()),
	# 				inbound_wait_time=Cast(Coalesce(Sum('inbound_wait_time'),default_time),TextField()),
	# 				blended_wait_time=Cast(Coalesce(Sum('blended_wait_time'),default_time),TextField()),
	# 				app_idle_time=Cast(Coalesce(Sum('idle_time',filter=app_idle_time_filter),default_time),TextField()),
	# 				dialer_idle_time=Cast(Coalesce(Sum('idle_time',filter=dialler_idle_time_filter),default_time),TextField())
	# 				)
	# 		break_time_cal= {}
	# 		total_calls = calldetail.count()
	# 		break_name = list(PauseBreak.objects.values_list('name',flat=True))
	# 		for break_cal in break_name:
	# 			break_time_cal[break_cal] = agentactivity.filter(break_type=break_cal).aggregate(break_time__sum=Cast(Coalesce(Sum('break_time'),default_time),TextField())).get('break_time__sum')
	# 		pp_time = convert_into_timedelta(activity_cal['pause_progressive_time']).total_seconds()
	# 		pw_time = convert_into_timedelta(activity_cal['predictive_wait_time']).total_seconds()
	# 		preview_time = convert_into_timedelta(activity_cal['preview_time']).total_seconds()
	# 		break_time = convert_into_timedelta(activity_cal['break_time']).total_seconds()
	# 		talk_call = convert_into_timedelta(calldetail_cal['bill_sec']).total_seconds()
	# 		ring_duration =convert_into_timedelta(calldetail_cal['ring_duration']).total_seconds()
	# 		feedback_time =convert_into_timedelta(calldetail_cal['feedback_time']).total_seconds()
	# 		talk_total = int(talk_call) + int(feedback_time) + int(ring_duration)
	# 		customer_talk = int(talk_call) + int(ring_duration)
	# 		calldetail_cal['talk'] = convert_timedelta_hrs(timedelta(seconds=talk_total))
	# 		calldetail_cal['bill_sec'] = convert_timedelta_hrs(timedelta(seconds=customer_talk)) 
	# 		if total_calls:
	# 			break_time_avg = ((convert_into_timedelta(activity_cal['break_time']).total_seconds())/total_calls)
	# 			talk_avg = ((int(talk_call)+int(feedback_time)+int(ring_duration))/total_calls)
	# 			feedback_time_avg = ((convert_into_timedelta(calldetail_cal['feedback_time']).total_seconds())/total_calls)
	# 			customer_avg_talk = ((int(talk_call)+int(ring_duration))/total_calls)
	# 			pw_wait_avg = (int(pw_time)/total_calls)
	# 			calldetail_cal['bill_sec_avg'] = convert_timedelta_hrs(timedelta(seconds=customer_avg_talk))
	# 			wait_avg = ((convert_into_timedelta(calldetail_cal['ring_duration']).total_seconds())/total_calls)
	# 			calldetail_cal['break_time_avg'] =  convert_timedelta_hrs(timedelta(seconds=break_time_avg))
	# 			calldetail_cal['talk_avg'] = convert_timedelta_hrs(timedelta(seconds=talk_avg)) 
	# 			calldetail_cal['feedback_time_avg'] =  convert_timedelta_hrs(timedelta(seconds=feedback_time_avg)) 
	# 			calldetail_cal['ring_duration_avg'] = convert_timedelta_hrs(timedelta(seconds=wait_avg)) 
	# 			activity_cal['predictive_wait_time_avg'] = convert_timedelta_hrs(timedelta(seconds=pw_wait_avg)) 
	# 		else:
	# 			default_time_delta_sec = timedelta(hours=0,minutes=0,seconds=0).total_seconds()
	# 			calldetail_cal['break_time_avg'] = time.strftime("%H:%M:%S", time.gmtime(default_time_delta_sec))
	# 			calldetail_cal['talk_avg'] = time.strftime("%H:%M:%S", time.gmtime(default_time_delta_sec))
	# 			calldetail_cal['feedback_time_avg'] = time.strftime("%H:%M:%S", time.gmtime(default_time_delta_sec))
	# 			calldetail_cal['bill_sec_avg'] = time.strftime("%H:%M:%S", time.gmtime(default_time_delta_sec))
	# 			calldetail_cal['ring_duration_avg'] = time.strftime("%H:%M:%S", time.gmtime(default_time_delta_sec))
	# 			activity_cal['predictive_wait_time_avg'] = time.strftime("%H:%M:%S", time.gmtime(default_time_delta_sec)) 
	# 		iw_time = convert_into_timedelta(activity_cal['inbound_wait_time']).total_seconds()
	# 		bw_time = convert_into_timedelta(activity_cal['blended_wait_time']).total_seconds()
	# 		ai_time = convert_into_timedelta(activity_cal['app_idle_time']).total_seconds()
	# 		di_time = convert_into_timedelta(activity_cal['dialer_idle_time']).total_seconds()
	# 		call_duration = convert_into_timedelta(calldetail_cal['call_duration']).total_seconds()
	# 		feedback_time = convert_into_timedelta(calldetail_cal['feedback_time']).total_seconds()
	# 		p_time = convert_into_timedelta(activity_cal['progressive_time']).total_seconds()
	# 		dialer_login_time = int(pp_time)+int(pw_time)+int(preview_time)+int(iw_time)+int(bw_time)+int(
	# 				di_time)+int(call_duration)+int(feedback_time)+int(p_time)
	# 		total_login_time = int(dialer_login_time)+int(ai_time)+int(break_time)
	# 		calldetail_cal['app_login_time'] = activity_cal['app_idle_time']
	# 		calldetail_cal['dialer_login_time'] = time.strftime("%H:%M:%S", time.gmtime(dialer_login_time))
	# 		calldetail_cal['total_login_time'] = time.strftime("%H:%M:%S", time.gmtime(total_login_time))
	# 		calldetail_cal = {**calldetail_cal, **activity_cal ,**break_time_cal}
	# 		calldetail_cal['total_calls'] = calldetail.count()
	# 		calldetail_cal['username'] = user.username
	# 		last_logout_time = ''
	# 		first_login_time = ''
	# 		if agentactivity.filter(event='LOGOUT').last():
	# 			last_logout_time = agentactivity.filter(event='LOGOUT').order_by('created').last().created.strftime("%Y-%m-%d %H:%M:%S")
	# 		if agentactivity.filter(event='LOGIN').first():
	# 			first_login_time = agentactivity.filter(event='LOGIN').order_by('created').first().created.strftime("%Y-%m-%d %H:%M:%S")
	# 		calldetail_cal['last_logout_time'] = last_logout_time
	# 		calldetail_cal['first_login_time'] = first_login_time
	# 		calldetail_cal['total_unique_connected_calls'] = calldetail.distinct('customer_cid').order_by('customer_cid').count()
	# 		if user.reporting_to:
	# 			calldetail_cal['supervisor_name'] = user.reporting_to.username
	# 		calldetail_cal['full_name'] = user.first_name+" "+user.last_name
	# 		camps = ",".join(list(set(list(user.agentactivity_set.exclude(campaign_name=None).exclude(campaign_name='').values_list("campaign_name",flat=True)))))
	# 		if selected_campaign:
	# 			calldetail_cal['campaign'] = [camp for camp in selected_campaign if camp in camps]
	# 		else:
	# 			calldetail_cal['campaign'] = camps
	# 		call_result.append(calldetail_cal)
	# 	return JsonResponse({'total_records': users.paginator.count,
	# 					'total_pages': users.paginator.num_pages,
	# 					'page': users.number,'start_index':users.start_index(), 'end_index':users.end_index(),
	# 					'has_next': users.has_next(),
	# 					'has_prev': users.has_previous(),'table_data':call_result[::-1]})


@method_decorator(check_read_permission, name='get')
class ManagementPerformanceReportView(LoginRequiredMixin,APIView):
	"""
	This View is used to show admin/manager/supervisor performance
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer,]
	template_name = "reports/management-performance-report.html"
	permissions = {"Dashboard": ["all"]}

	def get(self, request, *args, **kwargs):
		context = {}
		user_list = campaign_list =[]
		admin = False
		report_visible_cols = get_report_visible_column("15",request.user)
		if request.user.user_role and request.user.user_role.access_level == 'Admin':
			admin = True
		if request.user.is_superuser or admin:
			campaign_list = Campaign.objects.all().distinct().values("id", "name")
			user_list = User.objects.all().exclude(user_role__access_level='Agent').values("id", "username")
		else:
			camp = Campaign.objects.filter(Q(users=request.user, users__isnull=False)|
				Q( group__in=request.user.group.all(), group__isnull=False)).distinct()
			campaign_list = camp.values("id", "name")
			c_user  = c_group = []
			for campaign in camp:
				c_user.extend(list(campaign.users.all().values_list("id", flat=True)))
				c_group.extend(list(campaign.group.all().values_list("id", flat=True)))
			temp_id = c_user + c_group
			c_group_user = User.objects.filter(group__id__in=c_group)
			c_users = User.objects.filter(id__in=c_user)
			total_camp_users = c_group_user | c_users
			#reporting users
			users = User.objects.filter(reporting_to = request.user)
			if request.user.user_role.access_level == 'Manager':
				supervisors = users.exclude(user_role__access_level="Agent")
				team = User.objects.filter(reporting_to__in = supervisors)
				users = users | team
			final_camp_users = total_camp_users | users
			final_camp_users = final_camp_users.exclude(user_role__access_level="Agent").exclude(is_superuser=True)
			user_list = final_camp_users.values("id", "username")
		context["report_visible_cols"] = report_visible_cols
		context["campaign_list"] =campaign_list
		context['all_fields'] =  ('username','full_name','first_login_time','last_logout_time','login_duration')
		context["user_list"] = list(user_list)
		context = {**context, **kwargs['permissions']}
		return Response(context)

	def post(self, request, *args, **kwargs):
		context = {}
		log_result= []
		row = []
		writer = {}
		admin = False
		download_report = request.POST.get("management_reports_download", "")
		if download_report:
			context = {}
			col_name = request.POST.get("column_name", "")
			col_list = col_name.split(",")
			filters = request.POST.dict()
			filters['all_users'] = request.POST.get("all_users", "").split(',')
			filters['selected_user'] = request.POST.getlist("selected_user", [])
			filters['download_type'] = request.POST.get("agent_reports_download_type",'csv')
			DownloadReports.objects.create(report='Management Performance', filters=filters, user=request.user.id, serializers=None, col_list=col_list, status=True)
			return JsonResponse({"message":"Your Download request is created, will notify in download notification once completed."})

		if request.user.user_role and request.user.user_role.access_level == 'Admin':
			admin = True
		selected_user = request.POST.getlist("selected_user", [])
		selected_campaign = request.POST.getlist("selected_campaign", [])
		all_users = request.POST.get("all_users",[])
		all_users = all_users.split(',')
		if selected_user:
			queryset = User.objects.filter(id__in=selected_user)
		else:
			queryset = User.objects.filter(id__in=all_users)
		queryset = queryset.order_by("username")
		start_date = request.POST.get("start_date", "")
		end_date = request.POST.get("end_date", "")
		page = int(request.POST.get('page' ,1))
		paginate_by = int(request.POST.get('paginate_by', 10))
		users = get_paginated_object(queryset, page, paginate_by)
		start_date = datetime.strptime(start_date,"%Y-%m-%d %H:%M").isoformat()
		end_date = datetime.strptime(end_date,"%Y-%m-%d %H:%M").isoformat()
		start_end_date_filter = Q(created__gte=start_date)&Q(created__lte=end_date)
		default_time = timedelta(seconds=0)
		for index , user in enumerate(users,start=1):
			login_time = logout_time = ''
			# management_log_dict = {}
			user = User.objects.filter(id=user.id).prefetch_related(Prefetch('adminlogentry_set',queryset=AdminLogEntry.objects.filter(start_end_date_filter))).first()
			management_log = user.adminlogentry_set
			management_log_dict = management_log.aggregate(login_duration=Cast(Coalesce(Sum('login_duration'),default_time),TextField()),
				)
			management_log_dict['username'] = user.username
			login = management_log.filter(start_end_date_filter,event_type='LOGIN')
			logout = management_log.filter(start_end_date_filter,event_type='LOGOUT')
			if login.exists():
				login_time = login.first().created
			if logout.exists():
				logout_time = logout.last().created
			management_log_dict['first_login_time'] = login_time
			management_log_dict['last_logout_time'] = logout_time
			management_log_dict['login_duration'] = convert_into_timedelta(management_log_dict['login_duration']).total_seconds()
			management_log_dict['login_duration'] = time.strftime("%H:%M:%S", time.gmtime(management_log_dict['login_duration']))
			management_log_dict['full_name'] = user.first_name+" "+user.last_name
			log_result.append(management_log_dict)
		return JsonResponse({'total_records': users.paginator.count,
				'total_pages': users.paginator.num_pages,
				'page': users.number,'start_index':users.start_index(), 'end_index':users.end_index(),
				'has_next': users.has_next(),
				'has_prev': users.has_previous(),'table_data':log_result[::-1]})


@method_decorator(check_read_permission, name='get')
class CampainwisePerformanceReportView(LoginRequiredMixin,APIView):
	"""
	This View is used to show campaignwise performance report
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer,]
	template_name = "reports/campainwise-performance.html"
	permissions = {"Dashboard": ["all"]}

	def get(self, request, *args, **kwargs):
		context = {}
		user_list = campaign_list =[]
		admin = False
		report_visible_cols = get_report_visible_column("7",request.user)
		if request.user.user_role and request.user.user_role.access_level == 'Admin':
			admin = True
		if request.user.is_superuser or admin:
			campaign_list = Campaign.objects.all().distinct().values("id", "name")
			user_list = User.objects.all().exclude(
				user_role__access_level="Admin").exclude(is_superuser=True).values("id", "username")
		else:
			camp = Campaign.objects.filter(Q(users=request.user, users__isnull=False)|
				Q( group__in=request.user.group.all(), group__isnull=False)).distinct()
			campaign_list = camp.values("id", "name")
			c_user  = c_group = []
			for campaign in camp:
				c_user.extend(list(campaign.users.all().values_list("id", flat=True)))
				c_group.extend(list(campaign.group.all().values_list("id", flat=True)))
			temp_id = c_user + c_group
			c_group_user = User.objects.filter(group__id__in=c_group)
			c_users = User.objects.filter(id__in=c_user)
			total_camp_users = c_group_user | c_users
			#reporting users
			users = User.objects.filter(reporting_to = request.user)
			if request.user.user_role.access_level == 'Manager':
				supervisors = users.exclude(user_role__access_level="Agent")
				team = User.objects.filter(reporting_to__in = supervisors)
				users = users | team
			final_camp_users = total_camp_users | users
			final_camp_users = final_camp_users.exclude(user_role__access_level="Admin").exclude(is_superuser=True)
			user_list = final_camp_users.values("id", "username")
		context["campaign_list"] =campaign_list
		context['all_fields'] =  ('campaign','dialer_idle_time','pause_progressive_time','progressive_time','preview_time',
			'predictive_wait_time','inbound_wait_time','blended_wait_time','ring_duration','hold_time','media_time','bill_sec','call_duration','feedback_time','break_time',
			'dialer_login_time','total_login_time','total_calls')
		context["user_list"] = user_list
		context['report_visible_cols'] = report_visible_cols
		context = {**context, **kwargs['permissions']}
		return Response(context)

	def post(self, request, *args, **kwargs):
		context = writer = {}
		call_result= []
		admin = False
		logged_in_user = request.user
		download_report = request.POST.get("agent_reports_download", "")
		if download_report:
			context = {}
			col_name = request.POST.get("column_name", "")
			col_list = col_name.split(",")
			filters = request.POST.dict()
			filters['all_users'] = request.POST.get("all_users", "").split(',')
			filters['selected_campaign'] = request.POST.getlist("selected_campaign", [])
			filters['selected_user'] = request.POST.getlist("selected_user", [])
			filters['download_type'] = request.POST.get("agent_reports_download_type",'csv')
			DownloadReports.objects.create(report='Campaign Wise Performance',filters=filters, user=request.user.id, serializers=None, col_list=col_list, status=True)
			return JsonResponse({"message":"Your Download request is created, will notify in download notification once completed."})
		user_list = campaign_list =[]
		admin = False
		if request.user.user_role and request.user.user_role.access_level == 'Admin':
			admin = True

		selected_campaign = request.POST.getlist("selected_campaign", "")

		if request.user.is_superuser or admin:
			if selected_campaign:
				campaign_list = Campaign.objects.filter(name__in=selected_campaign).distinct().values_list("name", flat=True)
			else:
				campaign_list = Campaign.objects.all().distinct().values_list("name", flat=True)
		else:
			if selected_campaign:
				camp = Campaign.objects.filter(Q(users=request.user, users__isnull=False)| Q( group__in=request.user.group.all(), group__isnull=False), name__in=selected_campaign).distinct()
			else:
				camp = Campaign.objects.filter(Q(users=request.user, users__isnull=False)| Q( group__in=request.user.group.all(), group__isnull=False)).distinct()
			campaign_list = camp.values_list("name", flat=True)
		if request.user.user_role and request.user.user_role.access_level == 'Admin':
			admin = True
		selected_user = request.POST.get("selected_user", "")
		all_users = request.POST.get("all_users","")
		all_users = all_users.split(',')
	
		if selected_campaign:
			campaign_list = selected_campaign

		start_date = request.POST.get("start_date", "")
		end_date = request.POST.get("end_date", "")
		page = int(request.POST.get('page' ,1))
		paginate_by = int(request.POST.get('paginate_by', 10))
		campaign_list = get_paginated_object(campaign_list, page, paginate_by)
		if start_date:
			start_date = datetime.strptime(start_date,"%Y-%m-%d %H:%M").isoformat()
		if end_date:
			end_date = datetime.strptime(end_date,"%Y-%m-%d %H:%M").isoformat()

		start_end_date_filter = Q(created__gte=start_date)&Q(created__lte=end_date)
		dialler_idle_time_filter = ~Q(campaign_name="")&~Q(event__in=["DIALER LOGIN","LOGOUT"])
		default_time = timedelta(seconds=0)
		if start_date:
			call_details = CallDetail.objects.filter(created__gte=start_date).select_related()
			if end_date:
				call_details = call_details.filter(created__lte=end_date)
		else:
			call_details = CallDetail.objects.all().select_related()
		for i in campaign_list:
			calldetail = call_details.filter(Q(campaign_name=i))
			agentactivity = AgentActivity.objects.filter(Q(campaign_name=i))
			calldetail_cal = calldetail.aggregate(media_time=Cast(Coalesce(Sum('media_time',filter=start_end_date_filter),default_time),TextField()),
				ring_duration=Cast(Coalesce(Sum('ring_duration',filter=start_end_date_filter),default_time),TextField()),
				hold_time=Cast(Coalesce(Sum('hold_time',filter=start_end_date_filter),default_time),TextField()),
				call_duration=Cast(Coalesce(Sum('call_duration',filter=start_end_date_filter),default_time),TextField()),
				bill_sec=Cast(Coalesce(Sum('bill_sec',filter=start_end_date_filter),default_time),TextField()),
				feedback_time=Cast(Coalesce(Sum('feedback_time',filter=start_end_date_filter),default_time),TextField()),
				)
			activity_cal = agentactivity.aggregate(break_time=Cast(Coalesce(Sum('break_time',filter=start_end_date_filter),default_time),TextField()),
				pause_progressive_time=Cast(Coalesce(Sum('pause_progressive_time',filter=start_end_date_filter),default_time),TextField()),
				predictive_time=Cast(Coalesce(Sum('predictive_time',filter=start_end_date_filter),default_time),TextField()),
				progressive_time=Cast(Coalesce(Sum('progressive_time',filter=start_end_date_filter),default_time),TextField()),
				preview_time=Cast(Coalesce(Sum('preview_time',filter=start_end_date_filter),default_time),TextField()),
				predictive_wait_time=Cast(Coalesce(Sum('predictive_wait_time',filter=start_end_date_filter),default_time),TextField()),
				inbound_time=Cast(Coalesce(Sum('inbound_time',filter=start_end_date_filter),default_time),TextField()),
				blended_time=Cast(Coalesce(Sum('blended_time',filter=start_end_date_filter),default_time),TextField()),
				inbound_wait_time=Cast(Coalesce(Sum('inbound_wait_time',filter=start_end_date_filter),default_time),TextField()),
				blended_wait_time=Cast(Coalesce(Sum('blended_wait_time',filter=start_end_date_filter),default_time),TextField()),
				dialer_idle_time=Cast(Coalesce(Sum('idle_time',filter=start_end_date_filter & dialler_idle_time_filter),default_time),TextField())
				)
			pp_time = convert_into_timedelta(activity_cal['pause_progressive_time']).total_seconds()
			pw_time = convert_into_timedelta(activity_cal['predictive_wait_time']).total_seconds()
			preview_time = convert_into_timedelta(activity_cal['preview_time']).total_seconds()
			break_time = convert_into_timedelta(activity_cal['break_time']).total_seconds()
			iw_time = convert_into_timedelta(activity_cal['inbound_wait_time']).total_seconds()
			bw_time = convert_into_timedelta(activity_cal['blended_wait_time']).total_seconds()
			di_time = convert_into_timedelta(activity_cal['dialer_idle_time']).total_seconds()
			call_duration = convert_into_timedelta(calldetail_cal['call_duration']).total_seconds()
			feedback_time = convert_into_timedelta(calldetail_cal['feedback_time']).total_seconds()
			dialer_login_time = int(pp_time)+int(pw_time)+int(preview_time)+int(iw_time)+int(bw_time)+int(
				di_time)+int(call_duration)+int(feedback_time)
			total_login_time = int(dialer_login_time)+int(break_time)
			calldetail_cal['dialer_login_time'] = time.strftime("%H:%M:%S", time.gmtime(dialer_login_time))
			calldetail_cal['total_login_time'] = time.strftime("%H:%M:%S", time.gmtime(total_login_time))
			calldetail_cal = {**calldetail_cal, **activity_cal}
			calldetail_cal['total_calls'] = calldetail.count()
			calldetail_cal['campaign'] = i

			call_result.append(calldetail_cal)

		return JsonResponse({'total_records': campaign_list.paginator.count,
				'total_pages': campaign_list.paginator.num_pages,
				'page': campaign_list.number,'start_index':campaign_list.start_index(), 'end_index':campaign_list.end_index(),
				'has_next': campaign_list.has_next(),
				'has_prev': campaign_list.has_previous(),'table_data':call_result[::-1]})

@method_decorator(check_read_permission, name='get')
class AgentMISReportView(LoginRequiredMixin, generics.ListAPIView, pagination.PageNumberPagination):
	"""
	This View is used to show agent mis report 
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "reports/agent-mis.html"
	permissions = {"Dashboard": ["all"]}

	def get(self, request, *args, **kwargs):
		context = {}
		user_list = campaign_list =[]
		admin = False
		report_visible_cols = get_report_visible_column("4",request.user)
		if request.user.user_role and request.user.user_role.access_level == 'Admin':
			admin = True
		if request.user.is_superuser or admin:
			campaign_list = Campaign.objects.all().distinct().values("id", "name")
			user_list = User.objects.all().exclude(
				user_role__access_level="Admin").exclude(is_superuser=True).values("id", "username")
		else:
			camp = Campaign.objects.filter(Q(users=request.user, users__isnull=False)|
				Q( group__in=request.user.group.all(), group__isnull=False)).distinct()
			campaign_list = camp.values("id", "name")

			c_user  = c_group = []
			for campaign in camp:
				c_user.extend(list(campaign.users.all().values_list("id", flat=True)))
				c_group.extend(list(campaign.group.all().values_list("id", flat=True)))
			temp_id = c_user + c_group
			c_group_user = User.objects.filter(group__id__in=c_group)
			c_users = User.objects.filter(id__in=c_user)
			total_camp_users = c_group_user | c_users
			#reporting users
			users = User.objects.filter(reporting_to = request.user)
			if request.user.user_role.access_level == 'Manager':
				supervisors = users.exclude(user_role__access_level="Agent")
				team = User.objects.filter(reporting_to__in = supervisors)
				users = users | team
			final_camp_users = total_camp_users | users
			final_camp_users = final_camp_users.exclude(user_role__access_level="Admin").exclude(is_superuser=True)
			user_list = final_camp_users.values("id", "username")

		context["campaign_list"] =campaign_list
		all_fields =  set(Campaign.objects.filter(status='Active').exclude(disposition=None).values_list("disposition__name", flat=True))
		wfh_dispo_list = list(Campaign.objects.filter(wfh=True, status='Active').values_list('wfh_dispo',flat=True))
		wfh_dispo = set([ d for m in wfh_dispo_list for d in m.values()])
		all_fields.update(wfh_dispo)
		tmp_list = ["User", "Full Name","Supervisor Name","Campaign", "Total Dispo Count", "AutoFeedback", "AbandonedCall",
		'NC','Invalid Number',"RedialCount", "AlternateDial", "PrimaryDial", "NF(No Feedback)"]
		all_fields = tmp_list + list(all_fields)
		context["all_fields"] = all_fields
		context["user_list"] = user_list
		context['report_visible_cols'] = report_visible_cols
		context = {**context, **kwargs['permissions']}
		return Response(context)

	def post(self,request):
		download_report = request.POST.get("agent_reports_download", "")
		if download_report:
			context = {}
			col_name = request.POST.get("column_name", "")
			col_list = col_name.split(",")
			filters = request.POST.dict()
			filters['all_users'] = request.POST.get("all_users", "").split(',')
			filters['selected_campaign'] = request.POST.getlist("selected_campaign", [])
			filters['selected_user'] = request.POST.getlist("selected_user", [])
			filters['all_campaigns'] = request.POST.get("all_campaigns", "").split(',')
			filters['download_type'] = request.POST.get("agent_reports_download_type",'csv')
			DownloadReports.objects.create(report='Agent Mis Report', filters=filters, user=request.user.id, serializers=None, col_list=col_list, status=True)
			return JsonResponse({"message":"Your Download request is created, will notify in download notification once completed."})

		context = get_agent_mis(request.POST, request)
		camp_name, active_camp, noti_count = get_active_campaign(request)
		return JsonResponse(context)

@method_decorator(check_read_permission, name='get')
class CampaignMISReportView(LoginRequiredMixin, generics.ListAPIView, pagination.PageNumberPagination):
	"""
	This View is used to show campaignwise mis report 
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "reports/campaign-mis.html"
	permissions = {"Dashboard": ["all"]}

	def get(self, request, *args, **kwargs):
		context = {}
		user_list = campaign_list =[]
		admin = False
		report_visible_cols = get_report_visible_column("6",request.user)
		if request.user.user_role and request.user.user_role.access_level == 'Admin':
			admin = True
		if request.user.is_superuser or admin:
			campaign_list = Campaign.objects.all().distinct().values("id", "name")
			user_list = User.objects.all().exclude(
				user_role__access_level="Admin").exclude(is_superuser=True).values("id", "username")
		else:
			camp = Campaign.objects.filter(Q(users=request.user, users__isnull=False)|
				Q( group__in=request.user.group.all(), group__isnull=False)).distinct()
			campaign_list = camp.values("id", "name")

			c_user  = c_group = []
			for campaign in camp:
				c_user.extend(list(campaign.users.all().values_list("id", flat=True)))
				c_group.extend(list(campaign.group.all().values_list("id", flat=True)))
			temp_id = c_user + c_group
			c_group_user = User.objects.filter(group__id__in=c_group)
			c_users = User.objects.filter(id__in=c_user)
			total_camp_users = c_group_user | c_users
			#reporting users
			users = User.objects.filter(reporting_to = request.user)
			if request.user.user_role.access_level == 'Manager':
				supervisors = users.exclude(user_role__access_level="Agent")
				team = User.objects.filter(reporting_to__in = supervisors)
				users = users | team
			final_camp_users = total_camp_users | users
			final_camp_users = final_camp_users.exclude(user_role__access_level="Admin").exclude(is_superuser=True)
			user_list = final_camp_users.values("id", "username")

		context["campaign_list"] =campaign_list
		all_fields =  list(set(Campaign.objects.all().exclude(disposition=None).values_list("disposition__name", flat=True)))
		tmp_list = ["Campaign", "Total Dispo Count", "AutoFeedback", "AbandonedCall", "NC", "Invalid Number", "RedialCount", "AlternateDial", "PrimaryDial", "NF(No Feedback)"]
		all_fields = tmp_list + list(set(all_fields)) 
		context["all_fields"] = all_fields
		context["user_list"] = user_list
		context['report_visible_cols'] = report_visible_cols
		context = {**context, **kwargs['permissions']}
		return Response(context)

	def post(self,request):
		download_report = request.POST.get("agent_reports_download", "")
		if download_report:
			context = {}
			col_name = request.POST.get("column_name", "")
			col_list = col_name.split(",")
			filters = request.POST.dict()
			filters['selected_campaign'] = request.POST.getlist("selected_campaign", [])
			filters['all_campaigns'] = request.POST.get("all_campaigns", "").split(',')
			filters['download_type'] = request.POST.get("agent_reports_download_type",'csv')
			DownloadReports.objects.create(report='Campaign Mis', filters=filters, user=request.user.id, serializers=None, col_list=col_list, status=True)
			return JsonResponse({"message":"Your Download request is created, will notify in download notification once completed."})
		context = get_campaign_mis(request.POST, request)
		camp_name, active_camp, noti_count = get_active_campaign(request)
		return JsonResponse(context)
		
class GetCampaignUserAPIView(APIView):
	"""
	This view is used to return users of selected campaign
	"""
	def post(self, request):
		campaign = request.POST.getlist("campaign[]", "")
		if not campaign:
			campaign = [request.POST.get("campaign", "")]
		camp = Campaign.objects.filter(name__in=campaign)
		if campaign:
			users = list(get_campaign_users(campaign, request.user).values("id", "username"))
		else:
			users = []
		dispo = camp.values_list("disposition__id", flat=True)
		disposition = list(Disposition.objects.filter(id__in=dispo).values("id", "name"))
		return JsonResponse({"users":users, "disposition": disposition})    

# @method_decorator(check_read_permission, name='get')
class AgentHomeApiView(LoginRequiredMixin, APIView):
	"""
	This class based view is defined for agent home screen.
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "agent/crm.html"
	permission_classes = [AllowAny]

	def get(self, request, **kwargs):
		can_switch = False
		non_agent_user = False
		permissions = request.session.get('permissions')
		if not request.user.is_superuser and permissions:
			if 'R' in permissions['switchscreen']:
				can_switch = True
				non_agent_user = True
		today = date.today()  # Get today's date
		# Calculate start and end times
		start_date = today  # Midnight at the beginning of the day
		end_date = today + timedelta(days=1)  # Midnight at the beginning of the next day
		start_end_date_filter = Q(created__gte=start_date)&Q(created__lte=end_date)
		campaigns = Campaign.objects.filter(Q(users=request.user)|Q(group__in=request.user.group.all())).filter(status='Active')
		camp_name = list(campaigns.values_list('name',flat=True))
		breaks = PauseBreak.objects.filter(campaign__name__in=camp_name).distinct()
		pause_breaks= json.dumps(AgentPauseBreakSerializer(breaks.values('name','break_time','inactive_on_exceed'), many=True).data)
		#total_agentcalls = CallDetail.objects.filter(user=request.user).exclude(cdrfeedback=None).aggregate(total_agentcalls_today=Count('id', filter=start_end_date_filter),total_agentcalls_month=Count('id', filter=Q(created__month=datetime.now().month)))
		# total_agentcalls = CallDetail.objects.filter(user=request.user).filter(cdrfeedback__id__gte=0).aggregate(total_agentcalls_today=Count('id', filter=start_end_date_filter),total_agentcalls_month=Count('id', filter=Q(created__month=datetime.now().month)))
		
		today_start = datetime.combine(datetime.today(), datetime.min.time())  # Start of today
		today_end = datetime.combine(datetime.today(), datetime.max.time())  # End of today
		first_day_of_month = today_start.replace(day=1) 
	
		total_agentcalls = CallDetail.objects.filter(user=request.user,created__gte=first_day_of_month,cdrfeedback__isnull=False).aggregate(
		total_agentcalls_today=Count('id', filter=Q(created__gte=today_start, created__lte=today_end)),
		total_agentcalls_month=Count('id', filter=Q(created__gte=first_day_of_month, created__lte=today_end)))
		
		total_agent_assigned_calls = Contact.objects.filter(user=request.user, campaign__in=camp_name).count()
		login_agent_data = LoginAgentDataSerializer(request.user).data
		context = {'request':request, 'breaks':pause_breaks, "server_ip":settings.WEB_SOCKET_HOST, "can_switch":can_switch, "total_agent_assigned_calls":total_agent_assigned_calls, 
		'user':login_agent_data, 'non_agent_user':non_agent_user}
		context = {**context, **total_agentcalls}
		return Response(context)


class DiallerLogin(LoginRequiredMixin, APIView):
	"""
	This class based view is defined for DiallerLogin in agent home screen.
	"""
	login_url = '/'
	def post(self, request):
		campaign = Campaign.objects.get(pk=request.POST.get("campaign_id"))
		holiday_obj = Holidays.objects.filter(status='Active',holiday_date=datetime.today())
		if holiday_obj.exists():
			return Response({"error":"Today is Declared as Holiday so you can't login to the campaign"},status=403)
		if campaign.schedule and campaign.schedule.status == 'Active':
			camp_schedule=campaign.schedule.schedule
			day_now = datetime.today().strftime('%A')
			if camp_schedule.get(day_now)['start_time'] is not None and camp_schedule.get(day_now)['stop_time'] is not None:
				if camp_schedule.get(day_now)['start_time'] != "" and camp_schedule.get(day_now)['stop_time'] != "":
					start_time_obj = datetime.strptime(camp_schedule.get(day_now
						)['start_time'], '%I:%M %p').time()
					stop_time_obj = datetime.strptime(camp_schedule.get(day_now
						)['stop_time'], '%I:%M %p').time()
					if datetime.now().time() < start_time_obj or datetime.now().time() > stop_time_obj:
						return Response({'error':"This campaign is not available in this time period,please coordinate "\
						"with your administrator or login to the another campaign."}, status=403)
				else:
					return Response({'error':"This campaign is not available in this time period,please coordinate "\
						"with your administrator or login to the another campaign."}, status=403)   
			else:
				return Response({'error':"This campaign time period is None,please coordinate "\
						"with your administrator or login to the another campaign."}, status=403)   
		if request.user.call_type =='3':
			status = {"error":"SIP-IP-PHONE enable for this user..., please coordinate your administrator."}
			return Response(status, status=500)
		app_time = request.POST.get("app_time", "")
		idle_time = request.POST.get("idle_time", "")
		if app_time:
			app_time = datetime.strptime(app_time, '%H:%M:%S').time() 
			time = datetime.strptime("0:0:0", '%H:%M:%S').time()
			idle_time = datetime.strptime(idle_time, '%H:%M:%S').time()
			agent_data = {"user"}
			# track agent activities
			activity_list = ['dialer_time', 'media_time', 'spoke_time', 'preview_time',
			'predictive_time', 'feedback_time', 'break_time']
			activity_dict = dict.fromkeys(activity_list, time)
			activity_dict["user"] = request.user
			activity_dict["event"] = "DIALER LOGIN"
			activity_dict["campaign_name"] = campaign.name
			activity_dict["event_time"] =datetime.now()
			activity_dict["tos"] = app_time
			activity_dict["app_time"] = app_time
			activity_dict["idle_time"] = idle_time
			activity_dict["break_type"] = ""
			create_agentactivity(activity_dict)
		AGENTS = {}
		AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or
				pickle.dumps(AGENTS))
		extension =request.user.extension
		call_type = request.user.call_type
		caller_id = campaign.caller_id
		sip_udp_port = campaign.switch.sip_udp_port
		wss_port = campaign.switch.wss_port
		rpc_port = campaign.switch.rpc_port 
		disposition = DispositionSerializer(campaign.disposition.filter(status='Active'), many=True).data
		on_call_dispositions = []
		not_on_call_dispostion = []
		for dispo in disposition:
			if dispo['show_dispo'] in ['0','1']:
				on_call_dispositions.append(dispo)
			if dispo['show_dispo'] in ['0','2']:
				not_on_call_dispostion.append(dispo)
		if not on_call_dispositions:
			return Response({'error':"All Not-Connected Dispositions are selected, Contact "\
						"with your administrator to assign On-Connected Disposition"}, status=403)
		if not not_on_call_dispostion:
			return Response({'error':"All On-Connected Dispositions are selected, Contact "\
						"with your administrator to assign Not-Connected Disposition"}, status=403)
		relation_tag = RelationTagSerializer(campaign.relation_tag.filter(status='Active'),many=True).data
		campaign_data = ReadOnlyCampaignSerializer(campaign).data
		script =Script.objects.filter(campaign=campaign,status='Active')
		if script.exists():
			script=ScriptSerializer(script[0]).data
		crm_field = CrmField.objects.filter(campaign__name=campaign.name)
		required_field_list = []
		if crm_field.exists():
			crm_data = AgentCrmFieldSerializer(crm_field.first()).data
			crm_fields = crm_data['crm_fields']
			for crm_field in crm_fields:
				section_name = crm_field["db_section_name"]
				for fields in crm_field['section_fields']:
					if 'required' in fields and fields['required']:
						required_field_list.append(str(section_name)+":"+str(fields['db_field']))
		else:
			crm_fields = []
			unique_fields=[]
		crm_fieds_data = crm_field_value_schema(campaign.name)
		status=twinkle_session(campaign.switch.ip_address,extension=request.user.extension,
				campaign_name=campaign.slug,call_type=call_type)
		total_camp_assigned_calls = 0
		if campaign.portifolio:
			total_camp_assigned_calls = Contact.objects.filter(user=request.user.username, campaign=campaign.name).count()
		user_role_list = []
		if request.user.user_role:
			if request.user.user_role.access_level =='Agent':
				user_role_list = ['Admin','Supervisor','Manager']
			elif request.user.user_role.access_level =='Supervisor':
				user_role_list = ['Admin','Manager']
			elif request.user.user_role.access_level =='Manager':
				user_role_list = ['Admin']
		lead_user = User.objects.filter(Q(group__in=campaign.group.values_list('id',flat=True))|Q(id__in=campaign.users.values_list('id',flat=True))).filter(user_role__access_level__in=user_role_list).annotate(text=F('username')).values('id','text')
		if "error" in status:
			return Response(status, status=500)
		if 'error' not in status:
			if extension not in AGENTS:
				AGENTS[extension] = {}
				AGENTS[extension]['username']= request.user.username
				AGENTS[extension]['extension']= request.user.extension
				AGENTS[extension]['login_status'] = True
				AGENTS[extension]['login_time'] = datetime.now().strftime('%H:%M:%S')
				AGENTS[extension]['call_type'] = ''
				AGENTS[extension]['dial_number'] = ''
				AGENTS[extension]['call_timestamp'] = ''
			AGENTS[extension]['wfh'] = False
			AGENTS[extension]['campaign'] = campaign.name
			AGENTS[extension]['dialer_login_status'] = True
			AGENTS[extension]['dialer_login_time'] = datetime.now().strftime('%H:%M:%S')
			AGENTS[extension]['status'] = 'Ready'
			AGENTS[extension]['state'] = 'Idle'
			AGENTS[extension]['event_time'] = datetime.now().strftime('%H:%M:%S')
			AGENTS[extension]['dialerSession_switch'] = campaign.switch.ip_address
			AGENTS[extension]['dialerSession_uuid'] = status['ori_uuid']
			updated_agent_dict = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
			updated_agent_dict[extension] = AGENTS[extension]
			settings.R_SERVER.set("agent_status", pickle.dumps(updated_agent_dict))
		template = []
		email_gateway = {}
		disabled_sms_tab = False
		send_sms_callrecieve = False
		send_sms_on_dispo = False
		if campaign.sms_gateway:
			template = campaign.sms_gateway.template.filter(Q(campaign_id=campaign.id)|Q(template_type='0'))
			if campaign.sms_gateway.sms_trigger_on=='2':
				disabled_sms_tab = True
			elif campaign.sms_gateway.sms_trigger_on=='1':
				send_sms_on_dispo = True
			else:
				send_sms_callrecieve = True

			if template.exists():
				template = list(template.values('id','text'))
		if campaign.email_gateway and campaign.email_gateway.status == 'Active':
			email_gateway['gateway_id'] = campaign.email_gateway.id
			email_gateway['email_templates'] = campaign.email_gateway.template.filter(status='Active').values('id','email_body','email_subject')
			email_gateway['email_type'] = campaign.email_gateway.email_trigger_on
			email_gateway['email_dispositions'] = list(campaign.email_gateway.disposition.values_list('name',flat=True))
		PhonebookBucketCampaign.objects.filter(id=campaign.id).update(agent_login_count=F('agent_login_count')+1)
		return Response({'call_type':call_type,'status':status,
			'campaign':campaign_data, 'disposition':disposition,'relation_tag':relation_tag,
			'crm_fields':crm_fields, 'campaign_caller_id': caller_id,'script':script,
			'crm_fieds_data':crm_fieds_data, 'total_camp_assigned_calls':total_camp_assigned_calls,
			'sms_templates':template,'disabled_sms_tab':disabled_sms_tab,'send_sms_on_dispo':send_sms_on_dispo,'send_sms_callrecieve':send_sms_callrecieve,'lead_user':lead_user,
			'email_gateway':email_gateway, 'sip_udp_port':sip_udp_port, 'wss_port':wss_port, 'rpc_port':rpc_port,
			'required_fields':required_field_list,'on_call_dispositions':on_call_dispositions,"not_on_call_dispostion":not_on_call_dispostion })

class MaunalDialListAPIView(LoginRequiredMixin, APIView):
	"""
	This class based view is defined for manually List the customer numbers.
	"""
	login_url = '/'
	def post(self, request):
		dial_number = request.POST.get('dial_number', '')
		campaign = request.POST.get('campaign', '')
		campaign_object = Campaign.objects.get(name=campaign)
		data=customer_detials(campaign,dial_number,campaign_object)
		return JsonResponse(data)
		

class ManualDial(LoginRequiredMixin, APIView):
	"""
	This class based view is defined for manually dial the customer numbers.
	"""
	login_url = '/'
	def post(self, request):
		AGENTS = {}
		AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or
				pickle.dumps(AGENTS))
		status = {}
		dial_number = request.POST.get('dial_number', '')
		contact_id = request.POST.get('contact_id', '')
		# if not contact_id:
		#   contact_id = 0
		preview_number = request.POST.get('preview_number', '')
		campaign_name = request.POST.get('campaign_name', '')
		campaign_id = request.POST.get('campaign_id', '')
		session_details = json.loads(request.POST.get('session_details','{}'))
		user_name = request.POST.get('user_name', '')
		call_type = request.POST.get("call_type", "")
		caller_id = request.POST.get("caller_id", "")
		outbound = request.POST.get("outbound","")
		callmode = request.POST.get("callmode","")
		lead_preview = json.loads(request.POST.get("lead_preview","false"))
		is_callback = request.POST.get("is_callback",'false')
		is_abandoned_call = request.POST.get("is_abandoned_call", 'false')
		is_abandoned_callback = request.POST.get("is_abandoned_callback", 'false')
		man_unique_id = request.POST.get("unique_id",None)
		#Track agent activity 
		activity_dict = get_formatted_agent_activities(request.POST)
		activity_dict["user"] = request.user
		activity_dict["campaign_name"] = campaign_name
		if call_type != "not_manual":
			activity_dict["event"] = call_type.upper()
		else:
			activity_dict["event"] = outbound.upper()

		activity_dict["event_time"] =datetime.now()
		create_agentactivity(activity_dict)
		if preview_number:
			# if user clicked on next call and then he clicked on manual call
			# we have to changed next call status from locked to notdialed
			temp_contact = TempContactInfo.objects.filter(numeric=preview_number, status='Locked',
				campaign=campaign_name)
			if temp_contact.exists():
				temp_contact.update(status='NotDialed')
		if not dial_number:
			portifolio = Campaign.objects.filter(name=campaign_name).first().portifolio
			temp_contact = get_temp_contact(user_name, campaign_name, portifolio)
			if temp_contact:
				dummy_contact = GetContactToCheckcNdnc(user_name,campaign_name,campaign_id,temp_contact,portifolio)
				if dummy_contact:
					dial_number = dummy_contact.numeric
					contact_id = dummy_contact.id
				else:
					return Response({"msg": "Numbers are not present in this campaign"})    
			else:
				return Response({"msg": "Numbers are not present in this campaign"})
		if dial_number:
			user_trunk_id = None
			caller_id = None
			if request.user.trunk and request.user.caller_id:
				user_trunk_id = request.user.trunk_id
				caller_id = request.user.caller_id
			status = dial(session_details['variable_sip_from_host'],
				dial_number=dial_number,session_details=session_details,extension =request.user.extension,
				campaign=campaign_name,user_name=user_name,call_type=call_type,caller_id=caller_id, user_trunk_id=user_trunk_id,
				contact_id=contact_id, callmode=callmode,lead_preview=lead_preview, man_unique_id=man_unique_id,user_id=request.user.id)
		if 'success' in status:
			if is_callback == 'true':
				CurrentCallBack.objects.filter(numeric = dial_number,campaign=campaign_name,
					contact_id=contact_id).delete()
				CallBackContact.objects.filter(numeric = dial_number,campaign=campaign_name,
					contact_id=contact_id).delete()
				SnoozedCallback.objects.filter(numeric = dial_number,contact_id=contact_id).delete()
				Notification.objects.filter(numeric=dial_number, title='callback',
					user=user_name,contact_id=contact_id).update(viewed=True)
			if is_abandoned_call == 'true':
				Notification.objects.filter(numeric=dial_number, title='Abandonedcall').update(viewed=True)
				Abandonedcall.objects.filter(numeric=dial_number).delete()

			if is_abandoned_callback == 'true':
				CurrentCallBack.objects.filter(numeric = dial_number,campaign=campaign_name).delete()
				CallBackContact.objects.filter(numeric = dial_number,campaign=campaign_name).delete()
				SnoozedCallback.objects.filter(numeric = dial_number).delete()
				Notification.objects.filter(numeric=dial_number, title='callback',
					user=user_name).update(viewed=True)
			if call_type == 'manual':
				AGENTS[request.user.extension]['call_type'] = 'manual'
			else:
				AGENTS[request.user.extension]['call_type'] = outbound
			AGENTS[request.user.extension]['state'] = "InCall"
			AGENTS[request.user.extension]['event_time'] = datetime.now().strftime('%H:%M:%S')
			AGENTS[request.user.extension]['dial_number'] = dial_number
			updated_agent_dict = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
			updated_agent_dict[request.user.extension].update(AGENTS[request.user.extension])
			settings.R_SERVER.set("agent_status", pickle.dumps(updated_agent_dict))
		else:
			if is_callback == 'true':
				current_cb = CurrentCallBack.objects.filter(numeric = dial_number,campaign=campaign_name,
					contact_id=contact_id)
				callback_c = CallBackContact.objects.filter(numeric = dial_number,campaign=campaign_name,
					contact_id=contact_id)
				if current_cb.exists():
					current_cb.update(status='NotDialed')
					callback_c.update(status='Queued')
				else:
					callback_c.update(status='NotDialed')
			if is_abandoned_call == 'true':
				Abandonedcall.objects.filter(numeric=dial_number,caller_id=caller_id).update(status='NotDialed')
		return Response(status)

class HangupCall(LoginRequiredMixin, APIView):
	"""
	This class based view is defined for hangup the calls. 
	"""
	login_url = '/'
	def post(self, request):
		hangup_type =''
		hangup_status = {}
		AGENTS = {}
		campaign  = request.POST.get('campaign_name')
		contact_id = request.POST.get('contact_id', '')
		agent_uuid_id = request.POST.get('agent_uuid_id', None)
		if not contact_id:
			contact_id = 0
		extension = request.user.extension
		preview_number = request.POST.get('preview_number', '')
		call_type = request.POST.get('call_type','')
		if request.POST.get('hangup_type'):
			hangup_type = request.POST.get('hangup_type')
		activity_dict = get_formatted_agent_activities(request.POST)
		activity_dict["user"] = request.user
		activity_dict["campaign_name"] = campaign
		if hangup_type == "sip_agent":
			activity_dict["event"] = "DIALER LOGOUT"
		else:
			activity_dict["event"] = "AGENT HANGUP"
		activity_dict["event_time"] = datetime.now()
		create_agentactivity(activity_dict)
		if preview_number:
			# if user clicked on next call and then he clicked on manual call
			# we have to changed next call dstatus from locked to notdialed
			temp_contact = TempContactInfo.objects.filter(id=contact_id, status='Locked')
			if temp_contact.exists():
				temp_contact.update(status='NotDialed')
		
		hangup_status=hangup(request.POST.get('switch'),uuid=request.POST.get('uuid'),
				hangup_type=hangup_type,extension=extension, campaign = campaign, agent_uuid_id=agent_uuid_id)
		if request.POST.get('page_reload','false') == 'true':
			
			AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or
				pickle.dumps(AGENTS))
			set_agentReddis(AGENTS,request.user)
			updated_agent_dict = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
			updated_agent_dict[request.user.extension].update(AGENTS[request.user.extension])
			settings.R_SERVER.set("agent_status", pickle.dumps(updated_agent_dict))

		AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or
				pickle.dumps(AGENTS))

		return Response(hangup_status)

def GetContactToCheckcNdnc(user,campaign,campaign_id,temp_contact,portifolio=False):
	#check for ndnc scrub contact information 
	if CampaignVariable.objects.get(campaign=campaign_id).ndnc_scrub:
		response = scrub(temp_contact.numeric) 
		if response:
			#ndnc_number =True
			Contact.objects.filter(id=temp_contact.id).update(status='NDNC')
			TempContactInfo.objects.filter(contact_id=temp_contact.id).delete()
			temp_contact = get_temp_contact(user, campaign,portifolio)
			if temp_contact:
				temp_contact = GetContactToCheckcNdnc(user,campaign,campaign_id,temp_contact,portifolio)
	return temp_contact


class PreviewUpdateContactStatus(APIView):
	"""
	This view will show the contact information once
	the dialnext button is clicked
	"""
	def post(self, request):
		AGENTS = {}
		AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or
				pickle.dumps(AGENTS))
		contact_info = {}
		contact_dialled = {}
		campaign = request.POST.get("campaign_name", "")
		campaign_id = request.POST.get("campaign_id", "")
		user = request.POST.get("user_name", "")
		dial_number = request.POST.get("dial_number", "")
		contact_id = request.POST.get("contact_id", "")
		call_type = request.POST.get("call_type","")
		# Track agent activities
		agent_data = get_formatted_agent_activities(request.POST)
		agent_data["user"] = request.user
		agent_data["campaign_name"] = campaign
		agent_data["break_type"] = ""
		agent_data["event"] = "Next Call Info"
		agent_data["event_time"] = datetime.now()
		create_agentactivity(agent_data)
		update_status = False
		portifolio = Campaign.objects.filter(name=campaign).first().portifolio
		temp_contact = get_temp_contact(user, campaign, portifolio)
		if temp_contact:
			temp_contact = GetContactToCheckcNdnc(user,campaign,campaign_id,temp_contact,portifolio)
			if temp_contact:
				update_status = True
				temp_contact =Contact.objects.filter(id=temp_contact.id).first()
				contact_info = ContactSerializer(temp_contact).data
				if call_type:
					if call_type == "Progressive":
						AGENTS[request.user.extension]['state'] = "Progressive Dialling"
					else:
						AGENTS[request.user.extension]['state'] = "Preview Dialling"
					if not dial_number:
						AGENTS[request.user.extension]['event_time'] = datetime.now().strftime('%H:%M:%S')
			else:
				update_status = False
				if not contact_id:
					AGENTS[request.user.extension]['state'] = "Idle"
					AGENTS[request.user.extension]['event_time'] = datetime.now().strftime('%H:%M:%S')  
		else:
			update_status = False
			if not contact_id:
				AGENTS[request.user.extension]['state'] = "Idle"
				AGENTS[request.user.extension]['event_time'] = datetime.now().strftime('%H:%M:%S')
		updated_agent_dict = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
		updated_agent_dict[request.user.extension].update(AGENTS[request.user.extension])
		settings.R_SERVER.set("agent_status", pickle.dumps(updated_agent_dict))
		if dial_number and dial_number !="null" and update_status:
			if contact_id:
				temp_contact = TempContactInfo.objects.filter(numeric=dial_number, status='Locked', id=contact_id)
				if temp_contact.exists():
					temp_contact.update(status='NotDialed')
		return JsonResponse({"contact_info": contact_info})

class SkipCallContactStatus(APIView):
	"""
	Skipping the locked contact in progressive/preview
	"""
	def post(self,request):
		campaign_name = request.POST.get('campaign_name','')
		user =request.POST.get("user_name",'')
		dial_number= request.POST.get('dial_number','')
		contact_id = request.POST.get('contact_id', '')
		AGENTS = {}
		AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or
				pickle.dumps(AGENTS))
		AGENTS[request.user.extension]['state'] = "Idle"
		AGENTS[request.user.extension]['event_time'] = datetime.now().strftime('%H:%M:%S')
		settings.R_SERVER.set("agent_status", pickle.dumps(AGENTS))
		#Trac Agent Activity
		agent_activity_data = []
		agent_activity_data = get_formatted_agent_activities(request.POST)
		agent_activity_data['user'] = request.user
		agent_activity_data['campaign_name'] = campaign_name
		agent_activity_data["break_type"] = ""
		agent_activity_data["event"] = "Skiped"
		agent_activity_data["event_time"] = datetime.now()
		create_agentactivity(agent_activity_data)
		if dial_number and dial_number != "null":
			contact = TempContactInfo.objects.filter(id=contact_id)
			if contact.exists():
				contact.update(status='NotDialed')
		return JsonResponse({"msg":"Number skipped"})

class PauseprogressiveContactStatus(APIView):
	"""
	Pausing the progressive contact and storing the 
	agent activity 
	"""
	def post(self, request):
		campaign_name = request.POST.get("campaign_name", "")
		user = request.POST.get("username", "")
		dial_number = request.POST.get("dial_number", "")

		#Track agent activity 
		agent_activity_data = []
		agent_activity_data = get_formatted_agent_activities(request.POST)
		agent_activity_data['user'] = request.user
		agent_activity_data['campaign_name'] = campaign_name
		agent_activity_data["break_type"] = ""
		agent_activity_data["event"] = "Started progressive Pause"
		agent_activity_data["event_time"] = datetime.now()
		create_agentactivity(agent_activity_data)
		return Response({"success:Successfull"})

class StopprogressiveContactStatus(APIView):
	"""
	Stopping the progressive calling and 
	saving the agent activity 
	"""
	def post(self, request):
		campaign_name = request.POST.get("campaign_name", "")
		user = request.POST.get("username", "")
		dial_number = request.POST.get("dial_number", "")

		#Track agent activity 
		agent_activity_data = []
		agent_activity_data = get_formatted_agent_activities(request.POST)
		agent_activity_data['user'] = request.user
		agent_activity_data['campaign_name'] = campaign_name
		agent_activity_data["break_type"] = ""
		agent_activity_data["event"] = "Stopped progressive Pause"
		agent_activity_data["event_time"] = datetime.now()
		create_agentactivity(agent_activity_data)
		return Response({"success:Successfull"})    

class DispoSubmit(LoginRequiredMixin, APIView):
	"""
	This class based view is defined for submit disposition and update customer information.
			"""
	login_url = '/'
	def post(self, request):
		AGENTS = {}
		AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or
				pickle.dumps(AGENTS))
		campaign_name = request.POST.get('campaign')
		call_type = request.POST.get('call_type', '')
		switch_ip = request.POST.get('switch_ip', '')
		autodial_status = request.POST.get('autodial_status','')
		inbound_status = request.POST.get('inbound_status','')
		blended_status = request.POST.get('blended_status','')
		primary_dispo = request.POST.get('primary_dispo','')
		# Track agent activities
		agent_data = get_formatted_agent_activities(request.POST)
		agent_data["user"] = request.user
		agent_data["campaign_name"] = campaign_name
		agent_data["break_type"] = ""
		agent_data["event"] = "Disposition"
		agent_data["event_time"] = datetime.now()
		agent_data["predictive_wait_time"] = "0:0:0"
		agent_data["inbound_wait_time"] = "0:0:0"
		create_agentactivity(agent_data)
		
		status = submit_feedback(request.user,request.POST)
		today = date.today()  # Get today's date
		# Calculate start and end times
		start_date = today  # Midnight at the beginning of the day
		end_date = today + timedelta(days=1)  # Midnight at the beginning of the next day
		start_end_date_filter = Q(created__gte=start_date)&Q(created__lte=end_date)
		total_agentcalls_today = CallDetail.objects.filter(user=request.user).filter(start_end_date_filter).exclude(cdrfeedback=None).count()
		# total_agentcalls_month = CallDetail.objects.filter(user=request.user, created__month=datetime.now().month).exclude(cdrfeedback=None).count()
		total_agentcalls_month = CallDetail.objects.filter(user=request.user, created__month=datetime.now().month).filter(cdrfeedback__id__gte=0).aggregate(id_count=Count('id'))['id_count']
		status["total_agentcalls_today"] = total_agentcalls_today
		status["total_agentcalls_month"] = total_agentcalls_month
		if 'true' in [autodial_status, inbound_status, blended_status]:
			if autodial_status != 'false':
				call_type = 'predictive'
				state = 'Predictive Wait'
			elif inbound_status != 'false':
				call_type = 'inbound'
				state = 'Inbound Wait'
			elif blended_status != 'false':
				call_type = 'blended'
				state = 'Blended Wait'
			AGENTS[request.user.extension]['call_type'] = call_type
			AGENTS[request.user.extension]['state'] = state
			AGENTS[request.user.extension]['event_time'] = datetime.now().strftime('%H:%M:%S')
		else:
			if request.user.extension in AGENTS:
				AGENTS[request.user.extension]['call_type'] = ''
				AGENTS[request.user.extension]['state'] = 'Idle'
				AGENTS[request.user.extension]['event_time'] = datetime.now().strftime('%H:%M:%S')
		AGENTS[request.user.extension]['call_count'] = CallDetail.objects.filter(user__username=request.user.username).filter(start_end_date_filter).count()
		AGENTS[request.user.extension]['dial_number'] = ''
		AGENTS[request.user.extension]['campaign'] = campaign_name
		updated_agent_dict = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
		updated_agent_dict[request.user.extension].update(AGENTS[request.user.extension])
		settings.R_SERVER.set("agent_status", pickle.dumps(updated_agent_dict))
		print("Disp Submit", request.user, request.POST.get("primary_dispo",''), request.POST.get("feedback",{}))
		return Response(status)

class AutoDialApiView(LoginRequiredMixin, APIView):
	"""
	This view is used to do autodial functionality
	"""
	login_url = '/'

	def post(self, request):
		AGENTS = {}
		uuid = request.POST.get("uuid", "")
		switch = request.POST.get("switch", "")
		extension = request.POST.get("extension", "")
		autodial_status = request.POST.get("autodial_status", "")
		predictive_time = request.POST.get("predictive_time", "00:00:00")
		predictive_wait_time = request.POST.get("predictive_wait_time","00:00:00")
		# Track agent activities
		agent_data = get_formatted_agent_activities(request.POST)
		agent_data["user"] = request.user
		agent_data["campaign_name"] = request.POST.get("campaign_name", "")
		agent_data["break_type"] = ""
		if autodial_status == 'true':
			agent_data["event"] = "Predictive Start"
		else:
			agent_data["event"] = "Predictive Stop"
		agent_data["event_time"] = datetime.now()
		agent_data["predictive_time"] = datetime.strptime(predictive_time, '%H:%M:%S').time()
		agent_data["predictive_wait_time"] = datetime.strptime(predictive_wait_time, '%H:%M:%S').time()
		create_agentactivity(agent_data)
		if autodial_status == 'true':
			status = autodial_session(switch,extension=extension,uuid=uuid,
				sip_error=request.POST.get('sip_error','false'))
			if 'success' in status:
				AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
				AGENTS[request.user.extension]['call_type'] = 'predictive'
				AGENTS[request.user.extension]['call_mod'] = 'predictive'
				AGENTS[request.user.extension]['state'] = 'Predictive Wait'
				AGENTS[request.user.extension]['event_time'] = datetime.now().strftime('%H:%M:%S')
				settings.R_SERVER.set("agent_status", pickle.dumps(AGENTS))
			return Response(status)
		if autodial_status == 'false':
			status = autodial_session_hangup(switch,extension=extension,uuid=uuid)
			if 'success' in status:
				AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
				AGENTS[request.user.extension]['call_type'] = ''
				AGENTS[request.user.extension]['state'] = 'Idle'
				AGENTS[request.user.extension]['call_mod'] = ''
				AGENTS[request.user.extension]['event_time'] = datetime.now().strftime('%H:%M:%S')
				settings.R_SERVER.set("agent_status", pickle.dumps(AGENTS))
			return Response(status)

class InboundApiView(LoginRequiredMixin, APIView):
	"""
	This view is used to do autodial functionality
	"""
	login_url = '/'

	def post(self, request):
		AGENTS = {}
		uuid = request.POST.get("uuid", "")
		switch = request.POST.get("switch", "")
		extension = request.POST.get("extension", "")
		inbound_status = request.POST.get("ibc_status", "")
		inbound_time = request.POST.get("inbound_time", "00:00:00")
		inbound_wait_time = request.POST.get("inbound_wait_time","00:00:00")
		# Track agent activities
		agent_data = get_formatted_agent_activities(request.POST)
		agent_data["user"] = request.user
		agent_data["campaign_name"] = request.POST.get("campaign_name", "")
		agent_data["break_type"] = ""
		if inbound_status == 'true':
			agent_data["event"] = "Inbound Start"
		else:
			agent_data["event"] = "Inbound Stop"
		agent_data["event_time"] = datetime.now()
		agent_data["inbound_time"] = datetime.strptime(inbound_time, '%H:%M:%S').time()
		agent_data["inbound_wait_time"] = datetime.strptime(inbound_wait_time, '%H:%M:%S').time()
		create_agentactivity(agent_data)
		if inbound_status == 'true':
			status = autodial_session(switch,extension=extension,uuid=uuid,
				sip_error=request.POST.get('sip_error','false'))
			if 'success' in status:
				AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
				AGENTS[request.user.extension]['call_type'] = 'Inbound'
				AGENTS[request.user.extension]['state'] = 'Inbound Wait'
				settings.R_SERVER.set("agent_status", pickle.dumps(AGENTS))
			return Response(status)
		if inbound_status == 'false':
			status = autodial_session_hangup(switch,extension=extension,uuid=uuid)
			if 'success' in status:
				AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
				AGENTS[request.user.extension]['call_type'] = ''
				AGENTS[request.user.extension]['state'] = 'Idle'
				settings.R_SERVER.set("agent_status", pickle.dumps(AGENTS))
			return Response(status)

class BlendedApiView(LoginRequiredMixin, APIView):
	"""
	This view is used to do autodial functionality
	"""
	login_url = '/'

	def post(self, request):
		AGENTS = {}
		uuid = request.POST.get("uuid", "")
		switch = request.POST.get("switch", "")
		extension = request.POST.get("extension", "")
		blended_status = request.POST.get("blndd_status", "")
		blended_time = request.POST.get("blended_time", "0:0:0")
		blended_wait_time = request.POST.get("blended_wait_time","0:0:0")
		# Track agent activities
		agent_data = get_formatted_agent_activities(request.POST)
		agent_data["user"] = request.user
		agent_data["campaign_name"] = request.POST.get("campaign_name", "")
		agent_data["break_type"] = ""
		if blended_status == 'true':
			agent_data["event"] = "Blended Mode Start"
		else:
			agent_data["event"] = "Blended Mode Stop"
		agent_data["event_time"] = datetime.now()
		agent_data["blended_time"] = datetime.strptime(blended_time, '%H:%M:%S').time()
		agent_data["blended_wait_time"] = datetime.strptime(blended_wait_time, '%H:%M:%S').time()
		create_agentactivity(agent_data)
		if blended_status == 'true':
			status = autodial_session(switch,extension=extension,uuid=uuid,
				sip_error=request.POST.get('sip_error','false'))
			if 'success' in status:
				AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
				AGENTS[request.user.extension]['call_type'] = 'blended'
				AGENTS[request.user.extension]['state'] = 'Blended Wait'
				settings.R_SERVER.set("agent_status", pickle.dumps(AGENTS))
			return Response(status)
		if blended_status == 'false':
			status = autodial_session_hangup(switch,extension=extension,uuid=uuid)
			if 'success' in status:
				AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
				AGENTS[request.user.extension]['call_type'] = ''
				AGENTS[request.user.extension]['state'] = 'Idle'
				settings.R_SERVER.set("agent_status", pickle.dumps(AGENTS))
			return Response(status)         

class NdncListAPIView(LoginRequiredMixin, APIView):
	"""
	This view is used to show list of ndnc
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "ndnc/ndnc.html"

	def get(self, request):
		ndnc = NdncDeltaUpload.objects.all()
		return Response({'request':request, 'can_read': True, 'can_create':True,
			'ndnc_records': ndnc, 'can_delete':True, 'ndnc_list': list(ndnc.values_list("id", flat=True))})

	def post(self, request):
		form = NdncDeltaUploadSerializer(data=request.data)
		if form.is_valid():
			form.save()
		return Response({"msg":"ndnc uploaded"})

@method_decorator(check_read_permission, name='get')
class DNCListAPIView(LoginRequiredMixin, APIView):
	"""
	This view is used to show list of ndnc
	"""
	login_url = '/'
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "ndnc/dnc.html"

	def get(self, request, **kwargs):
		page_info = data_for_pagination(request)
		if page_info["search_by"] and page_info["column_name"]:
			if page_info["column_name"] == "campaign":
				dnc = DNC.objects.filter(campaign__name__istartswith=page_info["search_by"])
			else:
				dnc = DNC.objects.filter(**{page_info["column_name"]+"__istartswith": page_info["search_by"]})
		else:
			dnc = DNC.objects.all()

		dnc_list = list(dnc.values_list("id", flat=True))
		active_camp = list(Campaign.objects.filter(status='Active').values('id','slug'))
		dnc = get_paginated_object(dnc, page_info["page"], page_info["paginate_by"])
		paginate_by_columns = (('numeric', 'Numeric'),
			('campaign', 'Campaign'),
			('status', 'Status'),
			('global_dnc', 'Global Dnc'),
			('dnc_end_date','Dnc End Date'),
			)
		context ={'request':request, 'queryset': dnc, 'campaign_list':active_camp,
		'dnc_list':dnc_list, "paginate_by_columns":paginate_by_columns}

		camp_name, active_camp, noti_count = get_active_campaign(request)
		context = {**context, **kwargs['permissions'], **page_info}
		context["noti_count"] = noti_count
		if request.is_ajax():
			data = render_to_string("ndnc/dnc_table.html", context)
			context = {}
			context["data"] = data
			return JsonResponse(context)
		else:
			return Response(context)

	def post(self, request):
		try:
			dnc_file = request.FILES.get("uploaded_file", "")
			dnc_columns = ['numeric', 'global_dnc','dnc_end_date']
			if dnc_file:
				if dnc_file.size <= 1:
					response_data = {}
					response_data["column_err_msg"] = 'File must not be empty'
					response_data["column_id"] = "#empty-data"
				else:
					if dnc_file.name.endswith('.csv'):
						data = pd.read_csv(dnc_file, na_filter=False,  dtype = {"numeric" : "str","global_dnc" : "str","dnc_end_date":"str"})
					else:
						data = pd.read_excel(dnc_file)
						data = data.replace(np.NaN, "")
					column_names = data.columns.tolist() 
					valid = all(elem in column_names for elem in dnc_columns)
					if valid:
						response_data = validate_uploaded_dnc(data)
					else:
						response_data = {}
						response_data["column_err_msg"] = 'File must contains these '+','.join(dnc_columns)+' columns'
						response_data["column_id"] = "#dnc-file-error"
			return JsonResponse(response_data)
		except Exception as e:
			print(e)
			
class DNCCreateModifyApiView(APIView):
	"""
	Dnc contact create and edit 
	"""
	login_url = '/'

	def get(self,request):
		dnc_obj = DNC.objects.filter(pk=request.GET.get('pk',0))
		if dnc_obj:
			dnc_data = DNCUpdateSerializer(dnc_obj[0]).data
			return Response(dnc_data)
		return Response({'error':'Requested Dnc number is removed or not found'},status=HTTP_404_NOT_FOUND)

	def post(self,request):
		numeric = request.data.get('numeric')
		if not DNC.objects.filter(numeric=numeric).exists():
			dnc_serializer = DNCUpdateSerializer(data=request.data)
			if dnc_serializer.is_valid():
				dnc_obj = dnc_serializer.save()
				if not dnc_obj.global_dnc:
					campaign = list(dnc_obj.campaign.all().values_list("name", flat=True))
					temp_contact_data = TempContactInfo.objects.filter(numeric=dnc_obj.numeric, campaign__in=campaign)
				else:
					temp_contact_data = TempContactInfo.objects.filter(numeric=dnc_obj.numeric)
				temp_contact_id = temp_contact_data.values_list("id",flat=True)
				Contact.objects.filter(Q(id__in=temp_contact_id)|Q(numeric=dnc_obj.numeric)).update(status="Dnc")
				temp_contact_data.delete()
				return Response({"success":"Dnc created successfully"})
		return Response({"error":"this number already present in dnc"})

	def put(self,request):
		dnc_obj = DNC.objects.filter(pk=request.data.get('pk',0))
		if dnc_obj:
			dnc_serializer = DNCUpdateSerializer(dnc_obj[0],data=request.data)
			if dnc_serializer.is_valid():
				dnc_obj = dnc_serializer.save()
				if dnc_obj.status == 'Active':
					if not dnc_obj.global_dnc:
						campaign = list(dnc_obj.campaign.all().values_list("name", flat=True))
						temp_contact_data = TempContactInfo.objects.filter(numeric=dnc_obj.numeric, campaign__in=campaign)
					else:
						temp_contact_data = TempContactInfo.objects.filter(numeric=dnc_obj.numeric)
					temp_contact_id = temp_contact_data.values_list("id",flat=True)
					Contact.objects.filter(Q(id__in=temp_contact_id)|Q(numeric=dnc_obj.numeric)).update(status="Dnc")
					temp_contact_data.delete()
				return Response({"success":"Dnc updated successfully"})


class DNCUploadApiView(APIView):
	"""
	Uploading the ndnc contacts with this view
	"""
	def post(self, request):
		proper_file = request.POST.get("proper_file", "")
		improper_file = request.POST.get("improper_file", "")
		cwd = settings.BASE_DIR
		if request.POST.get("perform_upload", ""):
			if proper_file.endswith('.csv'):
				data = pd.read_csv(cwd+proper_file, na_filter=False, dtype={"numeric" : "str","dnc_end_date":"str"})
			else:
				#data = pd.read_excel(cwd+proper_file,encoding = "unicode_escape",parse_dates=['dnc_end_date'],converters={'numeric': str})
				data = pd.read_excel(cwd+proper_file, na_filter=False, dtype={"numeric" : "str","dnc_end_date":"str"})

			upload_dnc_nums(data, request.user)
		if proper_file:
			os.remove(cwd+proper_file)
		if improper_file:
			os.remove(cwd+improper_file)
		return Response({"msg": "file removed successfully"})

class AutodialCustomerDetail(APIView):
	"""
	Fetching the autodialing customer details with this view
	"""
	def post(self, request):
		AGENTS = {}
		data = {}
		campaign = request.POST.get("campaign_name", "")
		user = request.POST.get("user_name", "")
		call_time = request.POST.get("call_timestamp", "")[:13]
		dial_number = request.POST.get("dial_number", "")
		contact_id = request.POST.get("contact_id", "")
		dialed_uuid = request.POST.get("dialed_uuid", "")
		agent_data = get_formatted_agent_activities(request.POST)
		agent_data["user"] = request.user
		agent_data["event_time"] = datetime.now()
		agent_data["event"]=request.POST.get("event", "")
		agent_data["campaign_name"] = campaign
		create_agentactivity(agent_data)
		if not contact_id:
			contact_id = 0
		if dial_number and dial_number !="null":
			AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
			AGENTS[request.user.extension]['state'] = 'InCall'
			AGENTS[request.user.extension]['event_time'] = datetime.now().strftime('%H:%M:%S')
			AGENTS[request.user.extension]['dial_number'] = dial_number
			AGENTS[request.user.extension]['call_timestamp'] = request.POST.get("call_timestamp", "")[:13]
			settings.R_SERVER.set("agent_status", pickle.dumps(AGENTS))
			campaign_object = Campaign.objects.get(name=campaign)
			contact = Contact.objects.filter(id=contact_id)
			if contact.exists():
				data = ContactSerializer(contact[0]).data
			else:
				data['numeric']=dial_number
			thirdparty_api_status = False
			dynamic_api = False
			click_for_details = False
			weburl =""
			thirdparty_crm = campaign_object.apicampaign.filter(status='Active')
			if thirdparty_crm.exists():
				thirdparty_crm = thirdparty_crm.first()
				dynamic_obj = thirdparty_crm.dynamic_api
				click_for_details_obj = thirdparty_crm.click_url
				thirdparty_api_status =True
				if dynamic_obj and click_for_details_obj:
					click_for_details = True
					dynamic_api =True
				elif dynamic_obj:
					dynamic_api =True
				elif click_for_details_obj:
					click_for_details = True
				weburl = thirdparty_crm.weburl
			data["thirdparty_api_status"] = thirdparty_api_status
			data['dynamic_api'] = dynamic_api
			data['click_for_details'] = click_for_details
			data["weburl"] = json.dumps(weburl)
			return JsonResponse(data)

def delete_inbound_number(campaign=None, dial_number=None, user=None):
	"""
	deleting the inbondcall if its in any bucket list, eg:callbacks
	"""
	CurrentCallBack.objects.filter(Q(campaign=campaign,numeric = dial_number),Q(user=None)|Q(user='')|Q(user=user)).delete()
	CallBackContact.objects.filter(Q(campaign=campaign,numeric = dial_number),Q(user=None)|Q(user='')|Q(user=user)).delete()
	SnoozedCallback.objects.filter(numeric = dial_number).delete()
	Notification.objects.filter(Q(numeric=dial_number, title__in=['callback','Abandonedcall']), Q(user=None)|Q(user='')|Q(user=user)).update(viewed=True)
	Abandonedcall.objects.filter(Q(campaign=campaign,numeric = dial_number),Q(user=None)|Q(user='')|Q(user=user)).delete()
	contact_data = Contact.objects.filter(campaign=campaign,numeric=dial_number,status__in=['Queued-Callback','Queued-Abandonedcall']).values_list('id',flat=True)
	TempContactInfo.objects.filter(id__in=contact_data).delete()

class InboundCustomerDetail(APIView):
	"""
	Fetching the inbound customer details and 
	showing once the call patched/picked
	"""
	def post(self, request):
		try:
			AGENTS = {}
			contact_info = []
			campaign = request.POST.get("campaign_name", "")
			user = request.POST.get("user_name", "")
			call_time = request.POST.get("call_timestamp", "")[:13]
			dial_number = request.POST.get("dial_number", "")[:10]
			dialed_uuid = request.POST.get("dialed_uuid", "")
			agent_data = get_formatted_agent_activities(request.POST)
			agent_data["user"] = request.user
			agent_data["event_time"] = datetime.now()
			agent_data["event"]=request.POST.get("event", "")
			agent_data["campaign_name"] = campaign
			create_agentactivity(agent_data)
			delete_inbound_number(campaign, dial_number, user)
			if dial_number and dial_number !="null":
				AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
				AGENTS[request.user.extension]['state'] = 'InCall'
				AGENTS[request.user.extension]['dial_number'] = dial_number
				AGENTS[request.user.extension]['call_timestamp'] = request.POST.get("call_timestamp", "")[:13]
				settings.R_SERVER.set("agent_status", pickle.dumps(AGENTS))
				campaign_object = Campaign.objects.get(name=campaign)
				data=customer_detials(campaign,dial_number,campaign_object)
				return JsonResponse(data)
			return JsonResponse({})
		except Exception as e:
			print("error from InboundCustomerDetail.",e)
			return JsonResponse({})     

def get_ingroup_campaign(ingroup_campaign):
	""" 
	Get the ingroup campaign based on the 
	strategy and priority to patch the call
	"""
	strategy = ingroup_campaign.strategy
	phonebook_bucket = PhonebookBucketCampaign.objects.filter(agent_login_count__gt=0,id__in=list(ingroup_campaign.ingroup_campaign.all().values_list("campaign_id",flat=True)))
	if phonebook_bucket.exists():
		if strategy =='3':
			phonebook_bucket = phonebook_bucket.order_by('-agent_login_count')
			return phonebook_bucket.first().id

		phonebook_bucket = phonebook_bucket.values_list("id", flat=True)
		if strategy == '0':
			ingroup_campaign = ingroup_campaign.ingroup_campaign.filter(campaign__id__in=list(phonebook_bucket)).order_by('priority')
			for campaign in ingroup_campaign:
				if campaign.campaign_id in list(phonebook_bucket):
					return campaign.campaign_id
		elif strategy == '1':
			ingroup_campaign =ingroup_campaign.ingroup_campaign.filter(campaign__id__in=list(phonebook_bucket)).order_by('-priority')
			for campaign in ingroup_campaign:
				if campaign.campaign_id in list(phonebook_bucket):
					return campaign.campaign_id
		else:
			ingroup_campaign = ingroup_campaign.ingroup_campaign.filter(campaign__id__in=list(phonebook_bucket)).order_by('?')
		return ingroup_campaign.first().campaign_id
	return None

@csrf_exempt
def inbound_agents_availability(request):
	""" 
	if the request method is a POST request
	get the agent avaliable and to path the call

	"""
	if request.method == 'POST':
		extensions = []
		campaign = ''
		user = ''
		campaign_obj = None
		ibc_popup = ''
		queue_call = ''
		dial_method = {}
		non_office_hrs = False
		skill_routed_status = False
		skill = None
		stickyagent = False
		skill_popup = False
		callback = ""
		cust_status = 'false'
		audio_moh_sound = None
		c_max_wait_time = 25
		no_agent_audio = False
		try:
			AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
			caller_data=json.loads(request.body.decode('utf-8'))
			skill_obj = SkilledRouting.objects.filter(skill_id__did__contains = caller_data["caller_id"],status='Active')
			if skill_obj:
				campaign_obj = skill_obj
				ibc_popup = False
				queue_call = True
				skill_routed_status = True
				skill = skill_obj[0].skills
				skill_popup = skill_obj[0].skill_popup
			else:
				user_obj = User.objects.filter(caller_id = caller_data["caller_id"])
				user_extension = None
				if user_obj.exists():
					user_extension = user_obj.first().extension
				if user_extension and user_extension in AGENTS.keys():
					campaign = AGENTS[user_extension]['campaign']
					queue_call=False
					if campaign:
						campaign_obj = Campaign.objects.filter(name=campaign)
						dial_method = campaign_obj.first().dial_method
						if dial_method['inbound']:
							trunk = None
							if campaign_obj.first().is_trunk_group and campaign_obj.first().trunk_group:
								trunks = campaign_obj.first().trunk_group.trunks.filter(trunk_id=user_obj.first().trunk_id)
								if trunks.exists():
									trunk = trunks.first().trunk
							else:
								if campaign_obj.first().trunk and campaign_obj.first().trunk_id == user_obj.first().trunk_id:
									trunk = campaign_obj.first().trunk
							if trunk and trunk.status == 'Active':
								ibc_popup = dial_method['ibc_popup']
								user = user_extension
								if ibc_popup:
									if AGENTS[user_extension]['status'] == 'Ready' and AGENTS[user_extension]['state'] not in ['InCall','Predictive Wait','Blended Wait','Inbound Wait']:
										extensions.append(user_extension)
								else:
									if AGENTS[user_extension]['status'] == 'Ready' and AGENTS[user_extension]['state'] not in ['InCall','Predictive Wait']:
										extensions.append(user_extension)
				else:
					ingroup_campaign = InGroupCampaign.objects.filter(caller_id__did__contains=caller_data["caller_id"], status='Active',
						ingroup_campaign__campaign__status='Active')
					campaign_id = None
					if ingroup_campaign.exists():
						ingroup_campaign = ingroup_campaign.first()
						campaign_id = get_ingroup_campaign(ingroup_campaign)
						if campaign_id == None:
							campaign_id = ingroup_campaign.ingroup_campaign.first().campaign_id
					campaign_obj = Campaign.objects.filter(id=campaign_id).prefetch_related()
					# campaign_obj = Campaign.objects.filter(all_caller_id__contains=[str(caller_data["caller_id"])],
					#   dial_method__contains={"inbound":True}).order_by('?')
					if campaign_obj:
						dial_method =campaign_obj.first().dial_method
						campaign = campaign_obj.first().slug
						r_campaigns = pickle.loads(settings.R_SERVER.get("campaign_status") or pickle.dumps(CAMPAIGNS))
						AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))                        
						if dial_method['inbound']:
							queue_call=True
							callback = campaign_obj[0].queued_busy_callback
							ibc_popup = dial_method['ibc_popup']
							stk_obj = StickyAgent.objects.none()
							if dial_method['sticky_agent_map']:
								stk_obj = StickyAgent.objects.filter(campaign_name=campaign_obj[0].name,numeric=caller_data['destination_number'])
							if stk_obj.exists():
								stk_obj = stk_obj.latest('id')
							if dial_method['ibc_popup']:
								queue_call=False
								if stk_obj and stk_obj.agent.extension in AGENTS:
									extension = stk_obj.agent.extension 
									if AGENTS[extension]['status'] == 'Ready' and AGENTS[extension]['state'] not in ['InCall','Predictive Wait','Blended Wait']:
										extensions.append(extension)
								else:
									camp_users=list(campaign_obj.values_list("users", flat=True).exclude(users__isnull=True))
									camp_grp_users = list(campaign_obj.values_list("group__user_group", flat=True).exclude(group__isnull=True))
									user_ids = list(set(camp_grp_users+camp_users))
									users = list(UserVariable.objects.filter(user__id__in = user_ids,
										user__is_active=True).values_list('extension',flat=True))
									if users:
										extensions = []
										if campaign_obj[0].slug in r_campaigns:
											unique_extensions = list(set(r_campaigns[campaign_obj[0].slug]))
											for active_user in users:
												if active_user in unique_extensions:
													if AGENTS[active_user]['status'] == 'Ready' and AGENTS[active_user]['state'] not in ['InCall','Predictive Wait','Blended Wait'] and AGENTS[active_user]['campaign']==campaign:
														extensions.append(active_user)
							else:
								camp_users=list(campaign_obj.values_list("users", flat=True).exclude(users__isnull=True))
								camp_grp_users = list(campaign_obj.values_list("group__user_group", flat=True).exclude(group__isnull=True))
								user_ids = list(set(camp_grp_users+camp_users))
								users = list(UserVariable.objects.filter(user__id__in = user_ids,
									user__is_active=True).values_list('extension',flat=True))
								if users:
									extensions = []
									if campaign_obj[0].slug in r_campaigns:
										unique_extensions = list(set(r_campaigns[campaign_obj[0].slug]))
										for active_user in users:
											if active_user in unique_extensions:
												if AGENTS[active_user]['status'] == 'Ready' and AGENTS[active_user]['state'] not in ['InCall','Predictive Wait','Blended Wait']:
													extensions.append(active_user)
						else:
							if stk_obj:
								if campaign_obj[0].slug in r_campaigns:
									unique_extensions = list(set(r_campaigns[campaign_obj[0].slug]))                                    
									if stk_obj.agent.extension in unique_extensions:
										user=stk_obj.agent.extension
										if AGENTS[user]['status'] == 'Ready' and AGENTS[user]['state'] in ['Inbound Wait','Blended Wait']:
											extensions.append(user)
											stickyagent = True
			if campaign != '':
				settings.R_SERVER.sadd(campaign, caller_data['dialed_uuid'])
			else:
				if skill_obj:
					campaign = skill_obj[0].d_abandoned_camp
			status = fs_set_variables(caller_data['server'],dialed_uuid=caller_data['dialed_uuid'],extension=user,
				campaign=campaign,campaign_obj=campaign_obj,extensions=extensions,queue_call=queue_call,ibc_popup=ibc_popup,
				skill_routed_status=skill_routed_status)
			if 'non_office_hrs' in status and status['non_office_hrs']==True:
				non_office_hrs = True
				extensions=[]
			if ibc_popup and not queue_call:
				inbound_uuids = pickle.loads(settings.R_SERVER.get("inbound_status") or pickle.dumps({}))
				inbound_uuids[caller_data["dialed_uuid"]]=extensions
				settings.R_SERVER.set("inbound_status", pickle.dumps(inbound_uuids))
			return JsonResponse({'extension':extensions,'dial_method':dial_method,'non_office_hrs':non_office_hrs,
				'queue_call':queue_call,"campaign":campaign,'skill_routed_status':skill_routed_status,'skilled_obj':skill,
				"StickyAgent":stickyagent,'skill_popup':skill_popup,'callback':callback,
				'cust_status':status.get('cust_status',False),'no_agent_audio':status.get('no_agent_audio',False),'c_max_wait_time':status.get('c_max_wait_time',25),'audio_moh_sound':status.get('audio_moh_sound',None)})
		except Exception as e:
			print("inbound error",e)
			exc_type, exc_obj, exc_tb = sys.exc_info()
			fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
			print(exc_type, fname, exc_tb.tb_lineno)
			return JsonResponse({'extension':extensions,'dial_method':dial_method,'non_office_hrs':non_office_hrs,
				'queue_call':queue_call,"campaign":campaign,'skill_routed_status':skill_routed_status,'skilled_obj':skill,
				"StickyAgent":stickyagent,'skill_popup':skill_popup,'callback':callback,
				'cust_status':cust_status,'no_agent_audio':no_agent_audio,'c_max_wait_time':c_max_wait_time,'audio_moh_sound':audio_moh_sound})                

class IncomingCallAPIView(APIView):
	"""
	This view is for Incoming Call button action.
	"""
	def post(self, request):
		action = request.POST.get("action","")
		if action == 'reject':
			return JsonResponse({"rejected":"Call Rejected"})
		elif action == 'accept':
			destination_number = request.POST.get("destination_number","")
			session_details = json.loads(request.POST.get('session_details'))
			status = inbound_call(session_details['variable_sip_from_host'],dialed_uuid=session_details['dialed_uuid'],
				extension=request.user.extension,campaign = request.POST.get('campaign_name'),
				unique_uuid = session_details['Unique-ID'],inbound_number=destination_number)
			delete_inbound_number(request.POST.get('campaign_name'), destination_number, request.user)
			if 'success' in status:
				#Track agent activity 
				activity_dict = get_formatted_agent_activities(request.POST)
				activity_dict["user"] = request.user
				activity_dict["event"] = "INCOMING CALL"
				activity_dict["event_time"] = datetime.now()
				activity_dict["campaign_name"] = request.POST.get('campaign_name')
				create_agentactivity(activity_dict)
			return JsonResponse(status)
		return JsonResponse({"error":"some error occured"})

class InboundStickyAgent(APIView):
	"""
	bridge the call to the inbound sticky agent 	
	"""
	def post(self, request):
		switch_ip = request.POST.get('variable_sip_from_host','')
		dialed_uuid = request.POST.get('dialed_uuid','')
		unique_uuid = request.POST.get('Unique-ID','')
		status = inbound_stiky_agent_bridge(switch_ip,dialed_uuid=dialed_uuid,unique_uuid = unique_uuid,extension=request.user.extension)
		return JsonResponse(status)
	
class SetIbcContactId(APIView):
	""" This class is used to set_ibc_contact_id """
	def post(self,request):
		contact_id = request.POST.get('contact_id','')
		switch_ip = request.POST.get('switch_ip','')
		dialed_uuid = request.POST.get('dialed_uuid','')
		ic_number = request.POST.get('ic_number','')
		callmode = request.POST.get('callmode', '')
		campaign_obj=Campaign.objects.filter(id=request.POST.get('campaign_id', ''))
		status = fs_set_ibc_contact_id(switch_ip,ic_number=ic_number,contact_id=contact_id,extension=request.user.extension,
			dialed_uuid=dialed_uuid, callmode=callmode,campaign_obj=campaign_obj)
		if contact_id:
			TempContactInfo.objects.filter(id=contact_id).update(status='Locked')
		prev_selected_contact_id=request.POST.get('prev_selected_contact_id','')
		if prev_selected_contact_id:
			TempContactInfo.objects.filter(id=prev_selected_contact_id).update(status='NotDialed')
		return JsonResponse(status)     

@csrf_exempt
def rec_check_agent_availabilty(request):
	"""
	recersive check the agent avaliable for calls 
	in the queue
	"""
	extensions = []
	campaign = ''
	user = ''
	campaign_obj = None
	ibc_popup = ''
	queue_call = ''
	dial_method = {}
	non_office_hrs = False
	skill_routed_status = False
	skill = None
	stickyagent = False
	skill_popup = False
	callback = ""
	cust_status = 'false'
	audio_moh_sound = None
	c_max_wait_time = 25
	no_agent_audio = False
	try:
		caller_data=json.loads(request.body.decode('utf-8'))
		ingroup_campaign = InGroupCampaign.objects.filter(caller_id__did__contains=caller_data["caller_id"], status='Active',
			ingroup_campaign__campaign__status='Active')
		campaign_id = None
		if ingroup_campaign.exists():
			ingroup_campaign = ingroup_campaign.first()
			campaign_id = get_ingroup_campaign(ingroup_campaign)
			if campaign_id == None:
				campaign_id = ingroup_campaign.ingroup_campaign.first().campaign_id
		campaign_obj = Campaign.objects.filter(id=campaign_id).prefetch_related()
		# campaign_obj = Campaign.objects.filter(all_caller_id__contains=[str(caller_data["caller_id"])],
		#   dial_method__contains={"inbound":True}).order_by('?')
		if campaign_obj:
			dial_method =campaign_obj.first().dial_method
			campaign = campaign_obj.first().slug
			r_campaigns = pickle.loads(settings.R_SERVER.get("campaign_status") or pickle.dumps(CAMPAIGNS))
			AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))                        
			if dial_method['inbound']:
				queue_call=True
				callback = campaign_obj[0].queued_busy_callback
				ibc_popup = dial_method['ibc_popup']
				stk_obj = StickyAgent.objects.none()
				if dial_method['sticky_agent_map']:
					stk_obj = StickyAgent.objects.filter(campaign_name=campaign_obj[0].name,numeric=caller_data['destination_number'])
				if stk_obj.exists():
					stk_obj = stk_obj.latest('id')
				if dial_method['ibc_popup']:
					queue_call=False
					if stk_obj and stk_obj.agent.extension in AGENTS:
						extension = stk_obj.agent.extension 
						if AGENTS[extension]['status'] == 'Ready' and AGENTS[extension]['state'] not in ['InCall','Predictive Wait','Blended Wait']:
							extensions.append(extension)
					else:
						camp_users=list(campaign_obj.values_list("users", flat=True).exclude(users__isnull=True))
						camp_grp_users = list(campaign_obj.values_list("group__user_group", flat=True).exclude(group__isnull=True))
						user_ids = list(set(camp_grp_users+camp_users))
						users = list(UserVariable.objects.filter(user__id__in = user_ids,
							user__is_active=True).values_list('extension',flat=True))
						if users:
							extensions = []
							if campaign_obj[0].slug in r_campaigns:
								unique_extensions = list(set(r_campaigns[campaign_obj[0].slug]))
								for active_user in users:
									if active_user in unique_extensions:
										if AGENTS[active_user]['status'] == 'Ready' and AGENTS[active_user]['state'] not in ['InCall','Predictive Wait','Blended Wait'] and AGENTS[active_user]['campaign']==campaign:
											extensions.append(active_user)
				else:
					camp_users=list(campaign_obj.values_list("users", flat=True).exclude(users__isnull=True))
					camp_grp_users = list(campaign_obj.values_list("group__user_group", flat=True).exclude(group__isnull=True))
					user_ids = list(set(camp_grp_users+camp_users))
					users = list(UserVariable.objects.filter(user__id__in = user_ids,
						user__is_active=True).values_list('extension',flat=True))
					if users:
						extensions = []
						if campaign_obj[0].slug in r_campaigns:
							unique_extensions = list(set(r_campaigns[campaign_obj[0].slug]))
							for active_user in users:
								if active_user in unique_extensions:
									if AGENTS[active_user]['status'] == 'Ready' and AGENTS[active_user]['state'] not in ['InCall','Predictive Wait','Blended Wait']:
										extensions.append(active_user)
			else:
				if stk_obj:
					if campaign_obj[0].slug in r_campaigns:
						unique_extensions = list(set(r_campaigns[campaign_obj[0].slug]))                                    
						if stk_obj.agent.extension in unique_extensions:
							user=stk_obj.agent.extension
							if AGENTS[user]['status'] == 'Ready' and AGENTS[user]['state'] in ['Inbound Wait','Blended Wait']:
								extensions.append(user)
								stickyagent = True
		status = check_ibc_cust_status(caller_data['server'],dialed_uuid=caller_data['dialed_uuid'],campaign_obj=campaign_obj)
		timestamp = int(caller_data['intiate_time'])/1000000
		diff_in_seconds = diff_time_in_seconds(timestamp)
		if diff_in_seconds < status.get('c_max_wait_time',25):
			inbound_uuids = pickle.loads(settings.R_SERVER.get("inbound_status") or pickle.dumps({}))
			if caller_data["dialed_uuid"] in inbound_uuids:
				if extensions and not queue_call and status['cust_status']:
					inbound_uuids[caller_data["dialed_uuid"]]=extensions
					settings.R_SERVER.set("inbound_status", pickle.dumps(inbound_uuids))
				else:
					extensions=[]
			else:
				extensions=[]
				status['cust_status']='uuid_not_exist'
		else:
			status['cust_status']='timeout'
			extensions=[]           
		return JsonResponse({'extension':extensions,'cust_status':status.get('cust_status',False),
				'no_agent_audio':status.get('no_agent_audio',False),'c_max_wait_time':status.get('c_max_wait_time',25),
				'audio_moh_sound':status.get('audio_moh_sound',None)})
	except Exception as e:
		print("check_agent_availabilty",e)
		return JsonResponse({'extension':extensions,'cust_status':status['cust_status'],'no_agent_audio':no_agent_audio,'c_max_wait_time':c_max_wait_time,'audio_moh_sound':audio_moh_sound})


class ParkCallAPIView(APIView):
	"""
	This view is used to implement park call
	"""

	def post(self, request):
		status = fs_park_call(request.POST.get('sip_server'),dialed_uuid=request.POST.get('dialed_uuid'),session_uuid=request.POST.get('Unique-ID')
			,park_status=request.POST.get('park_status'))

		if 'success' in status:
			#Track agent activity 
			activity_dict =dummy_agent_activity()
			activity_dict["user"] = request.user
			if request.POST.get('park_status') == 'true':
				activity_dict["event"] = "PARK CALL"
			else:
				activity_dict["event"] = "RESUME CALL"
			activity_dict["event_time"] = datetime.now()
			activity_dict["campaign_name"] = request.POST.get('campaign_name')
			create_agentactivity(activity_dict)
		return JsonResponse({"success":"successfully"})


class SendDTMFAPIView(APIView):
	"""
	This view used to send the dtmf to the freeswitch
	"""
	def post(self,request):
		status = fs_send_dtmf(request.POST.get('sip_server'),dialed_uuid=request.POST.get('dialed_uuid'),session_uuid=request.POST.get('Unique-ID')
			,dtmf_digit=request.POST.get('dtmf_digit'))
		if status and 'success' in status:
			return JsonResponse({'success':'Dtmf inserted successfully'})
		else:
			return JsonResponse({'error':'Dtmf Failed to insert'})

class TransferParkCallAPIView(APIView):
	"""
	This view is used to implement park call
	"""

	def post(self, request):
		status = fs_transferpark_call(request.POST.get('sip_server'),dialed_uuid=request.POST.get('dialed_uuid')
			,transfer_call_status=request.POST.get('transfer_call_status'),session_uuid=request.POST.get('session_uuid'), conf_uuids=request.POST.get('conf_uuids'))
		if 'success' in status:
			pass
		return JsonResponse({"success":"successfully"})

class TransferAgentCallAPIView(APIView):
	"""
	This view is used to implement transfer call
	"""

	def post(self, request):
		transfer_number = request.POST.get("transfer_to_agent_number", "")
		transfer_type = request.POST.get("transfer_type","")
		activity_dict =dummy_agent_activity()
		activity_dict["user"] = request.user
		activity_dict["event_time"] = datetime.now()
		activity_dict["campaign_name"] = request.POST.get('campaign_name')
		activity_dict['event'] = request.POST.get('event')
		transfer_mode = request.POST.get("transfer_mode","")
		create_agentactivity(activity_dict)
		status = fs_transfer_agent_call(request.POST.get("variable_sip_from_host"),campaign=request.POST.get("campaign_name")
			,dialed_uuid=request.POST.get("dialed_uuid",""),transfer_from_agent_uuid=request.POST.get("transfer_from_agent_uuid",""),
			unique_uuid=request.POST.get("Unique-ID",""),extension=request.user.extension,caller_id=request.POST.get('caller_id',""),
			dial_number=transfer_number,transfer_type=transfer_type,transfer_mode=transfer_mode,
			transfer_from_agent_number=request.POST.get('transfer_from_agent_number',""))
		return JsonResponse(status)

class TransferAgentCallHangupAPIView(APIView):
	"""
	Hangup the transfer agent calls 
	"""
	def post(self, request):
		event = request.POST.get('event')
		activity_dict =dummy_agent_activity()
		activity_dict["user"] = request.user
		activity_dict["event_time"] = datetime.now()
		activity_dict["campaign_name"] = request.POST.get('campaign_name')
		activity_dict['event'] = event
		create_agentactivity(activity_dict)
		if event == 'Transfer Hangup':
			hangup_uuid = request.POST.get("transfer_uuid","")
		else:
			hangup_uuid = request.POST.get("conference_num_uuid","")
		status = fs_transferhangup_call(request.POST.get("variable_sip_from_host"),transfer_uuid=hangup_uuid)
		return JsonResponse(status)

class TransferCallAPIView(APIView):
	"""
	Transfer the call to the agent 
	"""
	def post(self, request):
		transfer_uuid = request.POST.get("transfer_uuid", "")
		dialed_uuid = request.POST.get("dialed_uuid", "")
		transfer_number = request.POST.get("transfer_number","")
		transfer_mode = request.POST.get("transfer_mode","")
		contact_id = request.POST.get("contact_id","")
		activity_dict =dummy_agent_activity()
		activity_dict["user"] = request.user
		activity_dict["event_time"] = datetime.now()
		activity_dict["campaign_name"] = request.POST.get('campaign_name')
		activity_dict['event'] = request.POST.get('event')
		create_agentactivity(activity_dict)
		status = fs_transfer_call(request.POST.get("variable_sip_from_host"),transfer_uuid=transfer_uuid,dialed_uuid=dialed_uuid,
			transfer_number=transfer_number,transfer_mode=transfer_mode)
		return JsonResponse(status)

class MergeCallAPIView(APIView):
	"""
	This view is used to merge calls while transfering
	"""
	def post(self, request):
		extension = request.user.extension
		conference_num_uuid = request.POST.get("conference_num_uuid", "")
		dialed_uuid = request.POST.get("dialed_uuid", "")
		transfer_mode = request.POST.get("transfer_mode","")
		session_uuid = request.POST.get("Unique-ID","")
		conf_uuids=request.POST.get('conference_uuids','')
		activity_dict =dummy_agent_activity()
		activity_dict["user"] = request.user
		activity_dict["event_time"] = datetime.now()
		activity_dict["campaign_name"] = request.POST.get('campaign_name')
		activity_dict['event'] = request.POST.get('event')
		create_agentactivity(activity_dict)
		status = fs_transfer_call(request.POST.get("variable_sip_from_host"),conference_num_uuid=conference_num_uuid,dialed_uuid=dialed_uuid
			,transfer_mode=transfer_mode,session_uuid =session_uuid,extension=extension,conf_uuids=conf_uuids)        
		status={"success":"successfully"}
		return JsonResponse(status)

class GetAvailableAgentsAPIView(APIView):
	"""
	This view is used get available agents from particular campaign
	"""

	def post(self, request):
		campaign = request.POST.get("campaign")
		agent_extension = []
		all_agents = pickle.loads(settings.R_SERVER.get("agent_status"))
		for extension in all_agents:
			if extension != request.user.extension:
				rule = [all_agents[extension]["state"] == "Idle",
						all_agents[extension]["status"] == "Ready",
						all_agents[extension]["campaign"] == campaign
				]
				if all(rule):
					agent_extension.append(extension)

		user_list = UserVariable.objects.filter(
			extension__in=agent_extension).values("user__username", "extension")
		
		available_agents = []
		campaign_obj = Campaign.objects.get(slug=campaign)
		for user in user_list:
			available_agents.append({"agent_extension": user["extension"],
				"username": user["user__username"]})
		return JsonResponse({"available_agents": available_agents,'dialtimeout':campaign_obj.campaign_variable.dialtimeout})

class WebrtcSessionSetVar(APIView):
	"""
	webrtc session enable and seting into redis
	"""
	def post(self, request):
		AGENTS = {}
		session_details = request.POST.get("variable_sip_from_host")
		fs_set_variables(request.POST.get("variable_sip_from_host"),campaign=request.POST.get("campaign_name")
			,dialed_uuid=request.POST.get("Unique-ID"),extension=request.user.extension,call_type='webrtc')
		if request.POST.get('update_autodial_session',False):
			autodial_session(request.POST.get("variable_sip_from_host"), extension=request.user.extension,uuid=request.POST.get("Unique-ID"), sip_error='false')
		AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
		AGENTS[request.user.extension]['dialerSession_uuid'] = request.POST.get("Unique-ID")
		settings.R_SERVER.set("agent_status", pickle.dumps(AGENTS))
		return JsonResponse({"success":"successfully"})

class InternalTransferCallHangup(APIView):
	"""
	Internal transfer call hangup 
	"""
	def post(self, request):
		uuid = request.POST.get("uuid", "")
		status = fs_internal_transferhangup_call(request.POST.get("switch"),uuid=uuid)
		return JsonResponse(status)

class TransferCustomerDetail(APIView):

	""" Transfer the customer detials with the transfer call """
	def post(self, request):
		contact_info = []
		AGENTS = {}
		AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or
				pickle.dumps(AGENTS))
		contact_info = []
		campaign = request.POST.get("campaign_name", "")
		user = request.POST.get("extension", "")
		transfer_agent = request.POST.get("transfer_agent", "")
views_110325.py
Displaying views_110325.py.
