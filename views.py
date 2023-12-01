from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
# from callcenter.views import WebPSTNAgentCallAPIClick2CallView
from callcenter.models import ThirdPartyApiUserToken,User,UserVariable,Campaign
from .models import ClickToCallDispo,ClickToCallConfig,ClickToCallUserConfig
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from dialer.dialersession import click_to_call_initiate,click_to_call_inbound_initiate,click_to_call_transfer_call,hangup,fs_transfer_agent_call,fs_transfer_call,click_to_call_conference
from django.db.models import Q, F, Sum, TimeField, Value, Count,Max
import json
from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponseRedirect,HttpResponse, StreamingHttpResponse, JsonResponse
from callcenter.utility import get_agent_status,set_agent_status,get_all_keys_data_df
from django.contrib.auth.mixins import LoginRequiredMixin


class ClickToCallConfigView(APIView):
	login_url = '/'
	renderer_classes = [ TemplateHTMLRenderer ]
	template_name = 'clicktocall/clicktocallconfig.html'

	def get(self, request, **kwargs):
		ctcc_obj = ClickToCallConfig.objects.first()
		active_campaigns = Campaign.objects.filter(status="Active") #.values("id","name")
		context = {'ctcc_obj':ctcc_obj,"active_campaigns":active_campaigns}
		return Response(context)

	def post(self, request, **kwargs):
		call_log_url = request.POST.get('call_log_url','')
		agent_popup_url = request.POST.get('agent_popup_url','')
		agent_route_url = request.POST.get('agent_route_url','')
		clicktocall_campaign = request.POST.get('clicktocall_campaign','')
		
		data_params = {
			'call_log_url' : call_log_url,
			'agent_popup_url' : agent_popup_url,
			'agent_route_url':agent_route_url,
		}

		is_obj_exists = ClickToCallConfig.objects.filter()
		if is_obj_exists.exists:
			is_obj_exists.update(is_active=True if request.POST.get('is_active') == 'true' else False,data_parameters=data_params,campaign=clicktocall_campaign)
		else:
			ctcc_create = ClickToCallConfig.objects.create(created_by=request.user,is_active=True if request.POST.get('is_active') == 'true' else False,data_parameters=data_params,campaign=clicktocall_campaign)
		return JsonResponse({"msg": "Saved Successfully"})


class ThirdPartyClickToCallDispo(APIView):
	permission_classes = [AllowAny]

	def head(self, request, *args, **kwargs):
		headers = {
			'Content-Type': 'application/json',
			'Content-Length': 12345,
			'Last-Modified': 'Wed, 25 Oct 2023 11:21:36 GMT',
		}
		return Response(headers, status=200)

	def post(self, request, *args, **kwargs):
		try:
			data = json.loads(request.body.decode())
			save_data = ClickToCallDispo.objects.create(session_uuid =  data.get('callSessionId'),customer_number= data.get('customerNumber'),virtual_number= data.get('virtualNumber'),disposition= data.get('dispositionValue'),agent_number= data.get('agentNumber'),agent_id= data.get('agentId'))
			data.pop("callSessionId", None) 
			data.pop("customerNumber", None) 
			data.pop("virtualNumber", None)
			data.pop("dispositionValue", None) 
			data.pop("agentNumber", None) 
			data.pop("agentId", None) 
			save_data.data_parameters = data
			save_data.save()
			return Response({"message": "Data collected successfully"}, status=200)
		except Exception as e:
			print(e,'Error occured')
			return Response({"error": "Something went wrote",'cause':str(e)}, status=200)



class ClickToCallInbound(APIView):
	permission_classes = [AllowAny]
	def post(self, request):
		try:
			incom_post_data=json.loads(request.body.decode('utf-8'))
			caller_id = incom_post_data.get("caller_id")
			print(caller_id,'caller_idcaller_idcaller_id',type(caller_id))
			dialed_uuid = incom_post_data.get("dialed_uuid")
			server = incom_post_data.get("server")
			destination_number = incom_post_data.get("destination_number") 

			import requests

			# url = f'https://telephony-in21.leadsquared.com/1/api/Telephony/LeadRouteV2/ORG70791/247007b33beb43855a032bc27b64af282d/a9198f8a-f69d-4c5a-b920-1134d9adb274?caller_id={destination_number}&agentInfo=true'

			ctc_config_obj = ClickToCallConfig.objects.first()
			url = ctc_config_obj.data_parameters['agent_route_url']
			
			response = requests.get(url)

			resp_agent_data = json.loads(response.text)
			agent_username = resp_agent_data.get('TelephonyAgentId','')
			print(agent_username,'agent_usernameagent_username')
			if not agent_username:
				all_agents_data = get_all_keys_data_df()
				all_agents_data_active = all_agents_data[all_agents_data['state'] != 'InCall']
				all_agents_act_list = all_agents_data_active['username'].to_list()
				all_agents_list = all_agents_data_active['username'].to_list()
				print(all_agents_list,'all_agents_listall_agents_list')
				if all_agents_act_list:
					agent_username = all_agents[0]
				else:
					agent_username = all_agents_list[0]	
				# agent_username = "flexy_mahesh"
				# pass
				# we need to call lead creation api from here
			
			agent_obj = User.objects.filter(username=agent_username)
			incom_user_groups = agent_obj.first().group.all()
			campaign_obj = ClickToCallConfig.objects.filter().first().campaign #Campaign.objects.filter(name='test').first()
			extension = agent_obj.first().properties.extension
			user_numeric = agent_obj.first().properties.wfh_numeric

			data = click_to_call_inbound_initiate(server,extension=extension,
							campaign=campaign_obj.name
							,campaign_obj=campaign_obj,
							user_obj = agent_obj.first(),
							ori_uuid1 = dialed_uuid,
							user_numeric = user_numeric,
							destination_number=destination_number,
							virtual_number = str(caller_id)

							)
			return JsonResponse({'extension':[extension],'no_agent_audio':True,'c_max_wait_time':True,'audio_moh_sound':True})
		except Exception as e:
			print(e,'AAAAAAAAAAAAAAA')
			return JsonResponse({'no_agent_audio':True,'c_max_wait_time':True,'audio_moh_sound':True})

class ThirdPartyCall(APIView):
	"""
	Intiate the click to call
	"""
	permission_classes = [AllowAny]

	model = ThirdPartyApiUserToken
	def get(self, request, token=None, contact=None, agent=None):
		try:
			if validate_third_party_token(token, request.META.get("REMOTE_ADDR")):
				queryset = self.model.objects.get(token=token)
				campaign_obj = Campaign.objects.get(name=queryset.campaign.name)
				user_obj = User.objects.get(username=queryset.user.username)
				agent_number = agent if agent is not None else queryset.mobile_no
				trunk_id , dial_string, caller_id, country_code = channel_trunk_single_call(campaign_obj)
				if trunk_id:
					data = click_to_call_initiate(campaign_obj.switch.ip_address,extension=user_obj.extension,
							campaign=queryset.campaign.name,caller_id=caller_id,customer_num=contact,agent_num=agent_number
							,dial_string=dial_string)

					if 'error' in data:
						return JsonResponse(data,status=404)
					return JsonResponse(data,status=200)
				else:
					return JsonResponse({"Channel Is not from_iterable":""},status=404)
			return JsonResponse({"message":"Wrong Credentials, Please Check Credentials again"},status=404)
		except Exception as e:
			print('Exception in ThirdPartyCall', e)
			return JsonResponse({"message":"exception"},status=404)

	def post(self, request):
		print(request.body,'++++')
		try:
			raw_data = json.loads(request.body.decode())
			caller_id = raw_data.get("caller_id","")
			agent_number = raw_data.get("agent_number","")
			customer_number = raw_data.get("customer_number","")
			agent_id = raw_data.get("agent_id","")
			VirtualNumberWithoutCC = raw_data.get("VirtualNumberWithoutCC",'')
			if not customer_number:
				return JsonResponse({'error':'Please provide customer number'},status=404)

			if agent_number:
				c2c_user = UserVariable.objects.filter(wfh_numeric=agent_number)
				if not c2c_user.exists():
					return JsonResponse({'error':'Agent number didn"t find in our records'},status=404)
				c2c_user = c2c_user.first()
				c2c_user_config = ClickToCallUserConfig.objects.filter(config_user__id = c2c_user.user.id).first()
				
				if not c2c_user:
					return JsonResponse({'error':'Agent number didn"t find in our records'},status=404)
					
				extension =  c2c_user.extension
				user_obj = c2c_user.user
				virtual_dialstring =  c2c_user_config.user_dial_trunk.dial_string
				VirtualNumberWithoutCC = c2c_user_config.virtual_numeric #gsm_numbers[0]
				if c2c_user:

					campaign_obj  = ClickToCallConfig.objects.filter().first().campaign
					switch_ip  =  campaign_obj.switch.ip_address 
					dial_string  =  campaign_obj.trunk.dial_string
					data = click_to_call_initiate(switch_ip,extension=extension,
										campaign=campaign_obj.name,customer_num=customer_number,agent_num=agent_number
										,dial_string=dial_string,campaign_obj=campaign_obj,virtual_number = VirtualNumberWithoutCC,
										virtual_dialstring=virtual_dialstring,user_obj = user_obj )
					if 'error' in data:
						return JsonResponse(data,status=404)
					return JsonResponse(data,status=200)
				return JsonResponse({'error':'Agent number didn"t find in our records'},status=404)
		except Exception as e:
			print(e,'eeeeee')
			return JsonResponse({'error':'Please provide agent number'},status=404)
		
class ClickToCallConfAPIView(APIView):
	"""
	This view is used to implement conference call
	"""
	permission_classes = [AllowAny]

	def post(self, request):
		raw_data = json.loads(request.body.decode())
		print(raw_data,'raw_dataraw_data')
		agent_number = raw_data.get("agent_number","")
		customer_number = raw_data.get("customer_number","")
		c2c_user = UserVariable.objects.filter(wfh_numeric=agent_number)
		if c2c_user.exists():
			c2c_user = c2c_user.first()
			c2c_user_config = ClickToCallUserConfig.objects.filter(config_user__id = c2c_user.user.id).first()
			agent_details = get_agent_status(c2c_user.extension).get(c2c_user.extension,{})
			if agent_details:
				agent_uuid = agent_details.get("dialerSession_uuid",'')
				customer_uuid = agent_details.get("user_dialed_uuid",'')
				transfer_agent_number = raw_data.get("transfer_agent_number","")
				
				campaign_obj = ClickToCallConfig.objects.filter().first().campaign
				switch_ip  =  campaign_obj.switch.ip_address 
				status = click_to_call_conference(switch_ip,campaign_obj=campaign_obj,transf_num=transfer_agent_number,uuid1=agent_uuid,uuid2=customer_uuid)
				return JsonResponse(status)
			else:
				status = {'message':"We Didn't find any User Details"}
				return JsonResponse(status,404)
		status = {"message":"We didnt find any user with that agent number"}
		return JsonResponse(status,404)
	


class ClickToCallTransferCallAPIView(APIView):
	"""
	This view is used to implement transfer call
	"""
	permission_classes = [AllowAny]

	def post(self, request):
		raw_data = json.loads(request.body.decode())
		print(raw_data,'raw_dataraw_data')
		agent_number = raw_data.get("agent_number","")
		customer_number = raw_data.get("customer_number","")
		c2c_user = UserVariable.objects.filter(wfh_numeric=agent_number)
		if c2c_user.exists():
			c2c_user = c2c_user.first()
			c2c_user_config = ClickToCallUserConfig.objects.filter(config_user__id = c2c_user.user.id).first()
			agent_details = get_agent_status(c2c_user.extension).get(c2c_user.extension,{})
			if agent_details:
				agent_uuid = agent_details.get("dialerSession_uuid",'')
				customer_uuid = agent_details.get("user_dialed_uuid",'')
				transfer_agent_number = raw_data.get("transfer_agent_number","")
				# transfer_agent_number
				# agent_uuid = raw_data.get("agent_uuid","")
				# customer_uuid = raw_data.get("customer_uuid","")
				# print(customer_uuid,'customer_uuidcustomer_uuid')
				campaign_obj = ClickToCallConfig.objects.filter().first().campaign
				switch_ip  =  campaign_obj.switch.ip_address 
				status = click_to_call_transfer_call(switch_ip,campaign_obj=campaign_obj,transf_num=transfer_agent_number,uuid1=agent_uuid,uuid2=customer_uuid)
				return JsonResponse(status)
			else:
				status = {'message':"We Didn't find any User Details"}
				return JsonResponse(status,404)
		status = {"message":"We didnt find any user with that agent number"}
		return JsonResponse(status,404)


class HangupforcelogoutAPIView(APIView):
	"this view is used to forcelogout the user"

	permission_classes = [AllowAny]


	def post(self, request):
		
		extension = request.POST.get("extension",'')
		agent_dict	= get_agent_status(extension)
		print('agent_dictagent_dict',agent_dict)
		session_uuid = agent_dict.get(extension,{}).get('dialerSession_uuid','')
		user_dialed_uuid = agent_dict.get(extension,{}).get('user_dialed_uuid','')
		print(session_uuid,'session_uuidsession_uuid',user_dialed_uuid)
		# campaign_obj  = Campaign.objects.get(name='test')
		campaign_obj = ClickToCallConfig.objects.filter().first().campaign
		switch_ip  =  campaign_obj.switch.ip_address
		
		hangup_status=hangup(switch_ip,uuid=str(session_uuid),
						hangup_type='sip_agent',extension=extension,campaign=campaign_obj.name)
		hangup_status=hangup(switch_ip,uuid=str(user_dialed_uuid),
						hangup_type='sip_agent',extension=extension,campaign=campaign_obj.name)

		set_agent_status(extension,{},True)
		return JsonResponse(hangup_status)