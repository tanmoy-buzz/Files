import json
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.postgres.fields import JSONField, HStoreField
from datetime import datetime
from mptt.models import MPTTModel
from django.db.models import signals, Q
import pytz,os
import re
from django.conf  import settings
from flexydial.constants import (Status, REPORTS_LIST,auto_dialed_status, PROTOCOL_CHOICES, TRUNK_TYPE, CALL_TYPE,
	CALLBACK_MODE, DIAL_RATIO_CHOICES, CAMPAIGN_STRATEGY_CHOICES, DNC_MODE, ACCESS_LEVEL, DISPO_FIELD_TYPE,
	SCHEDULE_TYPE, SCHEDULE_DAYS, CONTACT_STATUS, UPLOAD_STATUS, VB_MODE, TEMPLATE_TYPE, TRIGGER_ACTIONS, SMS_STATUS, ACTION,
	TYPE_OF_DID, STRATEGY_CHOICES, REPORT_NAME, COUNTRY_CODES,BROADCAST_MESSAGE_TYPE,PasswordChangeType,SHOW_DISPOS_TYPE)
from callcenter.signals import (
	fs_del_campaign,
	fs_group_campaign,
	fs_add_user,
	fs_del_user,
	fs_campaign,
	fs_user_campaign,
	fs_switch_action
	)
timezone = list(pytz.common_timezones)
USER_TIMEZONE = [(zone, zone) for zone in timezone]

default_time = datetime.strptime('00:00:00', '%H:%M:%S').time()

# Create your models here.
class Switch(models.Model):
	""" This table is used to store the switch information of freeswitch """
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
			on_delete=models.SET_NULL,null=True)
	name = models.CharField(max_length = 50)
	ip_address = models.CharField(max_length =20, db_index=True, unique=True)
	status = models.CharField(default='Active',choices=Status, max_length=10)
	created_date = models.DateTimeField(auto_now_add=True)
	sip_udp_port = models.IntegerField(default=40506, null=True)
	rpc_port = models.IntegerField(default=8080, null=True)
	wss_port = models.IntegerField(default=7443, null=True)
	modified_date = models.DateTimeField(auto_now=True)
	created_by = models.ForeignKey('User', related_name='switch_created_by',on_delete=models.SET_NULL,
		blank=True, null=True)

	def __str__(self):
		return self.name
	class Meta:
		ordering = ('created_date',)
		unique_together = (
				('name', 'ip_address'),
				)

signals.post_save.connect(fs_switch_action, sender=Switch)

class DialTrunk(models.Model):
	""" This table is used to store the Dialtrunk infromation of the freeswitch """
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
			on_delete=models.SET_NULL,null=True)	
	name = models.CharField(max_length = 100, db_index=True, unique=True)
	description = models.TextField(blank=True, null=True)
	dial_string = models.CharField(max_length=200, default='freetdm/default/a',
			help_text='Dial String for outbound call.<br/>format: '\
					'endpoint/trunk/<br/>eg. freetdm/default/a')
	channel_count = models.BigIntegerField(default=0)
	trunk_type = models.CharField(default='domestic',choices=TRUNK_TYPE, max_length=15)
	switch = models.ForeignKey(Switch, related_name='Switch',
			null=True, on_delete=models.SET_NULL, blank=True)
	did_range = models.CharField(max_length = 50, blank=True, null=True)
	prefix = models.BooleanField(default=False,null=True, blank=True)
	country_code = models.CharField( choices=COUNTRY_CODES, blank=True, null=True, max_length=10)
	status = models.CharField(default='Active',choices=Status, max_length=10)
	created_date = models.DateTimeField(auto_now_add=True)
	modified_date = models.DateTimeField(auto_now=True)
	created_by = models.ForeignKey('User', related_name='dial_trunk_created_by',on_delete=models.SET_NULL,
		blank=True, null=True)

	def __str__(self):
		return self.name
	class Meta:
		ordering = ('created_date',)

class UserRole(models.Model):
	""" This table is used to store the users role an there access levels and permissions """
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
		on_delete=models.SET_NULL,null=True)	
	name = models.CharField(max_length = 50, db_index=True, unique=True)
	description = models.CharField(max_length = 200, null=True, blank=True)
	permissions  = JSONField()
	access_level = models.CharField(db_index=True, choices=ACCESS_LEVEL, default=ACCESS_LEVEL[0][0], max_length=50)
	status =  models.CharField(default='Active',choices=Status, max_length=10)
	created_date = models.DateTimeField(auto_now_add=True)
	modified_date = models.DateTimeField(auto_now=True)
	created_by = models.ForeignKey('User', related_name='user_role_created_by',on_delete=models.SET_NULL,
		blank=True, null=True)

	def __str__(self):
		return self.name

		class Meta:
			ordering = ('created_date',)

	@property
	def created_by_user(self):
		if self.created_by:
			return self.created_by.username
		else:
			return ""

class Group(models.Model):
	""" This table will store the group along with the users in them """
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
			on_delete=models.SET_NULL,null=True)	
	name = models.CharField(max_length = 50, db_index=True, unique=True)
	status =  models.CharField(default='Active',choices=Status, max_length=10)
	color_code = models.CharField(null=True, blank=True, max_length=10)
	created_date = models.DateTimeField(auto_now_add=True)
	modified_date = models.DateTimeField(auto_now=True)
	created_by = models.ForeignKey('User', related_name='group_created_by',on_delete=models.SET_NULL,
		blank=True, null=True)

	def __str__(self):
		return self.name

	@property
	def users(self):
		return list(User.objects.filter(group=self).exclude(is_superuser=True).values("username","id"))
		
	@property
	def allusers(self,request):
			from flexydial.views import user_hierarchy_func
			if request.user.is_superuser:
				return list(User.objects.all().exclude(group=self).exclude(is_superuser=True).values("username", "id"))
			else:
				return list(User.objects.filter(id__in=user_hierarchy_func(request.user.id)).exclude(group=self).exclude(is_superuser=True).values("username", "id"))
	
	@property
	def users_name(self):
		return ', '.join(User.objects.filter(group=self).values_list(
				"username", flat=True))

	class Meta:
		ordering = ('created_date',)

# signals.post_save.connect(fs_add_grp_user, sender=Group)
		  
class User(AbstractUser):
	""" This table will store the user information """
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
			on_delete=models.SET_NULL,null=True)	
	date_of_birth = models.DateField(null=True, blank=True)
	user_role = models.ForeignKey(UserRole, related_name='User_Role',
			null=True, on_delete=models.SET_NULL, blank=True)
	group = models.ManyToManyField(Group, related_name='user_group',
			null=True, blank=True)
	reporting_to = models.ForeignKey("self", related_name='report_to',
			null=True, blank=True, on_delete=models.SET_NULL)
	call_type= models.CharField(default=CALL_TYPE[0][0],
			choices=CALL_TYPE, max_length=100)
	user_timezone = models.CharField(default='Asia/Kolkata',
			choices=USER_TIMEZONE, max_length=100)
	trunk = models.ForeignKey(DialTrunk, related_name='user_trunk', null=True, blank=True, on_delete=models.SET_NULL)
	caller_id = models.CharField(max_length=15, null=True, blank=True)
	created = models.DateTimeField(auto_now_add=True, db_index=True, editable=False)
	updated = models.DateTimeField(auto_now=True, db_index=True, editable=False)
	password_date = models.DateField(auto_now_add=True, db_index=True, editable=False)
	employee_id = models.CharField(max_length=50, unique=True, null=True ,help_text='employee_id')
	email_password = models.CharField(max_length=50,blank=True,null=True)
	created_by = models.ForeignKey("self", related_name='user_created_by',on_delete=models.SET_NULL,
		blank=True, null=True)
   
	def __str__(self):
		return self.username

	@property
	def active_status(self):
		if self.is_active == True:
			return "Active"
		else:
			return "Inactive"

	@property
	def extension(self):
		return self.properties.extension

	@property
	def uservariable(self):
		return self.properties

	@property
	def active_department(self):
		if self.group.all():
			return ', '.join(self.group.all().filter(status="Active").values_list(
				"name", flat=True))
		return ""

	@property
	def groups(self):
		if self.group.all():
			return ', '.join(self.group.all().values_list(
				"name", flat=True).exclude(name__isnull=True))
		return ""
   
	@property
	def active_campaign(self):
		return Campaign.objects.filter(Q(users=self)|Q(
			group__in=self.group.all().filter(status="Active"))).filter(
			status="Active").distinct().values("id","name","switch__ip_address", "auto_feedback_time", "auto_progressive_time")

	@property
	def role_name(self):
		if self.user_role:
			return self.user_role.name
		else:
			return ""

	@property
	def created_by_user(self):
		if self.created_by:
			return self.created_by.username
		return ""
	
	class Meta:
		ordering = ('-id',)

def getAdmin():
	team_extensions = list(User.objects.filter(Q(is_superuser=True)|Q(user_role__access_level='Admin')).values_list("id", flat=True))
	print(team_extensions)
	admin_list = list(UserVariable.objects.filter(
			user__in=team_extensions).values_list("extension", flat=True))
	return admin_list

class UserVariableManager(models.Manager):
	""" 
	The custom model manager will create the bulk user variable and call 
	fs_add_phone_user to trigger the signals for saving the  user in freeswitch
	"""
	def bulk_create(self, objs, **kwargs):
		super().bulk_create(objs,**kwargs)
		for user in objs:
			fs_add_phone_user(sender=UserVariable, instance=user, created=True)

class UserVariable(models.Model):
	""" This table will store the additional information of the users """
	AGENT_TYPE = (
			('uuid-standby', 'uuid-standby'),
			('callback', 'callback'),
			)
	AGENT_STATUS_CHOICES = (
			('Logged Out', 'Logged Out'),
			('Available', 'Available'),
			('Available (On Demand)', 'Available (On Demand)'),
			)
	user    = models.OneToOneField(User, null=True,
			on_delete=models.CASCADE, blank=True,
			editable=False, related_name='properties')
	extension = models.CharField(db_index=True, max_length=100, unique=True,
					 help_text='sip extension')
	wfh_numeric = models.BigIntegerField(default=None,blank=True, null=True, unique=True,
			help_text='wfh numeric')
	wfh_password = models.CharField(max_length=50,blank=True,null=True,
		help_text="wfh password")
	device_pass = models.CharField(default=1234, max_length=100, db_index=True,
			help_text='Phone password')
	level       = models.IntegerField(default=1, db_index=True , null = True,
			help_text='Mapping an agent to a campaign')
	position    = models.IntegerField(default=1, db_index=True,
			help_text='Position in campaign')
	domain = models.ForeignKey(Switch, related_name='user_switch',
			null=True, on_delete=models.SET_NULL, blank=True)
	type        = models.CharField(default='uuid-standby',
			choices=AGENT_TYPE, max_length=100,
			help_text='We currently support 2 types, callback and uuid-standby.'\
			'callback will try to reach the agent via the contact fields value.'\
			'uuid-standby will try to directly bridge the call using the agent uuid')
	contact     = models.CharField(default='[call_timeout=10]user',
			max_length=100, help_text='A simple dial string can be put in here, '\
					'like: user/1000@default')
	dial_status      = models.CharField(default='Logged Out',
			choices=AGENT_STATUS_CHOICES, max_length=100,\
			help_text='Define the current status of an agent.\
			Check the Agents Status table for more informations')
	max_no_answer   = models.IntegerField(default=3, db_index=True,
			help_text='If the agent reach this number of consecutive no answer,'\
			'his status is changed to On Break automatically')
	wrap_up_time    = models.IntegerField(default=10, db_index=True,
			help_text='Allow an agent to have a delay when\
			finishing a call before receiving another one')
	reject_delay_time   = models.IntegerField(default=10, db_index=True,
			help_text='If the agent press the reject on their phone,\
			we wait this defined time amount')
	busy_delay_time = models.IntegerField(default=60, db_index=True,
			help_text='If the agent is on do not disturb,\
			we wait this defined time before trying him again')
	protocol      = models.CharField(default=PROTOCOL_CHOICES[0][0],
			choices=PROTOCOL_CHOICES, max_length=30)
	created_date = models.DateTimeField(auto_now_add=True,db_index=True)
	modified_date = models.DateTimeField(auto_now=True)
	enabled = models.DateTimeField(null=True, blank=True, db_index=True)
	w_req_callback = models.BooleanField(default=False,null=True, blank=True)
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
			on_delete=models.SET_NULL,null=True)
	objects = UserVariableManager()

	def __str__(self):
		return self.extension
	@property
	def campaign(self):
		return Campaign.objects.all()	

	class Meta:
		ordering = ('created_date',)

signals.post_save.connect(fs_add_user, sender=UserVariable)
signals.pre_delete.connect(fs_del_user, sender=UserVariable)

class CampaignSchedule(models.Model):
	""" This table will store the shift timing """
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
			on_delete=models.SET_NULL,null=True)	
	name = models.CharField(max_length = 100, db_index=True, unique=True)
	description = models.TextField(blank=True, null=True)
	schedule_days = models.CharField(default=SCHEDULE_DAYS[0][0], choices=SCHEDULE_DAYS, max_length=10)
	schedule = JSONField()
	status = models.CharField(default='Active',choices=Status, max_length=10)
	created_date = models.DateTimeField(auto_now_add=True)
	modified_date = models.DateTimeField(auto_now=True)
	created_by = models.ForeignKey(User, related_name='campaign_schedule_created_by',on_delete=models.SET_NULL,
		blank=True, null=True)
	def __str__(self):
		return self.name

class AudioFile(models.Model):
	""" This table will store the audio file information """	
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
			on_delete=models.SET_NULL,null=True)	
	name = models.CharField(max_length = 100, db_index=True, unique=True)
	description = models.TextField(blank=True, null=True)
	audio_file = models.FileField(upload_to='upload', blank=True)
	status = models.CharField(default='Active',choices=Status, max_length=10)
	created_date = models.DateTimeField(auto_now_add=True)
	modified_date = models.DateTimeField(auto_now=True)
	created_by = models.ForeignKey(User, related_name='audio_created_by',on_delete=models.SET_NULL,
		blank=True, null=True)
	
	def __str__(self):
		return self.name

	@property
	def audio_file_name(self):
		if self.audio_file:
			return os.path.basename(self.audio_file.name)

class Disposition(models.Model):
	""" This table will store the dispostion infomation """
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
			on_delete=models.SET_NULL,null=True)
	name = models.CharField(max_length= 50, db_index=True)
	dispos = JSONField()
	dispo_type = models.CharField(default='dropdown',choices=DISPO_FIELD_TYPE,max_length=10)
	dispo_keys = JSONField(default=list)
	status = models.CharField(default='Active',choices=Status, max_length=10)
	color_code = models.CharField(null=True, blank=True, max_length=10, default='#3a3f51')
	deleted_date = models.DateTimeField(blank=True,null=True)
	deleted_by = models.CharField(blank=True,null=True,max_length=150)
	created_date = models.DateTimeField(auto_now_add=True)
	modified_date = models.DateTimeField(auto_now=True)
	show_dispo = models.CharField(default='0', choices=SHOW_DISPOS_TYPE, max_length=2)
	created_by = models.ForeignKey(User, related_name='disposition_created_by',on_delete=models.SET_NULL,
		blank=True, null=True)
	updatelead = models.BooleanField(default=False)
	
	def __str__(self):
		return self.name

class RelationTag(models.Model):
	""" This table will store the relationship tag information """
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
			on_delete=models.SET_NULL,null=True)
	name = models.CharField(max_length= 50, db_index=True, unique=True)
	relation_fields = JSONField()
	relation_type = models.CharField(default='dropdown',choices=DISPO_FIELD_TYPE,max_length=10)
	status = models.CharField(default='Active',choices=Status, max_length=10)
	color_code = models.CharField(null=True, blank=True, max_length=10, default='#3a3f51')
	created_date = models.DateTimeField(auto_now_add=True)
	modified_date = models.DateTimeField(auto_now=True)
	created_by = models.ForeignKey(User, related_name='relationtag_created_by',on_delete=models.SET_NULL,
		blank=True, null=True)
	
	def __str__(self):
		return self.name

class PauseBreak(models.Model):
	""" This table will store the break time and other information """
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
			on_delete=models.SET_NULL,null=True)	
	name = models.CharField(max_length= 200, db_index=True, unique=True)
	status = models.CharField(default='Active',choices=Status, max_length=10)
	break_time = models.TimeField(blank=True, null=True)
	break_color_code = models.CharField(null=True, blank=True, max_length=10, default="#3a3f51")
	inactive_on_exceed  = models.BooleanField(default=True)
	created_date = models.DateTimeField(auto_now_add=True)
	modified_date = models.DateTimeField(auto_now=True)
	created_by = models.ForeignKey(User, related_name='pausebreak_created_by',on_delete=models.SET_NULL,
		blank=True, null=True)

	def __str__(self):
		return self.name
	
	class Meta:
		ordering = ['-id']

class CSS(models.Model):
	""" This table will store the Css Query and other information """
	name = models.CharField(max_length=30, null=True,unique=True)
	campaign = models.CharField(max_length=50, null=True)
	status = models.CharField(default='Active', choices=Status, max_length=10)
	raw_query = JSONField(default=list)
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)
	class Meta:
		get_latest_by = '-created'
		ordering = ['-created']
	def __str__(self):
		return str(self.name)

class SkilledRouting(models.Model):
	""" This table will store the Skill Routing and other information """
	name =  models.CharField(max_length=100,null=True)
	skill_id = JSONField(default=dict)
	skills = JSONField(default=dict)
	schedule = models.ForeignKey(CampaignSchedule,
			null=True, on_delete=models.SET_NULL, blank=True)
	skill_popup = models.BooleanField(default=False)
	d_abandoned_camp = models.CharField(max_length=100,null=True) 
	audio = JSONField(default=dict)
	status = models.CharField(default='Active', choices=Status, max_length=10)
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)
	class Meta:
		get_latest_by ='-created'
		ordering =['-created']
	def __str__(self):
		return str(self.name)

class SMSTemplate(models.Model):
	""" This table will store the Sms Templates information """
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
			on_delete=models.SET_NULL,null=True)	
	name = models.CharField(max_length = 50, unique=True)
	campaign = models.ForeignKey('Campaign',on_delete=models.SET_NULL,null=True,blank=True, related_name='template_campaign')
	text = models.TextField(null=True, blank=True)
	status = models.CharField(default='Active', choices=Status, max_length=10)
	template_type = models.CharField(default='0',choices=TEMPLATE_TYPE, max_length=2)
	created_date = models.DateTimeField(auto_now_add=True)
	modified_date = models.DateTimeField(auto_now=True)
	created_by = models.ForeignKey('User', related_name='template_created_by',on_delete=models.SET_NULL,
		blank=True, null=True)
	def __str__(self):
		return self.name
	class Meta:
		ordering =['-id']

class SMSGateway(models.Model):
	""" This table will store the Sms credentials gateway  information """
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
			on_delete=models.SET_NULL,null=True)	
	name = models.CharField(max_length = 50, unique=True)
	key = models.CharField(max_length = 1032, null=True)
	gateway_url = models.URLField(max_length = 200) 
	disposition = models.ManyToManyField(Disposition, blank=True)
	template = models.ManyToManyField(SMSTemplate, blank=True)
	status = models.CharField(default='Active', choices=Status, max_length=10)
	sms_trigger_on = models.CharField(default='2',choices=TRIGGER_ACTIONS, max_length=2)
	created_date = models.DateTimeField(auto_now_add=True)
	modified_date = models.DateTimeField(auto_now=True)
	created_by = models.ForeignKey('User', related_name='gateway_created_by',on_delete=models.SET_NULL,
		blank=True, null=True)
	def __str__(self):
		return self.name
	class Meta:
		ordering =['-id']

class EmailTemplate(models.Model):
	""" This table will store the Email Templates information """
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
			on_delete=models.SET_NULL,null=True)	
	name = models.CharField(max_length = 100, unique=True)
	campaign = models.ManyToManyField('Campaign', related_name='email_campaign',
			null=True, blank=True)
	email_subject = models.CharField(default='', max_length=255)
	email_body = models.TextField(null=True, blank=True)
	status = models.CharField(default='Active',choices=Status, max_length=10)
	created_date = models.DateTimeField(auto_now_add=True)
	modified_date = models.DateTimeField(auto_now=True)
	created_by = models.ForeignKey('User', related_name='email_created_by',on_delete=models.SET_NULL,
		blank=True, null=True)

	def __str__(self):
		return self.name

class EmailGateway(models.Model):
	""" This table will store the Email Credentails gateway information """
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
			on_delete=models.SET_NULL,null=True)	
	name = models.CharField(max_length = 50, unique=True)
	email_host = models.CharField(max_length = 1032)
	email_port = models.IntegerField()
	default_email = models.CharField(max_length = 1032, blank=True, null=True)
	default_email_password = models.CharField(max_length=50,blank=True,null=True)
	disposition = models.ManyToManyField(Disposition, blank=True)
	template = models.ManyToManyField(EmailTemplate, blank=True)
	status = models.CharField(default='Active', choices=Status, max_length=10)
	email_trigger_on = models.CharField(default='2',choices=TRIGGER_ACTIONS, max_length=2)
	created_date = models.DateTimeField(auto_now_add=True)
	modified_date = models.DateTimeField(auto_now=True)
	created_by = models.ForeignKey('User', related_name='emailgateway_created_by',on_delete=models.SET_NULL,
		blank=True, null=True)
	def __str__(self):
		return self.name
	class Meta:
		ordering =['-id']

class DialTrunkPriority(models.Model):
	""" 
	This table stores the mutiple trunks info and 
	will pick on priority will dialing the calling
	"""
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
			on_delete=models.SET_NULL,null=True)	
	priority = models.IntegerField(default=0, db_index=True, blank=True)	
	trunk = models.ForeignKey(DialTrunk, related_name='priority_trunk',
			null=True, blank=True, on_delete=models.CASCADE)
	did = JSONField(default=dict)
	created_date = models.DateTimeField(auto_now=True)
	def __str__(self):
		return self.trunk.name
	class Meta:
		ordering =['id']

class DiaTrunkGroup(models.Model):
	""" this table stores the dial trunk group information  """
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
			on_delete=models.SET_NULL,null=True)	
	name = models.CharField(max_length = 50, unique=True)
	trunks =  models.ManyToManyField(DialTrunkPriority, blank=True)
	total_channel_count = models.IntegerField(default=0, db_index=True, blank=True)
	status = models.CharField(default='Active', choices=Status, max_length=10)
	created_date = models.DateTimeField(auto_now=True)
	created_by = models.ForeignKey(User, related_name='trunk_group_created_by',on_delete=models.SET_NULL,
		blank=True, null=True)
	def __str__(self):
		return self.name
	class Meta:
		ordering =['-id']

class Campaign(models.Model):
	""" This table stores all the campaign related info """
	name = models.CharField(max_length=100,db_index=True)
	slug = models.SlugField(max_length=100, unique=True)
	description = models.TextField(blank=True, null=True)
	users = models.ManyToManyField(User, related_name='campaign_users', null=True, blank=True)
	group = models.ManyToManyField(Group, blank=True)
	schedule = models.ForeignKey(CampaignSchedule, related_name='campaign_schedule',
			null=True, on_delete=models.SET_NULL, blank=True)
	breaks = models.ManyToManyField(PauseBreak, null=True, blank=True)
	disposition = models.ManyToManyField(Disposition, blank=True, null=True)
	relation_tag = models.ManyToManyField(RelationTag, blank=True, null=True)
	dial_method = JSONField()
	wfh_dispo = JSONField(default=dict)
	transfer = models.BooleanField(default=False)
	conference = models.BooleanField(default=False)
	search_alternate = models.BooleanField(default=False)
	callback_mode = models.CharField(default='self',choices=CALLBACK_MODE, max_length=20)
	callback_threshold = models.IntegerField(default=0, db_index=True, blank=True)
	queued_busy_callback = models.CharField(max_length=10, null=True,blank=True)
	dnc = models.CharField(default='local',choices=DNC_MODE, max_length=20)
	show_queue_call_count = models.BooleanField(default=False)
	hopper_level = models.BigIntegerField(default='100')
	portifolio = models.BooleanField(default=False, blank=True, null=True)
	css = models.BooleanField(default=False, blank=True,null=True)
	wfh = models.BooleanField(default=False, blank=True,null=True)
	wfh_request_call = models.BooleanField(default=False, blank=True,null=True)
	auto_qcb_dial = models.BooleanField(default=False, blank=True, null=True)
	auto_ac_dial = models.BooleanField(default=False, blank=True, null=True)
	switch = models.ForeignKey(Switch, related_name='campaign_switch',
			null=True, on_delete=models.SET_NULL, blank=True)
	trunk = models.ForeignKey(DialTrunk, related_name='trunk',
			null=True, blank=True, on_delete=models.SET_NULL)
	trunk_group = models.ForeignKey(DiaTrunkGroup, related_name='trunk_group',
			null=True, blank=True, on_delete=models.SET_NULL)
	is_trunk_group = models.BooleanField(default=False,null=True, blank=True)
	trunk_did = JSONField(default=dict)
	status = models.CharField(default='Active',choices=Status,db_index=True,max_length=10)
	created_date = models.DateTimeField(auto_now_add=True)
	modified_date = models.DateTimeField(auto_now=True)
	lead_priotize = JSONField(default=dict)
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
			on_delete=models.SET_NULL,null=True)
	auto_feedback = models.BooleanField(null=True, blank=True)
	auto_feedback_time = models.CharField(max_length=20,blank=True, null=True)
	created_by = models.ForeignKey(User, related_name='campaign_created_by',on_delete=models.SET_NULL,
		blank=True, null=True)
	auto_progressive_time = models.CharField(max_length=20, blank=True, null=True)
	inbound_threshold = models.IntegerField(default=0, db_index=True, blank=True)
	sms_gateway = models.ForeignKey(SMSGateway,on_delete=models.SET_NULL,blank=True, null=True)
	email_gateway = models.ForeignKey(EmailGateway,on_delete=models.SET_NULL, blank=True, null=True)
	all_caller_id = JSONField(default=dict)

	class Meta:
		get_latest_by = 'modified_date'
		ordering = ['-id']

	@property
	def group_list(self):
		return ", ".join(self.group.all().values_list("name", flat=True))

	@property
	def transfer_list(self):
		return self.transfer.split(",")

	@property
	def dispo_list(self):
		return ", ".join(self.disposition.all().values_list("name", flat=True))

	@property
	def extension(self):
		if self.campaignvariable_set.all():
			return self.campaignvariable_set.all()[0].extension
		return None

	@property
	def caller_id(self):
		if self.campaignvariable_set.all():
			return self.campaignvariable_set.all()[0].caller_id
		return None

	@property
	def prefix(self):
		if self.campaignvariable_set.all():
			return self.campaignvariable_set.all()[0].prefix
		return ""
	
	@property
	def campaign_script(self):
		return ", ".join(self.script.all().values_list("id", flat=True))
		
	@property
	def campaign_variable(self):
		return CampaignVariable.objects.get(campaign=self)	

	def __str__(self):
		return self.name or self.slug 	

	def save(self, *args, **kwargs):
		super().save(*args, **kwargs)
		from crm.models import CampaignInfo
		camp_info = CampaignInfo.objects.filter(id=self.id)
		if camp_info.exists():
			camp_info.update(name=self.name)
		else:
			CampaignInfo.objects.create(id=self.id, name=self.name)
		if not PhonebookBucketCampaign.objects.filter(id=self.id).exists():
			PhonebookBucketCampaign.objects.create(id=self.id)

class CampaignVariable(models.Model):
	""" This table stores the addational information of the campaign """
	campaign = models.ForeignKey(Campaign,on_delete=models.CASCADE,null=True,blank=True)
	extension = models.BigIntegerField(db_index=True, unique=True,
			help_text='Campaign DID')
	prefix = models.CharField(max_length=30,null=True,blank=True,
			help_text='The prefix is for match to the DID')
	caller_id = models.CharField(max_length=100,blank=True, null=True)
	wfh_caller_id = models.CharField(max_length=100,blank=True, null=True)
	strategy = models.CharField(max_length=100,
			default='longest-idle-agent',
			choices=CAMPAIGN_STRATEGY_CHOICES,
			help_text='The strategy defines how calls are distributed '\
					'in a queue. A table of different strategies can be found below'
			)
	dial_ratio = models.FloatField(default=1, choices=DIAL_RATIO_CHOICES,
			help_text='Calls thrown per agent')
	variables = models.TextField(default='originate_timeout=25', null=False,
								   help_text='Use to set channel variables,'
											 ' separate them with comma and'
											 ' do not use any space')
	ndnc_scrub = models.BooleanField(default=False, help_text='Scrub NDNC'\
			' numbers on the fly')
	moh_sound = models.ForeignKey(AudioFile, related_name='AudioFile'
				,on_delete=models.SET_NULL,help_text='The system will playback whatever you specify to '\
				'incoming calls or Hold', blank=True, null=True)
	hold_music = models.ForeignKey(AudioFile, related_name='hold_music'
				,on_delete=models.SET_NULL,help_text='The system will play this when you put'\
				'calls on hold', blank=True, null=True)
	record_template = models.CharField(
			default='default',
			max_length=255,
			verbose_name='Recording Directory',
			help_text='Use the record-directory to save your campaign '\
					'recording on specific directory'
			)
	time_base_score = models.CharField(default='system', max_length=100,
			help_text='This can be either queue or system '\
					'(system is the default).')
	max_wait_time = models.IntegerField(default=0, db_index=True,
			help_text='Default to 0 to be disabled. Any value are in seconds,'\
					'and will define the delay before we quit the callcenter '\
					'application IF the member have not been answered by an agent')
	max_wait_time_with_no_agent = models.IntegerField(
			default=0, db_index=True, help_text='Default to 0 to be disabled.'\
					'Any value are in seconds, and will define the length of' \
					'time a queue be empty of available (on a call or not) '\
					'before we disconnect members')
	max_wait_time_with_no_agent_time_reached = models.IntegerField(
			default=5, db_index=True, help_text='Default to 5. Any value are '\
					'in seconds, and will define the length of time after the'\
					'max-wait-time-with-no-agent is reached to reject new '\
					'caller.')
	tier_rules_apply = models.BooleanField(default=False,
			help_text='Can be True or False. This defines if we should apply '\
					'the following tier rules when a caller advances through '\
					'a queues tiers. If False, they will use all tiers with '\
					'no wait')
	tier_rule_wait_second = models.IntegerField(default=100, db_index=True,
			help_text='The time in seconds that a caller is required\
					to wait before advancing to the next tier')
	tier_rule_wait_multiply_level = models.BooleanField(default=False, help_text='Can '\
			'be True or False. If False, then once tier-rule-wait-second is '\
			'passed, the caller is offered to all tiers in order '\
			'(level/position)')
	tier_rule_no_agent_no_wait = models.BooleanField(default=False,
			help_text='Can be True or False. If True, callers will skip '\
					'tiers that don\'t have agents available')
	discard_abandoned_after = models.IntegerField(default=100, db_index=True,
			help_text='The number of seconds before we completely remove an '\
					'abandoned member from the queue')
	abandoned_resume_allowed = models.BooleanField(default=False,
			help_text='Can be True or False. If True, a caller who has '\
					'abandoned the queue '\
					'can re-enter and resume their previous position in '\
					'that queue')
	dialtimeout = models.CharField(max_length=25, blank=True, null=True)

signals.post_save.connect(fs_campaign, sender=CampaignVariable)
signals.pre_delete.connect(fs_del_campaign, sender=Campaign)
signals.m2m_changed.connect(fs_group_campaign, sender=Campaign.group.through)
signals.m2m_changed.connect(fs_user_campaign, sender=Campaign.users.through)

class CampaignPriority(models.Model):
	""" This table store the campaign information for ingroup campaings """
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
			on_delete=models.SET_NULL,null=True)	
	priority = models.IntegerField(default=0, db_index=True, blank=True)	
	campaign = models.ForeignKey(Campaign, related_name='priority_campaign',
			null=True, blank=True, on_delete=models.CASCADE)
	created_date = models.DateTimeField(auto_now=True)
	def __str__(self):
		return self.campaign.name
	class Meta:
		ordering =['id']

class InGroupCampaign(models.Model):
	""" This table store the inbound functionality of the campaign """
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
			on_delete=models.SET_NULL,null=True)	
	name = models.CharField(max_length = 100, db_index=True, unique=True)
	caller_id =JSONField(default=dict)
	strategy = models.CharField(default='0',choices=STRATEGY_CHOICES, max_length=10)
	ingroup_campaign =  models.ManyToManyField(CampaignPriority, related_name="ingroup_campaign",
				null=True,blank=True)
	status = models.CharField(default='Active',choices=Status, max_length=10)
	created_date = models.DateTimeField(auto_now_add=True)
	created_by = models.ForeignKey('User', related_name='ingroup_created_by',on_delete=models.SET_NULL,
		blank=True, null=True)
	def __str__(self):
		return self.name

class Script(models.Model):
	""" This table sotre the script info"""
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
			on_delete=models.SET_NULL,null=True)	
	name = models.CharField(max_length = 100, db_index=True, unique=True)
	campaign = models.ForeignKey(Campaign,on_delete=models.SET_NULL,null=True,blank=True)
	text = models.TextField(null=True, blank=True)
	status = models.CharField(default='Active',choices=Status, max_length=10)
	created_date = models.DateTimeField(auto_now_add=True)
	modified_date = models.DateTimeField(auto_now=True)
	created_by = models.ForeignKey('User', related_name='script_created_by',on_delete=models.SET_NULL,
		blank=True, null=True)

	def __str__(self):
		return self.name

class Modules(models.Model):
	""" This table stores the newly created module/pages dynmaically """
	name = models.CharField(max_length=50,unique=True)
	title = models.CharField(max_length=50, default='')
	icon = models.CharField(max_length=50, default='fa-file-contract', null=True)
	url_abbr = models.CharField(max_length=10, default='', null=True) ### abbr = abbrevarion
	parent = models.ForeignKey("self", related_name='parent_menu', null=True, blank=True, on_delete=models.SET_NULL)
	status = models.CharField(default='Active',choices=Status, max_length=10)
	sequence = models.IntegerField(default=1)
	permissions = models.CharField(max_length=100, db_index=True, default="C,R,U,D")
	created_date = models.DateTimeField(auto_now_add=True)
	modified_date = models.DateTimeField(auto_now=True)
	is_menu = models.BooleanField(default=True)

	@property
	def permission_list(self):
		return self.permissions.split(",")

	def __str__(self):
		return self.name

class LeadRecycle(models.Model):
	""" This table stores the lead recycle information defined in campaign"""
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
			on_delete=models.SET_NULL,null=True)
	campaign = models.ForeignKey(Campaign,on_delete=models.SET_NULL,null=True)
	name = models.CharField(max_length=150, db_index=True)
	schedule_period = JSONField(blank=True, null=True)
	recycle_time = models.BigIntegerField(default=0)
	count = models.IntegerField(default=0)
	status = models.CharField(default='Active',choices=Status, max_length=10)
	schedule_type = models.CharField(choices=SCHEDULE_TYPE, max_length=15, null=True, blank=True)
	ldr_period_update=models.DateField(auto_now_add=True, null=True, blank=True)
	created_date = models.DateTimeField(auto_now_add=True)
	modified_date = models.DateTimeField(auto_now=True)
	def __str__(self):
		return self.name

# signals.pre_delete.connect(aps_leadrecycle_del, sender=LeadRecycle)
# signals.post_save.connect(aps_leadrecycle_add, sender=LeadRecycle)

class CallDetail(models.Model):
	"""
	This table is for storing the calldetail logs with agent feedback.
	"""
	site = models.ForeignKey(Site, default=settings.SITE_ID, 
			on_delete=models.SET_NULL,null=True,related_name='CallDetail')
	campaign = models.ForeignKey(Campaign,on_delete=models.SET_NULL,null=True,db_index=True)
	campaign_name = models.CharField(default='', max_length=50,null=True,db_index=True)
	user = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,db_index=True)
	phonebook = models.CharField(default='',max_length=50,  null=True) 
	contact_id = models.BigIntegerField(blank=True, null=True, db_index=True)
	customer_cid = models.CharField(default='', max_length=50,null=True,db_index=True)
	callflow = models.CharField(default='', max_length=50, null=True)
	callmode = models.CharField(default='', max_length=50, null=True)
	destination_extension = models.CharField(default='', max_length=50, null=True)
	dialed_status = models.CharField(default='',choices=auto_dialed_status, max_length=50,db_index=True)
	session_uuid = models.UUIDField(db_index=True,  null=True)
	a_leg_uuid = models.UUIDField(null=True)
	b_leg_uuid = models.UUIDField(null=True)
	predictive_time = models.TimeField(default=default_time, null=True, blank=True)
	progressive_time = models.TimeField(default=default_time, null=True, blank=True)
	preview_time = models.TimeField(default=default_time, null=True, blank=True)
	init_time = models.DateTimeField(null=True, blank=True, default=None)
	ring_time = models.DateTimeField(default=None, null=True, blank=True)
	ring_duration = models.TimeField(default=default_time, null=True, blank=True)
	connect_time = models.DateTimeField(default=None,  null=True, blank=True)
	wait_time = models.TimeField(default=default_time, null=True, blank=True)
	predictive_wait_time = models.TimeField(default=default_time, null=True, blank=True)
	hold_time =models.TimeField(default=default_time,null=True, blank=True)
	media_time = models.TimeField(default=default_time,null=True, blank=True)
	bill_sec = models.TimeField(default=default_time,null=True, blank=True, verbose_name="Talk Time")
	ivr_duration = models.TimeField(default=default_time,null=True, blank=True)
	call_duration = models.TimeField(default=default_time, null=True, blank=True)
	feedback_time = models.TimeField(default=default_time, null=True, blank=True, verbose_name="Wrap-Up Time")
	cfc_number = models.CharField(max_length=50, null=True, blank=True, verbose_name='conference_numbers')
	internal_tc_number = models.CharField(max_length=50, null=True, blank=True, verbose_name='internal transfer number')
	external_tc_number = models.CharField(max_length=50, null=True, blank=True, verbose_name='external transfer number')
	hangup_time = models.DateTimeField(default=None, null=True, blank=True)
	hangup_source = models.CharField(default='', max_length=100, null=True)
	hangup_cause = models.CharField(default='', max_length=100, null=True)
	hangup_cause_code = models.IntegerField(default=None, null=True, blank=True)
	inbound_time = models.TimeField(default=default_time, null=True, blank=True)
	inbound_wait_time = models.TimeField(default=default_time, null=True, blank=True)
	blended_time = models.TimeField(default=default_time, blank=True, null=True)
	blended_wait_time = models.TimeField(default=default_time, blank=True, null=True)
	uniqueid = models.CharField(default=None, max_length=30, null=True,db_index=True)			
	created = models.DateTimeField(auto_now_add=True, db_index=True)
	updated = models.DateTimeField(auto_now=True, db_index=True)

	class Meta:
		get_latest_by = 'created'
		ordering = ['-created']

	def __str__(self):
		return "%s" % self.session_uuid

	def get_details(self):
		if re.search('\\^',self.info):
			return re.sub(r'(\\)', '', self.info).split('^')
		else:
			return ['']*6

	def diallereventlog(self):
		if DiallerEventLog.objects.filter(session_uuid=self.session_uuid).exists():
			return DiallerEventLog.objects.filter(session_uuid=self.session_uuid)[0]
		return self

class DiallerEventLog(models.Model):
	"""
	This table is for storing the calldetail logs get from freeswitch \
	events through event socket.
	"""
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
			on_delete=models.SET_NULL,null=True,related_name='DiallerEventLog')
	campaign = models.ForeignKey(Campaign,on_delete=models.SET_NULL,null=True)
	campaign_name = models.CharField(default='', max_length=50,null=True)
	user = models.ForeignKey(User,on_delete=models.SET_NULL,null=True)
	phonebook = models.CharField(default='',max_length=50, editable=False, null=True) 
	contact_id = models.BigIntegerField(blank=True, null=True, db_index=True)
	session_uuid = models.UUIDField(db_index=True, editable=False, null=True)
	a_leg_uuid = models.UUIDField(editable=False, null=True)
	b_leg_uuid = models.UUIDField(editable=False, null=True)
	init_time = models.DateTimeField(editable=False,null=True, blank=True, default=None,db_index=True)
	ring_time = models.DateTimeField(default=None, editable=False,	null=True, blank=True)
	ring_duration = models.TimeField(default=default_time, null=True, blank=True)
	connect_time = models.DateTimeField(default=None, editable=False, null=True, blank=True)
	wait_time = models.TimeField(default=default_time, editable=False, null=True, blank=True)
	hold_time = models.TimeField(default=default_time, editable=False, null=True, blank=True)
	media_time = models.TimeField(default=default_time, editable=False, null=True, blank=True)
	callflow = models.CharField(default='', max_length=50, editable=False, null=True)
	callmode = models.CharField(default='', max_length=50, null=True)
	customer_cid = models.CharField(default='', max_length=50, editable=False, null=True)
	destination_extension = models.CharField(default='', max_length=50, editable=False, null=True)
	transfer_history = models.TextField(default='', editable=False, null=True)
	call_duration = models.TimeField(default=default_time, editable=False, null=True, blank=True)
	bill_sec = models.TimeField(default=default_time, editable=False, null=True, blank=True, verbose_name="Talk Time")
	ivr_duration = models.TimeField(default=default_time,null=True, blank=True)
	hangup_time = models.DateTimeField(default=None, editable=False, null=True, blank=True)
	dialed_status = models.CharField(default='',choices=auto_dialed_status, max_length=50)
	hangup_cause = models.CharField(default='', max_length=100, editable=False, null=True)
	hangup_cause_code = models.IntegerField(default=None, editable=False, null=True, blank=True)
	channel = models.TextField(default='', editable=False, null=True)
	info = models.TextField(default='', editable=False, null=True)
	uniqueid = models.CharField(default=None, max_length=30, null=True)
	created = models.DateTimeField(auto_now_add=True, db_index=True, editable=False)
	updated = models.DateTimeField(auto_now=True, db_index=True, editable=False)
	objects = models.Manager()

	class Meta:
		get_latest_by = 'init_time'
		ordering = ['-init_time']

	def __str__(self):
		return "%s" % self.session_uuid

	def get_details(self):
		if re.search('\\^',self.info):
			return re.sub(r'(\\)', '', self.info).split('^')
		else:
			return ['']*6

	
		
class CdrFeedbck(models.Model):
	"""
	This model is used to store feedback submitted on hangup
	"""

	primary_dispo = models.CharField(default='', max_length=250, null=True,db_index=True)
	feedback = JSONField()
	relation_tag = JSONField()
	calldetail = models.OneToOneField(CallDetail, related_name='cdrfeedback', on_delete=models.CASCADE, null=True,db_index=True)
	session_uuid = models.UUIDField(db_index=True, editable=False, null=True)
	contact_id = models.BigIntegerField(blank=True, null=True, db_index=True)
	comment = models.TextField(blank=True, null=True) 

	class Meta:
		get_latest_by = 'session_uuid'
		ordering = ['-session_uuid']

class Cdr(models.Model):
	"""
	This table is for storing the cdr logs directly from freeswitch.
	"""
	local_ip_v4 = models.CharField(default='', editable=False,
			null=True, max_length=50)
	caller_id_name = models.CharField(default='', editable=False,
			null=True, max_length=50)
	caller_id_number = models.CharField(default='', editable=False,
			null=True, max_length=50)
	destination_number = models.CharField(default='', editable=False,
			null=True, max_length=50)
	context = models.CharField(default='', editable=False, null=True,
			max_length=50)
	start_stamp = models.CharField(default='', editable=False,
			null=True, max_length=50)
	answer_stamp = models.CharField(default='', editable=False,
			null=True, max_length=50)
	end_stamp = models.CharField(default='', editable=False,
			null=True, max_length=50)
	duration = models.CharField(default='', editable=False,
			null=True, max_length=50)
	billsec = models.CharField(default='', editable=False,
			null=True, max_length=50)
	hangup_cause = models.CharField(default='', editable=False,
			null=True, max_length=50)
	uuid = models.CharField(default='', editable=False,
			null=True, max_length=50)
	bleg_uuid = models.CharField(default='', editable=False,
			null=True, max_length=50)
	accountcode = models.CharField(default='', editable=False,
			null=True, max_length=50)
	read_codec = models.CharField(default='', editable=False,
			null=True, max_length=50)
	write_codec = models.CharField(default='', editable=False,
			null=True, max_length=50)

	def __str__(self):
		return "%s" % self.uuid

class NdncDeltaUpload(models.Model):
	""" this model sores the NDN contacts file defined by TRAI"""
	delta_file = models.FileField(upload_to='ndnc')
	created = models.DateTimeField(auto_now_add=True, db_index=True)
	updated = models.DateTimeField(auto_now=True, db_index=True)

	@property
	def delta_file_name(self):
		if self.delta_file:
			return os.path.basename(self.delta_file.name)
		else:
			return ""

	class Meta:
		get_latest_by = '-created'
		ordering = ['-created']

	def __str__(self):
		return "%s" % self.delta_file

class AgentActivitybk(models.Model):
	username = models.CharField(max_length=50,default='',db_index=True)
	full_name = models.CharField(max_length=150,default='')
	supervisor_name = models.CharField(max_length=150,default='')
	campaign     =  models.CharField(max_length=150,default='',db_index=True)
	app_idle_time = models.TimeField(default=default_time, blank=True, null=True)
	dialer_idle_time = models.TimeField(default=default_time, blank=True, null=True)
	pause_progressive_time = models.TimeField(default=default_time, blank=True, null=True)
	progressive_time = models.TimeField(default=default_time, blank=True, null=True)
	preview_time = models.TimeField(default=default_time, blank=True, null=True)
	predictive_wait_time = models.TimeField(default=default_time, blank=True, null=True)
	inbound_wait_time = models.TimeField(default=default_time, blank=True, null=True)
	blended_wait_time = models.TimeField(default=default_time, blank=True, null=True)
	ring_duration = models.TimeField(default=default_time, blank=True, null=True)
	ring_duration_avg = models.CharField(max_length=255, blank=True, null=True)
	hold_time = models.TimeField(default=default_time, blank=True, null=True)
	media_time = models.TimeField(default=default_time, blank=True, null=True)
	predictive_wait_time_avg = models.CharField(max_length=255, blank=True, null=True)
	talk = models.CharField(max_length=255, blank=True, null=True)
	talk_avg = models.CharField(max_length=255, blank=True, null=True)
	bill_sec = models.CharField(max_length=255, blank=True, null=True)
	bill_sec_avg = models.CharField(max_length=255, blank=True, null=True)
	call_duration = models.CharField(max_length=255, blank=True, null=True)
	feedback_time = models.TimeField(default=default_time, blank=True, null=True)
	feedback_time_avg = models.CharField(max_length=150,default='')
	break_time = models.TimeField(default=default_time, blank=True, null=True)
	break_time_avg = models.CharField(max_length=150,default='')
	app_login_time = models.TimeField(default=default_time, blank=True, null=True)
	tea_break = models.CharField(max_length=150,default='')
	lunch_break = models.CharField(max_length=150,default='')
	breakfast_break = models.CharField(max_length=150,default='')
	meeting = models.CharField(max_length=150,default='')
	dinner_break = models.CharField(max_length=150,default='')
	dialer_login_time = models.CharField(max_length=150,default='')
	total_login_time = models.CharField(max_length=150,default='')
	first_login_time = models.CharField(max_length=150,default='')
	last_logout_time = models.CharField(max_length=150,default='')
	total_calls = models.CharField(max_length=150,default='')
	total_unique_connected_calls = models.CharField(max_length=150,db_index=True, default=None, null=True)
	date = models.DateField(auto_now_add=False, db_index=True,default=None,null=True)


class AgentActivity(models.Model):
	""" This table stores the every agents activity performed while login onwards"""
	user = models.ForeignKey(User, on_delete=models.SET_NULL,db_index=True, null=True)
	event = models.CharField(max_length=255, blank=True, null=True)
	event_time = models.DateTimeField(blank=True, null=True,db_index=True)
	tos = models.TimeField(default=default_time, blank=True, null=True)
	app_time = models.TimeField(default=default_time, blank=True, null=True)
	campaign_name = models.CharField(max_length=50, null=True, blank=True)
	dialer_time = models.TimeField(default=default_time, blank=True, null=True)
	wait_time = models.TimeField(default=default_time, blank=True, null=True, verbose_name='Wait Time')
	idle_time = models.TimeField(default=default_time, blank=True, null=True, verbose_name='Idle Time')
	media_time = models.TimeField(default=default_time, blank=True, null=True)
	spoke_time = models.TimeField(default=default_time, blank=True, null=True)
	preview_time = models.TimeField(default=default_time, blank=True, null=True)
	progressive_time = models.TimeField(default=default_time, blank=True, null=True)
	predictive_time = models.TimeField(default=default_time, blank=True, null=True)
	predictive_wait_time = models.TimeField(default=default_time, blank=True, null=True)
	feedback_time = models.TimeField(default=default_time, blank=True, null=True)
	break_type = models.CharField(default='',max_length=50, null=True, blank=True,db_index=True)
	break_time = models.TimeField(default=default_time, blank=True, null=True)
	created = models.DateTimeField(auto_now_add=True,db_index=True)
	hold_time = models.TimeField(default=default_time, blank=True, null=True)
	transfer_time = models.TimeField(default=default_time, blank=True, null=True)
	pause_progressive_time  = models.TimeField(default=default_time, blank=True, null=True,
		verbose_name='Pause Progressive Time')
	inbound_time = models.TimeField(default=default_time, blank=True, null=True)
	inbound_wait_time = models.TimeField(default=default_time, blank=True, null=True)	
	blended_time = models.TimeField(default=default_time, blank=True, null=True)
	blended_wait_time = models.TimeField(default=default_time, blank=True, null=True)
	class Meta:
		get_latest_by = '-event_time'
		ordering = ['-event_time']

	def __str__(self):
		return "%s" % self.user

class DNC(models.Model):
	"""
	This model is for storing the Dnc numbers.
	"""
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
			on_delete=models.CASCADE,null=True)
	campaign = models.ManyToManyField(Campaign, related_name="dnc_campaign",
				null=True,blank=True)
	phonebook = models.CharField(default='',max_length=50,)
	user = models.ForeignKey(User, on_delete=models.SET_NULL,related_name="dnc_user",null=True, blank=True)
	numeric  = models.CharField(default='', max_length=50,null=True, db_index=True)
	global_dnc = models.BooleanField(default=False)
	dnc_end_date = models.DateField(auto_now_add=False, db_index=True,default=None,null=True)
	uniqueid = models.CharField(default=None, max_length=30, null=True)			
	status = models.CharField(default='Active',choices=Status, max_length=10)
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)
	class Meta:
		get_latest_by = '-created'
		ordering = ['-created']

	@property
	def campaign_list(self):
		return ", ".join(self.campaign.all().values_list("name", flat=True))
		
	def __str__(self):
		return str(self.numeric)

class CallBackContact(models.Model):
	"""
	This model is for storing the customer contact data for dialler dialling purpose.
	"""
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
			on_delete=models.CASCADE,null=True)
	contact_id = models.BigIntegerField(null=True, blank=True, db_index=True)
	campaign = models.CharField(max_length=100,null=True, blank=True) 
	phonebook = models.CharField(max_length=100,null=True, blank=True)
	user = models.CharField(max_length=100,null=True)
	numeric  = models.CharField(default='', max_length=50,null=True, db_index=True)
	alt_numeric = HStoreField(default=dict)
	first_name	= models.CharField(default='', max_length=50)
	last_name	= models.CharField(default='', max_length=50)
	email	= models.EmailField(max_length=100,null=True, blank=True)
	callback_title = models.CharField(default='',max_length=100,null=True)
	status  = models.CharField(default=CONTACT_STATUS[0][0],choices=CONTACT_STATUS,db_index=True,max_length=15)
	dialcount = models.IntegerField(default=1)
	callback_type = models.CharField(default=CALLBACK_MODE[0][0],choices=CALLBACK_MODE,db_index=True,max_length=15)
	schedule_time = models.DateTimeField(null=True,blank=True,db_index=True)
	disposition = models.CharField(max_length=100,null=True,blank=True)
	comment =  models.CharField(default='', max_length=500, blank=True, null=True)
	customer_raw_data = JSONField()
	assigned_by = models.CharField(max_length=500, blank=True, null=True)
	callmode = models.CharField(default='', max_length=50, null=True, db_index=True)

	def __str__(self):
		return str(self.numeric)

class CurrentCallBack(models.Model):
	"""
	This model is for storing the agent current callbacks for later on dialler dialling purpose.
	"""
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
			on_delete=models.CASCADE,null=True)
	contact_id = models.BigIntegerField(null=True, blank=True, db_index=True)
	callbackcontact_id = models.BigIntegerField(null=True, blank=True, db_index=True)
	notification_id = models.BigIntegerField(null=True, blank=True, db_index=True)
	campaign = models.CharField(max_length=100,null=True, blank=True) 
	phonebook = models.CharField(max_length=100,null=True, blank=True)
	user = models.CharField(max_length=100,null=True)
	numeric  = models.CharField(default='', max_length=50,null=True, db_index=True)
	status  = models.CharField(default=CONTACT_STATUS[0][0],choices=CONTACT_STATUS,db_index=True,max_length=15)
	callback_title = models.CharField(default='',max_length=100,null=True)
	callback_type = models.CharField(default=CALLBACK_MODE[0][0],choices=CALLBACK_MODE,db_index=True,max_length=15)
	schedule_time = models.DateTimeField(null=True,blank=True,db_index=True)
	disposition = models.CharField(max_length=100,null=True,blank=True)
	comment =  models.CharField(default='', max_length=500, blank=True, null=True)
	callmode = models.CharField(default='', max_length=50, null=True, db_index=True)

	@property
	def schedule_date(self):
		return self.schedule_time.strftime("%d-%m-%Y %H:%M:%S")

	def __str__(self):
		return str(self.numeric)

class Abandonedcall(models.Model):
	""" This table is used to to store the missed/abandoned calls information """
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
			on_delete=models.CASCADE,null=True)
	campaign = models.CharField(max_length=100,null=True, blank=True) 
	user = models.CharField(max_length=100,null=True)
	caller_id = models.CharField(max_length=100,null=True)
	numeric  = models.CharField(default='', max_length=50,null=True, db_index=True)
	status  = models.CharField(default=CONTACT_STATUS[0][0],choices=CONTACT_STATUS,db_index=True,max_length=15)
	created_date = models.DateTimeField(auto_now_add=True)

	@property
	def call_date(self):
		return self.created_date.strftime("%d-%m-%Y %H:%M:%S")


	def __str__(self):
		return str(self.numeric)

	class Meta:
		ordering = ['-created_date']

class Notification(models.Model):
	"""
	This model is for storing the notification data for sending notifications.
	"""
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
			on_delete=models.CASCADE,null=True)
	contact_id = models.BigIntegerField(blank=True, null=True, db_index=True)
	campaign = models.CharField(max_length=100,null=True, blank=True, db_index=True) 
	user = models.CharField(max_length=100,null=True)
	title=models.CharField(max_length=256,null=True)
	message = models.TextField()
	numeric = models.CharField(default='', max_length=50,null=True, db_index=True)
	viewed  = models.BooleanField(default=False, db_index=True)
	created_date = models.DateTimeField(auto_now_add=True)
	modified_date = models.DateTimeField(auto_now=True)
	notification_type = models.CharField(max_length=100, null=True, blank=True)    
	def __str__(self):
		return str(self.title)

class SnoozedCallback(models.Model):
	"""
	This model is for storing snoozed callbacks
	"""
	site = models.ForeignKey(Site, default=settings.SITE_ID, editable=False,
			on_delete=models.CASCADE,null=True)
	contact_id = models.BigIntegerField(null=True, blank=True, db_index=True)
	user = models.CharField(max_length=100,null=True)
	numeric  = models.CharField(default='', max_length=50,null=True, db_index=True)
	callback_type = models.CharField(default=CALLBACK_MODE[0][0],choices=CALLBACK_MODE,db_index=True,max_length=15)
	snoozed_time = models.DateTimeField(null=True,blank=True,db_index=True)
	created_date = models.DateTimeField(auto_now_add=True)
	def __str__(self):
		return str(self.user)

class DataUploadLog(models.Model):
	"""
	This model is for storing uploaded phonebook log
	"""
	improper_file = models.FileField(upload_to='upload', blank=True)
	completed_percentage = models.IntegerField(default='0')
	created_date = models.DateTimeField(auto_now_add=True,null=True,blank=True)
	modified_date = models.DateTimeField(auto_now=True,null=True,blank=True)
	job_id = models.CharField(max_length=100, null=True, blank=True)
	status = models.CharField(default=0,choices=UPLOAD_STATUS, max_length=15)

	def __str__(self):
		return self.job_id+str(self.completed_percentage)

class StickyAgent(models.Model):
	"""
	This models stores the sticky agent info 
	"""
	numeric  = models.CharField(default='', max_length=15,null=True, db_index=True)
	campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE ,db_index=True, null=True)
	campaign_name = models.CharField(max_length=100,null=True, blank=True)
	agent = models.ForeignKey(User, on_delete=models.CASCADE)
	created = models.DateTimeField(auto_now_add=True)
	modified = models.DateTimeField(auto_now=True)

	def __str__(self):
		return str(self.numeric)

class ThirdPartyApiUserToken(models.Model):
	"""
	This model is used to create Token for third party api
	"""
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
	mobile_no = models.BigIntegerField(blank=True, null=True)
	token = models.CharField(max_length=50, unique=True)
	domain = models.CharField(max_length=100)
	token_creation_date = models.DateTimeField(auto_now=True)
	last_ip_addresss = models.CharField(max_length=20, null=True, blank=True)
	last_used = models.DateTimeField(auto_now_add=True)

class SMSLog(models.Model):
	"""
	Thid model is used to store sms logs
	"""
	sms_text = models.TextField(blank=True, null=True)
	template = models.ForeignKey(SMSTemplate, on_delete=models.SET_NULL, null=True, related_name='template_sms')
	sent_by = models.ForeignKey(User,on_delete=models.SET_NULL, null=True,
		blank=True, related_name='sms_sender')
	reciever = models.BigIntegerField(blank=True, null=True, db_index=False)
	status = models.CharField(default='Active', choices=Status, max_length=10)
	session_uuid = models.UUIDField(db_index=True, editable=False, null=True)
	status_message =  models.CharField(max_length=255, blank=True, null=True)
	created = models.DateTimeField(auto_now_add=True)


class ThirdPartyApi(models.Model):
	"""
	This model is used for thirdparty api 
	"""
	name = models.CharField(max_length=50)
	status = models.CharField(default='Active',choices=Status, max_length=10)
	dynamic_api = models.BooleanField(default=False)
	campaign = models.ManyToManyField(Campaign, related_name="apicampaign",
				null=True,blank=True)
	click_url = models.BooleanField(default=False)
	weburl = JSONField(default=list)
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)

	class Meta:
		get_latest_by = '-created'
		ordering = ['-created']

	def __str__(self):
		return self.name

class VoiceBlaster(models.Model):
	""" 
	This is the model for voiceblaster
	"""
	name = models.CharField(max_length=50)
	voice_blaster = models.BooleanField(default=False)
	campaign = models.ManyToManyField(Campaign, related_name="vbcampaign",
				null=True,blank=True)
	vb_mode = models.CharField(choices=VB_MODE, max_length=2, null=True, db_index=True)
	vb_audio = models.ForeignKey(AudioFile, related_name='voice_blaster_audio', on_delete=models.SET_NULL, blank=True, null=True)
	vb_data = JSONField(default=dict)
	status = models.CharField(default='Active', choices=Status, max_length=10)
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)

	class Meta:
		get_latest_by = '-created'
		ordering = ['-created']

	def __str__(self):
		return self.name

class AdminLogEntry(models.Model):
	"""
	This model is used to create admin log
	"""
	created_by = models.ForeignKey(User, on_delete=models.CASCADE ,db_index=True)
	created = models.DateTimeField(auto_now_add=True)
	change_message = models.CharField(max_length=250, null=True, blank=True)
	action_name = models.CharField(max_length=1, null=True, blank=True, choices=ACTION)
	event_type = models.CharField(max_length=255, null=True, blank=True)
	login_duration = models.TimeField(default=default_time, blank=True, null=True)
	def __str__(self):
		return str(self.change_message)

class PhonebookBucketCampaign(models.Model):
	"""
	Thid model is used to store phonebook bucket campaigns ordering and priority
	"""
	campaign = models.ForeignKey(Campaign,on_delete=models.CASCADE, null=True,
		blank=True, related_name='pb_campaign')
	agent_login_count = models.IntegerField(default=0)
	is_contact = models.BooleanField(default=False)

class EmailScheduler(models.Model):
	"""
	This models is used to store the email schedule
	"""
	reports = JSONField(default=list)
	status = models.CharField(default='Active', choices=Status, max_length=10)
	created_by = models.ForeignKey('User',on_delete=models.CASCADE, null=True,
		blank=True, related_name='email_scheduler_user')
	schedule_time = models.CharField(max_length=20, blank=True, null=True)
	emails = JSONField(default=dict)
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)

	class Meta:
		get_latest_by = '-created'
		ordering = ['-created']

class ReportColumnVisibility(models.Model):
	"""
	Thid model is used to store userwise visibility of report columns 
	"""
	user = models.ForeignKey(User,on_delete=models.CASCADE, null=True,
		blank=True, related_name='user_report')
	report_name = models.CharField(default='1',choices=REPORT_NAME, max_length=2)
	columns_name = JSONField(default=list)
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)
	def __str__(self):
		return str(self.user.username)

class CallRecordingFeedback(models.Model):
	"""
	Thid model is used to store userwise visibility of report columns 
	"""
	user = models.ForeignKey(User,on_delete=models.CASCADE, null=True,
		blank=True, related_name='user_call_recording')
	feedback = models.TextField(blank=True, null=True)
	calldetail = models.ForeignKey(CallDetail, related_name='callrecording_calldetail', on_delete=models.CASCADE, null=True)
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)
	def __str__(self):
		return str(self.user.username)

class FullertonTempData(models.Model):
	"""this table is for FullertonTempData"""
	user = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,db_index=True)
	campaign_name = models.CharField(default='', max_length=50,null=True)
	customer_cid  = models.CharField(default='', max_length=15,null=True, db_index=True)
	uniqueid = models.CharField(default=None, max_length=30, null=True)			
	callflow = models.CharField(default='', max_length=15,null=True,)
	diallereventlog = JSONField(default=dict)
	dialed_status = models.CharField(default='', max_length=50)
	primary_dispo = models.CharField(default='', max_length=250, blank=True, null=True)
	comment = models.TextField(blank=True, null=True) 
	created = models.DateTimeField(null=True,blank=True)
	def __str__(self):
		return str(self.customer_cid)	

class SkilledRoutingCallerid(models.Model):
	""" this models is used for  storing skill routing callerids"""
	skill = models.ForeignKey(SkilledRouting, on_delete=models.CASCADE, null=True, blank=True, related_name='skillroute_callerid')
	caller_id = models.CharField(max_length=100,blank=True, null=True)

class BroadcastMessages(models.Model):
	"""
	This model stores all the broadcast messages that has been published to agents 
	"""
	sent_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,
			related_name='broadcast_user')
	receivers = JSONField(default=dict)
	message = models.CharField(max_length=255, blank=True, null=True)
	message_type = models.CharField(default='0',max_length=2, choices=BROADCAST_MESSAGE_TYPE)
	broadcast_time = models.CharField(default='5',max_length=4)
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)
	def __str__(self):
		return str(self.sent_by)

class Daemons(models.Model):
	""" This model is used for demon service and their status  """
	service_name = models.TextField(blank=False, null=False)
	status = models.BooleanField(default=True, null=True, blank=True)
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)


class Holidays(models.Model):
	name = models.CharField(max_length = 100, db_index=True, unique=True)
	status = models.CharField(default='Active',choices=Status, max_length=10)
	description = models.TextField(blank=True, null=True)
	holiday_date = models.DateField(null=True, blank=True)
	holiday_audio = models.ForeignKey(AudioFile, related_name='holiday_audio', on_delete=models.SET_NULL, blank=True, null=True)
	created_by = models.ForeignKey(User, related_name='holiday_created_by',on_delete=models.SET_NULL,blank=True, null=True)
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)
	
	def __str__(self):
		return self.name

class PasswordManagement(models.Model):
	password_expire = models.IntegerField(default=0)
	max_password_attempt = models.IntegerField(default=3)
	forgot_password = models.BooleanField(default=False)
	password_data = JSONField(default=dict)


class PasswordResetLogs(models.Model):
	username = models.CharField(max_length=150,blank=True,null=True)
	password_uuid = models.CharField(max_length=255,blank=True,null=True)
	reset_success = models.BooleanField(default=False)
	created = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.username

class PasswordChangeLogs(models.Model):
	username = models.CharField(max_length=150,blank=True,null=True)
	change_type= models.CharField(default='0',choices=PasswordChangeType,max_length=2,null=True,blank=True)
	changed_by = models.ForeignKey(User,on_delete=models.SET_NULL,blank=True, null=True, related_name='password_changed_by')
	user_email = models.CharField(max_length=150,blank=True,null=True)
	message = models.TextField() 
	created = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.username

