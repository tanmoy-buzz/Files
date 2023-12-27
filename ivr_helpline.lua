--Freeswitch session anwered here for playing ivr welcome msg.
session:answer();
callerId = session:getVariable("destination_number");
audio_dir = "/var/lib/flexydial/media/" 
count=1
---This is the commands to connect database.
dbh = freeswitch.Dbh("odbc://freeswitch::")
assert(dbh:connected())
json = require "json"

my_query = "select * from callcenter_skilledrouting as a inner join callcenter_skilledroutingcallerid as b on a.id = b.skill_id where caller_id ='"..callerId.."'"

ivr_nums = ""
wellcome_gt = ""

--This is the function to check digit is exited in skill route table.
function setContains(set, key)
    return set[key] ~= nil
end

--This is the code for get the Skill routed queues.
assert(dbh:query(my_query, function(qrow)
      data = json.decode(qrow.skills)
      if (data ~= nil and data ~="") then
      	for k, v in pairs(data) do
      		ivr_nums = ivr_nums..k
        end
      end
      audio_jsn = json.decode(qrow.audio)
      session:consoleLog("log",audio_jsn.welcome_file)
      audio_query = "select * from callcenter_audiofile where name ='"..audio_jsn.welcome_file.."'"
      assert(dbh:query(audio_query, function(aqrow)
	wellcome_gt = audio_dir..aqrow.audio_file
	digits="default"
	digit_chk = setContains(data,digits)
	if (digit_chk) then
		session:execute("playback",wellcome_gt);
	else
		digits = session:playAndGetDigits(1,1,3, 10000, "",wellcome_gt,"Wrong_entry.mp3","["..ivr_nums.."]", "digits_received",10000);
	end
      end))
end))

--This is the function is repeat main menu agian.
function recall_main_menu(digits,callerId)
    digits = session:playAndGetDigits(1,1,3, 10000, "",wellcome_gt,"Wrong_entry.mp3","["..ivr_nums.."]", "digits_received",10000);
    if (digits ~= "") then 
        main_menu(digits,callerId)
    else
    	session:execute("playback","Wrong_entry.mp3");
    	session:hangup();
    end
end

--This is the function to check digit is exited in skill route table.
function setContains(set, key)
    return set[key] ~= nil
end

--This is the funcation of main menu.
function main_menu(digits,callerId)
	digit_chk = setContains(data,digits)
	if (digit_chk) then
		if (data[digits] == "repeat") then
	        	if (count <= 3) then
        	        	count = count + 1
                		recall_main_menu(digits,callerId)
        		else
                		session:hangup();
        		end
             	elseif (data[digits] == "hangup") then
                	 session:hangup();		     
             	else
			queue = data[digits]     
                	if (queue ~= "") then
			    sql="SELECT * FROM callcenter_campaign where name ='"..queue.."'"
	                    assert(dbh:query(sql, function(aqrow)
                                callback_digit = aqrow.queued_busy_callback
                            end))
				session:execute('set', "queued_busy_callback="..callback_digit);
				session:execute('event', "Event-Subclass=CUSTOM::queued_busy_callback,Event-Name=CUSTOM");
                        	session:execute('callcenter',queue)
                	else
                        	session:hangup();
                	end
	     	end
         
	else
        	session:execute("playback","Wrong_entry.mp3");
             	session:hangup();
	end
	return 
end
if digits ~= "" then
   main_menu(digits,callerId)
else
    session:execute("playback","Wrong_entry.mp3");
    session:hangup();
end
