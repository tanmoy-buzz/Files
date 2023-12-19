--Freeswitch session anwered here for playing ivr welcome msg.
cc_customer = session:getVariable("cc_customer");
campaign = session:getVariable("campaign");
phonebook = session:getVariable("phonebook")
contact_id = session:getVariable("contact_id")
or_caller_id_number = session:getVariable("caller_id");
mobile_num = string.sub(session:getVariable("caller_id_number"), -10)
cc_agent = session:getVariable("cc_agent");
dial_method = string.lower(session:getVariable("outbound_dial_method"))
---This is the commands to connect database.
dbh = freeswitch.Dbh("odbc://freeswitch::")
assert(dbh:connected())
function string.starts(String,Start)
   return string.sub(String,1,string.len(Start))==Start
end

json = require "json"
my_query ="select * from callcenter_dialtrunk where id in (select trunk_id from callcenter_campaign where name = '"..campaign.."')"
--This is the code for get the Skill routed queues.

assert(dbh:query(my_query, function(qrow)
	if (qrow ~= nil and qrow ~="") then
		status = string.starts(qrow.dial_string,'sofia')
                session:execute("set","continue_on_fail=true")
                session:execute("set","b_uuid=${create_uuid()}")
                session:execute("set","RECORD_TITLE=Recording ${dialed_number} ${caller_id_number} ${strftime(%Y-%m-%d %H:%M)}")
                session:execute("set","RECORD_COPYRIGHT=(c) Buzzworks, Inc.")
                session:execute("set","RECORD_SOFTWARE=FreeSWITCH")
                session:execute("set","RECORD_ARTIST=Buzzworks")
                session:execute("set","RECORD_COMMENT=Buzz that works")
                session:execute("set","RECORD_DATE=${strftime(%Y-%m-%d %H:%M)}")
                session:execute("set","RECORD_STEREO=true")
                session:execute("record_session","/var/spool/freeswitch/default/${strftime(%d-%m-%Y-%H-%M)}_"..cc_customer.."_${b_uuid}.mp3")	
		if (status) then
			dial_string = qrow.dial_string
			dial_string = dial_string:gsub("${destination_number}", cc_customer)
			session:execute("bridge","{origination_uuid=${b_uuid},origination_caller_id_number="..or_caller_id_number..",call_mode="..dial_method..",disposition='Connected',cc_agent="..cc_agent..",campaign="..campaign..",contact_id="..contact_id..",phonebook="..phonebook..",usertype='client'}"..dial_string)
			session:execute("transfer","12312 XML default2")
		end
	end
end))
