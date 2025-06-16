autodial_hangup = false
inbound_hangup = false
blended_hangup = false
var dap_details_data = ""
var admin_socket = '';
// var nodejs_port = '3233';
// admin_socket = io('https://'+server_ip + ':' + nodejs_port, {
//     'reconnection': true,
//     'reconnectionDelay': 2000,
//     'reconnectionDelayMax': 5000,
//     'reconnectionAttempts': 10
// });
// socket = io(host + ':' + nodejs_port);
function prepare_data_to_store() {
	if ($.inArray(agent_info_vue.state,['InCall','Feedback']) == -1){
		var agent_activity_data = create_agent_activity_data()
		agent_activity_data["campaign"] = campaign_name
		agent_activity_data["login_user"] = user_name
		if (extension in session_details) {
			agent_activity_data['switch_ip'] = session_details[extension]["variable_sip_from_host"]
			agent_activity_data['uuid'] = session_details[extension]['Unique-ID']
		}
		if (autodial_status == true){
			agent_activity_data["predictive_time"] = sessionStorage.getItem("predictive_time")
			agent_activity_data['predictive_wait_time'] = sessionStorage.getItem('wait_time')
			agent_activity_data['call_type'] = "autodial"
			agent_activity_data['autodial_status'] = autodial_status
			agent_activity_data['sip_error'] = true;
		}
		if(agent_info_vue.state == 'OnBreak'){
			agent_activity_data["break_type"] = agent_info_vue.selected_status
			agent_activity_data["break_time"] = sessionStorage.getItem("break_time");
			agent_activity_data["tos_time"] = sessionStorage.getItem("break_time");
		}
	}else{
		auto_feedback = true
		sip_error = true
		if (!hangup_time){
			hangup_time = new Date($.now());
		}
		agent_activity_data = create_feedback_data()
	}
	agent_activity_data['agent_state'] = agent_info_vue.state
	flush_agent_timer()
	$('#idle_timer, #wait_timer, #predictive_timer, #break_timer').countimer('stop')
	$('#idle_timer, #wait_timer, #predictive_timer, #break_timer').text('0:0:0')
	sessionStorage.setItem("idle_time", "0:0:0");
	sessionStorage.setItem("wait_time", "0:0:0");
	sessionStorage.setItem("predictive_time", "0:0:0");
	sessionStorage.setItem("break_time", "0:0:0");
	if (call_type == 'webrtc') {
		if (sipStack) {
			sipStack.stop()
		}
		SIPml["b_initialized"] = false
	} else {
		agent_activity_data['call_protocol'] = call_type
	}
	return agent_activity_data
}
function common_function_before_page_unload (event_name, event_created_by="") {
	agent_activity_data = prepare_data_to_store()
	agent_activity_data["event"] = event_name
	if(!window_reload_stop){	
		$.ajax({
			type:'post',
			headers: {"X-CSRFToken":csrf_token},
			url: '/api/window_reload/',
			data: agent_activity_data,
			success: function(data){ 
				if(event_name.indexOf("Force Logout") != -1) {
					socket.emit("emergency_logout_status", {"extension":extension, "username":event_created_by})
					app_logout=true
					window.location.href = "/logout/"
				}
			}
		});
	}
}
function timer_div() {
	$('#fb_timer_div').removeClass('d-none');
	$("#fb_timer").click()
	$("#fb_timer").remove()
	$("#dummy-fb-time").append('<span id="fb_timer" class="pl-1"></span>')
	// $("#fb_timer").countimer('start');
	var camp_feedback_time = $("#select_camp option:selected").attr("data-feedback_time")
	var camp_progressive_time = $('#select_camp option:selected').attr("data-progressive_time")
	if (camp_feedback_time != "None") {
		if(camp_feedback_time){
			camp_feedback_time = camp_feedback_time.split(":")
			$("#fb_timer").countdowntimer({
				// hours : camp_feedback_time[0],
				minutes : camp_feedback_time[0],
				seconds : camp_feedback_time[1],
				size : "lg",
				timeUp:stopped_feedback_func,
				stopButton : "fb_timer"
			 });
		}else{
			$("#fb_timer").countimer({
				autoStart: false,
				enableEvents: true,
				initHours: "00",
				initMinutes: "00",
				initSeconds: "00",
			});
			$("#fb_timer").countimer('start')
		}
	}else{
		$("#fb_timer").countimer({
				autoStart: false,
				enableEvents: true,
				initHours: "00",
				initMinutes: "00",
				initSeconds: "00",
			});
			$("#fb_timer").countimer('start')
	}	  
}
function progressive_timer(){
	var camp_progressive_time = $('#select_camp option:selected').attr("data-progressive_time")
	$("#fb_timer").click()
	$("#fb_timer").remove()
	$("#dummy-fb-time").append('<span id="fb_timer" class="pl-1"></span>')
	if(camp_progressive_time != "None") {
		if(camp_progressive_time){
			// camp_progressive_time = moment.utc(camp_progressive_time*1000).format('HH:mm:ss');
			camp_progressive_time = camp_progressive_time.split(":")
			$("#fb_timer").countdowntimer({
				// hours : camp_progressive_time[0],
				minutes : camp_progressive_time[0],
				seconds : camp_progressive_time[1],
				size : "lg",
				timeUp:stopped_feedback_func,
				stopButton : "fb_timer",
				pauseButton : "timer_pause_progressive"
			});	
		}else{
			$("#fb_timer").countdowntimer({
				hours : 0,
				minutes : 1,
				size : "lg",
				timeUp:stopped_feedback_func,
				stopButton : "fb_timer"
			});
		}
	}
	else{
		$("#fb_timer").countdowntimer({
		hours : 0,
		minutes : 1,
		size : "lg",
		timeUp:stopped_feedback_func,
		stopButton : "fb_timer"
		});
	}	  
}
function timer_on_hangup() {
	$('#SecondsDISP').countimer('stop');
	timer_div()
	$("#btnParkCall, #btnTransferCall").prop('disabled', false);
	hangup_activity()
}
sip_error = false
function socketevents (){
	if(socket){
		socket.emit('new','sip_intialized');
		socket.on("event", function (data){
			alert(data);
		});
		socket.on("update", function(data){
			alert(data)
		})
		socket.on("cc_hangup", function(data){
			alert(data);
		})
		socket.on("error",function(data){
			$('.preloader').fadeIn('fast');
			errorAlert("Connetion Error","Error occured with Node connetion");
			$('#btnLogMeOut').click();
		})
		socket.on("sip_hangup_client", function(data){
			if (extension == data){
				if (user_role =='Agent' || non_agent_user){
					if(agent_info_vue.state!=='OnBreak'){
						// errorAlert("Sip Hangup occured");
						sip_error = true
						if ($.inArray(agent_info_vue.state,['InCall','Feedback']) == -1){
							var agent_activity_data = {}
							var camp = $("#select_camp option:selected").text()
							agent_activity_data["campaign_name"] = campaign_name
							agent_activity_data["event"] = "Sip Reinitialize"
							$.ajax({
								type:'post',
								headers: {"X-CSRFToken":csrf_token},
								url: '/CRM/save-agent-breaks/',
								data: agent_activity_data,
								success: function(data){ }
							})
						}
						else {
							if (Object.keys(dummy_session_details) ==0){
								dummy_session_details = {...session_details[extension]}
							}
							var agent_activity_data = {}
							var camp = $("#select_camp option:selected").text()
							agent_activity_data["campaign_name"] = campaign_name
							agent_activity_data["event"] = "Sip Hangup"
							$.ajax({
								type:'post',
								headers: {"X-CSRFToken":csrf_token},
								url: '/CRM/save-agent-breaks/',
								data: agent_activity_data,
								success: function(data){
									if ($('#btnDialHangup').attr("title") == 'Hangup Call'){
										$('#btnDialHangup').click()
									}
								},
								error: function(data){
									if ($('#btnDialHangup').attr("title") == 'Hangup Call'){
										$('#btnDialHangup').click()
									}
								}
							});
						}
					}				
				}
				else{
					session_details[extension] = {}
					if($('#eavesdrop_session').prop('checked') == true){
						errorAlert('OOPS!!! Something Went Wrong',"Sip Hangup occured");
						$('#eavesdrop_session').prop('checked',false)
					}
				}
			}
		})
		socket.on("OUTBOUND_CHANNEL_ANSWER", function(data){
			if (extension == data['sip_extension']){

				close_agent_sidebar()
				// agent_info_vue.state = 'InCall'
				set_agentstate('InCall')
				dispo_vue.on_call_dispo = true
				$("#ring_timer").countimer('stop')
				$("#speak_timer").countimer('start')
				$("#btnParkCall, #btnTransferCall").prop('disabled', false);
				$('#relation_tag_link,#feedback_tab_link').removeClass('disabled')
				$('#SecondsDISP').countimer('start');
				$("#call_duration_timer").removeClass('d-none')
				connect_time = new Date($.now());
				dial_number = $("#MDPhonENumbeR").val();
				// sessionStorage.setItem('previous_number', $("#phone_number").text().trim())
				if(sms_templates.send_sms_callrecieve){ 
					sms_templates.sendSMS(campaign_id,sms_templates.selected_template,dial_number)
				}
				if(email_templates.email_type == '0'){
					email_templates.sendEmail();
				}
				 var call_info = {
					"dial_number": dial_number,
					'campaign_name': campaign_name,
					'call_timestamp':data['call_timestamp'],
					'sip_extension':data['sip_extension']
				}
				$.ajax({
					method:"get",
					headers:{"X-CSRFToken":csrf_token},
					url: '/api/customer_info/',
					data:call_info,
					success:function(data){
						thirdparty_module(data)
					}
				})
			}
			
		})
		socket.on("OUTBOUND_CHANNEL_HANGUP", function(data){
			if (extension == data["sip_extension"] && agent_hangup == false && customer_hangup==false){
				close_agent_sidebar()
				// $("#submit_customer_info").attr("disabled", false);
				$('#relation_tag_link,#feedback_tab_link').removeClass('disabled')
				// sessionStorage.setItem('previous_number',$("#phone_number").text().trim())
				// agent_info_vue.state = 'Feedback'
				set_agentstate('Feedback')
				$("#btnPrevCall").removeClass("d-none")
				hangup_time = new Date($.now());
				$('#speak_timer, #ring_timer, #display_hold_timer, #hold_timer, #dialer_timer').countimer('stop');
				$('#btnParkCall').removeClass('active')
				customer_hangup = true
				timer_on_hangup()
				var agent_activity_data = create_agent_activity_data()
				agent_activity_data["campaign_name"] = $("#select_camp option:selected").text()
				agent_activity_data["event"] = "CUSTOMER HANGUP"
				if(add_three_way_conference_vue.three_way_list.length > 0){
					add_three_way_conference_vue.confHangupAll()
				}
				outbound_agent_beep_file= document.getElementById("autodial_agent_beep");
                outbound_agent_beep_file.play()
				$.ajax({
					type:'post',
					headers: {"X-CSRFToken":csrf_token},
					url: '/CRM/save-agent-breaks/',
					data: agent_activity_data,
					success: function(data){
						// flush_agent_timer()
						if (sessionStorage.getItem("outbound") == "Predictive") {
							$('#btnResumePause').attr('disabled', true)
						}
						if (ibc_status == true){
							$('#ibc_btnResumePause').attr('disabled', true)
						}
						if (blndd_status == true){
							$('#blndd_btnResumePause').attr('disabled', true)
						}
						$("#dialer_timer, #speak_timer, #ring_timer").text("0:0:0")
						$("#dialer_timer").countimer('start');
						$("#fb_timer_div strong").text("WrapUp Time :")
						$("#feedback_timer").countimer('start');
						if($('#iframe_tab_link').hasClass('active')){
							$('#iframe_tab_link, #iframe-tab').removeClass('active show')
						}
						add_three_way_conference_vue.three_way_list = []
					}
				})
				if(($("#model-popup-div").data('bs.modal') || {})._isShown == true){
					$("#transfer-btn").prop('disabled',true)
					$('#attr-hangup-btn').addClass('call_hanguped')
				}
			}
		})
		socket.on("AUTODIAL_CHANNEL_BRIDGE", function(autodial_data){
			var sip_extension = autodial_data["sip_extension"]
			if (sip_extension == extension) {
				agent_hangup = false
				close_agent_sidebar()
				$("#wait_timer").countimer('stop')
				$("#dialer_timer").countimer('stop')
				$("#speak_timer").countimer('start')
				dispo_vue.on_call_dispo = true
				var agent_activity_data = create_agent_activity_data()
				init_time = ring_time = connect_time = new Date($.now());
				if (blndd_status == true){
					callmode='predictive-blended'
					blended_hangup =true
					agent_activity_data['blended_wait_time'] = sessionStorage.getItem('wait_time')	
				}else{
					agent_activity_data['predictive_wait_time'] = sessionStorage.getItem('wait_time')
					callmode = 'predictive';
					autodial_hangup =true
				}
				var customer_number = autodial_data["customer_number"]
				var fs_call_timestamp = autodial_data["call_timestamp"]
				var campaign = $("#select_camp :selected").text()
				var contact_id = autodial_data["contact_id"]
				autodial_agent_beep_file= document.getElementById("autodial_agent_beep");
				autodial_agent_beep_file.play()
				$("#livecall h3").removeClass().addClass("text-success").text("LIVE CALL").attr("title", "LIVE CALL");
				// agent_info_vue.state = 'InCall'
				set_agentstate('InCall')
				call_info_vue.dailed_numeric = customer_number
				sessionStorage.setItem('previous_number', customer_number)
				sessionStorage.setItem('contact_id', contact_id)
				$("#btnPrevCall").addClass("d-none")
				$("#dialer_timer").text('0:0:0')
				$("#dialer_timer").countimer('start')
				$('#SecondsDISP').countimer('start');
				$("#call_duration_timer").removeClass('d-none')
				if (blndd_status == true){
					$("#blndd_btnResumePause").addClass("d-none")
				}else{
					$("#btnResumePause").addClass("d-none")
				}
				$('#btnDialHangup').removeClass("d-none")
				HangupCss()
				$("#btnParkCall").removeClass("d-none")
				$("#btnParkCall").prop("disabled", false)
				if (sessionStorage.getItem('can_transfer') == "true"){
					$("#btnTransferCall").removeClass("d-none")
					$("#btnTransferCall").prop("disabled", false)
				}
				$('#relation_tag_link,#feedback_tab_link').removeClass('disabled')

				agent_activity_data['campaign_name'] = campaign
				agent_activity_data['user_name'] = user_name
				agent_activity_data['dial_number'] = customer_number
				agent_activity_data['call_timestamp'] = fs_call_timestamp
				agent_activity_data['contact_id'] = contact_id
				agent_activity_data['dialed_uuid'] = autodial_data['dialed_uuid']
				agent_activity_data['event'] = "Agent-Answered"
				if (customer_number !="") {
					$.ajax({
						type:'post',
						headers: {"X-CSRFToken": csrf_token},
						url: '/api/autodial-customer-detail/',
						data: agent_activity_data,
						success: function(data){
							if(sessionStorage.getItem('previous_number')===customer_number){
								session_details[extension]['dialed_uuid'] = autodial_data['dialed_uuid']
								if ("contact_info" in data && data["contact_info"].length !=0) {
									$('#cust_basic_info a').editable('setValue', '');
									$("#editable-form").trigger("reset")
									if ("contact_info" in data) {
										showcustinfo(data)
										call_info_vue.callflow = 'Outbound'
										$("#contact-info").trigger("click")
									}
								}
								if(sms_templates.send_sms_callrecieve){ 
									setTimeout(sms_templates.sendSMS(campaign_id,sms_templates.selected_template,customer_number), 5000)
								}
								if(email_templates.email_type == '0'){
									setTimeout(email_templates.sendEmail(), 5000)
								}
								thirdparty_module(data)
							}
						}
					})

				}
			}
		})

		socket.on("AUTODIAL_CHANNEL_HANGUP", function(data){
			if (extension == data["sip_extension"] && agent_hangup == false){
				close_agent_sidebar()
				hangup_time = new Date($.now());
				var previous_number = sessionStorage.getItem('previous_number','')
		        if (previous_number) {
		            sessionStorage.setItem('previous_contact_id', $(this).attr("contact_id"))
		            $("#btnPrevCall").removeClass("d-none")
		        }
				$('#speak_timer, #ring_timer, #display_hold_timer, #hold_timer, #dialer_timer').countimer('stop');
				$('#btnParkCall').removeClass('active')
				if (blndd_status == true){
					sessionStorage.setItem("blended_time_val", sessionStorage.getItem("blended_time"))
				}else{
					sessionStorage.setItem("predictive_time_val", sessionStorage.getItem("predictive_time"))
				}
				timer_on_hangup()
				var agent_activity_data = create_agent_activity_data()
				agent_activity_data["campaign_name"] = $("#select_camp option:selected").text()
				agent_activity_data["event"] = "CUSTOMER HANGUP"
				autodial_agent_beep_file= document.getElementById("autodial_agent_beep");
				autodial_agent_beep_file.play()
				$.ajax({
					type:'post',
					headers: {"X-CSRFToken":csrf_token},
					url: '/CRM/save-agent-breaks/',
					data: agent_activity_data,
					success: function(data){
						$("#dialer_timer, #speak_timer, #ring_timer").text("0:0:0")
		                $('#dialer_timer').countimer('start');
		                $("#call-loader").fadeOut("fast")
		                $("#feedback_timer").countimer('start');
		                if($('#iframe_tab_link').hasClass('active')){
		                    $('#iframe_tab_li').addClass('d-none')
		                    $('#iframe_tab_link, #iframe-tab').removeClass('active show')
		                    $('#iframe-tab').find('iframe').prop("src", "")
		                }
						$("#toggleMute").addClass("d-none")
					}
				})
				if (blndd_status == true){
					$('#blndd_btnResumePause').attr('disabled', true)
				}else{
					$('#btnResumePause').attr('disabled', true)
				}				
				// agent_info_vue.state = 'Feedback'
				set_agentstate('Feedback')
			}
		})
		
		socket.on("sip_session_details",function(data){
			if (extension == data["Caller-Caller-ID-Number"]) {
				if (user_role == "Agent" || non_agent_user){
					temp_dict = {}
					temp_dict['Unique-ID'] = data['Unique-ID'];
					temp_dict['Caller-Caller-ID-Number'] = data['Caller-Caller-ID-Number'];
					temp_dict['variable_sip_from_host'] = data['variable_sip_from_host'];
					temp_dict['campaign_name'] = campaign_name
					if ($.inArray(agent_info_vue.state,['InCall','Feedback']) != -1 && Object.keys(dummy_session_details) == 0){
						dummy_session_details = {...session_details[extension]}
					}
					session_details[extension] = {...temp_dict}
					if (call_type == 'webrtc'){
						if ($.inArray(agent_info_vue.state,['Inbound Wait', 'Blended Wait', 'Predictive Wait']) != -1) {
							temp_dict['update_autodial_session'] = true
						}
						$.ajax({
							type:'post',
							headers: {"X-CSRFToken": csrf_token},
							url: '/api/webrtc_session_setvar/',
							data: temp_dict,
							success: function(data){
								}
						})
					}
				}else{
					temp_dict = {}
					temp_dict['Unique-ID'] = data['Unique-ID'];
					temp_dict['Caller-Caller-ID-Number'] = data['Caller-Caller-ID-Number'];
					temp_dict['variable_sip_from_host'] = data['variable_sip_from_host'];
					// temp_dict['campaign_name'] = campaign_name
					session_details[extension] = temp_dict
									
				}
			}
		});
		//incomming call socket functionality...
		socket.on("inbound_agents",function(data){
			if(jQuery.inArray(extension, data['extension']) !== -1){
				if(!(data['dialed_uuid'] in ic_vue.incomingCall_data) && !(data['dialed_uuid'] in ic_vue.rejectCall_data)){
					autodial_agent_beep_file= document.getElementById("autodial_agent_beep");
					autodial_agent_beep_file.play()
					Vue.set(ic_vue.incomingCall_data, data['dialed_uuid'], data)
					ic_vue.incomingCall = true
				}
			}
		});

		socket.on("inbound_StickyAgent",function(data){
			console.log(data)
			if(jQuery.inArray(extension, data['extension']) !== -1){
					autodial_agent_beep_file= document.getElementById("autodial_agent_beep");
	                autodial_agent_beep_file.play()
				    data = {"dialed_uuid":data["dialed_uuid"],"Unique-ID":session_details[extension]['Unique-ID'],"variable_sip_from_host":session_details[extension]["variable_sip_from_host"]}
						$.ajax({
							type:'post',
							headers: {"X-CSRFToken": csrf_token},
							url: '/api/incoming-sticky-bridge/',
							data: data,
							success: function(data){
								}
						})
				}
		});

		socket.on("INBOUND_CHANNEL_BRIDGE", function(inbound_data){
			var sip_extension = inbound_data["sip_extension"]
			if (sip_extension == extension) {
				dispo_vue.on_call_dispo = true
				close_agent_sidebar()
				agent_hangup = false
				callflow = "inbound"
				$("#wait_timer, #dialer_timer").countimer('stop')
				$("#dialer_timer").text('0:0:0')
				$("#speak_timer, #dialer_timer, #SecondsDISP").countimer('start')
				$("#call_duration_timer").removeClass('d-none')
				if (blndd_status == true){
					$("#blndd_btnResumePause").addClass("d-none")
				}else{
					$("#ibc_btnResumePause").addClass("d-none")
				}							
				$('#btnDialHangup').removeClass("d-none")
				HangupCss()
				$("#btnParkCall").removeClass("d-none")
				$("#btnParkCall").prop("disabled", false)
				if (sessionStorage.getItem('can_transfer') == "true"){
					$("#btnTransferCall").removeClass("d-none")
					$("#btnTransferCall").prop("disabled", false)
				}
				session_details[extension]['dialed_uuid'] = inbound_data['dialed_uuid']
				var agent_activity_data = create_agent_activity_data()
				init_time = new Date($.now());
				ring_time = new Date($.now());
				connect_time = new Date($.now());
				if (blndd_status == true){
					callmode='inbound-blended'
					blended_hangup =true
					agent_activity_data['blended_wait_time'] = sessionStorage.getItem('wait_time')	
				}else{
					agent_activity_data['inbound_wait_time'] = sessionStorage.getItem('wait_time')
					callmode = 'inbound';
					inbound_hangup =true
				}				
				var customer_number = inbound_data["customer_number"]
				var fs_call_timestamp = inbound_data["call_timestamp"]
				var campaign = $("#select_camp :selected").text()
				var contact_id = inbound_data["contact_id"]
				inbound_agent_beep_file= document.getElementById("autodial_agent_beep");
				inbound_agent_beep_file.play()
				$("#livecall h3").removeClass().addClass("text-success").text("LIVE CALL").attr("title", "LIVE CALL");
				call_info_vue.dailed_numeric = customer_number
				// agent_info_vue.state = 'InCall'
				set_agentstate('InCall')
				sessionStorage.setItem('previous_number', customer_number)
				sessionStorage.setItem('contact_id', contact_id)
				$("#btnPrevCall").addClass("d-none")
				$("#dialer_timer").text('0:0:0')
				$("#dialer_timer").countimer('start')
				$('#SecondsDISP').countimer('start');
				$("#call_duration_timer").removeClass('d-none')
				if (blndd_status == true){
					$("#blndd_btnResumePause").addClass("d-none")
				}else{
					$("#ibc_btnResumePause").addClass("d-none")
				}							
				$('#btnDialHangup').removeClass("d-none")
				HangupCss()
				$("#btnParkCall").removeClass("d-none")
				$("#btnParkCall").prop("disabled", false)
				if (sessionStorage.getItem('can_transfer') == "true"){
					$("#btnTransferCall").removeClass("d-none")
					$("#btnTransferCall").prop("disabled", false)
				}
				session_details[extension]['dialed_uuid'] = inbound_data['dialed_uuid']

				agent_activity_data['campaign_name'] = campaign
				agent_activity_data['user_name'] = user_name
				agent_activity_data['dial_number'] = customer_number
				agent_activity_data['call_timestamp'] = fs_call_timestamp
				agent_activity_data['contact_id'] = contact_id
				agent_activity_data['dialed_uuid'] = inbound_data['dialed_uuid']
				agent_activity_data['event'] = "Agent-Answered"
				if (customer_number !="") {
					$.ajax({
						type:'post',
						headers: {"X-CSRFToken": csrf_token},
						url: '/api/inbound-customer-detail/',
						data: agent_activity_data,
						success: function(data){
							if(sessionStorage.getItem('previous_number')===customer_number){
								if(data['contact_count'] > 1){
									if('contact_info' in data){
										$('#contact-info, #contact-info-tab').removeClass('active show')
										$('#list_li').removeClass('d-none')
										$('#list-info, #list-info-tab').addClass('active show')
										$("#list-info").click()
										list_of_contacts_table.clear().draw()
				                        list_of_contacts_table.rows.add(data['contact_info']);
				                        list_of_contacts_table.draw();
									}else if('error' in data){
										showWarningToast('Contact Info is Not avaliabe', 'top-right')
									}
								}else{
									var contact_id = ""
									if(data['contact_info'].length > 0){
										contact_id = data['contact_info'][0]['id']
									}
									set_inbound_customer_detail(customer_number,contact_id)
								}
								thirdparty_module(data)
							}
						}
					})

				}
			}
		})

		socket.on("INBOUND_CHANNEL_HANGUP", function(data){
				if (extension == data["sip_extension"] && agent_hangup == false && agent_info_vue.state == 'InCall'){
					close_agent_sidebar()
					var previous_number = sessionStorage.getItem('previous_number','')
			        if (previous_number) {
			            sessionStorage.setItem('previous_contact_id', $(this).attr("contact_id"))
			            $("#btnPrevCall").removeClass("d-none")
			        }
			        $('#hold_timer, #display_hold_timer').countimer('stop');
                	$('#btnParkCall').removeClass('active')
					if (inboundCall_picked){
						hangup_time = new Date($.now());
						$('#speak_timer, #ring_timer, #dialer_timer').countimer('stop');
						$("#feedback_timer").countimer('start');
						// agent_info_vue.state = 'Feedback'
						set_agentstate('Feedback')
						timer_on_hangup()
					}else{
						if(data["ibc_popup"]=='False' && data["queue_call"]=='True'){
							hangup_time = new Date($.now());
							$('#speak_timer, #ring_timer, #dialer_timer').countimer('stop');
							if ($("#fb_timer_div").hasClass("d-none")) {
			                    $("#fb_timer_div").removeClass("d-none")
			                    $("#fb_timer_div strong").text("WrapUp Time :")
			                }
							if (blndd_status == true){
								sessionStorage.setItem("blended_time_val", sessionStorage.getItem("blended_time"))
							}else{
								sessionStorage.setItem("inbound_time_val", sessionStorage.getItem("inbound_time"))
							}							
							timer_on_hangup()
							var agent_activity_data = create_agent_activity_data()
							agent_activity_data["campaign_name"] = $("#select_camp option:selected").text()
							agent_activity_data["event"] = "HANGUP"
							autodial_agent_beep_file= document.getElementById("autodial_agent_beep");
							autodial_agent_beep_file.play()
							$.ajax({
								type:'post',
								headers: {"X-CSRFToken":csrf_token},
								url: '/CRM/save-agent-breaks/',
								data: agent_activity_data,
								success: function(data){
									$("#dialer_timer, #speak_timer, #ring_timer").text("0:0:0")
					                $('#dialer_timer').countimer('start');
					                $("#call-loader").fadeOut("fast")
					                $("#feedback_timer").countimer('start');
					                if($('#iframe_tab_link').hasClass('active')){
					                    $('#iframe_tab_li').addClass('d-none')
					                    $('#iframe_tab_link, #iframe-tab').removeClass('active show')
					                    $('#iframe-tab').find('iframe').prop("src", "")
					                }
									$("#toggleMute").addClass("d-none")
								}
							})
							if (blndd_status == true){
								$('#blndd_btnResumePause').attr('disabled', true)
							}else{
								$('#ibc_btnResumePause').attr('disabled', true)
							}											
							// agent_info_vue.state = 'Feedback'
							set_agentstate('Feedback')
						}						
					}
				}
			})

		socket.on("inbound_notanswer_agents", function(data){
			if (data['extension'].length > 0 ){
				if(jQuery.inArray(extension, data['extension']) !== -1){
					Vue.delete(ic_vue.incomingCall_data, data['dialed_uuid'])
					Vue.delete(ic_vue.rejectCall_data, data['dialed_uuid'])
					if(Object.keys(ic_vue.incomingCall_data).length == 0){
						ic_vue.incomingCall = false;
					}
				}
			}
		})
		//incomming call socket functionality ends here...

		//transfer call socket functionality...
		socket.on("transfer_agents",function(data){
			if(data['transfer_to_agent_number'] == extension){
				Vue.set(ic_vue_transfer.transfercall_data, data['transfer_from_agent_uuid'], data)
				ic_vue_transfer.transfercall = true
				transfer_popup=setTimeout(function(){
					if (transferCall_picked != true){
						socket.emit("transfer_to_agent_rejected",data)
						Vue.delete(ic_vue_transfer.transfercall_data, data['transfer_from_agent_uuid'])
						if(Object.keys(ic_vue_transfer.transfercall_data).length == 0){
							ic_vue_transfer.transfercall = false
						}
					}
				},25000)
			}
		});

		socket.on("tr_internal_agent_answer_res",function(data){
			if(data['transfer_from_agent_number'] == extension){
				$("#call-loader").fadeOut("fast")
				session_details[extension]['transfer_uuid']=data['transfer_from_agent_uuid']
				transfer_ringback_file.pause();
				transfer_notanswer_file.pause();
				clearInterval(transfer_audio_func)
				$('#transfer-btn').removeClass('d-none')
				$('#transfer-btn').text("Transfer")
				$('#transfer-btn').prop('disabled',false)
			}
		});

		socket.on("transfer_to_agent_rejected_res",function(data){
			if(data['transfer_from_agent_number'] == extension){
				if(data['status']=='notanswered'){
					transfer_ringback_file.pause();
					transfer_busy_file= document.getElementById("Transfer-Busy");
					transfer_busy_file.play();
					clearInterval(transfer_audio_func)
				}
				session_details[extension]['transfer_uuid']=''
				$('#queue-radio,#external-radio,#agents-type-select,#internal-dial-btn,#close-popup,#transfer-type-select').prop("disabled", false);
				$('#hang-transfer-btn-div,#transfer-btn').addClass('d-none')
				$('#agents-type-select').prop('selectedIndex', 0)
			}
		});

		socket.on("tr_from_agent_hangup_res",function(data){
			if(data['transfer_to_agent_number'] == extension){
				// clearInterval(transfer_audio_func)
				if (transferCall_picked == false){
					Vue.delete(ic_vue_transfer.transfercall_data, data['transfer_from_agent_uuid'])
					if(Object.keys(ic_vue_transfer.transfercall_data).length == 0){
						ic_vue_transfer.transfercall = false
					}
				}else{
					if($('#btnDialHangup').attr("title") == "Transferhangup"){
						$('#btnDialHangup').trigger('click')
					}
				}
			}
		});

		socket.on("dial_number_transfer_to_agent_res",function(data){
			if(data['transfer_to_agent_number'] == extension){
				$('#btnDialHangup').attr("title","Hangup Call")
				HangupCss()
				transferCall_picked = false
				$("#btnTransferCall, #btnParkCall").removeClass("d-none")
				$("#btnTransferCall, #btnParkCall").prop("disabled",false)
				$('#relation_tag_link,#feedback_tab_link').removeClass('disabled')
				callmode = 'transfer';
				var customer_number = data["transfer_number"]
				var campaign = $("#select_camp :selected").text()
				var transfer_agent = data['transfer_from_agent_number']
				session_details[extension]['dialed_uuid'] = data['dialed_uuid']
				session_details[extension]['dial_number']= data["transfer_number"]
				sessionStorage.setItem("contact_id", data["contact_id"])
				sessionStorage.setItem("previous_number", data["previous_number"])
				if (customer_number !="") {
					$.ajax({
						type:'post',
						headers: {"X-CSRFToken": csrf_token},
						url: '/api/transfer-customer-detail/',
						data: {"campaign_name": campaign, "extension": extension,'dialed_uuid':data['dialed_uuid'],
						 "dial_number":customer_number,"transfer_agent":transfer_agent, "contact_id":data["contact_id"]},
						success: function(ajx_data){
							if(sessionStorage.getItem("contact_id")==data["contact_id"]){
								if ("contact_info" in ajx_data && ajx_data["contact_info"].length !=0) {
									$('#cust_basic_info a').editable('setValue', '');
									$("#editable-form").trigger("reset")
									if ("contact_info" in ajx_data) {
										showcustinfo(ajx_data["contact_info"])
										call_info_vue.callflow = 'Internal'
									}
								}else{
									var transfer_data = [{'numeric':data["transfer_number"]}]
									showcustinfo(transfer_data)
									call_info_vue.callflow = 'Internal'
								}
							}
						}
					});
				}
			}
		});	

		socket.on("OUTBOUND_TRANSFER_CHANNEL_ANSWER",function(data){
			if(data == extension){
				$("#transfer-btn").prop('disabled',false)
				$("#transfer-btn").removeClass('d-none')
				if ($('#transfer-type-select').val() == "three-way-calling") {
					$('#transfer-btn').text("Merge")
				}
				else {
					$('#transfer-btn').text("Transfer")	
				}

			}
		})
		
		socket.on("OUTBOUND_TRANSFER_CHANNEL_HANGUP",function(data){
			if(data == extension){
				$('#transfer-type-select').prop("disabled", false);
				$('#queue-radio,#internal-radio,#dial-number-text,#external-dial-btn,#close-popup').prop("disabled", false);
				$('#external-dial-btn').removeClass('d-none')
				$('#hang-transfer-btn-div').addClass('d-none')
				$('#hang-merge-btn-div').addClass('d-none')
				$('#dial-number-text').val("")
				$("#transfer-btn").addClass('d-none')
				if ($('#attr-hangup-btn').hasClass('call_hanguped')){
					$('#attr-hangup-btn').removeClass('call_hanguped')
					$("#model-popup-div").modal('hide')
				}
			}
		})	
		//transfer call socket functionality ends here...
		// conference call hangup functionality
		socket.on("OUTBOUND_CONFERENCE_CHANNEL_HANGUP",function(data){
			if(data['sip_extension'] == extension){
				var tw_list_index = 0
				var merged_call = true
				add_three_way_conference_vue.three_way_list.filter(function(conf_dict,index){
					if(conf_dict['conf_uuid'] == data['conference_num_uuid']){
						tw_list_index = index
						merged_call = false
					}
				})
				if (merged_call){
					$('#queue-radio,#internal-radio,#dial-number-text,#external-dial-btn,#close-popup,#transfer-type-select').prop("disabled", false);
					$('#external-dial-btn').removeClass('d-none')
					$('#hang-transfer-btn-div,#hang-merge-btn-div,#transfer-btn').addClass('d-none')
					$('#dial-number-text').val("")
					session_details[extension]['conference_num_uuid'] = ""
					if ($('#attr-hangup-btn').hasClass('call_hanguped')){
						$('#attr-hangup-btn').removeClass('call_hanguped')
						$("#model-popup-div").modal('hide')
					}
				}else{
					add_three_way_conference_vue.removeHangupedDict(tw_list_index)
					disable_conference = false
					$("#btnTransferCall").attr("disabled",false)
				}
			}
		})	
		//Emergency logout user by admin
		socket.on("do_emergency_logout",function(data){
			if(data["extension"] == extension){ 
				common_function_before_page_unload(`Force Logout By ${data["user_role"]} ${data["username"]}`, data["username"])
			}
		})	
		force_logout_all = false	
		socket.on("do_emergency_logout_all_users",function(data){
			if(data["user_list"].includes(extension)){ 
				force_logout_all = true
				common_function_before_page_unload(`Force Logout By ${data["user_role"]} ${data["username"]}`, data["username"])
			}
		})	
		socket.on("do_broadcast_message",function(data){
			if(data["users"].includes(extension)){ 
				if(data['type'] == '0'){
					showInfoToast(data['message'],'top-center',data['broadcast_time'])
				}else if(data['type'] == '1'){
					showWarningToast(data['message'],'top-center',data['broadcast_time'])
				}else{
					showDangerToast('Danger',data['message'],'top-center',data['broadcast_time'])
				}
				getBroadCastMessages()
			}
		})	

		socket.on("emergency_all_logout_status_admin",function(data){
			if(data["username"] == user_name){ 
				showSwal('success-message', 'Force logout for all user is successful')
			}
		})	
	}
	socket.on('message',function(message){
		var message = JSON.parse(message);
		console.log(message)
		if(campaign_name != "" && campaign_name == message['campaign'] && agent_info_vue.is_portfolio == false){
			if(agent_info_vue.state == 'Idle' && dial_flag == true){
				showInfoToast("Lead Inserted You can Dial Now",'top-center',false)
			}
		}
	})
	let hangupHandlerAttached = true;
	if (hangupHandlerAttached) {
		hangupHandlerAttached = false;

		socket.on('hangup_client_on_fs_hangup', function (message) {
			console.log('inside hangupHandlerAttached ')
			var data = JSON.parse(message);
			if (extension == data.extension){
				setTimeout(	()=>{
					if (('dialed_uuid' in session_details[extension] && data.dialed_uuid ==  session_details[extension]['dialed_uuid']) && ($('#btnDialHangup').attr("title") == 'Hangup Call')){
						$('#btnDialHangup').click()			
					}
				},1000)
			}
		});
	}
};




