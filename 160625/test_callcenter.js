(function () {
	util = require('util');
	esl = require('esl');
	var fs = require('fs');
	var https = require('https');
	var inbound = require("./inboundcall.js");
	var transfer_call = require("./transfercall_route.js");
	var MEDIA_ROOT = '/var/lib/flexydial/media'
	// Socket io initialization starts
	const options =
					{
						 key: fs.readFileSync('/etc/ssl/flexydial.key'),
						 cert: fs.readFileSync('/etc/ssl/flexydial.crt')
					};
	var socket_server = https.createServer(options);
	var io = require('socket.io')(socket_server);
	socket_server.listen(3232)
	
	var redis = require('redis');
	leadlist_details_data = redis.createClient();
	//leadlist_details_data = redis.createClient({host : 'localhost', port : 6379, password : 'Flexydial@123'});
	leadlist_details_data.subscribe('lead-details');
	
	changestatefeedback = redis.createClient();
	changestatefeedback.subscribe('hangup_client_on_fs_hangup');
	
	io.on('connection', function(socket) {
		socket.on('new',function(data){
			console.log(data)
		 });
		leadlist_details_data.on('message',function(channel, message){
				socket.send(message);
			});
		changestatefeedback.on('message',function(channel, message){
			socket.send(message);
		});
		 socket.on('transfer',function(data){
			 if (data['transfer_type'] == 'external'){
				 console.log('external',data)
			 }else{
				transfer_call.transfercall_route(data,function(err,data){
					io.emit("transfer_agents",data)
				})	 		
			 }
		});
		
		socket.on('tr_internal_agent_answer',function(data){
			io.emit("tr_internal_agent_answer_res",data)
		});	
	
		socket.on('transfer_to_agent_rejected',function(data){
			transfer_call.transfercall_del_alert(data,function(err,data){
				io.emit("transfer_to_agent_rejected_res",data)
			})	 		
		});	
	
		socket.on('tr_from_agent_hangup',function(data){
			transfer_call.transfercall_del_alert(data,function(err,data){
				io.emit("tr_from_agent_hangup_res",data)
			})	 			
		});
		socket.on("dial_number_transfer_to_agent",function(data){
			io.emit("dial_number_transfer_to_agent_res",data)
		});
		socket.on('emergency_logout',function(data){
			io.emit("do_emergency_logout",data)
		});	
		socket.on('emergency_logout_status',function(data){
			io.emit("emergency_logout_status_admin",data)
		});
		socket.on('emergency_all_logout_status',function(data){
			io.emit("emergency_all_logout_status_admin",data)
		});
		socket.on('emergency_logout_all_users',function(data){
			io.emit("do_emergency_logout_all_users",data)
		});	
		socket.on('broadcast_message_to_users',function(data){
			io.emit("do_broadcast_message",data)
		});	
		socket.on('check_progressive_preview_data',function(data){
			io.emit("do_progressive_preview_newlead",data)
		});		
	});
	
	server = esl.createCallServer();
	server.on('CONNECT', function (req) {
			if ('variable_wfh' in req.body & req.body['variable_wfh'] == 'true'){
				if (req.body['variable_usertype'] != 'wfh-agent-req-dial'){
					dial_method = req.body['variable_outbound_dial_method']
					if (dial_method == 'Predictive' | dial_method == 'Progressive' | dial_method == 'Preview'){
						req.execute("transfer","12345 XML default2")
					} 
				}
			}else{
				server_ip = req.body['variable_sip_from_host']
				if (('variable_sip_from_host' in req.body)==false){
					server_ip = req.body['FreeSWITCH-IPv4']
				}
				io.emit('sip_session_details',{'Unique-ID':req.body['Unique-ID'], 
					'Caller-Caller-ID-Number':req.body['Channel-Orig-Caller-ID-Number'],
					'variable_sip_from_host': server_ip
				});
				req.execute("transfer","00019916 XML default")
			}
			req.on('DTMF', function (req) {
				dtmf = req.body['DTMF-Digit']
				if ('variable_wfh' in req.body & req.body['variable_wfh'] == 'true') {
					if ('Other-Leg-Unique-ID' in req.body){
						uuid = req.body['Other-Leg-Unique-ID']
						session_uuid = req.body['Unique-ID']
						if(dtmf == '1'){
							action = 'customer_name'
							inbound.wfh_customer_details_route(req,uuid,session_uuid,action,function(err,data){
								req.execute_uuid(session_uuid, 'playback', `${MEDIA_ROOT}/${session_uuid}.mp3`);
								// req.execute_uuid(session_uuid, 'playback', `${MEDIA_ROOT}/${session_uuid}.wav`);
							})            	
							//inbound.wfh_client_hangup(uuid, action='customer_name', function(err,data){
							// })
							// req.execute_uuid(uuid, 'set', 'tts_engine=flite');                     
							// req.execute_uuid(uuid, 'set', 'tts_voice=slt');
							// req.execute_uuid(uuid, 'speak', 'hello dinesh');
						}else if(dtmf == '2'){
							action = 'customer_number'
							inbound.wfh_customer_details_route(req,uuid,session_uuid,action,function(err,data){
								req.execute_uuid(session_uuid, 'playback', `${MEDIA_ROOT}/${session_uuid}.mp3`);
								// req.execute_uuid(session_uuid, 'playback', `${MEDIA_ROOT}/${session_uuid}.wav`);
							}) 
						}else if(dtmf == '#'){
							inbound.wfh_client_hangup(uuid, action='unmute', function(err,data){
							})
						}else if(dtmf == '*'){
							inbound.wfh_client_hangup(uuid, action='mute', function(err,data){
							})
						}else if(dtmf == '0'){
							req.execute_uuid(uuid, 'hangup');
							// inbound.wfh_client_hangup(uuid, action='hangup', function(err,data){
							// })            		
						}
					} 
				   }         
				return util.log('DTMF',dtmf,"a-leg : ",req.body['Unique-ID']," b-leg : ",req.body['Other-Leg-Unique-ID']);
			})
			req.on('CHANNEL_ANSWER',function (req){
				if ('variable_wfh' in req.body & req.body['variable_wfh'] == 'true'){
					if (req.body['variable_usertype'] == 'wfh-agent-req-dial'){
						req.execute("transfer","12345 XML default2")
					} 			
				}
			})	
			req.on('CHANNEL_HANGUP', function (req) {
				if (!('variable_wfh' in req.body)){
					io.emit("sip_hangup_client",req.body['variable_cc_agent'])
				}
				return util.log('CHANNEL_HANGUP',req.body['variable_cc_agent']);
		 });
	
	});
	server.listen(8084);
	
	outbound_server = esl.createCallServer();
	outbound_server.on('CONNECT', function (req) {
		//console.log(req.body)
		var campaign_name = req.body['variable_campaign_name']
		var usertype =req.body['variable_usertype']
		req.execute('set', 'campaign_name=${campaign_name}');
		req.execute('set', 'usertype=${usertype}');
		req.execute('set', 'cc_export_vars=campaign_name,usertype');
		req.execute('set','disposition=NC')
		var date_time = '${strftime(%d-%m-%Y-%H-%M)}'
		var destination_number = req.body['Channel-Caller-ID-Number'].slice(-10)
		var cc_agent = req.body['variable_cc_agent']
		var dialed_uuid = req.body['Unique-ID']
		if (!('wfh_call' in req.body)){
			req.execute("conference",req.body['variable_agent-Unique-ID']+"@sla")
		}
		req.execute('set', `cc_customer=${destination_number}`)
		req.execute('set', 'RECORD_TITLE=Recording ${dialed_number} ${caller_id_number} ${strftime(%Y-%m-%d %H:%M)');
		req.execute('set', 'RECORD_COPYRIGHT=(c) Buzzworks, Inc.');
		req.execute('set', 'RECORD_SOFTWARE=FreeSWITCH');
		req.execute('set', 'RECORD_ARTIST=Buzzworks');
		req.execute('set', 'RECORD_COMMENT=Buzz that works');
		req.execute('set', 'RECORD_DATE=${strftime(%Y-%m-%d %H:%M)}');
		req.execute('set', 'RECORD_STEREO=true');
		req.execute("record_session",`/var/spool/freeswitch/default/${date_time}_${destination_number}_${dialed_uuid}.mp3`)			
		console.log("outbound connected");
		req.on('CHANNEL_ANSWER', function (req) {
			console.log(req.body['Event-Date-Timestamp'])
			// req.execute("bridge","user/"+cc_agent)
			if('variable_fake_ring' in req.body && req.body['variable_fake_ring'] == 'true'){
				var date_time = '${strftime(%d-%m-%Y-%H-%M)}'
				var destination_number = req.body['variable_cc_customer'].slice(-10)
				var dialed_uuid = req.body['Unique-ID']
				req.execute("conference",req.body['variable_agent-Unique-ID']+"@sla")
				req.execute('set', 'RECORD_TITLE=Recording ${dialed_number} ${caller_id_number} ${strftime(%Y-%m-%d %H:%M)');
				req.execute('set', 'RECORD_COPYRIGHT=(c) Buzzworks, Inc.');
				req.execute('set', 'RECORD_SOFTWARE=FreeSWITCH');
				req.execute('set', 'RECORD_ARTIST=Buzzworks');
				req.execute('set', 'RECORD_COMMENT=Buzz that works');
				req.execute('set', 'RECORD_DATE=${strftime(%Y-%m-%d %H:%M)}');
				req.execute('set', 'RECORD_STEREO=true');
				req.execute("record_session",`/var/spool/freeswitch/default/${date_time}_${destination_number}_${dialed_uuid}.mp3`)
			}
			req.execute('set','disposition=Connected')
			if(req.body['variable_usertype'] == 'transfer_client' || req.body['variable_usertype'] == 'conference_client'){
				io.emit("OUTBOUND_TRANSFER_CHANNEL_ANSWER",req.body['variable_cc_agent'])
			}else{
				io.emit("OUTBOUND_CHANNEL_ANSWER",{'sip_extension':req.body['variable_cc_agent'],'call_timestamp':req.body['Event-Date-Timestamp']})
			}
			return util.log('OUTBOUND_CHANNEL_ANSWER',req.body['variable_cc_agent']);
		})
		req.on('CHANNEL_BRIDGE', function (req) {
			return util.log('OUTBOUND_CHANNEL_BRIDGE');
		})
		req.on('CALL_UPDATE', function (req) {
			return util.log('OUTBOUND_CALL_UPDATE');
		})
		req.on('CHANNEL_HANGUP', function (req) {
			if( req.body['variable_transfer_status']=='true'){
				io.emit("OUTBOUND_CHANNEL_HANGUP",{"sip_extension":req.body['Other-Leg-Orig-Caller-ID-Number'],"dialed_number":destination_number})
				return util.log('OUTBOUND_TRANSFERED_CHANNEL_HANGUP',req.body['Other-Leg-Orig-Caller-ID-Number']);
			}else{
				if(req.body['variable_usertype'] == 'transfer_client'){
					io.emit("OUTBOUND_TRANSFER_CHANNEL_HANGUP",req.body['variable_cc_agent'])
					return util.log('OUTBOUND_TRANSFER_CHANNEL_HANGUP',req.body['variable_cc_agent']);
				}else if(req.body['variable_usertype'] == 'conference_client') {
					io.emit("OUTBOUND_CONFERENCE_CHANNEL_HANGUP",{"sip_extension":req.body['variable_cc_agent'],"conference_num_uuid":req.body['Unique-ID'],
						"dialed_number":req.body['Caller-Caller-ID-Number']})
					return util.log('OUTBOUND_CONFERENCE_CHANNEL_HANGUP',req.body['variable_cc_agent']);
				}else{
					io.emit("OUTBOUND_CHANNEL_HANGUP", {"sip_extension":req.body['variable_cc_agent'],"dialed_number":destination_number})
					return util.log('OUTBOUND_CHANNEL_HANGUP',req.body['variable_cc_agent']);
				}
			}
		})
		req.on('CHANNEL_HANGUP_COMPLETE', function (req) {
			return util.log('OUTBOUND_CHANNEL_HANGUP_COMPLETE');
		})
	});
	outbound_server.listen(8085);
	inbound_server = esl.createCallServer();
	inbound_server.on('CONNECT', function (req) {
			var channel_data = req.body;
			destination_number = req.body['Caller-Caller-ID-Number'].slice(-10)
			caller_id = req.body['Caller-Destination-Number']
			dialed_uuid = req.body['Unique-ID']
			server = req.body['variable_sip_to_host']
			date_time = '${strftime(%d-%m-%Y-%H-%M)}'
			var callback = ""
			audio_played = false
			inbound.inboundcall_route(req,caller_id,dialed_uuid,server,destination_number,function(err,data){
				if (data['dial_method']['ibc_popup']==true){
					req.execute('set', 'call_mode=inbound');
					data['destination_number']= destination_number
					data['dialed_uuid']= dialed_uuid
					intiate_time = req.body['Channel-Channel-Created-Time']
					if (data['non_office_hrs']==false){
						// req.execute("record_session",`/var/spool/freeswitch/default/${date_time}_${destination_number}_${dialed_uuid}.mp3`)
						io.emit("inbound_agents",data)
						req.execute('set','no_agent_audio=false')
						if (data['no_agent_audio'] & data['audio_moh_sound'] != null & audio_played == false){
							req.execute('set','no_agent_audio=true')
							req.execute("answer")
							audio_played = true
							req.execute('endless_playback', `${MEDIA_ROOT}/${data['audio_moh_sound']}`)
						}					
						inbound.availale_agents(req,caller_id,dialed_uuid,server,destination_number,intiate_time,function(err,data){
							if (data['cust_status'] == 'true'){
								io.emit("inbound_agents",data)
							}else{
								if(data['cust_status'] == 'timeout'){
									req.execute('hangup');
								}
							}
						})
					}else{
						req.execute('hangup');
					}
				}else if(data['dial_method']['inbound']== true & data['dial_method']['ibc_popup']==false){
					if (data['queue_call']==true){
						call_mode = 'inbound'
						callback = data['callback']
						if(data['dial_method']['outbound']=='Predictive'){
							call_mode = 'inbound-blended'
						}
						var domain_name = channel_data['variable_sip_from_host'];
						req.execute('set', 'hangup_after_bridge=false');
						req.execute('set', `call_mode=${call_mode}`);
						if (data['non_office_hrs']==false){
							if (data['StickyAgent'] != true ){
								req.execute('set', `cc_customer=${destination_number}`);
								req.execute('set', 'cc_export_vars=cc_customer');
								req.execute('callcenter', data['campaign']);
								req.execute('answer');
							}else{
								data['dialed_uuid']= dialed_uuid
								io.emit("inbound_StickyAgent",data)
							}
						}else{
							req.execute('hangup');
						}
					}else{
						req.execute('set', 'call_mode=inbound');
						data['destination_number']= destination_number
						data['dialed_uuid']= dialed_uuid
						if (data['non_office_hrs']==false){
	
							io.emit("inbound_agents",data)
						}else{
							req.execute('hangup');
						}
					}					
				}else if(data['queue_call']==true & data['skill_routed_status']==true){
						req.execute('set', 'call_mode=inbound');
						req.execute('set', `cc_customer=${destination_number}`);
						req.execute('set', 'cc_export_vars=cc_customer');
						if (data['non_office_hrs']==false){
							req.execute("transfer",`${caller_id} XML default2`)
						}else{
							req.execute('hangup');	
						}	
				}
			})
			req.on('CUSTOM', function (req) {
				if(req.body['Event-Subclass'] == 'CUSTOM::queued_busy_callback'){
					if (req.body['variable_queued_busy_callback']){
						callback = req.body['variable_queued_busy_callback']
					}
				}
				if (req.body['CC-Action'] == 'member-queue-end' && req.body['CC-Cause'] == 'Cancel'){
					if ('CC-Cancel-Reason' in req.body){
						if (req.body['CC-Cancel-Reason'] == 'TIMEOUT'){
							req.execute('hangup');	
						}
					}
	
				}
			})
	
			 req.on('CHANNEL_ANSWER', function (req) {
					 if (req.body['variable_ibc_popup']=='True' && req.body['variable_queue_call']=='False'){
						 answered_agent = req.body['variable_cc_agent']
						 if (answered_agent){
							   dialed_uuid = req.body['Unique-ID']
							   destination_number = req.body['Caller-Caller-ID-Number'].slice(-10)
							   date_time = '${strftime(%d-%m-%Y-%H-%M)}'
							   req.execute('set','disposition=Connected')
							   req.execute('set', 'cc_customer=${destination_number}');
							   req.execute('set', 'cc_export_vars=cc_customer,cc_uname,disposition');                                  
							   req.execute("record_session",`/var/spool/freeswitch/default/${date_time}_${destination_number}_${dialed_uuid}.mp3`)
							   inbound.inboundcall_dis_alert(answered_agent,dialed_uuid,state='answer',function(err,data){
								   dict_data = {'dialed_uuid':dialed_uuid,'extension':data}
								   io.emit("inbound_notanswer_agents",dict_data)
							   })
						   }
					 }
				return util.log('INBOUND_CHANNEL_ANSWER');
			})
			req.on('CHANNEL_BRIDGE', function (req) {
					callback = ""
					req.execute('set','disposition=Connected')
					if (req.body['variable_ibc_popup']=='False'  && req.body['variable_queue_call']=='True'){
						destination_number = req.body['Caller-Caller-ID-Number'].slice(-10)
						dialed_uuid = req.body['Unique-ID']
						// date_time = '${strftime(%d-%m-%Y-%H-%M)}'
						// req.execute("record_session",`/var/spool/freeswitch/default/${date_time}_${destination_number}_${dialed_uuid}.mp3`)
						req.execute('set','disposition=Connected')
						req.execute('set', 'cc_customer=${destination_number}');
						req.execute('set', 'cc_export_vars=cc_customer,cc_uname,disposition');
						io.emit("INBOUND_CHANNEL_BRIDGE",{"sip_extension":req.body['Other-Leg-Orig-Caller-ID-Number'],
												"customer_number":destination_number,"dialed_uuid":dialed_uuid,
												"call_timestamp":req.body['Event-Date-Timestamp'],"campaign":req.body['variable_campaign']})
					}else if(req.body['variable_ibc_popup']=='True' & 'variable_no_agent_audio' in req.body & req.body['variable_no_agent_audio'] == 'true'){
						answered_agent = req.body['variable_cc_agent']
						 if (answered_agent){
							   dialed_uuid = req.body['Unique-ID']
							   destination_number = req.body['Caller-Caller-ID-Number'].slice(-10)
							   date_time = '${strftime(%d-%m-%Y-%H-%M)}'
							   req.execute('set','disposition=Connected')
							   req.execute('set', 'cc_customer=${destination_number}');
							   req.execute('set', 'cc_export_vars=cc_customer,cc_uname,disposition');                                  
							   req.execute("record_session",`/var/spool/freeswitch/default/${date_time}_${destination_number}_${dialed_uuid}.mp3`)
							   inbound.inboundcall_dis_alert(answered_agent,dialed_uuid,state='answer',function(err,data){
								   dict_data = {'dialed_uuid':dialed_uuid,'extension':data}
								   io.emit("inbound_notanswer_agents",dict_data)
							   })
						   }					
					}
				return util.log('INBOUND_CHANNEL_BRIDGE');
			 })
	
			req.on('CALL_UPDATE', function (req) {
				 return util.log('INBOUND_CALL_UPDATE');
					})
	
			var dtmf = ""
			req.on('DTMF', function (req) {
				if(dtmf == ""){
					t=setTimeout(function(){
						dtmf = "" 
					}, 5000);
				}
				dtmf = req.body['DTMF-Digit'] 
				c_dtmf = dtmf.concat(dtmf);
				if (c_dtmf == callback.concat('#')){
					clearTimeout(t);
					dtmf = ""
					req.execute('set','disposition=CBR')
					req.execute('hangup');
				}         
				return util.log('INBOUND_DTMF');
			})
			
			req.on('CUSTOM', function (req) {
				if (req.body['CC-Action'] == 'member-queue-end' && req.body['CC-Cause'] == 'Cancel'){
					if ('CC-Cancel-Reason' in req.body){
						if (req.body['CC-Cancel-Reason'] == 'TIMEOUT'){
							req.execute('hangup');	
						}
					}
	
				}
			})
	
			req.on('CHANNEL_HANGUP', function (req) {
				 dialed_uuid = req.body['Unique-ID']
				 if (req.body['variable_ibc_popup']=='True' | req.body['variable_queue_call']=='False'){
					 inbound.inboundcall_dis_alert(answered_agent='',dialed_uuid,state='hangup',function(err,data){
						 dict_data = {'dialed_uuid':dialed_uuid,'extension':data}
						 io.emit("inbound_notanswer_agents",dict_data)
					})
					 inbound.inboundcall_del_alert(dialed_uuid)			
				 }	 		
				 // console.log({"sip_extension":req.body['variable_cc_agent'],"ibc_popup":req.body['variable_ibc_popup'],"queue_call":req.body['variable_queue_call']})
				io.emit("INBOUND_CHANNEL_HANGUP",{"sip_extension":req.body['variable_cc_agent'],"ibc_popup":req.body['variable_ibc_popup'],"queue_call":req.body['variable_queue_call']})
				return util.log('INBOUND_CHANNEL_HANGUP');
			})
						
			req.on('CHANNEL_HANGUP_COMPLETE', function (req) {
				 return util.log('INBOUND_CHANNEL_HANGUP_COMPLETE');
			})
		});
	inbound_server.listen(8087);
	
	autodial_server = esl.createCallServer();
	autodial_server.on('CONNECT', function (req) {
					var channel_data = req.body;
					var callback = channel_data['variable_queued_busy_callback']
					var unique_id = channel_data['Unique-ID'];
					var caller_id_number = channel_data['Caller-Caller-ID-Number'];
					var destination_number = channel_data['Caller-Destination-Number'];
					var campaign = channel_data['variable_campaign'];
					var contact_id = channel_data['variable_contact_id'];
					var phonebook = req.body['variable_phonebook']
					req.execute('set', 'hangup_after_bridge=false');
					req.execute('set', 'cc_customer=${caller_id_number}');
					req.execute('set', 'cc_export_vars=cc_customer,cc_uname,campaign,disposition,contact_id,phonebook');
					req.execute('callcenter', campaign);
					req.execute('answer');
					req.execute('hangup');
					req.on('CHANNEL_BRIDGE', function (req) {
						callback = ""	
						var bridge_agent = req.body['Other-Leg-Orig-Caller-ID-Number']
						var dialed_uuid = req.body['Unique-ID']
						req.execute('set','disposition=Connected')
						io.emit("AUTODIAL_CHANNEL_BRIDGE",{"sip_extension":req.body['Other-Leg-Orig-Caller-ID-Number'],
												"customer_number":req.body['variable_cc_customer'],"dialed_uuid":req.body['Unique-ID'],
												"call_timestamp":req.body['Event-Date-Timestamp'],"contact_id":contact_id})
								console.log('Bridging');
					});
					req.on('CALL_UPDATE', function (req) {
							console.log('call updated');
					});
	
					// req.on('DTMF', function (req) {
					// 	console.log(req.body)
					// 	return util.log('Autodial_DTMF');
					// })		
	
					req.on('CHANNEL_ANSWER', function (req) {
							return util.log('Call was answered');
					});
	
					req.on('CUSTOM', function (req) {
						if (req.body['CC-Action'] == 'member-queue-end' && req.body['CC-Cause'] == 'Cancel'){
							if ('CC-Cancel-Reason' in req.body){
								if (req.body['CC-Cancel-Reason'] == 'TIMEOUT'){
									req.execute('hangup');	
								}
							}
	
						}
					})
									
					req.on('CHANNEL_HANGUP', function (req) {
							io.emit("AUTODIAL_CHANNEL_HANGUP",{"sip_extension":req.body['variable_cc_agent']})
							return util.log('CHANNEL_HANGUP');
					});
	
					req.on('CHANNEL_CALLSTATE', function (req) {
							return util.log('CHANNEL_CALLSTATE');
					});
					req.on('CHANNEL_HANGUP_COMPLETE', function (req) {
							return util.log('CHANNEL_HANGUP_COMPLETE');
					});
					req.on('DISCONNECT', function (req) {
							return util.log('DISCONNECT');
					});
					req.on('uncaughtException', function (req) {
							return util.log('Epipe Error');
					});
					req.on('error', function (req) {
							return util.log('Epipe Error');
					});
			});
	autodial_server.listen(8086);
	
	
	}).call(this);
	
	// Emergency logout event from admin
	
	
