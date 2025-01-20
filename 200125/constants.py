from django.conf import settings

CRM_FIELDS = ['section_name','section_priority','field','field_type',
'field_size','options','editable','field_priority','field_status', 'unique_field']

USER_FIELDS = ['username','email','password','group','role', 'first_name', 'last_name', 'wfh_numeric', 'employee_id']

HOLIDAYS_FIELDS = ['name','holiday_date','description','status']

DNC_FIELDS = ["numeric","campaign","global_dnc","dnc_end_date"]

ALTERNATE_FIELDS = ['uniqueid','alternate_numeric']

history_table_head_1 = [{"data":"user","title":"Username"},{"data":"campaign_name","title":"Campaign"},{"data":"customer_cid","title":"Phone Number"},{"data":"uniqueid","title":"Unique Id"}]

history_table_head_2 = [{"data":"callflow","title":"Callflow"},{"data":"init_time","title":"Calling Time"},{"data":"hangup_time","title":"Hangup Time"},{"data":"call_duration","title":"Call Duration"},{"data":"primary_dispo","title":"Disposition"},{"data":"comment","title":"Comment", "class":"comment-field"}]

WFH_DISPO = {'1':'Interested','2':'Not Intrested','3':'Call Back','4':'Test4','5':'Test5','6':'Test6','7':'Test7','8':'Test8','9':'Test9'}

Status = (
	('Active', 'Active'),
	('Inactive','Inactive'),
	('Delete','Delete')
)
PasswordChangeType = (
	('0','Application'),
	('1','Email'),
)
SHOW_DISPOS_TYPE = (
	('0','Both'),
	('1','Connected'),
	('2','NotConnected'),
	)

auto_dialed_status=(
('Connected','Connected'),
('Drop','Drop'),
('Abandoned','Abandoned')
,('Auto-Dialed','Auto-Dialed')
,('Dialed','Dialed'),
('Agent-Answered','Agent-Answered'),
('INVALID_NUMBER','INVALID_NUMBER')
)

TRUNK_TYPE = (
	('international', 'International'),
	('domestic','Domestic')
)
UserStatus = (
	(True, 'Active'),
	(False,'Inactive')
)
DIAL_KEY_OPTIONS = (
	('hangup','Hangup'),
	('repeat','Repeat')
)
PROTOCOL_CHOICES =  (
	('SIP', 'SIP'),
	('AIP','AIP')
)
CALL_MODE =  (
	('Outbound', 'Outbound'),
	('Inbound','Inbound'),
	('Blended','Blended'),
	('Predictive','Predictive'),
	('Progressive','Progressive'),
	('Autodial','Autodial')
)
CALL_TYPE = (
	('webrtc','Webrtc'),
	('softcall', 'SIPPhone'),
	('2', 'WebPSTN'),
	('3', 'SoftPBX'),
)
CAMPAIGN_STRATEGY_CHOICES = (
	('ring-all', 'Ring All'),
	('longest-idle-agent', 'Longest Idle Agent'),
	('round-robin','Round Robin'),
	('top-down','Top Down'),
	('agent-with-least-talk-time','Agent With Least Talk Time'),
	('agent-with-fewest-calls','Agent With Fewest Calls'),
	('sequentially-by-agent-order','Sequentially By Agent Order'),
	('random','Random'),
)
DIAL_RATIO_CHOICES = (
	(1.0,'1.0'),
	(1.5, '1.5'),
	(2.0, '2.0'),
	(2.5, '2.5'),
	(3.0, '3.0'),
	(3.5, '3.5'),
	(4.0, '4.0'),
	(4.5, '4.5'),
	(5.0, '5.0'),
)
OPERATORS_CHOICES =(
	('=', '='),
	('!=', '!='),
	('>', '>'),
	('>=','>='),
	('<','<'),
	('<=', '<='),
	('IN','IN'),
	('NOT IN', 'NOT IN'),
	('LIKE','LIKE'),
	('ISNULL','ISNULL'),
	('IS NOT NULL','IS NOT NULL')
)
LOGICAL_OPERATOR_CHOICES =(
	('AND','AND'),
	('OR', 'OR'),
	('Order By','order by')
)
TRANSFER_MODE =(
	('agent-to-agent','agent-to-agent'),
	('agent-to-campaign','agent-to-campaign'),
	('agent-to-thirdparty','agent-to-thirdparty'),
)
CALLBACK_MODE = (
	('self','self-callback'),
	('queue','queue-callback'),
)
DNC_MODE = (
	('local','local-dnc'),
	('global','global-dnc'),
)
ACCESS_LEVEL=(
	('Admin','Admin'),
	('Manager','Manager'),
	('Supervisor','Supervisor'),
	('Agent','Agent'),
)
OUTBOUND = (
	('Predictive','Predictive'),
	('Progressive','Progressive'),
	('Preview','Preview'),
)
API_MODE = (
	('API-in-Iframe','API-in-Iframe'),
	('API-in-Tab', 'API-in-Tab'),
)
CallBack_TYPE = (
	('self','self'),
	('queue','queue')
)
FIELD_TYPE = (('multifield','MultiField'),
	('link', 'Link'),
	('text', 'Text'),
	('textarea', 'TextArea'),
	('dropdown', 'DropDown'),
	('multiselect','MultiSelect'),
	('checkbox','CheckBox'),
	('multiselectcheckbox','MultiSelectCheckBox'),
	('radio','Radio'),
	('integer','Integer'),
	('datefield', 'DateField'),
	('timefield','TimeField'),
	('datetimefield', 'DateTimeField'),
)
DISPO_FIELD_TYPE = (
	('multifield','MultiField'),
	('dropdown','DropDown'),
)
SCHEDULE_TYPE = (('schedule_time','schedule_time'),
	('recycle_time','recycle_time')
)
TIMER_SEC = (
	(30,'30'),(60,'60'),
	(90,'90'),(120,'120'),
	(150,'150')
)
SCHEDULE_DAYS = (
	('all_days', "All Days"),
	('mon_to_fri',"Mon-Fri"),
	('custom', 'Custom')
)
PAGINATE_BY_LIST = (
	(10, 10),
	(25, 25),
	(50, 50),
	(100, 100),
)
CONTACT_STATUS = (
	('NotDialed', 'NotDialed'),
	('Queued','Queued'),
	('Dialed','Dialed'),
	('Locked','Locked'),
	('NDNC','NDNC'),
	('Callback','Callback'),
	('Snoozed','Snoozed'),
	('Abandonedcall','Abandonedcall'),
	('Drop','Drop'),
	('Dnc','Dnc'),
	('NC','NC'),
	('Invalid Number','Invalid Number'),
	('CBR','CBR'), 
	('Queued-Abandonedcall','Queued-Abandonedcall'),
	('Queued-Callback','Queued-Callback'),
	('Dialed-Queued','Dialed-Queued'),
)
ACTION = (
	(1, 'Creation'),
	(2,'Updation'),
	(3, 'Deletion'),
	(4, 'Login'),
	(5, 'Logout')
)
ACTION_TYPE = {"1":"created ", "1_prefix":"in ",
"2":"updated ","2_prefix":"in ",
"3":"deleted ids ","3_prefix":"from ",
"4":"activated ids ","4_prefix":"from ",
"5":"inactivated ids ", "5_prefix":"from ",
"6":"uploaded data in","6_prefix":"",
"7":"force logout all users"}

UPLOAD_STATUS = (
	(0,'InProgress'),
	(1,'Completed')
)
## crm app constants

FIELD_CHOICES = (
	('text', 'Text'),
	('textarea','Textarea'),
	('dropdown','Dropdown'),
	('multiselect','MultiSelect'),
	('checkbox','Checkbox'),
	('multicheckbox','MultiSelectCheckbox'),
	('radio','Radio'),
	('integer','Integer'),
	('float','float'),
	('dateField','DateField'),
	('datetimeField','DateTimeField'),
	('timefield','TimeField'),
)
ORDER_BY = (
	('Desc', 'Descending'),
	('Asc', 'Ascending'),
	('Random', 'Random'),
)

MONTHS = [{'month':'January','number':1},{'month':'February','number':2},{'month':'March','number':3},{'month':'April','number':4},{'month':'May','number':5},{'month':'June','number':6},{'month':'July','number':7},{'month':'August','number':8},{'month':'September','number':9},{'month':'October','number':10},{'month':'November','number':11},{'month':'December','number':12}]

VB_MODE = (('0','Audio File'),('1','TTS(Text to speech)'))

TEMPLATE_TYPE = (
		('0', 'Global'),
		('1', 'Campaign'),
		)

TRIGGER_ACTIONS = (
		('0', 'On Pre-Call'),
		('1', 'On Disposition'),
		('2', 'On Call'),
		)

SMS_STATUS = (
		('0', 'Success'),
		('1', 'Fail'),
		)

MODULES = ['sms_template','gateway_settings','thirdpartyapi','third_party_user_campaign','voiceblaster','email_scheduler','emaillog']

Gateway_Mode = (
		('0', 'Sms'),
		('1', 'Whats-App'),
		)

SEARCH_TYPE = ( 
	('0','PHONEBOOK'), 
	('1','CAMPAIGN'),
	('2','GLOBAL') 
	)
TYPE_OF_DID = (
	('1','single did'),
	('2','multiple did'),
	('3','did range'),
	)

TYPE_OF_INBOUND_CALLER_ID=(
('1','single'),
('2','range'),
('3','multiple')
)
STRATEGY_CHOICES = (
('0','Top-to-bottom'),
('1','Bottom-to-top'),
('2','Random'),
('3','Highest-waiting-agent')
)

REPORTS_LIST = (
	('Call Detail','Call Detail'),
	('Agent Performance','Agent Performance'),
	('Campaign Performance','Campaign Performance'),
	('Agent Mis','Agent Mis'),
	('Agent Activity','Agent Activity'),
	('Campaign Mis','Campaign Mis'),
	('Abandoned Call','Abandoned Call'),
	('CallBack','CallBack'),
	('Billing','Billing'),
	)

REPORT_NAME =  (
	('1','call_detail'),
	('2','call_recording'),
	('3','agent_performance'),
	('4','agent_mis'),
	('5','agent_activity'),
	('6','campaign_mis'),
	('7','campaign_performance'),
	('8','callback_call'),
	('9','abandoned_call'),
	('10','contact_info'),
	('11','billing'),
	('12','admin_log'),
	('13','call_recording_feedback'),
	('14','alternate_number'),
	('15','management_performace'),
	('16','lan'),
	('17','ic_report'),
	)


CDR_DOWNLOAD_COl = {'campaign_name':'callcenter_calldetail.campaign_name as campaign_name',
	'user':'usr.username as user',
	'full_name': "CONCAT(usr.first_name, ' ' ,usr.last_name) as full_name",
	'supervisor_name':'supr.username as supervisor_name',
	'phonebook':'callcenter_calldetail.phonebook as phonebook',
	'customer_cid':'callcenter_calldetail.customer_cid as customer_cid',
	'contact_id':'callcenter_calldetail.contact_id as contact_id',
	'lan':'callcenter_calldetail.uniqueid as lan',
	'session_uuid':'callcenter_calldetail.session_uuid as session_uuid',
	'init_time':"date_trunc('second', CASE WHEN callcenter_diallereventlog.init_time IS NULL THEN callcenter_calldetail.init_time ELSE callcenter_diallereventlog.init_time END at time zone 'Asia/Kolkata') as init_time",
	'ring_time':"date_trunc('second', CASE WHEN callcenter_diallereventlog.ring_time IS NULL THEN callcenter_calldetail.ring_time ELSE callcenter_diallereventlog.ring_time END at time zone 'Asia/Kolkata') as ring_time",
	'connect_time':"date_trunc('second', CASE WHEN callcenter_diallereventlog.connect_time IS NULL THEN callcenter_calldetail.connect_time ELSE callcenter_diallereventlog.connect_time END at time zone 'Asia/Kolkata') as connect_time",
	'hangup_time':"date_trunc('second', CASE WHEN callcenter_diallereventlog.hangup_time IS NULL THEN callcenter_calldetail.hangup_time ELSE callcenter_diallereventlog.hangup_time END at time zone 'Asia/Kolkata') as hangup_time",
	'wait_time':'CASE WHEN callcenter_diallereventlog.wait_time IS NULL THEN callcenter_calldetail.wait_time ELSE callcenter_diallereventlog.wait_time END as wait_time',
	'ring_duration':'CASE WHEN callcenter_diallereventlog.ring_duration IS NULL THEN callcenter_calldetail.ring_duration ELSE callcenter_diallereventlog.ring_duration END as ring_duration',
	'hold_time':'CASE WHEN callcenter_diallereventlog.hold_time IS NULL THEN callcenter_calldetail.hold_time ELSE callcenter_diallereventlog.hold_time END as hold_time',
	'callflow':'callcenter_calldetail.callflow as callflow',
	'callmode':'callcenter_calldetail.callmode as callmode',
	'bill_sec':'CASE WHEN callcenter_diallereventlog.bill_sec IS NULL THEN callcenter_calldetail.bill_sec ELSE callcenter_diallereventlog.bill_sec END as talk_time',
	'ivr_duration':'CASE WHEN callcenter_diallereventlog.ivr_duration IS NULL THEN callcenter_calldetail.ivr_duration ELSE callcenter_diallereventlog.ivr_duration END as ivr_duration',
	'call_duration':'CASE WHEN callcenter_diallereventlog.call_duration IS NULL THEN callcenter_calldetail.call_duration ELSE callcenter_diallereventlog.call_duration END as call_duration',
	'feedback_time':'callcenter_calldetail.feedback_time as wrapup_time',
	'call_length':'cast(CASE WHEN callcenter_diallereventlog.call_duration IS NULL THEN callcenter_calldetail.call_duration::interval + feedback_time::interval ELSE callcenter_diallereventlog.call_duration::interval + feedback_time::interval END as text) as call_length',
	'hangup_source':'callcenter_calldetail.hangup_source as hangup_source',
	'internal_tc_number':'callcenter_calldetail.internal_tc_number as internal_tc_number',
	'external_tc_number':'callcenter_calldetail.external_tc_number as external_tc_number',
	'progressive_time':'callcenter_calldetail.progressive_time as progressive_time',
	'preview_time':'callcenter_calldetail.preview_time as preview_time',
	'predictive_wait_time':'callcenter_calldetail.predictive_wait_time as predictive_wait_time',
	'inbound_wait_time':'callcenter_calldetail.inbound_wait_time as inbound_wait_time',
	'blended_wait_time':'callcenter_calldetail.blended_wait_time as blended_wait_time',
	'hangup_cause':'CASE WHEN callcenter_diallereventlog.hangup_cause IS NULL THEN callcenter_calldetail.hangup_cause ELSE callcenter_diallereventlog.hangup_cause END as hangup_cause',
	'hangup_cause_code':'CASE WHEN callcenter_diallereventlog.hangup_cause_code IS NULL THEN callcenter_calldetail.hangup_cause_code ELSE callcenter_diallereventlog.hangup_cause_code END as hangup_cause_code',
	'dialed_status':'CASE WHEN callcenter_diallereventlog.dialed_status IS NULL THEN callcenter_calldetail.dialed_status ELSE callcenter_diallereventlog.dialed_status END as dialed_status',
	'comment':'callcenter_cdrfeedbck.comment as comment',
	'primary_dispo':'callcenter_cdrfeedbck.primary_dispo as primary_dispo',
	'sms_sent':"CASE WHEN sms.name IS NULL THEN 'No' WHEN sms.name IS NOT NULL THEN 'Yes' END as sms_sent",
	'sms_message':'sms.name as sms_message'
	}

LAN_REPORT_COL ={
	'lan':"uniqueid as lan",
	'username':'usr.username as username',
	'primary_dispo':'primary_dispo',
	'customer_cid':'customer_cid',
	'created_on':"(init_time at time zone 'Asia/Kolkata') as init_time",
	'comment':'comment'
}

QC_FEEDBACK_COL = {
	'agent':"usr.username as agent",
	'cli':"callcenter_calldetail.customer_cid as cli",
	'session_uuid':"callcenter_calldetail.session_uuid as session_uuid",
	'primary_dispo': 'callcenter_cdrfeedbck.primary_dispo as primary_dispo',
	'uniqueid':'callcenter_calldetail.uniqueid as uniqueid',
	'feedback': 'callcenter_callrecordingfeedback.feedback as feedback',
	'submitted_by':'crfb_user.username as submitted_by'
}

IC_REPORT_COL = {
	"lan": 'callcenter_calldetail.uniqueid AS "account_no"',
	"username":'SUBSTRING(usr.username, 2) AS "user"',
	"action_date":'to_char(callcenter_calldetail.hangup_time at time zone \'Asia/Kolkata\', \'DD.MM.YYYY\') AS "action_date"',
	"action_code":'COALESCE((callcenter_cdrfeedbck.feedback ->> \'action_code\'), \'OCMO\') AS "action_code"',
	"result_code":'callcenter_cdrfeedbck.primary_dispo AS "result_code"',
	"rfd":'trim(split_part(COALESCE((callcenter_cdrfeedbck.feedback ->> \'rfd\'), \'NCCT\'), \'-\', 1)) AS "rfd"',
	"next_action_code":'COALESCE((callcenter_cdrfeedbck.feedback ->> \'next_action_code\'), \'OCMO\') AS "next_action_code"',
	"next_action_date_time":'to_char(COALESCE(NULLIF(((callcenter_cdrfeedbck.feedback ->> \'next_action_date_time\')),\'\')::timestamp with time zone, (callcenter_calldetail.hangup_time at time zone \'Asia/Kolkata\' + \'2 days\')), \'DD.MM.YYYY HH:MM\') AS "next_action_date_time"',
	"remark":'callcenter_cdrfeedbck.comment AS "remark"',
	"promise_date":'CASE WHEN callcenter_cdrfeedbck.primary_dispo = \'PTP\' THEN to_char(CASE WHEN COALESCE(NULLIF(((callcenter_cdrfeedbck.feedback ->> \'ptp_date\')),\'\')::date, callcenter_calldetail.hangup_time at time zone \'Asia/Kolkata\') < (callcenter_calldetail.hangup_time at time zone \'Asia/Kolkata\') THEN callcenter_calldetail.hangup_time ELSE COALESCE(NULLIF((callcenter_cdrfeedbck.feedback ->> \'ptp_date\'),\'\')::date, callcenter_calldetail.hangup_time at time zone \'Asia/Kolkata\') END, \'DD.MM.YYYY\') ELSE \'\' END AS "promise_date"',
	"promise_amount":'(callcenter_cdrfeedbck.feedback ->> \'ptp_amount\') AS "promise_amount"'
}

COUNTRY_CODES = (
	('0','INDIA'),
	('91', 'INDIA'),
	('0091', 'INDIA'),
	('93','AFGHANISTAN'),
	('1-907','ALASKA (USA)'),
	('355','ALBANIA'),
	('213','ALGERIA'),
	('1-684','AMERICAN SAMOA'),
	('376','ANDORRA'),
	('244','ANGOLA'),
	('1-264','ANGUILLA'),
	('1-268','ANTIGUA & BARBUDA'),
	('54','ARGENTINA'),
	('374','ARMENIA'),
	('297','ARUBA'),
	('247','ASCENSION'),
	('61','AUSTRALIA'),
	('43','AUSTRIA'),
	('994','AZERBAIJAN'),
	('1-242','BAHAMAS'),
	('973','BAHRAIN'),
	('880','BANGLADESH'),
	('1-246','BARBADOS'),
	('375','BELARUS'),
	('32','BELGIUM'),
	('501','BELIZE'),
	('229','BENIN'),
	('1-441','BERMUDA'),
	('975','BHUTAN'),
	('591','BOLIVIA'),
	('387','BOSNIA / HERZEGOVINA'),
	('267','BOTSWANA'),
	('55','BRAZIL'),
	('1-284','BRITISH VIRGINISLANDS'),
	('673','BRUNEI'),
	('359','BULGARIA'),
	('226','BURKINA FASO'),
	('257','BURUNDI'),
	('855','CAMBODIA'),
	('237','CAMEROON'),
	('1','CANADA'),
	('238','CAPE VERDE'),
	('1-345','CAYMAN ISLANDS'),
	('236','CENTRAL AFRICANREPUBLIC'),
	('235','CHAD'),
	('56','CHILE'),
	('86','CHINA'),
	('57','COLOMBIA'),
	('269','COMOROS'),
	('242','CONGO'),
	('243','CONGO DEM. REP.(ZAIRE)'),
	('682','COOK ISLAND'),
	('506','COSTA RICA'),
	('385','CROATIA'),
	('53','CUBA'),
	('357','CYPRUS'),
	('420','CZECH REPUBLIC'),
	('45','DENMARK'),
	('246','DIEGO GARCIA'),
	('253','DJIBOUTI'),
	('1-767','DOMINICA'),
	('1-809','DOMINICAN REPUBLIC'),
	('670','EAST TIMOR'),
	('593','ECUADOR'),
	('20','EGYPT'),
	('503','EL SALVADOR'),
	('240','EQUATORIAL GUINEA'),
	('291','ERITREA'),
	('372','ESTONIA'),
	('251','ETHIOPIA'),
	('500','FALKLAND ISLANDS'),
	('298','FAROE ISLANDS'),
	('679','FIJI'),
	('358','FINLAND'),
	('33','FRANCE'),
	('594','FRENCH GUIANA'),
	('689','FRENCH POLYNESIA'),
	('241','GABON'),
	('220','GAMBIA'),
	('995','GEORGIA'),
	('49','GERMANY'),
	('233','GHANA'),
	('350','GIBRALTAR'),
	('30','GREECE'),
	('299','GREENLAND'),
	('1-473','GRENADA'),
	('590','GUADALOUPE'),
	('1-671','GUAM'),
	('502','GUATEMALA'),
	('224','GUINEA'),
	('245','GUINEA BISSAU'),
	('592','GUYANA'),
	('509','HAITI'),
	('1-808','HAWAII (USA)'),
	('504','HONDURAS'),
	('852','HONG KONG'),
	('36','HUNGARY'),
	('354','ICELAND'),
	('62','INDONESIA'),
	('98','IRAN'),
	('964','IRAQ'),
	('353','IRELAND'),
	('972','ISRAEL'),
	('39','ITALY'),
	('225','IVORY COAST'),
	('1-876','JAMAICA'),
	('81','JAPAN'),
	('962','JORDAN'),
	('7','KAZAKHSTAN'),
	('254','KENYA'),
	('686','KIRIBATI'),
	('850','KOREA (NORTH)'),
	('82','KOREA SOUTH'),
	('965','KUWAIT'),
	('996','KYRGHYZSTAN'),
	('856','LAOS'),
	('371','LATVIA'),
	('961','LEBANON'),
	('266','LESOTHO'),
	('231','LIBERIA'),
	('218','LIBYA'),
	('423','LIECHTENSTEIN'),
	('370','LITHUANIA'),
	('352','LUXEMBOURG'),
	('853','MACAU'),
	('389','MACEDONIA'),
	('261','MADAGASCAR'),
	('265','MALAWI'),
	('60','MALAYSIA'),
	('960','MALDIVES'),
	('223','MALI'),
	('356','MALTA'),
	('1-670','MARIANA IS.(SAIPAN)'),
	('692','MARSHALL ISLANDS'),
	('596','MARTINIQUE(FRENCHANTILLES)'),
	('222','MAURITANIA'),
	('230','MAURITIUS'),
	('269','MAYOTTE'),
	('52','MEXICO'),
	('691','MICRONESIA'),
	('373','MOLDOVA'),
	('377','MONACO'),
	('976','MONGOLIA'),
	('1-664','MONTSERRAT'),
	('212','MOROCCO'),
	('258','MOZAMBIQUE'),
	('95','MYANMAR'),
	('264','NAMIBIA'),
	('674','NAURU'),
	('977','NEPAL'),
	('31','NETHERLANDS'),
	('599','NETHERLANDS ANTILLES'),
	('687','NEW CALEDONIA'),
	('64','NEW ZEALAND'),
	('505','NICARAGUA'),
	('227','NIGER'),
	('234','NIGERIA'),
	('683','NIUE ISLAND'),
	('47','NORWAY'),
	('968','OMAN'),
	('92','PAKISTAN'),
	('680','PALAU'),
	('970','PALESTINE'),
	('507','PANAMA'),
	('675','PAPUA NEW GUINEA'),
	('595','PARAGUAY'),
	('51','PERU'),
	('63','PHILIPPINES'),
	('48','POLAND'),
	('351','PORTUGAL'),
	('1-787','PUERTO RICO (I) (USA)'),
	('1-939','PUERTO RICO (II)(USA)'),
	('974','QATAR'),
	('262','REUNION'),
	('40','ROMANIA'),
	('7','RUSSIA'),
	('250','RWANDA'),
	('685','SAMOA WESTERN'),
	('378','SAN MARINO'),
	('239','SAO TOME &PRINCIPE'),
	('966','SAUDI ARABIA'),
	('221','SENEGAL'),
	('248','SEYCHELLES'),
	('232','SIERRA LEONE'),
	('65','SINGAPORE'),
	('421','SLOVAKIA'),
	('386','SLOVENIA'),
	('677','SOLOMON ISLANDS'),
	('252','SOMALIA'),
	('27','SOUTH AFRICA'),
	('34','SPAIN'),
	('94','SRI LANKA'),
	('290','ST HELENA'),
	('1-869','ST KITTS & NEVIS'),
	('1-758','ST LUCIA'),
	('1-784','ST VINCENT &GRENADINES'),
	('508','ST. PIERRE &MIQUELON'),
	('249','SUDAN'),
	('597','SURINAM'),
	('268','SWAZILAND'),
	('46','SWEDEN'),
	('41','SWITZERLAND'),
	('963','SYRIA'),
	('886','TAIWAN'),
	('992','TAJIKISTAN'),
	('255','TANZANIA'),
	('66','THAILAND'),
	('228','TOGO'),
	('690','TOKELAU'),
	('676','TONGA'),
	('1-868','TRINIDAD & TOBAGO'),
	('216','TUNISIA'),
	('90','TURKEY'),
	('993','TURKMENISTAN'),
	('1-649','TURKS & CAICOSISLANDS'),
	('688','TUVALU'),
	('256','UGANDA'),
	('380','UKRAINE'),
	('971','UNITED ARAB EMIRATES'),
	('44','UNITED KINGDOM'),
	('598','URUGUAY'),
	('998','UZBEKISTAN'),
	('678','VANUATU'),
	('39','VATICAN CITY'),
	('58','VENEZUELA'),
	('84','VIETNAM'),
	('1-340','VIRGIN ISLAND (USA)'),
	('681','WALLIS & FUTUNA'),
	('967','YEMEN'),
	('381','YUGOSLAVIA (SERBIA)'),
	('260','ZAMBIA'),
	('255','ZANZIBAR'),
	('263','ZIMBABWE'),
)

MODULE_LIST = [{'name':'dashboard','title':'Dashboard','icon':'fa-home', 'permissions':'R','sequence':1,'children':[]},
	{'name':'user_management','title':'User Management','icon':'fa-users','sequence':2, 'children':[
		{'name':'users','title':'Users','icon':'fa-users-cog','sequence':1,'children':[]},
		{'name':'user_roles','title':'Access Management','icon':'fa-user-tie','sequence':2,'children':[]},
		{'name':'groups','title':'Groups','icon':'fa-object-group','sequence':3,'children':[]},
		{'name':'password_management','title':'Password Management','icon':'fa-key','sequence':4,'children':[]}
	]},
	{'name':'campaign_management','title':'Campaign Management','icon':'fa-flag','sequence':3,
		'children':[{'name':'campaigns','title':'Campaigns','icon':'fa-flag','sequence':1,'children':[]},
		{'name':'ingroup_campaign','title':'InGroup','icon':'fa-object-group','sequence':2,'children':[]},
		{'name':'css', 'title':"CSS", 'icon':'fa-search','sequence':3,'children':[]},
		{'name':'skilledrouting', 'title':"Skill Routing", 'icon':'fa-cogs','sequence':4,'children':[]},
		{'name':'switch','title':'Switch','icon':'fa-server','sequence':5,'children':[]},
		{'name':'dialtrunks','title':'Dial Trunk','icon':'fa-signal','sequence':6,'children':[]},
		{'name':'dialtrunk_group','title':'Dial Trunk Group','icon':'fa-signal','sequence':7,'children':[]},
		{'name':'dispositions','title':'Dispositions','icon':'fa-tty','sequence':8,'children':[]},
		{'name':'relationtags','title':'Relationship Tag','icon':'fa-tty','sequence':9,'children':[]},
		{'name':'pause_breaks', 'title':"Pause Breaks", 'icon':'fa-pause','sequence':10,'children':[]},
		{'name':'campaign_schedules', 'title':"Shift Timing", 'icon':'fa-list-ol','sequence':11,'children':[]},
		{'name':'scripts', 'title':"Scripts", 'icon':'fa-comment','sequence':12,'children':[]},
		{'name':'audio_files', 'title':'Audio Files', 'icon':'fa-music','sequence':13,'children':[]}
	]},
	{'name':'crm','title':'CRM','icon':'fa-file-contract','sequence':4,'children':[
		{'name':'crm_fields', 'title':'CRM Field', 'icon':'fa-list','sequence':1,'children':[]},
		{'name':'phonebook', 'title':'Lead List', 'icon':'fa-address-book','sequence':2,'children':[]},
		{'name':'lead_priority', 'title':'Lead Priority', 'icon':'fa-address-book', 'permissions':'R','sequence':3,'children':[]},
	]},
	{'name':'call_report','title':'Call Reports','icon':'fa-chart-bar','sequence':5,'children':[
		{'name':'call_detail', 'title':'Call Details', 'icon':'fa-phone-square fa-rotate-90','url_abbr':'report', 'permissions':'R','sequence':1,'children':[]},
		{'name':'call_recordings', 'title':'Call Recordings', 'icon':'fa-microphone-alt','url_abbr':'report', 'permissions':'R','sequence':2,'children':[]},
		{'name':'agent_performance', 'title':'Agent Performance', 'icon':'fa-chart-line','url_abbr':'report', 'permissions':'R','sequence':3,'children':[]},
		{'name':'agent_mis', 'title':'Agent MIS', 'icon':'fa-phone-square fa-rotate-90','url_abbr':'report', 'permissions':'R','sequence':4,'children':[]},
		{'name':'agent_activity', 'title':'Agent Activity', 'icon':'fa-file-contract','url_abbr':'report', 'permissions':'R','sequence':5,'children':[]},
		{'name':'campaign_performance', 'title':'Campaign Performance', 'icon':'fa-chart-line','url_abbr':'report', 'permissions':'R','sequence':6,'children':[]},
		{'name':'campaign_mis', 'title':'Campaign MIS', 'icon':'fa-phone-square fa-rotate-90','url_abbr':'report', 'permissions':'R','sequence':7,'children':[]},
		{'name':'reschedule_callbacks', 'title':'Callback Call', 'icon':'fa-file-contract','url_abbr':'report', 'permissions':'R','sequence':8,'children':[]},
		{'name':'reschedule_abandoned_call', 'title':'Abandoned Call', 'icon':'fa-file-contract','url_abbr':'report', 'permissions':'R','sequence':9,'children':[]},
		{'name':'contact_info', 'title':'Contact Info', 'icon':'fa-user-tie','sequence':10,'children':[]},
		{'name':'alternate_number', 'title':'Altenate Number', 'icon':'fa-envelope-square','permissions':'R','sequence':11,'children':[]},
		{'name':'billing', 'title':'Billing', 'icon':'fa-money-bill-alt','url_abbr':'report', 'permissions':'R','sequence':12,'children':[]},
		{'name':'charts', 'title':'Charts', 'icon':'fa-chart-bar','sequence':13, 'permissions':'R','children':[]},
		{'name':'call_recording_feedback', 'title':'Call Recordings Feedback', 'icon':'fa-money-bill-alt', 'permissions':'R','sequence':14,'children':[]},
		{'name':'admin_log', 'title':'Admin Log', 'icon':'fa-money-bill-alt', 'permissions':'R','sequence':15,'children':[]},
		{'name':'management_performance', 'title':'Admin Performance', 'icon':'fa-chart-line', 'permissions':'R','sequence':16,'children':[]},
		{'name':'lan', 'title':'LAN Report', 'icon':'fa fa-tty', 'url_abbr':'report', 'permissions':'R','sequence':17,'children':[]},
	]},
	{'name':'administration','title':'Administration','icon':'fa-tachometer-alt','sequence':6,'children':[
		{'name':'dnc', 'title':'DNC', 'icon':'fa-file-contract','sequence':1,'children':[]},
		{'name':'ndnc', 'title':'NDNC', 'icon':'fa-envelope-square','sequence':2,'children':[]},
		{'name':'modules', 'title':'Module Management', 'icon':'fa-envelope-square','sequence':3,'children':[]},
		{'name':'holidays', 'title':'Holidays', 'icon':'fa-gift','sequence':4,'children':[]},
	]},
	{'name':'module_management','title':'Module Management','icon':'fa-tachometer-alt','sequence':7,'children':[
		{'name':'sms_template', 'title':'SMS Template', 'icon':'fa-envelope-square','sequence':1,'children':[]}, 
		{'name':'gateway_settings', 'title':'Sms Gateway Settings', 'icon':'fa-file-contract','sequence':2,'children':[]},
		{'name':'thirdpartyapi', 'title':'Thirdparty CRM', 'icon':'fa-envelope-square','sequence':3,'children':[]}, 
		{'name':'third_party_user_campaign', 'title':'Third Party User', 'icon':'fa-envelope-square','sequence':4, 'status':'Inactive','children':[]}, 
		{'name':'voiceblaster', 'title':'Voice Blaster', 'icon':'fa-envelope-square','sequence':5,'children':[]},
		{'name':'email_scheduler', 'title':'Reports Email Schedualer', 'icon':'fa-envelope-square','sequence':6,'status':'Inactive','children':[]},
		{'name':'email_log', 'title':'Email Log', 'icon':'fa-envelope-square','permissions':'R','sequence':7,'status':'Inactive','children':[]},
		{'name':'email_gateway', 'title':'Email Gateway', 'icon':'fa-list','sequence':8,'children':[]},
		{'name':'email_template', 'title':'Email Template', 'icon':'fa-list','sequence':9,'children':[]},
		{'name':'switchscreen', 'title':'Switch Screen', 'icon':'fa-envelope-square', 'permissions':'R', 'is_menu':False,'sequence':10,'children':[]},
		{'name':'qc_feedback', 'title':'QC Feedback', 'icon':'fa-envelope-square','permissions':'R', 'is_menu':False,'sequence':11,'children':[]},
		{'name':'system_boot_action', 'title':'System Boot Action','permissions':'R', 'is_menu':False, 'sequence':12,'children':[]}
	]}
]

BROADCAST_MESSAGE_TYPE = (
	('0','info'),
	('1','warning'),
	('2','danger'),
	)
