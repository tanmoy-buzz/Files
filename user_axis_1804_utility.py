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
from importlib import import_module
from django.core.files import File
import dateutil.parser
from datetime import datetime, date,timedelta
import datetime as dt
import itertools
from .models import (CampaignSchedule, Switch, DialTrunk, User, Group,AgentProductivityReport,
	Disposition, AudioFile, PauseBreak, UserVariable, RelationTag,PhonebookBucketCampaign,
	UserRole, Script, User, AgentActivity, Campaign, DiallerEventLog, CallDetail,DNC,CSS, CdrFeedbck,
	CallBackContact, CurrentCallBack, SnoozedCallback, Abandonedcall, ThirdPartyApiUserToken, SMSTemplate, SMSGateway,
	DiaTrunkGroup,EmailScheduler,AdminLogEntry, ReportColumnVisibility, CallRecordingFeedback, InGroupCampaign, SkilledRouting,
	EmailGateway,CampaignVariable, SkilledRoutingCallerid,Daemons,Holidays,PasswordManagement,PasswordChangeLogs)
from flexydial.constants import (Status,CALL_MODE, CAMPAIGN_STRATEGY_CHOICES, DIAL_RATIO_CHOICES, CDR_DOWNLOAD_COl,QC_FEEDBACK_COL,PasswordChangeType)
from .serializers import (GroupSerializer,CallDetailSerializer, CallBackContactSerializer,
	SetCallBackContactSerializer, DncSerializer, CallDetailReportSerializer, AgentActivityReportSerializer, CurrentCallBackSerializer, AbandonedcallSerializer, CallRecordingFeedbackSerializer)
from flexydial.views import (get_paginated_object, data_for_pagination, sendSMS, create_admin_log_entry, user_hierarchy_func)
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
import pytz
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
	users = User.objects.exclude(id=request.user.id)
	admin=False
	if request.user.user_role and request.user.user_role.access_level == 'Admin':
		admin = True
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


def get_switch_list(user, output='id'):
	"""
	function will return switch list as per access
	second parameter is optional
	default return is ids list, if second parameter is name then return names list
	"""
	try:
		switch_list = []

		# switch assign to logined user in user management
		switch_list.append(user.uservariable.domain_id)

		# switch created by logined user
		# switch_created = list(Switch.objects.filter(created_by_id=user.id).values_list('id', flat=True))

		# logined users camapaign list
		campaign_list = list(user.active_campaign.values_list('id', flat=True))
		campaigns_switch = list(Campaign.objects.filter(id__in=campaign_list).values_list('switch_id', flat=True))

		# users list under the logined user as per hierarchy
		user_list = user_hierarchy_func(user.id)
		users_switch = list(UserVariable.objects.filter(user_id__in=user_list).values_list('domain_id', flat=True))
		users_switch_created = list(Switch.objects.filter(Q(created_by_id__in=user_list) | Q(created_by_id=user.id)).values_list('id', flat=True))

		switch_list = list(set(switch_list+campaigns_switch+users_switch+users_switch_created))
		if output == 'name':
			switch_list_names = Switch.objects.filter(id__in=switch_list).all().values_list("name", flat=True)
			return list(switch_list_names)

		return switch_list
	except Exception as e:
		print('Exception from get switch list ', e)
		return []

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
	# user_list = User.objects.values("id", "username")
	if request.user.is_superuser:
		user_list=User.objects.all().values("id", "username")
	else:
		user_list = User.objects.filter(id__in=user_hierarchy_func(request.user.id)).values("id", "username")
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
	self_campaign = object_data.group.all().values_list("id", flat=True)
	self_dispo = object_data.disposition.all().values_list("id", flat=True)
	self_relationtag = object_data.relation_tag.all().values_list("id",flat=True)
	groups = Group.objects.all()
	data["is_non_admin"] = check_non_admin_user(request.user)
	data['non_user'] = []
	if request.user.is_superuser:
		users = User.objects.all().values('id',"username")
	else:
		users = User.objects.filter(id__in=user_hierarchy_func(request.user.id))
	if data["is_non_admin"]:
		groups = groups.filter(Q(user_group=request.user)|Q(created_by=request.user))
		data['user_groups'] = groups.values_list('id',flat=True)
		# users = users.filter(Q(group__in=request.user.group.all())|Q(created_by=request.user)|Q(reporting_to=request.user))
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

#def validate_data(username, email,wfh_numeric, employee_id=''):
#	"""
#	this is the function defined for validating the user information
#	"""	
#	data = {}
#	if username:
#		is_present = User.objects.filter(username=username.strip()).exists()
#		if is_present:
#			data["username"] = "This Username is already taken"
#	if email:
#		is_present = User.objects.filter(email=email.strip()).exists()
#		if is_present:
#			data["email"] = "User with this email id is already there"#

#	if wfh_numeric and wfh_numeric != float:
#		is_present = UserVariable.objects.filter(wfh_numeric=str(wfh_numeric).strip()).exists()
#		if is_present:
#			data['wfh_numeric'] = "wfh_numeric is already there"#

#	if employee_id:
#		is_present = User.objects.filter(employee_id=employee_id.strip()).exists()
#		if is_present:
#			data["employee_id"] = "This employee_id is already taken"#

#	return data

from flexydial.constants import CALL_TYPE
def validate_data(username, email,wfh_numeric, employee_id='',reporting_to='',domain='',call_protocol='',user_role='',dial_trunk='',caller_id=''):
	"""
	this is the function defined for validating the user information
	"""	
	data = {}

	username=username.strip()
	if username=="":
		data['username']="username should not be empty"

	if email and email!="None":
		regex_email = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
		if not (re.fullmatch(regex_email, email)):
			data['email']="enter proper email"

	if domain and domain!="None":
		switches=list(Switch.objects.all().values_list('name',flat=True))
		if domain not in switches:
			data['domain']="the domain does not exists"

	if call_protocol and call_protocol!='None':
		list_call_type=list(dict(CALL_TYPE).values())
		if call_protocol not in list_call_type:
			data['call_protocol']='the call protocol must be of'+str(list_call_type)


	if wfh_numeric and wfh_numeric!='None':
		wfh_numeric=str(wfh_numeric)		
		if not wfh_numeric.isdigit():
			data['wfh_numeric']="wfh numeric should be only integers"

	if reporting_to and reporting_to!='None':
		try:
			reporting_to=reporting_to.strip()
			reporting_user_obj = User.objects.filter(username=reporting_to)
			if user_role=='None':
				user_role=User.objects.get(username=username).user_role.access_level.lower()
			else:
				user_role=UserRole.objects.get(name=user_role).access_level.lower()
			if user_role=='admin' and reporting_to:
				data['reporting_to']='admin cannot report to any'
			elif user_role=='agent' and reporting_to:
				if reporting_user_obj.exists():
					reporting_user_role = reporting_user_obj[0].user_role.access_level.lower()
					if reporting_user_role in ['agent']:
						data['reporting_to']='agent cannot report agent'
				else:
					data['reporting_to']='given reporting user is not present'
			elif user_role=='supervisor' and reporting_to:
				if reporting_user_obj.exists():
					reporting_user_role = reporting_user_obj[0].user_role.access_level.lower()
					if reporting_user_role in ['agent','supervisor']:
						data['reporting_to'] = 'supervisor cannot report agent, supervisor'
				else:
					data['reporting_to']='given reporting user is not present'
#			elif user_role=='manager' and reporting_to:
#				if reporting_user_obj.exists():
#					reporting_user_role = reporting_user_obj[0].user_role.access_level.lower()
#					if reporting_user_role in ['agent','supervisor','manager']:
#						data['reporting_to'] = 'manager cannot report agent, supervisor, manager'
#				else:
#					data['reporting_to'] = 'given reporting user is not present'
		except Exception as e:
			print("EXCEPTION OCCURED AT def validate_data",e)
			

	if dial_trunk and dial_trunk!='None':
		userobj=User.objects.filter(username=username)
		if userobj.exists():
			username=userobj.first()
			campaign = Campaign.objects.filter(Q(users=username)|Q(group__in=username.group.all())).filter(status='Active').distinct()
			trunk_group = campaign.filter(is_trunk_group=True).values_list('trunk_group__trunks__trunk',flat=True)
			camp_trunk = campaign.filter(is_trunk_group=False).values_list('trunk',flat=True)
			trunk_list = list(DialTrunk.objects.filter(Q(id__in=camp_trunk)|Q(id__in=trunk_group)).values_list('name',flat=True))
			if dial_trunk not in trunk_list:
				data['dial_trunk']='the trunks must be of '+str(trunk_list)
		else:
			data['dial_trunk']="the user must be not new for dial trunk"

	if caller_id and caller_id!='None':
		if caller_id.isdigit():
			userobj=User.objects.filter(username=username)
			if userobj.exists():
				username=userobj.first()
				campaign = Campaign.objects.filter(Q(users=username)|Q(group__in=username.group.all())).filter(status='Active').distinct()
				trunk_group = campaign.filter(is_trunk_group=True).values_list('trunk_group__trunks__trunk',flat=True)
				camp_trunk = campaign.filter(is_trunk_group=False).values_list('trunk',flat=True)
				trunk_list = list(DialTrunk.objects.filter(Q(id__in=camp_trunk)|Q(id__in=trunk_group)).values_list('name',flat=True))
				if dial_trunk=="None":
					dial_trunk=User.objects.get(username=username).trunk.name
				if dial_trunk in trunk_list:
					trunk_obj=DialTrunk.objects.filter(name=dial_trunk).first()
					trunk_obj_range=trunk_obj.did_range
					trunk_obj_range=trunk_obj_range.split(",")
					trunk_obj_range=range(int(trunk_obj_range[0]),int(trunk_obj_range[1]))
					if not int(caller_id) in trunk_obj_range:
						data['caller id']='the caller id must be in the range of'+str(trunk_obj_range)

					exst_user=User.objects.exclude(username=str(username)).filter(trunk=trunk_obj.id,caller_id=caller_id)
					if exst_user.exists():
						data['caller id']="this number is already taken by user"+str(exst_user.first().username)

				else:
					data['dial_trunk__caller_id']='caller id the trunks must be of '+str(trunk_list)

			else:
				data['caller id']="the user must be not new for caller id"
		else:
			data['caller id']="caller id must be integer"
	return data

#def validate_uploaded_users_file(data):
#	"""
#	This method is used to validate uploaded user file
#	"""
#	correct_count = 0
#	incorrect_count = 0
#	correct_list = []
#	incorrect_list = []
#	duplicate_list = []
#	if not data.empty:
#		duplicate_list = data[data.duplicated('username', keep='first')]
#		duplicate_list['description']='This username is duplicated'
#		data.drop_duplicates(subset ="username", keep = 'first', inplace = True) #

#		dummy_df = data[(data["wfh_numeric"] != '')]
#		duplicate_list = dummy_df[dummy_df.duplicated('wfh_numeric', keep='first')]
#		data = data.drop(duplicate_list.index.tolist())
#		duplicate_list['description']='This wfh_numeric is duplicated'
#		dummy_df= data[(data["employee_id"]!='')]
#		dup_email_list = dummy_df[dummy_df.duplicated(["employee_id"], keep='first')]
#		dup_email_list['description']='This employee_id is duplicated'#

#		frame = [duplicate_list]
#		duplicate_list = pd.concat(frame)
#		# index_list = dup_email_list.index.tolist()
#		# data = data.drop(index_list)#

#		# duplicate_list['description']='This row is duplicated'
#		data = data.replace(np.nan, '', regex=True)
#		incorrect_count =len(duplicate_list)#

#		for index, row in data.iterrows():
#			username = row.get("username", "")
#			email = row.get("email", "")
#			#

#			# extension = row.get("extension", "")
#			# data = {}
#			user_role = row.get("role", "")
#			group = row.get("group", "")
#			password = row.get("password", "")
#			wfh_numeric = row.get("wfh_numeric","")
#			employee_id = row.get("employee_id","")
#			if not username or not password:
#				data = {"Msg": "Missing value in row"}
#			
#			data = validate_data(str(username), str(email), wfh_numeric, str(employee_id))
#			if user_role:
#				check_role = UserRole.objects.filter(
#					name__iexact=user_role.strip()).exists()
#				if not check_role:
#					data["role"] = "This is not a valid role"
#			if group:
#				check_dept = Group.objects.filter(
#					name__iexact=group.strip()).exists()
#				if not check_dept:
#					data["group"] = "This is not a valid group"
#			if data:
#				incorrect_count = incorrect_count + 1
#				row["description"] = json.dumps(data)
#				incorrect_data = pd.DataFrame(row).T
#				incorrect_list.append(pd.DataFrame(row).T)
#			else:
#				correct_count = correct_count + 1
#				correct_list.append(pd.DataFrame(row).T)
#		cwd = os.path.join(settings.BASE_DIR, 'static/')
#		if correct_count:
#			with open(cwd+"csv_files/proper_data.csv", 'w') as proper_file:
#				for correct_row in correct_list:
#					correct_row.to_csv(
#						proper_file, index=False, header=proper_file.tell() == 0)#

#			correct_file_path = "/static/csv_files/proper_data.csv"
#			data["correct_file"] = correct_file_path
#			data["correct_count"] = correct_count
#		if incorrect_count:
#			with open(cwd+"csv_files/improper_data.csv", 'w') as improper_file:
#				for incorrect_row in incorrect_list:
#					incorrect_row.to_csv(
#						improper_file, index=False, header=improper_file.tell() == 0)
#				if not duplicate_list.empty:
#					duplicate_list.to_csv(improper_file, index=False, header=improper_file.tell()==0)
#			incorrect_file_path = "/static/csv_files/improper_data.csv"
#			data["incorrect_file"] = incorrect_file_path
#			data["incorrect_count"] = incorrect_count
#	else:
#		data = {}
#		data["empty_file"] = "File is empty"
#	return data

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

		# index_list = dup_email_list.index.tolist()
		# data = data.drop(index_list)

		# duplicate_list['description']='This row is duplicated'
		data = data.replace(np.nan, '', regex=True)
		incorrect_count =len(duplicate_list)
		if 'wfh_numeric' in data:#checking wfh_numeric column present in data(DataFrame)
			wfh_numeric_duplicate_df=data[data.duplicated('wfh_numeric')]
			wfh_numerics_duplicates=set(wfh_numeric_duplicate_df['wfh_numeric'].tolist())

			if "" in wfh_numerics_duplicates:
				wfh_numerics_duplicates.remove("")

			wfh_numerics_db=list(UserVariable.objects.exclude(wfh_numeric=None).values_list('wfh_numeric',flat=True))

		username_duplicate_df=data[data.duplicated('username')]
		username_duplicates=set(username_duplicate_df['username'].tolist())

		user_trunk_list=[]#need to have empty list because if given empty dialtrunk caller id checking conditon fails.
		if ('dial_trunk' in data) and ('caller_id' in data):
			duplicate = data[data.duplicated(['dial_trunk', 'caller_id'])]
			duplicate_col=duplicate[['username','dial_trunk','caller_id']]
			null_filter = duplicate_col["dial_trunk"] != ""
			dfNew = duplicate_col[null_filter]
			user_trunk_list=dfNew['username'].tolist()#this list contains which has duplicate caller id's

		for index, row in data.iterrows():
			username = str(row.get("username", ""))
			email = row.get("email", "")


			# extension = row.get("extension", "")
			# data = {}
			user_role = row.get("role")
			group = row.get("group")
			password = str(row.get("password"))
			# password=password.strip()
			wfh_numeric = row.get("wfh_numeric")
			employee_id = row.get("employee_id","")
			if not username or not password:
				data = {"Msg": "Missing value in row"}
			
			reporting_to=row.get("reporting_to")
			domain=row.get("domain")
			call_protocol=row.get("call_protocol")

			dial_trunk=str(row.get("dial_trunk")).strip()
			caller_id=str(row.get("caller_id")).strip()
			data = validate_data(str(username), str(email), wfh_numeric, str(employee_id),str(reporting_to),str(domain),str(call_protocol),str(user_role),dial_trunk,caller_id)
			if user_role!=None:
				check_role = UserRole.objects.filter(
					name__iexact=user_role.strip()).exists()
				if not check_role:
					data["role"] = "This is not a valid role"
			if group and group!="None":
				group=group.strip()
				group_lst=list(group.split(","))
				for x in group_lst:
					exist=Group.objects.filter(name=x,status="Active").exists()
					if not exist:
						data['group']="this "+x+" is not valid group"
			if domain and domain!="None":
				switches = list(Switch.objects.all().values_list('name',flat=True))
				if domain not in switches:
					data['domain']="The Domain does not exists"
			else:
				data['domain']="The Domain should not be empty"

			if str(len(username.strip()))==0:
				data['username']="Username must not be empty"
			if username in username_duplicates:
				data['username']="given username already in the file multiple times"
			if username in user_trunk_list:#we are returning error in same caller id present in file by taking username as key
				data['caller_id']='this domain with same caller_id exists in the file'
			if wfh_numeric!=None and (wfh_numeric in wfh_numerics_duplicates) :
				data['wfh_numeric']="given wfh_numeric contains duplicates in file"

			status=str(row.get('status')).strip()
			str_bools=['True','False']
			if (status!="None") and (len(status)) ==0:
				data['status']="status must be not empty"
			elif (status!="None") and (status not in str_bools):
				data['status']="status must be boolean only"

			if wfh_numeric and wfh_numeric!='None':
				s=User.objects.filter(username=username)
				if s:
					if wfh_numeric==s[0].properties.wfh_numeric:
						pass
					else:
						if wfh_numeric in wfh_numerics_db:
							data['wfh_numeric']='given wfh numeric present in db'
				else:
					if wfh_numeric in wfh_numerics_db:
						data['wfh_numeric']='given wfh numeric present in db'

			user_obj=User.objects.filter(username=username)
			if (not user_obj.exists()) and (not password) and password!='None':
					data['password']="password should be not null for new users"	

			if password and password!='None':
				reg = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,20}$"
				pat=re.compile(reg)
				mat=re.search(pat,password)
				if not mat:
					data['password']="password should be strong"
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
				if len(duplicate_list)!=0:
					duplicate_list.to_csv(improper_file, index=False, header=improper_file.tell()==0)
			incorrect_file_path = "/static/csv_files/improper_data.csv"
			data["incorrect_file"] = incorrect_file_path
			data["incorrect_count"] = incorrect_count
	else:
		data = {}
		data["empty_file"] = "File is empty"
	return data

#def upload_users(data, logged_in_user):
#	"""
#	this is the function defined for uploading the user
#	"""
#	domain_obj=Switch.objects.filter().first()	
#	for index, row in data.iterrows():
#		username = row.get("username", "")
#		email = row.get("email", "")
#		email_password = str(row.get("email_password", ""))
#		password = row.get("password", "").strip()
#		user_role = row.get("role", "")
#		group = row.get("group", "")
#		first_name = row.get("first_name", "")
#		last_name = row.get("last_name","")
#		wfh_numeric = row.get("wfh_numeric","")
#		employee_id = row.get("employee_id","")
#		user, created = User.objects.get_or_create(username=username)
#		if user_role:
#			role = UserRole.objects.get(name__iexact=user_role.strip())
#			user.user_role = role
#		if group:
#			group = Group.objects.get(name__iexact=group.strip())
#			user.group.add(group)
#		user.set_password(password)
#		user.email = email.strip()
#		user.first_name = first_name
#		user.last_name = last_name
#		user.created_by = logged_in_user
#		user.email_password = email_password.strip()
#		if employee_id:
#			user.employee_id = employee_id
#		user.save()
#		if created:
#			user_variable = UserVariable()
#			user_variable.user = user
#		else:
#			user_variable = UserVariable.objects.get(user=user)#

#		extension_exist = UserVariable.objects.all().values_list('extension',flat=True)
#		extension = sorted(list(set(four_digit_number) - set(extension_exist)))[0]
#		user_variable.extension = extension
#		UserVariable.domain=domain_obj
#		if wfh_numeric == '':
#			user_variable.wfh_numeric = None
#		else:
#			user_variable.wfh_numeric = wfh_numeric
#		user_variable.save()

def upload_users(data, logged_in_user):
	"""
	this is the function defined for uploading the user
	"""
	domain_obj=Switch.objects.filter().first()	
	for index, row in data.iterrows():
		username = row.get("username", "")
		username=str(username).strip()
		username=re.sub("\s", "_", username)
		email_password = str(row.get("email_password", ""))
		password = row.get("password", "").strip()
		employee_id = row.get("employee_id","")
		user_obj_exists=User.objects.filter(username=username).exists()
		

		user, created = User.objects.get_or_create(username=username)
		user_role = row.get("role")
		# user_role = row.get("role",user.user_role.name)
		if user_role:
			role = UserRole.objects.get(name__iexact=user_role.strip())
			user.user_role = role

		user_groups_tup=list(User.objects.filter(username=username).values_list("group__name"))
		user_groups=[item for t in user_groups_tup for item in t]
		user_str_groups=','.join(map(str, user_groups))
		group=row.get('group',user_str_groups)
		if group:
			group_lst=list(group.split(","))
			group_objs=Group.objects.filter(name__in=group_lst)
			user.group.clear()
			user.group.add(*group_objs)
		else:
			user.group.clear() 

		if user_obj_exists:
			if password:
				user.set_password(password)
			else:
				pass
		else:
			user.set_password(password)
		user.email = row.get("email".strip(),user.email)
		user.first_name = row.get('first_name',user.first_name)
		user.last_name = row.get('last_name',user.last_name)
		user.created_by = logged_in_user
		user.email_password = email_password.strip()
		user.is_active=row.get("status",user.is_active)
		if employee_id:
			user.employee_id = employee_id
		Reporting_User = row.get('reporting_to')
		if Reporting_User:
			reporting_user_obj = User.objects.get(username=Reporting_User)
			user.reporting_to = reporting_user_obj
		elif Reporting_User=='':
			user.reporting_to=None	
		call_protocol=row.get("call_protocol")
		if call_protocol and call_protocol!='None':
			call_type_dict=dict(CALL_TYPE)
			call_protocol_key = [k for k, v in call_type_dict.items() if v == call_protocol]#we need to store the call type key as we get value from dict we are getting key from calltype
			user.call_type=call_protocol_key[0]
		
		if row.get('dial_trunk')=='':
			user.trunk=None
		elif row.get('dial_trunk'):
			trunk_obj=DialTrunk.objects.get(name=row.get('dial_trunk'))
			user.trunk=trunk_obj
		elif row.get('dial_trunk')!=None:
			user.trunk=user.trunk
		
		caller_id=row.get('caller_id',user.caller_id)

		user.caller_id=caller_id

		user.save()
		if created:
			user_variable = UserVariable()
			user_variable.user = user
			extension_exist = UserVariable.objects.all().values_list('extension',flat=True)
			extension = sorted(list(set(four_digit_number) - set(extension_exist)))[0]
			user_variable.extension = extension
		else:
			user_variable = UserVariable.objects.get(user=user)

		#this domain, wfh_numeric need to optimize for missing column name it will come as None,
		# if column exists and value empty it comes as '' and if value exists it comes value we need to obj and save it
		
		if row.get('domain')=='':
			dmn=None
		elif row.get('domain'):
			dmn=Switch.objects.get(name=row.get('domain'))
		elif row.get('domain')!='None':
			dmn=user.properties.domain
		user_variable.domain=dmn
		
		if row.get('wfh_numeric')=='':
			klm=None
		elif row.get('wfh_numeric'):
			klm=row.get('wfh_numeric')
		elif row.get('wfh_numeric')!='None':
			klm=user.properties.wfh_numeric
		user_variable.wfh_numeric=klm
		user_variable.save()

def upload_dnc_nums(data, logged_in_user):
	"""
	this is the function defined for uploading the dnc numbers 
	"""	
	try:
		for index, row in data.iterrows():
			numeric = row.get("numeric", "")
			campaign = row.get("campaign", "")
			camp_obj=None
			if campaign:
				camp_obj = list(Campaign.objects.filter(name__in=campaign.split(',')))
			global_dnc = row.get("global_dnc", False)
			dnc_obj = DNC.objects.create(numeric=numeric[-10:],global_dnc=global_dnc)
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

		# download_folder = settings.MEDIA_ROOT+"/download/"+datetime.now().strftime("%m.%d.%Y")+"/"+str(user.id)+"/"
		download_folder = settings.MEDIA_ROOT+"/download/"+datetime.now().strftime("%m.%d.%Y")+"/"+str(user)+"/"

		if not os.path.exists(download_folder):
			os.makedirs(download_folder)
		if file_type == 'csv':
			file_path = download_folder+str(user)+'_'+str(report_name)+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".csv"
			with open(file_path, 'w', newline='') as file:
				writer = csv.writer(file, delimiter=',')
				writer.writerows(csv_file)
				file.close()
		else:
			file_path = download_folder+str(user)+'_'+str(report_name)+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".xlsx"
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
			sending_reports_through_mail(user,report_name)
		if download_report_id !=None:
			os.remove(file_path)
			set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
		transaction.commit()
		connections['crm'].close()      
		connections['default'].close()
	except Exception as e:
		print('save file error',e)
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print(exc_type, fname, exc_tb.tb_lineno)

def sending_reports_through_mail(user,report_name):
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

def extract_inner_data(row, data, prefix=""):
    if isinstance(data, dict):
        for key, value in data.items():
            new_prefix = f"{key}" if prefix else key
            if isinstance(value, dict):
                extract_inner_data(row, value, prefix=new_prefix)
            else:
                row[new_prefix] = value
    return row

def extract_dynamic_keys(feedback_dict):
    dynamic_keys = {}
    for key, value in feedback_dict.items():
        if isinstance(value, dict):
            dynamic_keys.update(value)
        else:
            dynamic_keys[key] = value
    return dynamic_keys

def convert_timezone_to_kolkata(dt):
	""" Converts a datetime object to Kolkata (Asia/Kolkata) timezone. """
	if dt is not None:
		if dt.tzinfo is None:
			dt = dt.tz_localize('UTC')
		return dt.tz_convert(pytz.timezone('Asia/Kolkata'))
	return None

def process_datetime_columns(df):
	""" Process datetime columns in a DataFrame to convert them to Kolkata (Asia/Kolkata) timezone. """
	for col, col_dtype in df.dtypes.items():
		if col_dtype in ['datetime64[ns, UTC]', 'datetime64[ns]']:
			df[col] = df[col].apply(convert_timezone_to_kolkata)
			df[col] = df[col].apply(lambda x: x.replace(tzinfo=None) if x is not None else None)

def thri_download_call_detail_report(filters, user, col_list, serializer_class, download_report_id=None):
	"""
	this is the function for download call details reports
	"""	
	try:
		query = {}
		user = User.objects.get(id=user)
		admin = False
		if user.user_role and user.user_role.access_level == 'Admin':
			admin = True
		all_campaigns = filters.get("all_campaigns",[])
		if '' in all_campaigns: all_campaigns.remove('')
		all_users = filters.get("all_users",[])
		if '' in all_users:
			all_users.remove('')
			all_users.append(0)
		selected_campaign = filters.get("selected_campaign", "")
		selected_disposition = filters.get("selected_disposition", "")
		selected_user = filters.get("selected_user", "")
		numeric = filters.get("numeric", "")
		start_date = filters.get("start_date", "")
		modified_date = start_date[:10]
		end_date = filters.get("end_date", "")
		start_date = datetime.strptime(start_date,"%Y-%m-%d %H:%M").isoformat()
		end_date = datetime.strptime(end_date,"%Y-%m-%d %H:%M").isoformat()
		unique_id = filters.get("unique_id","")
		dispo_keys = filters.get("dispo_keys","")
		download_type = filters.get('download_type',"")
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
			sql_query_where = ' ((callcenter_calldetail.campaign_name IN '+str(tuple(selected_campaign))+' AND callcenter_calldetail.user_id IN '+str(tuple(all_users))+') OR ( callcenter_calldetail.campaign_name IN '+str(tuple(selected_campaign))+' AND callcenter_calldetail.user_id IS NULL ))'
		else:
			sql_query_where = ' ((callcenter_calldetail.user_id IN '+str(tuple(all_users))+') OR ( callcenter_calldetail.user_id IS NULL ))'
		if selected_user and selected_campaign:
			sql_query_where = ' (callcenter_calldetail.campaign_name IN '+str(tuple(selected_campaign))+' AND callcenter_calldetail.user_id IN '+str(tuple(all_users))+') '
		elif selected_user:
			sql_query_where = ' (callcenter_calldetail.user_id IN '+str(tuple(all_users))+' ) '
		elif selected_campaign:
			if selected_campaign:
				sql_query_where = ' (callcenter_calldetail.campaign_name IN '+str(tuple(selected_campaign))+' ) '
				if not (user.is_superuser or admin):
					get_camp_users = list(get_campaign_users(selected_campaign,
						user).values_list("id",flat=True))
					if len(get_camp_users) == 1:
						get_camp_users.append(get_camp_users[0])
					sql_query_where = ' ((callcenter_calldetail.campaign_name IN '+str(tuple(selected_campaign))+' AND callcenter_calldetail.user_id IN '+str(tuple(get_camp_users))+') OR ( callcenter_calldetail.campaign_name IN '+str(tuple(selected_campaign))+' AND callcenter_calldetail.user_id IS NULL ))'
		if selected_disposition:
			if len(selected_disposition)==1:
				selected_disposition.append(selected_disposition[0])
			sql_query_where += " and ( callcenter_cdrfeedbck.primary_dispo IN "+str(tuple(selected_disposition))+" ) "
		if numeric:
			sql_query_where += " and ( callcenter_calldetail.customer_cid = '"+str(numeric)+"') "
		if unique_id:
			sql_query_where += " and ( callcenter_calldetail.uniqueid = '"+str(unique_id)+"') "
		where = " WHERE ( callcenter_calldetail.created at time zone 'Asia/Kolkata' >= '" + str(start_date)+"' and callcenter_calldetail.created at time zone 'Asia/Kolkata' <= '" +str(end_date)+"') and "+ sql_query_where + ' order by callcenter_calldetail.created desc'
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
				sub_dispo += "callcenter_cdrfeedbck.feedback ->> '"+str(col_name)+"' as "+'"'+str(col_name)+'"'
			if index < len(col_list) and sub_dispo[-2:] != ", ":
				sub_dispo += ", "
		download_folder = settings.MEDIA_ROOT+"/download/"+datetime.now().strftime("%m.%d.%Y")+"/"+str(user.id)+"/"
		if not os.path.exists(download_folder):
			os.makedirs(download_folder)
		set_download_progress_redis(download_report_id, 25, is_refresh=True)
		db_settings = settings.DATABASES['default']
		if sub_dispo[-2:] == ", ":
			sub_dispo = sub_dispo[:-2]
		sub_dispo += " from callcenter_calldetail left join callcenter_diallereventlog on callcenter_diallereventlog.session_uuid = callcenter_calldetail.session_uuid left join callcenter_cdrfeedbck on callcenter_cdrfeedbck.calldetail_id=callcenter_calldetail.id left join callcenter_user usr on usr.id = callcenter_calldetail.user_id left join callcenter_user supr on supr.id = usr.reporting_to_id left join (select sms.session_uuid as session_uuid, string_agg(template.name, ', ') as name from callcenter_smslog sms left join callcenter_smstemplate template on sms.template_id = template.id group by sms.session_uuid) sms on sms.session_uuid = callcenter_calldetail.session_uuid left join ( SELECT * FROM dblink('dbname=crm port={port} host={host} user={user} password={password}','SELECT id, customer_raw_data,created_date,modified_date FROM crm_contact') AS tb2 (id bigint, customer_raw_data jsonb,created_date timestamp with time zone,modified_date timestamp with time zone) WHERE  (modified_date >= '{modified_date}') ) AS tb2 ON tb2.id = callcenter_calldetail.contact_id ".format(port = db_settings['PORT'], host = db_settings['HOST'], user = db_settings['USER'], password=db_settings['PASSWORD'],modified_date = modified_date) + where
		db_connection = "postgresql://{user}:{password}@{host}:{port}/{db_name}".format(user = db_settings['USER'], password=db_settings['PASSWORD'], host = db_settings['HOST'], db_name = db_settings['NAME'], port = db_settings['PORT'])
		# print(sub_dispo)
		if download_type == 'xls':
			file_path = download_folder+str(user.id)+'_'+str('call_details')+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".xlsx"
			with pd.ExcelWriter(file_path, engine="xlsxwriter",options={'remove_timezone': True}) as writer:
				row = 0
				for chunk in pd.read_sql(sub_dispo,db_connection,chunksize=10000):
					chunk.to_excel(writer,'Main', startrow=row, index=False)
					row = row + len(chunk.index) +  1      
					time.sleep(0.01)
		else:
			file_path = download_folder+str(user.id)+'_'+str('call_details')+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".csv"
			# df = pd.read_sql(sub_dispo,db_connection)
			# df.to_csv(file_path, index = False)
			file_exists = False
			try:
				for chunk in pd.read_sql(sub_dispo,db_connection,chunksize=10000):
					if not file_exists:
						file_exists = True
						chunk.to_csv(file_path, index = False)
						chunk = []
						time.sleep(0.01)
					else:
						chunk.to_csv(file_path, index = False,mode='a',header=False)
						chunk = []
						time.sleep(0.01)
			except Exception as e:
				print(e)
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
		print('calldetail download error',e)
	finally:
		transaction.commit()
		connections["default"].close()
def download_call_detail_report(filters, user, col_list, serializer_class, download_report_id=None):
	"""
	this is the function for download call details reports
	"""	
	try:
		def process_time_columns(final_df, orig_column, new_column, default_column):
			# This function will pick time values from dialler event log table and if its 00:00:00 then take the value from calldetail
			# Identify rows where original column is '00:00:00'
			mask = final_df[orig_column].astype(str) == '00:00:00'
			# Fill those specific rows with values from default column
			final_df.loc[mask, new_column] = final_df.loc[mask, default_column]
			# For other rows, keep values from original column
			final_df.loc[~mask, new_column] = final_df.loc[~mask, orig_column]

		query = {}
		user = User.objects.get(id=user)
		admin = False
		if user.user_role and user.user_role.access_level == 'Admin':
			admin = True
		all_campaigns = filters.get("all_campaigns",[])
		if '' in all_campaigns: all_campaigns.remove('')
		all_users = filters.get("all_users",[])
		print(all_users, 'all_users 1')
		if '' in all_users:
			all_users.remove('')
			all_users.append(0)
   
		print(all_users, 'all_users 2')
		selected_campaign = filters.get("selected_campaign", "")
		selected_campaigngroup = filters.get('selected_campaigngroup','')
		selected_disposition = filters.get("selected_disposition", "")
		selected_user = filters.get("selected_user", "")
		print(selected_user, 'selected_user 1')
		numeric = filters.get("numeric", "")
		start_date = filters.get("start_date", "")
		modified_date = start_date[:10]
		end_date = filters.get("end_date", "")
		start_date = datetime.strptime(start_date,"%Y-%m-%d %H:%M").isoformat()
		end_date = datetime.strptime(end_date,"%Y-%m-%d %H:%M").isoformat()
		unique_id = filters.get("unique_id","")
		dispo_keys = filters.get("dispo_keys","")
		dispo_keys_lst = dispo_keys.split(',')
		download_type = filters.get('download_type',"csv")
		uniquefields = filters.get('uniquefields',"")
		db_settings = settings.DATABASES['default']
		db_connection = "postgresql://{user}:{password}@{host}:{port}/{db_name}".format(user = db_settings['USER'], password=db_settings['PASSWORD'], host = db_settings['HOST'], db_name = db_settings['NAME'], port = db_settings['PORT'])
		db_settings_crm=settings.DATABASES['crm']
		db_connection1 = "postgresql://{user}:{password}@{host}:{port}/{db_name}".format(user = db_settings_crm['USER'], password=db_settings_crm['PASSWORD'], host = db_settings_crm['HOST'], db_name = db_settings_crm['NAME'], port = db_settings_crm['PORT'])
		where = " WHERE (callcenter_calldetail.created at time zone 'Asia/Kolkata' >= '" + str(start_date) + "' and callcenter_calldetail.created at time zone 'Asia/Kolkata' <= '" + str(end_date) + "')"
		if selected_campaigngroup:
			grp_list = list(Campaign.objects.filter(campaign_group__name__in =selected_campaigngroup).values_list('name',flat=True))
			if not selected_campaign:
				selected_campaign = []
			selected_campaign += grp_list
		if selected_campaign:
			if isinstance(selected_campaign, list):
				camp_ids = "', '".join(selected_campaign)
				where += f" AND callcenter_calldetail.campaign_name IN ('{camp_ids}')"
			else:
				where += f" AND callcenter_calldetail.campaign_name = '{selected_campaign}'"
		if selected_user :
			if isinstance(selected_user, list):
				user_ids = "', '".join(selected_user)
				where += f" AND callcenter_calldetail.user_id IN ('{user_ids}')"
			else:
				where += f" AND callcenter_calldetail.user_id = '{selected_user}'"
		if all_users :
			if isinstance(all_users, list):
				user_ids = "', '".join(all_users)
				where += f" AND callcenter_calldetail.user_id IN ('{user_ids}')"
			else:
				where += f" AND callcenter_calldetail.user_id = '{all_users}'"
		if numeric:
			where += f" AND callcenter_calldetail.customer_cid = ('{numeric}')"

		if unique_id:
			where += f" AND callcenter_calldetail.uniqueid = ('{unique_id}')"

		if selected_disposition:
			selected_disposition = str(selected_disposition).strip('[]')
			selected_disp_query  =f'''where callcenter_cdrfeedbck.primary_dispo IN ({selected_disposition}) '''
		else:
			selected_disp_query = ''
		where1 = " WHERE (callcenter_calldetail.created at time zone 'Asia/Kolkata' >= '" + str(start_date)+"' and callcenter_calldetail.created at time zone 'Asia/Kolkata' <= '" +str(end_date)+"')"+  ' order by callcenter_calldetail.created desc'
		where2 = " WHERE (callcenter_user.created at time zone 'Asia/Kolkata' >= '" + str(start_date)+"' and callcenter_user.created at time zone 'Asia/Kolkata' <= '" +str(end_date)+"')"+  ' order by callcenter_user.created desc'
		callcenter_calldetail = "SELECT *  "
		cdrfeedbck = "SELECT callcenter_cdrfeedbck.primary_dispo,callcenter_cdrfeedbck.comment,callcenter_cdrfeedbck.calldetail_id,callcenter_cdrfeedbck.session_uuid ,callcenter_cdrfeedbck.feedback as cdr_feedback_dispkey"
		user_table="SELECT *,CONCAT(callcenter_user.first_name, ' ' ,callcenter_user.last_name) as full_name "
		user_table1= "SELECT callcenter_user.username,T2.username as supervisor_name FROM callcenter_user LEFT JOIN callcenter_user T2 ON callcenter_user.reporting_to_id = T2.id "
		smslog = "SELECT callcenter_smslog.template_id,callcenter_smslog.session_uuid,CASE WHEN callcenter_smslog.session_uuid IS NULL THEN 'No' WHEN callcenter_smslog.session_uuid IS NOT NULL THEN 'Yes' END as sms_sent "

		smstemplate ="SELECT callcenter_smstemplate.id,callcenter_smstemplate.name as sms_message "

		db_settings = settings.DATABASES['default']
		callcenter_calldetail += "from callcenter_calldetail " + where1
		cdrfeedbck += " from callcenter_cdrfeedbck " 
		cdrfeedbck += selected_disp_query
		user_table +=" from callcenter_user "
		smslog += " from callcenter_smslog "
		smstemplate += " from callcenter_smstemplate "
		crm_contact='SELECT id,customer_raw_data,created_date '
		if uniquefields:
			where3=" WHERE (crm_contact.created_date at time zone 'Asia/Kolkata' >= '" + str(start_date)+"' and crm_contact.created_date at time zone 'Asia/Kolkata' <= '" +str(end_date)+"')"+  ' order by crm_contact.created_date desc'
			crm_contact += " from crm_contact " + where3	
		else:
			where3=" WHERE (crm_contact.created_date at time zone 'Asia/Kolkata' >= '" + str(start_date)+"' and crm_contact.created_date at time zone 'Asia/Kolkata' <= '" +str(end_date)+"')"+  ' order by crm_contact.created_date desc'
			crm_contact += " from crm_contact "
		df2=pd.read_sql(cdrfeedbck,db_connection)
		dispo_keys_df = df2.copy()
		df2.drop(columns=["cdr_feedback_dispkey"], inplace=True)
		dispo_keys_df['dynamic_keys'] = dispo_keys_df['cdr_feedback_dispkey'].apply(extract_dynamic_keys)
		dynamic_keys_df = pd.json_normalize(dispo_keys_df['dynamic_keys'])
		dispo_keys_df = pd.concat([dispo_keys_df, dynamic_keys_df], axis=1)
		dispo_keys_lst.append("session_uuid")

		non_exists_columns_list = [value for value in dispo_keys_lst if value not in dispo_keys_df.columns]
		dispo_keys_df[[non_exists_columns_list]] = np.nan
		dispo_keys_df = dispo_keys_df[dispo_keys_lst]
		dispo_keys_df = dispo_keys_df.rename(columns={'session_uuid':'session_uuid_dispo_keys'})
		if selected_disp_query:
			dispo_matched_vals = df2['session_uuid'].to_list()
			dispo_matched_vals          = [str(val) for val in dispo_matched_vals]
			dispo_matched_vals = str(dispo_matched_vals).strip('[]')
			where += f' AND  callcenter_calldetail.session_uuid in ({dispo_matched_vals})'
		calldetail = "SELECT * FROM callcenter_calldetail" + where + " ORDER BY callcenter_calldetail.created DESC "
		import copy
		new_dialer_where = copy.copy(where)
		new_dialer_where_ = new_dialer_where.replace('callcenter_calldetail',"callcenter_diallereventlog")
		diallereventlog = "SELECT wait_time as dialer_query_wait_time,init_time as dialer_query_init_time,ring_time as dialer_query_ring_time,connect_time as dialer_query_connect_time,hangup_time as dialer_query_hangup_time,ring_duration as dialer_query_ring_duration,hold_time as dialer_query_hold_time,bill_sec as dialer_query_talk_time,call_duration as dialer_query_call_duration,session_uuid as dialer_query_session FROM callcenter_diallereventlog" + new_dialer_where_ + " ORDER BY callcenter_diallereventlog.created DESC "
		reader_dialer=pd.read_sql(diallereventlog,db_connection,chunksize=1000)

		reader=pd.read_sql(calldetail,db_connection,chunksize=1000)
		download_folder = settings.MEDIA_ROOT+"/download/"+datetime.now().strftime("%m.%d.%Y")+"/"+str(user.id)+"/"
		if not os.path.exists(download_folder):
			os.makedirs(download_folder)
		if download_report_id:
			set_download_progress_redis(download_report_id, 25, is_refresh=True)
		df0 = pd.concat(reader)
		reader1=pd.read_sql(callcenter_calldetail,db_connection,chunksize=1000)
		df1 = pd.concat(reader1)
		df_dialer_query = pd.concat(reader_dialer)
		df3=pd.read_sql(user_table,db_connection)
		df9=pd.read_sql(user_table1,db_connection)
		df4=pd.read_sql(smslog,db_connection)
		df5=pd.read_sql(smstemplate,db_connection)
		df_user=pd.read_sql(user_table,db_connection)
		df_crm=pd.read_sql(crm_contact,db_connection1)
		df_crm1 = df_crm.apply(lambda row: extract_inner_data(row, row['customer_raw_data']), axis=1)
		df_crm1.drop(columns=['customer_raw_data'], inplace=True)
		df1 = df1.rename(columns=lambda x: x + '_dialer')
		df0 = df0.rename(columns=lambda x: x + '_calldetail')
		df_dialerlog = pd.merge(df0,df1,how='left',right_on='session_uuid_dialer' , left_on='session_uuid_calldetail')
		df2 = df2.rename(columns=lambda x: x + '_calldetailfb')
		df_cdr = pd.merge(df_dialerlog,df2,how='left',right_on='calldetail_id_calldetailfb',left_on='id_calldetail')
		df_crm1 = df_crm1.rename(columns={
			'id':'id_contact',
			'created_date':'created_date_contact'
		})
		df_cdr=df_cdr.merge(df_crm1,how='left',right_on='id_contact',left_on='contact_id_calldetail')
		df_cdr['hangup_cause_calldetail'] = np.where(((df_cdr['hangup_cause_dialer'].isnull())), df_cdr['hangup_cause_calldetail'], df_cdr['hangup_cause_dialer'])
		df_cdr['hangup_cause_code_calldetail'] = np.where(((df_cdr['hangup_cause_code_dialer'].isnull())), df_cdr['hangup_cause_code_calldetail'], df_cdr['hangup_cause_code_dialer'])
		df_cdr['dialed_status_calldetail'] = np.where(((df_cdr['dialed_status_dialer'].isnull())), df_cdr['dialed_status_calldetail'], df_cdr['dialed_status_dialer'])
		df_cdr['ring_duration_calldetail'] = np.where(((df_cdr['ring_duration_dialer'].isnull())), df_cdr['ring_duration_calldetail'], df_cdr['ring_duration_dialer'])
		df_cdr['connect_time_calldetail'] = np.where(((df_cdr['connect_time_dialer'].isnull())), df_cdr['connect_time_calldetail'], df_cdr['connect_time_dialer'])
		df_cdr['call_duration_calldetail'] = np.where(((df_cdr['call_duration_dialer'].isnull())), df_cdr['call_duration_calldetail'], df_cdr['call_duration_dialer'])
		df_cdr.drop(['id_dialer','phonebook_dialer','contact_id_dialer','a_leg_uuid_dialer','b_leg_uuid_dialer','init_time_dialer','ring_time_dialer','ring_duration_dialer','connect_time_dialer','wait_time_dialer','hold_time_dialer','media_time_dialer','callflow_dialer','callmode_dialer','customer_cid_dialer','destination_extension_dialer','call_duration_dialer','bill_sec_dialer','hangup_time_dialer','dialed_status_dialer','hangup_cause_dialer','hangup_cause_code_dialer','created_dialer','updated_dialer','campaign_id_dialer','site_id_dialer','user_id_dialer','ivr_duration_dialer','campaign_name_dialer','uniqueid_dialer'], axis = 1,inplace=True)
		df_cdr['user_id_calldetail'] = df_cdr['user_id_calldetail'].fillna(0)
		df3['id'] = df3['id'].astype('int64')
		df_cdr['user_id_calldetail'] = df_cdr['user_id_calldetail'].astype('int64')
		df_usr=df_cdr.merge(df3,how='left',left_on='user_id_calldetail',right_on = 'id')
		df_smslog_template=df4.join(df5.set_index('id'),lsuffix='_log',rsuffix='_template',on='template_id')
		final_df=df_usr.join(df_smslog_template.set_index('session_uuid'),lsuffix='_1',rsuffix='_2',on='session_uuid_calldetail')

		# final_df['call_duration_calldetail_dt']  = final_df['call_duration_calldetail'].apply(lambda x: x.hour * 3600 + x.minute * 60 + x.second)
		# final_df['feedback_time_calldetail_dt']   = final_df['feedback_time_calldetail'].apply(lambda x: x.hour * 3600 + x.minute * 60 + x.second)
		# final_df['call_length'] = final_df['call_duration_calldetail_dt'] + final_df['feedback_time_calldetail_dt']
		# # final_df['call_length'] = pd.to_timedelta(final_df['call_length'], unit='s').astype(str)
		# final_df['call_length'] = pd.to_timedelta(final_df['call_length'], unit='s')
		# final_df['call_length'] = final_df['call_length'].apply(lambda x: f'{x.components.hours:02d}:{x.components.minutes:02d}:{x.components.seconds:02d}')
		try:
			final_df.drop(['id_calldetail','destination_extension_calldetail','a_leg_uuid_calldetail','b_leg_uuid_calldetail','user_id_calldetail','predictive_time_calldetail','media_time_calldetail','cfc_number_calldetail','created_calldetail','updated_calldetail','campaign_id_calldetail','site_id_calldetail','inbound_time_calldetail','blended_time_calldetail','session_uuid_dialer','first_name','last_name', 'reporting_to_id','template_id'],axis=1,inplace=True)
		except:
			pass

		dict={'campaign_name_calldetail': 'campaign_name','username': 'user','phonebook_calldetail': 'phonebook','customer_cid_calldetail': 'customer_cid','contact_id_calldetail': 'contact_id','uniqueid_calldetail': 'uniqueid','session_uuid_calldetail': 'session_uuid','callflow_calldetail': 'callflow','callmode_calldetail': 'callmode','ivr_duration_calldetail': 'ivr_duration','call_duration_calldetail': 'call_duration','hangup_cause_calldetail': 'hangup_cause','hangup_cause_code_calldetail': 'hangup_cause_code','dialed_status_calldetail': 'dialed_status','name':'sms_message','primary_dispo_calldetailfb':'primary_dispo','comment_calldetailfb':'comment','internal_tc_number_calldetail':'internal_tc_number','external_tc_number_calldetail':'external_tc_number',
		'progressive_time_calldetail':'progressive_time','preview_time_calldetail':'preview_time','predictive_wait_time_calldetail':'predictive_wait_time','inbound_wait_time_calldetail':'inbound_wait_time','blended_wait_time_calldetail':'blended_wait_time','hangup_source_calldetail':'hangup_source','feedback_time_calldetail': 'wrapup_time'} #'wait_time_calldetail': 'wait_time'
		final_df.rename(columns=dict,inplace=True)
		df9 = df9.replace(np.nan, '', regex=True)
		df9 = df9.rename(columns = { 'username':'sup_df_username'})
		final_df = final_df.merge(df9,left_on='user',right_on='sup_df_username',how='left')
		final_df = final_df.merge(dispo_keys_df,how='left',left_on = 'session_uuid',right_on='session_uuid_dispo_keys')
		final_df = final_df.merge(df_dialer_query,how='left',left_on = 'session_uuid',right_on='dialer_query_session')

		process_time_columns(final_df, 'dialer_query_wait_time', 'wait_time_final', 'wait_time_calldetail')
		process_time_columns(final_df, 'dialer_query_talk_time', 'talk_time_final', 'bill_sec_calldetail')
		process_time_columns(final_df, 'dialer_query_ring_duration', 'ring_duration_final', 'ring_duration_calldetail')
		process_time_columns(final_df, 'dialer_query_hangup_time', 'hangup_time_final', 'hangup_time_calldetail')
		process_time_columns(final_df, 'dialer_query_init_time', 'init_time_final', 'init_time_calldetail')
		process_time_columns(final_df, 'dialer_query_ring_time', 'ring_time_final', 'ring_time_calldetail')
		process_time_columns(final_df, 'dialer_query_hold_time', 'hold_time_final', 'hold_time_calldetail')
		process_time_columns(final_df, 'dialer_query_connect_time', 'connect_time_final', 'connect_time_calldetail')

		final_df.rename(columns={"wait_time_final":"wait_time","init_time_final":"init_time","ring_time_final":"ring_time",'connect_time_final': 'connect_time','hangup_time_final': 'hangup_time','hold_time_final': 'hold_time','talk_time_final':'talk_time','ring_duration_final':'ring_duration'},inplace=True)

		wait_time_seconds=pd.to_timedelta(final_df['wait_time'].astype(str))
		talk_time_seconds = pd.to_timedelta(final_df['talk_time'].astype(str))
		ring_time_seconds = pd.to_timedelta(final_df['ring_duration'].astype(str))
		wrapup_time_seconds = pd.to_timedelta(final_df['wrapup_time'].astype(str))

		wait_time_seconds = wait_time_seconds.dt.seconds
		talk_time_seconds = talk_time_seconds.dt.seconds
		ring_time_seconds = ring_time_seconds.dt.seconds
		wrapup_time_seconds = wrapup_time_seconds.dt.seconds

		final_df['call_duration'] = wait_time_seconds + talk_time_seconds+ring_time_seconds
		final_df['call_duration'] = pd.to_timedelta(final_df['call_duration'], unit='s')
		final_df['call_duration'] = final_df['call_duration'].apply(lambda x: f'{x.components.hours:02d}:{x.components.minutes:02d}:{x.components.seconds:02d}' if not pd.isna(x) else None)
		final_df['call_length'] = wrapup_time_seconds + wait_time_seconds + talk_time_seconds+ring_time_seconds
		final_df['call_length'] = pd.to_timedelta(final_df['call_length'], unit='s')
		final_df['call_length'] = final_df['call_length'].apply(lambda x: f'{x.components.hours:02d}:{x.components.minutes:02d}:{x.components.seconds:02d}' if not pd.isna(x) else None)
		all_cols = list(final_df.columns)
		for sel_col in col_list:
			if sel_col not in all_cols:
				final_df[sel_col] = None
		if 'feedback_time' in col_list:
			index_of_fb = col_list.index('feedback_time')
			col_list[index_of_fb] = 'wrapup_time'
		if 'bill_sec' in col_list:
			index_of_tt = col_list.index('bill_sec')
			col_list[index_of_tt] = 'talk_time'
		selected_cols = col_list
		for col_name in all_cols:
			if col_name == 'sms_sent':
				final_df['sms_sent'] = final_df['sms_sent'].fillna('No')
			# if  col_name in ['talk_time','feedback_time','bill_sec','wrapup_time']:
			# 	pass
			if col_name not in selected_cols:
				final_df.drop(col_name,axis=1,inplace=True)	
		final_df = final_df[col_list]
		# column_name_mapping = {
        #        'feedback_time': 'wrapup_time',
        #        'bill_sec': 'talk_time'
        #                }
		# for col_name in column_name_mapping.keys():
		# 	if col_name in final_df.columns:
		# 		final_df[column_name_mapping[col_name]] = final_df[col_name]
		# 		final_df.drop(col_name, axis=1, inplace=True)
		# final_df = final_df.rename(columns=column_name_mapping)
		if download_type == 'xls':
			process_datetime_columns(final_df)
			file_path = download_folder+str(user.id)+'_'+str('call_details')+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".xlsx"
			with pd.ExcelWriter(file_path, engine="xlsxwriter",options={}) as writer:
				if 'campaign_name' in list(final_df.columns):
					name=final_df['campaign_name']
					final_df.drop(labels=['campaign_name'],axis=1,inplace=True)
					final_df.insert(0,'campaign_name',name)
				final_df.to_excel(writer, sheet_name = "Sheet1", header = True, index = False)
		else:
			process_datetime_columns(final_df)
			file_path = download_folder+str(user.id)+'_'+str('call_details')+'_'+str(datetime.now().strftime("%m.%d.%Y.%H.%M.%S"))+".csv"
			final_df.to_csv(file_path, index = False)
		f = open(file_path, 'rb')	
		if download_report_id:
			download_report = DownloadReports.objects.get(id=download_report_id)
			download_report.downloaded_file.save(os.path.basename(f.name), File(f), save=True)
			download_report.is_start = False
			download_report.save()
		f.close()
		subprocess.call(['chmod', '777', file_path])
		if download_report_id !=None:
			set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
			os.remove(file_path)
		else:
			sending_reports_through_mail(user,'call_details')
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
	# return camp[camp != np.array(None)]
	return [i for i in list(camp[camp != np.array(None)]) if i!=""]

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
			os.remove(file_path)
			set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
		transaction.commit()
		connections['crm'].close()      
		connections['default'].close()
	except Exception as e:
		print('save file error',e)

# def try_action_agent_performance_report(filters,download=False,download_report_id=0):
# 	try:
# 		print('ENTER ACTION AGENT PERF REP')
# 		all_users = filters.get("all_users", [])
# 		print('All USERS-------',all_users)
# 		selected_campaign = filters.get("selected_campaign", [])
# 		start_date = filters.get("start_date", "")
# 		end_date = filters.get("end_date", "")
# 		download_type = "csv"
# 		selected_user = filters.get('selected_user',"")
# 		start_date = start_date[:10]
# 		start_date = datetime.strptime(start_date, '%Y-%m-%d')
# 		end_date = end_date[:10]
# 		end_date = datetime.strptime(end_date, '%Y-%m-%d')
# 		# end_date = start_date + timedelta(days=1)
# 		# start_date = datetime.strptime(start_date,"%Y-%m-%d %H:%M").isoformat()
# 		page = int(filters.get('page' ,0))
# 		paginate_by = int(filters.get('paginate_by', 0))
# 		call_result = [{}]
# 		pause_breaks = list(set(PauseBreak.objects.values_list('name',flat=True)))
		
# 		all_col = ['app_idle_time','dialer_idle_time','pause_progressive_time','progressive_time','preview_time',
# 					'predictive_wait_time','inbound_wait_time','blended_wait_time','ring_duration','ring_duration_avg','hold_time','media_time','predictive_wait_time_avg','talk','talk_avg','bill_sec','bill_sec_avg','call_duration','feedback_time','feedback_time_avg','break_time','break_time_avg','app_login_time'
# 					] + pause_breaks + ['dialer_login_time','total_login_time','first_login_time','last_logout_time','total_calls','total_connected_calls','total_unique_connected_calls','created_date']
# 		if filters.get("start_date_ui",""):
# 			start_date = filters.get("start_date_ui","")
# 		conn = connections['default']
# 		agent_activity_query = f'''select 
# 				user_id,
# 				event,
# 				campaign_name,DATE(created) as created_date,
# 				count(user_id) as activity_count,
# 				sum(break_time) as break_time,
# 				sum(pause_progressive_time) as pause_progressive_time,
# 				sum(predictive_time) as predictive_time,
# 				sum(progressive_time) as progressive_time,
# 				sum(preview_time) as preview_time,
# 				sum(predictive_wait_time) as predictive_wait_time,
# 				sum(inbound_time) as inbound_time,
# 				sum(blended_time) as blended_time,
# 				sum(inbound_wait_time) as inbound_wait_time,
# 				sum(blended_wait_time) as blended_wait_time,
# 				sum(idle_time) as app_idle_time
# 				from callcenter_agentactivity 
# 				where created>'{start_date}' and created < '{end_date}'
# 				group by user_id,event,campaign_name,DATE(created)'''
# 		agent_activity_df = pd.read_sql_query(agent_activity_query,conn)
# 		print('-------11111111------------select user_id,event,created,campaign_name,count(user_id) as activity_count,sum(break_time) as break_time,sum(pause_progressive_time) as pause_progressive_time,sum(predictive_time) as predictive_time,sum(progressive_time) as progressive_time,sum(preview_time) as preview_time,sum(predictive_wait_time) as predictive_wait_time,sum(inbound_time) as inbound_time,sum(blended_time) as blended_time,sum(inbound_wait_time) as inbound_wait_time,sum(blended_wait_time) as blended_wait_time,sum(idle_time) as app_idle_time from callcenter_agentactivity where created>',start_date,' and created < ',end_date,'group by user_id,event,campaign_name,created')
# 		if download:
# 			set_download_progress_redis(download_report_id, 25, is_refresh=True)
# 		is_user_obj = False
# 		if selected_user:
# 			queryset = User.objects.filter(id__in=selected_user)
# 			is_user_obj = True
# 		else:
# 			if start_date == str(date.today()):
# 				# queryset = User.objects.filter(last_login__date=start_date).filter(id__in=all_users)
# 				# from datetime import time as time_datetime
# 				# start_time = datetime.combine(start_date, time_datetime.min)
# 				# end_date = datetime.combine(end_date, time_datetime.min)
# 				queryset = User.objects.filter(last_login__gte=start_date,last_login__lte=end_date).filter(id__in=all_users)		
# 				# dboptim
# 				is_user_obj = True
# 			else:
# 				queryset_agent = agent_activity_df[['user_id']] #AgentActivity.objects.filter(created__date = start_date).exclude(user_id = None).values('user_id').order_by('-user_id').annotate(count =Count('user_id'))
# 				print('22222222222222222222',queryset_agent)
# 				queryset_agent = queryset_agent.drop_duplicates(subset='user_id', keep="first")
# 				print('3333333333333333333333',queryset_agent)
# 				# queryset_agent['user_id'] = queryset_agent['user_id'].astype(str)

# 				# queryset = queryset_agent[int(queryset_agent['user_id']).apply(str).isin(all_users)]
# 				queryset = queryset_agent[queryset_agent['user_id'].apply(lambda x: str(int(x)) if not pd.isna(x) else '').isin(all_users)]

# 				print('4444444444444444444444',queryset)
# 				queryset = queryset.to_dict('records')
# 				print('5555555555555555555555',queryset)
# 				del queryset_agent
# 				print(len(queryset),'querysetquerysetquerysetqueryset',queryset)
# 		if download:
# 			users = queryset
# 		else:
# 			users = get_paginated_object(queryset, page, paginate_by)
# 		if download:
# 			set_download_progress_redis(download_report_id, 37, is_refresh=True)
# 		if len(queryset) == 0:
# 			if download:
# 				return pd.DataFrame(columns=['username','fullname','supervisor']+all_col)
# 			return call_result,users
# 		print(users,'usersusers')
# 		if is_user_obj:
# 			required_agents =  [user.id for user in users]
# 		else:
# 			del queryset
# 			required_agents =  [user['user_id'] for user in users]
# 		# All The Required queries
		

# 		user_query = 'select id,username,first_name,last_name,reporting_to_id from callcenter_user'

# 		calldetail_query = f'''select user_id,campaign_name,DATE(created) as cd_created_date,
# 							count(DISTINCT CASE WHEN dialed_status = 'Connected' THEN customer_cid ELSE NULL END) as total_unique_connected_calls, 
# 						count(distinct dialed_status) as total_connected_calls,
# 						count(user_id) as calldetail_count,
# 						sum(media_time) as media_time,
# 						sum(hold_time) as hold_time,
# 						sum(ring_duration) as ring_duration_calldetail,
# 						sum(call_duration) as call_duration,
# 						sum(bill_sec) as bill_sec,
# 						sum(feedback_time) as feedback_time 
# 						from callcenter_calldetail 
# 						where created>'{start_date}' and created < '{end_date}'
# 						group by user_id,campaign_name,DATE(created)'''
		
# 		print('-------calldetail query------------',"select user_id,campaign_name,DATE(created) as created_date,count(DISTINCT CASE WHEN dialed_status= 'Connected' THEN customer_cid ELSE NULL END) as total_unique_connected_calls, count(distinct dialed_status) as total_connected_calls,count(user_id) as calldetail_count,sum(media_time) as media_time,sum(hold_time) as hold_time,sum(ring_duration) as ring_duration_calldetail,sum(call_duration) as call_duration,sum(bill_sec) as bill_sec,sum(feedback_time) as feedback_time from callcenter_calldetail where created>'",start_date,"' and created < '",end_date,"' group by user_id,campaign_name,DATE(created)")

# 		breaks_activity_query = f'''select user_id,DATE(created) as created_date,sum(break_time) as break_time,
# 						break_type 
# 						from callcenter_agentactivity where created>'{start_date}' and created < '{end_date}'
# 						group by user_id,break_type,DATE(created) '''

# 		ring_duration_query = f'''select user_id,campaign_name,DATE(created) as created_date,sum(ring_duration) as ring_duration,sum(bill_sec) as bill_sec_dialler from callcenter_diallereventlog where DATE(created)>'{start_date}' and created < '{end_date}' group by user_id,campaign_name,created'''

# 		total_connected_calls_query= f''' select user_id,campaign_name,DATE(created) as created_date,count(dialed_status) as total_connected_calls from callcenter_calldetail where dialed_status='Connected' AND  created>'{start_date}' and created < '{end_date}' group by user_id,campaign_name,DATE(created)'''

# 		if download:
# 			set_download_progress_redis(download_report_id, 60, is_refresh=True)
		
# 		total_connected_calls_df = pd.read_sql_query(total_connected_calls_query, conn)
# 		total_connected_calls_df = total_connected_calls_df.rename(columns={'user_id':'apr_connected_user_id','campaign_name':'apr_connected_campaign_name'})
		
# 		if selected_campaign:

# 			total_connected_calls_df = total_connected_calls_df[(total_connected_calls_df['apr_connected_campaign_name'].isin(selected_campaign))]
# 			agent_activity_df = agent_activity_df[(agent_activity_df['campaign_name'].isin(selected_campaign))]
		
# 		total_connected_calls_df = total_connected_calls_df[(total_connected_calls_df['apr_connected_user_id'].isin(required_agents))]

# 		total_connected_calls_df = total_connected_calls_df.groupby('apr_connected_user_id').agg({'total_connected_calls':'sum'}).reset_index()

# 		# USER RELATED TABLE CONFIGURATIONS
# 		user_df = pd.read_sql_query(user_query, conn)
# 		user_df['full_name'] = user_df[['first_name','last_name']].apply(lambda x:' '.join(x.map(str)), axis=1)
# 		user_df = user_df.drop(['first_name','last_name'], axis=1)
# 		user_df['reporting_to_id'] = user_df['reporting_to_id'].fillna(-1)
# 		new_reporting_df = user_df.copy()

# 		reporting_df = new_reporting_df[['id','username','reporting_to_id']]
# 		reporting_df = reporting_df.rename(columns = {
# 			'id':'reporting_tble_id',
# 			'username':'supervisor_name',
# 			'reporting_to_id':'supervisor_id'
# 		})

# 		# MERGING USER TABLE AND ACTIVITY
# 		user_df_with_sup = pd.merge(user_df,reporting_df,left_on = 'reporting_to_id',right_on = 'reporting_tble_id',how='left')
# 		user_main = user_df_with_sup.drop(['reporting_to_id'],axis=1)
# 		user_agent_activity = pd.merge(agent_activity_df,user_main,right_on='id',left_on='user_id',how='left')
# 		del agent_activity_df
# 		user_agent_activity = user_agent_activity[user_agent_activity['user_id'].isin(required_agents)]

# 		all_time_related_cols = ['break_time','pause_progressive_time','predictive_time',
# 						'progressive_time',
# 						'preview_time',
# 						'predictive_wait_time',
# 						'inbound_time','blended_time','inbound_wait_time',
# 						'blended_wait_time','app_idle_time']



# 		# Converting times to seconds
# 		for time_type in all_time_related_cols:
# 			user_agent_activity[time_type] = user_agent_activity[time_type].apply( lambda x : to_secs(x)  )

# 		all_aggr_time_cols = {val:'sum' for val in all_time_related_cols}
# 		all_aggr_time_cols['campaign_name'] = 'unique'
# 		# all_aggr_time_cols['total_connected_calls'] = 'sum'
# 		user_agent_activity_all_data = user_agent_activity.groupby('user_id').agg(all_aggr_time_cols).reset_index()
# 		user_agent_activity_all_data['campaign_name'] = user_agent_activity_all_data['campaign_name'].apply(
# 													lambda x : ", ".join(campaign_join(x)))
# 		# FOR USER IDLE TIME AND DIALER TIME
# 		# COllecting user based app_idle_time_filter
# 		user_agent_activity_condition = user_agent_activity.where((user_agent_activity['campaign_name'].isin([None,'','None'])) |
# 												(user_agent_activity['event'] == 'DIALER LOGIN'))

# 		user_agent_activity_gb_user = user_agent_activity_condition.groupby(
# 									user_agent_activity_condition['user_id'])['app_idle_time'].sum()
# 		user_agent_activity_gb_user = user_agent_activity_gb_user.to_frame().reset_index()
# 		user_agent_activity_gb_user = user_agent_activity_gb_user.rename(columns={'app_idle_time': 'user_app_idle_time'})

# 		#  Dialler Idle Time

# 		user_agent_activity_cond_dialer = user_agent_activity.where((~user_agent_activity['campaign_name'].isin([None,'','None'])) &
# 												(~user_agent_activity['event'].isin(["DIALER LOGIN","LOGOUT"])))
# 		user_agent_activity_cond_dialer = user_agent_activity_cond_dialer[
# 												user_agent_activity_cond_dialer['user_id'].notna()]

# 		user_agent_activity_gb_userdialler = user_agent_activity_cond_dialer.groupby(
# 									user_agent_activity_cond_dialer['user_id'])['app_idle_time'].sum()
# 		user_agent_activity_gb_userdialler = user_agent_activity_gb_userdialler.to_frame().reset_index()
# 		user_agent_activity_gb_userdialler = user_agent_activity_gb_userdialler.rename(columns={'app_idle_time': 'dialer_app_idle_time'})
		
# 		agent_activity_main = pd.merge(user_agent_activity_all_data,user_agent_activity_gb_user,on='user_id',how='left') 
# 		agent_activity_main_updated = pd.merge(agent_activity_main,user_agent_activity_gb_userdialler,on='user_id',how='left') 

# 		agent_activity_main_withuser = pd.merge(agent_activity_main_updated,user_main,left_on='user_id',right_on='id',how='left')
# 		del user_main
# 		del agent_activity_main_updated
# 		agent_activity_main_withuser = agent_activity_main_withuser.drop(['id'], axis=1)

# 		dialler_event_df = pd.read_sql_query(ring_duration_query, conn)
# 		dialler_event_df = dialler_event_df.rename(columns={
# 			'user_id':'dialler_user_id','campaign_name':'dialler_campaign_name'
# 		})


# 		# CALLDETAILS 
# 		print('----------',calldetail_query)
# 		calldetail_df = pd.read_sql_query(calldetail_query, conn)
# 		print('666666666666666666',calldetail_df)

# 		calldetail_df = pd.merge(calldetail_df, dialler_event_df,how='left', left_on=['user_id','campaign_name'], right_on = ['dialler_user_id','dialler_campaign_name'])
# 		print('77777777777777777',calldetail_df)
# 		calldetail_df['ring_duration'] = calldetail_df['ring_duration'].fillna(calldetail_df['ring_duration_calldetail'])
# 		calldetail_df['bill_sec'] = calldetail_df['bill_sec_dialler'].fillna(calldetail_df['bill_sec'])

# 		calldetails_timecols = ['media_time','ring_duration','hold_time','call_duration','bill_sec','feedback_time',]
# 		for time_type in calldetails_timecols:
# 			calldetail_df[time_type] = calldetail_df[time_type].apply( lambda x : to_secs(x)  )

# 		# calldetails with campaign
# 		if selected_campaign:
# 			calldetail_df = calldetail_df[calldetail_df['campaign_name'].isin(selected_campaign)]    
		
# 		print('----------7.1------------',calldetail_df.columns)

# 		calldetail_df_without_camp = calldetail_df.groupby(['user_id','cd_created_date']).agg({
# 								'total_unique_connected_calls':'sum',
# 								'calldetail_count':'sum','media_time':'sum','hold_time':'sum','ring_duration':'sum','call_duration':'sum','bill_sec':'sum','feedback_time':'sum'
# 							}).reset_index()
# 		print('888888888888888888888',calldetail_df_without_camp)
# 		del calldetail_df
# 		apr_main = pd.merge(agent_activity_main_withuser,calldetail_df_without_camp,on='user_id',how='left')
# 		print('99999999999999999999',apr_main)
# 		del calldetail_df_without_camp,agent_activity_main_withuser

# 		# ALL AVERAGES 
# 		required_agents_ids = None
# 		if download:
# 			set_download_progress_redis(download_report_id, 70, is_refresh=True)
# 		if len(apr_main):
# 			# apr_main['talk_total'] = apr_main['bill_sec'] + apr_main['feedback_time'] + apr_main['ring_duration']
# 			apr_main['talk_total'] = apr_main['bill_sec']
# 			apr_main['customer_talk'] = apr_main['bill_sec'] + apr_main['ring_duration']
# 			apr_main['break_time_avg'] = apr_main['break_time']/apr_main['calldetail_count'] 
# 			apr_main['talk_avg'] = apr_main['talk_total']/apr_main['calldetail_count']
# 			apr_main['feedback_time_avg'] = apr_main['feedback_time']/apr_main['calldetail_count']
# 			apr_main['bill_sec_avg'] = apr_main['customer_talk']/apr_main['calldetail_count']
# 			apr_main['ring_duration_avg'] =apr_main['ring_duration']/apr_main['calldetail_count']
# 			apr_main['predictive_wait_time_avg'] = apr_main['predictive_wait_time']/apr_main['calldetail_count']
			
# 			apr_main['dialer_login_time'] = apr_main['pause_progressive_time']+ apr_main['predictive_wait_time'] + apr_main['preview_time']+ apr_main['inbound_wait_time'] +apr_main['blended_wait_time']+ apr_main['dialer_app_idle_time']+ apr_main['call_duration']+ apr_main['feedback_time']+ apr_main['progressive_time']

# 			apr_main['total_login_time'] = apr_main['dialer_login_time'] + apr_main['user_app_idle_time']+ apr_main['break_time']

# 			required_agents_ids = apr_main['user_id'].tolist()
# 			# First Login Last Logout
# 			agents_tple =  str(required_agents_ids).strip('[]')

# 			user_login_query = f'''select user_id,event,created from callcenter_agentactivity where user_id in ({agents_tple}) and created>'{start_date}' and created < '{end_date}'
# 					and event in ('LOGIN','LOGOUT') order by created asc 
# 				'''
# 			user_login_df = pd.read_sql_query(user_login_query, conn)
# 			# FIRST LOGIN
# 			user_first_login_df = user_login_df.where(user_login_df['event'] == "LOGIN")
# 			user_first_login_df = user_first_login_df[user_first_login_df['event'].notna()]
# 			user_first_login_df_gb = user_first_login_df.groupby('user_id').first().reset_index()
# 			user_first_login_df_gb = user_first_login_df_gb.rename(columns = {'event':'first_login','created':'first_login_time'})
# 			#LAST LOGOUT
# 			user_last_logout_df = user_login_df.where(user_login_df['event'] == "LOGOUT")
# 			user_last_logout_df = user_last_logout_df[user_last_logout_df['event'].notna()]
# 			user_last_logout_df_gb = user_last_logout_df.groupby('user_id').last().reset_index()
# 			user_last_logout_df_gb = user_last_logout_df_gb.rename(columns = {'event':'last_logout','created':'last_logout_time'})

# 			apr_main_with_fin = pd.merge(apr_main,user_first_login_df_gb,on='user_id',how = 'left')
# 			del apr_main
# 			apr_main_with_fin_lout = pd.merge(apr_main_with_fin,user_last_logout_df_gb,on='user_id',how = 'left')
# 			del apr_main_with_fin,user_last_logout_df_gb
# 			apr_main_with_fin_lout = apr_main_with_fin_lout.drop('app_idle_time',axis=1)
# 			apr_main_with_fin_lout = apr_main_with_fin_lout.rename(
# 											columns = {'user_app_idle_time':'app_idle_time',
# 													'dialer_app_idle_time':'dialer_idle_time',
# 													'campaign_name':'campaign',
# 													'calldetail_count':'total_calls'
# 													}
# 											)
# 			apr_main_with_fin_lout[['app_login_time']] = apr_main_with_fin_lout[['dialer_login_time']] 
# 			apr_main_final = apr_main_with_fin_lout[['app_idle_time','app_login_time','bill_sec','bill_sec_avg',
# 							'blended_time','blended_wait_time','break_time','break_time_avg',
# 							'call_duration','campaign','dialer_idle_time','dialer_login_time','feedback_time',
# 							'feedback_time_avg','first_login_time','full_name','hold_time','inbound_time',
# 							'inbound_wait_time','last_logout_time','media_time','pause_progressive_time',
# 							'predictive_time','predictive_wait_time','predictive_wait_time_avg','preview_time',
# 							'progressive_time','ring_duration','ring_duration_avg','talk_total','talk_avg','total_calls'
# 							,'total_login_time','total_unique_connected_calls','username','user_id','supervisor_name']]
# 			del apr_main_with_fin_lout
# 			breaks_activity_df = pd.read_sql_query(breaks_activity_query, conn)
# 			breaks_activity_df['break_type'] = breaks_activity_df['break_type'].replace(r'^\s*$', np.nan, regex=True)
# 			breaks_activity_df[['break_type']] = breaks_activity_df[['break_type']].fillna('None')
# 			breaks_activity_df.drop(breaks_activity_df[breaks_activity_df.break_type == 'None' ].index, inplace=True)
# 			all_breaks_df = breaks_activity_df.pivot_table('break_time', 'user_id','break_type')
# 			all_breaks_df.columns.name = None               #remove categories
# 			all_breaks_df = all_breaks_df.reset_index()
# 			all_breaks_df = all_breaks_df[(all_breaks_df['user_id'].isin(required_agents_ids))]
# 			break_time_cols = list(all_breaks_df.columns)
# 			break_time_cols.remove('user_id')
# 			for time_type in break_time_cols:
# 				all_breaks_df[time_type] = all_breaks_df[time_type].apply( lambda x : to_secs(x)  )
			
# 			for time_type in break_time_cols:
# 				all_breaks_df[time_type] = all_breaks_df[time_type].apply( lambda x : convert_to_hrs(x)   )

# 			final_dataframe  = pd.merge(apr_main_final,all_breaks_df,on='user_id',how='left')
# 			final_dataframe[['total_unique_connected_calls','total_calls']] = final_dataframe[['total_unique_connected_calls','total_calls']].fillna(0)
# 			# final_dataframe = final_dataframe.fillna('00:00:00')

# 			final_dataframe = pd.merge(final_dataframe,total_connected_calls_df,how='left',left_on= 'user_id',right_on='apr_connected_user_id')
		
# 			final_dataframe['first_login_time'] = final_dataframe['first_login_time'].fillna('-')
# 			final_dataframe['last_logout_time'] = final_dataframe['last_logout_time'].fillna('-')
# 			final_dataframe['first_login_time'] = final_dataframe['first_login_time'].apply( lambda x:x.strftime("%d-%m-%Y %H:%M:%S")if x != '-' else None) 
# 			final_dataframe['last_logout_time'] = final_dataframe['last_logout_time'].apply( lambda x:x.strftime("%d-%m-%Y %H:%M:%S")if x != '-' else None) 

# 			# final_dataframe = final_dataframe.fillna(pd.Timedelta(seconds=0))
# 			# final_dataframe = final_dataframe.replace('NaT','00:00:00')
# 			final_timecols = [
# 				'break_time','pause_progressive_time','predictive_time','progressive_time','preview_time',
# 				'predictive_wait_time','inbound_time','blended_time','inbound_wait_time','blended_wait_time',
# 				'app_idle_time','dialer_idle_time','media_time','ring_duration','hold_time','call_duration',
# 				'bill_sec','feedback_time','talk_total','break_time_avg','talk_avg','feedback_time_avg',
# 				'bill_sec_avg','ring_duration_avg','predictive_wait_time_avg','dialer_login_time','total_login_time','app_login_time'
				
# 			] #'customer_talk', ,'customer_talk',,'customer_talk'

# 			final_dataframe[['break_time','pause_progressive_time','predictive_time','progressive_time','preview_time',
# 				'predictive_wait_time','inbound_time','blended_time','inbound_wait_time','blended_wait_time',
# 				'app_idle_time','dialer_idle_time','media_time','ring_duration','hold_time','call_duration',
# 				'bill_sec','feedback_time','talk_total','break_time_avg','talk_avg','feedback_time_avg',
# 				'bill_sec_avg','ring_duration_avg','predictive_wait_time_avg','dialer_login_time','total_login_time']] = final_dataframe[['break_time','pause_progressive_time','predictive_time','progressive_time','preview_time',
# 				'predictive_wait_time','inbound_time','blended_time','inbound_wait_time','blended_wait_time',
# 				'app_idle_time','dialer_idle_time','media_time','ring_duration','hold_time','call_duration',
# 				'bill_sec','feedback_time','talk_total','break_time_avg','talk_avg','feedback_time_avg',
# 				'bill_sec_avg','ring_duration_avg','predictive_wait_time_avg','dialer_login_time','total_login_time']].fillna('00:00:00')
# 			final_dataframe['total_connected_calls']=final_dataframe['total_connected_calls'].fillna('0')
# 			final_dataframe[['total_unique_connected_calls','total_calls','total_connected_calls']] = final_dataframe[['total_unique_connected_calls','total_calls','total_connected_calls']].astype(int)
# 			# final_dataframe[all_col] = final_dataframe[all_col].fillna('00:00:00')
# 			for time_type in final_timecols:
# 				final_dataframe[time_type] = final_dataframe[time_type].apply( lambda x : convert_to_hrs(x))
# 			final_dataframe = final_dataframe.drop(['user_id'],axis=1)
# 			final_dataframe = final_dataframe.rename(columns = {
# 				'talk_total':'talk'
# 			})
# 			final_dataframe = final_dataframe.reindex(columns=['username','full_name','supervisor_name','campaign']+all_col)
# 			for brk in pause_breaks:
# 				final_dataframe[brk] = final_dataframe[brk].fillna('00:00:00')
# 			final_dataframe = final_dataframe.fillna("")
# 			if download:
# 				set_download_progress_redis(download_report_id, 90, is_refresh=True)
# 				return final_dataframe
# 			cols = list(final_dataframe.columns)
# 			call_result_old = [dict(zip(cols, i)) for i in final_dataframe.values]
# 			call_result = call_result_old[::-1]
# 		if download:
# 			return pd.DataFrame(columns=['username','fullname','supervisor']+all_col)
# 		return call_result,users
# 	except Exception as e:
# 		print("ERROR in agent_perorm",e)
# 		exc_type, exc_obj, exc_tb = sys.exc_info()
# 		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
# 		print(exc_type, fname, exc_tb.tb_lineno)

def agent_performance_report_calculations(filters, user, col_list, download_report_id , withcols=False):
	"""
	this is the function for download agent performance  reports
	"""	
	try:
		from datetime import date

		print('in----------agent_performance_report_calculations')
		query = {}
		csv_file = []
		count=0
		logged_in_user = User.objects.get(id=user)
		all_users = filters.get("all_users",[])
		selected_campaign = filters.get("selected_campaign", [])
		selected_campaigngroup = filters.get("selected_campaigngroup", [])
		selected_user = filters.get("selected_user", [])
		start_date = date.today().strftime('%Y-%m-%d %H:%M')
		end_date = date.today().strftime('%Y-%m-%d %H:%M')
		download_type = filters.get('download_type',"")
		start_date = datetime.strptime(start_date,"%Y-%m-%d %H:%M").isoformat()
		end_date = datetime.strptime(end_date,"%Y-%m-%d %H:%M").isoformat()
		if selected_user:
			queryset = User.objects.filter(id__in=selected_user)
		else:
			queryset = User.objects.filter(id__in=all_users)
		queryset = queryset.order_by("username")
		# start_end_date_filter = Q(created__gte=start_date)&Q(created__lte=end_date)
		app_idle_time_filter = Q(campaign_name='')|Q(event='DIALER LOGIN')
		dialler_idle_time_filter = ~Q(campaign_name="")&~Q(event__in=["DIALER LOGIN","LOGOUT"])
		default_time = timedelta(seconds=0)
		if "" in col_list:
			col_list.remove("")
		
		if withcols==True:
			col_list.append('date')
			csv_file.append(col_list)

		print('------today download start date end date----',start_date,end_date)
		date_range = pd.date_range(start_date,end_date)
		for date, user in itertools.product(date_range, queryset):
			next_date=date.date()+timedelta(days=1)
			user = User.objects.filter(id=user.id).prefetch_related(Prefetch('calldetail_set',queryset=CallDetail.objects.filter(created__date__gte=date.date()).filter(created__date__lte=next_date).filter(user=user)),Prefetch('agentactivity_set',queryset=AgentActivity.objects.filter(created__date__gte=date.date()).filter(created__date__lte=next_date).filter(user=user))).first()

			if selected_campaign:
				calldetail = user.calldetail_set.filter(campaign_name__in=selected_campaign)
				agentactivity = user.agentactivity_set.filter(Q(campaign_name__in=selected_campaign)|Q(
					event="DIALER LOGIN")|Q(campaign_name=''))
			else:
				calldetail = user.calldetail_set
				agentactivity = user.agentactivity_set
			calldetail_cal = calldetail.aggregate(media_time=Cast(Coalesce(Sum('media_time'),default_time),TimeField()),
				ring=Cast(Coalesce(Sum('ring_duration'),default_time),TimeField()),
				hold_time=Cast(Coalesce(Sum('hold_time'),default_time),TimeField()),
				call_duration=Cast(Coalesce(Sum('call_duration'),default_time),TimeField()),
				customer=Cast(Coalesce(Sum('bill_sec'),default_time),TimeField()),
				wrapup_time=Cast(Coalesce(Sum('feedback_time'),default_time),TimeField()),
				)
			activity_cal = agentactivity.aggregate(pause=Cast(Coalesce(Sum('break_time'),default_time),TimeField()),
				pause_progressive_time=Cast(Coalesce(Sum('pause_progressive_time'),default_time),TimeField()),
				predictive_time=Cast(Coalesce(Sum('predictive_time'),default_time),TimeField()),
				progressive_time=Cast(Coalesce(Sum('progressive_time'),default_time),TimeField()),
				preview_time=Cast(Coalesce(Sum('preview_time'),default_time),TimeField()),
				predictive_wait_time=Cast(Coalesce(Sum('predictive_wait_time'),default_time),TimeField()),
				inbound_time=Cast(Coalesce(Sum('inbound_time'),default_time),TimeField()),
				blended_time=Cast(Coalesce(Sum('blended_time'),default_time),TimeField()),
				inbound_wait_time=Cast(Coalesce(Sum('inbound_wait_time'),default_time),TimeField()),
				blended_wait_time=Cast(Coalesce(Sum('blended_wait_time'),default_time),TimeField()),
				app_idle_time=Cast(Coalesce(Sum('idle_time',filter=app_idle_time_filter),default_time),TimeField()),
				dialer_idle_time=Cast(Coalesce(Sum('idle_time',filter=dialler_idle_time_filter),default_time),TimeField())
				)
			break_time_cal= {}
			total_calls = calldetail.count()
			break_name = list(PauseBreak.objects.values_list('name',flat=True))

			all_fields = []
			call_details = CallDetail.objects.filter(Q(campaign_name__in=selected_campaign, user=user)| Q(user=user))
			user_call_detail = calldetail.exclude(cdrfeedback=None)

			all_fields =  set(Campaign.objects.filter(status='Active').exclude(disposition=None).values_list("disposition__name", flat=True))
			wfh_dispo_list = list(Campaign.objects.filter(wfh=True, status='Active').values_list('wfh_dispo',flat=True))
			wfh_dispo = set([ d for m in wfh_dispo_list for d in m.values()])
			all_fields.update(wfh_dispo)

			for dispo_name in all_fields:
				calldetail_cal[dispo_name] = user_call_detail.filter(cdrfeedback__primary_dispo=dispo_name).count()
			
			calldetail_cal["Total Dispo Count"] = user_call_detail.count()
			calldetail_cal["AutoFeedback"] = user_call_detail.filter(cdrfeedback__primary_dispo="AutoFeedback").count()
			calldetail_cal["AbandonedCall"] =  call_details.filter(user_id=user,dialed_status="Abandonedcall",cdrfeedback__primary_dispo='').count()
			calldetail_cal["NC"] = call_details.filter(user_id=user,dialed_status="NC",cdrfeedback__primary_dispo='').count()
			calldetail_cal["Invalid Number"] = call_details.filter(user_id=user,dialed_status="Invalid Number",cdrfeedback__primary_dispo='').count()
			calldetail_cal["RedialCount"] = user_call_detail.filter(cdrfeedback__primary_dispo="Redialed").count()
			calldetail_cal["AlternateDial"] = user_call_detail.filter(cdrfeedback__primary_dispo="AlternateDial").count()
			calldetail_cal["PrimaryDial"] = user_call_detail.filter(cdrfeedback__primary_dispo="PrimaryDial").count()
			calldetail_cal["NF(No Feedback)"] = user_call_detail.filter(cdrfeedback__primary_dispo="NF(No Feedback)").count()
			for break_cal in break_name:
				break_time_cal[break_cal] = agentactivity.filter(break_type=break_cal).aggregate(break_time__sum=Cast(Coalesce(Sum('break_time'),default_time),TimeField())).get('break_time__sum')
			pp_time = convert_into_timedelta(activity_cal['pause_progressive_time']).total_seconds()
			pw_time = convert_into_timedelta(activity_cal['predictive_wait_time']).total_seconds()
			preview_time = convert_into_timedelta(activity_cal['preview_time']).total_seconds()
			break_time = convert_into_timedelta(activity_cal['pause']).total_seconds()
			talk_call = convert_into_timedelta(calldetail_cal['customer']).total_seconds()
			talk_time = convert_into_timedelta(calldetail_cal['customer']).total_seconds()
			ring =convert_into_timedelta(calldetail_cal['ring']).total_seconds()
			feedback_time =convert_into_timedelta(calldetail_cal['wrapup_time']).total_seconds()
			talk_total = int(talk_call) + int(feedback_time) + int(ring)
			if talk_total > feedback_time :
				customer_talk = int(talk_total) - int(feedback_time)
			else:
				customer_talk = int(feedback_time) - int(talk_total)
			calldetail_cal['talk'] = convert_timedelta_hrs(timedelta(seconds=talk_total))
			calldetail_cal['talk_time'] = convert_timedelta_hrs(timedelta(seconds=talk_time))
			calldetail_cal['customer'] = convert_timedelta_hrs(timedelta(seconds=customer_talk))
			calldetail_cal['wait_time'] = convert_timedelta_hrs(timedelta(seconds=pw_time))
			if total_calls:
				pause_avg = ((convert_into_timedelta(activity_cal['pause']).total_seconds())/total_calls)
				talk_avg = ((int(talk_call)+int(feedback_time)+int(ring))/total_calls)
				wrapup_avg = ((convert_into_timedelta(calldetail_cal['wrapup_time']).total_seconds())/total_calls)
				customer_avg_talk = ((int(talk_call)+int(ring))/total_calls)
				wait_time_avg = (int(pw_time)/total_calls)
				# customer_avg = ((convert_into_timedelta(calldetail_cal['customer']).total_seconds())/total_calls)
				calldetail_cal['customer_avg'] = convert_timedelta_hrs(timedelta(seconds=customer_avg_talk))
				wait_avg = ((convert_into_timedelta(calldetail_cal['ring']).total_seconds())/total_calls)
				calldetail_cal['pause_avg'] =  convert_timedelta_hrs(timedelta(seconds=pause_avg))
				calldetail_cal['talk_avg'] = convert_timedelta_hrs(timedelta(seconds=talk_avg)) 
				calldetail_cal['wrapup_avg'] =  convert_timedelta_hrs(timedelta(seconds=wrapup_avg)) 
				calldetail_cal['ring_avg'] = convert_timedelta_hrs(timedelta(seconds=wait_avg)) 
				activity_cal['wait_time_avg'] = convert_timedelta_hrs(timedelta(seconds=wait_time_avg)) 
			else:
				default_time_delta_sec = timedelta(hours=0,minutes=0,seconds=0).total_seconds()
				calldetail_cal['pause_avg'] = time.strftime("%H:%M:%S", time.gmtime(default_time_delta_sec))
				calldetail_cal['talk_avg'] = time.strftime("%H:%M:%S", time.gmtime(default_time_delta_sec))
				calldetail_cal['wrapup_avg'] = time.strftime("%H:%M:%S", time.gmtime(default_time_delta_sec))
				calldetail_cal['customer_avg'] = time.strftime("%H:%M:%S", time.gmtime(default_time_delta_sec))
				calldetail_cal['ring_avg'] = time.strftime("%H:%M:%S", time.gmtime(default_time_delta_sec))
				activity_cal['wait_time_avg'] = time.strftime("%H:%M:%S", time.gmtime(default_time_delta_sec))
			iw_time = convert_into_timedelta(activity_cal['inbound_wait_time']).total_seconds()
			bw_time = convert_into_timedelta(activity_cal['blended_wait_time']).total_seconds()
			ai_time = convert_into_timedelta(activity_cal['app_idle_time']).total_seconds()
			di_time = convert_into_timedelta(activity_cal['dialer_idle_time']).total_seconds()
			call_duration = convert_into_timedelta(calldetail_cal['call_duration']).total_seconds()
			feedback_time = convert_into_timedelta(calldetail_cal['wrapup_time']).total_seconds()
			p_time = convert_into_timedelta(activity_cal['progressive_time']).total_seconds()
			dialer_login_time = int(pp_time)+int(pw_time)+int(preview_time)+int(iw_time)+int(bw_time)+int(
				di_time)+int(call_duration)+int(feedback_time)+int(p_time)
			total_login_time = int(dialer_login_time)+int(ai_time)+int(break_time)
			calldetail_cal['app_login_time'] = activity_cal['app_idle_time']
			calldetail_cal['dialer_login_time'] = time.strftime("%H:%M:%S", time.gmtime(dialer_login_time))
			calldetail_cal['total_login_time'] = time.strftime("%H:%M:%S", time.gmtime(total_login_time))
			calldetail_cal = {**calldetail_cal, **activity_cal ,**break_time_cal}
			calldetail_cal['total_calls'] = calldetail.count()
			calldetail_cal['id'] = user.username
			calldetail_cal['username'] = user.first_name + " " + user.last_name
			last_logout_time = ''
			first_login_time = ''
			logout_cond_one=Q(event__in=['LOGOUT','Old Login Session clear','Session Expired (Poor Connectivity)'])
			logout_cond_two=Q(event__icontains='Force')
			if agentactivity.filter(logout_cond_one|logout_cond_two).last():
				last_logout_time = agentactivity.filter(logout_cond_one|logout_cond_two).order_by('created').last().created.strftime("%Y-%m-%d %H:%M:%S")
			if agentactivity.filter(event='LOGIN').first():
				first_login_time = agentactivity.filter(event='LOGIN').order_by('created').first().created.strftime("%Y-%m-%d %H:%M:%S")
			calldetail_cal['last_logout_time'] = last_logout_time
			calldetail_cal['first_login_time'] = first_login_time
			calldetail_cal['total_connected_calls'] = calldetail.filter(dialed_status='Connected').order_by('customer_cid').count()
			calldetail_cal['total_unique_connected_calls'] = calldetail.filter(dialed_status='Connected').distinct('customer_cid').order_by('customer_cid').count()
			# calldetail_cal['total_unique_connected_calls'] = calldetail.exclude(uniqueid=None).distinct('uniqueid').order_by('uniqueid').count()
			calldetail_cal['supervisor_name'] = '' 
			if user.reporting_to:
				calldetail_cal['supervisor_name'] = user.reporting_to.username
			calldetail_cal['date'] = date.date()
			if selected_campaign:
				calldetail_cal['campaign'] = ','.join(selected_campaign)
			else:
				calldetail_cal['campaign'] = ",".join(list(set(list(user.agentactivity_set.exclude(campaign_name=None).exclude(campaign_name='').values_list("campaign_name",flat=True)))))
			row = []
			for field in col_list:
				row.append(calldetail_cal.get(field,""))
			csv_file.append(row)
		return csv_file
		# 	count += 1
		# 	percentage = ((count)/(len(date_range)*queryset.count()))*100
		# 	if download_report_id!=None:
		# 		set_download_progress_redis(download_report_id, round(percentage,2))
		# ####### To save file ###########
		# if download_type == 'xls':
		# 	save_file(csv_file, download_report_id, 'agent_performance', logged_in_user, 'xls')
		# else:
		# 	save_file(csv_file, download_report_id, 'agent_performance', logged_in_user, 'csv')
	except Exception as e:
		if download_report_id != None:
			set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
		print('Error in agent_performance_report_calculations', e)
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print(exc_type, fname, exc_tb.tb_lineno)

def apr_download(filters, user, col_list, download_report_id):
	try:
		csv_file=agent_performance_report_calculations(filters, user, col_list, download_report_id,True)
		print('------apr_download-----------',csv_file)

		percentage = 70
		if download_report_id!=None:
			set_download_progress_redis(download_report_id, round(percentage,2))
		####### To save file ###########
		if download_type == 'xls':
			save_file(csv_file, download_report_id, 'agent_performance', logged_in_user, 'xls')
		else:
			save_file(csv_file, download_report_id, 'agent_performance', logged_in_user, 'csv')
	except Exception as e:
		if download_report_id != None:
			set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
		print('Error in download agent performance report', e)

def download_agent_perforance_report(filters, user, col_list, download_report_id):
	"""
	this is the function for download agent performance reports
	"""	
	try:
		start_date = filters.get("start_date", "")
		end_date = filters.get("end_date", "")
		download_type = filters.get('download_type',"")
		start_date = start_date[:10]
		end_date = end_date[:10]

		print(start_date,'----',end_date,'----',date.today())

		if start_date==date.today() and end_date==date.today():
			# only current day data will be fetched with runtime calculations 
			apr_download(filters, user, col_list, download_report_id,True)
			
		else:
			start_date = datetime.strptime(start_date, '%Y-%m-%d')
			
			end_date = datetime.strptime(end_date, '%Y-%m-%d')
			selected_campaign = filters.get("selected_campaign", [])
			selected_campaigngroup = filters.get("selected_campaigngroup", [])
			download_type = "csv"
			selected_user = filters.get('selected_user',"")

			print('selected user---',selected_user)

			if "" in col_list:
				col_list.remove("")
			col_list.append('date')
			csv_file=[]
			csv_file.append(col_list)

			aprdata=AgentProductivityReport.objects.filter(date__gte=start_date).filter(date__lte=end_date)
			if selected_campaigngroup:
				grp_list = list(Campaign.objects.filter(campaign_group__name__in =selected_campaigngroup).values_list('name',flat=True))
				for camp_grp in grp_list:
					selected_campaign += [i.strip() for i in camp_grp.split(',')]

			if selected_campaign:
				aprdata=aprdata.filter(campaign__in=selected_campaign)
			if selected_user:
				aprdata=aprdata.filter(user_id__in=selected_user)
			apr_list = list(aprdata)
			
			for data in apr_list:
				row = []
				for field in col_list:
					if field=='NF(No Feedback)':
						field='nf'
					elif field=='id':
						field='username'
					elif field=='username':
						field='fullname'
					else:
						field= field.lower().replace(" ","_")
					row.append(getattr(data, field, ''))			
				csv_file.append(row)
			print('old data fetched---moving on to current date')
			# for multiple days , till -1 day data will be fetched from report table and present day data on runtime calculations
			if end_date== datetime.strptime(date.today().strftime('%Y-%m-%d'), '%Y-%m-%d') :
				today_csv=agent_performance_report_calculations(filters, user, col_list, download_report_id)
				csv_file.extend(today_csv)
			print('all data fetched')
			# count += 1
			# percentage = ((count)/len(campaign_list))*100
			percentage=90
			if download_report_id != None:
				set_download_progress_redis(download_report_id, round(percentage,2))
			####### To save file ###########
			if download_type == 'xls':
				save_file(csv_filef, download_report_id, 'agent_performance_report', user, 'xls')
			else:
				save_file(csv_file, download_report_id, 'agent_performance_report', user, 'csv')
		
	except Exception as e:
		# if download_report_id != None:
		# 	set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print(exc_type, fname, exc_tb.tb_lineno)
		print('Error in download agent AgentProductivityReport report----', e)

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
			next_date=date.date()+timedelta(days=1)
			login_duration = default_time
			login_time = logout_time = ''
			management_log_dict = {}
			user = User.objects.filter(id=user.id).prefetch_related(Prefetch('adminlogentry_set',queryset=AdminLogEntry.objects.filter(created__date__gte=date.date()).filter(created__date__lte=next_date))).first()
			management_log = user.adminlogentry_set
			management_log_dict = management_log.aggregate(login_duration=Cast(Coalesce(Sum('login_duration'),default_time),TimeField()),
				)
			management_log_dict['username'] = user.username
			login = management_log.filter(created__date__gte=date.date()).filter(created__date__lte=next_date).filter(event_type='LOGIN')
			logout = management_log.filter(created__date__gte=date.date()).filter(created__date__lte=next_date).filter(event_type='LOGOUT')
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
			next_date=date.date()+timedelta(days=1)
			performance_dict = {}
			performance_dict["User"] = user.username
			performance_dict["Full Name"] = user.first_name+" "+user.last_name
			if user.reporting_to:
				performance_dict["Supervisor Name"] = user.reporting_to.username
			campaign = Campaign.objects.filter(Q(users=user)|Q(
				group__in=user.group.all().filter(status="Active"))).filter(
				status="Active").values_list("name", flat=True)
			ucampaign = []
			call_details = CallDetail.objects.filter(created__date__gte=date.date()).filter(created__date__lte=next_date).filter(Q(campaign_name__in=all_campaigns, user=user)| Q(user=user))
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
			else: 
				query += col_name+" "
			if index < len(col_list) and query[-2:] != ", ":
					query += ", "
		query += "from callcenter_agentactivity left join callcenter_user usr on usr.id = callcenter_agentactivity.user_id"+ where 
		download_folder = settings.MEDIA_ROOT+"/download/"+datetime.now().strftime("%m.%d.%Y")+"/"+str(user.id)+"/"
		if not os.path.exists(download_folder):
			os.makedirs(download_folder)
		if download_report_id:
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
		if download_report_id:
			download_report = DownloadReports.objects.get(id=download_report_id)
			download_report.downloaded_file.save(os.path.basename(f.name), File(f), save=True)
			download_report.is_start = False
			download_report.save()
		f.close()
		if download_report_id != None:
			set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
			os.remove(file_path)
		else:
			sending_reports_through_mail(user,'agent_activity')	
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
		if download_report_id:
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
		if download_report_id:
			download_report = DownloadReports.objects.get(id=download_report_id)
			download_report.downloaded_file.save(os.path.basename(f.name), File(f), save=True)
			download_report.is_start = False
			download_report.save()
		f.close()
		if download_report_id:
			os.remove(file_path)
			set_download_progress_redis(download_report_id, 100.0, is_refresh=True)	
		else:
			sending_reports_through_mail(user,'pending_callback')
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
		if download_report_id:
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
		if download_report_id:
			download_report = DownloadReports.objects.get(id=download_report_id)
			download_report.downloaded_file.save(os.path.basename(f.name), File(f), save=True)
			download_report.is_start = False
			download_report.save()
		f.close()
		if download_report_id:
			os.remove(file_path)
			set_download_progress_redis(download_report_id, 100.0, is_refresh=True)
		else:
			sending_reports_through_mail(user,'abandonnedcall')
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

def download_pendingcontacts_report(filters, user, col_list, download_report_id):
	try:
		filter_by_phonebook = filters.get("phonebook", "")
		logged_in_user = User.objects.get(id=user)
		filter_by_campaign = filters.get("campaign", "")
		numeric = filters.get('numeric','')
		filter_by_campaign = list(Campaign.objects.filter(id__in=filter_by_campaign).values_list("name", flat=True))
		queryset = Contact.objects.filter(Q(campaign__in=filter_by_campaign), Q(user=None)| Q(user=''),Q(created_date__date__lt=datetime.today()),Q(status="NotDialed"))
		campaign_column = True
		if filter_by_phonebook:
			queryset = queryset.filter(phonebook__id__in=filter_by_phonebook)
		if numeric:
			queryset = queryset.filter(numeric=numeric)
		col_list = ['id','user','numeric','uniqueid'] + col_list
		csv_file = []
		if 'created_date' in col_list:
			col_list.remove('created_date')
			col_list.append('flexydial_insert_date')
		if "" in col_list:
			col_list.remove("")
		csv_file.append(col_list)
		count = 0
		for c_info in queryset.iterator():
			row = []
			data = ContactListSerializer(c_info).data
			for field in col_list:
				field = field.split('.')
				if "flexydial_insert_date" in field:
					row.append(data.get('created_date',''))
				else:
					if len(field) > 1:
						if field[1] in data['contact_info']:
							if field[2] in data['contact_info'][field[1]]: 
								row.append(data['contact_info'][field[1]][field[2]])
							else:
								row.append('')
						else:
							row.append('')
					else:
						row.append(data.get(field[0],''))
			csv_file.append(row)
			count +=1
			percentage = ((count)/queryset.count())*100
			set_download_progress_redis(download_report_id, round(percentage,2))
		save_file(csv_file, download_report_id, 'call-info', logged_in_user)
	except Exception as e:
		print("Exception occures from Contact Info Download",e)
		set_download_progress_redis(download_report_id, 100)
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print(exc_type, fname, exc_tb.tb_lineno)

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
				if 'status' in col_list:
					row.append('Active' if user.is_active else "Inactive")
				if 'date' in col_list:
					row.append(user.updated.strftime("%Y-%m-%d %H:%M:%S"))
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
	if service == 'all':
		services_list = []
		for service in settings.SERVICES_LIST:
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
			service_status['name'] = service
			for line in output.splitlines():
				service_search = re.search(service_regx, line)
				status_search = re.search(status_regx, line)
				inactive_search = re.search(inactive_regx, line)

				if status_search:
					service_status['status'] = status_search.group(1).strip()
					service_status['since'] = datetime.strftime(dateutil.parser.parse(
						status_search.group(3).strip()).date(),'%d-%m-%Y')
					service_status['uptime'] = status_search.group(4).strip()
				elif inactive_search:
					service_status['status'] = 'inactive'
			services_list.append(service_status)
		return services_list
	else:
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


def download_phonebookinfo_report(filters, user, col_list, download_report_id):
	""" download phonebook contacts  report """
	print('download_phonebookinfo_report functin called')
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
			if pass_manage_inst and datetime.now().date() >= user.password_date+timedelta(pass_manage_inst.password_expire):
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
				if  pass_manage_inst and pass_manage_inst.password_expire:
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

def get_agent_status(extension,full_key = False):
	if full_key:
		keys_list = ['username', 'name', 'login_status', 'campaign', 'dialer_login_status', 'dialer_login_time', 'status', 'state', 'event_time', 'call_type', 'dial_number', 'call_timestamp', 'extension', 'dialerSession_uuid', 'screen', 'login_time', 'call_count']
		agent_keys = []
		agent_dict = pickle.loads(settings.R_SERVER.get(extension) or pickle.dumps({}))
		extension1 = list(extension.split("_"))
		if extension1 and len(extension1)==2 and extension1[1] in agent_dict:
			agent_keys = agent_dict[extension1[1]].keys()
		if len(extension1)==2 and not set(agent_keys).issuperset(set(keys_list)):
			agent_dict[extension1[1]] = default_agent_status(extension1[1],agent_dict)
		return agent_dict
	return pickle.loads(settings.R_SERVER.get("flexydial_"+extension) or pickle.dumps({}))

def set_agent_status(extension,agent_dict,delete=False):
	stat_keys = ['onbreak','login_count','dialer_count','progressive','inbound','predictive','preview','manual']
	if delete:
		settings.R_SERVER.delete("flexydial_"+extension)
		# print("RedisDelete ",extension)
		for stat in stat_keys:
			stat_dict = get_statKey(stat)
			remove_redis_stat_val(stat_dict,stat,extension)
		return True
	updated_agent_dict = get_agent_status(extension)
	# print("RedisAvailable ",extension,updated_agent_dict)
	if extension not in updated_agent_dict:
		updated_agent_dict[extension] = {}
	# print("RedisNeedInsert ",agent_dict)
	agent_dict = default_agent_status(extension,agent_dict)
	if extension in agent_dict:
		updated_agent_dict[extension].update(agent_dict[extension])
	else:
		updated_agent_dict[extension].update(agent_dict)
	# print("RedisUpdatedDict ",updated_agent_dict)
	status = settings.R_SERVER.set("flexydial_"+extension, pickle.dumps(updated_agent_dict),ex=settings.REDIS_KEY_EXPIRE_IN_SEC)
	if status!=True:
		print("Log::RedisError:: ",status,updated_agent_dict)
	update_stats_data(updated_agent_dict,extension)
	return status

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
def update_redis_stat_key(stat_dict, key,extension):
	if extension not in stat_dict:
		stat_dict.append(extension)
		update_statKey(key,stat_dict)
def remove_redis_stat_val(stat_dict,key,extension):
	if extension in stat_dict:
		stat_dict.remove(extension)
		update_statKey(key,stat_dict)
def get_statKey(key):
	return pickle.loads(settings.R_SERVER.get(key) or pickle.dumps([]))
def update_statKey(key,val):
	return settings.R_SERVER.set(key, pickle.dumps(val),ex=settings.REDIS_KEY_EXPIRE_IN_SEC)

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

def get_all_keys_data_df(team_extensions=''):
	keysdata = settings.R_SERVER.scan_iter("flexydial_*")
	total_agents_df = pd.DataFrame()
	if team_extensions:
		team_extensions =[bytes("flexydial_"+s, encoding='utf-8')  for s in team_extensions]
		for k in keysdata:
			if k in team_extensions:
				AGENTS = get_agent_status(k.decode('utf-8'),True)
				total_agents_df = pd.concat([total_agents_df,pd.DataFrame.from_dict(AGENTS,orient='index')], ignore_index = True)
	else:
		for k in keysdata:
			AGENTS = get_agent_status(k.decode('utf-8'),True)
			total_agents_df = pd.concat([total_agents_df,pd.DataFrame.from_dict(AGENTS,orient='index')], ignore_index = True)
	return total_agents_df

def get_all_keys_data(team_extensions=""):
	keysdata = settings.R_SERVER.scan_iter("flexydial_*")
	agent_dict = {}
	if team_extensions:
		team_extensions =[bytes("flexydial_"+s, encoding='utf-8')  for s in team_extensions]
		for k in keysdata:
			if k in team_extensions:
				AGENTS = get_agent_status(k.decode('utf-8'),True)
				agent_dict.update(AGENTS)	
	else:
		for k in keysdata:
			AGENTS = get_agent_status(k.decode('utf-8'),True)
			agent_dict.update(AGENTS)
	return agent_dict

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