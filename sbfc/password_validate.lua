--Freeswitch session anwered here for playing ivr welcome msg.
callerId = session:getVariable("destination_number");
mobile_num = string.sub(session:getVariable("caller_id_number"), -10)
audio_dir = "/usr/local/freeswitch/sounds/custom_sounds/" 
---This is the commands to connect database.
dbh = freeswitch.Dbh("odbc://freeswitch::")
assert(dbh:connected())

json = require "json"
my_query ="select * from callcenter_campaign where id in (select id from callcenter_campaignvariable where wfh_caller_id='"..callerId.."');"
session:consoleLog("info",   my_query);
query2 = "select * from callcenter_uservariable  where wfh_numeric="..mobile_num
function get_password(password)
	validation=0
	count=1
	while (count <= 4) do
		session:answer();
		digits = session:playAndGetDigits(4,8,1, 10000,"#", audio_dir.."Enter_password.mp3", audio_dir.."Invalid_password.mp3","\\d+");
		if (digits == password) then
			validation = 1
			return validation
		else
			count = count + 1;
			session:execute("playback",audio_dir.."Invalid_password.mp3");
		end
	end
	session:execute("hangup")
end;

function check_ip_phones()
	ip_sql ="select extension from callcenter_uservariable where id in (select id from callcenter_user where caller_id='"..callerId.."');"
	ip_extension = nil
	user_data = nil 
    	assert(dbh:query(ip_sql, function(ip_qrow)
		if (ip_qrow ~= nil and ip_qrow ~="") then
			ip_extension=ip_qrow.extension
		end
	end));
	if (ip_extension ~= nil and ip_extension ~="") then
		api = freeswitch.API();
		user_data = api:execute("user_data", ip_extension.."@${domain} var call_protocal");
        	---user_data = api:execute("user_data", ip_extension.."@${domain} var call_protocal");
	end
	session:consoleLog("info", "${domain}");
	return ip_extension,user_data	
end;

function check_wfh()
    ip_extension,user_data = check_ip_phones()
    session:consoleLog("info", user_data);
    if (user_data ~= nil and user_data ~="" and user_data =="3") then
	session:execute("set","cc_agent="..ip_extension)
	session:execute("set","cc_customer="..mobile_num)
	session:execute("set","wfh=true")
	session:execute("set","usertype=client_ipphone")
	session:execute("set","call_mode=inbound")
	session:execute("set","disposition=Connected")
        session:execute("set","continue_on_fail=true")
        session:execute("set","b_uuid=${create_uuid()}")
        session:execute("set","RECORD_TITLE=Recording ${dialed_number} ${caller_id_number} ${strftime(%Y-%m-%d %H:%M)}")
        session:execute("set","RECORD_COPYRIGHT=(c) Buzzworks, Inc.")
        session:execute("set","RECORD_SOFTWARE=FreeSWITCH")
        session:execute("set","RECORD_ARTIST=Buzzworks")
        session:execute("set","RECORD_COMMENT=Buzz that works")
        session:execute("set","RECORD_DATE=${strftime(%Y-%m-%d %H:%M)}")
        session:execute("set","RECORD_STEREO=true")
        session:execute("record_session","/var/spool/freeswitch/default/${strftime(%d-%m-%Y-%H-%M)}_"..mobile_num.."_${b_uuid}.mp3")	 
	session:execute("bridge","{ignore_early_media=false,origination_uuid=${b_uuid}}user/"..ip_extension)
	return
    else 
        qrow = nil
        assert(dbh:query(my_query, function(qrow1)
            qrow = {} 
	    for key, val in pairs(qrow1) do
                qrow[key] = val
            end
        end));
        if (qrow ~= nil and qrow ~="") then
            if(qrow.wfh == '1') then
                campaign = qrow.name
                dial_method = json.decode(qrow.dial_method)
	        qrow = nil
    	        assert(dbh:query(query2, function(qrow2)
                    qrow = {}
                    for key, val in pairs(qrow2) do
                        qrow[key] = val
                    end
                end));
                if (qrow ~= 'null' and qrow ~= nil and qrow ~= "") then
                    session:execute("set","usertype=wfh_agent")
                    session:execute("set","wfh=true")
                    session:execute("set","outbound_dial_method="..dial_method.outbound)
                    if (qrow.extension ~= nil and campaign ~= nil) then
                        session:execute("set","cc_agent="..qrow.extension)
                        session:execute('set', 'cc_export_vars=cc_agent,wfh,usertype');
                        session:execute("set","campaign="..campaign)
                        if (qrow.wfh_password ~= nil and qrow.wfh_password ~="") then
                                status = get_password(qrow.wfh_password)
                                if status == 1 then
                                        if  qrow.w_req_callback == '1' then
                                                session:execute("event", "Event-Subclass=CUSTOM::WFH-REQ-CALLBACK,Event-Name=CUSTOM");
                                                session:answer();
                                                session:execute("hangup")
                                        else
                                                session:execute("event", "Event-Subclass=CUSTOM::LOGIN,Event-Name=CUSTOM");
                                                session:execute("socket","127.0.0.1:8084 async full")

                                        end
                                end
                        else
                                if  qrow.w_req_callback == '1' then

                                         session:execute("event", "Event-Subclass=CUSTOM::WFH-REQ-CALLBACK,Event-Name=CUSTOM");
                                         session:answer();
                                         session:execute("hangup")

                                 else
                                        session:execute("event", "Event-Subclass=CUSTOM::LOGIN,Event-Name=CUSTOM");
                                        session:execute("socket","127.0.0.1:8084 async full")

                                end

                        end
                else
                        session:execute("socket","127.0.0.1:8087 async full")
                end
            else
                session:execute("socket","127.0.0.1:8087 async full")
            end
        else
                session:execute("socket","127.0.0.1:8087 async full")
        end
    else
            session:execute("socket","127.0.0.1:8087 async full")
    end
   end
end
check_wfh()
