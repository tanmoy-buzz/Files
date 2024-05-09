import json
import xlwt
import re
import os
import sys
from django.apps import apps
import datetime
from datetime import datetime
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponseRedirect,HttpResponse, StreamingHttpResponse, JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.permissions import AllowAny

from callcenter.models import (Campaign,User,DNC, Notification, SMSLog, AdminLogEntry,PhonebookBucketCampaign, CSS, DiaTrunkGroup, DialTrunk, PauseBreak, PasswordManagement,
	Disposition, Group, User, Switch,PasswordResetLogs,PasswordChangeLogs)

import socket, errno, xmlrpc.client
import csv
import pandas as pd
import pickle
from datetime import date
from crm.models import TempContactInfo, Contact, TrashContact, CampaignInfo, AlternateContact, Phonebook,KycDocuments
from .constants import (CRM_FIELDS, USER_FIELDS ,DNC_FIELDS, PAGINATE_BY_LIST, ACTION_TYPE, ALTERNATE_FIELDS,HOLIDAYS_FIELDS,TTS_VOICES)
CAMPAIGNS={}
import base64
from django.core.mail import EmailMessage,EmailMultiAlternatives, get_connection, BadHeaderError
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.contrib.auth.views import PasswordResetCompleteView, PasswordResetConfirmView, INTERNAL_RESET_SESSION_TOKEN
import requests
from django.contrib.auth.forms import SetPasswordForm
import urllib

def freeswicth_server(server_ip):
	"""
	this function is for making connection to the freeswitch 
	by using the campaign Ip_address
	"""
	SERVER = xmlrpc.client.ServerProxy("http://%s:%s@%s:%s" % (settings.RPC_USERNAME,
			 settings.RPC_PASSWORD,server_ip,settings.RPC_PORT))
	return SERVER 

def check_permission(user, permissions):
	"""
	This function is used to check user permissions
	"""
	permission_dict = {'can_read':False, 'can_create':False,
	'can_update':False, 'can_delete':False}
	if user.is_superuser == False:
		if permissions != '':
			if 'R' in permissions:
				permission_dict['can_read'] = True
			if 'C' in permissions:
				permission_dict['can_create'] = True
			if 'U' in permissions:
				permission_dict['can_update'] = True
			if 'D' in permissions:
				permission_dict['can_delete'] = True
		return permission_dict
	else:
		permission_dict = {'can_read':True, 'can_create':True,
		'can_update':True, 'can_delete':True}
		return permission_dict
	return permission_dict


def get_login_campaign():
	""" 
	get the login campaings  from redis
	"""
	AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") )
	total_agents_df = pd.DataFrame.from_dict(AGENTS,orient='index')
	campaign_pd = total_agents_df[(total_agents_df['campaign']!="")]    
	agent_logged_in_campaign=campaign_pd['campaign'].tolist()
	return agent_logged_in_campaign

def get_login_agent():
	""" 
	get the login agents from redis
	"""
	AGENTS = pickle.loads(settings.R_SERVER.get("agent_status") )
	total_agents_df = pd.DataFrame.from_dict(AGENTS,orient='index')
	campaign_pd = total_agents_df[(total_agents_df['username']!="")]    
	agent_logged_in=campaign_pd['username'].tolist()
	return agent_logged_in

class CheckCanEditView(APIView):
	"""
	this view is written to check we can edit particular campaign or not
	"""
	def post(self, request):
		app_label = request.POST.get("app_name", "")
		model_name = request.POST.get("model_name", "")
		selected_entries = []
		selected_entries = request.POST.getlist('selected_entry')
		perform_op = request.POST.get("perform_operation", "")
		model = apps.get_model(app_label=app_label, model_name=model_name)
		go_to_camapgin_section = False

		if selected_entries:
			selected_entries = json.loads(selected_entries[0])
			agent_logged_in_campaign = get_login_campaign()
			if model_name == "PauseBreak":
				break_entries = list(Campaign.objects.filter(name__in=agent_logged_in_campaign).values_list("breaks__id",flat=True))
				pause_breaks = list(PauseBreak.objects.filter(id__in=selected_entries).exclude(id__in=break_entries).values_list("id",flat=True))
				return JsonResponse({"selected_entries":pause_breaks})                  
			if model_name == "Campaign":
				namelist=list(Campaign.objects.filter(id__in=selected_entries).values_list("name",flat=True))
				campaign_list = list(set(namelist) - set(agent_logged_in_campaign))
				selected_entries = list(Campaign.objects.filter(name__in=campaign_list).values_list("id",flat=True))
				return JsonResponse({"selected_entries":selected_entries})
			if model_name == "Disposition":
				dispo_entries = list(Campaign.objects.filter(name__in=agent_logged_in_campaign).values_list("disposition__id",flat=True))
				dispo = list(Disposition.objects.filter(id__in=selected_entries).exclude(id__in=dispo_entries).values_list("id",flat=True))
				return JsonResponse({"selected_entries":dispo})     
			if model_name == "DialTrunk":           
				trunk_entries = list(Campaign.objects.filter(name__in=agent_logged_in_campaign).values_list("trunk__id",flat=True))
				trunk_list = list(DialTrunk.objects.filter(id__in=selected_entries).exclude(id__in=trunk_entries).values_list("id",flat=True))
				return JsonResponse({"selected_entries":trunk_list})        
			if model_name == "DiaTrunkGroup":           
				trunk_group_entries = list(Campaign.objects.filter(name__in=agent_logged_in_campaign).values_list("trunk_group__id",flat=True))
				trunk_list = list(DiaTrunkGroup.objects.filter(id__in=selected_entries).exclude(id__in=trunk_group_entries).values_list("id",flat=True))
				return JsonResponse({"selected_entries":trunk_list})
			if model_name == "Switch":          
				switch_entries = list(Campaign.objects.filter(name__in=agent_logged_in_campaign).values_list("switch__id",flat=True))
				switch_list = list(Switch.objects.filter(id__in=selected_entries).exclude(id__in=switch_entries).values_list("id",flat=True))
				return JsonResponse({"selected_entries":switch_list})       
			if model_name == "User":
				agent_logged_in = get_login_agent()
				user_list = list(User.objects.filter(id__in=selected_entries).exclude(username__in=agent_logged_in).values_list("id",flat=True))
				return JsonResponse({"selected_entries":user_list}) 
			if model_name == "Group":
				agent_logged_in = get_login_agent()
				group_list = list(User.objects.filter(username__in=agent_logged_in, group__isnull=False).values_list("group__id",flat=True))
				group_ids = list(Group.objects.filter(id__in=selected_entries).exclude(id__in=group_list).values_list("id",flat=True))
				return JsonResponse({"selected_entries":group_ids})
			if model_name == "Phonebook":
				camp_id = Campaign.objects.filter(name__in=agent_logged_in_campaign).values_list('id',flat=True)
				login_phonebook_ids = Phonebook.objects.filter(campaign__in=list(camp_id)).values_list('id',flat=True)
				phonebook_ids = list(Phonebook.objects.filter(id__in=selected_entries).exclude(id__in=login_phonebook_ids).values_list('id',flat=True))
				return JsonResponse({"selected_entries":phonebook_ids})
		return Response({"campaign_id":selected_entries})

class DeleteEntryApiView(APIView):
	"""
	this class module is defined for delete operation of all the models.
	"""
	def post(self, request):
		app_label = request.POST.get("app_name", "")
		model_name = request.POST.get("model_name", "")
		selected_entries = request.POST.getlist('selected_entry')
		select_all = request.POST.get("select_all", "")
		perform_op = request.POST.get("perform_operation", "")
		model = apps.get_model(app_label=app_label, model_name=model_name)
		if selected_entries and perform_op == "delete":
			selected_entries = json.loads(selected_entries[0])
			if model_name == "Campaign":
				try:
					r_campaigns = pickle.loads(settings.R_SERVER.get("campaign_status") or pickle.dumps(CAMPAIGNS))
					for campaign_id in selected_entries:
						camp_ip_slug = Campaign.objects.values('switch__ip_address','slug','name').get(id=campaign_id)
						users = User.objects.filter(Q(group__in = model.objects.get(
							id = campaign_id).group.all())|Q(
							id__in = model.objects.get(id = campaign_id
							).users.all().values_list("id", flat=True))).prefetch_related()
						if users:
							SERVER = freeswicth_server(camp_ip_slug['switch__ip_address'])
							for user in users:
								print(user.properties.extension,camp_ip_slug['slug'])
								SERVER.freeswitch.api("callcenter_config",
									"tier del %s %s" % (camp_ip_slug['slug'],user.properties.extension))
						if camp_ip_slug['slug'] in r_campaigns:
							del r_campaigns[camp_ip_slug['slug']]
						CSS.objects.filter(campaign = camp_ip_slug['name']).delete()
						CampaignInfo.objects.filter(name=camp_ip_slug['slug']).delete()
					settings.R_SERVER.set("campaign_status", pickle.dumps(r_campaigns))
					PhonebookBucketCampaign.objects.filter(id__in=selected_entries).delete()
					model.objects.filter(id__in=selected_entries).delete()
					return Response({"msg": "Selected entries deleted"})                                
				except socket.error as v:
					print ("RPC Error %s: Freeswitch RPC module may not be" \
					"loaded or properly configured campaign" % v)
					r_campaigns = pickle.loads(settings.R_SERVER.get("campaign_status") or pickle.dumps(CAMPAIGNS))
					for campaign_id in selected_entries:
						camp_ip_slug = Campaign.objects.values('switch__ip_address','slug').get(id=campaign_id)
						if camp_ip_slug['slug'] in r_campaigns:
							del r_campaigns[camp_ip_slug['slug']]
						CSS.objects.filter(campaign = camp_ip_slug['name']).delete()
						CampaignInfo.objects.filter(name=camp_ip_slug['slug']).delete()
					settings.R_SERVER.set("campaign_status", pickle.dumps(r_campaigns))
					PhonebookBucketCampaign.objects.filter(id__in=selected_entries).delete()
					model.objects.filter(id__in=selected_entries).delete()
					return Response({"msg": "Selected entries deleted"})                    
			elif model_name == "Group":
				print("group called",selected_entries)
				try:
					camp_ip_slugs = Campaign.objects.filter(group__in = selected_entries).values(
						'slug','switch__ip_address','group__id').prefetch_related()
					if camp_ip_slugs:
						for campaign in camp_ip_slugs:
							users=User.objects.filter(group__id = campaign['group__id'])
							SERVER = freeswicth_server(campaign['switch__ip_address'])
							for user in users:
								print(user.properties.extension,campaign['slug'])
								SERVER.freeswitch.api("callcenter_config",
									"tier del %s %s" % (campaign['slug'],user.properties.extension))
					model.objects.filter(id__in=selected_entries).delete()
					return Response({"msg": "Selected entries deleted"})
				except socket.error as v:
					print ("RPC Error %s: Freeswitch RPC module may not be" \
					"loaded or properly configured campaign" % v)
					model.objects.filter(id__in=selected_entries).delete()
					return Response({"msg": "Selected entries deleted"})
			elif model_name == "User":
				r_campaigns = pickle.loads(settings.R_SERVER.get("campaign_status") or pickle.dumps(CAMPAIGNS))
				for user_id in selected_entries:
					users=User.objects.get(id=user_id)
					campaigns = users.properties.campaign
					for campaign in campaigns:
						if campaign in r_campaigns:
							r_campaigns[campaign].remove(users.properties.extension)
				settings.R_SERVER.set("campaign_status", pickle.dumps(r_campaigns))
				model.objects.filter(id__in=selected_entries).exclude(username="admin").delete()
			elif model_name == "PauseBreak":
				exclude_phonebook_list = ['tea break', 'lunch break', 'breakfast break','meeting','dinner break']
				model.objects.filter(id__in=selected_entries).exclude(name__in=[ex_list for ex_list in exclude_phonebook_list]).delete()
			elif model_name == "Switch":
				model.objects.filter(id__in=selected_entries).exclude(name="freeswitch").delete()
			elif model_name =="Disposition":
				exclude_dis_list = ['local dnc', 'global dnc','not connected','connected','callback','busy' ,'transfer']
				model.objects.filter(id__in=selected_entries).exclude(name__in=[dis for dis in exclude_dis_list]).update(status="Delete",
					deleted_by=request.user.username,deleted_date=datetime.now())
			elif model_name == "Phonebook":
				alternate_numbers = []
				trash_contacts = []
				phonebooks = model.objects.filter(id__in=selected_entries)
				phonebook_campaign = list(phonebooks.values_list("campaign", flat=True))
				contacts = Contact.objects.filter(phonebook__in=phonebooks)
				phonebooks_id = tuple(list(phonebooks.values_list("id",flat=True)))
				query_ids = ",".join(str(i) for i in phonebooks_id)
				backup_folder = settings.MEDIA_ROOT+"/contact_backup/"+datetime.now().strftime("%m.%d.%Y")+"/"
				if not os.path.exists(backup_folder):
					os.makedirs(backup_folder)
				from scripts.eventdump import dump_contact
				dump_contact(backup_folder+"contact_"+datetime.now().strftime("%m.%d.%Y%H:%M:%S")+".sql")
				# for contact in contacts:
				#   if TrashContact.objects.filter(numeric=contact.numeric).exists():
				#       TrashContact.objects.filter(numeric=contact.numeric).delete()
				#   trash_contacts.append(TrashContact(phonebook=contact.phonebook.name, user=contact.user, numeric=contact.numeric,
				#       alt_numeric=contact.alt_numeric, first_name=contact.first_name, last_name=contact.last_name, email=contact.email,
				#       disposition=contact.disposition, status=contact.status, customer_raw_data=contact.customer_raw_data))
				# TrashContact.objects.bulk_create(trash_contacts)
				# for contact in contacts:
				#   if contact.alt_numeric:
				#       alternate_numbers.append(AlternateContact(numeric=contact.numeric, uniqueid=contact.uniqueid, alt_numeric=contact.alt_numeric))
				# AlternateContact.objects.bulk_create(alternate_numbers)
				phonebooks.delete()
				for camp in phonebook_campaign:
					contact_count = Contact.objects.filter(campaign=Campaign.objects.get(id=camp)).count()
					if contact_count == 0:
						PhonebookBucketCampaign.objects.filter(id=camp).update(is_contact=False)
			elif model_name == 'Contact':
				trash_contacts = []
				alternate_numbers = []
				contacts = model.objects.filter(id__in=selected_entries)
				numbers = list(contacts.values_list("numeric", flat=True))
				TempContactInfo.objects.filter(numeric__in=numbers).delete()
				TrashContact.objects.filter(numeric__in=numbers).delete()
				for contact in contacts:
					# if contact.alt_numeric:
					#   alternate_numbers.append(AlternateContact(numeric=contact.numeric, uniqueid=contact.uniqueid, alt_numeric=contact.alt_numeric))
					trash_contacts.append(TrashContact(phonebook=contact.phonebook.name, user=contact.user, numeric=contact.numeric,
						alt_numeric=contact.alt_numeric, first_name=contact.first_name, last_name=contact.last_name, email=contact.email,
						disposition=contact.disposition, status=contact.status, customer_raw_data=contact.customer_raw_data))
				TrashContact.objects.bulk_create(trash_contacts)
				# AlternateContact.objects.bulk_create(alternate_numbers)
				contacts.delete()
			elif model_name == 'DNC':
				for dnc_id in selected_entries:
					dnc_obj = DNC.objects.get(id=dnc_id)
					if not dnc_obj.global_dnc:
						dnc_campaign = dnc_obj.campaign.all().values_list("name", flat=True)
						Contact.objects.filter(campaign__in=list(dnc_campaign), numeric=dnc_obj.numeric).update(status="NotDialed")
				numeric = list(DNC.objects.filter(id__in=selected_entries).values_list("numeric", flat=True))
				Contact.objects.filter(id__in=selected_entries).update(status="NotDialed")
				model.objects.filter(id__in=selected_entries).delete()
			elif model_name == 'DialTrunk':
				trunks = model.objects.filter(id__in=selected_entries)
				for trunk in trunks:
					if DiaTrunkGroup.objects.filter(trunks__trunk_id=trunk.id).exists():
						dial_trunk_group = DiaTrunkGroup.objects.filter(trunks__trunk_id=trunk.id).first()
						dial_trunk_group.total_channel_count = dial_trunk_group.total_channel_count - trunk.channel_count
						dial_trunk_group.save()
				model.objects.filter(id__in=selected_entries).delete()
			else:
				model.objects.filter(id__in=selected_entries).delete()

		if perform_op == "delete" and not select_all:
			selected_entries_txt = " ,".join(str(ele) for ele in selected_entries)
			create_admin_log_entry(request.user, model_name.lower(), "3",'DELETED',selected_entries_txt)
		if perform_op=="delete" and select_all:
			if model_name == "User":
				model.objects.all().exclude(username="admin").delete()
			else:
				model.objects.all().delete()
			message = user.username+' has deleted all'+model_name.lower()+' data'
			AdminLogEntry.objects.create(**{'created_by_id':user.id, 'change_message':message,
				'action_name':"3", 'event_type':'DELETED'})
		if perform_op =="Make Active" and select_all:
			if model_name=="User":
				model.objects.all().update(is_active=True)
			else:
				model.objects.all().update(status="Active")
			if model_name == "Campaign":
				PhonebookBucketCampaign.objects.filter().update(is_contact=True)
			if model_name == "CSS":
				camp = model.objects.values_list("campaign",flat=True)
				PhonebookBucketCampaign.objects.filter(id__in=list(Campaign.objects.filter(name__in=list(camp)).values_list("id",flat=True))).update(is_contact=True)
			if model_name == "Phonebook":
				PhonebookBucketCampaign.objects.filter(id__in=list(model.objects.values_list("campaign",flat=True))).update(is_contact=True)
			message = user.username+' has enabled all'+model_name.lower()+' data'
			AdminLogEntry.objects.create(**{'created_by_id':user.id, 'change_message':message,
				'action_name':action_type,'event_type':'ENABLED'})
		if perform_op =="Make Active" and selected_entries:
			selected_entries = json.loads(selected_entries[0])
			if model_name=="User":
				model.objects.filter(id__in=selected_entries).update(is_active=True)
			else:
				model.objects.filter(id__in=selected_entries).update(status="Active")
			if model_name == "Campaign":
				PhonebookBucketCampaign.objects.filter(id__in=selected_entries).update(is_contact=True)
			if model_name == "CSS":
				camp = model.objects.filter(id__in=selected_entries).values_list("campaign",flat=True)
				PhonebookBucketCampaign.objects.filter(id__in=list(Campaign.objects.filter(name__in=list(camp)).values_list("id",flat=True))).update(is_contact=True)
			if model_name == "Phonebook":
				PhonebookBucketCampaign.objects.filter(id__in=list(model.objects.filter(id__in=selected_entries).values_list("campaign",flat=True))).update(is_contact=True)
			selected_entries_txt = " ,".join(str(ele) for ele in selected_entries)
			create_admin_log_entry(request.user, model_name.lower(), "4",'ACTIVE',selected_entries_txt)
		temp_data = TempContactInfo.objects.none()
		if perform_op =="Make InActive" and selected_entries:
			selected_entries = json.loads(selected_entries[0])
			if model_name=="Phonebook":
				temp_data =TempContactInfo.objects.filter(phonebook__in=model.objects.filter(id__in=selected_entries))
			if model_name == "CSS":
				temp_data = TempContactInfo.objects.filter(campaign__in=list(model.objects.filter(id__in=selected_entries).values_list("campaign",flat=True)))
			if model_name == "Campaign":
				temp_data = TempContactInfo.objects.filter(campaign__in=list(model.objects.filter(id__in=selected_entries).values_list("name",flat=True)))
			if temp_data.exists():
				camp = temp_data.values_list("campaign",flat=True)
				for temp in temp_data:
					Contact.objects.filter(id=temp.contact_id).update(status=temp.previous_status)
				temp_data.delete()
				PhonebookBucketCampaign.objects.filter(id__in=list(Campaign.objects.filter(name__in=list(camp)).values_list("id",flat=True))).update(is_contact=True)
			if model_name=="User":
				model.objects.filter(id__in=selected_entries).exclude(id=request.user.id).update(is_active=False)   
			else:
				model.objects.filter(id__in=selected_entries).update(status="Inactive")
			selected_entries_txt = " ,".join(str(ele) for ele in selected_entries)
			create_admin_log_entry(request.user, model_name.lower(), "5",'INACTIVE', selected_entries_txt)
		if perform_op =="Make InActive" and select_all:
			if model_name=="Phonebook":
				temp_data =TempContactInfo.objects.filter(phonebook__in=model.objects.all())
			if model_name == "CSS":
				temp_data = TempContactInfo.objects.filter(campaign__in=list(model.objects.all().values_list("campaign",flat=True)))
			if model_name == "Campaign":
				temp_data = TempContactInfo.objects.filter(campaign__in=list(model.objects.alll().values_list("name",flat=True)))
			if temp_data.exists():
				camp = temp_data.values_list("campaign",flat=True)
				for temp in temp_data:
					Contact.objects.filter(id=temp.contact_id).update(status=temp.previous_status)
				temp_data.delete()
				PhonebookBucketCampaign.objects.filter(id__in=list(Campaign.objects.filter(name__in=camp).values_list("id",flat=True))).update(is_contact=True)
			if model_name=="User":
				model.objects.all().exclude(id=request.user.id).update(is_active=False)
			else:
				model.objects.all().update(status="Inactive")
			message = user.username+' has inactive all'+model_name.lower()+' data'
			AdminLogEntry.objects.create(**{'created_by_id':user.id, 'change_message':message,
				'action_name':"5",'event_type':'INACTIVE'})
		return Response({"msg": "Selected entries deleted"})


def csvDownload(fields, model, file_type, exclude=[],
				description="Export filtered data as CSV file"):

	"""
	Generic csv export admin action.
	"""
	response = HttpResponse(content_type='application/force-download')
	response['Content-Disposition'] = 'attachment; filename=%s.%s' % \
			(model, file_type)

	if file_type=="csv":
		writer = csv.writer(response)
		writer.writerow(list(fields))
	else:
		wb = xlwt.Workbook(encoding='utf-8')
		ws = wb.add_sheet(model)
		row_num = 0
		columns = list(fields)
		for col_num in range(len(columns)):
			ws.write(row_num,col_num, columns[col_num])
		wb.save(response)
	return response


class ChangePasswordApiView(APIView):
	"""
	This view is to change password 
	"""
	renderer_classes = [TemplateHTMLRenderer]
	template_name = "admin/change_password.html"
	permission_classes = [AllowAny]

	def get(self, request):
		return Response({'request':request})

	def post(self, request):
		username = request.POST.get('username','')
		old_password = base64.b64decode(request.POST.get('old_password','')).decode('utf-8')
		new_password = base64.b64decode(request.POST.get('new_password','')).decode('utf-8')
		if old_password == new_password:
			return JsonResponse({"error":"New password should not be same as Old password"}, status=401)
		PASSWORD_ATTEMPTS = pickle.loads(settings.R_SERVER.get("password_attempt_status") or pickle.dumps({}))
		if username:
			if not User.objects.filter(username=username).exists():
				return JsonResponse({"error": "No such username or password"}, status=404)
			user = User.objects.get(username=username)
		else:
			user = request.user
		if user.is_active:
			if user.check_password(old_password):
				user.set_password(new_password)
				user.password_date = date.today()
				user.save()
				PASSWORD_ATTEMPTS[user.username] = 0
				settings.R_SERVER.set('password_attempt_status',pickle.dumps(PASSWORD_ATTEMPTS))
				PasswordChangeLogs.objects.create(username=user.username,change_type='0')
				return JsonResponse({"msg":"Password Updated Successfully"})
			return JsonResponse({"error":"Old Password you have entered is incorrect"}, status=401)
		return JsonResponse({"error": "You are not an active user. Please contact Administrator."}, status=401)


class FetchExistingDataApiView(APIView):
	'''
	This view is used to get basic information of existing data
	
	'''
	def post(self, request):
		app_label = request.POST.get("app_label", "")
		model_name = request.POST.get("model_name", "")
		serializer_name = request.POST.get("serializer", "")
		instance_id = request.POST.get("instance_id", "")
		
		model = apps.get_model(app_label=app_label, model_name=model_name)
		
		serializer = ['UserSerializer', 'CampaignSerializer']
		serializer_list = __import__(app_label+'.serializers', fromlist=serializer)
		serializer_inst = getattr(serializer_list, serializer_name)

		instance_data = serializer_inst(model.objects.get(id=instance_id)).data
		return JsonResponse({"instance_info": instance_data})

class DownloadSampleApiView(APIView):
	'''
	This view is used to download sample file
	'''

	def get(self, request, file_name, file_type):
		cols = []
		if file_name == 'crm-fields':
			cols = CRM_FIELDS
			model = "CRM"
		if file_name == "user":
			cols = USER_FIELDS
			model = "User"
		if file_name == "dnc_list":
			cols = DNC_FIELDS
			model = "DNC"
		if file_name == "alt_numeric":
			cols = ALTERNATE_FIELDS
			model = "AlternateContact"
		if file_name == "holidays":
			cols = HOLIDAYS_FIELDS
			model =  "Holidays"
		if cols:
			return csvDownload(cols, model,file_type)

class DownloadSampleContactApiView(APIView):
	'''
	This view is used to download sample
	'''
	def get(self, request, col_name, file_type):
		if col_name == "transfer_contacts":
			cols = ["from_agent","to_agent"]
			model="sample_transfer_contact"
		else:
			cols = [col_name]
			model="sample_contact_delete"
		return csvDownload(cols, model,file_type)

def get_paginated_object(result, page, paginate_by):
	""" 
	getting the pagination objects
	"""
	paginator = Paginator(result, paginate_by)
	try:
		result = paginator.page(page)
	except PageNotAnInteger:
		result = paginator.page(1)
	except EmptyPage:
		result = paginator.page(paginator.num_pages)
	return result

def data_for_pagination(request):
	""" 
	data for pagination objects 
	"""
	data = {}
	if request.GET.get('page'):
		data["page"] = int(request.GET.get('page' ,1))
	else:
		data["page"] = 1
	data["paginate_by"] = int(request.GET.get('paginate_by', 10))
	data["search_by"] = request.GET.get('search_by','')
	data["column_name"] = request.GET.get('column_name', '')
	data['paginate_by_list']= PAGINATE_BY_LIST
	return data

def data_for_vue_pagination(queryset):
	""" 
	data for fron end vue pagination 
	"""
	pagination_dict = {'total_records': queryset.paginator.count,
	'total_pages': queryset.paginator.num_pages,
	'page': queryset.number,
	'has_next': str(queryset.has_next()).lower(),
	'has_prev': str(queryset.has_previous()).lower(),
	'start_index': queryset.start_index(),
	'end_index': queryset.end_index()}
	return pagination_dict

def get_active_campaign(request):
	# campain related count
	admin = False
	if request.user.user_role and request.user.user_role.access_level == 'Admin':
		admin = True
	if request.user.is_superuser or admin:
		active_camps = Campaign.objects.filter(status="Active")
		camp = active_camps.values_list("name", flat=True)
		active_camp = list(active_camps.values_list("id",flat=True))
	else:
		users = User.objects.filter(reporting_to = request.user).prefetch_related(
			'group', 'reporting_to', 'user_role')
		if request.user.user_role.access_level == 'Manager':
			team = User.objects.filter(reporting_to__in = users)
			users = users | team
		users = list(users.values_list("id", flat=True))
		camp_objs = Campaign.objects.filter(Q(users__id__in=users)|Q(users=request.user)|Q(group__in=request.user.group.all())).filter(status="Active")
		camp_list = list(camp_objs.values_list("name", flat=True))
		active_camps = camp_objs.filter(status="Active").distinct()
		# camp_name = list(active_camps.values_list("name", flat=True))
		active_camp = list(active_camps.values_list("id",flat=True))
		camp = set(camp_list)
	noti_count = Notification.objects.filter(campaign__in=camp, viewed=False).count()
	return camp, active_camp, noti_count

def create_admin_log_entry(user, model, action_type, event_type,name=""):
	""" 
	will create an admin log entry 
	"""
	if action_type == "7":
		message = "Force logout all users by "+user.username
	elif user.is_superuser:
		message = user.username+' with role admin has '+ACTION_TYPE[action_type]+name+' '+ACTION_TYPE[action_type+'_prefix']+model+' model'
	else:
		message = user.username+' with role '+user.user_role.name+'  has '+ACTION_TYPE[action_type]+name+' '+ACTION_TYPE[action_type+'_prefix']+model+' model'
	AdminLogEntry.objects.create(**{'created_by_id':user.id, 'change_message':message,
				'action_name':action_type,'event_type':event_type})

def sendsmsparam(campaign, numeric, session_uuid, message,user_id=None):
	""" 
	Sms sending related parameters or information 
	"""
	try:
		data = {'url':'','msg':'','phone_numbers':[],'auth_key':'','sender_id':'','session_uuid':''}
		response = ''
		if campaign.sms_gateway:
			data['url'] = campaign.sms_gateway.gateway_url
			data['auth_key'] = campaign.sms_gateway.key
			data['sender_id'] = user_id
			data['phone_numbers'] = numeric
			data['session_uuid'] = session_uuid
			remove_html = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
			for sms in message:
				data['msg'] = re.sub(remove_html,'',sms['text'])
				response = sendSMS(data, sms['id'])
		return response
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print(exc_type, fname, exc_tb.tb_lineno)


def sendSMS(data,template_id):
	""" Sending the sms """
	url = data['url']
	msg = data['msg']
	auth_key = data["auth_key"]
	msg = re.sub(r'\\x..', ' ', msg)
	msg = msg.encode('ascii', 'ignore').decode('unicode_escape')
	reciever = data["phone_numbers"]
	# payload = "sender_id=FSTSMS&message={}&language=english&route=p&numbers={}".format(msg, reciever)
	# headers = {
	# 'authorization': data["auth_key"],
	# 'Content-Type': "application/x-www-form-urlencoded",
	# 'Cache-Control': "no-cache",
	# }
	final_message = urllib.parse.quote(msg)
	final_url = "{}{}&send_to={}&msg={}".format(url,auth_key,reciever,final_message)
	try:
		response = requests.request("GET", url=final_url)
		print(response.status_code,"code")
		# response = json.loads(response.text)
		msg = 'Unsuccessfully Sent'
		status = 'Inactive'
		success_message = response.text.split('|')[0].strip()
		if 'success' == success_message:
			msg = 'Successfully Sent'
			status = 'Active'
		SMSLog.objects.create(sms_text=data['msg'], sent_by_id=data["sender_id"], reciever=data["phone_numbers"], status=status,
			status_message=response.text,session_uuid=data['session_uuid'], template_id=template_id)
		return response.text
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		print(exc_type, fname, exc_tb.tb_lineno)
		return "Temporary Unavailable"

def csvDownloadTemplate(fields, model, file_type, dummy_value, exclude=[],
				description="Export filtered data as CSV file"):
	"""
	Generic csv export admin action.
	"""
	response = HttpResponse(content_type='application/force-download')
	response['Content-Disposition'] = 'attachment; filename=%s.%s' % \
			(model, file_type)
	if file_type=="csv":
		writer = csv.writer(response)
		writer.writerow(list(fields))
		writer.writerow(list(dummy_value))
	else:
		wb = xlwt.Workbook(encoding='utf-8')
		ws = wb.add_sheet('phonebook')
		row_num = 0
		columns = list(fields)
		for col_num in range(len(columns)):
			ws.write(row_num,col_num, columns[col_num])
		for col_num in range(len(dummy_value)):
			ws.write(1,col_num, dummy_value[col_num])
		wb.save(response)
	return response

class SystemBootAction(LoginRequiredMixin, APIView):
	"""
	This View to reboot or shutdown server
	"""
	login_url = '/'

	def post(self, request):
		user = request.user
		action = request.POST.get('action','')
		if user.is_superuser or (request.user.user_role and request.user.user_role.access_level == 'Admin'):
			try:
				if action == "shutdown":
					cmd = "sudo shutdown -h now"
					msg = "System ready for shutdown!"
				elif action == "reboot":
					cmd = "sudo reboot"
					msg = "System ready for restart!"
				os.system(cmd)
				# print(cmd)
			except:
				msg = "You not have enough privileges!"
		else:
			msg = "You not have enough privileges!"
		return JsonResponse({'msg':msg})



def mapmyindia_token_generator():
	try:
		url = settings.MAPMYINDIA_API_URL
		params = settings.MAPMYINDIA_API_DATA
		MAPMYINDIA = pickle.loads(settings.R_SERVER.get("mapmyindia") or pickle.dumps({}))
		response = requests.post(url,data=params)
		if response.status_code == 200:
			data = json.loads(response.text)
			settings.R_SERVER.set("mapmyindia", pickle.dumps(data))
		else:
			print("Invalid Response from MAPMYINDIA API",response.status_code)
			return "Invalid Response from MAPMYINDIA API"
	except Exception as e:
		print(e)

class PasswordResetView(APIView):
	permission_classes = [AllowAny]
	def post(self,request):
		from callcenter.utility import (email_connection) 
		username_or_email = request.POST.get('credentials')
		user_obj = User.objects.filter(Q(email__iexact=username_or_email)|Q(username__iexact=username_or_email))
		pass_obj = PasswordManagement.objects.filter().first()
		if user_obj.exists():
			user = user_obj.first()
			if user.email != '' and user.email != None:
				if pass_obj:
					subject = "Flexydial Password Reset Request"
					email_template_name = "registration/password_reset_email.txt"
					message = pass_obj.password_data['message'].replace('${username}',username_or_email)
					content = {
							"message": message,
							"username":username_or_email,
							"email":user.email,
							'domain':settings.WEB_SOCKET_HOST,
							'site_name': 'Flexydial',
							"uid": urlsafe_base64_encode(force_bytes(user.pk)),
							'token': default_token_generator.make_token(user),
							'protocol': 'https',
							}
					email = render_to_string(email_template_name, content)
					try:
						conn = email_connection(pass_obj.password_data['email_id'],pass_obj.password_data['email_password'],pass_obj.password_data['email_host'],pass_obj.password_data['port_number'])
						msg = EmailMultiAlternatives(subject,"",pass_obj.password_data['email_id'], [user.email],connection=conn)
						msg.attach_alternative(email, "text/html")
						response = msg.send()
						PasswordResetLogs.objects.create(username=user.username,password_uuid=content['token'])
					except BadHeaderError:
						return Response({"error":"Invalid header format"})
					return Response({"success":"Password Reset Mail has been sent"})
				else:
					return Response({"error":"Gateway Credentials are not Defined"})
			return Response({"error":"Email is Not Present for the User, Contact Admin For Updation"})
		return Response({"error":"User Does Not exists with this Credentials"})

class CustomPasswordResetConfirmView(PasswordResetConfirmView):

	def form_valid(self, form):
		pr_obj = PasswordResetLogs.objects.filter(password_uuid=self.request.session[INTERNAL_RESET_SESSION_TOKEN])
		if pr_obj:
			pr_obj.update(reset_success=True)
		return super().form_valid(form)


class CustomPasswordResetForm(SetPasswordForm):
	
	def save(self,*args, commit=True, **kwargs):
		user = super().save(*args, commit=False, **kwargs)
		user.is_active = True
		user.password_date = date.today()
		PASSWORD_ATTEMPTS = pickle.loads(settings.R_SERVER.get("password_attempt_status") or pickle.dumps({}))
		PASSWORD_ATTEMPTS[user.username] = 0
		settings.R_SERVER.set('password_attempt_status',pickle.dumps(PASSWORD_ATTEMPTS))
		if commit:
			user.save()
		return user

class GetCrmDocuments(APIView):
	"""
	This view used to get data from sbfc client 
	"""
	permission_classes = [AllowAny]

	def post(self,request):
		data = request.data
		if data:
			if 'data' in data and  'crm_ref_no' in data['data'] and data['data']['crm_ref_no']:
				crm_ref_no = data['data']['crm_ref_no']
				crm_doc_obj = KycDocuments.objects.filter(crm_ref_no = crm_ref_no)
				if crm_doc_obj.exists():
					crm_doc_obj.update(data=data)
					return JsonResponse({'msg':'data updated successfully','status':200},status=200)
				else:
					KycDocuments.objects.create(crm_ref_no=crm_ref_no,data=data)
					return JsonResponse({'msg':'data created successfully','status':200},status=200)
			else:
				return JsonResponse({'error':'crm Ref No is empty/key is not present','status':402},status=402)
		else:
			return JsonResponse({'error':'kindly provide the data in json format','status':402},status=402)


class ShowDocument(LoginRequiredMixin,APIView):
	""" 
	This view is used to show the documents on the view document click
	"""
	def get(self,request):
		crm_ref_no  = request.GET.get('crm_ref_no','')
		final_list= []
		data = {}
		if crm_ref_no:	
			kyc_obj = KycDocuments.objects.filter(crm_ref_no=crm_ref_no)
			if kyc_obj.exists():
				data = kyc_obj.first().data
			if data:
				for key, value in data['data'].items():
					if isinstance(value,list):
						for doc in value:
							final_dict = {}
							final_dict['id_name'] = doc['master_nm']
							final_dict['image_content'] = doc['image_content']
							final_dict['id_number'] = doc['doc_no']
							final_list.append(final_dict)
				return JsonResponse({"success":final_list},status=200)
			else:
				return JsonResponse({'error':'No documents Found with us'},status=404)
		else:
			return JsonResponse({'error':'Send Crm Ref No from the appointmentdetails - crm_ref_no'},status=206)	


class Filter_TTS_Voices(LoginRequiredMixin,APIView):
	def get(self,request):
		tts_lang_code = request.GET.get('tts_lang_code','')
		collected_voices = []
		for voice in TTS_VOICES:
			if tts_lang_code in voice.keys():
				collected_voices = voice[tts_lang_code]
		return Response(collected_voices)
		