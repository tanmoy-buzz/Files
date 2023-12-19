--Freeswitch session anwered here for playing ivr welcome msg.
mobile_num = string.sub(session:getVariable("caller_id_number"), -10)
uuid = session:getVariable("origination_uuid")
contact_id = session:getVariable("contact_id")
campaign = session:getVariable("campaign")
audio_dir = "/usr/local/freeswitch/sounds/custom_sounds/"
audio_dir2 = "/var/lib/flexydial/media/"
audio_dir3 = audio_dir2.."TTS/"
session:execute("set","cc_customer="..mobile_num)
session:execute("set", "cc_export_vars=cc_customer,cc_uname")
---This is the commands to connect database.
dbh = freeswitch.Dbh("odbc://freeswitch::")
assert(dbh:connected())
json = require "json"
ivr_nums=""
session:execute("answer")
session:execute("set","RECORD_TITLE=Recording ${dialed_number} ${caller_id_number} ${strftime(%Y-%m-%d %H:%M)}")
session:execute("set","RECORD_COPYRIGHT=(c) Buzzworks, Inc.")
session:execute("set","RECORD_SOFTWARE=FreeSWITCH")
session:execute("set","RECORD_ARTIST=Buzzworks")
session:execute("set","RECORD_COMMENT=Buzz that works")
session:execute("set","RECORD_DATE=${strftime(%Y-%m-%d %H:%M)}")
session:execute("set","RECORD_STEREO=true")
session:execute("record_session","/var/spool/freeswitch/default/${strftime(%d-%m-%Y-%H-%M)}_"..mobile_num.."_"..uuid..".mp3")
session:execute('set','disposition=Connected')
my_query = "select *,CAST(vb_data as TEXT)  from callcenter_voiceblaster where id in (select voiceblaster_id from callcenter_voiceblaster_campaign where campaign_id in (select id from callcenter_campaign where name='"..campaign.."'));"
assert(dbh:query(my_query, function(qrow)
	session:consoleLog("info", qrow.vb_data)
	data = json.decode(qrow.vb_data)
    	if (data ~= nil and data ~="") then
		if(data.hasDTMF) then
        		for k, v in pairs(data.vb_dtmf) do
                		ivr_nums = ivr_nums..k
        		end
		end
      	end
end))
vb_mode = ""
vb_mode_sql = "select vb_mode from callcenter_voiceblaster where id in (select voiceblaster_id from callcenter_voiceblaster_campaign where campaign_id in (select id from callcenter_campaign where name='"..campaign.."'))"
assert(dbh:query(vb_mode_sql, function(qrow2)
	session:consoleLog("info", qrow2.vb_mode)
	vb_mode = qrow2.vb_mode
end))
if (vb_mode ~= "1") then
	sql = "select audio_file from callcenter_audiofile where id in (select vb_audio_id from callcenter_voiceblaster where id in (select voiceblaster_id from callcenter_voiceblaster_campaign where campaign_id in (select id from callcenter_campaign where name='"..campaign.."')))"
	assert(dbh:query(sql, function(qrow2)
		audio_file=qrow2.audio_file

	end))
end
function makeHttpRequest(url)
    local command = "curl -sk '" .. url .. "'"
    local handle = io.popen(command)
    local result = handle:read("*a")
    handle:close()
    return result
end


function play_audio(ivr_nums)
	
	if (vb_mode == "1") then
		session:consoleLog("info", ivr_nums)
		local apiUrl = "https://localhost/api/voice-blaster-tts/"..contact_id.."/"
		local response = makeHttpRequest(apiUrl)
		session:consoleLog("info",response)
		audio_play = audio_dir3..contact_id..".mp3"
	else
		session:consoleLog("info", "else")
		audio_play = audio_dir2..audio_file
	end
	if (ivr_nums ~= "") then
        	digits = session:playAndGetDigits(1,1,3, 10000,"#", audio_play, audio_dir.."Invalid_digit.mp3","["..ivr_nums.."]", "digits_received",10000);
		if digits == "2" then 
			play_audio(ivr_nums)
		end
	else
		session:execute("playback",audio_play)
	end
	session:execute("playback",audio_dir.."thankyou.mp3")
	session:execute("hangup")
end
play_audio(ivr_nums)
