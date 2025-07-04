#import logging
import os
import ntpath
import json
import base64
import time
import re
import pandas as pd
from datetime import datetime
from django.http import HttpResponseRedirect, HttpResponse
from django.db import transaction, connections
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.apps import apps
from django.conf  import settings
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.db.models import Q, F, Sum, TimeField, Value, Count, Prefetch, F
from django.db.models.functions import Cast, Coalesce
from django.contrib.postgres.fields.jsonb import KeyTransform
import csv
import xlsxwriter
from django.core.files import File
import dateutil.parser
from datetime import datetime, date,timedelta
import datetime as dt
import itertools
from .models import (CampaignSchedule, AgentActivitybk,Switch, DialTrunk, User, Group,
	Disposition, AudioFile, PauseBreak, UserVariable, RelationTag,PhonebookBucketCampaign,
	UserRole, Script, User, AgentActivity, Campaign, DiallerEventLog, CallDetail,DNC,CSS, CdrFeedbck,
	CallBackContact, CurrentCallBack, SnoozedCallback, Abandonedcall, ThirdPartyApiUserToken, SMSTemplate, SMSGateway,
	DiaTrunkGroup,EmailScheduler,AdminLogEntry, ReportColumnVisibility, CallRecordingFeedback, InGroupCampaign, SkilledRouting,
	EmailGateway,CampaignVariable, SkilledRoutingCallerid,Daemons,Holidays,PasswordManagement,PasswordChangeLogs)
from flexydial.constants import (Status,CALL_MODE, CAMPAIGN_STRATEGY_CHOICES, DIAL_RATIO_CHOICES, CDR_DOWNLOAD_COl, QC_FEEDBACK_COL, LAN_REPORT_COL, IC_REPORT_COL,PasswordChangeType)

from .serializers import (GroupSerializer,CallDetailSerializer, CallBackContactSerializer,
	SetCallBackContactSerializer, DncSerializer, CallDetailReportSerializer, AgentActivityReportSerializer, CurrentCallBackSerializer, AbandonedcallSerializer, CallRecordingFeedbackSerializer)
from flexydial.views import (get_paginated_object, data_for_pagination, sendSMS, create_admin_log_entry,user_hierarchy_func)
import numpy as np
import socket, errno, xmlrpc.client
import sys
from crm.models import (TempContactInfo, Contact, ContactInfo,
	Phonebook, CrmField, DownloadReports, LeadBucket, AlternateContact)
from crm.serializers import (TempContactInfoSerializer, ContactSerializer, SetContactSerializer, ContactListSerializer, AlternateContactSerializer)
cwd = os.path.join(settings.BASE_DIR, 'static/')
from .constants import four_digit_number
import re
import uuid
import pickle
from shutil import make_archive, rmtree
import calendar
import random
from django.core.mail import EmailMessage,EmailMultiAlternatives, get_connection
import xlwt
from xlwt import Workbook
import xlrd
from xlutils.copy import copy
import subprocess
from importlib import import_module
class Echo(object):
	def write(self, value):
		return value

def diff_time_in_seconds(timestamp):
	""" to get time diff in seconds """
	current_time = dt.datetime.now()
	timestring = dt.datetime.fromtimestamp(timestamp)
	diff_in_seconds = (current_time - timestring).seconds
	return diff_in_seconds

def check_non_admin_user(user):
	""" check user is adim or not """
	if (user.is_superuser or (user.user_role and user.user_role.access_level == 'Admin')):
		return False
	return True

def get_temp_contact(user, campaign, portfolio=False):
	""" Get temp contact data"""
	temp_contact = None
	if not portfolio:
		if TempContactInfo.objects.filter(campaign=campaign, status='NotDialed').exists():
			temp_contact = TempContactInfo.objects.filter(campaign=campaign, status='NotDialed').order_by('priority','modified_date').first()
			temp_contact.status = 'Locked'
			temp_contact.save()
	else:
		if TempContactInfo.objects.filter(user=user, campaign=campaign, status='NotDialed').exists():
			temp_contact = TempContactInfo.objects.filter(user=user, campaign=campaign, status='NotDialed').order_by('priority','modified_date').first()
			temp_contact.status = 'Locked'
			temp_contact.save()
		elif TempContactInfo.objects.filter(Q(campaign=campaign, status='NotDialed'),(Q(user='')|Q(user=None))).exists():
			temp_contact = TempContactInfo.objects.filter(Q(campaign=campaign, status='NotDialed'),(Q(user='')|Q(user=None))).order_by('priority','modified_date').first()
			temp_contact.status = 'Locked'
			temp_contact.save()
	return temp_contact

def get_agent_status(extension,full_key = False):
	if full_key:
		return pickle.loads(settings.R_SERVER.get(extension) or pickle.dumps({}))
	return pickle.loads(settings.R_SERVER.get("flexydial_"+extension) or pickle.dumps({}))

def get_statKey(key):
	return pickle.loads(settings.R_SERVER.get(key) or pickle.dumps([]))

def update_statKey(key,val):
	print('nothig printing')
	return settings.R_SERVER.set(key, pickle.dumps(val),ex=settings.REDIS_KEY_EXPIRE_IN_SEC)

def remove_redis_stat_val(stat_dict,key,extension):
	if extension in stat_dict:
		stat_dict.remove(extension)
		update_statKey(key,stat_dict)

def default_agent_status(extension,agent_dict):
	if extension in agent_dict:
		agent_dict = agent_dict[extension]
	if 'username' not in agent_dict:
		username = first_name = last_name = ""
		user_var = UserVariable.objects.filter(extension=extension).first()
		if user_var:
			username = user_var.user.username
			first_name = user_var.user.first_name
			last_name = user_var.user.last_name
		print('Log::default::username_is_missing::',extension,username)
		agent_dict['username'] = username
		agent_dict['name'] = first_name + ' ' + last_name
	agent_dict['login_status'] = True if "login_status" not in agent_dict else agent_dict['login_status']
	agent_dict['campaign'] = '' if "campaign" not in agent_dict else agent_dict['campaign']
	agent_dict['dialer_login_status'] = False if "dialer_login_status" not in agent_dict else agent_dict['dialer_login_status']
	agent_dict['dialer_login_time'] = '' if "dialer_login_time" not in agent_dict else agent_dict['dialer_login_time']
	agent_dict['status'] = 'NotReady' if "status" not in agent_dict else agent_dict['status']
	agent_dict['state'] = '' if "state" not in agent_dict else agent_dict['state']
	agent_dict['event_time'] = '' if "event_time" not in agent_dict else agent_dict['event_time']
	agent_dict['call_type'] = '' if "call_type" not in agent_dict else agent_dict['call_type']
	agent_dict['dial_number'] = '' if "dial_number" not in agent_dict else agent_dict['dial_number']
	agent_dict['call_timestamp'] = '' if "call_timestamp" not in agent_dict else agent_dict['call_timestamp']
	agent_dict['extension'] = extension if "extension" not in agent_dict else agent_dict['extension']
	agent_dict['dialerSession_uuid'] = '' if "dialerSession_uuid" not in agent_dict else agent_dict['dialerSession_uuid']
	agent_dict['screen'] = 'AgentScreen' if "screen" not in agent_dict else agent_dict['screen']
	agent_dict['call_count'] = 0 if "call_count" not in agent_dict else agent_dict['call_count']
	agent_dict['login_time'] = '' if "login_time" not in agent_dict else agent_dict['login_time']
	return agent_dict

def update_redis_stat_key(stat_dict, key,extension):
	if extension not in stat_dict:
		stat_dict.append(extension)
		update_statKey(key,stat_dict)

def update_stats_data(updated_agent_dict,extension):
	if extension in updated_agent_dict:
		break_stat = get_statKey('onbreak')
		login_count = get_statKey('login_count')
		dialer_count = get_statKey('dialer_count')
		if updated_agent_dict[extension]['state'].lower() == 'onbreak':
			update_redis_stat_key(break_stat,'onbreak',extension)
			remove_redis_stat_val(login_count,'login_count',extension)
			remove_redis_stat_val(dialer_count,'dialer_count',extension)
		else:
			remove_redis_stat_val(break_stat,'onbreak',extension)
			if updated_agent_dict[extension]['dialer_login_status'] == True:
				update_redis_stat_key(dialer_count,'dialer_count',extension)
				remove_redis_stat_val(login_count,'login_count',extension)
			else:
				update_redis_stat_key(login_count,'login_count',extension)
				remove_redis_stat_val(dialer_count,'dialer_count',extension)
		# on_call_agent = get_statKey("on_call_agent")
		dial_modes = ['progressive','inbound','predictive','preview','manual']
		if updated_agent_dict[extension]['state'] == "InCall" and updated_agent_dict[extension]['dial_number'] and updated_agent_dict[extension]['call_timestamp']!="":
		# 	update_redis_stat_key(on_call_agent,'on_call_agent',extension)
		# else:
		# 	remove_redis_stat_val(on_call_agent,"on_call_agent",extension)
			for dial_mode in dial_modes:
				dial_mode_dict = get_statKey(dial_mode)
				if updated_agent_dict[extension]['call_type'].lower() == dial_mode:
					update_redis_stat_key(dial_mode_dict,dial_mode,extension)
				else:
					remove_redis_stat_val(dial_mode_dict,dial_mode,extension)
		else:
			for dial_mode in dial_modes:
				dial_mode_dict = get_statKey(dial_mode)
				remove_redis_stat_val(dial_mode_dict,dial_mode,extension)

def set_agent_status(extension,agent_dict,delete=False):
	stat_keys = ['onbreak','login_count','dialer_count','progressive','inbound','predictive','preview','manual']
	if delete:
		settings.R_SERVER.delete("flexydial_"+extension)
		for stat in stat_keys:
			stat_dict = get_statKey(stat)
			remove_redis_stat_val(stat_dict,stat,extension)
		return True
	updated_agent_dict = get_agent_status(extension)
	if extension not in updated_agent_dict:
		updated_agent_dict[extension] = {}
	agent_dict = default_agent_status(extension,agent_dict)
	if extension in agent_dict:
		updated_agent_dict[extension].update(agent_dict[extension])
	else:
		updated_agent_dict[extension].update(agent_dict)
	status = settings.R_SERVER.set("flexydial_"+extension, pickle.dumps(updated_agent_dict),ex=settings.REDIS_KEY_EXPIRE_IN_SEC)
	if status!=True:
		print("Log::RedisError:: ",status,updated_agent_dict)
	update_stats_data(updated_agent_dict,extension)
	return status

def get_contact_data(user, campaign_id, campaign):
	"""
	this is the function defined to get the contact data 
	"""	
	contact = []
	phonebook = Phonebook.objects.filter(campaign=campaign_id, status='Active').order_by('priority')
	if Contact.objects.filter(phonebook__in=phonebook, user=user, status='NotDialed').exists():
		contact = Contact.objects.filter(phonebook__in=phonebook, user=user, status='NotDialed').order_by('priority','modified_date').first()
	elif Contact.objects.filter(Q(campaign=campaign, status='NotDialed'),(Q(user='')|Q(user=None))).exists():
		contact = Contact.objects.filter(Q(campaign=campaign, status='NotDialed'),(Q(user='')|Q(user=None))).order_by('priority','modified_date').first()
	return contact

def get_crm_fields_dict(campaign_name):
	""" get the crm fields of a campaign """
	column_dict = {}
	if Campaign.objects.filter(name=campaign_name).exists():
		crm_fields = CrmField.objects.filter(campaign__name=campaign_name)
		if crm_fields.exists():
			crm_field = crm_fields.first()
			sections = sorted(crm_field.crm_fields, key = lambda i: i['section_priority'])
			for section in sections:
				section_fields = sorted(section["section_fields"], key = lambda f: f['priority'])
				section_key = section["db_section_name"]
				for section_field in section_fields:
					column_dict[section_key+':'+section_field["db_field"]] = section_field["field"]
	return column_dict

def total_list_users(server_ip):
	"""
	this is the function defined fto get the list of users  with the server_ip
	"""	
	campaigns = Campaign.objects.filter(switch__ip_address = server_ip,status="Active")
	camp_grp_users = []
	if campaigns:
		camp_group_id = list(campaigns[0].group.values_list('id',flat=True))
		camp_grp_users = list(User.objects.filter(group__in=camp_group_id).values_list('id',flat=True))
	camp_users = list(campaigns.values_list("users", flat=True).exclude(users__isnull=True))
	users = list(UserVariable.objects.filter(domain__ip_address = server_ip).values_list('user__id',flat=True))
	user_ids = list(set(camp_grp_users+camp_users+users))
	return user_ids

def camp_list_users(camp_name):
	"""
	this is the function defined to get list of user in the campaign 
	"""	
	campaigns = Campaign.objects.filter(name = camp_name)
	camp_grp_users = []
	if campaigns:
		camp_group_id = list(campaigns[0].group.values_list('id',flat=True))
		camp_grp_users = list(User.objects.filter(group__in=camp_group_id).values_list('id',flat=True))
	camp_users = list(campaigns.values_list("users", flat=True).exclude(users__isnull=True))    
	user_ids = list(set(camp_grp_users+camp_users))
	return user_ids

def user_hierarchy(request,camp_name):
	"""
	this is the function defined to get the user reporting hirerarchy
	"""	
	# users = User.objects.exclude(id=request.user.id)
	admin=False
	if request.user.is_superuser or (request.user.user_role and request.user.user_role.access_level == 'Admin'):
		users = User.objects.exclude(id=request.user.id)
		admin = True
	else:
		users = User.objects.filter(id__in=user_hierarchy_func(request.user.id))
	# if request.user.user_role and request.user.user_role.access_level == 'Admin':
	if request.user.is_superuser:
		team_extensions = UserVariable.objects.filter(user__in=users).values_list("extension", flat=True)
	elif admin:
		team_extensions = UserVariable.objects.filter(user__in=users.exclude(is_superuser=True)).values_list("extension", flat=True)
	else:
		camp_users = []
		for campaign in camp_name:
			temp_camp_list_users= camp_list_users(campaign)
			camp_users.extend(temp_camp_list_users)
		total_camp_users = users.filter(Q(id__in=camp_users )| Q( reporting_to = request.user)).prefetch_related(
			'group', 'reporting_to', 'user_role')
		if request.user.user_role.access_level == 'Manager':
			team = users.filter(reporting_to__in = total_camp_users)
			total_camp_users = total_camp_users | team
			total_camp_users = total_camp_users.exclude(user_role__access_level='Admin').exclude(is_superuser=True).distinct()
		elif request.user.user_role.access_level == 'Supervisor':
			total_camp_users = total_camp_users.exclude(user_role__access_level__in=['Admin','Manager']).exclude(is_superuser=True).distinct()
		team_extensions = list(UserVariable.objects.filter(
			user__in=total_camp_users).values_list("extension", flat=True))
	return team_extensions

def user_hierarchy_object(user,camp_name=[]):
	"""
	this is the function defined user hierarcy object data
	"""	
	# users = User.objects.exclude(id=user.id).all()
	if user.is_superuser and user.user_role and user.user_role.access_level == 'Admin':
		admin = True
		users = User.objects.exclude(id=user.id)
	else:
		users = User.objects.filter(id__in=user_hierarchy_func(user.id)).all()
	if user.is_superuser:
		total_camp_users =users
	elif user.user_role and user.user_role.access_level == 'Admin':
		total_camp_users = users.exclude(is_superuser=True)
	else:
		camp_users = []
		for campaign in camp_name:
			temp_camp_list_users= camp_list_users(campaign)
			camp_users.extend(temp_camp_list_users)
		total_camp_users = users.filter(Q(id__in=camp_users )| Q( reporting_to = user)).prefetch_related(
			'group', 'reporting_to', 'user_role')
		if user.user_role.access_level == 'Manager':
			team = users.filter(reporting_to__in = total_camp_users)
			total_camp_users = total_camp_users | team
			total_camp_users = total_camp_users.exclude(user_role__access_level='Admin').exclude(is_superuser=True).distinct()
		elif user.user_role.access_level == 'Supervisor':
			total_camp_users = total_camp_users.exclude(user_role__access_level__in=['Admin','Manager']).exclude(is_superuser=True).distinct()
	return total_camp_users

def freeswicth_server(server_ip):
	"""
	this function is for making connection to the freeswitch 
	by using the campaign ip_address
	"""
	rpc_port = Switch.objects.filter(ip_address=server_ip).first().rpc_port
	SERVER = xmlrpc.client.ServerProxy("http://%s:%s@%s:%s" % (settings.RPC_USERNAME,
			 settings.RPC_PASSWORD,server_ip,rpc_port))
	return SERVER 

def filter_queryset(request,queryset,filter_backends):
	for backend in list(filter_backends):
		queryset = backend().filter_queryset(request, queryset)
	return queryset

def paginate_queryset(request,queryset, paginator):
	if paginator is None:
		return None
	return paginator.paginate_queryset(queryset=queryset, request=request)

def get_paginated_response(data, paginator):
	assert paginator is not None
	return paginator.get_paginated_response(data)

def get_current_users():
	"""this method is used to get all login user details form 
	djjango session
	"""
	active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
	user_id_list = []
	for session in active_sessions:
		data = session.get_decoded()
		user_id_list.append(data.get('_auth_user_id', None))
	# Query all logged in users based on id list
	return User.objects.filter(id__in=user_id_list)


def redirect_user(request, user):
	"""
	This method redirect user to his respective home page
	as per his role or permissions
	"""
	if not user.is_superuser:
		permissions = user.user_role.permissions
		request.session['permissions'] = permissions
		if permissions['dashboard'] == []:
			return HttpResponseRedirect(reverse("agent"))
	if request.POST.get("next",""):
		return HttpResponseRedirect(request.POST.get("next",""))
	return HttpResponseRedirect(reverse("dashboard"))

def set_agentReddis(AGENTS,user):
	"""
	this is the function defined to set the redies data of an agent
	"""	
	if not user.extension in AGENTS:
		AGENTS.update({user.extension:{}})

	AGENTS[user.extension]['username'] = user.username
	AGENTS[user.extension]['name'] = user.first_name + ' ' + user.last_name
	AGENTS[user.extension]['login_status'] = True
	AGENTS[user.extension]['campaign'] = ''
	AGENTS[user.extension]['dialer_login_status'] = False
	AGENTS[user.extension]['dialer_login_time'] = ''
	AGENTS[user.extension]['status'] = 'NotReady'
	AGENTS[user.extension]['state'] = ''
	AGENTS[user.extension]['event_time'] = ''
	AGENTS[user.extension]['call_type'] = ''
	AGENTS[user.extension]['dial_number'] = ''
	AGENTS[user.extension]['call_timestamp'] = ''
	AGENTS[user.extension]['extension'] = user.extension
	AGENTS[user.extension]['dialerSession_uuid'] = ''
	return AGENTS

def get_object(pk, app_name, model_name):
	"""
	This method is used to get object from particular model 
	"""
	model = apps.get_model(app_label=app_name, model_name=model_name)
	return get_object_or_404(model, pk=pk)

def get_user_group(user):
	"""
	this is the function defined to get the user group 
	"""	
	if user.is_superuser:
		groups = Group.objects.all()
	else:
		groups = Group.objects.filter(created_by=user)
		if user.user_role.access_level.lower() == "admin":
			team = User.objects.filter(reporting_to=user)
			manager_group = Group.objects.filter(created_by__in=team)
			groups = manager_group | groups
	return groups

def get_user_switch(user):
	"""
	this is the function defined to get the user switch 
	"""	
	if user.is_superuser:
		switch = Switch.objects.all()
	else:
		switch = Switch.objects.filter(created_by=user)
		if user.user_role.access_level.lower() == "admin":
			team = User.objects.filter(reporting_to=user)
			switch = Switch.objects.filter(created_by__in=team) | switch
	return switch

def get_user_dialtrunk(user):
	"""
	this is the function defined user assigned dialed trunk 
	"""	
	if user.is_superuser:
		dial_trunk = DialTrunk.objects.all()
	else:
		dial_trunk = DialTrunk.objects.filter(created_by=user)
		if user.user_role.access_level.lower() == "admin":
			team = User.objects.filter(reporting_to=user)
			dial_trunk = DialTrunk.objects.filter(created_by__in=team) | dial_trunk
	return dial_trunk 

def get_user_disposition(user):
	"""
	this is the function defined for dispostion created by that user 
	"""	
	if user.is_superuser:
		disposition = Disposition.objects.all()
	else:
		disposition = Disposition.objects.filter(created_by=user)
		if user.user_role.access_level.lower() == "admin":
			team = User.objects.filter(reporting_to=user)
			disposition = Disposition.objects.filter(created_by__in=team) | disposition
	return disposition 

def get_user_pausebreak(user):
	"""
	this is the function defined for diapostion created by that user 
	"""	
	if user.is_superuser:
		pausebreak = PauseBreak.objects.all()
	else:
		pausebreak = PauseBreak.objects.filter(created_by=user)
		if user.user_role.access_level.lower() == "admin":
			team = User.objects.filter(reporting_to=user)
			pausebreak = PauseBreak.objects.filter(created_by__in=team) | pausebreak
	return pausebreak 

def get_user_campaignschedule(user):
	"""
	this is the function defined forshoft time created by that user
	"""	
	if user.is_superuser:
		campaign_schedule = CampaignSchedule.objects.all()
	else:
		campaign_schedule = CampaignSchedule.objects.filter(created_by=user)
		if user.user_role.access_level.lower() == "admin":
			team = User.objects.filter(reporting_to=user)
			campaign_schedule = CampaignSchedule.objects.filter(created_by__in=team) | campaign_schedule
	return campaign_schedule 

def get_model_data(user, app_label, model_name):
	"""
	this is the function defined for showing the model data 
	"""	
	model = apps.get_model(app_label=app_label, model_name=model_name)
	if user.is_superuser:
		queryset = model.objects.all()
	else:
		queryset = model.objects.filter(created_by=user)
		if user.user_role.access_level.lower() == "admin":
			team = User.objects.filter(reporting_to=user)
			queryset = model.objects.filter(created_by__in=team) | queryset
	return queryset 

def validate_third_party_token(token, ip_address):
	"""
	this is the function defined for validating the thirdparty token 
	"""	
	token_queryset = ThirdPartyApiUserToken.objects.filter(token=token)
	ip_user = ThirdPartyApiUserToken.objects.filter(last_ip_addresss=ip_address)
	if token_queryset:
		token_queryset = token_queryset.first()
		domain = token_queryset.domain
		username = token_queryset.user.username
		campaign = token_queryset.campaign.name
		current_date = datetime.now().strftime("%Y-%m-%d")
		token_str = domain+username+campaign+current_date
		old_token = uuid.uuid5(uuid.NAMESPACE_OID, token_str).hex
		if old_token==token:
			if ip_user and token_queryset.user!=ip_user.last().user:
				extend_date = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
				last_access_date = (ip_user.last().last_used+timedelta(seconds=300)).strftime("%Y-%m-%d %H:%M:%S")
				if last_access_date>extend_date:
					return False
				else:
					ThirdPartyApiUserToken.objects.filter(last_ip_addresss=ip_address).update(last_ip_addresss='')
					ThirdPartyApiUserToken.objects.filter(token=token).update(last_used=datetime.now(), last_ip_addresss=ip_address)
					return True
			else:
				ThirdPartyApiUserToken.objects.filter(id=token_queryset.id).update(last_used=datetime.now(), last_ip_addresss=ip_address)
				return True
		else:
			return False
	return False

def get_pre_campaign_create_info(request):
	"""
	this is the function defined for get the info of campaign before create 
	"""	
	data = {}
	groups = Group.objects.all()
	if check_non_admin_user(request.user):
		groups = groups.filter(Q(user_group=request.user)|Q(created_by=request.user))
	data["gateway_list"] = SMSGateway.objects.all().values("id","name")
	data["groups"] = GroupSerializer(groups, many=True).data
	department_id = groups.values_list("id", flat=True)
	data["call_time"] = CampaignSchedule.objects.values("id", "name")
	data["switch_detail"] = Switch.objects.values("name", "id")
	user_list = User.objects.values("id", "username")
	data["users"] = user_list
	data["phone_extensions"] = UserVariable.objects.filter(
		user__isnull=True).values("id", "extension")
	data["dial_trunk"] = DialTrunk.objects.values("switch__id", "name", "id")
	data["campaign_status"] = Status
	data["lead_status"] = Status
	standard_dispo = ["Dnc", "Not Connected", 
			"Connected", "Callback", "Busy", "Transfer"]
	data["default_dispo"] = list(Disposition.objects.filter(name__in=standard_dispo).exclude(status="Delete").values("id", "name",
		'color_code', 'dispos'))
	data["disposition"] = list(Disposition.objects.filter(
		status='Active').values("id", "name", 'color_code', 'dispos').exclude(name__in=standard_dispo).exclude(status="Delete"))
	data["campaign_call_mode"] = CALL_MODE
	data['dispo_list'] = Disposition.objects.all().exclude(status="Delete").values("id", "name","color_code").exclude(name__in=standard_dispo)
	data['relationtag_list'] = RelationTag.objects.all().values("id","name","color_code").exclude(status="Inactive")
	data["agent_status_list"] = PauseBreak.objects.all().values("id", "name",'break_color_code')
	# data["available_manager"] = User.objects.filter(user_role__name="manager",
	#                                group__id__in=department_id).values("id", "username")
	data["users_count"] = User.objects.all().count()
	data["dial_ratio"] = DIAL_RATIO_CHOICES
	data['css_obj'] = CSS.objects.values('id','name')
	# data["scripts"] = Script.objects.values("id", "name")
	return data

def get_pre_campaign_edit_info(pk, request):
	"""
	this is the function defined for geting the info of a campaign after creation 
	"""	
	data = {}
	data["camp_schedule"] = CampaignSchedule.objects.all().values("id", "name")
	data["switch_detail"] = Switch.objects.values("name", "id")
	data["gateway_list"] = SMSGateway.objects.all().values("id","name")
	data["trunk"] = DialTrunk.objects.values("switch__id", "name", "id")
	data["campaign_status"] = Status
	data["lead_status"] = Status
	object_data = get_object(pk, "callcenter", "Campaign")
	data["emailgateway_list"] = EmailGateway.objects.filter(template__in = object_data.email_campaign.all())
	data["strategy"] = CAMPAIGN_STRATEGY_CHOICES
	data["campaign"] = object_data
	data['dial_method'] = json.dumps(object_data.dial_method)
	data["dial_ratio"] = DIAL_RATIO_CHOICES
	# department_id = Group.objects.values_list("id", flat=True,)
	self_campaign = object_data.group.all().values_list("id", flat=True)
	self_dispo = object_data.disposition.all().values_list("id", flat=True)
	self_relationtag = object_data.relation_tag.all().values_list("id",flat=True)
	groups = Group.objects.all()
	data["is_non_admin"] = check_non_admin_user(request.user)
	data['non_user'] = []
	# users = User.objects.all()
	if request.user.is_superuser:
		users = User.objects.all().values('id',"username")
	else:
		users = User.objects.filter(id__in=user_hierarchy_func(request.user.id))
	if data["is_non_admin"]:
		groups = groups.filter(Q(user_group=request.user)|Q(created_by=request.user))
		data['user_groups'] = groups.values_list('id',flat=True)
		users = users.filter(Q(group__in=request.user.group.all())|Q(created_by=request.user)|Q(reporting_to=request.user))
		data['non_user'] = list(object_data.users.exclude(id__in=users).values_list("username", flat=True))
		users = users.exclude(id__in=object_data.users.all().values_list("id", flat=True)).values("id", "username")
	data["users"] = users
	data["groups"] = GroupSerializer(groups.exclude(id__in=self_campaign), many=True).data
	data["disposition"] = list(Disposition.objects.filter(
		status='Active').exclude(id__in=self_dispo).values("id", "name", 'color_code', 'dispos'))
	data["relationtag"] = list(RelationTag.objects.filter(
		status='Active').exclude(id__in=self_relationtag).values("id","name","color_code","relation_fields"))
	data["audio_files"] = AudioFile.objects.all().values("name", "id")
	self_agent_brekas = object_data.breaks.all().values_list(
		"id", flat=True)
	data["agent_status_list"] = PauseBreak.objects.all().exclude(
		id__in=list(self_agent_brekas)).values("id", "name", 'break_color_code')
	data["scripts"] = Script.objects.values("id", "name")
	data["users_count"] = User.objects.all().count()
	data['css_obj'] = CSS.objects.values('id','name')
	data['crm_field'] = ''
	crm_fields = CrmField.objects.filter(campaign__name=object_data.name)
	if crm_fields.exists():
		data['crm_field'] = crm_fields.first().unique_fields
	numbers = [i for i in range(0,10)]
	keys = ['*','#']
	numbers.extend(keys)
	data['dial_number'] = numbers
	trunk_group = DiaTrunkGroup.objects.all().values("id","name")
	data['trunk_group'] = list(trunk_group.values("id","name"))
	data["dial_trunk"] = DialTrunk.objects.values("switch__id", "name", "id")
	# call_mode_list = list(CALL_MODE)
	# data["campaign_call_mode"] = [i for i in call_mode_list if i[0] not  in object_data.callback_mode]
	return data

def validate_data(username, email,wfh_numeric, employee_id=''):
	"""
	this is the function defined for validating the user information
	"""	
	data = {}
	if username:
		is_present = User.objects.filter(username=username.strip()).exists()
		if is_present:
			data["username"] = "This Username is already taken"
	if email:
		is_present = User.objects.filter(email=email.strip()).exists()
		if is_present:
			data["email"] = "User with this email id is already there"

	if wfh_numeric and wfh_numeric != float:
		is_present = UserVariable.objects.filter(wfh_numeric=str(wfh_numeric).strip()).exists()
		if is_present:
			data['wfh_numeric'] = "wfh_numeric is already there"

	if employee_id:
		is_present = User.objects.filter(employee_id=employee_id.strip()).exists()
		if is_present:
			data["employee_id"] = "This employee_id is already taken"

	return data


def validate_uploaded_users_file(data):
	"""
	This method is used to validate uploaded user file
	"""
	correct_count = 0
	incorrect_count = 0
	correct_list = []
	incorrect_list = []
	duplicate_list = []
	if not data.empty:
		duplicate_list = data[data.duplicated('username', keep='first')]
		duplicate_list['description']='This username is duplicated'
		data.drop_duplicates(subset ="username", keep = 'first', inplace = True) 

		dummy_df = data[(data["wfh_numeric"] != '')]
		duplicate_list = dummy_df[dummy_df.duplicated('wfh_numeric', keep='first')]
		data = data.drop(duplicate_list.index.tolist())
		duplicate_list['description']='This wfh_numeric is duplicated'
		dummy_df= data[(data["employee_id"]!='')]
		dup_email_list = dummy_df[dummy_df.duplicated(["employee_id"], keep='first')]
		dup_email_list['description']='This employee_id is duplicated'

		frame = [duplicate_list]
		duplicate_list = pd.concat(frame)
		# index_list = dup_email_list.index.tolist()
		# data = data.drop(index_list)

		# duplicate_list['description']='This row is duplicated'
		data = data.replace(np.nan, '', regex=True)
		incorrect_count =len(duplicate_list)

		for index, row in data.iterrows():
			username = row.get("username", "")
			email = row.get("email", "")
			

			# extension = row.get("extension", "")
			# data = {}
			user_role = row.get("role", "")
			group = row.get("group", "")
			password = row.get("password", "")
			wfh_numeric = row.get("wfh_numeric","")
			employee_id = row.get("employee_id","")
			if not username or not password:
				data = {"Msg": "Missing value in row"}
			
			data = validate_data(str(username), str(email), wfh_numeric, str(employee_id))
			if user_role:
				check_role = UserRole.objects.filter(
					name__iexact=user_role.strip()).exists()
				if not check_role:
					data["role"] = "This is not a valid role"
			if group:
				check_dept = Group.objects.filter(
					name__iexact=group.strip()).exists()
				if not check_dept:
					data["group"] = "This is not a valid group"
			if data:
				incorrect_count = incorrect_count + 1
				row["description"] = json.dumps(data)
				incorrect_data = pd.DataFrame(row).T
				incorrect_list.append(pd.DataFrame(row).T)
			else:
				correct_count = correct_count + 1
				correct_list.append(pd.DataFrame(row).T)
		cwd = os.path.join(settings.BASE_DIR, 'static/')
		if correct_count:
			with open(cwd+"csv_files/proper_data.csv", 'w') as proper_file:
				for correct_row in correct_list:
					correct_row.to_csv(
						proper_file, index=False, header=proper_file.tell() == 0)

			correct_file_path = "/static/csv_files/proper_data.csv"
			data["correct_file"] = correct_file_path
			data["correct_count"] = correct_count
		if incorrect_count:
			with open(cwd+"csv_files/improper_data.csv", 'w') as improper_file:
				for incorrect_row in incorrect_list:
					incorrect_row.to_csv(
						improper_file, index=False, header=improper_file.tell() == 0)
				if not duplicate_list.empty:
					duplicate_list.to_csv(improper_file, index=False, header=improper_file.tell()==0)
			incorrect_file_path = "/static/csv_files/improper_data.csv"
			data["incorrect_file"] = incorrect_file_path
			data["incorrect_count"] = incorrect_count
	else:
		data = {}
		data["empty_file"] = "File is empty"
	return data

def upload_users(data, logged_in_user):
	"""
	this is the function defined for uploading the user
	"""
	domain_obj=Switch.objects.filter().first()	
	for index, row in data.iterrows():
		username = row.get("username", "")
		email = row.get("email", "")
		email_password = str(row.get("email_password", ""))
		password = row.get("password", "").strip()
		user_role = row.get("role", "")
		group = row.get("group", "")
		first_name = row.get("first_name", "")
		last_name = row.get("last_name","")
		wfh_numeric = row.get("wfh_numeric","")
		employee_id = row.get("employee_id","")
		user, created = User.objects.get_or_create(username=username)
		if user_role:
			role = UserRole.objects.get(name__iexact=user_role.strip())
			user.user_role = role
		if group:
			group = Group.objects.get(name__iexact=group.strip())
			user.group.add(group)
		user.set_password(password)
		user.email = email.strip()
		user.first_name = first_name
		user.last_name = last_name
		user.created_by = logged_in_user
		user.email_password = email_password.strip()
		if employee_id:
			user.employee_id = employee_id
		user.save()
		if created:
			user_variable = UserVariable()
			user_variable.user = user
		else:
			user_variable = UserVariable.objects.get(user=user)

		extension_exist = UserVariable.objects.all().values_list('extension',flat=True)
		extension = sorted(list(set(four_digit_number) - set(extension_exist)))[0]
		user_variable.extension = extension
		UserVariable.domain=domain_obj
		if wfh_numeric == '':
			user_variable.wfh_numeric = None
		else:
			user_variable.wfh_numeric = wfh_numeric
		user_variable.save()

def upload_dnc_nums(data, logged_in_user):
	"""
	this is the function defined for uploading the dnc numbers 
	"""	
	try:
		for index, row in data.iterrows():
			numeric = row.get("numeric", "")
			campaign = row.get("campaign", "")
			dnc_end_date=row.get("dnc_end_date")
			camp_obj=None
			if campaign:
				camp_obj = list(Campaign.objects.filter(name__in=campaign.split(',')))
			global_dnc = row.get("global_dnc", False)
			res = isinstance(dnc_end_date, str)
			if res:
				try:
					dnc_end_date=datetime.strptime(dnc_end_date,'%Y-%m-%d %H:%M:%S')
				except:
					dnc_end_date=datetime.strptime(dnc_end_date,'%Y-%m-%d')
			dnc_obj = DNC.objects.create(numeric=numeric[-10:],global_dnc=global_dnc,dnc_end_date=dnc_end_date)
			if not dnc_obj.global_dnc:
				dnc_obj.campaign.add(*camp_obj)
				temp_contact_data = TempContactInfo.objects.filter(numeric=numeric, campaign__in=campaign.split(','))
			else:
				temp_contact_data = TempContactInfo.objects.filter(numeric=numeric)
			temp_contact_id = temp_contact_data.values_list("id",flat=True)
			contacts = Contact.objects.filter(Q(id__in=temp_contact_id)|Q(numeric=numeric))
			uniqueid = contacts.values_list("uniqueid",flat=True).first()
			dnc_obj.uniqueid = uniqueid
			dnc_obj.save()
			contacts.update(status="Dnc")
			temp_contact_data.delete()
	except Exception as e:
		print(e)

def inactiveDNCNumber():
	today_date=datetime.date(datetime.now())
	dnc_obj=list(DNC.objects.filter(dnc_end_date__lt=today_date).values_list("numeric",flat=True))
	if dnc_obj:
		DNC.objects.filter(numeric__in=dnc_obj).update(status="Inactive")
     
def get_formatted_agent_activities(data):
	# this function is used to format agent activity time to time object    
	agent_data = {}
	wait_timer = data.get('wait_timer', '0:0:0')
	agent_data["wait_time"] = datetime.strptime(wait_timer, '%H:%M:%S').time()
	idle_time = data.get('idle_time', '0:0:0')
	agent_data["idle_time"] = datetime.strptime(idle_time, '%H:%M:%S').time()
	app_time = data.get('app_time', '0:0:0')
	agent_data["app_time"] = datetime.strptime(app_time, '%H:%M:%S').time()
	dialer_time = data.get('dialer_time', '0:0:0')
	agent_data["dialer_time"] = datetime.strptime(dialer_time, '%H:%M:%S').time()
	ring_time = data.get('ring_time', '0:0:0')
	agent_data["media_time"] = datetime.strptime(ring_time, '%H:%M:%S').time()
	speak_time = data.get('speak_time', '0:0:0')
	agent_data["spoke_time"] = datetime.strptime(speak_time, '%H:%M:%S').time()
	feedback_timer = data.get('feedback_timer', '0:0:0')
	agent_data["feedback_time"] = datetime.strptime(feedback_timer, '%H:%M:%S').time()

	preview_timer = data.get('preview_time', '0:0:0')
	agent_data["preview_time"] = datetime.strptime(preview_timer, '%H:%M:%S').time()

	progressive_time = data.get('progressive_time', '0:0:0')
	agent_data["progressive_time"] = datetime.strptime(progressive_time, '%H:%M:%S').time()
	
	pause_progressive_time = data.get('pause_progressive_time', '0:0:0')
	agent_data["pause_progressive_time"] = datetime.strptime(pause_progressive_time, '%H:%M:%S').time()
	
	hold_time = data.get('agent_hold_time', '0:0:0')
	agent_data["hold_time"] = datetime.strptime(hold_time, '%H:%M:%S').time()

	tos = data.get('tos_time', '0:0:0')
	agent_data["tos"] = datetime.strptime(tos, '%H:%M:%S').time()
	
	agent_transfer_time = data.get('agent_transfer_time', '0:0:0')
	agent_data["transfer_time"] = datetime.strptime(agent_transfer_time, '%H:%M:%S').time()

	agent_predictive_wait_time = data.get("predictive_wait_time", '0:0:0')
	agent_data["predictive_wait_time"] = datetime.strptime(agent_predictive_wait_time, '%H:%M:%S').time()

	agent_inbound_wait_time = data.get("inbound_wait_time", '0:0:0')
	agent_data["inbound_wait_time"] = datetime.strptime(agent_inbound_wait_time, '%H:%M:%S').time() 
	agent_blended_wait_time = data.get("blended_wait_time", '0:0:0')
	agent_data["blended_wait_time"] = datetime.strptime(agent_blended_wait_time, '%H:%M:%S').time()     
	# agent_data["time"] = datetime.strptime("0:0:0", '%H:%M:%S').time()
	return agent_data

def create_agentactivity(agent_data):
	"""
	this is the function defined for create agent activity
	"""	
	agent_inst = AgentActivity(**agent_data)
	agent_inst.save()

def get_campaign_users(campaign, user):
	"""
	this is the function defined for get campaign users
	"""	
	campaign = Campaign.objects.filter(name__in=campaign)
	final_users_list = []
	for camp in campaign:
		user_list = list(camp.users.all().values_list("id", flat=True))
		group_users = camp.group.all()
		group_user_list = list(User.objects.filter(group__in=group_users).values_list("id", flat=True))
		user_list.extend(group_user_list)
		user_list = list(set(user_list))
		final_users_list.extend(user_list)
	users = User.objects.filter(id__in=final_users_list).exclude(
				user_role__access_level="Admin").exclude(
				is_superuser=True).exclude(id=user.id)
	return users

def get_agent_mis(data, request) :
	"""
	this is the function defined for agent mis data information
	"""	
	context = {}
	call_details = user_campaign = []
	all_users = request.POST.get("all_users","")
	all_users = all_users.split(',')
	all_campaigns = request.POST.get("all_campaigns","")
	all_campaigns = all_campaigns.split(',')
	selected_campaign = data.getlist("selected_campaign", [])
	selected_user = data.getlist("selected_user", [])
	start_date = data.get("start_date", "")
	end_date = data.get("end_date", "")
	page = int(request.POST.get('page' ,1))
	paginate_by = int(request.POST.get('paginate_by', 10))
	start_date = datetime.strptime(data.get('start_date', ''),"%Y-%m-%d %H:%M").isoformat()
	end_date = datetime.strptime(data.get('end_date', ''),"%Y-%m-%d %H:%M").isoformat()
	performance_list = []
	if selected_user:
		all_users = selected_user
	users = User.objects.filter(id__in=all_users)
	
	start_end_date_filter = Q(created__gte=start_date)&Q(created__lte=end_date)
	if selected_campaign:
		user_campaign = selected_campaign
	else:
		user_campaign = all_campaigns
	all_fields =  set(Campaign.objects.filter(status='Active').exclude(disposition=None).values_list("disposition__name", flat=True))
	wfh_dispo_list = list(Campaign.objects.filter(wfh=True, status='Active').values_list('wfh_dispo',flat=True))
	wfh_dispo = set([ d for m in wfh_dispo_list for d in m.values()])
	all_fields.update(wfh_dispo)
	users = get_paginated_object(users, page, paginate_by)
	for user in users:
		performance_dict = {}
		performance_dict["User"] = user.username
		performance_dict["Full Name"] = user.first_name+" "+user.last_name
		if user.reporting_to:
			performance_dict["Supervisor Name"] = user.reporting_to.username
		campaign = Campaign.objects.filter(Q(users=user)|Q(group__in=user.group.all().filter(status="Active"))).filter(status="Active").values_list("name", flat=True)
		call_details = CallDetail.objects.filter(start_end_date_filter).filter(Q(campaign_name__in=user_campaign, user=user)| Q(user=user))
		ucampaign = []
		if campaign.exists():
			ucampaign = list(set(list(campaign)).intersection(selected_campaign))
		performance_dict["Campaign"] = ucampaign
		user_call_detail = call_details.exclude(cdrfeedback=None)
		for dispo_name in all_fields:
			performance_dict[dispo_name] = user_call_detail.filter(cdrfeedback__primary_dispo=dispo_name).count()
		performance_dict["Total Dispo Count"] = user_call_detail.count()
		performance_dict["AutoFeedback"] = user_call_detail.filter(cdrfeedback__primary_dispo="AutoFeedback").count()
		performance_dict["AbandonedCall"] =  call_details.filter(user_id=user,dialed_status="Abandonedcall",cdrfeedback__primary_dispo='').count()
		performance_dict["NC"] = call_details.filter(user_id=user,dialed_status="NC",cdrfeedback__primary_dispo='').count()
		performance_dict["Invalid Number"] = call_details.filter(user_id=user,dialed_status="Invalid Number",cdrfeedback__primary_dispo='').count()
		performance_dict["RedialCount"] = user_call_detail.filter(cdrfeedback__primary_dispo="Redialed").count()
		performance_dict["AlternateDial"] = user_call_detail.filter(cdrfeedback__primary_dispo="AlternateDial").count()
		performance_dict["PrimaryDial"] = user_call_detail.filter(cdrfeedback__primary_dispo="PrimaryDial").count()
		performance_dict["NF(No Feedback)"] = user_call_detail.filter(cdrfeedback__primary_dispo="NF(No Feedback)").count()
		performance_list.append(performance_dict)
	context["table_data"] = performance_list
	context["total_records"] = users.paginator.count
	context["total_pages"] = users.paginator.num_pages
	context["page"] = users.number
	context["has_next"] = users.has_next()
	context["has_prev"] = users.has_previous()
	context['start_index'] = users.start_index()
	context['end_index'] = users.end_index()
	return context

def get_campaign_mis(data, request) :
	"""
	this is the function defined for campaign mis report 
	"""	
	logged_in_user = request.user
	context = user_campaign = writer = {}
	call_details = user_id = []
	admin = False
	if logged_in_user.user_role and logged_in_user.user_role.access_level == 'Admin':
		admin = True
	if logged_in_user.is_superuser:
		admin= True
	all_users = request.POST.get("all_users","")
	all_users = all_users.split(',')
	all_campaigns = request.POST.get("all_campaigns","")
	all_campaigns = all_campaigns.split(',')
	selected_campaign = data.getlist("selected_campaign", "")
	selected_user = data.get("selected_user", "")
	start_date = data.get("start_date", "")
	end_date = data.get("end_date", "")
	page = int(request.POST.get('page' ,1))
	paginate_by = int(request.POST.get('paginate_by', 10))
	download_report = request.POST.get("agent_reports_download", "")
	if start_date:
		start_date = datetime.strptime(data.get('start_date', ''),
			"%Y-%m-%d %H:%M").isoformat()
	if end_date:
		end_date = datetime.strptime(data.get('end_date', ''),
			"%Y-%m-%d %H:%M").isoformat()
	performance_list = []
	start_end_date_filter = Q(created__gte=start_date)&Q(created__lte=end_date)

	call_details = CallDetail.objects.filter(start_end_date_filter)
	# camp_ids = Campaign.objects.filter(name__in=all_campaigns).values_list('id',flat=True)
	if admin:
		call_details =  call_details.filter(Q(campaign_name__in=list(all_campaigns)))
	# data_distinct = call_details.distinct().order_by().values_list("campaign_name", flat=True)
	if call_details.exists():
		if selected_campaign:
			user_campaign = Campaign.objects.filter(name__in=selected_campaign)
		else:
			user_campaign = Campaign.objects.filter(name__in=list(all_campaigns)).filter(
				status="Active").distinct()
		if not download_report:
			user_campaign = get_paginated_object(user_campaign, page, paginate_by)
		else:
			col_name = request.POST.get("column_name", "")
			col_list = col_name.split(",")
			if "" in col_list:
				col_list.remove("")
			writer = csv.writer(Echo())
			performance_list.append(writer.writerow(col_list))

		for camp in user_campaign:
			dialed_status= []
			all_fields = []
			all_fields =  list(set(Campaign.objects.filter(name=camp.name).exclude(disposition=None).values_list("disposition__name", flat=True)))
			performance_dict = {}
			performance_dict["Campaign"] = camp.name
			campaign_call_detail = call_details.filter(campaign_name=camp.name)
			cdr_feedback = campaign_call_detail.exclude(cdrfeedback=None)
			for dispo_name in all_fields:
				performance_dict[dispo_name] = cdr_feedback.filter(cdrfeedback__primary_dispo=dispo_name).count()
			performance_dict["AutoFeedback"] = cdr_feedback.filter(cdrfeedback__primary_dispo="AutoFeedback").count()
			performance_dict["AbandonedCall"] =  campaign_call_detail.filter(dialed_status="Abandonedcall",cdrfeedback__primary_dispo='').count()
			performance_dict["NC"] = campaign_call_detail.filter(dialed_status="NC",cdrfeedback__primary_dispo='').count()
			performance_dict["Invalid Number"] = campaign_call_detail.filter(dialed_status="Invalid Number",cdrfeedback__primary_dispo='').count()
			performance_dict["RedialCount"] = cdr_feedback.filter(cdrfeedback__primary_dispo="Redialed").count()
			performance_dict["AlternateDial"] = cdr_feedback.filter(cdrfeedback__primary_dispo="AlternateDial").count()
			performance_dict["PrimaryDial"] = cdr_feedback.filter(cdrfeedback__primary_dispo="PrimaryDial").count()
			performance_dict["NF(No Feedback)"] = cdr_feedback.filter(cdrfeedback__primary_dispo="NF(No Feedback)").count()
			performance_dict["Total Dispo Count"] = cdr_feedback.count()
			row = []
			if download_report:
				for field in col_list:
					row.append(performance_dict.get(field,""))
				performance_list.append(writer.writerow(row))
			else:
				performance_list.append(performance_dict)

	context["table_data"] = performance_list
	if download_report:
		return context
	if type(user_campaign) != dict:
		context["total_records"] = user_campaign.paginator.count
		context["total_pages"] = user_campaign.paginator.num_pages
		context["page"] = user_campaign.number
		context["has_next"] = user_campaign.has_next()
		context["has_prev"] = user_campaign.has_previous()
		context['start_index'] = user_campaign.start_index()
		context['end_index'] = user_campaign.end_index()
	return context


def dummy_agent_activity():
	""" create a dummy agent activity  """
	time = datetime.strptime("0:0:0", '%H:%M:%S').time()
	activity_list = ['tos', 'app_time', 'dialer_time', 'wait_time',
				'media_time', 'spoke_time', 'preview_time',
				'predictive_time', 'feedback_time', 'break_time']
	activity_dict = dict.fromkeys(activity_list, time)
	activity_dict["break_type"] = ""
	return activity_dict


def fs_group_add_user(domain,user):
	"""
	this is the function defined for add group user
	"""	
	SERVER = freeswicth_server(domain)
	extension = user.properties.extension
	if type(extension) == int:
		extension = str(user.properties.extension)
	user_in_server = SERVER.freeswitch.api("callcenter_config","agent list "+extension)
	try:
		if user_in_server[1:][0].split('|')[0] != extension:
			SERVER.freeswitch.api("callcenter_config",
					"agent add %s %s" % (extension, user.properties.type))
		else:
			pass
		if 'freetdm' not in user.properties.contact:
			SERVER.freeswitch.api("callcenter_config",
					"agent set contact %s %s/%s@%s" % (extension, user.properties.contact,
						extension, user.properties.domain.ip_address))
		else:
			SERVER.freeswitch.api("callcenter_config",
					"agent set contact %s %s/%s" % (extension, user.properties.contact,
						extension))
		SERVER.freeswitch.api("callcenter_config",
				"agent set type %s %s" % (extension, user.properties.type))
		SERVER.freeswitch.api("callcenter_config",
				"agent set status %s '%s'" % (extension, user.properties.dial_status))
		SERVER.freeswitch.api("callcenter_config",
				"agent set max_no_answer %s %s" % (extension,
					user.properties.max_no_answer))
		SERVER.freeswitch.api("callcenter_config",
				"agent set wrap_up_time %s %s" % (extension,
					user.properties.wrap_up_time))
		SERVER.freeswitch.api("callcenter_config",
				"agent set reject_delay_time %s %s" % (extension,
					user.properties.reject_delay_time))
		SERVER.freeswitch.api("callcenter_config",
				"agent set busy_delay_time %s %s" % (extension,
					user.properties.busy_delay_time))
	except socket.error as e:
		print ("RPC Error %s: Freeswitch RPC module may not be" \
				"loaded or properly configured" % e)
		return None

def group_add_user_rpc(**kwargs):
	"""
	this is the function defined for add user rpc
	"""	
	campaign_ip = Campaign.objects.filter(group__id=kwargs['group_id']).prefetch_related('switch')
	if campaign_ip:
		for campaign in campaign_ip:
			camp_domain = campaign.switch.ip_address
			if  kwargs['user_add_queryset']:
				for user in kwargs['user_add_queryset']:
					fs_group_add_user(camp_domain,user)
	else:
		if  kwargs['user_add_queryset']:
			for user in kwargs['user_add_queryset']:
				fs_group_add_user(user.properties.domain.ip_address,user)
	return

def get_user_role(user):
	"""
	this is the function defined for user role of a user 
	"""	
	if user.is_superuser:
		user_role = UserRole.objects.all()
	else:
		if user.user_role.access_level.lower() == "admin":
			team = User.objects.filter(reporting_to=user)
			user_role = UserRole.objects.filter(Q(created_by__in=team)|Q(created_by=user))
		else:
			user_role = UserRole.objects.filter(access_level="Agent")
	return user_role

def validate_uploaded_dnc(data):
	"""
	This method is used to validate dnc file.
	It will check dnc with given info already exists
	or not
	"""
	correct_count = 0
	incorrect_count = 0
	correct_list = []
	incorrect_list = []
	duplicate_list = []
	if not data.empty:
		duplicate_list = data[data.duplicated('numeric', keep='first')]
		data.drop_duplicates(subset="numeric", keep='first', inplace=True)
		duplicate_list['description'] = 'This row is duplicated'
		incorrect_count = len(duplicate_list)
		for index, row in data.iterrows():
			data_dict = {}
			numeric = str(row.get("numeric", "")).strip()
			global_dnc = str(row.get("global_dnc", ""))
			dnc_end_date=str(row.get("dnc_end_date"," "))
			campaign = str(row.get("campaign", ""))
			if numeric:
				if not numeric.isdigit():
					data_dict["number"] = "Enter Valid Number"
				else:
					if DNC.objects.filter(numeric=numeric[-10:]).exists():
						data_dict["number"] = "This number already exists"
			if not numeric:
				data_dict["number"] = "Enter Number"    
			if not campaign and not global_dnc:
				data_dict["campaign_global_dnc"] = "Atleast provide one campaign or global_dnc as TRUE"
			if campaign:
				campaign = campaign.split(',')
				camp_len = len(campaign)
				camp_objs_len = Campaign.objects.filter(name__in=campaign).count()
				if camp_len != camp_objs_len:
					data_dict["campaign"] = "Campaign with this name is not exists" 
			if global_dnc:
				if not global_dnc.lower() in ["true","false"]:
					data_dict["global_dnc"] = "Global_dnc values should be TRUE or FALSE"
				elif global_dnc.lower() == 'false' and not campaign:
					data_dict["campaign"] = 'Atleast provide one camaign or make global dnc as TRUE'
			if data_dict:
				incorrect_count = incorrect_count + 1
				row["description"] = json.dumps(data_dict)
				incorrect_data = pd.DataFrame(row).T
				incorrect_list.append(pd.DataFrame(row).T)
			else:
				# print("correct_count", column_list)
				correct_count = correct_count + 1
				correct_list.append(pd.DataFrame(row).T)
		data = {}
		if correct_count:
			with open(cwd+"csv_files/proper_data.csv", 'w') as proper_file:
				for correct_row in correct_list:
					correct_row.to_csv(
						proper_file, index=False, header=proper_file.tell() == 0)

			correct_file_path = "/static/csv_files/proper_data.csv"
			data["correct_file"] = correct_file_path
			data["correct_count"] = correct_count
		if incorrect_count:
			with open(cwd+"csv_files/improper_data.csv", 'w') as improper_file:
				for incorrect_row in incorrect_list:
					incorrect_row.to_csv(
						improper_file, index=False, header=improper_file.tell() == 0)
				if not duplicate_list.empty:
					duplicate_list.to_csv(
						improper_file, index=False, header=improper_file.tell() == 0)
			incorrect_file_path = "/static/csv_files/improper_data.csv"
			data["incorrect_file"] = incorrect_file_path
			data["incorrect_count"] = incorrect_count
	else:
		data = {}
		data["empty_file"] = "File is empty"
	return data

def format_time(date_time):
	if date_time:
		return datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')
	else:
		return None

def convert_into_timedelta(given_time):
	""" converting into the timdelta"""
	if type(given_time) != str:
		return timedelta(hours=given_time.hour, minutes=given_time.minute, seconds=given_time.second)
	elif type(given_time) == str:
		given_time_list = given_time.split(':')
		return timedelta(hours=int(given_time_list[0]),minutes=int(given_time_list[1]), seconds=int(given_time_list[2]))
	else:
		return timedelta(seconds=0)

def submit_feedback(user,data):
	"""
	This method is used to submit feedback of customer
	"""
	try:
		phonebook_name = ""
		phone_number = data.get('numeric', '')
		primary_dispo = data.get('primary_dispo','')
		hangup_cause = data.get('hangup_cause_er','')
		hangup_cause_code = data.get('hangup_cause_code_er','')
		dialed_status = data.get('dialed_status_er','')
		update_lead_user = data.get('sys_update_lead_user',None)
		sys_reverify_lead = data.get('sys_reverify_lead',False)
		calldetail_id = data.get('calldetail_id',None)
		customer_raw_data = json.loads(data.get("customer_raw_data","{}"))
		customer_raw_data = {sec_name :{field_name:(None if field_value=='' else field_value) for field_name,field_value in sec_value.items()} for sec_name,sec_value in customer_raw_data.items()}
		alt_numeric = json.loads(data.get("alt_numeric","{}"))
		update_crm = data.get('update_crm','false')
		if hangup_cause == 'NOT_FOUND' and dialed_status == 'NOT_FOUND' and hangup_cause_code == '':
			hangup_cause ='NOT_FOUND' 
			dialed_status = 'NOT_FOUND'
			hangup_cause_code = '502'
		else:
			if data.get("c_connect_time",''):
				dialed_status = 'Connected'
				hangup_cause = 'NORMAL_CLEARING'
				hangup_cause_code = '16'
			else:
				dialed_status = 'NC'
				hangup_cause = 'NORMAL_CLEARING'
				hangup_cause_code = '16'
		status='Dialed'
		if primary_dispo.lower() == 'dnc':
			status= primary_dispo.title()
		campaign_obj = Campaign.objects.get(name=data.get('campaign'))
		cb_schedule_time = data.get('schedule_time','') 
		contact_id = data.get('contact_id', None) 
		uniqueid = None
		if not contact_id or contact_id == "":
			contact_id = None
		tempcontact = contact = []
		progressive_val = data.get('progressive_time_val','0:0:0')
		if progressive_val:
			progressive_val = dateutil.parser.parse(progressive_val).time()
		predictive_val = data.get('predictive_time_val','0:0:0')
		if predictive_val:
			predictive_val = dateutil.parser.parse(predictive_val).time()
		inbound_val = data.get('inbound_time_val','0:0:0')
		if inbound_val:
			inbound_val = dateutil.parser.parse(inbound_val).time()
		preview_val = data.get('preview_time_val', '0:0:0')
		if preview_val:
			preview_val = dateutil.parser.parse(preview_val).time()
		if phone_number:
			contact = Contact.objects.filter(id=contact_id)
			phonebook_name=""
			if contact.exists():
				uniqueid = contact.first().uniqueid
				if contact.first().phonebook:
					phonebook_name = contact.first().phonebook.name
				ci_serializer = SetContactSerializer(contact.first(), data=data)
			else:
				ci_serializer = SetContactSerializer(data=data)
				update_crm = 'true'
			if ci_serializer.is_valid():
				tempobj = ci_serializer.save(disposition=primary_dispo, status=status, modified_date=datetime.now(),
						last_connected_user=user.extension, last_dialed_date = datetime.now())
				tempobj.dial_count = tempobj.dial_count + 1
				if update_crm == 'true':
					tempobj.customer_raw_data = customer_raw_data
				tempobj.save()
				contact_id = tempobj.id
				if LeadBucket.objects.filter(contact=tempobj).exists():
					if update_lead_user and sys_reverify_lead:
						LeadBucket.objects.filter(contact=tempobj).update(last_verified_by=user.username, verified_to=str(update_lead_user), reverify_lead=True)
					elif update_lead_user:
						LeadBucket.objects.filter(contact=tempobj).update(last_verified_by=user.username, verified_to=str(update_lead_user), reverify_lead=False)
				elif update_lead_user:
					LeadBucket.objects.create(contact=tempobj, created_by=user.username, last_verified_by=user.username, verified_to=str(update_lead_user))
				if alt_numeric.keys():
					if uniqueid and AlternateContact.objects.filter(uniqueid=uniqueid).exists():
						AlternateContact.objects.filter(uniqueid=uniqueid).update(alt_numeric=alt_numeric)
					elif AlternateContact.objects.filter(numeric=phone_number).exists():
						alt_num_obj = AlternateContact.objects.filter(numeric=phone_number).first()
						if uniqueid and not alt_num_obj.uniqueid:
							alt_num_obj.uniqueid = uniqueid
						alt_num_obj.alt_numeric = alt_numeric
						alt_num_obj.save()
					else:
						AlternateContact.objects.create(numeric=phone_number, uniqueid=uniqueid, alt_numeric=alt_numeric)

			temp_hold_time = data.get("hold_time", "")
			if not calldetail_id:
				cd_serializer = CallDetailSerializer(data=data)
				if cd_serializer.is_valid():
					predictive_wait_time = data.get("predictive_wait_time", '0:0:0')
					inbound_wait_time = data.get("inbound_wait_time", '0:0:0')
					bill_sec = data.get("bill_sec", "").split(":")
					formatted_bill_sec = timedelta(hours=int(bill_sec[0]), minutes=int(bill_sec[1]), seconds=int(bill_sec[2]))
					wait_time = data.get("wait_time", "").split(":")
					formatted_wait_time = timedelta(hours=int(wait_time[0]), minutes=int(wait_time[1]), seconds=int(wait_time[2]))
					hold_time = temp_hold_time.split(":")
					formatted_hold_time = timedelta(hours=int(hold_time[0]), minutes=int(hold_time[1]), seconds=int(hold_time[2]))
					formatted_init_time = format_time(data.get("c_init_time",''))
					formatted_connect_time = format_time(data.get("c_connect_time",''))
					formatted_hangup_time = format_time(data.get("c_hangup_time",''))
					formatted_ring_time = format_time(data.get("c_ring_time",''))
					calculate_ring_duration = timedelta(hours=0, minutes=0, seconds=0)
					if data.get("c_connect_time",''):
						if formatted_connect_time > formatted_ring_time:
							calculate_ring_duration = formatted_connect_time - formatted_ring_time 
					else:
						if formatted_ring_time or formatted_init_time:
							try:
								if formatted_hangup_time > formatted_ring_time:
									calculate_ring_duration = formatted_hangup_time - formatted_ring_time
							except:
								if formatted_hangup_time > formatted_init_time:
									calculate_ring_duration = formatted_hangup_time - formatted_init_time
						else:
							print(data)

					formatted_ring_duration = time.strftime('%H:%M:%S', time.gmtime(
						calculate_ring_duration.total_seconds()))
					call_duration = formatted_bill_sec+formatted_wait_time+formatted_hold_time+calculate_ring_duration
					cd_obj = cd_serializer.save(user=user, campaign_name=campaign_obj.name,
						init_time=formatted_init_time,
						ring_time=formatted_ring_time,
						ring_duration = formatted_ring_duration,
						connect_time=formatted_connect_time,
						hangup_time=format_time(data.get("c_hangup_time",'')),
						phonebook = phonebook_name,
						progressive_time = progressive_val,
						predictive_time = predictive_val,
						inbound_time = inbound_val,
						preview_time = preview_val,
						hold_time = temp_hold_time,
						predictive_wait_time = predictive_wait_time,
						inbound_wait_time = inbound_wait_time,
						call_duration = str(call_duration),
						dialed_status= dialed_status,
						hangup_cause = hangup_cause,
						hangup_cause_code = hangup_cause_code,
						contact_id = contact_id,
						hangup_source=data.get("hangup_source",''),
						uniqueid=uniqueid)
					print(data,"this is data after dispo")

					CdrFeedbck.objects.create(primary_dispo=primary_dispo, feedback=json.loads(
						data.get("feedback",{})), relation_tag=json.loads(data.get("relation_tag","")),
						session_uuid = data.get("session_uuid",None), contact_id = contact_id,
						comment=data.get("comment", ""), calldetail=cd_obj
						)
			else:
				CallDetail.objects.filter(id=calldetail_id).update(contact_id=contact_id, uniqueid=uniqueid, phonebook = phonebook_name)
				CdrFeedbck.objects.filter(calldetail_id=calldetail_id).update(primary_dispo=primary_dispo, feedback=json.loads(
					data.get("feedback",{})), relation_tag=json.loads(data.get("relation_tag","")),comment=data.get("comment", ""),
					contact_id = contact_id)
			del_obj = DiallerEventLog.objects.filter(session_uuid=data.get("session_uuid"))
			if del_obj.exists():
				if del_obj.first().contact_id:
					del_obj.update(hold_time=temp_hold_time,uniqueid=uniqueid,phonebook = phonebook_name)
				else:
					del_obj.update(hold_time=temp_hold_time, contact_id=contact_id,uniqueid=uniqueid,phonebook = phonebook_name)
			if phone_number and campaign_obj:
				query = Q(contact_id=contact_id)|Q(campaign=campaign_obj.name,numeric=phone_number)
				CallBackContact.objects.filter(query).delete()
				CurrentCallBack.objects.filter(query).delete()
				SnoozedCallback.objects.filter(Q(contact_id=contact_id)|Q(numeric=phone_number)).delete()
				Abandonedcall.objects.filter(numeric=phone_number).delete()
			if cb_schedule_time:
				call_back_contact_inst = CallBackContact.objects.filter(contact_id=contact_id)
				if call_back_contact_inst.exists():
					cbc_serializer = SetCallBackContactSerializer(call_back_contact_inst.first(), data=data)
					CurrentCallBack.objects.filter(contact_id=contact_id).delete()
					SnoozedCallback.objects.filter(contact_id=contact_id).delete()
				else:
					cbc_serializer = SetCallBackContactSerializer(data=data)
				if cbc_serializer.is_valid():
					if contact_id == 0:
						t_contact = TempContactInfo.objects.filter(numeric=phone_number)
						if t_contact.exists():
							contact_id = t_contact.first().id
						else:
							contact_id = Contact.objects.filter(numeric=phone_number).first().id
					user_extension = user.extension
					if data.get("callback_type","") == "queue":
						user_extension = None
					cbc_obj = cbc_serializer.save(user=user_extension, alt_numeric=json.loads(data.get("alt_numeric","{}")),
						customer_raw_data=customer_raw_data,disposition=primary_dispo,
						contact_id=contact_id, phonebook=phonebook_name, status = 'NotDialed'
						)
				else:
					print(cbc_serializer.errors)
			if primary_dispo.lower() == 'dnc':
				data = data.copy()
				data['status'] = 'Active'
				dnc_obj = DNC.objects.filter(numeric=data['numeric'])
				if dnc_obj:
					dnc_serializer=DncSerializer(dnc_obj[0],data=data)
				else:
					dnc_serializer=DncSerializer(data=data)
				if dnc_serializer.is_valid():
					dnc_obj = dnc_serializer.save(user=user,phonebook = phonebook_name)
					dnc_obj.uniqueid=uniqueid
					dnc_obj.save()
					if data['global_dnc'] == 'true':
						dnc_obj.campaign.clear()
						Contact.objects.filter(numeric=data["numeric"]).update(status="DNC")
						TempContactInfo.objects.filter(numeric=data["numeric"]).delete()
					else:
						dnc_obj.campaign.add(campaign_obj)
						Contact.objects.filter(numeric=data["numeric"], campaign=campaign_obj.name).update(status="DNC")
						TempContactInfo.objects.filter(numeric=data["numeric"], campaign=campaign_obj.name).delete()

				else:
					print(dnc_serializer.errors)
		if data.get("callmode","") in ["manual", "inbound", "inbound-blended", "redial", "alternate-dial"]:
			TempContactInfo.objects.filter(id=contact_id).delete()
		return {'success':'Data Updated Successfully', 'contact_id':contact_id}
	except Exception as e:
		print("error from submit dispo function",e)
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print(exc_type, fname, exc_tb.tb_lineno)
		return {'error':'Data Not Updated Successfully'}    
		

def customer_detials(campaign,dial_number,campaign_object):
	""" get the customer details of a contact"""
	contact_number = TempContactInfo.objects.filter(numeric=dial_number, campaign=campaign, 
		status='Locked').values_list("id", flat=True)
	contact_number_data = Contact.objects.filter(numeric=dial_number,
		campaign=campaign).exclude(id__in=contact_number).order_by("-modified_date")[:15]
	contact_number_list = list(contact_number_data.values('id', 'first_name','last_name',
		'numeric', 'alt_numeric', 'status', 'uniqueid'))
	contact_count = len(contact_number_list)
	if contact_count == 0:
		if campaign_object.search_alternate:
			alt_contact_list = AlternateContact.objects.filter(alt_numeric__values__contains=[dial_number]).values_list('uniqueid',flat=True)
			contact_number = TempContactInfo.objects.filter(uniqueid__in=list(alt_contact_list), campaign=campaign, status='Locked').values_list("id", flat=True)
			contact_number_data = Contact.objects.filter(uniqueid__in=list(alt_contact_list), campaign=campaign).exclude(id__in=contact_number)[:15]
			contact_number_list = list(contact_number_data.values('id', 'first_name','last_name', 'numeric', 'alt_numeric', 'status', 'uniqueid'))
			contact_count = len(contact_number_list)
	if contact_count == 0:
		contact_number_list = [{'id':0,'numeric':dial_number,'status':'NewContact','uniqueid':None}]
		contact_count = len(contact_number_list)
	weburl =""
	thirdparty_api_status = False
	dynamic_api = False
	click_for_details = False
	if campaign_object.apicampaign.exists():
		dynamic_obj = campaign_object.apicampaign.all().first().dynamic_api
		click_for_details_obj = campaign_object.apicampaign.all().first().click_url
		if campaign_object.apicampaign.exists():
			thirdparty_api_status =True
			if dynamic_obj and click_for_details_obj:
				click_for_details = True
				dynamic_api =True
			elif dynamic_obj:
				dynamic_api =True
			elif click_for_details_obj:
				click_for_details = True
			weburl = campaign_object.apicampaign.all().first().weburl
	data={'contact_info':contact_number_list, 'contact_count':contact_count,"thirdparty_api_status":thirdparty_api_status, 
		"dynamic_api":dynamic_api,"click_for_details":click_for_details,"weburl":weburl}
	return data
def pd_to_csv(df,download_report_id,report_name, user, file_type='csv'):
	try:
		from django.conf import settings

		download_folder = settings.MEDIA_ROOT+"/download/"+datetime.now().strftime("%m.%d.%Y")+"/"+str(user.id)+"/"
		if not os.path.exists(download_folder):
			os.makedirs(download_folder)
		if file_type == 'csv':
			file_path = download_folder+str(user.id)+'_'+str(report_name)+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".csv"
			df.to_csv(file_path, index = False)
			# with open(file_path, 'w', newline='') as file:
			# 	writer = csv.writer(file, delimiter=',')
			# 	writer.writerows(csv_file)
			# 	file.close()
		# else:
		# 	file_path = download_folder+str(user.id)+'_'+str(report_name)+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".xlsx"
		# 	with pd.ExcelWriter(file_path, engine="xlsxwriter",options={'remove_timezone': True, 'strings_to_formulas': False}) as writer:
		# 		df = pd.DataFrame(csv_file[1:], columns=csv_file[0])
		# 		df.to_excel(writer, sheet_name = "Sheet1", header = True, index = False)
		f = open(file_path, 'rb')
		if download_report_id !=None:
			download_report = DownloadReports.objects.get(id=download_report_id)
			download_report.downloaded_file.save(os.path.basename(f.name), File(f), save=True)
			download_report.is_start = False
			download_report.save()
		f.close()
		if not download_report_id:
			sending_reports_through_mail(user,report_name)
		if download_report_id !=None:
#			os.remove(file_path)
			set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
		transaction.commit()
		connections['crm'].close()      
		connections['default'].close()
	except Exception as e:
		print('save file error',e)

def sending_reports_through_mail(user,report_name):
	full_name = user.first_name+" "+user.last_name
	encode_file_name = "download/"+datetime.now().strftime("%m.%d.%Y")+"/"+str(user.id)+"/"+str(user.id)+'_'+str(report_name)+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".csv"
	response = 0 
	try:
		email_sch_obj = EmailScheduler.objects.filter(created_by_id=user.id).first()
		if email_sch_obj:
			connection = email_connection(email_sch_obj.emails['from'],email_sch_obj.emails['password'])
			email_sch_obj = EmailScheduler.objects.all()
			for emails_obj in email_sch_obj:
				email_report_names = [email_report_name.replace(" ","").lower() for email_report_name in emails_obj.reports]
				download_report_name  = []
				user_id = User.objects.get(username=user).id
				if report_name.replace("_","").lower() in email_report_names and user_id == emails_obj.created_by_id:
					subject = report_name.title() +'Reports Of '+datetime.today().date().strftime('%Y-%m-%d')
					#encode the file name
					sample_string_bytes = encode_file_name.encode("ascii") 
					
					base64_bytes = base64.b64encode(sample_string_bytes) 
					base64_string = base64_bytes.decode("ascii") 
					html_content = """
					<p>
					Hello {0},<br>
					Kindly click the below link to download {1} report of  {2}
					<br>
					<a href='https://{3}/api/download-scheduled-report/{4}'>Download Report</a>
					""".format(full_name, report_name,datetime.today().date().strftime('%Y-%m-%d'),settings.IP_ADDRESS,base64_string)
					from_email = emails_obj.emails['from']
					to = emails_obj.emails['to']
					msg = EmailMultiAlternatives(subject,"",from_email, to,connection=connection)
					msg.attach_alternative(html_content, "text/html")
					response = msg.send()
					save_email_log(report_name,emails_obj.emails['from'],emails_obj.emails['to'],response)
	except Exception as e:
		print('Sending Email from Scheduler',e)
def update_contact_on_css(campaign_name):
	""" update the conatcts in css"""
	temp_data = TempContactInfo.objects.filter(campaign=campaign_name, status='NotDialed').exclude(
		Q(contact__status='Queued-Callback')|Q(contact__status='Queued-Abandonedcall'))
	for temp in temp_data:
		Contact.objects.filter(id=temp.contact_id).update(status=temp.previous_status)
	temp_data.delete()
	campaign_id = Campaign.objects.get(name=campaign_name)
	PhonebookBucketCampaign.objects.filter(id=campaign_id.id).update(is_contact=True)

def update_contact_on_portifolio(campaign):
	"""
	this is the function defined update contact on portfolio based
	"""	
	queued_callback = TempContactInfo.objects.filter(campaign=campaign.name).filter(Q(contact__status='Queued-Callback')|Q(contact__status='Queued-Abandonedcall'))
	for callback in queued_callback:
		if callback.contact__status=='Queued-Abandonedcall':
			abd_instance = Abandonedcall.objects.create(campaign=campaign.name,caller_id=caller_id,numeric = callback.numeric, status ='Abandonedcall',user=callback.user)
			abd_instance.created_date = callback.created_date
			abd_instance.save()
		if callback.contact__status=='Queued-Callback':
			cbr_instance = CallBackContact.objects.create(numeric =callback.numeric,campaign =campaign.name, callback_type = campaign.callback_mode,status = 'NotDialed',customer_raw_data={},contact_id=callback.contact.id, callmode='callback')
			cbr_instance.schedule_time = callback.created_date
			cbr_instance.save()
	temp_data = TempContactInfo.objects.filter(campaign=campaign.name, status='NotDialed')
	for temp in temp_data:
		Contact.objects.filter(id=temp.contact_id).update(status=temp.previous_status)
	temp_data.delete()
	PhonebookBucketCampaign.objects.filter(id=campaign.id).update(is_contact=True)

def save_csv(file_name, list):
	"""
	this is the function defined for save csv 
	"""	
	try:
		with open(file_name, 'w+', encoding='utf-8') as file:
			for row in list:
				row.to_csv(file, index=False, header=file.tell() == 0,encoding='utf-8')
	except Exception as e:
		print(e)

def set_download_progress_redis(instance_id, percentage=0, is_refresh=False):
	"""
	this is the function defined for set downloading progress
	"""	
	DOWNLOAD_STATUS = {}
	DOWNLOAD_STATUS = pickle.loads(settings.R_SERVER.get("download") or pickle.dumps(DOWNLOAD_STATUS))
	if percentage == 100.0:
		DOWNLOAD_STATUS['is_refresh'] = is_refresh
		if str(instance_id) in DOWNLOAD_STATUS:
			del DOWNLOAD_STATUS[''+str(instance_id)+'']
		if is_refresh:
			download_report = DownloadReports.objects.get(id=instance_id)
			download_report.is_start = False
			download_report.save()
	else:
		if DOWNLOAD_STATUS:
			if ''+str(instance_id)+'' not in DOWNLOAD_STATUS:
				DOWNLOAD_STATUS[''+str(instance_id)+''] = percentage
			else:
				DOWNLOAD_STATUS[''+str(instance_id)+''] = percentage
		else:
			DOWNLOAD_STATUS[''+str(instance_id)+''] = percentage
	settings.R_SERVER.set("download", pickle.dumps(DOWNLOAD_STATUS))

def get_download_progress(instance_id):
	"""
	this is the function defined for get the download progress
	"""	
	DOWNLOAD_STATUS = {}
	DOWNLOAD_STATUS = pickle.loads(settings.R_SERVER.get("download") or pickle.dumps(DOWNLOAD_STATUS))
	if str(instance_id) in DOWNLOAD_STATUS:
		return DOWNLOAD_STATUS[''+str(instance_id)+'']
	return 100

def email_connection(email_id, email_password, host_name='smtp.gmail.com', port=587):
	"""
	this is the function defined for email connection string
	"""	
	use_tls = True
	use_ssl = False
	port = port
	host_name = host_name
	connection = get_connection(
		host=host_name,
		port=port, 
		username= email_id, 
		password=email_password.strip(),
		use_tls=use_tls,
		use_ssl=use_ssl
		)
	return connection

def save_email_log(report_name,from_email="",to_email="",response="",user=""):
	"""
	this is the function defined for save email log data into file
	"""	
	try:
		if response == 1:
			status = 'Email sent successfully'
		elif response == 2:
			status = 'Report Downloaded'
		else:
			status = 'Failed to send the Email'

		if os.path.isdir('/var/lib/flexydial/media/emaillog'):
			file_path = '/var/lib/flexydial/media/emaillog/emaillog.xls'
			if os.path.isfile(file_path):
				readbook = xlrd.open_workbook(file_path,formatting_info=True,on_demand=True)
				r_sheet = readbook.sheet_by_index(0) 
				row_number = r_sheet.nrows
				workbook  = copy(readbook)
				sheet = workbook.get_sheet(0)
				sheet.write(row_number,0,report_name)
				sheet.write(row_number,1,from_email)
				sheet.write(row_number,2,to_email)
				sheet.write(row_number,3,status)
				sheet.write(row_number,4,datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
				sheet.write(row_number,5,user)
				workbook.save(file_path) 
			else:
				wb = Workbook()
				sheet = wb.add_sheet('emaillog')
				sheet.write(0, 0, 'Report Name')
				sheet.write(0, 1, 'From Email')
				sheet.write(0, 2, 'To Email')
				sheet.write(0, 3, 'Status')
				sheet.write(0, 4, 'DateTime')
				sheet.write(0, 5, 'User')
				sheet.write(1,0,report_name)
				sheet.write(1,1,from_email)
				sheet.write(1,2,to_email)
				sheet.write(1,3,status)
				sheet.write(1,4,datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
				sheet.write(1,5,user)
				wb.save(file_path)
		else:
			os.mkdir('/var/lib/flexydial/media/emaillog')
	except Exception as e:
		print(e)


def save_download_log(user, filename):
	"""
	this is the function defined for download logs 
	"""	
	try:
		if os.path.isdir('/var/lib/flexydial/media/download'):
			file_path = '/var/lib/flexydial/media/download/download.xls'
			if os.path.isfile(file_path):
				readbook = xlrd.open_workbook(file_path,formatting_info=True,on_demand=True)
				r_sheet = readbook.sheet_by_index(0) 
				row_number = r_sheet.nrows
				workbook  = copy(readbook)
				sheet = workbook.get_sheet(0)
				sheet.write(row_number,0,user)
				sheet.write(row_number,1,filename)
				sheet.write(row_number,2,datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
				workbook.save(file_path) 
			else:
				wb = Workbook()
				sheet = wb.add_sheet('download')
				sheet.write(0, 0, 'UserId')
				sheet.write(0, 1, 'File Name')
				sheet.write(0, 2, 'DateTime')
				sheet.write(1,0,user)
				sheet.write(1,1,filename) 
				sheet.write(1,2,datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
				wb.save(file_path)
		else:
			os.mkdir('/var/lib/flexydial/media/download')
	except Exception as e:
		print(e)

def save_file(csv_file, download_report_id, report_name, user, file_type='csv'):
	"""
	this is the function defined for save the file name of the download 
	"""	
	try:
		from django.conf import settings

		download_folder = settings.MEDIA_ROOT+"/download/"+datetime.now().strftime("%m.%d.%Y")+"/"+str(user.id)+"/"
		if not os.path.exists(download_folder):
			os.makedirs(download_folder)
		if file_type == 'csv':
			file_path = download_folder+str(user.id)+'_'+str(report_name)+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".csv"
			with open(file_path, 'w', newline='') as file:
				writer = csv.writer(file, delimiter=',')
				writer.writerows(csv_file)
				file.close()
		else:
			file_path = download_folder+str(user.id)+'_'+str(report_name)+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".xlsx"
			with pd.ExcelWriter(file_path, engine="xlsxwriter",options={'remove_timezone': True, 'strings_to_formulas': False}) as writer:
				df = pd.DataFrame(csv_file[1:], columns=csv_file[0])
				df.to_excel(writer, sheet_name = "Sheet1", header = True, index = False)
		f = open(file_path, 'rb')
		if download_report_id !=None:
			download_report = DownloadReports.objects.get(id=download_report_id)
			download_report.downloaded_file.save(os.path.basename(f.name), File(f), save=True)
			download_report.is_start = False
			download_report.save()
		f.close()
		if not download_report_id:
			full_name = user.first_name+" "+user.last_name
			encode_file_name = "download/"+datetime.now().strftime("%m.%d.%Y")+"/"+str(user.id)+"/"+str(user.id)+'_'+str(report_name)+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".csv"
			response = 0 
			try:
				email_sch_obj = EmailScheduler.objects.filter(created_by_id=user.id).first()
				connection = email_connection(email_sch_obj.emails['from'],email_sch_obj.emails['password'])
				email_sch_obj = EmailScheduler.objects.all()
				for emails_obj in email_sch_obj:
					email_report_names = [email_report_name.replace(" ","").lower() for email_report_name in emails_obj.reports]
					download_report_name  = []
					user_id = User.objects.get(username=user).id
					if report_name.replace("_","").lower() in email_report_names and user_id == emails_obj.created_by_id:
						subject = report_name.title() +'Reports Of '+datetime.today().date().strftime('%Y-%m-%d')
						#encode the file name
						sample_string_bytes = encode_file_name.encode("ascii") 
						  
						base64_bytes = base64.b64encode(sample_string_bytes) 
						base64_string = base64_bytes.decode("ascii") 
						html_content = """
						<p>
						Hello {0},<br>
						Kindly click the below link to download {1} report of  {2}
						<br>
						<a href='http://{3}/api/download-scheduled-report/{4}'>Download Report</a>
						""".format(full_name, report_name,datetime.today().date().strftime('%Y-%m-%d'),settings.IP_ADDRESS,base64_string)
						from_email = emails_obj.emails['from']
						to = emails_obj.emails['to']
						msg = EmailMultiAlternatives(subject,"",from_email, to,connection=connection)
						msg.attach_alternative(html_content, "text/html")
						response = msg.send()
						save_email_log(report_name,emails_obj.emails['from'],emails_obj.emails['to'],response)
			except Exception as e:
				print('calldetail download error',e)
		if download_report_id !=None:
			os.remove(file_path)
			set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
		transaction.commit()
		connections['crm'].close()      
		connections['default'].close()
	except Exception as e:
		print('save file error',e)



def download_call_detail_report(filters, user, col_list, serializer_class, download_report_id=None):
	"""
	this is the function for download call details reports
	"""	
	try:
		query = {}
		user = User.objects.get(id=user)
		admin = False
		if user.user_role and user.user_role.access_level == 'Admin':
			print(user.user_role,'this is a print statement for user')
			admin = True
		all_campaigns = filters.get("all_campaigns",[])
		if '' in all_campaigns: all_campaigns.remove('')
		all_users = filters.get("all_users",[])
		if '' in all_users:
			all_users.remove('')
			all_users.append(0)
		selected_campaign = filters.get("selected_campaign", "")
		if not selected_campaign:
			selected_campaign = filters.get("all_campaigns", "")
		selected_disposition = filters.get("selected_disposition", "")
		selected_user = filters.get("selected_user", "")
		numeric = filters.get("numeric", "")
		start_date = filters.get("start_date", "")
		end_date = filters.get("end_date", "")
		start_date = datetime.strptime(start_date,"%Y-%m-%d %H:%M").isoformat()
		end_date = datetime.strptime(end_date,"%Y-%m-%d %H:%M").isoformat()
		unique_id = filters.get("unique_id","")
		dispo_keys = filters.get("dispo_keys","")
		download_type = filters.get('download_type',"")
		print(download_type,'this is download type')
		uniquefields = filters.get('uniquefields',"")
		if uniquefields:
			uniquefields = uniquefields.split(',')
		dispo_keys = dispo_keys.split(',')
		if '' in dispo_keys: dispo_keys.remove('')
		sql_query_where = ''
		if selected_user:
			all_users = selected_user
		if len(selected_campaign)==1:
			selected_campaign.append(selected_campaign[0])
		if len(all_users) == 1:
			all_users.append(all_users[0])

		if selected_campaign:
			sql_query_where = '''callcenter_calldetail.campaign_name IN {campaigns} AND COALESCE(callcenter_calldetail.user_id, 0) IN {users}'''.format(campaigns=str(tuple(selected_campaign)),users=str(tuple(all_users)))
		else:
			sql_query_where = '''(COALESCE(callcenter_calldetail.user_id, 0) IN {users})'''.format(users=str(tuple(all_users)))
		if selected_user and selected_campaign:
			sql_query_where = '''(COALESCE(callcenter_calldetail.campaign_name, 'DefaultCampaign') IN {campaigns}
			AND COALESCE(callcenter_calldetail.user_id, 0) IN {users})
			'''.format(campaigns=str(tuple(selected_campaign)),users=str(tuple(all_users)))
		elif selected_user:
			sql_query_where = '''(COALESCE(callcenter_calldetail.user_id, 0) IN {users})'''.format(users=str(tuple(all_users)))
		elif selected_campaign:
			if selected_campaign:
				sql_query_where = '''(callcenter_calldetail.campaign_name IN {campaigns})'''.format(campaigns=str(tuple(selected_campaign)))
				if not (user.is_superuser or admin):
					get_camp_users = list(get_campaign_users(selected_campaign,
						user).values_list("id",flat=True))
					if len(get_camp_users) == 1:
						get_camp_users.append(get_camp_users[0])
					sql_query_where = '''((callcenter_calldetail.campaign_name IN {campaigns} AND COALESCE(callcenter_calldetail.user_id, 0) IN {camp_users}))'''.format(campaigns=str(tuple(selected_campaign)), camp_users=str(tuple(get_camp_users)))
		if selected_disposition:
			if len(selected_disposition)==1:
				selected_disposition.append(selected_disposition[0])
			sql_query_where += " and ( callcenter_cdrfeedbck.primary_dispo IN "+str(tuple(selected_disposition))+" ) "
		if numeric:
			sql_query_where += " and ( callcenter_calldetail.customer_cid = '"+str(numeric)+"') "
		if unique_id:
			sql_query_where += " and ( callcenter_calldetail.uniqueid = '"+str(unique_id)+"') "
		where = " WHERE ( callcenter_calldetail.created at time zone 'Asia/Kolkata' between '" + str(start_date)+"' and '" +str(end_date)+"') and "+ sql_query_where + ' order by callcenter_calldetail.created desc'
		sub_dispo = "SELECT "
		for index,col_name in enumerate(col_list, start=1):
			if col_name in CDR_DOWNLOAD_COl:
				if col_name == 'uniqueid':
					if len(uniquefields) != 0 and len(uniquefields) < 2:
						sub_dispo += 'callcenter_calldetail.uniqueid as '+uniquefields[0].split(':')[1]
					else:
						sub_dispo += 'callcenter_calldetail.uniqueid as uniqueid'
				else:
					sub_dispo += CDR_DOWNLOAD_COl[col_name]+" "
			elif col_name in dispo_keys:
				sub_dispo += "callcenter_cdrfeedbck.feedback ->> '"+str(col_name)+"' as "+'"'+str(col_name)+'" '
			if index < len(col_list) and sub_dispo[-2:] != ", ":
				sub_dispo += ", "
		sub_dispo += """from callcenter_calldetail left join callcenter_diallereventlog on callcenter_diallereventlog.session_uuid = callcenter_calldetail.session_uuid left join callcenter_cdrfeedbck on callcenter_cdrfeedbck.calldetail_id=callcenter_calldetail.id left join callcenter_user usr on usr.id = callcenter_calldetail.user_id left join callcenter_user supr on supr.id = usr.reporting_to_id left join (select sms.session_uuid as session_uuid, string_agg(template.name, ', ') as name from callcenter_smslog sms left join callcenter_smstemplate template on sms.template_id = template.id left join callcenter_calldetail calldetail on calldetail.session_uuid = sms.session_uuid where calldetail.campaign_name IN {campaigns} group by sms.session_uuid) sms on sms.session_uuid = callcenter_calldetail.session_uuid """.format(campaigns=str(tuple(selected_campaign))) + where
		download_folder = settings.MEDIA_ROOT+"/download/"+datetime.now().strftime("%m.%d.%Y")+"/"+str(user.id)+"/"
		if not os.path.exists(download_folder):
			os.makedirs(download_folder)
		# file_path = download_folder+str(user.id)+'_'+str('call_details')+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".xls"
		set_download_progress_redis(download_report_id, 25, is_refresh=True)
		db_settings = settings.DATABASES['default']
		db_connection = "postgresql://{user}:{password}@{host}:{port}/{db_name}".format(user = db_settings['USER'], password=db_settings['PASSWORD'], host = db_settings['HOST'], db_name = db_settings['NAME'], port = db_settings['PORT'])
		print(db_connection,'ths is db connection')
		if download_type == 'xls':
			file_path = download_folder+str(user.id)+'_'+str('call_details')+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".xlsx"
			with pd.ExcelWriter(file_path, engine="xlsxwriter",options={'remove_timezone': True}) as writer:
				df = pd.read_sql(sub_dispo,db_connection)
				df.to_excel(writer, sheet_name = "Sheet1", header = True, index = False)
		else:
			file_path = download_folder+str(user.id)+'_'+str('call_details')+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".csv"
			df = pd.read_sql(sub_dispo,db_connection)
			df.to_csv(file_path, index = False)
		file_path_1 =  download_folder+str(user.id)+'_'+str('call_details')+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+"_Tanmoy.csv"
		df.to_csv(file_path_1,index=False)
		subprocess.call(['chmod', '777', file_path])
		f = open(file_path, 'rb')
		download_report = DownloadReports.objects.get(id=download_report_id)
		download_report.downloaded_file.save(os.path.basename(f.name), File(f), save=True)
		download_report.is_start = False
		download_report.save()
		f.close()
#		os.remove(file_path)
		set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
		print("download report completed")
		transaction.commit()
		connections['crm'].close()      
		connections['default'].close()
	except Exception as e:
		transaction.commit()
		connections['crm'].close()      
		connections['default'].close()
		if download_report_id:
			set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
		print('calldetail download error',e)

def action_agent_performance_report(filters,download=False,download_report_id=0):
	# try:
		all_users = filters.get("all_users", [])
		selected_campaign = filters.get("selected_campaign", [])
		start_date = filters.get("start_date", "")
		download_type = "csv"
		selected_user = filters.get('selected_user',"")
		start_date = start_date[:10]

		start_date = datetime.strptime(start_date, '%Y-%m-%d')
		end_date = filters.get("end_date", "")
		# end_date = start_date + timedelta(days=1)
		# start_date = datetime.strptime(start_date,"%Y-%m-%d %H:%M").isoformat()
		page = int(filters.get('page' ,0))
		paginate_by = int(filters.get('paginate_by', 0))
		call_result = [{}]
		pause_breaks = list(set(PauseBreak.objects.values_list('name',flat=True)))
		all_col = ['app_idle_time','dialer_idle_time','pause_progressive_time','progressive_time','preview_time',
					'predictive_wait_time','inbound_wait_time','blended_wait_time','ring_duration','ring_duration_avg','hold_time','media_time','predictive_wait_time_avg','talk','talk_avg','bill_sec','bill_sec_avg','call_duration','feedback_time','feedback_time_avg','break_time','break_time_avg','app_login_time'
					] + pause_breaks + ['dialer_login_time','total_login_time','first_login_time','last_logout_time','total_calls','total_unique_connected_calls']
		if filters.get("start_date_ui",""):
			start_date = filters.get("start_date_ui","")
			start_date = datetime.strptime(start_date, '%Y-%m-%d')

		conn = connections['default']
		agent_activity_query = f'''select user_id,event,min(created) as event_min_time,max(created) as event_max_time,campaign_name,count(user_id) as activity_count,
		sum(break_time) as break_time,sum(pause_progressive_time) as pause_progressive_time,
		sum(predictive_time) as predictive_time,sum(progressive_time) as progressive_time,
		sum(preview_time) as preview_time,sum(predictive_wait_time) as predictive_wait_time,
		sum(inbound_time) as inbound_time,sum(blended_time) as blended_time,
		sum(inbound_wait_time) as inbound_wait_time,sum(blended_wait_time) as blended_wait_time,
		sum(idle_time) as app_idle_time from callcenter_agentactivity 
		where created > '{start_date}' and created < '{end_date}' 
		group by user_id,event,campaign_name'''


		user_query = 'select id,username,first_name,last_name,reporting_to_id from callcenter_user'

		calldetail_query = f'''select user_id,campaign_name,count(distinct customer_cid) as total_unique_connected_calls, 
		count(user_id) as calldetail_count,sum(media_time) as media_time,sum(ring_duration) as ring_duration,
		sum(hold_time) as hold_time,sum(call_duration) as call_duration,sum(bill_sec) as bill_sec,
		sum(feedback_time) as feedback_time from callcenter_calldetail 
		where created > '{start_date}' and created < '{end_date}'
		group by user_id,campaign_name'''

		breaks_activity_query = f'''select user_id,sum(break_time) as break_time,break_type 
		from callcenter_agentactivity  
		where created > '{start_date}' and created < '{end_date}' group by user_id,break_type   '''
		
		agent_activity_df = pd.read_sql_query(agent_activity_query, conn)
		if download:
			set_download_progress_redis(download_report_id, 25, is_refresh=True)
		is_user_obj = False
		if selected_user:
			queryset = User.objects.filter(id__in=selected_user)
			is_user_obj = True
		else:
			if start_date == str(date.today()):
				queryset = User.objects.filter(last_login__date=start_date).filter(id__in=all_users)
				is_user_obj = True
			else:
				queryset_agent = agent_activity_df[['user_id']] #AgentActivity.objects.filter(created__date = start_date).exclude(user_id = None).values('user_id').order_by('-user_id').annotate(count =Count('user_id'))
				queryset_agent = queryset_agent.drop_duplicates(subset='user_id', keep="first")
				queryset = queryset_agent[queryset_agent['user_id'].apply(str).isin(all_users)]
				queryset = queryset.to_dict('records')
				del queryset_agent
		if download:
			users = queryset
		else:
			users = get_paginated_object(queryset, page, paginate_by)
		if download:
			set_download_progress_redis(download_report_id, 37, is_refresh=True)
		if len(queryset) == 0:
			if download:
				return pd.DataFrame(columns=['username','fullname','supervisor']+all_col)
			return call_result,users
		if is_user_obj:
			required_agents =  [user.id for user in users]
		else:
			required_agents =  [user['user_id'] for user in users]
		del queryset
		# All The Required queries

		agent_activity_df_logoutlogin = agent_activity_df[['user_id','event_min_time','event_max_time','event']]
		
		agent_activity_df = agent_activity_df[agent_activity_df['user_id'].isin(required_agents)]
		if selected_campaign:
			agent_activity_df = agent_activity_df[(agent_activity_df['campaign_name'].isin(selected_campaign))]        
		# LOGOUT TImes
		agent_activity_df_condition_in = agent_activity_df_logoutlogin.where((agent_activity_df_logoutlogin['event'] == 'LOGIN') )
		agent_activity_df_condition_out = agent_activity_df_logoutlogin.where((agent_activity_df_logoutlogin['event'] == 'LOGOUT') )

		agent_first_login_df = agent_activity_df_condition_in.groupby(['user_id','event']).agg({'event_min_time':'min'})
		agent_last_logout_df = agent_activity_df_condition_out.groupby(['user_id','event']).agg({'event_max_time':'max'})

		agent_fi_lo = pd.merge(agent_first_login_df,agent_last_logout_df,how='left',on = 'user_id' ).reset_index()
		agent_fi_lo = agent_fi_lo.rename(columns={
			'event_min_time' : 'first_login_time',
			'event_max_time' : 'last_logout_time',
		})
		agent_fi_lo['first_login_time'] = agent_fi_lo['first_login_time'].fillna('-')
		agent_fi_lo['last_logout_time'] = agent_fi_lo['last_logout_time'].fillna('-')
		agent_fi_lo['first_login_time'] = agent_fi_lo['first_login_time'].apply( lambda x:x.strftime("%d-%m-%Y %H:%M:%S") if x != '-' else None)
		agent_fi_lo['last_logout_time'] = agent_fi_lo['last_logout_time'].apply( lambda x:x.strftime("%d-%m-%Y %H:%M:%S") if x != '-' else None)

		del agent_first_login_df,agent_last_logout_df

		if download:
			set_download_progress_redis(download_report_id, 53, is_refresh=True)

		# USER RELATED TABLE CONFIGURATIONS
		user_df = pd.read_sql_query(user_query, conn)
		user_df['full_name'] = user_df[['first_name','last_name']].apply(lambda x:' '.join(x.map(str)), axis=1)
		user_df = user_df.drop(['first_name','last_name'], axis=1)
		user_df['reporting_to_id'] = user_df['reporting_to_id'].fillna(-1)
		new_reporting_df = user_df.copy()
		user_df = user_df[user_df['id'].isin(required_agents)]

		reporting_df = new_reporting_df[['id','username','reporting_to_id']]
		reporting_df = reporting_df.rename(columns = {
			'id':'reporting_tble_id',
			'username':'supervisor_name',
			'reporting_to_id':'supervisor_id'
		})

		# MERGING USER TABLE AND ACTIVITY
		user_df_with_sup = pd.merge(user_df,reporting_df,left_on = 'reporting_to_id',right_on = 'reporting_tble_id',how='left')
		user_main = user_df_with_sup.drop(['reporting_to_id'],axis=1)
		user_agent_activity = pd.merge(agent_activity_df,user_main,right_on='id',left_on='user_id',how='left')
		del agent_activity_df

		all_time_related_cols = ['break_time','pause_progressive_time','predictive_time',
						'progressive_time',
						'preview_time',
						'predictive_wait_time',
						'inbound_time','blended_time','inbound_wait_time',
						'blended_wait_time','app_idle_time']

		# Converting times to seconds
		for time_type in all_time_related_cols:
			user_agent_activity[time_type] = user_agent_activity[time_type].apply( lambda x : to_secs(x)  )

		all_aggr_time_cols = {val:'sum' for val in all_time_related_cols}
		all_aggr_time_cols['campaign_name'] = 'unique'
		user_agent_activity_all_data = user_agent_activity.groupby('user_id').agg(all_aggr_time_cols).reset_index()
		user_agent_activity_all_data['campaign_name'] = user_agent_activity_all_data['campaign_name'].apply(lambda x : ",".join(campaign_join(x)))
		user_agent_activity_all_data['campaign_name'] = user_agent_activity_all_data['campaign_name'].apply(lambda x : x.strip(',') )

		# FOR USER IDLE TIME AND DIALER TIME
		# COllecting user based app_idle_time_filter

		user_agent_activity_condition = user_agent_activity.where((user_agent_activity['campaign_name'].isin([None,'','None'])) |
												(user_agent_activity['event'] == 'DIALER LOGIN'))
		user_agent_activity_gb_user = user_agent_activity_condition.groupby(
									user_agent_activity_condition['user_id'])['app_idle_time'].sum()
		user_agent_activity_gb_user = user_agent_activity_gb_user.to_frame().reset_index()
		user_agent_activity_gb_user = user_agent_activity_gb_user.rename(columns={'app_idle_time': 'user_app_idle_time'})
		if download:
			set_download_progress_redis(download_report_id, 62, is_refresh=True)
		#  Dialler Idle Time

		user_agent_activity_cond_dialer = user_agent_activity.where((~user_agent_activity['campaign_name'].isin([None,'','None'])) &
												(~user_agent_activity['event'].isin(["DIALER LOGIN","LOGOUT"])))
		user_agent_activity_cond_dialer = user_agent_activity_cond_dialer[
			user_agent_activity_cond_dialer['user_id'].notna()]

		user_agent_activity_gb_userdialler = user_agent_activity_cond_dialer.groupby(
									user_agent_activity_cond_dialer['user_id'])['app_idle_time'].sum()
		user_agent_activity_gb_userdialler = user_agent_activity_gb_userdialler.to_frame().reset_index()
		user_agent_activity_gb_userdialler = user_agent_activity_gb_userdialler.rename(columns={'app_idle_time': 'dialer_app_idle_time'})

		agent_activity_main = pd.merge(user_agent_activity_all_data,user_agent_activity_gb_user,on='user_id',how='left') 
		agent_activity_main_updated = pd.merge(agent_activity_main,user_agent_activity_gb_userdialler,on='user_id',how='left') 

		agent_activity_main_withuser = pd.merge(agent_activity_main_updated,user_main,left_on='user_id',right_on='id',how='left')

		agent_activity_main_withuser = pd.merge(agent_activity_main_withuser,agent_fi_lo,on='user_id',how='left')
		del user_main
		del agent_activity_main_updated
		agent_activity_main_withuser = agent_activity_main_withuser.drop(['id'], axis=1)

		if download:
			set_download_progress_redis(download_report_id, 67, is_refresh=True)
		# CALLDETAILS 
		calldetail_df = pd.read_sql_query(calldetail_query, conn)
		calldetails_timecols = ['media_time','ring_duration','hold_time','call_duration','bill_sec','feedback_time',]
		for time_type in calldetails_timecols:
			calldetail_df[time_type] = calldetail_df[time_type].apply( lambda x : to_secs(x)  )

		# calldetails with campaign
		if selected_campaign:
			calldetail_df = calldetail_df[calldetail_df['campaign_name'].isin(selected_campaign)]    

		calldetail_df_without_camp = calldetail_df.groupby('user_id').agg({
								'total_unique_connected_calls':'sum',
								'calldetail_count':'sum','media_time':'sum','ring_duration':'sum','hold_time':'sum',
								'call_duration':'sum','bill_sec':'sum','feedback_time':'sum'
							}).reset_index()
		del calldetail_df
		apr_main = pd.merge(agent_activity_main_withuser,calldetail_df_without_camp,on='user_id',how='left')
		del calldetail_df_without_camp,agent_activity_main_withuser
		# ALL AVERAGES 
		required_agents_ids = None
		if download:
			set_download_progress_redis(download_report_id, 70, is_refresh=True)
		if len(apr_main):
			apr_main['talk'] = apr_main['bill_sec'] + apr_main['feedback_time'] + apr_main['ring_duration']
			apr_main['customer_talk'] = apr_main['bill_sec'] + apr_main['ring_duration']
			apr_main['break_time_avg'] = apr_main['break_time']/apr_main['calldetail_count'] 
			apr_main['talk_avg'] = apr_main['talk']/apr_main['calldetail_count']
			apr_main['feedback_time_avg'] = apr_main['feedback_time']/apr_main['calldetail_count']
			apr_main['bill_sec_avg'] = apr_main['customer_talk']/apr_main['calldetail_count']
			apr_main['ring_duration_avg'] =apr_main['ring_duration']/apr_main['calldetail_count']
			apr_main['predictive_wait_time_avg'] = apr_main['predictive_wait_time']/apr_main['calldetail_count']
			apr_main['dialer_login_time'] = apr_main['pause_progressive_time']+ apr_main['predictive_wait_time'] + apr_main['preview_time']+ apr_main['inbound_wait_time'] +apr_main['blended_wait_time']+ apr_main['dialer_app_idle_time']+ apr_main['call_duration']+ apr_main['feedback_time']+ apr_main['progressive_time']
			apr_main['total_login_time'] = apr_main['dialer_login_time'] + apr_main['user_app_idle_time']+ apr_main['break_time']
			required_agents_ids = apr_main['user_id'].tolist()
			apr_main = apr_main.drop('app_idle_time',axis=1)
			apr_main = apr_main.rename(columns = {'user_app_idle_time':'app_idle_time','campaign_name':'campaign','calldetail_count':'total_calls'
													, 'dialer_app_idle_time':'dialer_idle_time'})
			apr_main[['first_login_time','last_logout_time']] = apr_main[['first_login_time','last_logout_time']].fillna('None')
			apr_main[['app_login_time']] = apr_main[['dialer_login_time']] 
			apr_main = apr_main[['app_idle_time','app_login_time','bill_sec','bill_sec_avg',
							'blended_time','blended_wait_time','break_time','break_time_avg',
							'call_duration','campaign','dialer_idle_time','dialer_login_time','feedback_time',
							'feedback_time_avg','first_login_time','full_name','hold_time','inbound_time',
							'inbound_wait_time','last_logout_time','media_time','pause_progressive_time',
							'predictive_time','predictive_wait_time','predictive_wait_time_avg','preview_time',
							'progressive_time','ring_duration','ring_duration_avg','talk','talk_avg','total_calls'
							,'total_login_time','total_unique_connected_calls','username','user_id','supervisor_name']]

			apr_main['supervisor_name'] = apr_main['supervisor_name'].fillna('')
			all_exist_breaks_query = '''select name from callcenter_pausebreak '''
			del all_exist_breaks_query
			breaks_activity_df = pd.read_sql_query(breaks_activity_query, conn)
			# if(len(all_exist_breaks_list)):
			all_exist_breaks_list = pause_breaks.copy()
			is_breaks_work = False
			try:
				for i in all_exist_breaks_list:
					breaks_activity_df[i] = timedelta(seconds=0)
				breaks_activity_df['break_type'] = breaks_activity_df['break_type'].replace(r'^\s*$', np.nan, regex=True)
				breaks_activity_df[['break_type']] = breaks_activity_df[['break_type']].fillna('None')
				breaks_activity_df.drop(breaks_activity_df[breaks_activity_df.break_type == 'None' ].index, inplace=True)
				breaks_activity_df = breaks_activity_df.reset_index()
				breaks_activity_df = breaks_activity_df.drop(['index'],axis=1)
				for each in range(len(breaks_activity_df)):
					if breaks_activity_df["break_type"][each] in all_exist_breaks_list:
						col_name = breaks_activity_df["break_type"][each] 
						breaks_activity_df[col_name][each] = breaks_activity_df["break_time"][each]
				if required_agents_ids:
					breaks_activity_df = breaks_activity_df[(breaks_activity_df['user_id'].isin(required_agents_ids))]

				breaks_activity_df = breaks_activity_df.drop(['break_time'],axis=1)

				all_break_aggr = {val:'sum' for val in all_exist_breaks_list}
				breaks_activity_df = breaks_activity_df.groupby('user_id').agg(all_break_aggr).reset_index()
				final_dataframe  = pd.merge(apr_main,breaks_activity_df,on='user_id',how='left')
				is_breaks_work = True
			except:
				final_dataframe = apr_main.copy()
				pass
			del breaks_activity_df,apr_main
			final_dataframe[['total_unique_connected_calls','total_calls']] = final_dataframe[['total_unique_connected_calls','total_calls']].fillna(0)
			final_dataframe = final_dataframe.fillna(pd.Timedelta(seconds=0))
			final_timecols = ['break_time','pause_progressive_time','predictive_time','progressive_time','preview_time',
								'predictive_wait_time','inbound_time','blended_time','inbound_wait_time','blended_wait_time',
								'app_idle_time','dialer_idle_time','media_time','ring_duration','hold_time','call_duration',
								'bill_sec','feedback_time','talk','break_time_avg','talk_avg','feedback_time_avg',
								'bill_sec_avg','ring_duration_avg','predictive_wait_time_avg','dialer_login_time','total_login_time','app_login_time',
							]
			
			final_dataframe[final_timecols] = final_dataframe[final_timecols].fillna(convert_to_hrs(0))
			for time_type in final_timecols:
				final_dataframe[time_type] = final_dataframe[time_type].apply( lambda x : to_secs(x))
				final_dataframe[time_type] = final_dataframe[time_type].apply( lambda x : convert_to_hrs(x))
			final_dataframe = final_dataframe.drop(['user_id'],axis=1)
			final_dataframe = final_dataframe.fillna(pd.Timedelta(seconds=0))
			if is_breaks_work:
				for val in all_exist_breaks_list:
					final_dataframe[val] = final_dataframe[val].apply( lambda x : to_secs(x)  )
					final_dataframe[val] = final_dataframe[val].apply(lambda x : convert_to_hrs(x))
			finall = final_dataframe.copy() 
			if download:
				set_download_progress_redis(download_report_id, 90, is_refresh=True)
				return final_dataframe
			cols = list(final_dataframe.columns)
			call_result_old = [dict(zip(cols, i)) for i in final_dataframe.values]
			call_result = call_result_old[::-1]
		if download:
			return pd.DataFrame(columns=['username','fullname','supervisor']+all_col)
		return call_result,users
	# except Exception as e:
	# 	print("ERROR in agent_perorm",e)
	# 	exc_type, exc_obj, exc_tb = sys.exc_info()
	# 	fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
	# 	print(exc_type, fname, exc_tb.tb_lineno)
	# if download:
	# 	return None
	# return None,None



# def download_call_detail_report(filters, user, col_list, serializer_class, download_report_id=None):
# 	"""
# 	this is the function for download call details reports
# 	"""	
# 	try:
# 		vary=datetime.now().time()
# 		print(vary,"starting time====")
# 		query = {}
# 		user = User.objects.get(id=user)
# 		admin = False
# 		if user.user_role and user.user_role.access_level == 'Admin':
# 			admin = True
# 		all_campaigns = filters.get("all_campaigns",[])
# 		if '' in all_campaigns: all_campaigns.remove('')
# 		all_users = filters.get("all_users",[])
# 		if '' in all_users:
# 			all_users.remove('')
# 			all_users.append(0)
# 		selected_campaign = filters.get("selected_campaign", "")
# 		selected_disposition = filters.get("selected_disposition", "")
# 		selected_user = filters.get("selected_user", "")
# 		numeric = filters.get("numeric", "")
# 		start_date = filters.get("start_date", "")
# 		end_date = filters.get("end_date", "")
# 		start_date = datetime.strptime(start_date,"%Y-%m-%d %H:%M").isoformat()
# 		end_date = datetime.strptime(end_date,"%Y-%m-%d %H:%M").isoformat()
# 		vary2=datetime.now().time()
# 		print(vary2,"before query =======")
# 		unique_id = filters.get("unique_id","")
# 		dispo_keys = filters.get("dispo_keys","")
# 		download_type = filters.get('download_type',"")
# 		uniquefields = filters.get('uniquefields',"")
# 		if uniquefields:
# 			uniquefields = uniquefields.split(',')
# 		dispo_keys = dispo_keys.split(',')
# 		if '' in dispo_keys: dispo_keys.remove('')
# 		sql_query_where = ''
# 		if selected_user:
# 			all_users = selected_user
# 		if len(selected_campaign)==1:
# 			selected_campaign.append(selected_campaign[0])
# 		if len(all_users) == 1:
# 			all_users.append(all_users[0])

# 		if selected_campaign:
# 			sql_query_where = ' ((callcenter_calldetail.campaign_name IN '+str(tuple(selected_campaign))+' AND callcenter_calldetail.user_id IN '+str(tuple(all_users))+') OR ( callcenter_calldetail.campaign_name IN '+str(tuple(selected_campaign))+' AND callcenter_calldetail.user_id IS NULL ))'
# 		else:
# 			sql_query_where = ' ((callcenter_calldetail.user_id IN '+str(tuple(all_users))+') OR ( callcenter_calldetail.user_id IS NULL ))'
# 		if selected_user and selected_campaign:
# 			sql_query_where = ' (callcenter_calldetail.campaign_name IN '+str(tuple(selected_campaign))+' AND callcenter_calldetail.user_id IN '+str(tuple(all_users))+') '
# 		elif selected_user:
# 			sql_query_where = ' (callcenter_calldetail.user_id IN '+str(tuple(all_users))+' ) '
# 		elif selected_campaign:
# 			if selected_campaign:
# 				sql_query_where = ' (callcenter_calldetail.campaign_name IN '+str(tuple(selected_campaign))+' ) '
# 				if not (user.is_superuser or admin):
# 					get_camp_users = list(get_campaign_users(selected_campaign,
# 						user).values_list("id",flat=True))
# 					if len(get_camp_users) == 1:
# 						get_camp_users.append(get_camp_users[0])
# 					sql_query_where = ' ((callcenter_calldetail.campaign_name IN '+str(tuple(selected_campaign))+' AND callcenter_calldetail.user_id IN '+str(tuple(get_camp_users))+') OR ( callcenter_calldetail.campaign_name IN '+str(tuple(selected_campaign))+' AND callcenter_calldetail.user_id IS NULL ))'
# 		if selected_disposition:
# 			if len(selected_disposition)==1:
# 				selected_disposition.append(selected_disposition[0])
# 			sql_query_where += " and ( callcenter_cdrfeedbck.primary_dispo IN "+str(tuple(selected_disposition))+" ) "
# 		if numeric:
# 			sql_query_where += " and ( callcenter_calldetail.customer_cid = '"+str(numeric)+"') "
# 		if unique_id:
# 			sql_query_where += " and ( callcenter_calldetail.uniqueid = '"+str(unique_id)+"') "
# 		where = " WHERE ( callcenter_calldetail.created at time zone 'Asia/Kolkata' >= '" + str(start_date)+"' and callcenter_calldetail.created at time zone 'Asia/Kolkata' <= '" +str(end_date)+"') and "+ sql_query_where + ' order by callcenter_calldetail.created desc'
# 		sub_dispo = "SELECT "
# 		for index,col_name in enumerate(col_list, start=1):
# 			if col_name in CDR_DOWNLOAD_COl:
# 				if col_name == 'uniqueid':
# 					if len(uniquefields) != 0 and len(uniquefields) < 2:
# 						sub_dispo += 'callcenter_calldetail.uniqueid as '+uniquefields[0].split(':')[1]
# 					else:
# 						sub_dispo += 'callcenter_calldetail.uniqueid as uniqueid'
# 				else:
# 					sub_dispo += CDR_DOWNLOAD_COl[col_name]+" "
# 			elif col_name in dispo_keys:
# 				sub_dispo += "callcenter_cdrfeedbck.feedback ->> '"+str(col_name)+"' as "+'"'+str(col_name)+'" '
# 			if index < len(col_list) and sub_dispo[-2:] != ", ":
# 				sub_dispo += ", "
# 		sub_dispo += "from callcenter_calldetail left join callcenter_diallereventlog on callcenter_diallereventlog.session_uuid = callcenter_calldetail.session_uuid left join callcenter_cdrfeedbck on callcenter_cdrfeedbck.calldetail_id=callcenter_calldetail.id left join callcenter_user usr on usr.id = callcenter_calldetail.user_id left join callcenter_user supr on supr.id = usr.reporting_to_id left join (select sms.session_uuid as session_uuid, string_agg(template.name, ', ') as name from callcenter_smslog sms left join callcenter_smstemplate template on sms.template_id = template.id group by sms.session_uuid) sms on sms.session_uuid = callcenter_calldetail.session_uuid " + where
# 		download_folder = settings.MEDIA_ROOT+"/download/"+datetime.now().strftime("%m.%d.%Y")+"/"+str(user.id)+"/"
# 		if not os.path.exists(download_folder):
# 			os.makedirs(download_folder)
# 		# file_path = download_folder+str(user.id)+'_'+str('call_details')+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".xls"
# 		set_download_progress_redis(download_report_id, 25, is_refresh=True)
# 		db_settings = settings.DATABASES['default']
# 		db_connection = "postgresql://{user}:{password}@{host}:{port}/{db_name}".format(user = db_settings['USER'], password=db_settings['PASSWORD'], host = db_settings['HOST'], db_name = db_settings['NAME'], port = db_settings['PORT'])
# 		if download_type == 'xls':
# 			file_path = download_folder+str(user.id)+'_'+str('call_details')+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".xlsx"
# 			with pd.ExcelWriter(file_path, engine="xlsxwriter",options={'remove_timezone': True}) as writer:
# 				df = pd.read_sql(sub_dispo,db_connection)
# 				df.to_excel(writer, sheet_name = "Sheet1", header = True, index = False)
# 		else:
# 			file_path = download_folder+str(user.id)+'_'+str('call_details')+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".csv"
# 			df = pd.read_sql(sub_dispo,db_connection)
# 			df.to_csv(file_path, index = False)
# 		vary3=datetime.now().time()
# 		print(vary3,"ending time====")
# 		subprocess.call(['chmod', '777', file_path])
# 		f = open(file_path, 'rb')
# 		download_report = DownloadReports.objects.get(id=download_report_id)
# 		download_report.downloaded_file.save(os.path.basename(f.name), File(f), save=True)
# 		download_report.is_start = False
# 		download_report.save()
# 		f.close()
# 		os.remove(file_path)
# 		set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
# 		print("download report completed")
# 		transaction.commit()
# 		connections['crm'].close()      
# 		connections['default'].close()
# 	except Exception as e:
# 		transaction.commit()
# 		connections['crm'].close()      
# 		connections['default'].close()
# 		if download_report_id:
# 			set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
# 		print('calldetail download error',e)

def DownloadCssQuery(filters, download_report_id, user):
	"""
	this is the function for download download css query reports
	"""	
	try:
		query_string = filters["query"]
		user = User.objects.get(id=user)
		contact = Contact.objects.raw(query_string)
		data=ContactListSerializer(contact, many=True).data
		fields = []
		fields.extend(['campaign','phonebook','user','numeric','alt_numeric','first_name','last_name','disposition','churncount','dial_count','last_dialed_date','last_connected_user','created_date','modified_date','priority','uniqueid','status'])
		final_data = []
		count = 0
		data = list(data)
		for contact_detail in data:
			row_data = []
			contact_detail = dict(contact_detail)
			for i in fields:
				if i in contact_detail:
					row_data.append(contact_detail[i])
			for contact_info, contact_data in contact_detail["contact_info"].items():
				temp_key = contact_info
				for key,value in contact_data.items():
					dummy_key = temp_key+":"+key
					if dummy_key not in fields:
						fields.append(dummy_key)
					row_data.append(value)
			final_data.append(row_data)
			count += 1
			percentage = ((count)/(len(data)))*100
			set_download_progress_redis(download_report_id, round(percentage,2))
		final_data.insert(0, fields)
		####### To save file ###########
		save_file(final_data, download_report_id, 'cssquery',user)
	except Exception as e:
		print("Error in download css query", e)

def agentactivity_data(start_date,request):
	"""
	Agent Activity data from backup table 
	"""
	data = {}
	queryset = AgentActivitybk.objects.filter(date=start_date)
	selected_user = request.POST.getlist("selected_user", [])
	selected_campaign = request.POST.getlist("selected_campaign", [])
	all_users = request.POST.get("all_users",[])
	if selected_user:
		users = list(User.objects.filter(id__in=selected_user).values_list("username",flat=True))
		queryset = queryset.filter(username__in=users)
	if selected_campaign:
		queryset = queryset.filter(campaign__in=selected_campaign)
	page = int(request.POST.get('page' ,1))
	paginate_by = int(request.POST.get('paginate_by', 10))
	agent_data = list(queryset.values())
	users = get_paginated_object(queryset, page, paginate_by)
	data['total_records'] = users.paginator.count
	data['total_pages'] = users.paginator.num_pages
	data['page'] = users.number
	data['start_index'] = users.start_index()
	data['end_index'] = users.end_index()
	data['has_next'] = users.has_next()
	data['has_prev'] = users.has_previous()
	data['table_data'] = agent_data[::-1]
	return data

def backup_agentdata(csv=[]):
	"""
	This function will call in download_agent_performance function to
	get data and create or bulk_create at AgentActivitybk table 
	"""
	try:
		dataframe = pd.DataFrame(csv[1:],columns=csv[0])
		AgentActivitybk.objects.bulk_create(
		AgentActivitybk(**vals) for vals in dataframe.to_dict('records'))
		
	except Exception as e:
		print("Error at backup_agentdata function ", e)

def download_from_bkapr(filters,user,col_list,download_report_id):
	try:
		download_folder = settings.MEDIA_ROOT+"/download/"
		selected_campaign = filters.get("selected_campaign", [])
		selected_user = filters.get("selected_user", [])
		start_date = filters.get("start_date", "")
		selected_date = start_date[:10]
		download_type = filters.get('download_type',"")
		file_path = download_folder + str(user)+'_'+"agent_performance_report"+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))
		selected_usernames = list(User.objects.filter(id__in=selected_user).values_list("username",flat=True))
		agentactivity_data = AgentActivitybk.objects.filter(date=selected_date)#,users__in=users,campaign__in=selected_campaign).values()
		if selected_campaign:
			agentactivity_data = agentactivity_data.filter(campaign__in=selected_campaign)
		if selected_user:
			agentactivity_data = agentactivity_data.filter(username__in=selected_usernames)
		agentactivity_data = list(agentactivity_data.values())
		df = pd.DataFrame(agentactivity_data)
		#change all columns to lower case
		final_clmns = []
		for col in col_list:
			clmn=col.lower().replace(" ","_")
			final_clmns.append(clmn)
		df = df[final_clmns]
	
		if download_type == 'xls':
			file_path = file_path + ".xls"
			with pd.ExcelWriter(file_path, engine="xlsxwriter",options={'remove_timezone': True}) as writer:
				df.to_excel(writer, sheet_name = "Sheet1", header = True, index = False)
		else:
			file_path = file_path + ".csv"
			df.to_csv(file_path)

	except Exception as e:
		print("exception from download from bkapr ",e)

def move_agent_performance_report(start_date=datetime.today() - timedelta(days=1),script=False):
	try:
		selected_date = start_date.strftime('%Y-%m-%d 00:00')
		filters={'start_date':selected_date,'download_type':"backup"}
		col_list = ['username', 'full_name', 'supervisor_name', 'campaign', 'app_idle_time', 'dialer_idle_time', 'pause_progressive_time', 'progressive_time', 'preview_time', 'predictive_wait_time', 'inbound_wait_time', 'blended_wait_time', 'ring_duration', 'ring_duration_avg', 'hold_time', 'media_time', 'predictive_wait_time_avg', 'talk', 'talk_avg', 'bill_sec', 'bill_sec_avg', 'call_duration', 'feedback_time', 'feedback_time_avg', 'break_time', 'break_time_avg', 'app_login_time', 'tea_break', 'lunch_break', 'breakfast_break', 'meeting', 'dinner_break', 'dialer_login_time', 'total_login_time', 'first_login_time', 'last_logout_time', 'total_calls', 'total_unique_connected_calls']
		user = User.objects.filter(username='admin').first().id
		download_report_id = None
		if script:
			filters['script'] = True

		agent_qs = AgentActivity.objects.filter(created__date=selected_date[:10])
		
		if agent_qs:
			old_download_agent_perforance_report(filters, user,col_list,download_report_id)
			# agent_qs.delete()
			print("!!! DATA MOVED AT callcenter_agentactivitybk table from callcenter_agentactivity of date  !!! ",selected_date[:10])
		else:
			print("!!! DATA NOT AVAILABLE FOR DATE !!!",selected_date[:10])
	except Exception as e:
		print(" !!! Exception from move_agent_performance_report  !!!",e)

def to_secs(delta):
		if delta: 
			if delta.__class__.__name__ == 'Timedelta':
				return delta.total_seconds()
			else:
				return delta
		else:
			return timedelta(hours=0,minutes=0,seconds=0).total_seconds()
			
def convert_to_hrs(secondss):
	""" agent performance timdelta to 24 hours """
	# print(secondss,'secondsssecondss',type(secondss))
	if secondss == 'NaT' or secondss.__class__.__name__ == 'NaTType' or secondss == 'nan' or secondss == 'NaN':
		duration = timedelta(seconds=0)
	else:
		try:
			duration = timedelta(seconds=secondss)
		except:
			return "00:00:00"
	if duration:
		try:
			days, seconds = duration.days, duration.seconds
			hours = days * 24 + seconds // 3600
			minutes = (seconds % 3600) // 60
			seconds = seconds % 60
			if hours < 10:
				hours = "0"+str(hours)
			if minutes < 10:
				minutes = "0"+str(minutes)
			if seconds < 10:
				seconds = "0"+str(seconds)
			timeformat = str(hours)+":"+ str(minutes)+":"+str(seconds)
			return timeformat
		except Exception as e:
			return "00:00:00"
	else:
		return "00:00:00" 
def campaign_join(camp):
	# return camp[camp!='']
	
	return [i for i in list(camp[camp != np.array(None)]) if i!=""]



def download_agent_perforance_report(filters, user, col_list, download_report_id):
	try:
		logged_in_user = User.objects.get(id=user)
		call_result = action_agent_performance_report(filters,True,download_report_id)
		pd_to_csv(call_result,download_report_id,'agent_performance', logged_in_user, 'csv')
	except Exception as e:
		print(e,"download_agent_perforance_report")
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print(exc_type, fname, exc_tb.tb_lineno)

# def old_download_agent_perforance_report(filters, user, col_list, download_report_id):
# 	"""
# 	this is the function for download agent performance  reports
# 	"""	
# 	try:
# 		query = {}
# 		csv_file = []
# 		count=0
# 		logged_in_user = User.objects.get(id=user)
# 		all_users = filters.get("all_users",[])
# 		selected_campaign = filters.get("selected_campaign", [])
# 		selected_user = filters.get("selected_user", [])
# 		start_date = filters.get("start_date", "")
# 		start_date = start_date[:10]
# 		script = filters.get("script", False)
# 		if start_date != str(date.today()) and (not script): 
# 			download_from_bkapr(filters,user,col_list,download_report_id)
		
# 		download_type = filters.get('download_type',"")
# 		agentactivity_users = list(AgentActivity.objects.filter(created__date=start_date).values_list("user__id",flat=True))
# 		queryset = User.objects.filter(last_login__date=start_date)
# 		# users
# 		if selected_user:
# 			queryset = queryset.filter(id__in=selected_user)
# 		if selected_campaign: 
# 			queryset = Campaign.objects.filter(campaign_name__in=selected_campaign)
# 			camp_user_ids = list(queryset.values_list("users__id",flat=True))
# 			queryset = queryset.filter(id__in=camp_user_ids)

# 		queryset = queryset.order_by("username")
# 		app_idle_time_filter = Q(campaign_name='')|Q(event='DIALER LOGIN')
# 		dialler_idle_time_filter = ~Q(campaign_name="")&~Q(event__in=["DIALER LOGIN","LOGOUT"])
# 		default_time = timedelta(seconds=0)
		
# 		if "" in col_list:
# 			col_list.remove("")

# 		col_list.append('date')
# 		csv_file.append(col_list)
# 		# date_range = pd.date_range(start_date,end_date)
# 		for user in queryset:
# 			user = User.objects.filter(id=user.id).prefetch_related(Prefetch('calldetail_set',queryset=CallDetail.objects.filter(created__date=start_date).filter(user=user)),Prefetch('agentactivity_set',queryset=AgentActivity.objects.filter(created__date=start_date).filter(user=user))).first()
 			
# 			if selected_campaign:
# 				calldetail = user.calldetail_set.filter(campaign_name__in=selected_campaign)
# 				agentactivity = user.agentactivity_set.filter(Q(campaign_name__in=selected_campaign)|Q(
# 					event="DIALER LOGIN")|Q(campaign_name=''))
# 			else:
# 				calldetail = user.calldetail_set
# 				agentactivity = user.agentactivity_set

# 			calldetail_cal = calldetail.aggregate(media_time=Cast(Coalesce(Sum('media_time'),default_time),TimeField()),
# 				ring_duration=Cast(Coalesce(Sum('ring_duration'),default_time),TimeField()),
# 				hold_time=Cast(Coalesce(Sum('hold_time'),default_time),TimeField()),
# 				call_duration=Cast(Coalesce(Sum('call_duration'),default_time),TimeField()),
# 				bill_sec=Cast(Coalesce(Sum('bill_sec'),default_time),TimeField()),
# 				feedback_time=Cast(Coalesce(Sum('feedback_time'),default_time),TimeField()),
# 				)
# 			activity_cal = agentactivity.aggregate(break_time=Cast(Coalesce(Sum('break_time'),default_time),TimeField()),
# 				pause_progressive_time=Cast(Coalesce(Sum('pause_progressive_time'),default_time),TimeField()),
# 				predictive_time=Cast(Coalesce(Sum('predictive_time'),default_time),TimeField()),
# 				progressive_time=Cast(Coalesce(Sum('progressive_time'),default_time),TimeField()),
# 				preview_time=Cast(Coalesce(Sum('preview_time'),default_time),TimeField()),
# 				predictive_wait_time=Cast(Coalesce(Sum('predictive_wait_time'),default_time),TimeField()),
# 				inbound_time=Cast(Coalesce(Sum('inbound_time'),default_time),TimeField()),
# 				blended_time=Cast(Coalesce(Sum('blended_time'),default_time),TimeField()),
# 				inbound_wait_time=Cast(Coalesce(Sum('inbound_wait_time'),default_time),TimeField()),
# 				blended_wait_time=Cast(Coalesce(Sum('blended_wait_time'),default_time),TimeField()),
# 				app_idle_time=Cast(Coalesce(Sum('idle_time',filter=app_idle_time_filter),default_time),TimeField()),
# 				dialer_idle_time=Cast(Coalesce(Sum('idle_time',filter=dialler_idle_time_filter),default_time),TimeField())
# 				)
# 			break_time_cal= {}
# 			total_calls = calldetail.count()
# 			break_name = list(PauseBreak.objects.values_list('name',flat=True))
# 			for break_cal in break_name:
# 				break_time_cal[break_cal] = agentactivity.filter(break_type=break_cal).aggregate(break_time__sum=Cast(Coalesce(Sum('break_time'),default_time),TimeField())).get('break_time__sum')
# 			pp_time = convert_into_timedelta(activity_cal['pause_progressive_time']).total_seconds()
# 			pw_time = convert_into_timedelta(activity_cal['predictive_wait_time']).total_seconds()
# 			preview_time = convert_into_timedelta(activity_cal['preview_time']).total_seconds()
# 			break_time = convert_into_timedelta(activity_cal['break_time']).total_seconds()
# 			talk_call = convert_into_timedelta(calldetail_cal['bill_sec']).total_seconds()
# 			ring_duration =convert_into_timedelta(calldetail_cal['ring_duration']).total_seconds()
# 			feedback_time =convert_into_timedelta(calldetail_cal['feedback_time']).total_seconds()
# 			talk_total = int(talk_call) + int(feedback_time) + int(ring_duration)
# 			customer_talk = int(talk_call) + int(ring_duration)
# 			calldetail_cal['talk'] = convert_timedelta_hrs(timedelta(seconds=talk_total))
# 			calldetail_cal['bill_sec'] = convert_timedelta_hrs(timedelta(seconds=customer_talk)) 
# 			if total_calls:
# 				break_time_avg = ((convert_into_timedelta(activity_cal['break_time']).total_seconds())/total_calls)
# 				talk_avg = ((int(talk_call)+int(feedback_time)+int(ring_duration))/total_calls)
# 				feedback_time_avg = ((convert_into_timedelta(calldetail_cal['feedback_time']).total_seconds())/total_calls)
# 				customer_avg_talk = ((int(talk_call)+int(ring_duration))/total_calls)
# 				pw_wait_avg = (int(pw_time)/total_calls)
# 				# customer_avg = ((convert_into_timedelta(calldetail_cal['customer']).total_seconds())/total_calls)
# 				calldetail_cal['bill_sec_avg'] = convert_timedelta_hrs(timedelta(seconds=customer_avg_talk))
# 				wait_avg = ((convert_into_timedelta(calldetail_cal['ring_duration']).total_seconds())/total_calls)
# 				calldetail_cal['break_time_avg'] =  convert_timedelta_hrs(timedelta(seconds=break_time_avg))
# 				calldetail_cal['talk_avg'] = convert_timedelta_hrs(timedelta(seconds=talk_avg)) 
# 				calldetail_cal['feedback_time_avg'] =  convert_timedelta_hrs(timedelta(seconds=feedback_time_avg)) 
# 				calldetail_cal['ring_duration_avg'] = convert_timedelta_hrs(timedelta(seconds=wait_avg)) 
# 				activity_cal['predictive_wait_time_avg'] = convert_timedelta_hrs(timedelta(seconds=pw_wait_avg)) 
# 			else:
# 				default_time_delta_sec = timedelta(hours=0,minutes=0,seconds=0).total_seconds()
# 				calldetail_cal['break_time_avg'] = time.strftime("%H:%M:%S", time.gmtime(default_time_delta_sec))
# 				calldetail_cal['talk_avg'] = time.strftime("%H:%M:%S", time.gmtime(default_time_delta_sec))
# 				calldetail_cal['feedback_time_avg'] = time.strftime("%H:%M:%S", time.gmtime(default_time_delta_sec))
# 				calldetail_cal['bill_sec_avg'] = time.strftime("%H:%M:%S", time.gmtime(default_time_delta_sec))
# 				calldetail_cal['ring_duration_avg'] = time.strftime("%H:%M:%S", time.gmtime(default_time_delta_sec))
# 				activity_cal['predictive_wait_time_avg'] = time.strftime("%H:%M:%S", time.gmtime(default_time_delta_sec))
# 			iw_time = convert_into_timedelta(activity_cal['inbound_wait_time']).total_seconds()
# 			bw_time = convert_into_timedelta(activity_cal['blended_wait_time']).total_seconds()
# 			ai_time = convert_into_timedelta(activity_cal['app_idle_time']).total_seconds()
# 			di_time = convert_into_timedelta(activity_cal['dialer_idle_time']).total_seconds()
# 			call_duration = convert_into_timedelta(calldetail_cal['call_duration']).total_seconds()
# 			feedback_time = convert_into_timedelta(calldetail_cal['feedback_time']).total_seconds()
# 			p_time = convert_into_timedelta(activity_cal['progressive_time']).total_seconds()
# 			dialer_login_time = int(pp_time)+int(pw_time)+int(preview_time)+int(iw_time)+int(bw_time)+int(
# 				di_time)+int(call_duration)+int(feedback_time)+int(p_time)
# 			total_login_time = int(dialer_login_time)+int(ai_time)+int(break_time)
# 			calldetail_cal['app_login_time'] = activity_cal['app_idle_time']
# 			calldetail_cal['dialer_login_time'] = time.strftime("%H:%M:%S", time.gmtime(dialer_login_time))
# 			calldetail_cal['total_login_time'] = time.strftime("%H:%M:%S", time.gmtime(total_login_time))
# 			calldetail_cal = {**calldetail_cal, **activity_cal ,**break_time_cal}
# 			calldetail_cal['total_calls'] = calldetail.count()
# 			calldetail_cal['username'] = user.username
# 			calldetail_cal['full_name'] = user.first_name + " " + user.last_name
# 			last_logout_time = ''
# 			first_login_time = ''
# 			if agentactivity.filter(event='LOGOUT').last():
# 				last_logout_time = agentactivity.filter(event='LOGOUT').order_by('created').last().created.strftime("%Y-%m-%d %H:%M:%S")
# 			if agentactivity.filter(event='LOGIN').first():
# 				first_login_time = agentactivity.filter(event='LOGIN').order_by('created').first().created.strftime("%Y-%m-%d %H:%M:%S")
# 			calldetail_cal['last_logout_time'] = last_logout_time
# 			calldetail_cal['first_login_time'] = first_login_time
# 			calldetail_cal['total_unique_connected_calls'] = calldetail.distinct('customer_cid').order_by('customer_cid').count()
# 			calldetail_cal['supervisor_name'] = '' 
# 			if user.reporting_to:
# 				calldetail_cal['supervisor_name'] = user.reporting_to.username
# 			calldetail_cal['date'] = start_date
# 			if selected_campaign:
# 				calldetail_cal['campaign'] = ','.join(selected_campaign)
# 			else:
# 				calldetail_cal['campaign'] = ",".join(list(set(list(user.agentactivity_set.exclude(campaign_name=None).exclude(campaign_name='').values_list("campaign_name",flat=True)))))
# 			row = []
# 			for field in col_list:
# 				row.append(calldetail_cal.get(field,""))
# 			csv_file.append(row)
# 			count += 1
# 			percentage = ((count)/queryset.count()*100)
# 			if download_report_id!=None:
# 				set_download_progress_redis(download_report_id, round(percentage,2))
# 		####### To save file ###########
# 		if download_type == 'backup':
# 			backup_agentdata(csv = csv_file)

# 		if download_type == 'xls':
# 			save_file(csv_file, download_report_id, 'agent_performance', logged_in_user, 'xls')
# 		else:
# 			save_file(csv_file, download_report_id, 'agent_performance', logged_in_user, 'csv')
# 	except Exception as e:
# 		if download_report_id != None:
# 			set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
# 		print('Error in download agent performance report', e)



def campaignwise_performance_report(filters, user, col_list, download_report_id):
	"""
	this is the function for download campaignwise performance reports
	"""	
	try:
		context = writer = {}
		csv_file= []
		count = 0
		admin = False
		user = User.objects.get(id=user)
		all_users = filters.get("all_users", [])
		selected_campaign = filters.get("selected_campaign", [])
		start_date = filters.get("start_date", "")
		end_date = filters.get("end_date", "")
		download_type = filters.get('download_type',"")
		start_date = datetime.strptime(start_date,"%Y-%m-%d %H:%M").isoformat()
		end_date = datetime.strptime(end_date,"%Y-%m-%d %H:%M").isoformat()

		user_list = campaign_list =[]
		admin = False
		if user.user_role and user.user_role.access_level == 'Admin':
			admin = True

		if user.is_superuser or admin:
			if selected_campaign:
				campaign_list = Campaign.objects.filter(name__in=selected_campaign).distinct().values_list("name", flat=True)
			else:
				campaign_list = Campaign.objects.all().distinct().values_list("name", flat=True)
			queryset = campaign_list
		else:
			if selected_campaign:
				camp = Campaign.objects.filter(Q(users=user, users__isnull=False)| Q( group__in=user.group.all(), group__isnull=False), name__in=selected_campaign).distinct()
			else:
				camp = Campaign.objects.filter(Q(users=user, users__isnull=False)| Q( group__in=user.group.all(), group__isnull=False)).distinct()
			queryset = camp
			campaign_list = camp.values_list("name", flat=True)
		campaign_list = list(set(campaign_list))

		if user.user_role and user.user_role.access_level == 'Admin':
			admin = True
		if selected_campaign:
			campaign_list = selected_campaign

		start_end_date_filter = Q(created__gte=start_date)&Q(created__lte=end_date)
		app_idle_time_filter = Q(campaign_name='')|Q(event='DIALER LOGIN')
		dialler_idle_time_filter = ~Q(campaign_name="")&~Q(event__in=["DIALER LOGIN","LOGOUT"])
		default_time = timedelta(seconds=0)
		call_details = CallDetail.objects.filter(start_end_date_filter)
		if "" in col_list:
			col_list.remove("")
		csv_file.append(col_list)
		
		for i in campaign_list:
			calldetail = call_details.filter(campaign_name=i)
			agentactivity = AgentActivity.objects.filter(Q(campaign_name=i)|Q(event="DIALER LOGIN"))
			calldetail_cal = calldetail.aggregate(media_time=Cast(Coalesce(Sum('media_time',filter=start_end_date_filter),default_time),TimeField()),
				ring_duration=Cast(Coalesce(Sum('ring_duration',filter=start_end_date_filter),default_time),TimeField()),
				hold_time=Cast(Coalesce(Sum('hold_time',filter=start_end_date_filter),default_time),TimeField()),
				call_duration=Cast(Coalesce(Sum('call_duration',filter=start_end_date_filter),default_time),TimeField()),
				bill_sec=Cast(Coalesce(Sum('bill_sec',filter=start_end_date_filter),default_time),TimeField()),
				feedback_time=Cast(Coalesce(Sum('feedback_time',filter=start_end_date_filter),default_time),TimeField()),
				)
			activity_cal = agentactivity.aggregate(break_time=Cast(Coalesce(Sum('break_time',filter=start_end_date_filter),default_time),TimeField()),
				pause_progressive_time=Cast(Coalesce(Sum('pause_progressive_time',filter=start_end_date_filter),default_time),TimeField()),
				predictive_time=Cast(Coalesce(Sum('predictive_time',filter=start_end_date_filter),default_time),TimeField()),
				progressive_time=Cast(Coalesce(Sum('progressive_time',filter=start_end_date_filter),default_time),TimeField()),
				preview_time=Cast(Coalesce(Sum('preview_time',filter=start_end_date_filter),default_time),TimeField()),
				predictive_wait_time=Cast(Coalesce(Sum('predictive_wait_time',filter=start_end_date_filter),default_time),TimeField()),
				inbound_time=Cast(Coalesce(Sum('inbound_time',filter=start_end_date_filter),default_time),TimeField()),
				blended_time=Cast(Coalesce(Sum('blended_time',filter=start_end_date_filter),default_time),TimeField()),
				inbound_wait_time=Cast(Coalesce(Sum('inbound_wait_time',filter=start_end_date_filter),default_time),TimeField()),
				blended_wait_time=Cast(Coalesce(Sum('blended_wait_time',filter=start_end_date_filter),default_time),TimeField()),
				app_idle_time=Cast(Coalesce(Sum('idle_time',filter=start_end_date_filter & app_idle_time_filter),default_time),TimeField()),
				dialer_idle_time=Cast(Coalesce(Sum('idle_time',filter=start_end_date_filter & dialler_idle_time_filter),default_time),TimeField())
				)
			pp_time = convert_into_timedelta(activity_cal['pause_progressive_time']).total_seconds()
			pw_time = convert_into_timedelta(activity_cal['predictive_wait_time']).total_seconds()
			preview_time = convert_into_timedelta(activity_cal['preview_time']).total_seconds()
			break_time = convert_into_timedelta(activity_cal['break_time']).total_seconds()
			iw_time = convert_into_timedelta(activity_cal['inbound_wait_time']).total_seconds()
			bw_time = convert_into_timedelta(activity_cal['blended_wait_time']).total_seconds()
			ai_time = convert_into_timedelta(activity_cal['app_idle_time']).total_seconds()
			di_time = convert_into_timedelta(activity_cal['dialer_idle_time']).total_seconds()
			call_duration = convert_into_timedelta(calldetail_cal['call_duration']).total_seconds()
			feedback_time = convert_into_timedelta(calldetail_cal['feedback_time']).total_seconds()
			dialer_login_time = int(pp_time)+int(pw_time)+int(preview_time)+int(iw_time)+int(bw_time)+int(
				di_time)+int(call_duration)+int(feedback_time)
			total_login_time = int(dialer_login_time)+int(ai_time)+int(break_time)
			calldetail_cal['app_login_time'] = activity_cal['app_idle_time']
			calldetail_cal['dialer_login_time'] = time.strftime("%H:%M:%S", time.gmtime(dialer_login_time))
			calldetail_cal['total_login_time'] = time.strftime("%H:%M:%S", time.gmtime(total_login_time))
			calldetail_cal = {**calldetail_cal, **activity_cal}
			calldetail_cal['total_calls'] = calldetail.count()
			row = []
			calldetail_cal['campaign'] = i
			for field in col_list:
				row.append(calldetail_cal.get(field,""))
			csv_file.append(row)
			count += 1
			percentage = ((count)/len(campaign_list))*100
			if download_report_id != None:
				set_download_progress_redis(download_report_id, round(percentage,2))
		####### To save file ###########
		if download_type == 'xls':
			save_file(csv_file, download_report_id, 'campaign_performance', user, 'xls')
		else:
			save_file(csv_file, download_report_id, 'campaign_performance', user, 'csv')
	except Exception as e:
		if download_report_id != None:
			set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
		print('Error in agent mis report download', e)

def download_management_performance_report(filters, user, col_list, download_report_id):
	"""
	this is the function for download management performance  reports
	"""	
	try:
		query = {}
		csv_file = []
		count=0
		logged_in_user = User.objects.get(id=user)
		all_users = filters.get("all_users",[])
		selected_user = filters.get("selected_user", [])
		start_date = filters.get("start_date", "")
		end_date = filters.get("end_date", "")
		start_date = datetime.strptime(start_date,"%Y-%m-%d %H:%M").isoformat()
		end_date = datetime.strptime(end_date,"%Y-%m-%d %H:%M").isoformat()
		download_type = filters.get('download_type',"")
		if selected_user:
			queryset = User.objects.filter(id__in=selected_user)
		else:
			queryset = User.objects.filter(id__in=all_users)
		queryset = queryset.order_by("username")
		# start_end_date_filter = Q(created__gte=start_date)&Q(created__lte=end_date)
		default_time = timedelta(seconds=0)
		if "" in col_list:
			col_list.remove("")
		col_list.append('date')
		csv_file.append(col_list)
		date_range = pd.date_range(start_date,end_date)
		for date , user in itertools.product(date_range, queryset):
			login_duration = default_time
			login_time = logout_time = ''
			management_log_dict = {}
			user = User.objects.filter(id=user.id).prefetch_related(Prefetch('adminlogentry_set',queryset=AdminLogEntry.objects.filter(created__date=date.date()))).first()
			management_log = user.adminlogentry_set
			management_log_dict = management_log.aggregate(login_duration=Cast(Coalesce(Sum('login_duration'),default_time),TimeField()),
				)
			management_log_dict['username'] = user.username
			login = management_log.filter(created__date=date.date(),event_type='LOGIN')
			logout = management_log.filter(created__date=date.date(),event_type='LOGOUT')
			if login.exists():
				login_time = login.first().created
			if logout.exists():
				logout_time = logout.last().created
			# login_duration = convert_into_timeformat(login_time,logout_time)
			management_log_dict['first_login_time'] = login_time.strftime("%Y-%m-%d %H:%M:%S") if login_time else ''
			management_log_dict['last_logout_time'] = logout_time.strftime("%Y-%m-%d %H:%M:%S") if logout_time else ''
			management_log_dict['login_duration'] = management_log_dict['login_duration'].strftime("%H:%M:%S")
			management_log_dict['full_name'] = user.first_name+" "+user.last_name
			management_log_dict['date'] = date.date()
			# log_result.append(management_log_dict)
			row = []
			for field in col_list:
				row.append(management_log_dict.get(field,""))
			csv_file.append(row)
			count += 1
			percentage = ((count)/queryset.count())*100
			if download_report_id != None:
				set_download_progress_redis(download_report_id, round(percentage,2))
		####### To save file ###########
		if download_type == 'xls':
			save_file(csv_file, download_report_id, 'management_performance', user, 'xls')
		else:
			save_file(csv_file, download_report_id, 'management_performance', user, 'csv')
	except Exception as e:
		if download_report_id !=None:
			set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
		print('Error in Management Performance report download', e)

def download_agent_mis(filters, user, col_list, download_report_id):
	"""
	this is the function for download agent mis  reports
	"""	
	try:
		user = logged_in_user = User.objects.get(id=user)
		context = writer = {}
		count = 0
		call_details = user_id = user_campaign = []
		performance_list = csv_file = []
		all_campaigns = filters.get("all_campaigns",[])
		all_users = filters.get("all_users",[])
		selected_campaign = filters.get("selected_campaign", [])
		selected_user = filters.get("selected_user", [])
		start_date = filters.get("start_date", "")
		end_date = filters.get("end_date", "")
		download_type = filters.get('download_type',"")
		start_date = datetime.strptime(start_date,"%Y-%m-%d %H:%M").isoformat()
		end_date = datetime.strptime(end_date,"%Y-%m-%d %H:%M").isoformat()
		all_fields =  list(set(Campaign.objects.all().exclude(disposition=None).values_list("disposition__name", flat=True)))   
		# start_end_date_filter = Q(created__gte=start_date)&Q(created__lte=end_date)
		if selected_user:
			all_users = selected_user
		users = User.objects.filter(id__in=all_users)
		if selected_campaign:
			all_campaigns = selected_campaign
		user_campaign = Campaign.objects.filter(name__in=all_campaigns)

		if "" in col_list:
			col_list.remove("")
		col_list.append('date')
		csv_file.append(col_list)
		date_range = pd.date_range(start_date,end_date)
		for date, user in itertools.product(date_range, users):
			performance_dict = {}
			performance_dict["User"] = user.username
			performance_dict["Full Name"] = user.first_name+" "+user.last_name
			if user.reporting_to:
				performance_dict["Supervisor Name"] = user.reporting_to.username
			campaign = Campaign.objects.filter(Q(users=user)|Q(
				group__in=user.group.all().filter(status="Active"))).filter(
				status="Active").values_list("name", flat=True)
			ucampaign = []
			call_details = CallDetail.objects.filter(created__date=date.date()).filter(Q(campaign_name__in=all_campaigns, user=user)| Q(user=user))
			if campaign.exists():
				ucampaign = list(set(list(campaign)).intersection(selected_campaign))
			performance_dict["Campaign"] = ','.join(ucampaign) if len(ucampaign)>0 else ""
			user_call_detail = call_details.exclude(cdrfeedback=None)
			for dispo_name in all_fields:
				performance_dict[dispo_name] = user_call_detail.filter(cdrfeedback__primary_dispo=dispo_name).count()
			performance_dict["Total Dispo Count"] = user_call_detail.count()
			performance_dict["AutoFeedback"] = user_call_detail.filter(cdrfeedback__primary_dispo="AutoFeedback").count()
			performance_dict["AbandonedCall"] =  call_details.filter(user_id=user,dialed_status="Abandonedcall",cdrfeedback__primary_dispo='').count()
			performance_dict["NC"] = call_details.filter(user_id=user,dialed_status="NC",cdrfeedback__primary_dispo='').count()
			performance_dict["Invalid Number"] = call_details.filter(user_id=user,dialed_status="Invalid Number",cdrfeedback__primary_dispo='').count()
			performance_dict["RedialCount"] = user_call_detail.filter(cdrfeedback__primary_dispo="Redialed").count()
			performance_dict["AlternateDial"] = user_call_detail.filter(cdrfeedback__primary_dispo="AlternateDial").count()
			performance_dict["PrimaryDial"] = user_call_detail.filter(cdrfeedback__primary_dispo="PrimaryDial").count()
			performance_dict["NF(No Feedback)"] = user_call_detail.filter(cdrfeedback__primary_dispo="NF(No Feedback)").count()
			performance_dict["date"] = date.date()
			row = []
			for field in col_list:
				row.append(performance_dict.get(field,""))
			csv_file.append(row)
			count += 1
			percentage = ((count)/(len(date_range)*users.count()))*100
			if download_report_id !=None:
				set_download_progress_redis(download_report_id, round(percentage,2))
		####### To save file ###########
		if download_type == 'xls':
			save_file(csv_file, download_report_id, 'agent_mis', logged_in_user, 'xls')
		else:
			save_file(csv_file, download_report_id, 'agent_mis', logged_in_user, 'csv')
	except Exception as e:
		if download_report_id !=None:
			set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
		print('Error in agent mis report download', e)

def download_agent_activity_report(filters, user, col_list, download_report_id):
	"""
	this is the function for download agent activity reports
	"""	
	try:
		csv_file = []
		count = 0
		user = logged_in_user = User.objects.get(id=user)
		all_campaigns = filters.get("all_campaigns",[])
		if '' in all_campaigns: all_campaigns.remove('')
		all_users = filters.get("all_users",[])
		if '' in all_users:
			all_users.remove('')
			all_users.append(0)
		selected_campaign = filters.get("selected_campaign", [])
		selected_user = filters.get("selected_user", [])
		start_date = filters.get("start_date", "")
		end_date = filters.get("end_date", "")
		download_type = filters.get('download_type',"")
		start_date = datetime.strptime(start_date,"%Y-%m-%d %H:%M").isoformat()
		end_date = datetime.strptime(end_date,"%Y-%m-%d %H:%M").isoformat()
		sql_query_where = ''
		if selected_user:
			all_users = selected_user
		if len(selected_campaign)==1:
			selected_campaign.append(selected_campaign[0])
		if len(all_users) == 1:
			all_users.append(all_users[0])
		if selected_campaign:
			sql_query_where = ' ((callcenter_agentactivity.campaign_name IN '+str(tuple(selected_campaign))+' AND callcenter_agentactivity.user_id IN '+str(tuple(all_users))+') OR ( callcenter_agentactivity.campaign_name IN '+str(tuple(selected_campaign))+' AND callcenter_agentactivity.user_id IS NULL ))'
		else:
			sql_query_where = ' ((callcenter_agentactivity.user_id IN '+str(tuple(all_users))+') OR ( callcenter_agentactivity.user_id IS NULL ))'
		if selected_user and selected_campaign:
			sql_query_where = ' (callcenter_agentactivity.campaign_name IN '+str(tuple(selected_campaign))+' AND callcenter_agentactivity.user_id IN '+str(tuple(all_users))+') '
		elif selected_user:
			sql_query_where = ' (callcenter_agentactivity.user_id IN '+str(tuple(all_users))+' ) '

		where = " WHERE ( callcenter_agentactivity.created at time zone 'Asia/Kolkata' >= '" + str(start_date)+"' and callcenter_agentactivity.created at time zone 'Asia/Kolkata' <= '" +str(end_date)+"') and "+ sql_query_where + ' order by callcenter_agentactivity.created desc'
		query = "SELECT "
		for index,col_name in enumerate(col_list, start=1):
			if col_name == 'user':
				query += 'usr.username as user'+", "
			elif col_name == 'full_name':
				query += 'CONCAT(usr.first_name, ' 'usr.last_name) as full_name'+", "
			elif col_name == 'event_time':
				query = query + "event_time at time zone 'Asia/Kolkata'"
			else: 
				query += col_name+" "
			if index < len(col_list) and query[-2:] != ", ":
					query += ", "
		query += "from callcenter_agentactivity left join callcenter_user usr on usr.id = callcenter_agentactivity.user_id"+ where 
		download_folder = settings.MEDIA_ROOT+"/download/"+datetime.now().strftime("%m.%d.%Y")+"/"+str(user.id)+"/"
		if not os.path.exists(download_folder):
			os.makedirs(download_folder)
		set_download_progress_redis(download_report_id, 25, is_refresh=True)
		db_settings = settings.DATABASES['default']
		db_connection = "postgresql://{user}:{password}@{host}:{port}/{db_name}".format(user = db_settings['USER'], password=db_settings['PASSWORD'], host = db_settings['HOST'], db_name = db_settings['NAME'], port = db_settings['PORT'])
		if download_type == 'xls':
			file_path = download_folder+str(user.id)+'_'+str('agent_activity')+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".xlsx"
			with pd.ExcelWriter(file_path, engine="xlsxwriter",options={'remove_timezone': True, 'strings_to_formulas': False}) as writer:
				df = pd.read_sql(query,db_connection)
				df.to_excel(writer, sheet_name = "Sheet1", header = True, index = False)
		else:
			file_path = download_folder+str(user.id)+'_'+str('agent_activity')+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".csv"
			df = pd.read_sql(query,db_connection)
			df.to_csv(file_path, index = False)
		subprocess.call(['chmod', '777', file_path])
		f = open(file_path, 'rb')
		download_report = DownloadReports.objects.get(id=download_report_id)
		download_report.downloaded_file.save(os.path.basename(f.name), File(f), save=True)
		download_report.is_start = False
		download_report.save()
		f.close()
		os.remove(file_path)
		set_download_progress_redis(download_report_id, 100.0, is_refresh=True)	
		transaction.commit()
		connections['crm'].close()      
		connections['default'].close()
	except Exception as e:
		transaction.commit()
		connections['crm'].close()      
		connections['default'].close()
		if download_report_id:
			set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
		print('agentactivity download error',e)

def download_campaignmis_report(filters, user, col_list, download_report_id):
	"""
	this is the function for download campaign mis  reports
	"""	
	csv_file = []
	count = 0
	user = User.objects.get(id=user)
	all_campaigns = filters.get("all_campaigns",[])
	selected_campaign = filters.get("selected_campaign", [])
	download_type = filters.get('download_type',"")
	start_date = datetime.strptime(filters.get("start_date", ""),"%Y-%m-%d %H:%M").isoformat()
	end_date =  datetime.strptime(filters.get("end_date", ""),"%Y-%m-%d %H:%M").isoformat()
	start_end_date_filter = Q(created__gte=start_date)&Q(created__lte=end_date)
	if selected_campaign:
		user_campaign = Campaign.objects.filter(name__in=selected_campaign)
	else:
		user_campaign = Campaign.objects.filter(name__in=all_campaigns).filter(
				status="Active")
	if "" in col_list:
		col_list.remove("")
	csv_file.append(col_list)
		
	for camp in user_campaign:
		dialed_status= []
		all_fields = []
		all_fields =  list(set(Campaign.objects.filter(name=camp.name).exclude(disposition=None).values_list("disposition__name", flat=True)))
		performance_dict = {}
		performance_dict["Campaign"] = camp.name
		campaign_call_detail = CallDetail.objects.filter(start_end_date_filter).filter(campaign_name=camp.name)
		# session_id = list(campaign_call_detail.values_list("session_uuid", flat=True))
		cdr_feedback = campaign_call_detail.exclude(cdrfeedback=None)
		for dispo_name in all_fields:
			performance_dict[dispo_name] = cdr_feedback.filter(cdrfeedback__primary_dispo=dispo_name).count()
		performance_dict["Total Dispo Count"] = cdr_feedback.count()
		performance_dict["AutoFeedback"] = cdr_feedback.filter(cdrfeedback__primary_dispo="AutoFeedback").count()
		performance_dict["AbandonedCall"] =  campaign_call_detail.filter(dialed_status="Abandonedcall",cdrfeedback__primary_dispo='').count()
		performance_dict["NC"] = campaign_call_detail.filter(dialed_status="NC",cdrfeedback__primary_dispo='').count()
		performance_dict["Invalid Number"] = campaign_call_detail.filter(dialed_status="Invalid Number",cdrfeedback__primary_dispo='').count()
		performance_dict["RedialCount"] = cdr_feedback.filter(cdrfeedback__primary_dispo="Redialed").count()
		performance_dict["AlternateDial"] = cdr_feedback.filter(cdrfeedback__primary_dispo="AlternateDial").count()
		performance_dict["PrimaryDial"] = cdr_feedback.filter(cdrfeedback__primary_dispo="PrimaryDial").count()
		performance_dict["NF(No Feedback)"] = cdr_feedback.filter(cdrfeedback__primary_dispo="NF(No Feedback)").count()
		row = []
		for field in col_list:
			row.append(performance_dict.get(field,""))
		csv_file.append(row)
		count +=1
		percentage = ((count)/(user_campaign.count()))*100
		if download_report_id !=None: 
			set_download_progress_redis(download_report_id, round(percentage,2))
	####### To save file ###########
	if download_type == 'xls':
		save_file(csv_file, download_report_id, 'campaign_mis', user, 'xls')
	else:
		save_file(csv_file, download_report_id, 'campaign_mis', user, 'csv')

def download_callbackcall_report(filters, user, col_list, download_report_id):
	"""
	this is the function for download callback contacts reports
	"""	
	try:
		csv_file = []
		count = 0
		user = User.objects.get(id=user)
		selected_campaign = filters.get("selected_campaign", "")
		selected_user = filters.get("selected_user", "")
		col_name = filters.get("column_name", "").split(",")
		all_users = filters.get("all_users","")
		if type(all_users) == str:
			all_users = all_users.split(',')
		if '' in all_users:
			all_users.remove('')
		start_date = datetime.strptime(filters.get("start_date", ""),"%Y-%m-%d %H:%M").isoformat()
		end_date =  datetime.strptime(filters.get("end_date", ""),"%Y-%m-%d %H:%M").isoformat()
		download_type = filters.get('download_type',"")
		sql_query_where = ''
		if selected_user:
			all_users = selected_user
		if len(selected_campaign)==1:
			selected_campaign.append(selected_campaign[0])
		username = list(User.objects.filter(id__in=list(all_users)).values_list("username", flat=True))
		if not username:
			username.append('')
		if len(username) == 1:
			username.append(username[0])
		if selected_campaign:
			sql_query_where = ' ((callcenter_currentcallback.campaign IN '+str(tuple(selected_campaign))+' AND callcenter_currentcallback.user IN '+str(tuple(username))+') OR ( callcenter_currentcallback.campaign IN '+str(tuple(selected_campaign))+' AND callcenter_currentcallback.user IS NULL ))'
		else:
			sql_query_where = ' ((callcenter_currentcallback.user IN '+str(tuple(username))+') OR ( callcenter_currentcallback.user IS NULL ))'
		if selected_user and selected_campaign:
			sql_query_where = ' (callcenter_currentcallback.campaign IN '+str(tuple(selected_campaign))+' AND callcenter_currentcallback.user IN '+str(tuple(username))+') '
		elif selected_user:
			sql_query_where = ' (callcenter_currentcallback.user IN '+str(tuple(username))+' ) '

		where = " WHERE ( callcenter_currentcallback.schedule_time at time zone 'Asia/Kolkata' >= '" + str(start_date)+"' and callcenter_currentcallback.schedule_time at time zone 'Asia/Kolkata' <= '" +str(end_date)+"') and "+ sql_query_where + ' order by callcenter_currentcallback.schedule_time desc'
		query = "SELECT "
		for index,col_name in enumerate(col_list, start=1):
			if col_name == 'full_name':
				query += 'CONCAT(usr.first_name, ' 'usr.last_name) as full_name'+", "
			elif col_name == 'schedule_date':
				query += 'callcenter_currentcallback.schedule_time as schedule_date'
			else:
				query += col_name+" "
			if index < len(col_list) and query[-2:] != ", ":
					query += ", "
		query += "from callcenter_currentcallback left join callcenter_user usr on usr.username = callcenter_currentcallback.user"+ where
		download_folder = settings.MEDIA_ROOT+"/download/"+datetime.now().strftime("%m.%d.%Y")+"/"+str(user.id)+"/"
		if not os.path.exists(download_folder):
			os.makedirs(download_folder)
		set_download_progress_redis(download_report_id, 25, is_refresh=True)
		db_settings = settings.DATABASES['default']
		db_connection = "postgresql://{user}:{password}@{host}:{port}/{db_name}".format(user = db_settings['USER'], password=db_settings['PASSWORD'], host = db_settings['HOST'], db_name = db_settings['NAME'], port = db_settings['PORT'])
		if download_type == 'xls':
			file_path = download_folder+str(user.id)+'_'+str('pending_callback')+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".xlsx"
			with pd.ExcelWriter(file_path, engine="xlsxwriter",options={'remove_timezone': True}) as writer:
				df = pd.read_sql(query,db_connection)
				df.to_excel(writer, sheet_name = "Sheet1", header = True, index = False)
		else:
			file_path = download_folder+str(user.id)+'_'+str('pending_callback')+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".csv"
			df = pd.read_sql(query,db_connection)
			df.to_csv(file_path, index = False)
		subprocess.call(['chmod', '777', file_path])
		f = open(file_path, 'rb')
		download_report = DownloadReports.objects.get(id=download_report_id)
		download_report.downloaded_file.save(os.path.basename(f.name), File(f), save=True)
		download_report.is_start = False
		download_report.save()
		f.close()
		os.remove(file_path)
		set_download_progress_redis(download_report_id, 100.0, is_refresh=True)	
		transaction.commit()
		connections['crm'].close()      
		connections['default'].close()
	except Exception as e:
		transaction.commit()
		connections['crm'].close()      
		connections['default'].close()
		if download_report_id:
			set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
		print('callbackcontacts download error',e)
	

def download_abandonedcall_report(filters, user, col_list, download_report_id):
	"""
	this is the function for download abandoned reports
	"""	
	try:
		csv_file = []
		count = 0
		user = User.objects.get(id=user)
		selected_campaign = filters.get("selected_campaign", [])
		if '' in selected_campaign:
			selected_campaign.remove('')
		selected_user = filters.get("selected_user", [])
		all_users = filters.get("all_users","")
		if type(all_users) == str:
			all_users = all_users.split(",")
		if '' in all_users:
			all_users.remove('')
		col_name = filters.get("column_name", "").split(",")
		start_date = datetime.strptime(filters.get("start_date", ""),"%Y-%m-%d %H:%M").isoformat()
		end_date =  datetime.strptime(filters.get("end_date", ""),"%Y-%m-%d %H:%M").isoformat()
		download_type = filters.get('download_type',"")
		sql_query_where = ''
		if selected_user:
			all_users = selected_user
		if len(selected_campaign)==1:
			selected_campaign.append(selected_campaign[0])
		if not all_users:
			all_users.append('')
		if len(all_users) == 1:
			all_users.append(all_users[0])
		if selected_campaign:
			sql_query_where = ' ((callcenter_abandonedcall.campaign IN '+str(tuple(selected_campaign))+' AND callcenter_uservariable.extension IN '+str(tuple(all_users))+') OR ( callcenter_abandonedcall.campaign IN '+str(tuple(selected_campaign))+' AND callcenter_abandonedcall.user IS NULL ))'
		else:
			sql_query_where = ' ((callcenter_uservariable.extension IN '+str(tuple(all_users))+') OR ( callcenter_abandonedcall.user IS NULL ))'
		if selected_user and selected_campaign:
			sql_query_where = ' (callcenter_abandonedcall.campaign IN '+str(tuple(selected_campaign))+' AND callcenter_uservariable.extension IN '+str(tuple(all_users))+') '
		elif selected_user:
			sql_query_where = ' (callcenter_uservariable.extension IN '+str(tuple(all_users))+' ) '

		where = " WHERE ( callcenter_abandonedcall.created_date at time zone 'Asia/Kolkata' >= '" + str(start_date)+"' and callcenter_abandonedcall.created_date at time zone 'Asia/Kolkata' <= '" +str(end_date)+"') and "+ sql_query_where + ' order by callcenter_abandonedcall.created_date desc'
		query = "SELECT "
		for index,col_name in enumerate(col_list, start=1):
			if col_name == 'full_name':
				query += 'CONCAT(usr.first_name, ' 'usr.last_name) as full_name'+", "
			elif col_name == 'call_date':
				query += 'callcenter_abandonedcall.created_date as call_date'
			elif col_name == 'username':
				query += 'usr.username as username'
			else: 
				query += 'callcenter_abandonedcall.'+col_name+" "
			if index < len(col_list) and query[-2:] != ", ":
					query += ", "

		query += " from callcenter_abandonedcall left join callcenter_uservariable on callcenter_uservariable.extension = callcenter_abandonedcall.user left join callcenter_user as usr on usr.id=callcenter_uservariable.user_id "+ where
		download_folder = settings.MEDIA_ROOT+"/download/"+datetime.now().strftime("%m.%d.%Y")+"/"+str(user.id)+"/"
		if not os.path.exists(download_folder):
			os.makedirs(download_folder)
		set_download_progress_redis(download_report_id, 25, is_refresh=True)
		db_settings = settings.DATABASES['default']
		db_connection = "postgresql://{user}:{password}@{host}:{port}/{db_name}".format(user = db_settings['USER'], password=db_settings['PASSWORD'], host = db_settings['HOST'], db_name = db_settings['NAME'], port = db_settings['PORT'])
		if download_type == 'xls':
			file_path = download_folder+str(user.id)+'_'+str('abandonnedcall')+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".xlsx"
			with pd.ExcelWriter(file_path, engine="xlsxwriter",options={'remove_timezone': True}) as writer:
				df = pd.read_sql(query,db_connection)
				df.to_excel(writer, sheet_name = "Sheet1", header = True, index = False)
		else:
			file_path = download_folder+str(user.id)+'_'+str('abandonnedcall')+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".csv"
			df = pd.read_sql(query,db_connection)
			df.to_csv(file_path, index = False)
		subprocess.call(['chmod', '777', file_path])
		f = open(file_path, 'rb')
		download_report = DownloadReports.objects.get(id=download_report_id)
		download_report.downloaded_file.save(os.path.basename(f.name), File(f), save=True)
		download_report.is_start = False
		download_report.save()
		f.close()
		os.remove(file_path)
		set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
		transaction.commit()
		connections['crm'].close()      
		connections['default'].close()	
	except Exception as e:
		transaction.commit()
		connections['crm'].close()      
		connections['default'].close()
		if download_report_id:
			set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
		print('pending download error',e)

def download_call_recording_feedback_report(filters, user, col_list, download_report_id):
	"""
	this is the function for download call recording reports
	"""	
	try:
		csv_file = []
		count = 0
		user = User.objects.get(id=user)
		selected_user = filters.get("selected_user", [])
		selected_agent = filters.get("selected_agent", [])
		all_users = filters.get("all_users","")
		if all_users:
			all_users = all_users.split(',')
		else:
			all_users = []
		if len(selected_agent)==1:
			selected_agent.append(selected_agent[0])
		if len(selected_user) == 1:
			selected_user.append(selected_user[0])
		if len(all_users) == 1:
			all_users.append(all_users[0])
		customer_cid = filters.get("cli","")
		col_name = filters.get("column_name", "").split(",")
		start_date = datetime.strptime(filters.get("start_date", ""),"%Y-%m-%d %H:%M").isoformat()
		end_date =  datetime.strptime(filters.get("end_date", ""),"%Y-%m-%d %H:%M").isoformat()
		download_type = filters.get('download_type',"")
		sql_query_where = ''
		if selected_user:
			sql_query_where += " and (usr.id IN "+str(tuple(selected_user))+")"+"" 
		if selected_agent:
			sql_query_where += " and (crfb_user.id IN "+str(tuple(selected_agent))+ ")"+""
		if customer_cid:
			sql_query_where += " and ( callcenter_calldetail.customer_cid = "+str(customer_cid)+")"+""
		where =  " WHERE ( callcenter_callrecordingfeedback.created at time zone 'Asia/Kolkata' >= '" + str(start_date)+"' and callcenter_callrecordingfeedback.created at time zone 'Asia/Kolkata' <= '" +str(end_date)+"') and  callcenter_callrecordingfeedback.user_id IN "+str(tuple(all_users))+"" + sql_query_where + ' order by callcenter_callrecordingfeedback.created desc'
		query = "SELECT "
		for index,col_name in enumerate(col_list, start=1):
			if col_name in QC_FEEDBACK_COL:
				query += QC_FEEDBACK_COL[col_name]+" "
			if index < len(col_list) and query[-2:] != ', ':
				query += ", "
		query += "from callcenter_callrecordingfeedback LEFT JOIN callcenter_calldetail ON (callcenter_callrecordingfeedback.calldetail_id = callcenter_calldetail.id) LEFT JOIN callcenter_user usr ON (callcenter_calldetail.user_id = usr.id) LEFT JOIN callcenter_user crfb_user ON (callcenter_callrecordingfeedback.user_id = crfb_user.id) LEFT JOIN callcenter_cdrfeedbck ON (callcenter_calldetail.id = callcenter_cdrfeedbck.calldetail_id)" + where
		download_folder = settings.MEDIA_ROOT+"/download/"+datetime.now().strftime("%m.%d.%Y")+"/"+str(user.id)+"/"
		if not os.path.exists(download_folder):
			os.makedirs(download_folder)
		set_download_progress_redis(download_report_id, 25, is_refresh=True)
		db_settings = settings.DATABASES['default']
		db_connection = "postgresql://{user}:{password}@{host}:{port}/{db_name}".format(user = db_settings['USER'], password=db_settings['PASSWORD'], host = db_settings['HOST'], db_name = db_settings['NAME'], port = db_settings['PORT'])
		if download_type == 'xls':
			file_path = download_folder+str(user.id)+'_'+str('qc_callrecordingfeedback')+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".xlsx"
			with pd.ExcelWriter(file_path, engine="xlsxwriter",options={'remove_timezone': True}) as writer:
				df = pd.read_sql(query,db_connection)
				df.to_excel(writer, sheet_name = "Sheet1", header = True, index = False)
		else:
			file_path = download_folder+str(user.id)+'_'+str('qc_callrecordingfeedback')+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".csv"
			df = pd.read_sql(query,db_connection)
			df.to_csv(file_path, index = False)
		subprocess.call(['chmod', '777', file_path])
		f = open(file_path, 'rb')
		download_report = DownloadReports.objects.get(id=download_report_id)
		download_report.downloaded_file.save(os.path.basename(f.name), File(f), save=True)
		download_report.is_start = False
		download_report.save()
		f.close()
		os.remove(file_path)
		set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
		print("download report completed")
		transaction.commit()
		connections['crm'].close()      
		connections['default'].close()
	except Exception as e:
		transaction.commit()
		connections['crm'].close()      
		connections['default'].close()
		if download_report_id:
			set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
		print("qc_callrecordingfeedback error ",e)

def get_transform_key(uniquefields):
	"""
	this is the function for  get the keystransform
	"""	
	transform = {}
	field_list = []
	for field_inst in uniquefields:
		section_name = re.sub('[_]+', '_', field_inst.split(':')[0])
		field_name = re.sub('[_]+', '_', field_inst.split(':')[1])
		if section_name not in transform:
			transform[section_name] = KeyTransform(field_inst.split(':')[0],'customer_raw_data')
		if field_name not in transform:
			field_list.append(field_name)
			transform[field_name] = KeyTransform(field_inst.split(':')[1],section_name)
	return {'transform':transform, 'field_list':field_list}

def convert_to_zip(result, download_report_id):
	"""
	this is the function for convert to zip file
	"""	
	parent_file_path = '/var/spool/freeswitch/default/'
	download_report = DownloadReports.objects.get(id=download_report_id)
	path_to_zip = ''
	count = 0
	if result.count():
		path = settings.MEDIA_ROOT+'/call_recordings_'+str(uuid.uuid4())
		os.mkdir(path)
		for detail in result:
			exact_path = ''
			count +=1
			percentage = ((count)/len(result))*100
			set_download_progress_redis(download_report_id, round(percentage,2))
			if detail.ring_time.date() < date.today():
				exact_path = parent_file_path+detail.ring_time.strftime('%d-%m-%Y')+'/'
			else:
				exact_path = parent_file_path
			current_file = exact_path + detail.ring_time.strftime('%d-%m-%Y-%H-%M')+'_'+detail.customer_cid+'_'+str(detail.session_uuid)+'.mp3'
			if os.path.isfile(current_file):
				os.system('cp '+current_file+' '+path)
				path_to_zip = make_archive(path, "zip", path)
				# rmtree(path)
			else:
				current_file = exact_path + detail.connect_time.strftime('%d-%m-%Y-%H-%M')+'_'+detail.customer_cid+'_'+str(detail.session_uuid)+'.mp3'
				if os.path.isfile(current_file):
					os.system('cp '+current_file+' '+path)
					path_to_zip = make_archive(path, "zip", path)
				else:
					pass
		if path_to_zip:
			f = open(path_to_zip, 'rb')
			download_report.downloaded_file.save(os.path.basename(f.name), File(f), save=True)
			f.close()
			os.remove(path_to_zip)
		rmtree(path)
	download_report.is_start = False
	download_report.save()
	return ''

def download_call_recordings(filters, user, col_list, download_report_id):
	"""
	this is the function for download call recording
	"""	
	try:
		csv_file = []
		count = 0
		user = logged_in_user = User.objects.get(id=user)
		all_campaigns = filters.get("all_campaigns",[])
		all_users = filters.get("all_users",[])
		selected_campaign = filters.get("selected_campaign", [])
		selected_user = filters.get("selected_user", [])
		numeric = filters.get("numeric", "")
		start_date = filters.get("start_date", "")
		end_date = filters.get("end_date", "")
		unique_id = filters.get("unique_id", "")
		start_date = datetime.strptime(start_date,"%Y-%m-%d %H:%M").isoformat()
		end_date = datetime.strptime(end_date,"%Y-%m-%d %H:%M").isoformat()
		start_duration = filters.get("start_duration",'')
		end_duration = filters.get("end_duration",'')
		selected_records = filters.get("selected_records",[])
		if selected_records:
			if selected_records[0]=='':
				selected_records = []
		if not selected_records:
			admin = False
			if user.user_role and user.user_role.access_level == 'Admin':
				admin = True
			customer_cid = filters.get("customer_cid","") 
			if selected_user:
				if selected_user[0]=='':
					selected_user = []
			if selected_campaign:
				if selected_campaign[0]=='':
					selected_campaign = []
			start_end_date_filter = Q(created__gte=start_date)&Q(created__lte=end_date)
			queryset = DiallerEventLog.objects.filter(start_end_date_filter).filter(dialed_status='Connected').filter(Q(campaign__name__in=list(all_campaigns),user__id__in=list(all_users))|Q(user__id__in=list(all_users))| Q(campaign__name__in=list(all_campaigns) ,user=None)|Q(campaign=None)|Q(user=None)).select_related("campaign", "user")
			if start_duration and end_duration:
				queryset = queryset.filter(call_duration__range=(start_duration,end_duration))
			elif start_duration:
				queryset = queryset.filter(call_duration__gte=start_duration)
			elif end_duration:
				queryset = queryset.filter(call_duration__lte=end_duration)
			if queryset.exists():
				if customer_cid:
					queryset = queryset.filter(customer_cid=customer_cid)
				if selected_campaign:
					if not (logged_in_user.is_superuser or admin):
						get_camp_users = list(get_campaign_users(selected_campaign, 
						logged_in_user).values_list("id",flat=True))
						queryset = queryset.filter(Q(campaign_name__in = selected_campaign), 
							Q(user__in=get_camp_users)|Q(user=None))
					else:
						queryset = queryset.filter(campaign_name__in = selected_campaign)
				if selected_user:
					queryset = queryset.filter(user__id__in=selected_user)
				if unique_id:
					queryset = queryset.filter(uniqueid=unique_id)
		else:
			queryset = DiallerEventLog.objects.filter(id__in=selected_records)
		convert_to_zip(queryset, download_report_id)
		set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
	except Exception as e:
		print("Exception occures from create_zip",e)

def download_contactinfo_report(filters, user, col_list, download_report_id):
	"""
	this is the function for download contact info
	"""	
	try:
		filter_by_phonebook = filters.get("phonebook", [])
		logged_in_user = User.objects.get(id=user)
		filter_by_campaign = filters.get("campaign", "")
		filter_by_user = filters.get('user',[])
		disposition = filters.get('disposition',[])
		numeric = filters.get('numeric','')
		uniqueid = filters.get('uniqueid','')
		start_date = filters.get("start_date", "")
		end_date = filters.get("end_date", "")
		uniqueid = filters.get("uniqueid", "")
		download_type = filters.get("download_type","")
		filter_by_campaign = list(Campaign.objects.filter(id__in=filter_by_campaign).values_list("name", flat=True))
		if len(filter_by_campaign)==1:
			filter_by_campaign.append(filter_by_campaign[0])
		if len(disposition) == 1:
			disposition.append(disposition[0])
		if len(filter_by_phonebook) == 1:
			filter_by_phonebook.append(filter_by_phonebook[0])
		if len(filter_by_user) == 1:
			filter_by_user.append(filter_by_user[0])
		sql_query_where = ""
		if filter_by_phonebook:
			sql_query_where += " and phonebook_inst.id IN "+str(tuple(filter_by_phonebook))+""
		if filter_by_user:
			sql_query_where += " and crm_contact.user IN "+str(tuple(filter_by_user))+""
		if disposition:
			sql_query_where += " and crm_contact.disposition IN  "+str(tuple(disposition))+""
		if numeric:
			sql_query_where += " and crm_contact.numeric ='"+str(numeric)+"'"
		if uniqueid:
			sql_query_where += " and crm_contact.uniqueid ='"+str(uniqueid)+"'"
		where =  " WHERE ( crm_contact.created_date::date at time zone 'Asia/Kolkata' >= '" + str(start_date)+"' and crm_contact.created_date::date at time zone 'Asia/Kolkata' <= '" +str(end_date)+"') and  crm_contact.campaign IN "+str(tuple(filter_by_campaign))+"" + sql_query_where
		query = "SELECT "
		for index,col_name in enumerate(col_list, start=1):
			if col_name == 'alt_numeric':
				query += "array_to_string(avals(alt_numeric),"+"','" +") as alt_numeric"+" "
			elif col_name =='campaign':
				query += 'crm_contact.campaign as campaign'+" "
			elif col_name =='phonebook':
				query += 'phonebook_inst.name as phonebook'+" "
			elif col_name =='user':
				query += '"user" as user'+" "
			elif col_name =='status':
				query += 'crm_contact.status as status'+" "
			elif col_name =='lan':
				query += 'crm_contact.uniqueid as lan'+" "
			else:
				query += col_name+" "
			if index < len(col_list) and query[-2:] != ", ":
					query += ", "
		query += "from crm_contact left join crm_phonebook phonebook_inst on phonebook_inst.id = crm_contact.phonebook_id"+ where 
		download_folder = settings.MEDIA_ROOT+"/download/"+datetime.now().strftime("%m.%d.%Y")+"/"+str(user)+"/"
		if not os.path.exists(download_folder):
			os.makedirs(download_folder)
		set_download_progress_redis(download_report_id, 25, is_refresh=True)
		db_settings = settings.DATABASES['crm']
		db_connection = "postgresql://{user}:{password}@{host}:{port}/{db_name}".format(user = db_settings['USER'], password=db_settings['PASSWORD'], host = db_settings['HOST'], db_name = db_settings['NAME'], port = db_settings['PORT'])
		if download_type == 'xls':
			file_path = download_folder+str(logged_in_user.id)+'_'+str('contactinfo')+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".xlsx"
			with pd.ExcelWriter(file_path, engine="xlsxwriter",options={'remove_timezone': True}) as writer:
				df = pd.read_sql(query,db_connection)
				df.to_excel(writer, sheet_name = "Sheet1", header = True, index = False)
		else:
			file_path = download_folder+str(user)+'_'+str('contactinfo')+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".csv"
			df = pd.read_sql(query,db_connection)
			df.to_csv(file_path, index = False)
		subprocess.call(['chmod', '777', file_path])
		f = open(file_path, 'rb')
		download_report = DownloadReports.objects.get(id=download_report_id)
		download_report.downloaded_file.save(os.path.basename(f.name), File(f), save=True)
		download_report.is_start = False
		download_report.save()
		f.close()
		os.remove(file_path)
		set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
		transaction.commit()
		connections['crm'].close()      
		connections['default'].close()
	except Exception as e:
		transaction.commit()
		connections['crm'].close()      
		connections['default'].close()
		if download_report_id:
			set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
		print("contatinfo error ",e)

def download_billing_report(filters, user, col_list, download_report_id):
	"""
	this is the function for download billing report download
	"""	
	try:
		csv_file = []
		count = 0
		logged_in_user = User.objects.get(id=user)
		queryset = User.objects.filter()
		end_date = calendar.monthrange(int(filters.get('years')), int(filters.get('month')))[1]
		end_date = str(filters.get('years'))+'-'+str(filters.get('month'))+'-'+str(end_date)
		start_date = str(filters.get('years'))+'-'+str(filters.get('month'))+'-01'
		download_type = filters.get('download_type',"")
		csv_file.append(col_list)
		if queryset.exists():
			for user in queryset:
				days = 0
				admin_count = 0
				agent_count = 0
				row = []
				if user.user_role and user.user_role.access_level == 'Agent':
					ac_obj = AgentActivity.objects.filter(user=user, created__date__gte=start_date, created__date__lte=end_date, event='LOGIN').distinct('created__date').order_by('created__date')
					agent_count = ac_obj.count()
					unique_dates = ac_obj.values_list('created')
					admin_count = AdminLogEntry.objects.filter(created_by=user, created__date__gte=start_date, created__date__lte=end_date,action_name='4').distinct('created__date').order_by('created__date').exclude(created__date__in=unique_dates).count()
					days = int(agent_count) + int(admin_count)
				else:
					ad_obj = AdminLogEntry.objects.filter(created_by=user, created__date__gte=start_date, created__date__lte=end_date,action_name='4').distinct('created__date').order_by('created__date')
					unique_dates = ad_obj.values_list('created')
					admin_count = ad_obj.count()
					agent_count = AgentActivity.objects.filter(user=user, created__date__gte=start_date, created__date__lte=end_date, event='LOGIN').exclude(created__date__in=unique_dates).distinct('created__date').order_by('created__date').count()
					days = int(admin_count) + int(agent_count)
				if 'source' in col_list:
					row.append(settings.SOURCE)
				if 'buzzworks_id' in col_list:
					row.append(user.extension)
				if 'user_id' in col_list:
					row.append(user.username)
				if 'location' in col_list:
					row.append(settings.LOCATION)
				if 'ip_address' in col_list:
					row.append(settings.IP_ADDRESS)
				if 'days' in col_list:
					row.append(days)
				if 'days_band' in col_list:
					days_band = '>=15' if days >=15 else '< 15'
					row.append(days_band)
				csv_file.append(row)
				count +=1
				percentage = ((count)/queryset.count())*100
				if download_report_id !=None:
					set_download_progress_redis(download_report_id, round(percentage,2))
		if download_type == 'xls':
			save_file(csv_file, download_report_id, 'billing', logged_in_user, 'xls')
		else:
			save_file(csv_file, download_report_id, 'billing', logged_in_user, 'csv')
	except Exception as e:
		print("Exception occures from Billing Download",e)

def upload_template_sms(data, logged_in_user, campaign):
	"""
	this is the function for upload template sms
	"""	
	sms_template_list = []
	templates_name = []
	incorrect_count = correct_count=0
	incorrect_list =  []
	duplicate_list = []
	errors = ""
	data_count = data.shape[0] 
	response_data = {}
	if not data.empty:
		duplicate_list = data[data.duplicated('Text', keep='first')]
		duplicate_list['description']='This Text is duplicated'
		data.drop_duplicates(subset ="Text", keep = 'first', inplace = True)

		frame = [duplicate_list]
		duplicate_list = pd.concat(frame)
		for index, row in data.iterrows():
			data_dic = {}
			status = 'Active'
			template_type = 0
			if row["Status"].lower() == "inactive":
				status='Inactive'
			if row["Template_type"].lower() == "campaign":
				template_type=1
			if len(row["Text"]) >150:
				data_dic["text_length"] ="It should be in range of 150 characters"
			if SMSTemplate.objects.filter(name=row["Text"]).exists():
				data_dic["template"] = "Template with this name already exist"
			cwd = os.path.join(settings.BASE_DIR, 'static/')
			if not SMSTemplate.objects.filter(name=row["Name"]).exists():
				sms_template_list.append(SMSTemplate(name=row["Name"], text=row["Text"], campaign_id=campaign, status=status, template_type=template_type,
				created_by=logged_in_user))
				correct_count = correct_count + 1
			else:
				data_dic["template"] = "Template with this name already exist"
			if data_dic:
				incorrect_count = incorrect_count + 1
				row["description"] = json.dumps(data_dic)
				incorrect_list.append(pd.DataFrame(row).T)

		SMSTemplate.objects.bulk_create(sms_template_list)
				
		if incorrect_count:
			response_data["incorrect_count"] = incorrect_count
			with open(cwd+"csv_files/improper_data.csv", 'w') as improper_file:
				for incorrect_row in incorrect_list:
					incorrect_row.to_csv(
						improper_file, index=False, header=improper_file.tell() == 0)
				if not duplicate_list.empty:
					duplicate_list.to_csv(improper_file, index=False, header=improper_file.tell()==0)
			incorrect_file_path = "/static/csv_files/improper_data.csv"
			response_data["incorrect_file"] = incorrect_file_path
			response_data["incorrect_msg"] = "Improper Data: "+str(incorrect_count)
			if correct_count != 0:
				response_data["correct_msg"] =str(correct_count) +" template uploaded successfully"
		if data_count != incorrect_count:
			response_data["success_msg"] = True
		return response_data
	else:
		response_data["empty_file"] = "File is empty"
		return response_data




def upload_holiday_dates(data, logged_in_user,audio_file_id):
	incorrect_count = correct_count=0
	incorrect_list =  []
	duplicate_list = []
	holidays_list = []
	errors = ""
	data_count = data.shape[0] 
	response_data = {}
	if not data.empty:
		duplicate_list = data[data.duplicated('name', keep='first')]
		duplicate_list['description']='This name is duplicated'
		data.drop_duplicates(subset ="name", keep = 'first', inplace = True)

		frame = [duplicate_list]
		duplicate_list = pd.concat(frame)
		for index, row in data.iterrows():
			data_dic = {}
			status = 'Active'
			template_type = 0
			if row["status"].lower() == "inactive":
				status='Inactive'
			if len(row["name"]) >150:
				data_dic["text_length"] ="It should be in range of 150 characters"
			if row['holiday_date'].date() < datetime.now().date():
				data_dic['holiday_date'] = "Enter Upcoming Holidays"
			if Holidays.objects.filter(holiday_date=row["holiday_date"].date()).exists():
				data_dic['holiday_date'] = "Holiday with this date already exists"
			if  Holidays.objects.filter(name=row["name"]).exists():
				data_dic["holiday"] = "Holiday with this name already exist"
			cwd = os.path.join(settings.BASE_DIR, 'static/')
			if not Holidays.objects.filter(name=row["name"]).exists() and not data_dic:
				holidays_list.append(Holidays(name=row["name"], holiday_date=row["holiday_date"], status=status, description=row["description"],created_by=logged_in_user, holiday_audio_id=audio_file_id))
				correct_count = correct_count + 1
			if data_dic:
				incorrect_count = incorrect_count + 1
				row["remarks"] = json.dumps(data_dic)
				incorrect_list.append(pd.DataFrame(row).T)

		Holidays.objects.bulk_create(holidays_list)	
		if incorrect_count:
			response_data["incorrect_count"] = incorrect_count
			with open(cwd+"csv_files/improper_data.csv", 'w') as improper_file:
				for incorrect_row in incorrect_list:
					incorrect_row.to_csv(
						improper_file, index=False, header=improper_file.tell() == 0)
				if not duplicate_list.empty:
					duplicate_list.to_csv(improper_file, index=False, header=improper_file.tell()==0)
			incorrect_file_path = "/static/csv_files/improper_data.csv"
			response_data["incorrect_file"] = incorrect_file_path
			response_data["incorrect_msg"] = "Improper Data: "+str(incorrect_count)
			if correct_count != 0:
				response_data["correct_msg"] =str(correct_count) +" Holidays uploaded successfully"
		if data_count != incorrect_count:
			response_data["success_msg"] = True
		return response_data
	else:
		response_data["empty_file"] = "File is empty"
		return response_data

def get_group_did(trunk):
	"""
	this is the function for get group dids
	"""	
	did_list = []
	did = trunk.did
	try:
		if did['type_of_did'] in ['single','multiple']:
			did_list.extend(did['did'])
		else:
			did_list.extend(list(range(int(did['start']),int(did['end'])+1)))
		return did_list
	except Exception as e:
		return did_list


def get_campaign_did(campaign_obj):
	"""
	this is the function for campaign did 
	"""	
	did_list = []
	did = campaign_obj.trunk_did
	try:
		if did['type_of_did'] in ['single','multiple']:
			did_list.extend(did['did'])
		else:
			did_list.extend(list(range(int(did['did_start']),int(did['did_end'])+1)))
		return did_list
	except Exception as e:
		return did_list

def trunk_channels_count(campaign_obj):
	"""
	this is the function for trunk channels count 
	"""	
	try:
		TRUNK = pickle.loads(settings.R_SERVER.get("trunk_status") or pickle.dumps({}))
		truck_ids = []
		trunkwise_status = {}
		total_used_channels = 0
		did_list = []
		# c_total_chennals = 0
		country_code = ''
		trunc_total_channel = 0
		if campaign_obj.is_trunk_group and campaign_obj.trunk_group:
			trunc_total_channel = campaign_obj.trunk_group.total_channel_count
			for trunk in campaign_obj.trunk_group.trunks.all().order_by('priority'):
				if trunk.trunk.status == 'Active':
					if trunk.trunk.country_code:
						country_code = trunk.trunk.country_code
					did_list = get_group_did(trunk)
					if str(trunk.trunk.id) in TRUNK:
						# c_total_chennals = TRUNK[str(str(trunk.trunk.id))][campaign_obj.name]['c_total_chennals']
						total_used_channels += TRUNK[str(trunk.trunk.id)]
						if trunk.trunk.channel_count > TRUNK[str(trunk.trunk.id)]:
							trunkwise_status[str(str(trunk.trunk.id))] = {'is_available':True, 'free_channels': trunk.trunk.channel_count - TRUNK[str(trunk.trunk.id)] }
							truck_ids.append({'id':str(trunk.trunk.id), 'dial_string':str(trunk.trunk.dial_string),'did_list':did_list})
						else:
							trunkwise_status[str(trunk.trunk.id)] = {'is_available':False, 'free_channels': 0 }
					else:
						TRUNK[str(trunk.trunk.id)] = 0
						trunkwise_status[str(str(trunk.trunk.id))] = {'is_available':True, 'free_channels': trunk.trunk.channel_count }
						truck_ids.append({'id':str(trunk.trunk.id), 'dial_string':str(trunk.trunk.dial_string),'did_list':did_list})
						settings.R_SERVER.set("trunk_status", pickle.dumps(TRUNK))
		else:
			if campaign_obj.trunk and campaign_obj.trunk.dial_string and campaign_obj.trunk.status == 'Active':
				if campaign_obj.trunk.country_code:
					country_code = campaign_obj.trunk.country_code
				trunc_total_channel = campaign_obj.trunk.channel_count
				did_list = get_campaign_did(campaign_obj)
				if str(campaign_obj.trunk.id) in TRUNK:
					# c_total_chennals = TRUNK[str(campaign_obj.trunk.id)][campaign_obj.name]['c_total_chennals']
					total_used_channels += TRUNK[str(campaign_obj.trunk.id)]
					if trunc_total_channel > TRUNK[str(campaign_obj.trunk.id)]:
						trunkwise_status[str(campaign_obj.trunk.id)] = {'is_available':True, 'free_channels': total_used_channels - TRUNK[str(campaign_obj.trunk.id)] }
						# for ids in range(0, total_used_channels - TRUNK[str(campaign_obj.trunk.id)]):
						truck_ids.append({'id':str(campaign_obj.trunk.id), 'dial_string':str(campaign_obj.trunk.dial_string),'did_list':did_list})
					else:
						trunkwise_status[str(campaign_obj.trunk.id)] = {'is_available':False, 'free_channels': 0 }
				else:
					TRUNK[str(campaign_obj.trunk.id)] = 0
					trunkwise_status[str(str(campaign_obj.trunk.id))] = {'is_available':True, 'free_channels': campaign_obj.trunk.channel_count }
					truck_ids.append({'id':str(campaign_obj.trunk.id), 'dial_string':str(campaign_obj.trunk.dial_string),'did_list':did_list})
					settings.R_SERVER.set("trunk_status", pickle.dumps(TRUNK))
		return total_used_channels , trunkwise_status, truck_ids, trunc_total_channel, country_code
	except Exception as e:
		print("trunk_channels_count",e)

def set_campaign_channel(truck_ids, trunkwise_status, initiated_call):
	"""
	this is the function for set campaign chennals 
	"""	
	try:
		for trunk in truck_ids:
			if str(trunk['id']) in trunkwise_status:
				if trunkwise_status[str(trunk['id'])]['is_available']:
					if initiated_call <= trunkwise_status[str(trunk['id'])]['free_channels']:
						initiated_call+=1
						trunkwise_status[str(trunk['id'])]['free_channels'] -= 1
						if len(trunk['did_list'])>0:
							caller_id = random.sample(trunk['did_list'], 1)[0]
						else:
							caller_id = ''
						return initiated_call, trunkwise_status, trunk, caller_id
					else:
						trunkwise_status[str(trunk['id'])]['free_channels'] = 0
		return 0, trunkwise_status, None, ''
	except Exception as e:
		print("trunk_channels_count",e)

def channel_trunk_single_call(campaign_obj):
	"""
	this is the function for channel trunk signle call
	"""	
	try:
		TRUNK = pickle.loads(settings.R_SERVER.get("trunk_status") or pickle.dumps({}))
		truck_ids = []
		trunkwise_status = {}
		total_used_channels = 0
		c_total_chennals = 0
		trunc_total_channel = 0
		country_code = ''
		if campaign_obj.is_trunk_group and campaign_obj.trunk_group:
			# trunc_total_channel = campaign_obj.trunk_group.total_channel_count
			for trunk in campaign_obj.trunk_group.trunks.all().order_by('priority'):
				if trunk.trunk.status == 'Active':
					if trunk.trunk.country_code:
						country_code = trunk.trunk.country_code
					did_list = get_group_did(trunk)
					if len(did_list)>0:
						caller_id = random.sample(did_list, 1)[0]
					else:
						caller_id = ''
					if str(trunk.trunk.id) in TRUNK:
						if trunk.trunk.channel_count > TRUNK[str(trunk.trunk.id)]:
							return trunk.trunk.id, trunk.trunk.dial_string, caller_id, country_code
					else:
						TRUNK[str(trunk.trunk.id)] = 0
						settings.R_SERVER.set("trunk_status", pickle.dumps(TRUNK))
						return trunk.trunk.id, trunk.trunk.dial_string, caller_id, country_code
		else:
			if campaign_obj.trunk and campaign_obj.trunk.dial_string and campaign_obj.trunk.status == 'Active':
				did_list = get_campaign_did(campaign_obj)
				if campaign_obj.trunk.country_code:
					country_code = campaign_obj.trunk.country_code
				if len(did_list)>0:
					caller_id = random.sample(did_list, 1)[0]
				else:
					caller_id = ''
				if str(campaign_obj.trunk.id) in TRUNK:
					if campaign_obj.trunk.channel_count > TRUNK[str(campaign_obj.trunk.id)]:
						return campaign_obj.trunk.id, campaign_obj.trunk.dial_string, caller_id, country_code
				else:
					TRUNK[str(campaign_obj.trunk.id)] = 0
					settings.R_SERVER.set("trunk_status", pickle.dumps(TRUNK))
					return campaign_obj.trunk.id, campaign_obj.trunk.dial_string, caller_id, country_code
		return None, None, '', ''
	except Exception as e:
		print("channel_trunk_single_call",e)

def trunk_with_agent_call_id(user_trunk_id, user_caller_id, campaign_obj):
	"""
	this is the function for trunk with agent call ids 
	"""	
	try:
		country_code = ''
		TRUNK = pickle.loads(settings.R_SERVER.get("trunk_status") or pickle.dumps({}))
		if campaign_obj.is_trunk_group and campaign_obj.trunk_group:
			for trunk in campaign_obj.trunk_group.trunks.filter(trunk_id=user_trunk_id).order_by('priority'):
				if trunk.trunk.status == 'Active':
					if trunk.trunk.country_code:
						country_code = trunk.trunk.country_code
					if str(trunk.trunk.id) in TRUNK:
						if trunk.trunk.channel_count > TRUNK[str(trunk.trunk.id)]:
							return trunk.trunk.id, trunk.trunk.dial_string, user_caller_id, country_code
					else:
						TRUNK[str(trunk.trunk.id)] = 0
						settings.R_SERVER.set("trunk_status", pickle.dumps(TRUNK))
						return trunk.trunk.id, trunk.trunk.dial_string, user_caller_id, country_code
		else:
			if campaign_obj.trunk and campaign_obj.trunk.dial_string and campaign_obj.trunk.status == 'Active':
				if user_trunk_id == campaign_obj.trunk_id:
					if campaign_obj.trunk.country_code:
						country_code = campaign_obj.trunk.country_code
					if str(campaign_obj.trunk.id) in TRUNK:
						if campaign_obj.trunk.channel_count > TRUNK[str(campaign_obj.trunk.id)]:
							return campaign_obj.trunk.id, campaign_obj.trunk.dial_string, user_caller_id, country_code
					else:
						TRUNK[str(campaign_obj.trunk.id)] = 0
						settings.R_SERVER.set("trunk_status", pickle.dumps(TRUNK))
						return campaign_obj.trunk.id, campaign_obj.trunk.dial_string, user_caller_id, country_code
				else:
					if campaign_obj.trunk.country_code:
						country_code = campaign_obj.trunk.country_code
					if str(campaign_obj.trunk.id) in TRUNK:
						if campaign_obj.trunk.channel_count > TRUNK[str(campaign_obj.trunk.id)]:
							return campaign_obj.trunk.id, campaign_obj.trunk.dial_string, user_caller_id, country_code
					else:
						TRUNK[str(campaign_obj.trunk.id)] = 0
						settings.R_SERVER.set("trunk_status", pickle.dumps(TRUNK))
						return campaign_obj.trunk.id, campaign_obj.trunk.dial_string, user_caller_id, country_code
		return None, None, '', ''
	except Exception as e:
		print("channel_trunk_single_call",e)
		return None, None, '', ''

# her get used did old replaced with new 
def get_used_did(type=''):
	'''
	This function is used to get used did in wfh, skill route and voice bot
	'''
	used_did = []
	if type in ['skill_routing', 'wfh']:
		skill_dids = list(SkilledRoutingCallerid.objects.values_list('caller_id',flat=True))
		used_did.extend(skill_dids)
		wfh_dids = CampaignVariable.objects.exclude(wfh_caller_id='').exclude(wfh_caller_id=None).values_list('wfh_caller_id',flat=True)
		used_did.extend(list(wfh_dids))
	elif type in ['ingroup', 'user']:
		ingroup_dids = InGroupCampaign.objects.values_list('caller_id__did',flat=True)
		for ingroup_did in ingroup_dids:
			used_did.extend(ingroup_did)
		user_dids = User.objects.exclude(caller_id='').exclude(caller_id=None).values_list('caller_id',flat=True)
		used_did.extend(list(user_dids))
	return used_did
def get_used_did_by_pk(pk, type='wfh'):
	"""
	this is the function for get used did by ids
	"""	
	used_did = []
	if type in ['skill_routing','wfh']:
		skill_dids = SkilledRoutingCallerid.objects.values_list('caller_id',flat=True)
		if type=='skill_routing':
			skill_dids = skill_dids.exclude(skill_id=pk)
		used_did.extend(list(skill_dids))
		wfh_camp = CampaignVariable.objects.exclude(wfh_caller_id='').exclude(wfh_caller_id=None)
		if type =='wfh':
			wfh_camp = wfh_camp.exclude(id=pk)
		wfh_dids = wfh_camp.values_list('wfh_caller_id',flat=True)
		used_did.extend(list(wfh_dids))
	elif type in ['ingroup', 'user']:
		ingroup = InGroupCampaign.objects.all()
		if type=='ingroup':
			ingroup = ingroup.exclude(id=pk)
		ingroup_dids = ingroup.values_list('caller_id__did',flat=True)
		for ingroup_did in ingroup_dids:
			used_did.extend(ingroup_did)
		users = User.objects.exclude(caller_id='').exclude(caller_id=None)
		if type=='user':
			users = users.exclude(id=pk)
		user_dids = users.values_list('caller_id',flat=True)
		used_did.extend(list(user_dids))
	return used_did

def save_report_column_visibility(report_name, column_list, user):
	"""
	this is the function for save report colums reports 
	"""	
	report,_ = ReportColumnVisibility.objects.get_or_create(report_name=report_name, user=user)
	if report:
		report.columns_name = column_list
		report.save()
	return report

def get_report_visible_column(report_name, user):
	"""
	this is the function for get report visible columns 
	"""	
	report_columns = ReportColumnVisibility.objects.filter(report_name=report_name, user=user)
	if report_columns.exists():
		return report_columns.first().columns_name
	return []

def download_alternate_contact_report(filters, user, col_list, download_report_id):
	"""
	this is the function for alternate contact report 
	"""	
	try:
		user = User.objects.get(id=user)
		start_date = filters.get("start_date", "")
		end_date = filters.get("end_date", "")
		unique_id = filters.get("unique_id", "")
		slected_entry = filters.get("slected_entry", [])
		start_date = datetime.strptime(start_date,"%Y-%m-%d %H:%M").isoformat()
		end_date = datetime.strptime(end_date,"%Y-%m-%d %H:%M").isoformat()
		download_type = filters.get('download_type',"")
		sql_query_where = ''
		if filters.get("unique_id", ""):
			sql_query_where +=  " and (crm_alternatecontact.uniqueid = "+str(selected_user)+")"+""
		if slected_entry:
			sql_query_where += " and (crm_alternatecontact.id IN ("+str(tuple(slected_entry))+")"+""

		where =  " WHERE ( crm_alternatecontact.created_date >= '" + str(start_date)+"' and crm_alternatecontact.created_date <= '" +str(end_date)+"')" + sql_query_where
		query = "SELECT "
		for index,col_name in enumerate(col_list, start=1):
			if col_name == 'alt_numeric':
				query += "array_to_string(avals(alt_numeric),"+"','" +") as alt_numeric"+" "
			else: 
				query += col_name+" "
			if index < len(col_list) and query[-2:] != ", ":
					query += ", "
		query += "from crm_alternatecontact"+ where
		download_folder = settings.MEDIA_ROOT+"/download/"+datetime.now().strftime("%m.%d.%Y")+"/"+str(user.id)+"/"
		if not os.path.exists(download_folder):
			os.makedirs(download_folder)
		set_download_progress_redis(download_report_id, 25, is_refresh=True)
		db_settings = settings.DATABASES['crm']
		db_connection = "postgresql://{user}:{password}@{host}:{port}/{db_name}".format(user = db_settings['USER'], password=db_settings['PASSWORD'], host = db_settings['HOST'], db_name = db_settings['NAME'], port = db_settings['PORT'])
		if download_type == 'xls':
			file_path = download_folder+str(user.id)+'_'+str('alternate')+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".xlsx"
			with pd.ExcelWriter(file_path, engine="xlsxwriter",options={'remove_timezone': True}) as writer:
				df = pd.read_sql(query,db_connection)
				df.to_excel(writer, sheet_name = "Sheet1", header = True, index = False)
		else:
			file_path = download_folder+str(user.id)+'_'+str('alternate')+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".csv"
			df = pd.read_sql(query,db_connection)
			df.to_csv(file_path, index = False)
		subprocess.call(['chmod', '777', file_path])
		f = open(file_path, 'rb')
		download_report = DownloadReports.objects.get(id=download_report_id)
		download_report.downloaded_file.save(os.path.basename(f.name), File(f), save=True)
		download_report.is_start = False
		download_report.save()
		f.close()
		os.remove(file_path)
		set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
		print("download report completed")
	except Exception as e:
		if download_report_id:
			set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
		print("alternate number download  error ",e)

def convert_into_timeformat(start,end):
	""" Not using but will may use for further"""
	if end:
		datetime_diff = end - start
		hours = datetime_diff.seconds//3600
		minutes = (datetime_diff.seconds//60)%60
		datetime = str(datetime_diff.days)+" Days "+str(hours)+" Hr " +str(minutes)+" Min "
		return datetime 

def download_lan_report(filters, user, col_list, download_report_id):
	try:
		query = {}
		csv_file = []
		count = 0
		user = User.objects.get(id=user)
		admin = False
		if user.user_role and user.user_role.access_level == 'Admin':
			admin = True
		all_users = filters.get("all_users",[])
		selected_user = filters.get("selected_user", "")
		numeric = filters.get("numeric", "")
		start_date = filters.get("start_date", "")
		end_date = filters.get("end_date", "")
		start_date = datetime.strptime(start_date,"%Y-%m-%d %H:%M").isoformat()
		end_date = datetime.strptime(end_date,"%Y-%m-%d %H:%M").isoformat()
		unique_id = filters.get("unique_id","")
		column_name = filters.get('column_name','').split(',')
		original_col =filters.get('original_col','').split(',')
		exclude_nonuser_dispo = ['Redialled','Alternate Dial','Primary Dial','Auto Feedback', '']
		query = 'SELECT '
		subquery = "SELECT "
		for index, col_name in enumerate(original_col,start=1):
			if col_name =='lan':
				query += 'lan'
			elif col_name == 'username':
				query += 'username'
			elif col_name == 'created_on':
				query += 'init_time'
			else:
				query += LAN_REPORT_COL[col_name]+" "
			if index < len(LAN_REPORT_COL) and query[-2:] != ", ":
				query += ", "
		query += " from (" 
		for index, col_name in enumerate(original_col,start=1):
			if col_name in LAN_REPORT_COL:
				subquery += LAN_REPORT_COL[col_name]+" "
			if index < len(LAN_REPORT_COL) and query[-2:] != ", ":
				subquery += ", "
		set_download_progress_redis(download_report_id, 10, is_refresh=True)
		where = "uniqueid  is not null and uniqueid !='' and callcenter_calldetail.created >= '"+ str(start_date)+"'  and callcenter_calldetail.created <= '"+str(end_date) +"' AND callcenter_cdrfeedbck.primary_dispo NOT IN "+str(tuple(exclude_nonuser_dispo))+""
		query = query + subquery + 	", Row_number() over(partition by uniqueid order by callcenter_calldetail.id DESC) rn from callcenter_calldetail left join callcenter_cdrfeedbck on calldetail_id = callcenter_calldetail.id left join callcenter_user usr on usr.id = callcenter_calldetail.user_id where "+ where 
		if unique_id:
			query += " and ( callcenter_calldetail.uniqueid = '"+str(unique_id)+"') "
		if numeric:
			query += " and ( callcenter_calldetail.customer_cid = '"+str(unique_id)+"') "
		query += ") as T where T.rn<=10 "
		set_download_progress_redis(download_report_id, 25, is_refresh=True)
		data_df  = pd.read_sql_query(query,connections['default'])
		new_df = (data_df.set_index(['lan',data_df.groupby(['lan']).cumcount().add(1)]).unstack())
		new_df.columns=[f'{a}_{b}' for a, b in new_df.columns]
		new_df = new_df.reset_index()
		download_folder = settings.MEDIA_ROOT+"/download/"+datetime.now().strftime("%m.%d.%Y")+"/"+str(user.id)+"/"
		if not os.path.exists(download_folder):
			os.makedirs(download_folder)
		file_path = download_folder+str(user.id)+'_'+str('lan_report')+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".xlsx"
		with pd.ExcelWriter(file_path, engine="xlsxwriter",options={'remove_timezone': True}) as writer:
			new_df.to_excel(writer, sheet_name = "Sheet1", header = True, index = False)
		set_download_progress_redis(download_report_id, 90, is_refresh=True)
		f = open(file_path, 'rb')
		download_report = DownloadReports.objects.get(id=download_report_id)
		download_report.downloaded_file.save(os.path.basename(f.name), File(f), save=True)
		download_report.is_start = False
		download_report.save()
		f.close()
		os.remove(file_path)
		set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
		print("download report completed")	
	except Exception as e:
		if download_report_id:
			set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
		print("lan report  download  error ",e)
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print(exc_type, fname, exc_tb.tb_lineno)
def convert_timedelta_hrs(duration):
	""" agent performance timdelta to 24 hours """
	if duration:
		days, seconds = duration.days, duration.seconds
		hours = days * 24 + seconds // 3600
		minutes = (seconds % 3600) // 60
		seconds = seconds % 60
		if hours < 10:
			hours = "0"+str(hours)
		if minutes < 10:
			minutes = "0"+str(minutes)
		if seconds < 10:
			seconds = "0"+str(seconds)
		timeformat = str(hours)+":"+ str(minutes)+":"+str(seconds)
		return timeformat
	else:
		return "00:00:00" 

def getDaemonsStatus():
	"""
	this is the function for get demon status
	"""	
	daemons = Daemons.objects.filter(status=True)
	daemons = list(daemons.values_list("service_name", flat=True))
	status_daemons = []
	for daemon in daemons:
		status_daemon_dict = {'service_name': daemon}
		reponse = read_status(daemon)
		for key in reponse:
			status_daemon_dict[key] = reponse[key]
		status_daemons.append(status_daemon_dict)
	return status_daemons


def read_status(service):
	"""
	this is the function for read the service status 
	"""	
	p = subprocess.Popen(["systemctl", "status",  service],
						 stdout=subprocess.PIPE)
	(output, err) = p.communicate()
	output = output.decode('utf-8')

	service_regx = r"Loaded:.*\/(.*service);"
	status_regx = r"Active:(.*)\((.*)\) since (.*);(.*)"
	inactive_regx = r"Active:(.*)\((.*)\)"
	# status_regx = r"Active:(.*) since (.*);(.*)" #it will give result with running or not.
	service_status = {}
	service_status['status'] = "-"
	service_status['since'] = "-"
	service_status['uptime'] = "-"
	for line in output.splitlines():
		service_search = re.search(service_regx, line)
		status_search = re.search(status_regx, line)
		inactive_search = re.search(inactive_regx, line)

		if status_search:
			service_status['status'] = status_search.group(1).strip()
			service_status['since'] = dateutil.parser.parse(
				status_search.group(3).strip()).date()
			service_status['uptime'] = status_search.group(4).strip()
		elif inactive_search:
			service_status['status'] = 'inactive'
	return service_status

def download_ic_report(filters, user, col_list, download_report_id=None):
	try:
		query = {}
		user = User.objects.get(id=user)
		all_campaigns = filters.get("all_campaigns",[])
		selected_campaign = filters.get("selected_campaign", [])
		start_date = filters.get("start_date", "")
		end_date = filters.get("end_date", "")
		start_date = datetime.strptime(start_date,"%Y-%m-%d %H:%M").isoformat()
		end_date = datetime.strptime(end_date,"%Y-%m-%d %H:%M").isoformat()
		download_type = filters.get('download_type',"")
		if selected_campaign:
			all_campaigns = selected_campaign
		if '' in all_campaigns:
			all_campaigns.remove('')
		if len(all_campaigns) == 1:
			all_campaigns.append(all_campaigns[0])
		sql_query_where = " ( callcenter_cdrfeedbck.primary_dispo NOT IN ('PrimaryDial', 'AlternateDial', 'Redial', 'AutoFeedback', 'Redialed', '') and callcenter_cdrfeedbck.primary_dispo is NOT NULL and callcenter_calldetail.uniqueid is not null and callcenter_calldetail.uniqueid !='' and campaign_name IN "+str(tuple(all_campaigns)) + ")"
		where = " WHERE ( callcenter_calldetail.created at time zone 'Asia/Kolkata' >= '" + str(start_date)+"' and callcenter_calldetail.created at time zone 'Asia/Kolkata' <= '" +str(end_date)+"') and "+ sql_query_where + ' order by callcenter_calldetail.created desc'
		query_string = "SELECT "
		for index,col_name in enumerate(col_list, start=1):
			if col_name in IC_REPORT_COL:
				query_string += IC_REPORT_COL[col_name]+" "
			if index < len(col_list) and query_string[-2:] != ", ":
				query_string += ", "
		db_settings = settings.DATABASES['default']
		query_string += "from callcenter_calldetail left join callcenter_cdrfeedbck on callcenter_cdrfeedbck.calldetail_id=callcenter_calldetail.id left join callcenter_user usr on usr.id = callcenter_calldetail.user_id " + where
		download_folder = settings.MEDIA_ROOT+"/download/"+datetime.now().strftime("%m.%d.%Y")+"/"+str(user.id)+"/"
		if not os.path.exists(download_folder):
			os.makedirs(download_folder)
		set_download_progress_redis(download_report_id, 25, is_refresh=True)
		db_connection = "postgresql://{user}:{password}@{host}:{port}/{db_name}".format(user = db_settings['USER'], password=db_settings['PASSWORD'], host = db_settings['HOST'], db_name = db_settings['NAME'], port = db_settings['PORT'])
		df=pd.read_sql(query_string,db_connection)
		df['result_code'].replace('NF(No Feedback)','NF',inplace=True)
		if download_type == 'xls':
			file_path = download_folder+str(user.id)+'_'+str('ic4_trails')+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".xlsx"
			with pd.ExcelWriter(file_path, engine="xlsxwriter",options={'remove_timezone': True}) as writer:
				df = pd.read_sql(query_string,db_connection)
				df['result_code'].replace('NF(No Feedback)','NF',inplace=True)
				df.to_excel(writer, sheet_name = "Sheet1", header = True, index = False)
		else:
			file_path = download_folder+str(user.id)+'_'+str('ic4_trails')+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".csv"
			sql = r"""\copy ({query}) to '{file_path}' DELIMITER ',' CSV HEADER;""".format(query = query_string, file_path = file_path)
			subprocess.call(["psql", "-d", db_connection, "-c", sql])
		subprocess.call(['chmod', '777', file_path])
		f = open(file_path, 'rb')
		download_report = DownloadReports.objects.get(id=download_report_id)
		download_report.downloaded_file.save(os.path.basename(f.name), File(f), save=True)
		download_report.is_start = False
		download_report.save()
		f.close()
		os.remove(file_path)
		set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
		print("download report completed")
		transaction.commit()
		connections['crm'].close()      
		connections['default'].close()
	except Exception as e:
		transaction.commit()
		connections['crm'].close()      
		connections['default'].close()
		if download_report_id:
			set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
		print('download_ic_report download error',e)

def download_phonebookinfo_report(filters, user, col_list, download_report_id):
	""" download phonebook contacts  report """
	# print('download_phonebookinfo_report functin called')
	try:
		filter_by_phonebook = filters.get("phonebook_id", None)
		phonebook_name = filters.get('phonebook_name','')
		logged_in_user = User.objects.get(id=user)
		if filter_by_phonebook:
			where =  " WHERE phonebook_inst.id = "+ filter_by_phonebook
			query = "SELECT "
			for index,col_name in enumerate(col_list, start=1):
				if col_name == 'alt_numeric':
					query += "array_to_string(avals(alt_numeric),"+"','" +") as alt_numeric"+" "
				elif col_name =='campaign':
					query += 'crm_contact.campaign as campaign'+" "
				elif col_name =='phonebook':
					query += 'phonebook_inst.name as phonebook'+" "
				elif col_name =='user':
					query += '"user" as user'+" "
				elif col_name =='status':
					query += 'crm_contact.status as status'+" "
				elif col_name =='priority':
					query += 'crm_contact.priority as priority'+" "
				elif len(col_name.split(':'))>1:
					crm_col_list = col_name.split(':')
					query += "crm_contact.customer_raw_data -> '{section}' ->> '{field}' as \"{section}:{field}\" ".format(section=str(crm_col_list[0]), field=str(crm_col_list[1]))
				else: 
					query += col_name+" "
				if index < len(col_list) and query[-2:] != ", ":
						query += ", "
			query += "from crm_contact left join crm_phonebook phonebook_inst on phonebook_inst.id = crm_contact.phonebook_id"+ where 
			download_folder = settings.MEDIA_ROOT+"/download/"+datetime.now().strftime("%m.%d.%Y")+"/"+str(user)+"/"
			if not os.path.exists(download_folder):
				os.makedirs(download_folder)
			set_download_progress_redis(download_report_id, 25, is_refresh=True)
			db_settings = settings.DATABASES['crm']
			db_connection = "postgresql://{user}:{password}@{host}:{port}/{db_name}".format(user = db_settings['USER'], password=db_settings['PASSWORD'], host = db_settings['HOST'], db_name = db_settings['NAME'], port = db_settings['PORT'])
			file_path = download_folder+str(logged_in_user.id)+'_'+str(phonebook_name)+'_lead_list_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".xlsx"
			with pd.ExcelWriter(file_path, engine="xlsxwriter",options={'remove_timezone': True}) as writer:
				df = pd.read_sql(query,db_connection)
				df.to_excel(writer, sheet_name = "Sheet1", header = True, index = False)
			subprocess.call(['chmod', '777', file_path])
			f = open(file_path, 'rb')
			download_report = DownloadReports.objects.get(id=download_report_id)
			download_report.downloaded_file.save(os.path.basename(f.name), File(f), save=True)
			download_report.is_start = False
			download_report.save()
			f.close()
			os.remove(file_path)
			set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
			transaction.commit()
			connections['crm'].close()      
			connections['default'].close()
		set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
	except Exception as e:
		transaction.commit()
		connections['crm'].close()      
		connections['default'].close()
		if download_report_id:
			set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
		print("contatinfo error ",e)

def password_mail_sender(conn,subject,message,sender_email,receiver_email,username):
	try:
		msg = EmailMultiAlternatives(subject,"",sender_email, [receiver_email],connection=conn)
		msg.attach_alternative(message, "text/html")
		response = msg.send()
		PasswordChangeLogs.objects.create(username=username,change_type=PasswordChangeType[1][0],user_email=receiver_email,message=message)
	except Exception as e:
		print("Password Email sending Error",e)

def PasswordChangeAndLockedReminder():
	try:
		users = User.objects.all().exclude(is_superuser=True)
		pass_manage_inst = PasswordManagement.objects.filter().first()
		PASSWORD_ATTEMPTS = pickle.loads(settings.R_SERVER.get("password_attempt_status") or pickle.dumps({}))
		for user in users:
			message = ""
			if datetime.now().date() >= user.password_date+timedelta(pass_manage_inst.password_expire):
				message = """<p>
							Hello {0},<br>
							Your Account has been Locked with Flexydial. <br>
							Kindly click the below link to reset Your Password or Contact your Administrator
							<br>
							<a href='https://{1}'>Forgot Password</a>
							""".format(user.username,settings.WEB_SOCKET_HOST)
				try:
					subject = "Flexydial Password Locked"
					conn = email_connection(pass_manage_inst.password_data['email_id'],pass_manage_inst.password_data['email_password'],pass_manage_inst.password_data['email_host'],pass_manage_inst.password_data['port_number'])
					password_mail_sender(conn,subject,message,pass_manage_inst.password_data['email_id'],user.email,user.username)
					PASSWORD_ATTEMPTS[user.username] = pass_manage_inst.max_password_attempt
					settings.R_SERVER.set('password_attempt_status',pickle.dumps(PASSWORD_ATTEMPTS))
					user.is_active = False
					user.save()
				except Exception as e:
					print("Password Email sending error for locked users",e)
			else:
				if pass_manage_inst.password_expire:
					if pass_manage_inst.forgot_password:
						if pass_manage_inst.password_data['password_reminder']:
							for reminder_dates in pass_manage_inst.password_data['password_reminder']:
									password_date_cal = user.password_date + timedelta(int(reminder_dates))
									if datetime.now().date() == password_date_cal:
										message = pass_manage_inst.password_data['message'].replace('${username}',user.username)
										message += """<br> Your Password will Expire in <strong>{0} Days</strong> Kindly click the below link to reset Your Password or Contact your Administrator
											<br>
											<a href='https://{1}'>Login to Flexydial</a>""".format(int(pass_manage_inst.password_expire) - int(reminder_dates),settings.WEB_SOCKET_HOST)
										try:
											subject = "Flexydial Password Reset Reminder"
											conn = email_connection(pass_manage_inst.password_data['email_id'],pass_manage_inst.password_data['email_password'],pass_manage_inst.password_data['email_host'],pass_manage_inst.password_data['port_number'])
											password_mail_sender(conn,subject,message,pass_manage_inst.password_data['email_id'],user.email,user.username)
										except Exception as e:
											print("Password Scheduler email fields error",e)
						else:
							print("Password Reminder is not configured")
					else:
						print("forgot password is not enabled")
				else:
					print("No Password Reminder Date Set")
					break
	except Exception as e:
		print("Error in sending password change reminder and locked mails",e)

def get_pd_dialing(pd_camp):
	"""
	To get count of agents which are in predictive campaign
	and in dialing state
	"""
	AGENTS = {}
	AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
	count = 0
	for i in AGENTS:
		print(i)
		if 'dialing' in AGENTS[i]:
			if AGENTS[i]['campaign']==pd_camp and AGENTS[i]['dialing']==True:
				if AGENTS[i]['state'] not in ['Feedback','InCall']: 
					count+=1
	return count

def get_predictive_campaign():
	"""
	To get predictive live campaign names
	"""
	pd_campaigns=[]
	AGENTS={}
	AGENTS=pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
	for i in AGENTS:
		if 'call_mod' in AGENTS[i] and AGENTS[i]['call_mod']=='predictive':
			pd_camp = AGENTS[i]['campaign']
			if pd_camp not in pd_campaigns:
				pd_campaigns.append(pd_camp)
	return pd_campaigns

def get_data_from_agent_redis(pd_camp):
	AGENTS = {}
	AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") or pickle.dumps(AGENTS))
	pd_user_count = 0
	pd_wait_count = 0
	pd_wrap_up_count = 0
	pd_talking_count = 0
	pd_hold_count = 0
	for i in AGENTS:
		if  AGENTS[i]['campaign']==pd_camp and AGENTS[i]['call_mod']=='predictive':
			pd_user_count +=1
			if AGENTS[i]['state']=='Predictive Wait':
				pd_wait_count +=1
			if AGENTS[i]['state']=='Feedback':
				pd_wrap_up_count +=1
			if AGENTS[i]['state']=='InCall':
				pd_talking_count +=1
			if 'on_hold' in AGENTS[i] and AGENTS[i]['on_hold']==True:
				pd_hold_count +=1
	return pd_user_count,pd_wait_count,pd_wrap_up_count,pd_talking_count,pd_hold_count

def delete_session(session):
	"""this method is used to get all user sessions form
	django session
	"""
	try:
		if settings.SESSION_ENGINE:
			SessionStore = import_module(settings.SESSION_ENGINE).SessionStore
			s = SessionStore(session_key=session.session_key)
			s.delete()
		else:
			session.delete()
	except Exception as e:
		print("ERROR:: delete_session function ",e)

def all_unexpired_sessions_for_user(user):
	"""this method is used to get all user sessions form
	django session
	"""
	user_sessions = []
	all_sessions  = Session.objects.filter(expire_date__gte=timezone.now())
	for session in all_sessions:
			session_data = session.get_decoded()
			if user.pk == int(session_data.get('_auth_user_id',0)):
				user_sessions.append(session.pk)
	return Session.objects.filter(pk__in=user_sessions)

def delete_all_unexpired_sessions_for_user(user, session_to_omit=None):
	"""this method is used to delete user sessions from
	django session
	"""
	session_list = all_unexpired_sessions_for_user(user)
	if session_to_omit is not None:
		session_list.exclude(session_key=session_to_omit.session_key)
	# session_list.delete()
	agent_activity_data = {}
	for session in session_list:
		session_data = session.get_decoded()
		last_req = ""
		last_req = session_data.get('last_request','')
		if last_req:
			last_req = datetime.fromtimestamp(last_req)
		print("AlreadyLoginLog::",user.username,"session_expiry:: ",session.expire_date," last_request :: ",last_req)
		agent_activity_data['user'] = user
		agent_activity_data["event"] = "Old Login Session clear"
		agent_activity_data["event_time"] = datetime.now()
		create_agentactivity(agent_activity_data)
		delete_session(session)
	return True
