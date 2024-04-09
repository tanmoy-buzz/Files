// agent page js
function agent_datatable(table){
    var id = '#'+ table.attr('id');
    $(table).DataTable( {
        "aaSorting": [],
        // "bPaginate": false,
        // "bInfo": false,
        // "searching": false,
        responsive: {
            details: {
                display: $.fn.dataTable.Responsive.display.modal( {
                    header: function ( row ) {
                        var data = row.data();
                        return 'Details for '+data[1];
                    }
                } ),
                renderer: $.fn.dataTable.Responsive.renderer.tableAll( {
                    tableClass: 'table'
                } )
            }
        },
        columnDefs: [ 
        {
            targets: [0, -2],
            orderable: false,
            width:"1%"
        },
        {
            targets: [ -1 ],
            orderable: false,
            width:"16%"
        },
        {
            responsivePriority: 1, targets: 0
        },
        {
            responsivePriority: 2, targets: 1
        },
        {
            responsivePriority: 3, targets: -2
        },
        {
            responsivePriority: 4, targets: -1
        }
        ],
        // order: [[ 0, 'asc' ]],
        // pageLength: 2
    } );}
function initial_dialler_state(){
    if ($("#feedback_tab_link").hasClass("disabled")) {
        $("#fb_timer").click()
        $("#fb_timer").remove()
        $("#dummy-fb-time").append('<span id="fb_timer" class="pl-1"></span>')
        $('#campain_name_div,#camp_name_div,#show-campaign-assigned-calls').addClass('d-none')
        $('#campain_name_display,#campain_name_disp').text("")
        $('#feedback-tab').removeClass('active show')
        $('#feedback-tab').addClass('hide')
        $('#cust_basic_info').addClass('d-none')
        $('#cust_basic_info a').editable('setValue', '');
        $("#crm-agent-logout").attr("onclick", "confirmLogout()")
        $("#script_name").text("")
        $("#script_description").html("")
        $("#agent-breaks-div").addClass("d-none")
        $("#MDPhonENumbeR, #manual-dial-now, #dialpad-toggle, #btnLogMeOut, #btnNextCall, #flexy-agent-dialpad button,#btnResumePause,#ibc_btnResumePause,#blndd_btnResumePause").attr("disabled", false)
        $("#MDPhonENumbeR").val("")
        $("#profile-tab, #btnNextCall, #agent-callbacks-div button, #profile-tab,#show-callbacks-active,#show-callbacks-campaign,#show-abandonedcalls-campaign, #show-campaign-lead-bucket, #show-campaign-assigned-calls, #show-camp-requeue-lead-bucket, #show-camp-assigned-dialed-calls, #show-camp-assigned-notdialed-calls,#show-Reconfirmappointment-calls").removeClass("disabled")
        $("#dispo-collaps button").removeClass("active")
        $("#submit_customer_info").attr("disabled", true)
        $("#feedback_tab_link, #relation_tag_link").addClass("disabled")
        $("#contact-info").click()
        $("#btnResumePause").attr({
            "class": "btn btn-success btn-lg d-none",
            "title": "Start Predictive Dialing"
        })
        $("#ibc_btnResumePause").attr({
            "class": "btn btn-success btn-lg d-none",
            "title": "Start Inbound"
        })
        $("#blndd_btnResumePause").attr({
            "class": "btn btn-success btn-lg d-none",
            "title": "Start Blended Mode"
        })        
        $("#btnResumePause,#ibc_btnResumePause,#blndd_btnResumePause").find('i').attr("class", "fa fa-play")
        $("#agent-break-status").addClass("d-none")
        $('#iframe_tab_li').addClass('d-none')
        $('#iframe_tab_link, #iframe-tab').removeClass('active show')
        $('#iframe-tab').find('iframe').prop("src", "")
        $('#app_timer, #idle_timer').countimer('start');
        $('#app_timer, #idle_timer').text("0:0:0")
        $('.breadcrumb li').find('#crm-home').trigger('click')
        $('#setting-content-dialer-tab ul').addClass('d-none');
        $('#flexy_agent_login').removeClass('d-none');
        $('#LeadPreview').parent().removeClass('pt-none')
        $('#LeadPreview').prop('checked',true)
        sip_login = socket_connection_fail = sip_error = redial_status = auto_feedback = autodial_status = blended_hangup = false
        ibc_status = blndd_status = app_logout = page_reload = disable_conference = inbound_hangup = autodial_hangup = false
        isTransferableCall = true
        update_sql_database = false
        campaign_id = campaign_name = "";
        agent_info_vue.camp_name = ""
        agent_info_vue.selected_status = 'NotReady'
        session_details[extension] = {};
        crm_field_vue.field_schema = []
        crm_field_vue.field_data = {}
        crm_field_vue.resetBasicField()
        crm_field_vue.resetExtraField()
        call_info_vue.resetCallInfo()
        crm_field_vue.temp_data = {}
        agent_relationtag_vue.relationTag_list = []
        agent_relationtag_vue.resetRelationForm()
        sessionStorage.setItem("caller_id", "")
        sessionStorage.setItem('can_transfer',false)
        sessionStorage.setItem('can_conference', false)
        sessionStorage.setItem("inbound",false)
        sessionStorage.setItem("ibc_popup",false)
        sessionStorage.setItem("manual",false)
        calldetail_id = null
        dispo_vue.reset_dispoform()
        if (sessionStorage.getItem("outbound") == "Predictive" && sessionStorage.getItem("inbound") == true && sessionStorage.getItem("ibc_popup")== false ){
            if ($("#predictive_timer").countimer('stopped') == false) {
                $("#predictive_timer").countimer('stop');
                $("#predictive_timer").text('00:00:00');
                $('#predictive_timer_div').addClass('d-none')
                $('#predictive_timer_display').countimer('stop')
                $('#predictive_timer_display').text('00:00:00')
            }
            if ($("#inbound_timer").countimer('stopped') == false) {
                $("#inbound_timer").countimer('stop');
                $("#inbound_timer").text('00:00:00');
                $('#inbound_timer_div').addClass('d-none')
                $('#inbound_timer_display').countimer('stop')
                $('#inbound_timer_display').text('00:00:00')
            }
            $('#wait_timer').countimer('stop');
            $('#wait_timer').text('0:0:0')
            sessionStorage.setItem("wait_time", "0:0:0");
        }
        else if (sessionStorage.getItem("outbound") == "Predictive") {
            if ($("#predictive_timer").countimer('stopped') == false) {
                $("#predictive_timer").countimer('stop');
                $("#predictive_timer").text('00:00:00');
                $('#predictive_timer_div').addClass('d-none')
                $('#predictive_timer_display').countimer('stop')
                $('#predictive_timer_display').text('00:00:00')
                $('#wait_timer').countimer('stop');
                $('#wait_timer').text('0:0:0')
                sessionStorage.setItem("wait_time", "0:0:0");
            }
        }
        else if (sessionStorage.getItem("inbound") == true) {
            if ($("#inbound_timer").countimer('stopped') == false) {
                $("#inbound_timer").countimer('stop');
                $("#inbound_timer").text('00:00:00');
                $('#inbound_timer_div').addClass('d-none')
                $('#inbound_timer_display').countimer('stop')
                $('#inbound_timer_display').text('00:00:00')
                $('#wait_timer').countimer('stop');
                $('#wait_timer').text('0:0:0')
                sessionStorage.setItem("wait_time", "0:0:0");
            }
        }
    }
}
// draggable incoming and transfer call popup
dragElement(document.getElementById("incoming_call_vue"));
dragElement(document.getElementById("transfer_call_vue"));

// global variables
var init_time = ring_time = connect_time = hold_time = media_time = call_duration = bill_sec = 0
wait_time = "0:0:0"
var callmode = 'outbound'
var callflow = 'outbound'
var hangup_time = feedback_time = ''
var manual = socket_connection_fail = agent_hangup = customer_hangup = false
var noti_interval;
// var ac_interval;
var tc_interval;
// var campcallback_interval;
var tmc_interval;
var cmc_interval;
var total_fu_interval;
var reconfirm_interval;
var active_fu_interval;
var camp_fu_interval;
var hold_time_flag = true
app_logout = false
page_reload = false
is_abandoned_callback = false
var hangup_cause_code_er = ''
var hangup_cause_er = ''
var dialed_status_er = ''
var update_sql_database = false
var window_reload_stop = false
var calldetail_id = null
sessionStorage.setItem("progressive_time_val", "0:0:0");
sessionStorage.setItem("predictive_time_val", "0:0:0");
sessionStorage.setItem("preview_time_val", "0:0:0");
sessionStorage.setItem("predictive_wait_time", "0:0:0");
sessionStorage.setItem("inbound_time_val", "0:0:0");
sessionStorage.setItem("inbound_wait_time", "0:0:0");

// This function is used to reset all agent timer
function flush_agent_timer() {
    $("#ring_timer, #speak_timer, #feedback_timer, #app_timer, #dialer_timer, #preview_timer, #progressive_timer, #hold_timer, #mute_timer, #transfer_timer, #pause_progressive_timer").countimer('stop')
    $("#ring_timer, #speak_timer, #feedback_timer, #app_timer, #dialer_timer, #preview_timer, #progressive_timer, #hold_timer, #mute_timer, #transfer_timer,#pause_progressive_timer").text('0:0:0')
    sessionStorage.setItem("ring_time", "0:0:0");
    sessionStorage.setItem("speak_time", "0:0:0");
    sessionStorage.setItem("feedback_time", "0:0:0");
    sessionStorage.setItem("app_time", "0:0:0");
    sessionStorage.setItem("dialer_time", "0:0:0");
    sessionStorage.setItem("preview_time", "0:0:0");
    sessionStorage.setItem("progressive_time", "0:0:0");
    sessionStorage.setItem("hold_time", "0:0:0");
    sessionStorage.setItem("mute_time", "0:0:0");
    sessionStorage.setItem("transfer_time", "0:0:0");
    sessionStorage.setItem("idle_time","0:0:0");
    sessionStorage.setItem("pause_progressive_time", "0:0:0");
}
// check entered value is number only starts
function isNumber(evt) {
    evt = (evt) ? evt : window.event;
    var charCode = (evt.which) ? evt.which : evt.keyCode;
    if (charCode > 31 && (charCode < 48 || charCode > 57)) {
        return false;
    }
    return true;
}
// check entered value is number only ends

// time format 
function format_time(datetime) {
    if (datetime != '') {
        return moment(datetime).format("YYYY-MM-DD HH:mm:ss");
    } else {
        return ''
    }
}
// time differnce
function diff_seconds(dt2, dt1) {
    if (dt2 && dt1) {
        var diff = (dt2.getTime() - dt1.getTime()) / 1000
        return Math.abs(Math.round(diff))
    } else {
        return 0
    }
}
// time string to seconds
function timestring_to_seconds(time_string) {
    if (time_string != '') {
        var split_string = time_string.split(':')
        if (split_string.length < 3) {
            split_string.splice(0, 0, "00");
            // split_string.insert(0, "00")
        }
        return (+split_string[0]) * 60 * 60 + (+split_string[1]) * 60 + (+split_string[2]);
    } else {
        return 0
    }
}

//This function is used to format agent activity data into a dictionary
function create_agent_activity_data() {
    var agent_activity = {}
    agent_activity['wait_timer'] = sessionStorage.getItem("wait_time");
    agent_activity['idle_time'] = sessionStorage.getItem("idle_time");
    agent_activity['app_time'] = sessionStorage.getItem("app_time")
    agent_activity['dialer_time'] = sessionStorage.getItem("dialer_time")
    moment_wait_time = moment.duration(agent_activity['dialer_time'], "HH:mm:ss");
    moment_app_time = moment.duration(agent_activity['app_time'], "HH:mm:ss");
    var tos_time = moment_wait_time.add(moment_app_time);
    agent_activity['tos_time'] = tos_time.hours() + ":" + tos_time.minutes() + ":" + tos_time.seconds()
    agent_activity['ring_time'] = sessionStorage.getItem("ring_time")
    agent_activity['speak_time'] = sessionStorage.getItem("speak_time")
    agent_activity['feedback_timer'] = sessionStorage.getItem("feedback_time")
    agent_activity['preview_time'] = sessionStorage.getItem("preview_time")
    agent_activity['progressive_time'] = sessionStorage.getItem("progressive_time")
    agent_activity['agent_hold_time'] = sessionStorage.getItem("hold_time")
    agent_activity['agent_mute_time'] = sessionStorage.getItem("mute_time")
    agent_activity['pause_progressive_time'] = sessionStorage.getItem("pause_progressive_time")
    if (sessionStorage.getItem("transfer_time") != "") {
        agent_activity['agent_transfer_time'] = sessionStorage.getItem("transfer_time") 
    }
    return agent_activity
}
// socket connection
var socket = '';

function node_connection(host) {
    var nodejs_port = '3232';
    socket = io(host + ':' + nodejs_port, {
        'reconnection': true,
        'reconnectionDelay': 2000,
        'reconnectionDelayMax': 5000,
        'reconnectionAttempts': 10
    });
}
node_connection(server_ip);
socket.on('connect', function() {
    socket_id = socket.id
    $('.preloader').fadeOut('slow')
    if (swal.getState()['isOpen']){
        swal.close()
    }
})
socketevents();
socket.on('disconnect', () => {
  if ($.inArray(agent_info_vue.state,['InCall','Feedback']) == -1){
    $('.preloader').fadeIn('fast')
  }
});
socket.on('connect_error', () => {
  if ($.inArray(agent_info_vue.state,['InCall','Feedback']) == -1){
    $('.preloader').fadeIn('fast')
  }
});
socket.io.on('reconnect_failed', function() {
    if ($.inArray(agent_info_vue.state,['InCall','Feedback']) == -1){
        if (agent_info_vue.selected_status == 'Ready'){
            if(blndd_status && sessionStorage.getItem("ibc_popup") == "false") $("#blndd_btnResumePause").click()
            if(autodial_status) $("#btnResumePause").click()
            if(ibc_status) $("#ibc_btnResumePause").click()
            $('#btnLogMeOut').click()
        }
        socketErrorAlert()
    }
})
function webrtcfunction() {
    alert("webrtc")
}
// hidden sidebar scroll
new PerfectScrollbar('#setting-content');
var csrf_token = $("input[name='csrfmiddlewaretoken']").val()

// toggle sidebar 
$('#right-sidebar-button').click(function() {
    $('#right-sidebar').toggleClass('open')
    if ($('#right-sidebar').hasClass('open')) {
        $('#incoming_call_vue').animate({ 'right': '250px' }, 200)
        $('body').removeClass('agent-sidebar-hidden')
    } else {
        $('#incoming_call_vue').animate({ 'right': '20px' }, 200)
        $('body').addClass('agent-sidebar-hidden')
    }
})

// jquery for datatables
function selective_datatable(table) {
    var id = '#' + table.attr('id');
    $(table).DataTable({
        responsive: {
            details: {
                display: $.fn.dataTable.Responsive.display.modal({
                    header: function(row) {
                        var data = row.data();
                        return 'Details for ' + data[1] + ' ' + data[2];
                    }
                }),
                renderer: $.fn.dataTable.Responsive.renderer.tableAll({
                    tableClass: 'table'
                })
            }
        },
        order: [
            [1, 'asc']
        ],
    });
}

// this function to clear inetrval and hide div's
function hideHomeDiv() {
    $("#mb_landing_page").addClass('d-none');
    $("#cust-info").addClass('d-none');
    $("#loaded-contents").removeClass('d-none');
    $("#loaded-contents").children().addClass('d-none');
    $('.breadcrumb li').remove();
    clearInterval(tc_interval);
    // clearInterval(ac_interval);
    clearInterval(noti_interval);
    // clearInterval(campcallback_interval);
    clearInterval(tmc_interval);
    clearInterval(cmc_interval);
    clearInterval(active_fu_interval);
    clearInterval(camp_fu_interval);
    clearInterval(total_fu_interval);
    clearInterval(reconfirm_interval)
}
// show dif tabs on click of link
$('#flexy_agent_profile li:nth-child(3),#flexy_agent_profile li:nth-child(4), .mb-callback, .mb-abandoned').click(function(e) {
    if ($(this).find('a').length != 0) {
        e.preventDefault();
        hideHomeDiv()
        $('#nextPage_number').val('1')
        $('#page_length').val('10')
        var tab_link = $(this).find('a').attr('id');
        if (tab_link == 'callbacks') {
            filter_dict = {}
            getTotalCallback(filter_dict);
        } else if (tab_link == 'abandonedcalls') {
            getAbandonedCalls();
        } 
        $("#contents-" + tab_link).removeClass('d-none');
        $('.page-title').text(tab_link)
        $('.breadcrumb').append('<li class="breadcrumb-item" aria-current="page"><a href="#" id="crm-home">'
            +'<i class="fas fa-home"></i></a></li>')
    }
});

// agent profile button to profile tab
$("#profile-btn").click(function(e) {
    e.preventDefault();
    hideHomeDiv()
    $("#contents-profile").removeClass('d-none');
    $('.page-title').text("My Profile");
    $('.breadcrumb').append('<li class="breadcrumb-item" aria-current="page"><a href="#" id="crm-home">'+
        +'<i class="fas fa-home"></i></a></li>')
})

// return to home page of agent
$(document).on('click', '#crm-home', function(e) {
    e.preventDefault();
    clearInterval(tc_interval);
    // clearInterval(ac_interval);
    clearInterval(noti_interval);
    // clearInterval(campcallback_interval);
    clearInterval(cmc_interval);
    clearInterval(tmc_interval);
    clearInterval(active_fu_interval);
    clearInterval(camp_fu_interval);
    clearInterval(total_fu_interval);
    clearInterval(reconfirm_interval)
    $('#mb_landing_page').removeClass('d-none')
    $("#cust-info").removeClass('d-none');
    $("#loaded-contents").addClass('d-none');
    $("#loaded-contents").children().addClass('d-none');
    $('.page-title').text("Contact Information")
    $('.breadcrumb li').remove();
    $('.breadcrumb').append('<li class="breadcrumb-item active" aria-current="page"><i class="fas fa-home"></i></li>')
});

// enable disable campaign selection submit btn

var dialler_login_vue = new Vue({
    el: '#set-agent-campaign',           //element on whiche vue will intiaize
    delimiters: ['${', '}'],
    data:function(){
       return { active_campaign :[]}
    },
    methods:{
        getAgentCamapign() {
           $.ajax({
                type: 'post',
                headers: { "X-CSRFToken": csrf_token },
                url: '/api/get-agent-campaign/',
                data: {},
                success: function(data) {
                    dialler_login_vue.active_campaign = [... data["active_campaign"]]
                },
                error: function(data) {
                    
                },
                complete: function (data) {
                  
                }
            })
        },
    }
})
$("#select_camp").change(function() {
    if ($(this).prop('selectedIndex') != 0) {
        $('#scSubmit').prop('disabled', false);
    } else {
        $('#scSubmit').prop('disabled', true);
    }
});

$("#btnLogMeIn").click(function() {
    dialler_login_vue.getAgentCamapign()
})

function reset_agent_login_dialer() {
    $('#setting-content-dialer-tab ul:not(#flexy-agent-manualdial)').removeClass('d-none');
    $('#flexy_agent_login, #btnNextCall, #lead-preview-li, #flexy-agent-manualdial, #btnDialHangup').addClass('d-none');
    $('#AgentDialPad').css('display', 'none')
    $("#MDPhonENumbeR").text("")
}

//This function is used to store agent call mode in session
function session_campaign_detail(dial_method) {
    list_of_modes = []
    sessionStorage.setItem("outbound", false);
    sessionStorage.setItem("ibc_popup",dial_method["ibc_popup"])
    if (dial_method["outbound"] == "Progressive" || dial_method["outbound"] == "Preview") {
        $("#btnNextCall").removeClass("d-none")
        $("#btnDialHangup").addClass("d-none")
        $(".lead-preview-li").removeClass("d-none")
        if (dial_method["outbound"] == "Progressive") {
            sessionStorage.setItem("outbound", "Progressive");
            list_of_modes.push('Progressive')
        } else {
            sessionStorage.setItem("outbound", "Preview");
            list_of_modes.push('Preview')
        }
    }
    if (dial_method["outbound"] == "Predictive") {
        if (dial_method["inbound"] == true){
            if (dial_method['ibc_popup']==true){
                sessionStorage.setItem("outbound", "Predictive")
                $("#btnResumePause").removeClass("d-none")
                list_of_modes.push('Predictive')
            }else{
                sessionStorage.setItem("ibc_popup",false)
                sessionStorage.setItem("inbound", true)
                sessionStorage.setItem("outbound", "Predictive")
                $("#blndd_btnResumePause").removeClass("d-none")
                list_of_modes.push('Blended')
            }
        }else{
            sessionStorage.setItem("outbound", "Predictive")
            $("#btnResumePause").removeClass("d-none") 
              list_of_modes.push('Predictive')         
        }
    }
    if (dial_method["manual"] == true) {
        $("#flexy-agent-manualdial").removeClass("d-none")
        $("#flexy-agent-manualdial, #AgentDialPad").prop("disabled", false)
        sessionStorage.setItem("manual", true)
         list_of_modes.push('Manual')
    }
    if (dial_method["inbound"] == true){
        if(dial_method["outbound"] != "Predictive" && dial_method['ibc_popup']==false) {
            sessionStorage.setItem("inbound", true)
            list_of_modes.push('Inbound')
            if (dial_method['ibc_popup'] != true){
                $("#ibc_btnResumePause").removeClass("d-none")  
            }
        }else{
            sessionStorage.setItem("inbound", true)
            if(dial_method["inbound"] == false && dial_method["outbound"] != "Predictive"){
                list_of_modes.push('Inbound')    
            }
            if(dial_method['ibc_popup']==true){
                list_of_modes.push('Inbound')    
            }
        }
    }
    if (dial_method["outbound"] == false) {
        $("#btnDialHangup, #btnNextCall").addClass("d-none")
        $("#LeadPreview").prop("checked", false)
    }
    sessionStorage.setItem("third_party_data_fetch",dial_method["third_party_data_fetch"])
    sessionStorage.setItem("thirdparty_data_push",dial_method["thirdparty_data_push"])
    sessionStorage.setItem("kyc_document_flag",dial_method["kyc_document"])
    if('kyc_document' in dial_method && dial_method["kyc_document"]){
        $('#documents_tab').removeClass('d-none')
    }
    agent_info_vue_mode.mode_list = list_of_modes
}

function set_agent_dashboard_count(){
    if(sessionStorage.getItem("assigned_calls","0")>0){
        $('#show-campaign-assigned-calls').removeClass('d-none')
        $('#show-campaign-assigned-calls a small span').text(sessionStorage.getItem("assigned_calls","0"))
    }else{
        $('#show-campaign-assigned-calls').addClass('d-none');
    }
    if(sessionStorage.getItem("campaign_leads_count","0") > 0){
        $('#show-campaign-lead-bucket').removeClass('d-none')
        $('#show-campaign-lead-bucket a small span').text(sessionStorage.getItem("campaign_leads_count","0"))
    }else{
        $('#show-campaign-lead-bucket').addClass('d-none');
    }
    if(sessionStorage.getItem("campaign_requeue_leads_count","0") > 0){
        $('#show-camp-requeue-lead-bucket').removeClass('d-none')
        $('#show-camp-requeue-lead-bucket a small span').text(sessionStorage.getItem("campaign_requeue_leads_count","0"))
    }else{
        $('#show-camp-requeue-lead-bucket').addClass('d-none');
    }
    if(sessionStorage.getItem("dialled_assingned_calls","0") > 0){
        $('#show-camp-assigned-dialed-calls').removeClass('d-none')
        $('#show-camp-assigned-dialed-calls a small span').text(sessionStorage.getItem("dialled_assingned_calls","0"))
    }else{
        $('#show-camp-assigned-dialed-calls').addClass('d-none');
    }
    if(sessionStorage.getItem("notdialed_assigned_calls","0") > 0){
        $('#show-camp-assigned-notdialed-calls').removeClass('d-none')
        $('#show-camp-assigned-notdialed-calls a small span').text(sessionStorage.getItem("notdialed_assigned_calls","0"))
    }else{
        $('#show-camp-assigned-notdialed-calls').addClass('d-none');
    }
    if(sessionStorage.getItem("todays_call","") > 0){
        $('#show-agent-totalcall-today small span').text(sessionStorage.getItem("todays_call",""))
    }
    if(sessionStorage.getItem("monthly_call","") > 0){
        $('#show-agent-totalcall-month small span').text(sessionStorage.getItem("monthly_call",""))
    }
}

var socket_id = ""
var sip_login = false;
// login to diler after campaign selection
$('#scSubmit').click(function() {
     // $('.circle').show();
    clear_cache()
    $("#btnPrevCall").addClass("d-none")
    host = $("#select_camp option:selected").attr('data-server');
    var app_time = sessionStorage.getItem("app_time");
    var login_time = sessionStorage.getItem("login_time");
    $('#idle_timer').countimer('stop');
    var idle_time = sessionStorage.getItem("idle_time");
    initial_dialler_state()
    campaign_id = $("#select_camp").val();
    $('#app_timer').countimer('stop');
    $(".modal").modal('hide');
    $('.preloader').fadeIn('fast');
    $("#show-agent-kycdocument").removeClass("d-none")
    $.ajax({
        type: 'post',
        headers: { "X-CSRFToken": csrf_token },
        url: '/api/dailer_login/',
        data: { "campaign_id": campaign_id, "app_time": app_time, "idle_time": idle_time },
        success: function(data) {
            if(agent_info_vue.isMobile()){
                $('#mb_landing_page').addClass('d-none');
                $('#mb_dialer_screen, #btnLogMeOut, .mb-page-header').removeClass('d-none')
            }
            agent_info_vue_mode.show_modes = true
            sms_templates.is_manual_sms = data['disabled_sms_tab']
            sms_templates.send_sms_on_dispo = data['send_sms_on_dispo']
            sms_templates.send_sms_callrecieve = data['send_sms_callrecieve']
            $("#fb_timer").click()
            $("#fb_timer").remove()
            $("#dummy-fb-time").append('<span id="fb_timer" class="pl-1"></span>')
            $("#idle_timer, #app_timer").text('0:0:0')
            sessionStorage.setItem("wait_time", "0:0:0");
            $('#dialer_timer, #idle_timer').countimer('start');
            campaign_name = $("#select_camp option:selected").text()
            $('#campain_name_div,#camp_name_div').removeClass('d-none')
            $('#campain_name_display,#campain_name_disp').text(campaign_name)
            sip_login = true
            if (data['call_type'] == 'softcall' | data['call_type']== '2') {
                $('.preloader').fadeOut('slow');
                reset_agent_login_dialer()
            } else {
                sip_identity = `sip:${extension}@${host}`
                websocket_proxy_url = `wss://${host}:`+data['wss_port'];
                outbound_proxy_url = `udp://${host}:`+data['sip_udp_port'];
                sipInitialize();
                reset_agent_login_dialer()
            }
            var rpc_port = data['rpc_port']
            dispo_vue.dispo_schema = data['not_on_call_dispostion'];
            dispo_vue.on_call_dispositions = data['on_call_dispositions']
            dispo_vue.not_on_call_dispostion = data["not_on_call_dispostion"]
            dispo_vue.assigned_lead_user = data['lead_user']
            agent_relationtag_vue.relationTag_list = data["relation_tag"]
            agent_info_vue.camp_name = campaign_name
            agent_info_vue.is_portfolio = data["campaign"]["portifolio"]
            sms_templates.templates = data['sms_templates']
            if (data['email_gateway']){
                email_templates.gateway_id = data['email_gateway']['gateway_id']
                email_templates.templates = data['email_gateway']['email_templates']
                email_templates.email_type = data['email_gateway']['email_type']
                email_templates.email_dispositions = data['email_gateway']['email_dispositions']
            }
            crm_field_vue.field_schema = data['crm_fields'];
            crm_field_vue.field_data = {...data['crm_fieds_data']}
            crm_field_vue.temp_data = {...data['crm_fieds_data']}
            crm_field_vue.required_fields = data['required_fields']
            // crm_field_vue.field_data = JSON.parse(JSON.stringify(data['crm_fieds_data']))
            // crm_field_vue.temp_data = JSON.parse(JSON.stringify(data['crm_fieds_data']))
            $('#cust_basic_info').removeClass('d-none')
            // check call type is progressive or not
            var dial_method = data["campaign"]["dial_method"]
            sessionStorage.setItem("dial_method", data["campaign"]["dial_method"])
            session_campaign_detail(dial_method)
            callback_mode = data['campaign']['callback_mode']
            $('#select_camp option:selected').attr({"data-server":data["campaign"]["switch"]["ip_address"],
            "data-feedback_time":data["campaign"]["auto_feedback_time"], 
            "data-progressive_time":data["campaign"]["auto_progressive_time"]})
            dnc=data['campaign']['dnc']
            $("#LeadPreview").prop("checked", true)
            $("#crm-agent-logout").attr("onclick", "")
            var script_avail = jQuery.isEmptyObject(data["script"])
            if (script_avail == false) {
                $("#script_name").text(data["script"]["name"])
                $("#script_description").html(data["script"]["text"])
            }
            if (data["campaign"]["portifolio"] == true && user_caller_id != "None") {
                sessionStorage.setItem("caller_id", user_caller_id)
            } else if (data["campaign"]["portifolio"] == false) {
                sessionStorage.setItem("caller_id", data["campaign_caller_id"])
            } else {
                sessionStorage.setItem("caller_id", "")
            }
            if (data["campaign"]["transfer"]){
                sessionStorage.setItem("can_transfer",true)
            }
            else{
                sessionStorage.setItem("can_transfer",false)
            }
            if (data["campaign"]["conference"]){
                sessionStorage.setItem("can_conference",true)
                // $('#transfer-type-select').find('option[value="three-way-calling"]').prop("disabled",false)
            }
            else{
                sessionStorage.setItem("can_conference",false)
                // $('#transfer-type-select').find('option[value="three-way-calling"]').prop("disabled",true)
            }

            agent_info_vue.agent_breaks = data["campaign"]["breaks"]
            $('#crm-agent-logout,#agent_to_admin_switchscreen').attr('style', 'display:none !important');
            sessionStorage.setItem("camp_assigned_calls", data['total_camp_assigned_calls'])
            set_agent_dashboard_count()
        },
        error: function(data) {
            $('.preloader').fadeOut('fast');
            errorAlert('OOPS!!! Something Went Wrong', data['responseJSON']['error']);
            initial_dialler_state()
            $("#select_camp").prop('selectedIndex', 0);
            $('#scSubmit').prop('disabled', true);
            campaign_id = campaign_name = "";
            agent_info_vue.selected_status = 'NotReady'
            $("#select_camp").prop('selectedIndex', 0);
            $('#scSubmit').prop('disabled', true);
        },
        complete: function (data) {
            
        }
    });
});

// logout from dialer
$('#btnLogMeOut').click(function() {
    if (autodial_status != true && manual != true && ibc_status !=true && blndd_status != true ) {
        $('#sms_tab').addClass('d-none')
        $('#documents_tab').addClass('d-none')
        $('#email_tab').addClass('d-none')
        sessionStorage.removeItem('previous_number')
        sip_login = false
        $("#crm-agent-logout").attr("onclick", "confirmLogout()")
        $('#camp_name_div,#show-campaign-assigned-calls').addClass('d-none')
        $('#campain_name_disp').text('')
        $('#fb_timer').click()
        $("#fb_timer").remove()
        $("#dummy-fb-time").append('<span id="fb_timer" class="pl-1"></span>')
        $('#fb_timer_div,#skip_btn_div, #pause_pro_div').addClass("d-none")
        $("#show-agent-kycdocument").addClass("d-none")
        var preview_number = ""
        var contact_id =  sessionStorage.getItem('contact_id')
        if ($("#phone_number").text().trim() != "Empty") {
            preview_number = $("#phone_number").text().trim()
        }
        $('.preloader').fadeIn('fast');
        // var campaign = $("#select_camp :selected").text()
        $('#break_timer').countimer('stop');    
        // $(".agent-break-status").addClass("d-none")
        if(agent_info_vue.isMobile()){
            $('#mb_landing_page').removeClass('d-none');
            $('#mb_dialer_screen, #btnLogMeOut , .mb-page-header').addClass('d-none')
        }
        agent_info_vue.selected_status = 'NotReady'
        if (session_details[extension]['Unique-ID'] || call_type == 'webrtc') {
            var logout_data = {
                'uuid': session_details[extension]['Unique-ID'],
                'switch': session_details[extension]['variable_sip_from_host'],
                'hangup_type': 'sip_agent',
                'extension': extension,
                'campaign_name': campaign_name,
                'preview_number': preview_number,
                'call_type': call_type,
                'contact_id':contact_id,
                'page_reload':page_reload,
            }
            var agent_activity_data = create_agent_activity_data()
            $.extend(logout_data, agent_activity_data)
            $.ajax({
                type: 'post',
                headers: { "X-CSRFToken": csrf_token },
                url: '/api/hangup_call/',
                data: logout_data,
                success: function(data) {
                    dial_flag = false
                    agent_info_vue_mode.show_modes=false
                    $('#crm-agent-logout,#agent_to_admin_switchscreen').attr("style","")
                    $("#agent-breaks-div").addClass("d-none")
                    if (call_type == 'webrtc') {
                        if (sipStack) {
                            sipStack.stop()
                        }
                        SIPml["b_initialized"] = false
                    }
                    session_details[extension] = {};
                    crm_field_vue.field_schema = []
                    $('#cust_basic_info, #btnParkCall').addClass('d-none')
                    $('#cust_basic_info a').editable('setValue', '');
                    crm_field_vue.field_data = {}
                    crm_field_vue.resetBasicField()
                    call_info_vue.resetCallInfo()
                    $("#MDPhonENumbeR, #manual-dial-now, #dialpad-toggle, #btnLogMeOut, #btnNextCall, #flexy-agent-dialpad button").attr("disabled", false)
                    $("#MDPhonENumbeR").val("")
                    $("#profile-tab, #btnNextCall, #show-callbacks-active, #show-callbacks-campaign, #show-abandonedcalls-campaign, #show-campaign-lead-bucket, #show-campaign-assigned-calls, #show-camp-requeue-lead-bucket, #show-camp-assigned-dialed-calls, #show-camp-assigned-notdialed-calls,#show-Reconfirmappointment-calls").removeClass("disabled")
                    $("#dispo-collaps button").removeClass("active")
                    $("#submit_customer_info").attr("disabled", true)
                    $("#feedback_tab_link, #relation_tag_link").addClass("disabled")
                    $("#contact-info").click()
                    $("#btnResumePause").attr({
                        "class": "btn btn-success btn-lg d-none",
                        "title": "Start Predictive Dialing"
                    })
                    $("#ibc_btnResumePause").attr({
                        "class": "btn btn-danger btn-lg d-none",
                        "title": "Start Inbound"
                    })
                    $("#blndd_btnResumePause").attr({
                        "class": "btn btn-danger btn-lg d-none",
                        "title": "Start Blended Mode"
                    })
                    $("#btnResumePause,#ibc_btnResumePause,#blndd_btnResumePause").find('i').attr("class", "fa fa-play")
                    $("#agent-break-status").addClass("d-none")
                    if($('#iframe_tab_link').hasClass('active')){
                        $('#iframe_tab_li').addClass('d-none')
                        $('#iframe_tab_link, #iframe-tab').removeClass('active show')
                        $('#iframe-tab').find('iframe').prop("src", "")
                    }
                    $('#iframe_tab_li').addClass('d-none')
                    $('#iframe_tab_link, #iframe-tab').removeClass('active show')
                    $('#iframe-tab').find('iframe').prop("src", "")
                    flush_agent_timer()
                    $('#app_timer, #idle_timer').countimer('start');
                    $('.breadcrumb li').find('#crm-home').trigger('click')
                    $("#script_name").text("")
                    $("#script_description").html("")
                    $('#list_li').addClass('d-none')
                    $('#list-info, #list-info-tab').removeClass('active show')
                    sessionStorage.setItem('can_transfer',false)
                    sessionStorage.setItem('can_conference', false)
                    campaign_name = ''
                    dispo_vue.reset_dispoform()
                    redial_status = false
                    if (sessionStorage.getItem("outbound") == "Progressive") {
                        // $('#fb_timer').countimer('stop');
                        $('#fb_timer').click()
                        $("#fb_timer").remove()
                        $("#dummy-fb-time").append('<span id="fb_timer" class="pl-1"></span>')
                        $('#fb_timer_div').addClass('d-none');
                        $("#stop_pro_div,#pause_pro_div,#skip_btn_div").addClass('d-none')
                    }
                    if (sessionStorage.getItem("outbound") == "Preview") {
                        $("#fb_timer_div, #skip_btn_div").addClass("d-none")
                        $("#fb_timer").click()
                        $("#fb_timer").remove()
                        $("#dummy-fb-time").append('<span id="fb_timer" class="pl-1"></span>')
                    }
                    if (sessionStorage.getItem("outbound") == "Predictive") {
                        if ($("#predictive_timer").countimer('stopped') == false) {
                            $("#predictive_timer").countimer('stop');
                            $("#predictive_timer").text('00:00:00');
                            $('#predictive_timer_div').addClass('d-none')
                            if ($('#predictive_timer_display').countimer('stopped') == false) {
                                $('#predictive_timer_display').countimer('stop')
                                $('#predictive_timer_display').text('00:00:00')
                            }
                        }
                        if ($('#wait_timer').countimer('stopped') == false) {
                            $('#wait_timer').countimer('stop');
                        }
                        $('#wait_timer').text('0:0:0')
                        sessionStorage.setItem("wait_time", "0:0:0");
                    }
                    clear_cache();
                    // if ($.fn.DataTable.isDataTable('#call-history-table')) {
                    //     call_history_table.clear().destroy();
                    //     $('#call-history-table').empty()
                    // }
                }
            });
        }
        // socket.close();
        $('.preloader, #call-loader').fadeOut('fast');
        $('#setting-content-dialer-tab ul').addClass('d-none');
        $('#flexy_agent_login').removeClass('d-none');
        $("#select_camp").prop('selectedIndex', 0);
        $('#scSubmit').prop('disabled', true);
        agent_relationtag_vue.relationTag_list = []
        agent_relationtag_vue.resetRelationForm()
        agent_relationtag_vue.taggingData_list = []
        email_templates.restetEmailTemplate();
    } else if (autodial_status == true) {
        showInfoToast("Stop Autodialling To Logout", 'top-center')
    } else if (ibc_status == true) {
        showInfoToast("Stop Inbound To Logout", 'top-center')
    } else if (!$("#btnDialHangup").hasClass("d-none") || manual == true) {
        showInfoToast("First Hangup Call To Logout", 'top-center')
    }

})

// on focus of mnaual dial input show dialpad
$("#dialpad-toggle").click(function(){
    $('#AgentDialPad').slideToggle('slow')
})
// dial pad button click to insert value in input
$('#AgentDialPad button').click(function() {
    if(agent_info_vue.state == 'InCall'){
        dtmf_value = $(this).text().trim()
        click_dtmf(dtmf_value)
    }else{ 
        var mdinput = $('#MDPhonENumbeR');
        if ($(this).attr('id') == 'dialer-pad-undo') {
            $(mdinput).val(
                function(index, value) {
                    return value.substr(0, value.length - 1);
                })
        } else if ($(this).attr('id') == 'dialer-pad-clear') {
            mdinput.val("");
        } else {
            mdinput.val(mdinput.val() + $(this).text());
        }
    }
})
//skip btn functionality
$('#skip_btn').click(function(){
    Isprogressive = IsPreview = false
    $("#profile-tab").removeClass("disabled")
    $("#wait_timer, #dialer_timer,#progressive_timer").countimer('stop');
    $("#wait_timer, #dialer_timer,#progressive_timer").text("0:0:0");
    var dial_number = $("#phone_number").text().trim()
    if (dial_number == "Empty") {
        dial_number = ""
    }
    var campaign_name = $("#select_camp :selected").text()
    var contact_id = sessionStorage.getItem('contact_id')
    var form_data = { "campaign_name": campaign_name, "user_name": user_name, "dial_number": dial_number,
    "contact_id": contact_id}
    var activity_data = create_agent_activity_data()
    $.extend(form_data, activity_data)
    sessionStorage.setItem("dialer_time", "0:0:0");
    sessionStorage.setItem("pause_progressive_time","0:0:0")
    $.ajax({
        type:'post',
        headers: { "X-CSRFToken": csrf_token },
        url: '/api/skip-call/',
        data: form_data,
        success: function(data){
            dial_flag = false
            $('#skip_btn, #btnNextCall,#btnDialHangup, #btnPrevCall').prop('disabled', false)
            $('#LeadPreview').parent().removeClass('pt-none')
            $("#dialer_timer, #idle_timer").countimer('start')
            crm_field_vue.resetBasicField()
            call_info_vue.resetCallInfo()
            crm_field_vue.field_data = {}
            sessionStorage.removeItem('contact_id')
            sessionStorage.removeItem("unique_id")
            sessionStorage.removeItem("previous_number")
            $('#profile-tab, #show-callbacks-active, #show-callbacks-campaign, #show-abandonedcalls-campaign, #show-campaign-lead-bucket, #show-campaign-assigned-calls, #show-camp-requeue-lead-bucket, #show-camp-assigned-dialed-calls, #show-camp-assigned-notdialed-calls,#show-Reconfirmappointment-calls').removeClass('disabled')
            $("#btnLogMeOut").attr("disabled", false)
            $('#btnDialHangup').addClass('d-none').removeAttr('contact_id')
            $("#livecall h3").removeClass().addClass("nolivecall").text("NO LIVE CALL").attr("title", "NO LIVE CALL");
            if (sessionStorage.getItem("outbound") == "Progressive") {
                $('#timer_pause_progressive').click()
                $('#progressive_timer').countimer('stop')
                sessionStorage.setItem("progressive_time", "0:0:0");
                $('#pause_progressive_timer').countimer('stop')
                $("#pause_progressive_timer,#progressive_timer").text('0:0:0')
                sessionStorage.setItem("pause_progressive_time","0:0:0")
                $('#show-callbacks-campaign,#show-callbacks-active,#MDPhonENumbeR,#dialpad-toggle').attr('disabled',false)
                // agent_info_vue.state = 'Idle'
                set_agentstate('Idle')
                $('#fb_timer_div,#skip_btn_div,#pause_pro_div, #stop_pro_div').addClass('d-none')
                $("#fb_timer").click()
                $("#fb_timer").remove()
                $(".progressive_pause_div").find("button").remove()
                $("#dummy-fb-time").append('<span id="fb_timer" class="pl-1"></span>')
                $("#fb_timer_div strong").text("WrapUp Time :")
                
            }else if(sessionStorage.getItem("outbound") == "Preview"){
                $("#MDPhonENumbeR, #manual-dial-now, #dialpad-toggle, #flexy-agent-dialpad").prop("disabled", false);
                // agent_info_vue.state = 'Idle'
                set_agentstate('Idle')
                $('#fb_timer_div,#skip_btn_div').addClass('d-none')
                $("#fb_timer").click()
                $("#fb_timer").remove()
                $("#dummy-fb-time").append('<span id="fb_timer" class="pl-1"></span>')
                $("#fb_timer_div strong").text("WrapUp Time :")
                $('#preview_timer').countimer('stop')
                $('#preview_timer').text("0:0:0")
                sessionStorage.setItem("preview_time", "0:0:0");
            }else{
                reste_basic_crm()
                showWarningToast(data['error'], 'top-center')
            }
            $('#stop_pro_div').addClass('d-none')
            if (inboundCall_picked == true) {
                incoming_call_functionality(inbound_dialed_uuid, inbound_action)
            }
        }
    })
})

function reset_dialnext_fields(){
    $('#idle_timer').countimer('start')
    $('#fb_timer').click()
    $("#fb_timer").remove()
    $("#dummy-fb-time").append('<span id="fb_timer" class="pl-1"></span>')
    $("#fb_timer_div, #skip_btn_div").addClass("d-none")
    $("#livecall h3").removeClass().addClass("nolivecall").text("NO LIVE CALL").attr("title", "NO LIVE CALL");
    // agent_info_vue.state = 'Idle'
    set_agentstate('Idle')
    $("#MDPhonENumbeR, #manual-dial-now, #dialpad-toggle, #flexy-agent-dialpad").prop("disabled", false);
    $("#btnNextCall, #btnLogMeOut").prop("disabled", false)
    $('#btnDialHangup').addClass('d-none').removeAttr('contact_id')
    $("#fb_timer_div strong").text("WrapUp Time :")
}

$("#LeadPreview").change(function(){
    var lead_preview = $("#LeadPreview").prop("checked")
    if (Isprogressive == true && lead_preview == false){
          $('#btnDialHangup,#skip_btn_div,#fb_timer_div').addClass('d-none')
          if (sessionStorage.getItem("outbound") == "Progressive") {
              $('#fb_timer').click()
              $("#fb_timer").remove()
              $("#dummy-fb-time").append('<span id="fb_timer" class="pl-1"></span>')
        } 
        $('#btnDialHangup').trigger("click")
    }
 })
 //Pause progressive Timer 
$('#pause_pro_btn').click(function(){
    $('#timer_pause_progressive').click()
    $("#progressive_timer").countimer('stop')
    $('#progressive_timer').text("0:0:0")
    $('#pause_progressive_timer').countimer('start')
    $('#pause_pro_btn').addClass('d-none')
    $('#btnNextCall,#btnDialHangup, #btnPrevCall').prop('disabled', true)
    $('#stop_pro_div').removeClass('d-none')
    $('#LeadPreview').parent().addClass('pt-none')
    // agent_info_vue.state = 'Progressive Pause'
    set_agentstate('Progressive Pause')
    var campaign = $("#select_camp :selected").text()
    var dial_number = $("#phone_number").text().trim()
    var form_data = { "campaign_name": campaign, "user_name": user_name, "dial_number": dial_number }
    var activity_data = create_agent_activity_data()
    $.extend(form_data, activity_data)
    $.ajax({
        type:'post',
        headers: { "X-CSRFToken": csrf_token },
        url: '/api/pause-progressive-call/',
        data: form_data,
        success:function(){
           
            // $('#pause_pro_btn').html("<button type='button' class='btn btn-danger btn-rounded btn-icon' id='resume_pro_btn'><i class='far fa-resume'></i></button>")
        }
    })
})
//stop progressive Timer 
$('#stop_pro_btn').click(function(){
    $('#timer_pause_progressive').click()
    $("#progressive_timer").countimer('start')
    $('#pause_progressive_timer').countimer('stop')
    $('#pause_progressive_timer').text("0:0:0")
    $('#stop_pro_div').addClass('d-none')
    $('#pause_pro_btn').removeClass('d-none')
    $('#skip_btn, #btnNextCall,#btnDialHangup, #btnPrevCall').prop('disabled', false)
    $('#LeadPreview').parent().removeClass('pt-none')
    // agent_info_vue.state = 'Progressive Dialling'
    set_agentstate('Progressive Dialling')
    var campaign = $("#select_camp :selected").text()
    var dial_number = $("#phone_number").text().trim()
    var form_data = { "campaign_name": campaign, "user_name": user_name, "dial_number": dial_number }
    var activity_data = create_agent_activity_data()
    $.extend(form_data, activity_data)
    $.ajax({
        type:'post',
        headers: { "X-CSRFToken": csrf_token },
        url: '/api/stop-progressive-call/',
        data: form_data,
        success:function(){
        }
    })
})
//dial next call
dial_flag = false
Isprogressive = IsPreview= false
$("#btnNextCall").click(function() {
    if (extension in session_details && Object.keys(session_details[extension]).length > 0){
        Isprogressive = IsPreview = true
        $("#profile-tab").addClass("disabled")
        $("#btnLogMeOut").attr("disabled", true)
        if ($('#list_li').hasClass('d-none') == false) {
            $('#list_li').addClass('d-none')
            $('#list-info, #list-info-tab').removeClass('active show')
        }
        $('.breadcrumb li').find('#crm-home').trigger('click')
        var dial_number = $("#phone_number").text().trim()
        var contact_id =  sessionStorage.getItem('contact_id', '')
        if (dial_number == "Empty") {
            dial_number = ""
        }
        else {
            sessionStorage.setItem('previous_number', dial_number)
        }
        var lead_preview = $("#LeadPreview").prop("checked")
        var campaign = $("#select_camp :selected").text()
        $("#call-loader").fadeIn("fast")
        if (lead_preview == true) {
            if (sessionStorage.getItem("outbound") == "Progressive") {
                $("#progressive_timer").countimer('start'); 
                $('#pause_pro_btn').removeClass('d-none')  
            } 
            if(sessionStorage.getItem("outbound") == "Preview"){
                $("#preview_timer").countimer('start');
                $('#pause_pro_btn').addClass('d-none')
                $('#stop_pro_btn').removeClass('d-none')
            }
            var status_data = { "campaign_name": campaign, "user_name": user_name, "dial_number": dial_number,
                        "call_type":sessionStorage.getItem("outbound") , "contact_id":contact_id, "campaign_id":campaign_id}
            var agent_activity_data = create_agent_activity_data()

            $.extend(status_data, agent_activity_data)
            $(" #dialer_timer").countimer('stop');
            $(" #dialer_timer").text("0:0:0");
            $.ajax({
                type: 'post',
                headers: { "X-CSRFToken": csrf_token },
                url: '/api/preview-update-contact-status/',
                data: status_data,
                success: function(data) {
                    $("#dialer_timer").countimer('start')
                    dial_flag = true
                    if ("contact_info" in data && Object.keys(data["contact_info"]).length != 0) {
                        $('#btnDialHangup').find("i").removeClass('fas fa-stop').addClass("fa fa-phone fa-rotate-90");
                        $('#btnDialHangup').removeClass("btn-danger").addClass("btn-success").prop({"title": "Dial" });
                        $('#cust_basic_info a').editable('setValue', '');
                        $("#editable-form").trigger("reset")
                        if ("contact_info" in data) {
                            showcustinfo(data["contact_info"])
                            call_info_vue.callflow = 'Outbound'
                            call_info_vue.dailed_numeric = data["contact_info"]['numeric']
                            sessionStorage.setItem('contact_id', data["contact_info"]["id"])
                        }
                        $('#profile-tab, #show-callbacks-active, #show-callbacks-campaign, #show-abandonedcalls-campaign, #show-campaign-lead-bucket, #show-campaign-assigned-calls, #show-camp-requeue-lead-bucket, #show-camp-assigned-dialed-calls, #show-camp-assigned-notdialed-calls,#show-Reconfirmappointment-calls').addClass('disabled')
                        $("#btnLogMeOut").attr("disabled", true)
                        if (sessionStorage.getItem("outbound") == "Progressive") {
                            $('#fb_timer').click()
                            $("#fb_timer").remove()
                            $("#dummy-fb-time").append('<span id="fb_timer" class="pl-1"></span>')
                            // $(".progressive_pause_div").find('button').remove()
                            $(".progressive_pause_div").html('<button class="d-none" id="timer_pause_progressive"></button>')
                            $("#fb_timer_div, #skip_btn_div, #pause_pro_div").removeClass("d-none")
                            $('#show-callbacks-campaign,#show-callbacks-active,#MDPhonENumbeR').attr('disabled','disabled')
                            $('#dialpad-toggle').prop('disabled',true)
                            $("#fb_timer_div strong").text("Auto Call :")
                            $("#livecall h3").removeClass().addClass("text-success").text("LIVE CALL").attr("title", "LIVE CALL");
                            // agent_info_vue.state = 'Progressive Dialling'
                            set_agentstate('Progressive Dialling')
                            $("#btnDialHangup").removeClass("d-none").prop("disabled", false).attr("contact_id", data["contact_info"]["id"])
                            $('#idle_timer').countimer('stop')
                            $('#idle_timer').text("0:0:0")
                            sessionStorage.setItem('idle_time',"0:0:0")
                            initiate_agent_timer("#idle_timer", "0:0:0")
                            progressive_timer()
                        }
                        if (sessionStorage.getItem("outbound") == "Preview") {
                            $("#btnDialHangup").removeClass("d-none").prop("disabled", false).attr("contact_id", data["contact_info"]["id"])
                            $("#MDPhonENumbeR, #manual-dial-now, #dialpad-toggle, #flexy-agent-dialpad").prop("disabled", true);
                            $("#fb_timer_div, #skip_btn_div").removeClass("d-none")
                            $("#skip_btn").attr("title","Stop Preview Dialing")
                            $("#dummy-fb-time").html('<span id="fb_timer" class="pl-1"></span>')
                            preview_timer_display = sessionStorage.getItem("preview_time");
                            preview_timer_display = sessionStorage.setItem("preview_time", "0:0:0"); 
                            agent_timer_data = agent_time_format(preview_timer_display)
                            initiate_agent_timer("#fb_timer", agent_timer_data)
                            $("#fb_timer_div strong").text("Preview Time :")
                            $("#livecall h3").removeClass().addClass("text-success").text("LIVE CALL").attr("title", "LIVE CALL");
                            // agent_info_vue.state = 'Preview Dialling'
                            set_agentstate('Preview Dialling')
                            $("#fb_timer").text('00:00:00');
                            $("#fb_timer").countimer('start');
                            $('#idle_timer').countimer('stop')
                            $('#idle_timer').text("0:0:0")
                            sessionStorage.setItem('idle_time',"0:0:0")
                            initiate_agent_timer("#idle_timer", "0:0:0")
                        }
                        $("#call-loader").fadeOut("fast")
                    } else {
                        if($("#phone_number").text().trim() == "") {
                            if (sessionStorage.getItem("outbound") == "Preview"){
                                $("#preview_timer").countimer('stop');
                                reset_dialnext_fields()
                            }else{
                                $("#progressive_timer").countimer('stop');
                                $("#stop_pro_div,#pause_pro_div").addClass('d-none')
                                reset_dialnext_fields()
                            }
                            Isprogressive = IsPreview= false
                            $('#cust_basic_info a').editable('setValue', '');
                            $("#btnLogMeOut").attr("disabled", false)

                            $('#profile-tab, #show-callbacks-active, #show-callbacks-campaign, #show-abandonedcalls-campaign, #show-campaign-lead-bucket, #show-campaign-assigned-calls, #show-camp-requeue-lead-bucket, #show-camp-assigned-dialed-calls, #show-camp-assigned-notdialed-calls,#show-Reconfirmappointment-calls').removeClass('disabled')
                            // agent_info_vue.state = 'Idle'
                            set_agentstate('Idle')
                        }
                        showInfoToast("Numbers are not present in this campaign", 'top-center')
                        $("#call-loader").fadeOut("fast")
                    }
                },
                error: function(data) {
                    if($("#phone_number").text().trim() == "") {
                        if (sessionStorage.getItem("outbound") == "Preview"){
                            $("#preview_timer").countimer('stop');
                            reset_dialnext_fields()
                        }else{
                            $("#progressive_timer").countimer('stop');
                            $("#stop_pro_div,#pause_pro_div").addClass('d-none')
                            reset_dialnext_fields()
                        }
                        Isprogressive = IsPreview= false
                        $('#cust_basic_info a').editable('setValue', '');
                        $("#btnLogMeOut").attr("disabled", false)
                        $('#profile-tab, #show-callbacks-active, #show-callbacks-campaign, #show-abandonedcalls-campaign, #show-campaign-lead-bucket, #show-campaign-assigned-calls, #show-camp-requeue-lead-bucket, #show-camp-assigned-dialed-calls, #show-camp-assigned-notdialed-calls,#show-Reconfirmappointment-calls').removeClass('disabled')
                        // agent_info_vue.state = 'Idle'
                        set_agentstate('Idle')
                    }
                    $("#call-loader").fadeOut("fast")
                    $("#dialer_timer").countimer('start')
                }
            })
        } else {
            init_time = new Date($.now());
            manual = true
            $("#wait_timer, #app_timer, #dialer_timer").countimer('stop')
            $("#MDPhonENumbeR, #manual-dial-now, #dialpad-toggle, #flexy-agent-dialpad").prop("disabled", true);
            var details = JSON.stringify(session_details[extension])
            $(this).attr("disabled", true)
            dial_number = ""
            var caller_id = sessionStorage.getItem("caller_id")
            if(sessionStorage.getItem("outbound") == "Progressive"){
               callmode = 'progressive'
            }else if(sessionStorage.getItem("outbound") == "Preview"){
               callmode = 'preview'
            }
            var call_data = {
                "dial_number": dial_number,
                'campaign_name': campaign,
                'user_name': user_name,
                'session_details': details,
                'call_type': 'not_manual',
                'caller_id': caller_id,
                'outbound': sessionStorage.getItem("outbound"),
                'callmode': callmode,
                'lead_preview':lead_preview,
                "campaign_id":campaign_id
            }
            var agent_activity_data = create_agent_activity_data()
            $.extend(call_data, agent_activity_data)

            $.ajax({
                type: 'post',
                headers: { "X-CSRFToken": csrf_token },
                url: '/api/manual_dial/',
                data: call_data,
                success: function(data) {
                    $("#wait_timer, #app_timer, #dialer_timer").text("0:0:0")
                    $("#dialer_timer").countimer('start')
                    manual = false
                    if('dialed_uuid' in data){
                        session_details[extension]['dialed_uuid'] = data['dialed_uuid']
                    }
                    if('dialed_number' in data){
                        call_info_vue.dailed_numeric = data['dialed_number']
                        sessionStorage.setItem('previous_number', data['dialed_number'])
                        call_info_vue.callflow = 'Outbound'
                    }
                    if ("contact_info" in data) {
                        showcustinfo(data['contact_info'])
                        if (sms_templates.is_manual_sms){
                            $('#sms_tab').removeClass('d-none')
                        }
                        if (email_templates.email_type == '2'){
                            $('#email_tab').removeClass('d-none')
                        }
                        sessionStorage.setItem('contact_id', data["contact_info"]["id"])
                    }
                    ring_time = new Date($.now());
                    $("#call-loader").fadeOut("fast")
                    if (data['success']) {
                        $("#ring_timer").countimer('start')
                        HangupCss()
                        $("#btnLogMeOut, #btnNextCall").prop("disabled", true)
                        $("#btnParkCall").removeClass("d-none")
                        if (sessionStorage.getItem('can_transfer') == "true"){
                            $("#btnTransferCall").removeClass("d-none")
                        }
                        $("#profile-tab, #btnNextCall, #agent-callbacks-div button, #show-callbacks-active, #show-callbacks-campaign, #show-abandonedcalls-campaign, #show-campaign-lead-bucket, #show-campaign-assigned-calls, #show-camp-requeue-lead-bucket, #show-camp-assigned-dialed-calls, #show-camp-assigned-notdialed-calls,#show-Reconfirmappointment-calls").addClass("disabled")
                        $("#btnNextCall").addClass("d-none")
                        $("#livecall h3").removeClass().addClass("text-success").text("LIVE CALL").attr("title", "LIVE CALL");
                        // agent_info_vue.state = 'InCall'
                        set_agentstate('InCall')
                    } else if ("msg" in data) {
                        showInfoToast(data['msg'], 'top-center')
                        $("#MDPhonENumbeR, #manual-dial-now, #dialpad-toggle, #flexy-agent-dialpad").prop("disabled", false);
                        $("#btnNextCall").prop("disabled", false)
                    } else {
                        calldetail_id = data['calldetail_id']
                        hangup_time = new Date($.now());
                        showWarningToast(data['error'], 'top-center')
                        if ($("#fb_timer_div").hasClass("d-none")) {
                            $("#fb_timer_div").removeClass("d-none")
                            $("#fb_timer_div strong").text("WrapUp Time :")
                        }
                        timer_on_hangup()
                        $("#feedback_timer").countimer('start');
                        hangup_cause_code_er = ''
                        hangup_cause_er = 'NOT_FOUND'
                        dialed_status_er = 'NOT_FOUND'
                    }
                },
            })
        }
    } else {
        showWarningToast('Session details not avaliabe, Re-Login to dialler', 'top-center')
        $('#btnLogMeOut').click()
    }
})

function HangupCss() {
    $('#btnDialHangup').find("i").removeClass("fa fa-phone fa-rotate-90").addClass("fas fa-stop")
    $('#btnDialHangup').removeClass("btn-success d-none").addClass("btn-danger").prop({
        "disabled": false,
        "title": "Hangup Call",
    });
}

function hangup_activity() {
    $('#btnDialHangup').find("i").removeClass('fas fa-stop').addClass("fa fa-phone fa-rotate-90");
    $('#btnDialHangup').removeClass("btn-danger").addClass("btn-success").prop({
        "disabled": true,
        "title": "Dial"
    });
    $("#btnLogMeOut, #btnNextCall").prop("disabled", true)
    $("#profile-tab, #btnNextCall,#show-callbacks-active, #show-callbacks-campaign, #show-abandonedcalls-campaign, #show-campaign-lead-bucket, #show-campaign-assigned-calls, #show-camp-requeue-lead-bucket, #show-camp-assigned-dialed-calls, #show-camp-assigned-notdialed-calls,#show-Reconfirmappointment-calls").addClass("disabled")
    if (sessionStorage.getItem("manual") == "true") {
        $("#flexy-agent-manualdial, #flexy-agent-dialpad").removeClass("d-none")
        $("#MDPhonENumbeR, #manual-dial-now, #dialpad-toggle, #flexy-agent-dialpad").prop("disabled", true);
    }
    $("#btnParkCall, #btnTransferCall").prop("disabled", true);
    $("#MDPhonENumbeR").val("");
    if (sessionStorage.getItem("outbound") == "Preview" || sessionStorage.getItem("outbound") == "Progressive") {
        $("#btnNextCall").removeClass("d-none")
    }
    if (sessionStorage.getItem("outbound") == "Predictive") {
       if (sessionStorage.getItem("inbound") == "true"){
            if ($.inArray(sessionStorage.getItem("ibc_popup"),["","true"]) != -1){
                $("#btnResumePause").removeClass("d-none")
            }else{
                $("#blndd_btnResumePause").removeClass("d-none")
            }
        }else{
            $("#btnResumePause").removeClass("d-none")            
        }        
    }
    if (sessionStorage.getItem("inbound") == "true" && sessionStorage.getItem("outbound") != "Predictive" && $.inArray(sessionStorage.getItem("ibc_popup"),["","false"]) != -1) {
        $("#ibc_btnResumePause").removeClass("d-none")
    }    
    $("#btnDialHangup, #btnParkCall, #btnTransferCall").addClass("d-none")
    $("#livecall h3").removeClass().addClass("nolivecall").text("NO LIVE CALL").attr("title", "NO LIVE CALL");
    agent_info_vue.state = 'Feedback'
    set_agentstate('Feedback')
    $("#relation_tag_link, #feedback_tab_link").removeClass('disabled');
    $("#feedback_tab_link").trigger("click")
}
auto_feedback = false
function stopped_feedback_func() {
    $("#fb_timer").click()
    $("#fb_timer").remove()
    $("#dummy-fb-time").append('<span id="fb_timer" class="pl-1"></span>')
    if (!$("#feedback_tab_link").hasClass("disabled")) {
        auto_feedback = true
        $('#submit_customer_info').click();
    }
    else if (sessionStorage.getItem("outbound") == "Progressive" && dial_flag == true ) {
        $("#btnDialHangup").click()
        $('#skip_btn_div, #pause_pro_div').addClass('d-none')
    }
}

// hangup and dial call btn
$('#btnDialHangup').click(function() {
    // var campaign_name = $("#select_camp :selected").text()
    $("#call-loader").fadeIn("fast")
    var contact_id = sessionStorage.getItem('contact_id')
    if ($(this).attr("title") == "Dial" || $(this).attr("title") == "Dial Previous Call") {
        if (Isprogressive == true || IsPreview == true) {
            if (sms_templates.is_manual_sms){
                $('#sms_tab').removeClass('d-none')
            }
            if (email_templates.email_type == '2'){
                $('#email_tab').removeClass('d-none')
            }
        }
        Isprogressive = IsPreview= false
        $('#skip_btn_div, #pause_pro_div').addClass('d-none')
        init_time = new Date($.now());
        callmode = 'outbound';
        $("#wait_timer, #dialer_timer").countimer('stop');
        agent_hangup = false
        manual = true
        $("#MDPhonENumbeR, #manual-dial-now, #dialpad-toggle, #show-callbacks-campaign,#show-abandonedcalls-campaign, #show-callbacks-active, #flexy-agent-dialpad button").prop("disabled", true);
        if (sessionStorage.getItem("outbound") == "Progressive") {
            $('#fb_timer').click()
            $("#fb_timer").remove()
            $("#dummy-fb-time").append('<span id="fb_timer" class="pl-1"></span>')
            $('#fb_timer_div').addClass('d-none');
        }
        if (!$("#fb_timer_div").hasClass("d-none")) {
            $("#fb_timer_div").addClass("d-none")
            $("#fb_timer_div strong").text("WrapUp Time :")
        }
        $("#btnDialHangup, #btnNextCall").attr("disabled", true)
        if( $(this).attr("title") == "Dial Previous Call") {
            var dial_number = sessionStorage.getItem('previous_number')
        }
        else {
            var dial_number = $("#phone_number").text().trim()
            sessionStorage.setItem('previous_number',dial_number)
        }
        
        var details = JSON.stringify(session_details[extension])
        var caller_id = sessionStorage.getItem("caller_id")
        var call_data = {
            "dial_number": dial_number,
            'campaign_name': campaign_name,
            'user_name': user_name,
            'session_details': details,
            'call_type': "not_manual",
            'caller_id': caller_id,
            'outbound': sessionStorage.getItem("outbound"),
            'contact_id':contact_id,
            'lead_preview':true,
            'unique_id':sessionStorage.getItem("unique_id")
        }
        sessionStorage.setItem("progressive_time_val", sessionStorage.getItem('progressive_time'))
        sessionStorage.setItem("preview_time_val", sessionStorage.getItem('preview_time'))
        var agent_activity_data = create_agent_activity_data()
        $.extend(call_data, agent_activity_data)
        if (sessionStorage.getItem("outbound") == "Progressive") {
            $("#progressive_timer").countimer('stop');
            $("#progressive_timer").text("0:0:0")
            callmode = 'progressive'
        } 
        if(sessionStorage.getItem("outbound") == "Preview"){
            $("#preview_timer").countimer('stop');
            $("#preview_timer").text("0:0:0")
            $("#fb_timer").countimer('stop')
            $("#fb_timer").text("0:0:0")
            callmode = 'preview'
        }
        call_data["callmode"] = callmode
        $.ajax({
            type: 'post',
            headers: { "X-CSRFToken": csrf_token },
            url: '/api/manual_dial/',
            data: call_data,
            success: function(data) {
                if($(this).attr("title") == "Dial Previous Call") {
                    $(this).addClass("d-none")
                }
                $("#wait_timer, #dialer_timer").text("0:0:0")
                $("#dialer_timer").countimer('start');
                manual = false
                $("#call-loader").fadeOut("fast")
                ring_time = new Date($.now());
                session_details[extension]['dialed_uuid'] = data['dialed_uuid']
                if (data['success']) {
                    // agent_info_vue.state = 'InCall'
                    set_agentstate('InCall')
                    $("#ring_timer").countimer('start');
                    $("#btnNextCall").addClass("d-none")
                    HangupCss()
                    $("#btnParkCall").removeClass("d-none")
                    if (sessionStorage.getItem('can_transfer') == "true"){
                        $("#btnTransferCall").removeClass("d-none")
                    }
                    $("#agent-callbacks-div button").addClass("disabled")
                    $("#btnLogMeOut, #btnNextCall").prop("disabled", true)
                } 
                else if ("info" in data) {
                    showInfoToast(data["info"], 'top-center')
                    $("#skip_btn").trigger("click")
                    $("#MDPhonENumbeR, #manual-dial-now, #dialpad-toggle, #flexy-agent-dialpad, #btnNextCall").prop("disabled", false);
                    sessionStorage.removeItem("previous_number")
                } else {
                    calldetail_id = data['calldetail_id']
                    var previous_number = sessionStorage.getItem('previous_number','')
                    if (previous_number) {
                        sessionStorage.setItem('previous_contact_id', $('#btnDialHangup').attr("contact_id"))
                        $("#btnPrevCall").removeClass("d-none")
                    }
                    hangup_time = new Date($.now());
                    showWarningToast(data['error'], 'top-center')
                    if ($("#fb_timer_div").hasClass("d-none")) {
                        $("#fb_timer_div").removeClass("d-none")
                        $("#fb_timer_div strong").text("WrapUp Time :")
                    }
                    timer_on_hangup()
                    $("#feedback_timer").countimer('start');
                    hangup_cause_code_er = ''
                    hangup_cause_er = 'NOT_FOUND'
                    dialed_status_er = 'NOT_FOUND'
                 }
            },
        })
    }else {
        if($(".mobile_no_search_div").length) {
            $(".mobile_no_search_div").addClass("d-none")
        }
        if(!$("#contents-agent-assigned-calls").hasClass("d-none")) {
            $("#contents-agent-assigned-calls").addClass("d-none")
        }
        var previous_number = sessionStorage.getItem('previous_number','')
        if (previous_number) {
            sessionStorage.setItem('previous_contact_id', $(this).attr("contact_id"))
            $("#btnPrevCall").removeClass("d-none")
        }
        var call_data = {
            'switch': session_details[extension]['variable_sip_from_host'],
            'campaign_name': $("#select_camp option:selected").text(),
            'call_type': call_type
        }
        if($(this).attr("title") == "Transferhangup"){
            url = '/agent/api/internal_transfercall_hangup/'
            call_data['uuid']=session_details[extension]['transfer_from_agent_uuid']
        }else{
            url = '/api/hangup_call/'
            if (Object.keys(dummy_session_details).length != 0){
                call_data['uuid']=dummy_session_details['dialed_uuid']
                call_data['agent_uuid_id'] = dummy_session_details['Unique-ID']
            } else{
                call_data['uuid']=session_details[extension]['dialed_uuid']
                call_data['agent_uuid_id'] =session_details[extension]['Unique-ID']
            }
        }
        
        agent_hangup = true
        hangup_time = new Date($.now());
        sessionStorage.setItem("predictive_time_val", sessionStorage.getItem("predictive_time"))
        var agent_activity_data = create_agent_activity_data()
        agent_activity_data['hangup_source'] = "AGENT"
        $.extend(call_data, agent_activity_data)
        $('#btnResumePause,#ibc_btnResumePause,#blndd_btnResumePause').attr('disabled', true)
        if(add_three_way_conference_vue.three_way_list.length > 0){
            add_three_way_conference_vue.confHangupAll()
        }
        $.ajax({
            type: 'post',
            headers: { "X-CSRFToken": csrf_token },
            url: url,
            data: call_data,
            success: function(data) {
                add_three_way_conference_vue.three_way_list = []
                isTransferableCall = disable_conference =conference_initiated = false
                $('#speak_timer, #ring_timer, #dialer_timer').countimer('stop');
                if ($("#fb_timer_div").hasClass("d-none")) {
                    $("#fb_timer_div").removeClass("d-none")
                    $("#fb_timer_div strong").text("WrapUp Time :")
                }
                if(transferCall_picked == true){
                    // transferCall_picked = false
                    var socket_data ={"transfer_from_agent_number":session_details[extension]['transfer_from_agent_number']}
                    if($("#btnDialHangup").attr("title") == "Transferhangup"){
                        socket.emit("transfer_to_agent_rejected",socket_data)
                    }
                }
                $("#dialer_timer, #speak_timer, #ring_timer").text("0:0:0")
                $('#dialer_timer').countimer('start');
                $("#call-loader").fadeOut("fast")
                timer_on_hangup()
                $('#hold_timer, #display_hold_timer').countimer('stop');
                $('#btnParkCall').removeClass('active')
                $("#feedback_timer").countimer('start');
                if($('#iframe_tab_link').hasClass('active')){
                    $('#iframe_tab_li').addClass('d-none')
                    $('#iframe_tab_link, #iframe-tab').removeClass('active show')
                    $('#iframe-tab').find('iframe').prop("src", "")
                }
            },
            error: function(data){
                $("#call-loader").fadeOut("fast")
            }
        })
    }
});

// resume and pause auto dial
var autodial_status = false
$('#btnResumePause').click(function() {
    btn_title = $(this).attr("title")
    if ((extension in session_details && Object.keys(session_details[extension]).length > 0) || btn_title !="Start Predictive Dialing"){
        if (btn_title == "Start Predictive Dialing") {
            if ($('#list_li').hasClass('d-none') == false) {
                $('#list_li').addClass('d-none')
                $('#list-info, #list-info-tab').removeClass('active show')
            }
            $('.breadcrumb li').find('#crm-home').trigger('click')
            // agent_info_vue.state = 'Predictive Wait'
            set_agentstate('Predictive Wait')
            $(this).removeClass("btn-success").addClass("btn-danger")
            $(this).find('i').removeClass().addClass("fas fa-pause");
            $(this).attr("title", "Stop Predictive Dialing");
            $("#MDPhonENumbeR").text("")
            $("#MDPhonENumbeR, #manual-dial-now, #dialpad-toggle,#show-callbacks-campaign,#show-abandonedcalls-campaign, #show-callbacks-active,#flexy-agent-dialpad button").prop("disabled", true);
            $("#btnParkCall, #btnTransferCall").prop("disabled", false);
            autodial_status = true
            $("#btnLogMeOut").attr("disabled", true)
            $("#crm-agent-logout").attr("onclick", "")
            $("#agent_breaks").addClass("restrict-agent_break")
            $("#predictive_timer").countimer('start');
            $('#idle_timer').countimer('stop');
            $("#agent-callbacks-div button, #profile-tab,#show-callbacks-active, #show-callbacks-campaign, #show-abandonedcalls-campaign, #show-campaign-lead-bucket, #show-campaign-assigned-calls, #show-camp-requeue-lead-bucket, #show-camp-assigned-dialed-calls, #show-camp-assigned-notdialed-calls,#show-Reconfirmappointment-calls").addClass("disabled")
            predictive_time  = sessionStorage.getItem("predictive_time"); 
            agent_timer_data = agent_time_format(predictive_time)
            initiate_agent_timer("#predictive_timer_display", agent_timer_data)
            $('#predictive_timer_div').removeClass('d-none')
            $('#predictive_timer_div strong').text('Predictive Call :')
            $('#predictive_timer_display').countimer('start')
        } else {
            // agent_info_vue.state = 'Idle'
            $("#agent_breaks").removeClass("restrict-agent_break")
            $(this).removeClass("btn-danger").addClass("btn-success")
            $(this).find('i').removeClass().addClass("fas fa-play");
            $(this).attr("title", "Start Predictive Dialing");
            $("#MDPhonENumbeR, #manual-dial-now, #dialpad-toggle,#show-callbacks-campaign,#show-abandonedcalls-campaign, #show-callbacks-active, #flexy-agent-dialpad button").prop("disabled", false);
            $("#btnParkCall, #btnTransferCall").prop("disabled", true);
            $("#livecall h3").removeClass().addClass("nolivecall").text("NO LIVE CALL").attr("title", "NO LIVE CALL");

            set_agentstate('Idle')
            $("#agent-callbacks-div button, #profile-tab, #show-callbacks-active, #show-callbacks-campaign, #show-abandonedcalls-campaign, #show-campaign-lead-bucket, #show-campaign-assigned-calls, #show-camp-requeue-lead-bucket, #show-camp-assigned-dialed-calls, #show-camp-assigned-notdialed-calls,#show-Reconfirmappointment-calls").removeClass("disabled")
            // autoDailAlert('Auto call Dialing stop')
            autodial_status = false
            $("#btnLogMeOut").attr("disabled", false)
            $("#crm-agent-logout").attr("onclick", "")
            $("#predictive_timer").countimer('stop');
            $('#predictive_timer_div').addClass('d-none')
            $('#predictive_timer_display').text('00:00:00')
            $('#wait_timer').countimer('stop');
            // sessionStorage.setItem('outbound', '')
            $('#predictive_timer_display').countimer('stop')
        }
        autodial_data = {
            'uuid': session_details[extension]['Unique-ID'],
            'switch': session_details[extension]['variable_sip_from_host'],
            'extension': extension,
            'autodial_status': autodial_status,
            'campaign_name': campaign_name,
            'sip_error': sip_error
        }
        var agent_activity_data = create_agent_activity_data()
        agent_activity_data["predictive_time"] = sessionStorage.getItem("predictive_time")
        agent_activity_data["predictive_wait_time"] = sessionStorage.getItem("wait_time")
        $.extend(autodial_data, agent_activity_data)
        $.ajax({
            type: 'post',
            headers: { "X-CSRFToken": csrf_token },
            url: '/api/start-autodial/',
            data: autodial_data,
            success: function(data) {
                flush_agent_timer()
                $('#wait_timer').text('0:0:0')
                sessionStorage.setItem("wait_time", "0:0:0");
                $("#dialer_timer").countimer('start');
                if ("success" in data) {
                    if (autodial_status == true) {
                        $('#wait_timer').countimer('start');
                        $("#crm-agent-logout").attr("onclick", "")
                        $('#idle_timer').text("0:0:0")
                        sessionStorage.setItem("idle_time", "0:0:0");
                        initiate_agent_timer("#idle_timer", "0:0:0")

                    } else {
                        $("#predictive_timer").text('0:0:0')
                        $('#idle_timer').countimer('start')
                        sessionStorage.setItem("predictive_time", "0:0:0");
                        if (!$("#feedback_tab_link").hasClass("disabled")) {
                            $("#btnResumePause").prop("disabled", true)
                        }
                    }
                } else {
                    errorAlert('OOPS!!! Something Went Wrong',data["error"]);
                }
            }
        })
    } else {
        showWarningToast('Session details not avaliabe, Re-Login to dialler', 'top-center')
        $('#btnLogMeOut').click()
    }
});

initial_hold_time = true
// park call
$('#btnParkCall').click(function() {
    var dialed_uuid = session_details[extension]['dialed_uuid']
    if (dialed_uuid) {
        if ($('#btnParkCall').hasClass('active')) {
            $('#btnParkCall').removeClass("active")
            var park_status = false;
        } else {
            $('#btnParkCall').addClass('active');
            var park_status = true
        }
    }
    var data = {
        'Unique-ID'  : session_details[extension]['Unique-ID'],
        'dialed_uuid': dialed_uuid,
        'park_status': park_status,
        'sip_server': session_details[extension]['variable_sip_from_host'],
    }
    $.ajax({
        type: 'post',
        headers: { "X-CSRFToken": csrf_token },
        url: '/api/park_call/',
        data: data,
        success: function(data) {
            if (park_status) {
                $('#SecondsDISP').countimer('stop')
                if (initial_hold_time == true) {
                    $("#hold_timer").countimer('start')
                    $("#display_hold_timer").countimer('start')
                    $("#call_hold_timer").removeClass('d-none')
                    initial_hold_time = false
                }
                else {
                    $("#hold_timer").countimer('resume')
                    $("#display_hold_timer").countimer('resume')
                }
            } else {
                $("#hold_timer").countimer('stop')
                $("#display_hold_timer").countimer('stop')
                $('#SecondsDISP').countimer('resume')
            }
            sessionStorage.setItem("hold_time", $("#hold_timer").text())
        },
        error: function(err) {
            $('#btnParkCall').removeClass("active")
        }
    });
});

$("#transfer-call-modal").on("hidden.bs.modal", function() {
    $("#internal_div, #external_div").addClass("d-none")
    $('.transfer-radio input').prop("checked", false)
    $("#make-transfer").addClass("btn-success").removeClass("btn-danger").text("Make Transfer")
    $("#merge-transfer").addClass("d-none")
});

// park call on ivr
$('#btnIVRParkCall').click(function() {
    alert("IVR Park Call")
});

// requeue call
$('#btnReQueueCall').click(function() {
    alert("Re Que Call")
});

// quick transfer call
$('#btnQuickTransfer').click(function() {
    alert("Quick Transfer")
});

function reste_basic_crm() {
    $("#btnLogMeOut, #btnNextCall").attr("disabled", false)
    crm_field_vue.resetBasicField()
    call_info_vue.resetCallInfo()
    $('#editable-form, #dispo-form').trigger("reset");
    $("#MDPhonENumbeR").val("")
    $("#MDPhonENumbeR, #manual-dial-now, #dialpad-toggle, #flexy-agent-dialpad").prop("disabled", false);
    var dial_method = sessionStorage.getItem("dial_method")
    session_campaign_detail(dial_method)
}
function do_manual_call(dial_number, contact_id="") {
    init_time = new Date($.now());
    if(!$("#contents-agent-assigned-calls").hasClass("d-none")) {
        $("#contents-agent-assigned-calls").addClass("d-none")
        $("#crm-home").click()
    }
    $('.breadcrumb li').find('#crm-home').trigger('click')
    if (($("#contact_detail_modal").data('bs.modal') || {})._isShown == true ) {
        $('#contact_detail_modal').modal('hide');
    }
    if (!$('#list_li').hasClass("d-none")) {
        $('#list_li').addClass("d-none")
    }
    // $('#AgentDialPad').slideUp('slow')
    agent_hangup = false
    $("#idle_timer,#app_timer, #dialer_timer").countimer('stop')
    manual = true
    var preview_number = ""
    if ($("#phone_number").text().trim() != "") {
        preview_number = $("#phone_number").text().trim()
    }
    if($(this).attr("id") == "manual-dial-now") {
        dial_flag = false
    }
    // stopped fb timer bcz in case if progessive auto call timer is on and agent clicks on manual call
    // $('#fb_timer').countimer('stop')
    $('#fb_timer').click()
    $("#fb_timer").remove()
    $("#dummy-fb-time").append('<span id="fb_timer" class="pl-1"></span>')
    $('#fb_timer_div').addClass('d-none');
    $("#MDPhonENumbeR, #manual-dial-now, #dialpad-toggle, #flexy-agent-dialpad").prop("disabled", true);
    $("#call-loader").fadeIn("fast")
    var caller_id = sessionStorage.getItem("caller_id")
    var details = JSON.stringify(session_details[extension])
    var call_data = {
        "dial_number": dial_number,
        'campaign_name': campaign_name,
        'user_name': user_name,
        'session_details': details,
        'preview_number': preview_number,
        'call_type': 'manual',
        'caller_id': caller_id,
        'is_callback': is_callback,
        'is_abandoned_call': is_abandoned_call,
        'is_abandoned_callback':is_abandoned_callback,
        'contact_id':contact_id,
        'callmode':callmode,
        'campaign_id':campaign_id
    }
    sessionStorage.setItem("previous_number", dial_number)
    var agent_activity_data = create_agent_activity_data()
    $.extend(call_data, agent_activity_data)
    $.ajax({
        type: 'post',
        headers: { "X-CSRFToken": csrf_token },
        url: '/api/manual_dial/',
        data: call_data,
        success: function(data) {
            $("#idle_timer, #app_timer, #dialer_timer").text("0:0:0")
            manual = false
            is_callback = false
            is_abandoned_call = false
            is_abandoned_callback = false
            $("#call-loader").fadeOut("fast")
            $("#dialer_timer").countimer('start')
            $("#editable-form").trigger("reset")
            session_details[extension]['dial_number'] = dial_number
            if (redial_status == false && call_info_vue.alt_dial == false) {
                if ('contact_info' in data) {
                    if(data['contact_count'] > 1 ){
                        $('#contact-info, #contact-info-tab').removeClass('active show')
                        if (is_abandoned_callback == true) {
                            callmode = 'callback'
                        }
                        $("#list_li").removeClass("d-none")
                        $("#list-info").click()
                        $('#list-info, #list-info-tab').addClass('active show')
                        list_of_contacts_table.clear().draw()
                        list_of_contacts_table.rows.add(data['contact_info']);
                        list_of_contacts_table.draw();
                    }
                    else {
                        showcustinfo(data['contact_info'])
                        sessionStorage.setItem('contact_id', data['contact_info']["id"])
                    }
                }
            }
            redial_status = call_info_vue.alt_dial = false
            if (data['success']) {
                $('#call-history-tab').removeClass('disabled');
                ring_time = new Date($.now());
                $("#ring_timer").countimer('start')
                session_details[extension]['dialed_uuid'] = data['dialed_uuid']
                call_info_vue.callflow = 'Outbound'
                call_info_vue.dailed_numeric = data['dialed_number']
                HangupCss()
                $("#profile-tab, #show-callbacks-active, #show-callbacks-campaign, #show-abandonedcalls-campaign, #show-campaign-lead-bucket, #show-campaign-assigned-calls, #show-camp-requeue-lead-bucket, #show-camp-assigned-dialed-calls, #show-camp-assigned-notdialed-calls,#show-Reconfirmappointment-calls").addClass("disabled")
                $("#btnResumePause,#ibc_btnResumePause,#blndd_btnResumePause").addClass("d-none")
                $("#btnLogMeOut").attr("disabled", true)
                $("#btnParkCall, #toggleMute").removeClass("d-none")
                if (sessionStorage.getItem('can_transfer') == "true"){
                    $("#btnTransferCall").removeClass("d-none")
                }

                $("#agent-callbacks-div button").addClass("disabled")
                if (sessionStorage.getItem("outbound") == "Preview" || sessionStorage.getItem("outbound") == "Progressive") {
                    $("#btnNextCall").addClass("d-none")
                }
                $("#livecall h3").removeClass().addClass("text-success").text("LIVE CALL").attr("title", "LIVE CALL");
                // agent_info_vue.state = 'InCall'
                set_agentstate('InCall')
            } else if ("info" in data) {
                $("#contact-info").trigger('click')
                showInfoToast(data["info"], 'top-center')
                $("#MDPhonENumbeR").val("")
                $("#MDPhonENumbeR, #manual-dial-now, #dialpad-toggle, #flexy-agent-dialpad").prop("disabled", false);
                sessionStorage.removeItem("previous_number")
                session_details[extension]['dial_number'] = ""
            } else {
                calldetail_id = data['calldetail_id']
                session_details[extension]['dialed_uuid'] = data['dialed_uuid']
                call_info_vue.callflow = 'Outbound'
                call_info_vue.dailed_numeric = data['dialed_number']
                var previous_number = sessionStorage.getItem('previous_number','')
                if (previous_number) {
                    sessionStorage.setItem('previous_contact_id', $('#btnDialHangup').attr("contact_id"))
                    $("#btnPrevCall").removeClass("d-none")
                }
                hangup_time = new Date($.now());
                showWarningToast(data['error'], 'top-center')
                if ($("#fb_timer_div").hasClass("d-none")) {
                    $("#fb_timer_div").removeClass("d-none")
                    $("#fb_timer_div strong").text("WrapUp Time :")
                }
                timer_on_hangup()
                $("#feedback_timer").countimer('start');
                hangup_cause_code_er = ''
                hangup_cause_er = 'NOT_FOUND'
                dialed_status_er = 'NOT_FOUND'
            }
        },
    })
}
// manual dial call
redial_status = false
$('#btnPrevCall').click(function() {
    redial_status = true
    $("#submit_customer_info").click()
    $(this).addClass("d-none")
    $('#fb_timer_div,#skip_btn_div,#pause_pro_div').addClass('d-none')
})

function common_manual_call_function(dial_number, data) {
    $.ajax({
        type: 'post',
        headers: { "X-CSRFToken": csrf_token },
        url: '/api/manual_dial_list/',
        data: data,
        success: function(data) {
            if(data['contact_count'] > 1){
                if('contact_info' in data){
                    $('#contact-info, #contact-info-tab').removeClass('active show')
                    if(is_abandoned_callback) {
                        $("#crm-home").trigger("click")
                    }
                    if (is_abandoned_callback == true) {
                         callmode = 'callback'
                    }
                    $("#list-info").click()
                    // $('#list_li').removeClass('d-none')
                    $('#list-info, #list-info-tab').addClass('active show')
                    list_of_contacts_table.clear().draw()
                    list_of_contacts_table.rows.add(data['contact_info']);
                    list_of_contacts_table.draw();
                   
                }else if('error' in data){
                    showWarningToast('Contact Info is Not avaliabe', 'top-right')
                }
            }
            else {
                if (is_abandoned_call == true) {
                    callmode = 'abandonedcall'
                }
                else if (is_abandoned_callback == true) {
                    callmode = 'callback'
                    $('#crm-home').trigger("click")
                     $('#notification_modal').modal('hide')
                }
                else {
                    callmode = 'manual'
                }
                var contact_id = ""
                if(data['contact_info'].length > 0){
                    contact_id = data['contact_info'][0]['id']
                }
                do_manual_call(dial_number,contact_id)
            }
        }
    })
}

$('#manual-dial-now').click(function() {
    $('#show_contact_list').removeClass('disabled');
    var dial_number = $("#MDPhonENumbeR").val();
    var phoneNo = document.getElementById('MDPhonENumbeR');

  if (phoneNo.value == "" || phoneNo.value == null) {
    showInfoToast('Please enter phone number to dial', 'top-right')
    return false;
  }
  if (phoneNo.value.length < 4 || phoneNo.value.length > 20) {
    showInfoToast('Please enter valid number ', 'top-right')
    return  ;
  }
    if(dial_number){
        if (extension in session_details && Object.keys(session_details[extension]).length > 0){
            var data = {'dial_number':dial_number, 'campaign':campaign_name}
            $('.breadcrumb li').find('#crm-home').trigger('click');     
            sessionStorage.setItem('previous_number', dial_number)
            var contact_id = ""
            callmode = 'manual'
            do_manual_call(dial_number,contact_id)
            // common_manual_call_function(dial_number, data)
        } else {
            showWarningToast('Session details not avaliabe, Re-Login to dialler', 'top-center')
            $('#btnLogMeOut').click()
        }
    }
    else{
        showInfoToast('Please enter phone number to dial', 'top-right')

    }
});

function process(input){
        let value = input.value;
        let numbers = value.replace(/[^0-9]/g, "");
        input.value = numbers;
      }

$(document).on("click", ".view-detail", function() {
    var contact_id = $(this).attr("id")
    var number = $(this).attr("phone_number")
    var campaign = $(this).attr("campaign")
    $.ajax({
            type: 'get',
            headers: { "X-CSRFToken": csrf_token },
            url: `/api/get-contact-info/${contact_id}/`,
            data: {},
            success: function(data) {
                crm_data_vue.crm_data = data
                $(".makecall_footer_div .contact-make-call").attr({"contact_id":contact_id, "phone_number":number, "campaign":campaign})
                $("#contact_detail_modal").modal('show');
                if(callmode == "inbound" || callmode=="blended" || callmode == "manual"){
                    $('.makecall_footer_div').addClass('d-none')
                }else{
                    $('.makecall_footer_div').removeClass('d-none')
                }
            }
        })
})
$('#contact_detail_modal').on('hidden.bs.modal', function () {
    crm_data_vue.crm_data = {}
})
$(document).on("click", ".inbound-view-detail", function() {
    var row_id = $(this).attr("id")
    var temp_data = inbound_all_cust_detail[0][row_id]
    inbound_cust_detail_vue.cust_detail = temp_data
    $('#inbound_contact_detail_modal').modal('show');
})
$(document).on("click", ".contact-make-call", function() {
    if($(this).attr('campaign')==campaign_name){
        if (extension in session_details && Object.keys(session_details[extension]).length > 0) {
            var dial_number = $(this).attr('phone_number')
            var contact_id = $(this).attr("contact_id")
            console.log(dial_number, contact_id)
            $('#show_contact_list').addClass('disabled')
            if(is_abandoned_callback) {
                callmode = 'callback'
            }
            else {
                callmode = 'manual'
            }
            do_manual_call(dial_number, contact_id)
            $('#crm-home').trigger("click")
            $('#dialer-tab').trigger("click")
        } else {
            showWarningToast('Session details not avaliabe, Re-Login to dialler', 'top-center')
            $('#btnLogMeOut').click()
        }
    } else {
        showWarningToast(`Login to <b>${$(this).attr('campaign')}</b> campaign to make call`, 'top-right')
    }
})

$(document).on("click", ".contact-set-call", function() {
    var ic_number = $(this).attr("phone_number")
    var contact_id = $(this).attr("contact_id")
    set_inbound_customer_detail(ic_number,contact_id)
})

$(document).on("click", ".inbound-contact-set-call", function() {
   var row_id = $(this).attr("row_id")
   var temp_data = incoming_call_list[0][row_id]
   showmysqlinfo([temp_data])
   // $('#list_li').addClass('d-none')
    $('#contact-info, #contact-info-tab').addClass('active show')
    $('#list-info, #list-info-tab').removeClass('active show')
})

// this function to create information on feedback submit
call_reset_agent_status = true
var sent_sms_flag = false
function create_feedback_data(){
    call_reset_agent_status = true
    if (Object.keys(dummy_session_details).length == 0){
        dummy_session_details = {...session_details[extension]}
    }
    var feedback_dict = {}
    var custinfo;
    var primary_dispo;
    var alt_numeric_dict = {}
    custinfo = crm_field_vue.basic_field_data;
    call_info_vue.alt_numeric.filter(function(val,index){
        if(val['alt_label'] == ''){
            val['alt_label'] = 'alt_num_'+(index+1)
        }
        alt_numeric_dict[val['alt_label']] = val['alt_value']
    })
    custinfo['alt_numeric'] = JSON.stringify(alt_numeric_dict)
    custinfo["status"] = ""
    custinfo['user'] = user_name;
    custinfo['campaign'] = campaign_name;
    if(sent_sms_flag){
        crm_field_vue.update_crm = true
        crm_field_vue.field_data['sms_status'] = {}
        crm_field_vue.field_data['sms_status']['status'] = true
    }
    custinfo['customer_raw_data'] = JSON.stringify(crm_field_vue.field_data);
    custinfo['hangup_cause_code_er'] = hangup_cause_code_er
    custinfo['hangup_cause_er'] = hangup_cause_er
    custinfo['dialed_status_er'] = dialed_status_er
    primary_dispo = dispo_vue.selected_pd
    // see the isconfirm contacts is true or false  
    custinfo['isconfirm'] = dispo_vue.reconfirm_disp
    if (auto_feedback == true ) {
       if(primary_dispo == ''){
            primary_dispo = 'AutoFeedback'
        }
    }
    if (redial_status == true) {
        primary_dispo = 'Redialed'   
        call_reset_agent_status = false
    }
    if (call_info_vue.alt_dial == true) {
        primary_dispo = 'AlternateDial'   
        if (call_info_vue.primary_dial){
            primary_dispo = 'PrimaryDial'   
        }
        call_reset_agent_status = false
    }
    custinfo['primary_dispo'] = primary_dispo;
    var callback_field = $("#dispo-form").find('input[name=default_schedule_time]')
    if(callback_field.length > 0 && $.inArray(primary_dispo,['AutoFeedback','Redialed','AlternateDial'])== -1){
        if($(callback_field[0]).val() != ''){
            custinfo['schedule_time'] = $(callback_field[0]).val()
            custinfo['callback_title'] = $(callback_field[0]).data('label')
            custinfo['callback_type'] = callback_mode
        }
    }
    if(custinfo['primary_dispo'].toLowerCase() === 'dnc'){
        if (dnc == 'local'){
            custinfo['global_dnc']=false
        }else{
            custinfo['global_dnc']=true   
        }
    }
    var cb_schedule_counter = 0
    $.each($("#dispo-form").serializeArray(), function(_, kv) {
        if(kv.name == "default_schedule_time"){
            var cb_name = $(callback_field[cb_schedule_counter]).data('label')
            feedback_dict[cb_name] = kv['value']
            cb_schedule_counter++;
        }else if(kv.name == 'sys_update_lead_user'){
            var lead_user_val = $('#sys_update_lead_user').select2('data')[0]
            if (lead_user_val['text'] !='Select User'){
                custinfo[kv.name] = lead_user_val['text']
            }
            if ('data-reverify' in lead_user_val && lead_user_val['data-reverify']){
                custinfo['sys_reverify_lead'] = true
            }
        }else{
            if(kv.name in feedback_dict){
                feedback_dict[kv.name] = feedback_dict[kv.name]+','+kv.value
            }else{
                feedback_dict[kv.name] = kv.value 
            }
        }
    })
    $.each($("#dispo-form input:checkbox"), function(index,val){
        if(val.value == 'on'){
            feedback_dict[val.name] = val.checked
        }
    })

    $.each($("#extraInfo-form").serializeArray(), function(_, kv) {
        if (kv.name == 'comment') {
            custinfo['comment'] = kv.value
        }
    })
    if(primary_dispo != 'AutoFeedback' && redial_status == false && call_info_vue.alt_dial == false) {
        custinfo['feedback'] = JSON.stringify(feedback_dict);
    }
    else {
        custinfo['feedback'] = JSON.stringify({});   
    }
    if (update_sql_database == true && sessionStorage.getItem("third_party_data_fetch") == "true") {
        var mobile_no = ''
        if ('customer_information' in crm_field_vue.field_data && 'mobile_no' in crm_field_vue.field_data['customer_information']){
            mobile_no = crm_field_vue.field_data['customer_information']['mobile_no']
        }
        update_mysqldatabase_details(mobile_no,feedback_dict, custinfo['primary_dispo'])
    }
    custinfo['relation_tag'] = JSON.stringify(agent_relationtag_vue.taggingData_list)
    if (transferCall_picked == true){
        transferCall_picked = false
        custinfo['session_uuid'] = dummy_session_details['transfer_from_agent_uuid']
        custinfo['b_leg_uuid'] = dummy_session_details['transfer_from_agent_uuid']
    }else{
        custinfo['session_uuid'] = dummy_session_details['dialed_uuid']
        custinfo['b_leg_uuid'] = dummy_session_details['dialed_uuid']
    }
    custinfo['a_leg_uuid'] = dummy_session_details['Unique-ID']
    custinfo['c_init_time'] = format_time(init_time)
    custinfo['c_ring_time'] = format_time(ring_time)
    custinfo['c_connect_time'] = format_time(connect_time)
    wait_time = diff_seconds(ring_time, init_time)
    wait_time = moment.utc(wait_time*1000).format('HH:mm:ss');
    if (autodial_status == true) {
        wait_time = "00:00:00"
    }
    custinfo['wait_time'] = wait_time
    custinfo['media_time'] = wait_time
    custinfo['callmode'] = callmode
    custinfo['callflow'] = callflow
    custinfo['hold_time'] = sessionStorage.getItem('hold_time')
    custinfo['feedback_time'] = sessionStorage.getItem("feedback_time")
    custinfo['bill_sec'] = $('#SecondsDISP').text()
    custinfo['customer_cid'] = sessionStorage.getItem('previous_number','')
    custinfo['destination_extension'] = extension
    custinfo['c_hangup_time'] = format_time(hangup_time)
    custinfo['switch_ip'] = dummy_session_details["variable_sip_from_host"]
    custinfo['uuid'] = dummy_session_details['Unique-ID']
    if (autodial_hangup == true) {
        custinfo['call_type'] = "autodial"
        custinfo['predictive_wait_time'] = sessionStorage.getItem('wait_time')
    }else if(inbound_hangup == true) {
        custinfo['call_type'] = "inbound"
        custinfo['inbound_wait_time'] = sessionStorage.getItem('wait_time')
    }else if(blended_hangup == true) {
        custinfo['call_type'] = "blended"
        custinfo['blended_wait_time'] = sessionStorage.getItem('wait_time')
    }
    else{
        custinfo['call_type'] = "manual"
    }
    custinfo['autodial_status'] = autodial_status
    custinfo['inbound_status'] = ibc_status
    custinfo['blended_status'] = blndd_status
    // transfer data
    session_transfer_time = sessionStorage.getItem("transfer_time")
    custinfo['internal_tc_number'] = sessionStorage.getItem('internal_transfer_no')
    custinfo['external_tc_number'] = sessionStorage.getItem('external_transfer_no')
    //Track agent activities
    custinfo['progressive_time_val'] = sessionStorage.getItem('progressive_time_val') 
    custinfo['predictive_time_val']  = sessionStorage.getItem('predictive_time_val')
    custinfo['inbound_time_val']  = sessionStorage.getItem('inbound_time_val')
    custinfo['blended_time_val']  = sessionStorage.getItem('blended_time_val')
    custinfo['preview_time_val'] = sessionStorage.getItem('preview_time_val')
    if(sessionStorage.getItem('contact_id','') == undefined || sessionStorage.getItem('contact_id','') == "undefined") {
        if(callmode == 'inbound' | callmode == 'inbound-blended' | callmode == 'manual'){    
             if(list_of_contacts_table.rows().any() == true){
                list_cont_id = list_of_contacts_table.rows(0).data()
                sessionStorage.setItem('contact_id',list_cont_id[0].id)
                custinfo['numeric'] = list_cont_id[0].numeric
                custinfo['customer_cid'] = list_cont_id[0].numeric
                custinfo['contact_id'] = sessionStorage.getItem('contact_id')
                custinfo['alt_numeric'] = JSON.stringify(list_cont_id[0].alt_numeric)
                custinfo['first_name'] = list_cont_id[0].first_name
                custinfo['last_name'] = list_cont_id[0].last_name
                custinfo['email'] = list_cont_id[0].email
                custinfo['customer_raw_data'] = JSON.stringify(list_cont_id[0].contact_info)
                crm_field_vue.update_crm = false
            }
        }else{
            custinfo['contact_id'] = ''
        }
    }
    else {
            custinfo['contact_id'] = sessionStorage.getItem('contact_id')
    }
    var agent_activity_data = create_agent_activity_data()
    agent_activity_data["agent_hold_time"] = "00:00:00"
    $.extend(custinfo, agent_activity_data)
    custinfo['sip_error'] = sip_error;
    var subdispo_key = ''
    $.each(JSON.parse(custinfo['feedback']), function(key,value){
        subdispo_key = key
    })
    if(agent_hangup == true){
        custinfo['hangup_source'] = "Agent"
    }
    else if(agent_hangup == false){
        custinfo['hangup_source']= "Customer"
    }else{
        custinfo['hangup_source']= "System"
    }
    if (calldetail_id){
        custinfo['calldetail_id'] = calldetail_id
    }
    custinfo['update_crm'] = crm_field_vue.update_crm
    custinfo['appointed_appraisers'] = crm_field_vue.book_agents_name
    // if (sessionStorage.getItem('thirdparty_data_push') == "true" && primary_dispo == 'Appointment confirmed'){
    //     update_crmapi_details(custinfo['customer_raw_data'], crm_field_vue.created_date) 
    // }
    var cust_raw_data = JSON.parse(custinfo.customer_raw_data)
    if (sessionStorage.getItem('thirdparty_data_push') == "true"){
        if(!cust_raw_data.appointment_details){
            cust_raw_data.appointment_details = {}
        }
        primary_dispo = primary_dispo.toLowerCase(); 
        if(primary_dispo == 'appointment confirmed'){
            updateAppointmentType(cust_raw_data,"new")
        }else if (dispo_vue.reconfirm_disp){
            updateAppointmentType(cust_raw_data,"unconfirm")
        }else if (primary_dispo == 'reschedule appointment'){
            updateAppointmentType(cust_raw_data,"update");
        }
        custinfo.customer_raw_data =JSON.stringify(cust_raw_data)
        if(primary_dispo == 'appointment confirmed' || dispo_vue.reconfirm_disp|| primary_dispo == 'reschedule appointment'){
            update_crmapi_details(custinfo['customer_raw_data'], crm_field_vue.created_date,custinfo['contact_id']) 
        }
    }
    return custinfo
}
function updateAppointmentType(cust_raw_data,type){
    cust_raw_data.appointment_details.type = type
    return cust_raw_data;
}
$("#submit_customer_info").click(function() {
    // localStorage.removeItem("connection_failure_data");
    customer_hangup = false
    crm_field_vue.required_crm = false
    if(agent_info_vue.state != 'InCall'){
        if(redial_status == true || auto_feedback == true || $("#dispo-form").isValid() || call_info_vue.alt_dial == true){
            required_validation = []
            $.each(crm_field_vue.required_fields,function(key,value){
                crm_data = value.split(":")
                if(!crm_field_vue.field_data[crm_data[0]][crm_data[1]] || crm_field_vue.field_data[crm_data[0]][crm_data[1]].length <= 0){
                   crm_field_vue.required_crm = true
                   required_validation.push(crm_data[0])
                   $('#contact-info').click()
                   $('#cust_info_accordion .collapse').collapse('show')
                   return false;
                }
            })
            var unique_required_validation = [...new Set(required_validation)]
            if(unique_required_validation.length > 0){
                // $('#contact-info').click()
                showDangerToast('Required','Field are required in '+unique_required_validation.join(','),'top-center')
                return;
            }
            $(this).attr("disabled", true)
            $("#btnPrevCall").addClass("d-none")
            $("#fb_timer").click()
            $("#fb_timer").remove()
            $("#dummy-fb-time").append('<span id="fb_timer" class="pl-1"></span>')
            $("#feedback_timer").countimer('stop');
            $('#list_li').addClass("d-none")
            inboundCall_picked = false;
            var custinfo = create_feedback_data()
            $.ajax({
                type: 'post',
                headers: { "X-CSRFToken": csrf_token },
                url: '/api/submit_dispo/',
                data: custinfo,
                success: function(data){
                    sent_sms_flag = false
                    kyc_document_vue.documents = []
                    $('.send_sms_btn').text('Send')
                    dispo_vue.on_call_dispo = false
                    crm_field_vue.update_crm = false
                    crm_field_vue.required_crm = false
                    agent_hangup = false
                    if(sms_templates.send_sms_on_dispo){
                        sms_templates.selected_template = []
                        $.each(sms_templates.templates,function(index, value){
                            sms_dict = {}
                            sms_dict['id'] = value.id
                            sms_dict['text'] = $('#sms_text'+value.id).text()
                            sms_templates.selected_template.push(sms_dict)
                        })
                        setTimeout(sms_templates.sendSMS(campaign_id,sms_templates.selected_template,sms_templates.customer_mo_no, custinfo['primary_dispo']), 3000)
                    }
                    if (email_templates.email_type=='1' && $.inArray(dispo_vue.selected_pd, email_templates.email_dispositions) != -1){
                        email_templates.selected_template = []
                        $.each(email_templates.templates,function(index,value){
                            email_dict = {}
                            email_dict['id'] = value['id']
                            email_dict['email_subject'] = $('#email_subject_'+value['id']).text()
                            email_dict['email_body'] = $('#email_body_'+value['id']).text()
                            email_templates.selected_template.push(email_dict)
                        })
                        email_templates.sendEmail()
                    }
                    dummy_session_details = {};
                    session_details[extension]['dialed_uuid'] = '';
                    session_details[extension]['dial_number'] = '';
                    calldetail_id = null;
                    callflow = 'outbound'
                    // agent_info_vue.state = 'Idle'
                    set_agentstate('Idle')
                    initial_hold_time = true
                    sessionStorage.removeItem("internal_transfer_no")
                    sessionStorage.removeItem("external_transfer_no")
                    if(!$(".mobile_no_search_div").hasClass("d-none")) {
                        $(".mobile_no_search_div").addClass("d-none")
                    }
                    sessionStorage.removeItem("prev_selected_contact_id")
                    // checking for dap button status 
                    if(!$('#dap_details').hasClass('d-none')){
                        dap_details_data = ""
                        $('#dap_details').addClass('d-none')
                    }
                    if (blndd_status == true && sessionStorage.getItem("ibc_popup") == "false") {
                        $("#blndd_btnResumePause").attr("disabled", false)
                        $("#blndd_btnResumePause").removeClass("d-none")
                        // agent_info_vue.state = 'Blended Wait'
                        set_agentstate('Blended Wait')
                        blended_hangup = false
                    }else if (autodial_status == true) {
                        $("#btnResumePause").attr("disabled", false)
                        $("#btnResumePause").removeClass("d-none")
                        // agent_info_vue.state = 'Predictive Wait'
                        set_agentstate('Predictive Wait')
                        autodial_hangup = false
                    }else if (ibc_status == true) {
                        $("#ibc_btnResumePause").attr("disabled", false)
                        $("#ibc_btnResumePause").removeClass("d-none")
                        // agent_info_vue.state = 'Inbound Wait'
                        set_agentstate('Inbound Wait')
                        inbound_hangup = false
                    }else {
                        $("#MDPhonENumbeR, #manual-dial-now, #dialpad-toggle, #show-abandonedcalls-campaign, #show-callbacks-active,#show-callbacks-campaign, #btnLogMeOut, #btnNextCall, #btnResumePause,#ibc_btnResumePause,#blndd_btnResumePause").attr("disabled", false)
                        $("#profile-tab, #btnNextCall, #agent-callbacks-div button, #show-callbacks-active, #show-callbacks-campaign, #show-abandonedcalls-campaign, #show-campaign-lead-bucket, #show-campaign-assigned-calls, #show-camp-requeue-lead-bucket, #show-camp-assigned-dialed-calls, #show-camp-assigned-notdialed-calls,#show-Reconfirmappointment-calls").removeClass("disabled")
                    }
                    $("#feedback_tab_link, #relation_tag_link").addClass("disabled")
                    $("#dispo-collaps button").removeClass("active")
                    $("#submit_customer_info").attr("disabled", true)
                    $("#contact-info").click();
                    $('#dispo-form').trigger("reset");
                    $("#extraInfo-form")[0].reset()
                    hangup_time = connect_time = init_time = ring_time = wait_time = "";
                    crm_field_vue.resetBasicField()
                    crm_field_vue.resetExtraField()
                    call_info_vue.resetCallInfo()
                    $('#fb_timer_div').addClass('d-none');
                    $('#SecondsDISP,#display_hold_timer').text("00:00:00");
                    $("#call_duration_timer,#call_hold_timer").addClass('d-none')
                    $('#fb_timer').text('00:00');
                    dispo_vue.secondry_dispo = {}
                    sessionStorage.setItem('progressive_time_val','0:0:0')
                    sessionStorage.setItem('blended_time_val', '0:0:0')
                    sessionStorage.setItem('predictive_time_val', '0:0:0')
                    sessionStorage.setItem('inbound_time_val', '0:0:0')
                    sessionStorage.setItem('preview_time_val','0:0:0')
                    flush_agent_timer()
                    sessionStorage.setItem("wait_time", "0:0:0");
                    initiate_agent_timer("#wait_timer", "0:0:0")
                    initiate_agent_timer("#dialer_timer", "0:0:0")
                    initiate_agent_timer("#hold_timer", "0:0:0")
                    initiate_agent_timer("#feedback_timer", "0:0:0")
                    $('#iframe_tab_li').addClass('d-none')
                    $('#iframe_tab_link, #iframe-tab').removeClass('active show')
                    $('#iframe-tab').find('iframe').prop("src", "")
                    if(autodial_status == true | ibc_status == true | blndd_status == true){
                        $("#wait_timer, #dialer_timer").countimer('start');
                    }else{
                        $("#idle_timer, #dialer_timer").countimer('start');
                    }
                    if(socket_connection_fail == true || !socket.connected){
                        $('#btnLogMeOut').click()
                        $('#crm-agent-logout,#agent_to_admin_switchscreen').attr("style","")
                    }
                    call_history_table.clear().draw();
                    list_of_contacts_table.clear().draw();
                    $.each(crm_field_vue.basic_field_data,function(key,value){
                        $('#script_description').find('[data-id="'+key+'"]').text('${'+key+'}')
                    })
                    dispo_vue.reset_dispoform()
                    if(sip_error == true) {
                        if(sessionStorage.getItem('outbound')=='Predictive' | sessionStorage.getItem('inbound')==true){
                            autodial_status = false
                            ibc_status = false
                            blndd_status = false
                        }
                        $("#btnLogMeOut").trigger("click")
                        $('#crm-agent-logout,#agent_to_admin_switchscreen').attr("style","")
                    }
                    if (redial_status == true && !sip_error && socket.connected) {
                        if ("contact_id" in data) {
                            sessionStorage.setItem('contact_id', data["contact_id"])
                        }
                        callmode = 'redial'
                        var contact_id = sessionStorage.getItem('contact_id', '')
                        if (contact_id == "undefined") {
                            contact_id = ""
                        }
                        var dial_number = sessionStorage.getItem('previous_number', '')
                        do_manual_call(dial_number, contact_id)
                    }else if(call_info_vue.alt_dial == true && !sip_error && socket.connected){
                        callmode = 'alternate-dial'
                        var dial_number = call_info_vue.selected_alt_numeric
                        if(call_info_vue.primary_dial){
                          callmode = 'manual'
                          dial_number = call_info_vue.numeric
                        }
                        call_info_vue.primary_dial = false
                        var contact_id = sessionStorage.getItem('contact_id', '')
                        if (contact_id == "undefined") {
                            contact_id = ""
                        }
                        sessionStorage.setItem('previous_number',dial_number)
                        do_manual_call(dial_number, contact_id)
                    }else{
                        sms_templates.customer_mo_no=''
                        email_templates.customer_email = ''
                        $('#email_tab').addClass('d-none')
                        callmode = 'outbound'
                        sessionStorage.removeItem('contact_id')
                        sessionStorage.removeItem("unique_id")
                        sessionStorage.removeItem("previous_number")
                        $('#list_li').addClass('d-none')
                        $('#list-info, #list-info-tab').removeClass('active show')
                        call_info_vue.show_caret = false
                        redial_status = call_info_vue.alt_dial = call_info_vue.primary_dial = false
                        crm_field_vue.resetBasicField()
                        call_info_vue.resetCallInfo()
                        crm_field_vue.field_data = {}
                        $.each(crm_field_vue.temp_data,function(sec_key, sec_value){
                            $.each(sec_value,function(field_key, field_value){
                                var script_field = sec_key+':'+field_key
                                $('#script_description').find('[data-id="'+script_field+'"]').text('${'+script_field+'}')
                                $.each(email_templates.templates,function(index, value){
                                    $('#email_body_'+value.id).find('[data-id="'+script_field+'"]').text('${'+script_field+'}')
                                })
                            })
                        })
                        $.each(crm_field_vue.basic_field_data,function(key,value){
                            $('#script_description').find('[data-id="'+key+'"]').text('${'+key+'}')
                            $.each(email_templates.templates,function(index, value){
                                $('#email_body_'+value.id).find('[data-id="'+key+'"]').text('${'+key+'}')
                            })
                        })
                        if(dial_flag==true && !sip_error && socket.connected){
                            if ($.inArray(sessionStorage.getItem('outbound'),["false", "Predictive", null]) == -1){
                                $("#btnNextCall").click()
                            }
                            $(".progressive_pause_div").html('<button class="d-none" id="timer_pause_progressive"></button>')
                        }
                        if(!socket.connected){
                            socket.connect()
                        }
                    }
                    auto_feedback = false
                    add_three_way_conference_vue.three_way_list = []
                    isTransferableCall = disable_conference =conference_initiated = false
                    hangup_cause_code_er = hangup_cause_er = dialed_status_er = ''
                    sessionStorage.setItem("todays_call", data['total_agentcalls_today'])
                    sessionStorage.setItem("monthly_call", data['total_agentcalls_month'])
                    list_of_inbound_contacts_table.clear().draw() // empty data from mssql
                    list_of_contacts_table.clear().draw()
                    $('.show_inbound_contact_div').addClass('d-none') // hide the list while manual 2nd case secanrio 
                    $("#contacts_list_div").removeClass("d-none") // remove class d-none for inbound call list
                    set_agent_dashboard_count()
                    $('#feedback-tab').removeClass('active show')
                    $('#feedback-tab').addClass('hide')
                    // $(".state,.city,.roi,.tenure,.rebate").text("")

                    // view is used to reset agent availability status
                    if (call_reset_agent_status == true && (blndd_status == true||
                        autodial_status == true || ibc_status == true)) {
                        $.ajax({
                            type: 'post',
                            headers: { "X-CSRFToken": csrf_token },
                            url: '/api/reset-agent-availabilty-status/',
                            data: {"uuid":session_details[extension]['Unique-ID'],
                            "sip_error":sip_error, "switch_ip":session_details[extension]["variable_sip_from_host"]
                            },
                            success: function(data){
                                temp_dispo = ""
                            }})
                    }
                },
                error: function(data){
                    $("#submit_customer_info").attr("disabled",false)
                }
            });
        }
    }else{
        showWarningToast('First hangup call to submit dispostion','top-center')
    }
})

$("#crm-agent-logout").click(function() {
    if (autodial_status == true) {
        showInfoToast("Stop Autodialling To Logout", 'top-center')
    } else if (!$("#btnDialHangup").hasClass("d-none")) {
        showInfoToast("First Hangup Call To Logout", 'top-center')
    } else if (sip_login == true) {
        showInfoToast("First Logout From The Dialer Sip Session", 'top-center')
    } else {
        $(this).attr("onclick", "confirmLogout()")
    }
})
create_data_on_internet_fail = true
// this function to get live data for login agent
function getAgentLivedata() {
    $.ajax({
        type: 'GET',
        url: '/api/agentlivedata/',
        data: { "campaign_name": campaign_name },
        cache: false,
        timeout: 5000,
        success: function(data,textStatus,xhr) {
            if(data['total_callbacks']){
                $('#callbacks').removeClass('d-none')
                $('#callbacks small span').text(data['total_callbacks'])
            }
            else{
                $('#callbacks').addClass('d-none')
            }
            if(data['total_abandonedcalls']){
                $('#abandonedcalls').removeClass('d-none')
                $('#abandonedcalls small span').text(data['total_abandonedcalls'])
            }
            else{
                $('#abandonedcalls').addClass('d-none')
            }
            $('#call_notificationDropdown span').text(data['notifications']);
            // show campain sidebar links if data is there
            if (data['active_callbacks_cc']){
                $('#show-callbacks-active').removeClass('d-none')
                $('#c-activecallbacks-count').text(data['active_callbacks_cc'])
            }
            else{
                $('#show-callbacks-active').addClass('d-none')
            }
            if(data['reconfirm_callbacks_cc']){
                $('#show-Reconfirmappointment-calls').removeClass('d-none')
                $('#c-reconfirmappointment-count').text(data['reconfirm_callbacks_cc'])
            }else{
                $('#show-Reconfirmappointment-calls').addClass('d-none')
            }
            if(data['total_callbacks_cc']){
                $('#c-totalcallbacks-count').text(data['total_callbacks_cc'])
                $('#show-callbacks-campaign').removeClass('d-none')
            }
            else{
                $('#show-callbacks-campaign').addClass('d-none')
            }

            if(data['total_abandonedcalls_cc']){
                $('#c-abandonedcalls-count').text(data['total_abandonedcalls_cc'])
                $('#show-abandonedcalls-campaign').removeClass('d-none')
            }
            else{
                $('#show-abandonedcalls-campaign').addClass('d-none')
            }
            if (data['c_callbacks'].length >= 1) {
                $('#heartbit').removeClass('d-none')
            }
            else {
                $('#heartbit').addClass('d-none')   
            }
            sessionStorage.setItem("dialled_assingned_calls", data['dialled_assingned_calls'])
            sessionStorage.setItem("notdialed_assigned_calls", data['notdialed_assigned_calls'])
            sessionStorage.setItem("campaign_leads_count", data['campaign_leads_count'])
            sessionStorage.setItem("campaign_requeue_leads_count", data['campaign_requeue_leads_count'])
            set_agent_dashboard_count()
        },
        error: function(data){
            // if(data['status'] == 0 && create_data_on_internet_fail==true){
            //     create_data_on_internet_fail = false
            //     agent_activity_data = {}
            //     agent_activity_data = prepare_data_to_store()
            //     agent_activity_data["event"] = "Internet connection failure"
            //     localStorage.setItem("connection_failure_data", JSON.stringify(agent_activity_data));
            // }    
            if(data['status'] == 403){
                create_data_on_internet_fail = true
                sessionTerminatedAlert()
            }
        }
    })
}
getcallbackcalls_vue = new Vue({
    el: '#getcallbackcalls_vue',
    delimiters: ['${', '}'],
    data: {
        total_records:0,
        total_pages:0,
        page:1,
        has_next:false,
        has_prev:false,
        start_index:0,
        end_index:0,
    },
    methods:{
        changePage(value){
             var filter_dict = {}
            $('#nextPage_number').val(value)
            filter_dict['callback_filter_date'] = $('#date_filter_callback_total input').val()
            if ($('#tcb_search_by').val().trim()){
                filter_dict['column_name'] = $('#tcb_column_name').val()
                filter_dict['search_by'] = $('#tcb_search_by').val()
            }
            getTotalCallback(filter_dict)
        }
    }

})
// this fucntion to get total callbacks for agent's campaigns
function getTotalCallback(filter_dict={}) {
    filter_dict['page'] = $('#nextPage_number').val()
    filter_dict['paginate_by'] = $('#page_length').val()
    $.ajax({
        type: 'get',
        url: '/api/get-totalcallbacks/',
        cache: false,
        timeout: 5000,
        data:filter_dict,
        success: function(data) {
            totalCallback_table.clear()
            totalCallback_table.rows.add(data['total_callback']).draw(false);
            getcallbackcalls_vue.total_records=data['total_records']
            getcallbackcalls_vue.total_pages=data['page']
            getcallbackcalls_vue.page=data['page']
            getcallbackcalls_vue.has_next=data['has_next']
            getcallbackcalls_vue.has_prev=data['has_prev']
            getcallbackcalls_vue.start_index=data['start_index']
            getcallbackcalls_vue.end_index=data['end_index']
        }
    })
}

// this function to get active callbacks of login campaign
function getActiveCallback(filter_dict={}) {
    $.ajax({
        type: 'post',
        headers: { "X-CSRFToken": csrf_token },
        url: '/api/get-activecallbacks/',
        data: filter_dict,
        success: function(data) {
            activeCallback_table.clear();
            activeCallback_table.rows.add(data['active_callback']).draw(false);
            active_callback_vue.total_records=data['total_records']
            active_callback_vue.total_pages=data['page']
            active_callback_vue.page=data['page']
            active_callback_vue.has_next=data['has_next']
            active_callback_vue.has_prev=data['has_prev']
            active_callback_vue.start_index=data['start_index']
            active_callback_vue.end_index=data['end_index']
        }
    })
}


active_callback_vue = new Vue({
    el: '#active_callback_vue',
    delimiters: ['${', '}'],
    data: {
        total_records:0,
        total_pages:0,
        page:1,
        has_next:false,
        has_prev:false,
        start_index:0,
        end_index:0,
    },
    methods:{
        changePage(value){
            var filter_dict = {}
            $('#nextPage_number').val(value)
            filter_dict['callback_filter_date'] = $('#date_filter_active_callback_campaign input').val()
            filter_dict['campaign_name'] = campaign_name
            getActiveCallback(filter_dict)
        }
    }
})

function getReConfirmCallback(campaign){
     $.ajax({
        type: 'post',
        headers: { "X-CSRFToken": csrf_token },
        url: '/api/get-reconfirmappointments/',
        data: { "campaign_name": campaign },
        success: function(data) {
            reconfirmCalls_table.clear();
            reconfirmCalls_table.rows.add(data['active_appointments']).draw();
        }
    })
}


// this function is to get total callbacks of current login campaign
function getCampaignTotalCallback(filter_dict={}) {
    $.ajax({
        type: 'post',
        headers: { "X-CSRFToken": csrf_token },
        url: '/api/get-campaigntotalcallbacks/',
        data:filter_dict,
        success: function(data) {
            console.log(data,"=========")
            campaignCallbacks_table.clear();
            campaignCallbacks_table.rows.add(data['campaign_total_callback']).draw(false);
            campagin_callback_vue.total_records=data['total_records']
            campagin_callback_vue.total_pages=data['page']
            campagin_callback_vue.page=data['page']
            campagin_callback_vue.has_next=data['has_next']
            campagin_callback_vue.has_prev=data['has_prev']
            campagin_callback_vue.start_index=data['start_index']
            campagin_callback_vue.end_index=data['end_index']
        }
    })
}

campagin_callback_vue = new Vue({
    el: '#campagin_callback_vue',
    delimiters: ['${', '}'],
    data: {
        total_records:0,
        total_pages:0,
        page:1,
        has_next:false,
        has_prev:false,
        start_index:0,
        end_index:0,
    },
    methods:{
        changePage(value){
            var filter_dict = {}
            $('#nextPage_number').val(value)
            filter_dict['callback_filter_date'] = $('#date_filter_callback_campaign input').val()
            if ($('#ccb_search_by').val().trim()){
                filter_dict['column_name'] = $('#ccb_column_name').val()
                filter_dict['search_by'] = $('#ccb_search_by').val()
            }
            filter_dict['campaign_name'] = campaign_name
            getCampaignTotalCallback(filter_dict)
        }
    }
})

getabandonedcalls_vue = new Vue({
    el: '#getabandoned_vue',
    delimiters: ['${', '}'],
    data: {
        total_records:0,
        total_pages:0,
        page:1,
        has_next:false,
        has_prev:false,
        start_index:0,
        end_index:0,
    },
    methods:{
        changePage(value){
            $('#nextPage_number').val(value)
            getAbandonedCalls()
        }
    }

})


// this function is to get total abandoned calls for agent.
function getAbandonedCalls() {
    var filter_dict = {}
    filter_dict['page'] = $('#nextPage_number').val()
    filter_dict['paginate_by'] = $('#page_length').val()
    $.ajax({
        type: 'GET',
        headers: { "X-CSRFToken": csrf_token },
        url: '/api/get-totalabandonedcalls/',
        cache: false,
        timeout: 5000,
        data:filter_dict,
        success: function(data) {
            totalAbandonedCalls_table.clear()
            totalAbandonedCalls_table.rows.add(data['total_abandonedcalls']).draw(false);
            getabandonedcalls_vue.total_records = data['total_records']
            getabandonedcalls_vue.total_pages = data['total_pages']
            getabandonedcalls_vue.page = data['page']
            getabandonedcalls_vue.has_next = data['has_next']
            getabandonedcalls_vue.has_prev = data['has_prev']
            getabandonedcalls_vue.start_index = data['start_index']
            getabandonedcalls_vue.end_index = data['end_index']
        }
    })
}
getcampaignabandonedcalls_vue = new Vue({
    el: '#getcampaignabandonedcalls_vue',
    delimiters: ['${', '}'],
    data: {
        total_records:0,
        total_pages:0,
        page:1,
        has_next:false,
        has_prev:false,
        start_index:0,
        end_index:0,
    },
    methods:{
        changePage(value){
            var filter_dict = {}
            $('#nextPage_number').val(value)
            getCampaignAbandonedcalls(campaign_name)
        }
    }

})
// this function is to get total abandoned calls of current login campaign
function getCampaignAbandonedcalls(campaign='') {
    filter_dict = {'campaign_name':campaign}
    filter_dict['page'] = $('#nextPage_number').val()
    filter_dict['paginate_by'] = $('#page_length').val()
    $.ajax({
        type: 'post',
        headers: { "X-CSRFToken": csrf_token },
        url: '/api/get-campaignabandonedcalls/',
        cache: false,
        timeout: 5000,
        data:filter_dict,
        success: function(data) {
            campaignAbandonedcalls_table.clear();
            campaignAbandonedcalls_table.rows.add(data['campaign_abandonedcalls']).draw(false);
            getcampaignabandonedcalls_vue.total_records = data['total_records']
            getcampaignabandonedcalls_vue.total_pages = data['total_pages']
            getcampaignabandonedcalls_vue.page = data['page']
            getcampaignabandonedcalls_vue.has_next = data['has_next']
            getcampaignabandonedcalls_vue.has_prev = data['has_prev']
            getcampaignabandonedcalls_vue.start_index = data['start_index']
            getcampaignabandonedcalls_vue.end_index = data['end_index']
        }
    })
}

callperday_vue = new Vue({
    el: '#callperday_vue',
    delimiters: ['${', '}'],
    data: {
        total_records:0,
        total_pages:0,
        page:1,
        has_next:false,
        has_prev:false,
        start_index:0,
        end_index:0,
        
    },
    methods:{
        changePage(value){
            var filter_dict = {}
            $('#nextPage_number').val(value)
            dispo_name = $('#fetch_dispo_count_daily').find('.dispo_count_btn span').text()
            if(dispo_name == 'All Dispositions'){
                dispo_name = ''
            }
            if ($('#cpd_search_by').val().trim()){
                filter_dict['column_name'] = $('#cpd_column_name').val()
                filter_dict['search_by'] = $('#cpd_search_by').val()
            }
            filter_dict['disposition'] = dispo_name
            getTotalCallsPerDay(filter_dict)
        }
    }
})
//this function is to get total calls made today by agent 
function getTotalCallsPerDay(filter_dict={}){
    filter_dict['page'] = $('#nextPage_number').val()
    filter_dict['paginate_by'] = $('#page_length').val()
    $.ajax({
        type:'post',
        headers:{"X-CSRFToken": csrf_token },
        url:'/api/get-totalcallsperday/',
        data: filter_dict,
        success:function(data){
            totalCallPerDay_table.clear()
            totalCallPerDay_table.rows.add(data['total_callperday']).draw();
            callperday_vue.total_records = data['total_records']
            callperday_vue.total_pages = data['total_pages']
            callperday_vue.page = data['page']
            callperday_vue.has_next = data['has_next']
            callperday_vue.has_prev = data['has_prev']
            callperday_vue.start_index = data['start_index']
            callperday_vue.end_index = data['end_index']
        },
    })
} 

$("#kyc_filter_contact").click(function() {
    var filter_dict = {}
    filter_dict['column_name'] = $('#kyc_column_name').val()
    filter_dict['search_by'] = $('#kyc_search_by').val().trim()
    filter_dict['campaign_name'] =campaign_name 
    getKycDocuments(filter_dict)
})

function getKycDocuments(filter_dict={}){
    filter_dict['page'] = $('#nextPage_number').val()
    filter_dict['paginate_by'] = $('#page_length').val()
    $.ajax({
        type:'post',
        headers:{"X-CSRFToken": csrf_token },
        url:'/api/get-kycdocuments/',
        data:filter_dict,                            
        success:function(data){
            totalkycdocuments_table.clear()
            totalkycdocuments_table.rows.add(data['context']).draw();
            totalkycdocuments_table.columns.adjust().draw();
            kycdocument_vue.total_records = data['total_records']
            kycdocument_vue.total_pages = data['total_pages']
            kycdocument_vue.page = data['page']
            kycdocument_vue.has_next = data['has_next']
            kycdocument_vue.has_prev = data['has_prev']
            kycdocument_vue.start_index = data['start_index']
            kycdocument_vue.end_index = data['end_index']
        },
    })
}

kycdocument_vue = new Vue({
    el: '#kycdocument_vue',
    delimiters: ['${', '}'],
    data: {
        total_records:0,
        total_pages:0,
        page:1,
        has_next:false,
        has_prev:false,
        start_index:0,
        end_index:0,
        
    },
    methods:{
        changePage(value){
            var filter_dict = {}
            $('#nextPage_number').val(value)
            if ($('#kyc_search_by').val().trim()){
                filter_dict['column_name'] = $('#kyc_column_name').val()
                filter_dict['search_by'] = $('#kyc_search_by').val()
            }
            getKycDocuments(filter_dict)
        }
    }
})

$('#show-agent-kycdocument, #mb-show-agent-kycdocument').click(function(){
    hideHomeDiv()
    $('#contents-agent-kycdocument').removeClass('d-none')
    $('.breadcrumb').append('<li class="breadcrumb-item" aria-current="page"><a href="#" id="crm-home">'+
        '<i class="fas fa-home"></i></a></li>')
    $('#nextPage_number').val(1)
    $('#page_length').val('10');
    filter_dict = {}
    filter_dict['campaign_name'] = campaign_name
    getKycDocuments(filter_dict)
})

// to show active callback table
$('#show-callbacks-active, #mb-show-callbacks-active').click(function() {
    hideHomeDiv()

    $("#contents-active-callbacks").removeClass('d-none');
    $('.page-title').text(campaign_name + " Active Callbacks")
    $('.breadcrumb').append('<li class="breadcrumb-item" aria-current="page"><a href="#" id="crm-home">'
        +'<i class="fas fa-home"></i></a></li>')
    filter_dict = {}
    filter_dict['campaign_name']=campaign_name
    getActiveCallback(filter_dict);
    // ac_interval = setInterval("getActiveCallback(filter_dict)", 10000);
})

// to show reconfirmappointment table
$('#show-Reconfirmappointment-calls').click(function() {
    hideHomeDiv()

    $("#contents-reconfirm-calls").removeClass('d-none');
    $('.page-title').text(campaign_name + " Active Callbacks")
    $('.breadcrumb').append('<li class="breadcrumb-item" aria-current="page"><a href="#" id="crm-home">'
        +'<i class="fas fa-home"></i></a></li>')
    getReConfirmCallback(campaign_name);
    // reconfirm_interval = setInterval("getReConfirmCallback(campaign_name)", 10000);
})


// to show campaign callback table.
$('#show-callbacks-campaign').click(function() {
    hideHomeDiv()
    $("#contents-campaign-callbacks").removeClass('d-none');
    $('.page-title').text(campaign_name + " Calls");
    $('.breadcrumb').append('<li class="breadcrumb-item" aria-current="page"><a href="#" id="crm-home">'
        +'<i class="fas fa-home"></i></a></li>')
    filter_dict = {}
    filter_dict['campaign_name'] = campaign_name
    getCampaignTotalCallback(filter_dict)
    // campcallback_interval = setInterval("getCampaignTotalCallback(filter_dict)", 10000);
})
// to show campaign missed callback table.
$('#show-abandonedcalls-campaign').click(function() {
    hideHomeDiv()
    $('#contents-campain-abandonedcalls').removeClass('d-none');
    $('.page-title').text(campaign_name + " Abandoned Calls");
    $('.breadcrumb').append('<li class="breadcrumb-item" aria-current="page"><a href="#" id="crm-home">'+
        '<i class="fas fa-home"></i></a></li>')
    $('#nextPage_number').val('1')
    $('#page_length').val('10')
    getCampaignAbandonedcalls(campaign_name)
})
// to show total contacts agent dialed today 
$('#show-agent-totalcall-today, #mb-show-agent-totalcall-today').click(function(){
    hideHomeDiv()
    $('#fetch_dispo_count_daily').find('.dispo_count_btn span').text('All Dispositions')
    $('#fetch_dispo_count_daily').find('.dropdown-content').html('')
    $('#page_length').val('10');
    $('#paginate_by_per_day').val('10')
    $('#nextPage_number').val(1)
    if (agent_info_vue.isMobile()){
        $('#total_calls_perday_filter').clone().appendTo('#modal_filter_body').removeClass('d-none')
    }
    $('#contents-agent-totalcallsperday').removeClass('d-none')
    $('.breadcrumb').append('<li class="breadcrumb-item" aria-current="page"><a href="#" id="crm-home">'+
        '<i class="fas fa-home"></i></a></li>')
    getTotalCallsPerDay()
})
$('#paginate_by_per_day').change(function () {
    var filter_dict = {}
    $('#page_length').val($(this).val());
    dispo_name = $('#fetch_dispo_count_daily').find('.dispo_count_btn span').text()
    if(dispo_name == 'All Dispositions'){
        dispo_name = ''
    }
    if ($('#cpd_search_by').val().trim()){
        filter_dict['column_name'] = $('#cpd_column_name').val()
        filter_dict['search_by'] = $('#cpd_search_by').val()
    }
    filter_dict['disposition'] = dispo_name
    getTotalCallsPerDay(filter_dict)
});
callpermonth_vue = new Vue({
    el: '#callpermonth_vue',
    delimiters: ['${', '}'],
    data: {
        total_records:0,
        total_pages:0,
        page:1,
        has_next:false,
        has_prev:false,
        start_index:0,
        end_index:0,
    },
    methods:{
        changePage(value){
            var filter_dict = {}
            $('#nextPage_number').val(value)
            dispo_name = $('#fetch_dispo_count_monthly').find('.dispo_count_btn span').text()
            if(dispo_name == 'All Dispositions'){
                dispo_name = ''
            }
            if ($('#cpm_search_by').val().trim()){
                filter_dict['column_name'] = $('#cpm_column_name').val()
                filter_dict['search_by'] = $('#cpm_search_by').val()
            }
            filter_dict['cpm_filter_date'] = $('#date_filter_monthly input').val()
            filter_dict['disposition'] = dispo_name
            CallPerMonth(filter_dict)
        }
    }
})


assigned_call_pagination_vue = new Vue({
    el: '#assigned_call_pagination_vue',
    delimiters: ['${', '}'],
    data: {
        total_records:0,
        total_pages:0,
        page:1,
        has_next:false,
        has_prev:false,
        start_index:0,
        end_index:0,
    },
    methods:{
        changePage(value){
            $('#nextPage_number').val(value)
            var filter_dict = {}
            if ($('#ac_column_name').val() && $('#ac_search_by').val().trim()){
                filter_dict['column_name'] = $('#ac_column_name').val()
                filter_dict['search_by'] = $('#ac_search_by').val()
            }
            if($('#assigned_call_title').data('type') == 'campaign'){
                filter_dict['campaign'] = campaign_name
            }
            if ($('#assigned_call_title').data('status') == 'Dialed'){
                filter_dict['status'] = 'Dialed'
            } else if($('#assigned_call_title').data('status') == 'NotDialed') {
                filter_dict['status'] = 'NotDialed'
            }
            getAssignedCalls(filter_dict)
        }
    }
})

function CallPerMonth(filter_dict={}){
    filter_dict['page'] = $('#nextPage_number').val()
    filter_dict['paginate_by'] = $('#page_length').val()
    $.ajax({
        type:'post',
        headers:{ 'X-CSRFToken':csrf_token },
        url:'/api/get-totalcallsper-month/',
        data: filter_dict,
        success:function(data){
            callpermonth_table.clear().draw();
            callpermonth_table.rows.add(data['total_data']); // Add new data
            callpermonth_table.columns.adjust().draw(); // Redraw the DataTable
            callpermonth_vue.total_records = data['total_records']
            callpermonth_vue.total_pages = data['total_pages']
            callpermonth_vue.page = data['page']
            callpermonth_vue.has_next = data['has_next']
            callpermonth_vue.has_prev = data['has_prev']
            callpermonth_vue.start_index = data['start_index']
            callpermonth_vue.end_index = data['end_index']
            $('#processingIndicator').css( 'display', false ? 'block' : 'none' );
        }
    })    
}
function callsmonthly_table(table){
    callpermonth_table = $(table).DataTable({
           "destroy": true,
            "bPaginate": false,
            "searching": false,
            "processing": true,
            "info": false,
            scrollX:true,
            overflowX:'auto',
            columnDefs:[{
                "targets":'phone_number_field',
                render:function(data,type,row){
                    return "<a class='td-call-number'>"+data+"</a>"
                }
            },
                {
                "targets":'time_field_format',
                render:function(data){
                    return format_time(data)
                },
            }],
            createdRow: function(row, data){
                $(row).attr('data-tableName','totalCallsPerMonth_table')
            },
        })
}

$('#show-agent-totalcall-month, #mb-show-agent-totalcall-month').click(function(){
    hideHomeDiv()
    $('#fetch_dispo_count_monthly').find('.dispo_count_btn span').text('All Dispositions');
    $('#fetch_dispo_count_monthly').find('.dropdown-content').html('');
    $('#page_length').val('10');
    $('#paginate_by_per_month').val('10')
    $('#nextPage_number').val(1)
    $('#contents-agent-totalcallsper-month').removeClass('d-none')
    $('.breadcrumb').append('<li class="breadcrumb-item" aria-current="page"><a href="#" id="crm-home">'+
        '<i class="fas fa-home"></i></a></li>')
    // CallPerMonth(calls_url)
    var callsmonthly = $('#agent-monthly-calls')
    callsmonthly_table(callsmonthly)
    CallPerMonth()
})
$('#paginate_by_per_month').change(function () {
    var filter_dict = {}
    $('#page_length').val($(this).val());
    dispo_name = $('#fetch_dispo_count_monthly').find('.dispo_count_btn span').text()
    if(dispo_name == 'All Dispositions'){
        dispo_name = ''
    }
    if ($('#cpm_search_by').val().trim()){
        filter_dict['column_name'] = $('#cpm_column_name').val()
        filter_dict['search_by'] = $('#cpm_search_by').val()
    }
    filter_dict['cpm_filter_date'] = $('#date_filter_monthly input').val()
    filter_dict['disposition'] = dispo_name
    CallPerMonth(filter_dict)
});

$('.custom_paginate_by').change(function () {
    var filter_dict = {}
    $('#page_length').val($(this).val());
    if($(this).attr('id') == 'custom_camp_callbacks_page'){    
        filter_dict['callback_filter_date'] = $('#date_filter_callback_campaign input').val()
        filter_dict['campaign_name'] = campaign_name
        if ($('#ccb_search_by').val().trim()){
            filter_dict['column_name'] = $('#ccb_column_name').val()
            filter_dict['search_by'] = $('#ccb_search_by').val()
         }
        getCampaignTotalCallback(filter_dict)
    }else if($(this).attr('id') == 'custom_total_callbacks_page'){
        filter_dict['callback_filter_date'] = $('#date_filter_callback_total input').val()
         if ($('#tcb_search_by').val().trim()){
            filter_dict['column_name'] = $('#tcb_column_name').val()
            filter_dict['search_by'] = $('#tcb_search_by').val()
        }
        filter_dict['campaign_name'] = campaign_name
        getTotalCallback(filter_dict)
    }else if($(this).attr('id') == 'custom_active_callbacks_page'){
        filter_dict['callback_filter_date'] = $('#date_filter_active_callback_campaign input').val()
        filter_dict['campaign_name'] = campaign_name
        getActiveCallback(filter_dict)
    }

});

function getAssignedCalls(filter_dict={}){
    filter_dict['page'] = $('#nextPage_number').val();
    filter_dict['paginate_by'] = $('#page_length').val();
    $.ajax({
        type: 'post',
        headers: {"X-CSRFToken": csrf_token },
        url: '/api/get-total-assigned-calls/',
        data: filter_dict,
        success:function(data){
            list_of_assigned_contacts_table.clear().draw();
            list_of_assigned_contacts_table.rows.add(data['total_data']); // Add new data
            list_of_assigned_contacts_table.columns.adjust().draw(); // Redraw the DataTable
            assigned_call_pagination_vue.total_records = data['total_records']
            assigned_call_pagination_vue.total_pages = data['total_pages']
            assigned_call_pagination_vue.page = data['page']
            assigned_call_pagination_vue.has_next = data['has_next']
            assigned_call_pagination_vue.has_prev = data['has_prev']
            assigned_call_pagination_vue.start_index = data['start_index']
            assigned_call_pagination_vue.end_index = data['end_index']
            $('#processingIndicator').css( 'display', false ? 'block' : 'none' );
            if($('#assigned_call_title').data('status') == 'Dialed'){
                list_of_assigned_contacts_table.columns('.dialled_table_column').visible(true)
            } else {
                list_of_assigned_contacts_table.columns('.dialled_table_column').visible(false)
            }
        },
    })
}
$('.show-assigned-calls').click(function(){
    hideHomeDiv()
    $('#contents-agent-assigned-calls').removeClass('d-none')
    $('.breadcrumb').append('<li class="breadcrumb-item" aria-current="page"><a href="#" id="crm-home">'+
        '<i class="fas fa-home"></i></a></li>')
    $('#nextPage_number').val(1)
    $('#page_length').val('10');
    $('#paginate_by_asigned_calls').val('10')
    if ($(this).attr('id') == 'show-camp-assigned-notdialed-calls'){
        $('#assigned_call_title').text(`NotDialed Assigned Calls: ${campaign_name}`).data({'type':'campaign','status':'NotDialed'})
        getAssignedCalls({'campaign':campaign_name,'status':'NotDialed'})
    } else if ($(this).attr('id') == 'show-camp-assigned-dialed-calls') {
       $('#assigned_call_title').text(`Dialed Assigned Calls: ${campaign_name}`).data({'type':'campaign','status':'Dialed'})
       getAssignedCalls({'campaign':campaign_name,'status':'Dialed'})
    } else if ($(this).attr('id') == 'show-campaign-assigned-calls'){
        $('#assigned_call_title').text(`Campaign Assigned Calls: ${campaign_name}`).data({'type':'campaign','status':''})
        getAssignedCalls({'campaign':campaign_name})
    } else {
        $('#assigned_call_title').text('Total Assigned Calls').data({'type':'','status':''})
        getAssignedCalls()
    }
})
$('#paginate_by_asigned_calls').change(function () {
    $('#page_length').val($(this).val());
    var filter_dict = {}
    if ($('#ac_column_name').val() && $('#ac_search_by').val().trim()){
        filter_dict['column_name'] = $('#ac_column_name').val()
        filter_dict['search_by'] = $('#ac_search_by').val()
    }
    if($('#assigned_call_title').data('type') == 'campaign'){
        filter_dict['campaign'] = campaign_name
    }
    if ($('#assigned_call_title').data('status') == 'Dialed'){
        filter_dict['status'] = 'Dialed'
    } else if($('#assigned_call_title').data('status') == 'NotDialed') {
        filter_dict['status'] = 'NotDialed'
    }
    getAssignedCalls(filter_dict)
});

$(document).on('click', '.filter_contact', function(){
    $('#nextPage_number').val(1)
    var filter_dict = {}
    if ($(this).attr('id') == 'ac_filter_contact'){
        if ($('#ac_column_name').val() && $('#ac_search_by').val().trim()){
            filter_dict['column_name'] = $('#ac_column_name').val()
            filter_dict['search_by'] = $('#ac_search_by').val()
        }
        if($('#assigned_call_title').data('type') == 'campaign'){
            filter_dict['campaign'] = campaign_name
        }
        if ($('#assigned_call_title').data('status') == 'Dialed'){
            filter_dict['status'] = 'Dialed'
        } else if($('#assigned_call_title').data('status') == 'NotDialed') {
            filter_dict['status'] = 'NotDialed'
        }
        getAssignedCalls(filter_dict)
    } else if ($(this).attr('id') == 'lb_filter_contact') {
        var filter_dict = {'campaign':campaign_name}
        if ($('#lb_column_name').val() && $('#lb_search_by').val().trim()){
            filter_dict['column_name'] = $('#lb_column_name').val()
            filter_dict['search_by'] = $('#lb_search_by').val()
        }
        if($('#lead_bucket_title').data('type') == 'reverify_lead'){
            filter_dict['reverify_lead'] = 'reverify_lead'
        }
        getLeadBucket(filter_dict)
    } else if ($(this).attr('id') == 'cpd_filter_contact') {
        dispo_name = $('#fetch_dispo_count_daily').find('.dispo_count_btn span').text()
        if(dispo_name == 'All Dispositions'){
            dispo_name = ''
        }
        if ($('#cpd_search_by').val().trim()){
            filter_dict['column_name'] = $('#cpd_column_name').val()
            filter_dict['search_by'] = $('#cpd_search_by').val()
        }
        filter_dict['disposition'] = dispo_name
        getTotalCallsPerDay(filter_dict)
    } else if ($(this).attr('id') == 'cpm_filter_contact') {
        dispo_name = $('#fetch_dispo_count_monthly').find('.dispo_count_btn span').text()
        if(dispo_name == 'All Dispositions'){
            dispo_name = ''
        }
        if ($('#cpm_search_by').val().trim()){
            filter_dict['column_name'] = $('#cpm_column_name').val()
            filter_dict['search_by'] = $('#cpm_search_by').val()
        }
        filter_dict['cpm_filter_date'] = $('#date_filter_monthly input').val()
        filter_dict['disposition'] = dispo_name
        CallPerMonth(filter_dict)
    }else if($(this).attr('id') == 'callback_filter_contact') {
         filter_dict['callback_filter_date'] = $('#date_filter_callback_campaign input').val()
         if ($('#ccb_search_by').val().trim()){
            filter_dict['column_name'] = $('#ccb_column_name').val()
            filter_dict['search_by'] = $('#ccb_search_by').val()
         }
         filter_dict['campaign_name'] = campaign_name
         getCampaignTotalCallback(filter_dict)
    }else if($(this).attr('id') == 'total_callback_filter_contact'){
        filter_dict['callback_filter_date'] = $('#date_filter_callback_total input').val()
        if ($('#tcb_search_by').val().trim()){
            filter_dict['column_name'] = $('#tcb_column_name').val()
            filter_dict['search_by'] = $('#tcb_search_by').val()
        }
        filter_dict['campaign_name'] = campaign_name
        getTotalCallback(filter_dict)
    }else if($(this).attr('id') == 'active_callback_filter_contact'){
        filter_dict['callback_filter_date'] = $('#date_filter_active_callback_campaign input').val()
        filter_dict['campaign_name'] = campaign_name
        getActiveCallback(filter_dict)
    }
    if(agent_info_vue.isMobile()){
        $('.mb-filter-modal').modal('hide');
    }
})
$(document).on('shown.bs.dropdown', '.fetch_dispo_count', function () {
    if($(this).find('.dropdown-content').is(':empty')){
        $(this).find('.dropdown-menu .dropdown-loading').fadeIn('fast')
        if($(this).attr('id') == 'fetch_dispo_count_monthly'){
            fetch_type = 'CallsPerMonth'
        } else{
            fetch_type = 'CallsPerDay'
        }
        $.ajax({
            type:'get',
            headers:{"X-CSRFToken": csrf_token },
            url:'/api/get-agent-dispo-count/',
            data:{'fetch_type':fetch_type},
            success:function(data){
                $('.fetch_dispo_count').find('.dropdown-menu .dropdown-content').html('')
                $('.fetch_dispo_count').find('.dropdown-menu .dropdown-content').append(`<a class='dropdown-item px-3' data-name="All Dispositions">All Dispositions</a>`)
                $.each(data['dispo_data'],function(k,v){
                   $('.fetch_dispo_count').find('.dropdown-menu .dropdown-content').append(`<a class='dropdown-item px-3' data-name="${v['primary_dispo']}"><span class='badge badge-pill badge-info float-right ml-2 py-1'>${v['count']}</span>${v['primary_dispo']}</a>`)
                })
                $('.fetch_dispo_count').find('.dropdown-menu .dropdown-loading').fadeOut('fast')
            },
        })
    }
})

$(document).on('click','.fetch_dispo_count .dropdown-menu .dropdown-content a',function(){
    var filter_dict = {}
    var selText = $(this).data('name');
    $(this).parents('.fetch_dispo_count').find('.dispo_count_btn span').html(selText);
    if(selText == 'All Dispositions'){
        selText = ''
    }
    if($(this).parents('.fetch_dispo_count').attr('id') == 'fetch_dispo_count_monthly'){
        if ($('#cpm_search_by').val().trim()){
            filter_dict['column_name'] = $('#cpm_column_name').val()
            filter_dict['search_by'] = $('#cpm_search_by').val()
        }
        filter_dict['cpm_filter_date'] = $('#date_filter_monthly input').val()
        filter_dict['disposition'] = selText
        CallPerMonth(filter_dict)
    } else{
        if ($('#cpd_search_by').val().trim()){
            filter_dict['column_name'] = $('#cpd_column_name').val() 
            filter_dict['search_by'] = $('#cpd_search_by').val()
        }
        filter_dict['disposition'] = selText
        getTotalCallsPerDay(filter_dict)
    }
})

lead_bucket_pagination_vue = new Vue({
    el: '#lead_bucket_pagination_vue',
    delimiters: ['${', '}'],
    data: {
        total_records:0,
        total_pages:0,
        page:1,
        has_next:false,
        has_prev:false,
        start_index:0,
        end_index:0,
    },
    methods:{
        changePage(value){
            $('#nextPage_number').val(value)
            var filter_dict = {'campaign':campaign_name}
            if ($('#lb_column_name').val() && $('#lb_search_by').val().trim()){
                filter_dict['column_name'] = $('#lb_column_name').val()
                filter_dict['search_by'] = $('#lb_search_by').val()
            }
            if($('#lead_bucket_title').data('type') == 'reverify_lead'){
                filter_dict['reverify_lead'] = 'reverify_lead'
            }
            getLeadBucket(filter_dict)
        }
    }
})

function getLeadBucket(filter_dict={}){
    filter_dict['page'] = $('#nextPage_number').val();
    filter_dict['paginate_by'] = $('#page_length').val();
    $.ajax({
        type:'get',
        headers:{"X-CSRFToken": csrf_token },
        url:'/api/get-leadbucket-data/',
        data: filter_dict,
        success:function(data){
            lead_bucket_table.clear().draw();
            lead_bucket_table.rows.add(data['total_data']); // Add new data
            lead_bucket_table.columns.adjust().draw(); // Redraw the DataTable
            lead_bucket_pagination_vue.total_records = data['total_records']
            lead_bucket_pagination_vue.total_pages = data['total_pages']
            lead_bucket_pagination_vue.page = data['page']
            lead_bucket_pagination_vue.has_next = data['has_next']
            lead_bucket_pagination_vue.has_prev = data['has_prev']
            lead_bucket_pagination_vue.start_index = data['start_index']
            lead_bucket_pagination_vue.end_index = data['end_index']
            $('#processingIndicator').css( 'display', false ? 'block' : 'none' );

        },
    })
}
$('.show-lead-bucket').click(function(){
    hideHomeDiv()
    $('#nextPage_number').val(1)
    $('#page_length').val('10');
    $('#paginate_by_lead_bucket').val('10')
    $('#contents-lead-bucket').removeClass('d-none')
    $('.breadcrumb').append('<li class="breadcrumb-item" aria-current="page"><a href="#" id="crm-home"><i class="fas fa-home"></i></a></li>')
    if($(this).attr('id') == 'show-camp-requeue-lead-bucket'){
        $('#lead_bucket_title').text(`Requeue Lead Bucket : ${campaign_name}`).data('type','reverify_lead')
        getLeadBucket({'campaign':campaign_name,'reverify_lead':'reverify_lead'})
    } else {
        $('#lead_bucket_title').text(`Lead Bucket : ${campaign_name}`).data('type','')
        getLeadBucket({'campaign':campaign_name})
    }
})
$('#paginate_by_lead_bucket').change(function () {
    $('#page_length').val($(this).val());
    var filter_dict = {'campaign':campaign_name}
    if ($('#lb_column_name').val() && $('#lb_search_by').val().trim()){
        filter_dict['column_name'] = $('#lb_column_name').val()
        filter_dict['search_by'] = $('#lb_search_by').val()
    }
    if($('#lead_bucket_title').data('type') == 'reverify_lead'){
        filter_dict['reverify_lead'] = 'reverify_lead'
    }
    getLeadBucket(filter_dict)
});
function agent_activity_timer() {
    sessionStorage.setItem("wait_time", $("#wait_timer").text());
    sessionStorage.setItem("app_time", $("#app_timer").text());
    sessionStorage.setItem("dialer_time", $("#dialer_timer").text());
    sessionStorage.setItem("ring_time", $("#ring_timer").text());
    sessionStorage.setItem("speak_time", $("#speak_timer").text());
    sessionStorage.setItem("feedback_time", $("#feedback_timer").text());
    sessionStorage.setItem("preview_time", $("#preview_timer").text());
    sessionStorage.setItem("progressive_time", $("#progressive_timer").text());
    sessionStorage.setItem("predictive_time", $("#predictive_timer").text());
    sessionStorage.setItem("inbound_time", $("#inbound_timer").text());
    sessionStorage.setItem("blended_time", $("#blended_timer").text());    
    sessionStorage.setItem("break_time", $("#break_timer").text());
    sessionStorage.setItem("mute_time", $("#mute_timer").text());
    sessionStorage.setItem("hold_time", $("#hold_timer").text());
    sessionStorage.setItem("transfer_time", $("#transfer_timer").text());
    sessionStorage.setItem("idle_time", $("#idle_timer").text());
    sessionStorage.setItem("pause_progressive_time", $('#pause_progressive_timer').text());
    sessionStorage.setItem("callflow", callflow);
    sessionStorage.setItem("callmode", callmode);
}

setInterval(agent_activity_timer, 500);

function agent_time_format(given_time) {
    if (given_time) {
        time_brk = given_time.split(":")
        wait_hours = time_brk[0]
        wait_min = time_brk[1]
        wait_sec = time_brk[2]
    } else {
        wait_hours = wait_min = wait_sec = 0
    }
    return [wait_hours, wait_min, wait_sec]
}

function initiate_agent_timer(timer_id, given_time) {
    $(timer_id).countimer({
        autoStart: false,
        enableEvents: true,
        initHours: given_time[0],
        initMinutes: given_time[1],
        initSeconds: given_time[2],
    })
}
// This function is used to track agent breaks
function stopped_break_func() {
    $("#break_timer").countimer('stop')
    swal.close();
    $(".agent-break-status").addClass("d-none")
    $("#agent_breaks").val("")
    // $("#wait_timer").countimer('start')
}

function makeCallbackcall(cb_numeric, cb_campaign, cb_user, cb_contact_id) {
    swal({
        text: 'Preparing to make call',
        closeOnClickOutside: false,
        button: false,
        icon: 'info'
    })
    setTimeout(
        function() {
            if (cb_contact_id) {
                data_dict = {
                        'cb_numeric': cb_numeric,
                        'cb_campaign': cb_campaign,
                        'cb_contact_id':cb_contact_id
                    }
                if(cb_user) {
                    data_dict['cb_user'] = cb_user
                }
                $.ajax({
                    type: 'POST',
                    headers: { "X-CSRFToken": csrf_token },
                    url: '/api/make-callbackcall/',
                    data: data_dict,
                    success: function(data) {
                        $('#notification_modal').modal('hide')
                        swal.close();
                        is_callback = true;
                        callmode = "callback"
                        do_manual_call(cb_numeric,cb_contact_id)
                        $('#notification_modal').modal('hide')
                        $('#crm-home').trigger("click")
                        $('#dialer-tab').trigger("click")
                    },
                    error: function(data) {
                        swal({
                            text: data['responseJSON']['error'],
                            closeOnClickOutside: false,
                            icon: 'error',
                            button: {
                                text: "OK",
                                value: true,
                                visible: true,
                                className: "btn btn-primary"
                            },
                        }).then(
                            function() {
                                $('#notification_modal').modal('hide')
                            })
                    }
                })
            }
            else {
                is_abandoned_callback = true
                var data = {'dial_number':cb_numeric, 'campaign':cb_campaign}
                is_callback = true
                swal.close();
                do_manual_call(cb_numeric, data)
            }
        }, 3000)
}


// Making the reconfrim calls from the  reconfrm appointment tab 
function makereconfirmcall(numeric,campaign,user_id,contact_id){
    swal({
        text: 'Preparing to make call',
        closeOnClickOutside: false,
        button: false,
        icon: 'info'
    })
    setTimeout(
        function() {
            if (contact_id) {
                data_dict = {
                        're_numeric': numeric,
                        're_campaign': campaign,
                        're_contact_id':contact_id
                    }
                if(user_id) {
                    data_dict['re_user'] = user_id
                }
                $.ajax({
                    type: 'POST',
                    headers: { "X-CSRFToken": csrf_token },
                    url: '/api/make-reconfrimcall/',
                    data: data_dict,
                    success: function(data) {
                        $('#notification_modal').modal('hide')
                        swal.close();
                        callmode = "manual"
                        do_manual_call(numeric,contact_id)
                        $('#notification_modal').modal('hide')
                        $('#crm-home').trigger("click")
                        $('#dialer-tab').trigger("click")
                    },
                    error: function(data) {
                        swal({
                            text: data['responseJSON']['error'],
                            closeOnClickOutside: false,
                            icon: 'error',
                            button: {
                                text: "OK",
                                value: true,
                                visible: true,
                                className: "btn btn-primary"
                            },
                        }).then(
                            function() {
                                $('#notification_modal').modal('hide')
                            })
                    }
                })
            }
        }, 3000)
}




function makeAbandonedcall_Call(mc_numeric, caller_id) {
    swal({
        text: 'Preparing to make call',
        closeOnClickOutside: false,
        button: false,
        icon: 'info'
    })
    setTimeout(
        function() {
            $.ajax({
                type: 'POST',
                headers: { "X-CSRFToken": csrf_token },
                url: '/api/make-abandonedcall-call/',
                data: { 'numeric': mc_numeric, 'caller_id': caller_id },
                success: function(data) {
                    $('#notification_modal').modal('hide')
                    swal.close();
                    is_abandoned_call = true;
                    $('#MDPhonENumbeR').val(mc_numeric)
                    $('#manual-dial-now').trigger("click")
                    $('#notification_modal').modal('hide')
                    $('#dialer-tab').trigger("click")
                },
                error: function(data) {
                    swal({
                        text: data['responseJSON']['error'],
                        closeOnClickOutside: false,
                        icon: 'error',
                        button: {
                            text: "OK",
                            value: true,
                            visible: true,
                            className: "btn btn-primary"
                        },
                    }).then(
                        function() {
                            $('#notification_modal').modal('hide')
                        })
                }
            })
        }, 3000)
}

//call history related to logged in campaign
$("#call-history-tab").click(function() {
    var selected_campaign = $("#select_camp :selected").text()
    var dialed_no = $("#phone_number").text().trim()
    var unique_id = sessionStorage.getItem('unique_id','')
    if (dialed_no != "") {
        $.ajax({
            type: 'post',
            headers: { "X-CSRFToken": csrf_token },
            url: '/api/get-call-history/',
            data: { "dialed_no": dialed_no, "campaign": selected_campaign, 'unique_id':unique_id },
            success: function(data) {
                call_history_table.clear().draw();
                call_history_table.rows.add(data);
                call_history_table.columns.adjust().draw();
                call_history_table.columns.adjust().responsive.recalc();
            }
        })
    }
})

function reset_transfer_popup() {
    $('#transfer-type-select,#close-popup').prop("disabled", false);
    $('#hang-transfer-btn-div,#hang-merge-btn-div,#transfer-btn').addClass('d-none')
    $('#queue-radio,#internal-radio,#dial-number-text,#external-dial-btn').prop("disabled", false);
    $('#external-dial-btn').removeClass('d-none')
    $('#dial-number-text').val("")
}
// transfer call functionality.
isTransferableCall = true
disable_conference = false
$('#btnTransferCall').click(function() {
    if (add_three_way_conference_vue.three_way_list.length == 0){
        isTransferableCall = true
        disable_conference = false
        $("#transfer-type-select option[value='attr-transfer']").attr("disabled", false)
    }
    if (isTransferableCall == true && disable_conference== false) {
        $("#btnTransferCall").attr("disabled",false)
        var transfer_time=sessionStorage.getItem("transfer_time", "")
        if (transfer_time == '0:0:0' | transfer_time == null|transfer_time =='00:00:00') {
            $('#transfer_timer').countimer('start');
        }
        else {
            $('#transfer_timer').countimer('resume');
        }
        var dialed_uuid = session_details[extension]['dialed_uuid']
        if (dialed_uuid) {
            if ($('#btnTransferCall').val()=='false') {
                $('#btnParkCall').addClass('active');
                $('#btnTransferCall').val('true')
                var btn_transfer_call_status = true;
            }
        } 
        var data = {
            'dialed_uuid': dialed_uuid,
            'transfer_call_status': btn_transfer_call_status,
            'session_uuid':session_details[extension]['Unique-ID'],
            'sip_server': session_details[extension]['variable_sip_from_host'],
            'campaign_name': campaign_name,
            'conf_uuids': add_three_way_conference_vue.getAllConf_uuid()
        }
        function ajax_call() {
             return $.ajax({
                type: 'post',
                headers: { "X-CSRFToken": csrf_token },
                url: 'api/transfer_park_call/',
                data: data,
                success: function(data) {
                    if (isTransferableCall = true) {
                        isTransferableCall=false
                    }
                }, 
                error: function(err) {
                    $('#btnParkCall').removeClass("active")
                    $('#btnTransferCall').val('false')
                    var btn_transfer_call_status = false;
                }
            });
        }
    }
    if (disable_conference == false) {
        $.when( isTransferableCall ==false || ajax_call()).done(function(){
            $('#model-popup-div').modal('show');
            $('input[name="my-radio"]').prop('checked', false);
            $('#radio-btn-div,#external-sec-div,#queue-sec-div,#internal-sec-div').addClass('d-none');
            $('#external-radio,#internal-radio,#queue-radio,#agents-type-select,#transfer-type-select').prop("disabled", false);
            $('#internal-dial-btn,#external-dial-btn,#queue-dial-btn,#close-popup').prop("disabled", false);
            $('#external-dial-btn').removeClass('d-none')
            $('#queue-type-select,#dial-number-text,#agents-type-select').prop("disabled", false);
            $('#hang-merge-btn-div,#hang-transfer-btn-div').addClass('d-none')
            $('#transfer-type-select-div').removeClass('d-none');
            $('#transfer-type-select').val('')
        });
        if(isTransferableCall ==false) {
            $("#transfer-type-select option[value='attr-transfer']").attr("disabled", true)
        }
    }
});

$('#transfer-type-select').change(function() {
    $('#radio-btn-div').find('.col-4').addClass('d-none');
    if ($(this).val() == "") {
        $('#radio-btn-div,.sec-div').addClass('d-none');
        $("input[name=my-radio]:radio").prop("checked",false)
        $('#devp-alert').addClass('d-none');
        $("#external_div").addClass("d-none")
    }else if($(this).val() =='three-way-calling'){
        // $("#external_div").removeClass("d-none")
        $('.sec-div').addClass('d-none');
        $('#external-sec-div').removeClass('d-none');
        $('#internal-sec-div,#queue-sec-div').addClass('d-none');
        $('#devp-alert').addClass('d-none');
        $("#external-radio").prop("checked",true);
    }
    else {
        $('#radio-btn-div').removeClass('d-none');
        $("#internal_div, #queue_div").removeClass("d-none")
        $('.sec-div').addClass('d-none');
    }
});

//transfer call scop functionality
$("input[name=my-radio]:radio").click(function() {
    $('#dial-number-text,#agents-type-select,#queue-type-select').val('');
    if ($('input[name=my-radio]:checked').val() == "internal") {
        $('#internal-sec-div').removeClass('d-none');
        $('#external-sec-div,#queue-sec-div').addClass('d-none');
        $('#devp-alert').addClass('d-none');
        $.ajax({
            type: 'post',
            headers: { "X-CSRFToken": csrf_token },
            url: '/api/get-available-agent/',
            data: { 'campaign': campaign_name },
            success: function(data) {
                if ("available_agents" in data) {
                    var avail_agents = data["available_agents"]
                    $('#agents-type-select').find('option').not(":first").remove();
                    session_details[extension]['dialtimeout']=data['dialtimeout']
                    $.each(avail_agents, function(index, value) {
                        $('#agents-type-select').append($("<option></option>").attr("value",value["agent_extension"]).text(value["username"]));                         
                       /* $("#agents-type-select").append(new Option(value["username"], value["extension"], false, false))*/
                    });

                }
            }
        });        

    }else if ($('input[name=my-radio]:checked').val() == "external"){
        $('#external-sec-div').removeClass('d-none');
        $('#internal-sec-div,#queue-sec-div').addClass('d-none');
        $('#devp-alert').addClass('d-none');
    }else{
        $('#devp-alert').removeClass('d-none');
            setTimeout(function(){
            $('#devp-alert').addClass('d-none');
        },3000)         
        // $('#queue-sec-div').removeClass('d-none');
        $('#internal-sec-div,#external-sec-div').addClass('d-none');
    }
});

//tranfercall dial btn funcationality
var transfer_list = ['attr-transfer','three-way-calling']
$('#external-dial-btn,#internal-dial-btn,#queue-dial-btn').click(function() {
    if (transfer_list.includes($('#transfer-type-select').val()) == true) {
        if ($('input[name=my-radio]:checked').val() == "internal") {
            if($('#agents-type-select').val() != ""){
                $('#close-popup').prop("disabled",true)
                var transfer_agent_number = $('#agents-type-select').val()
                var data = {'transfer_type':'internal'}
                var ext_internal = sessionStorage.getItem("internal_transfer_no")
                if (ext_internal != null ) {
                    ext_internal+=", "+transfer_agent_number
                }
                else {
                    ext_internal = transfer_agent_number
                }
                sessionStorage.setItem("internal_transfer_no", ext_internal)
                data['transfer_to_agent_number']=transfer_agent_number
                data['transfer_from_agent_number']=extension
                data['transfer_from_agent_uuid']=session_details[extension]['Unique-ID']
                data['transfer_number']=session_details[extension]['dial_number']
                $('#queue-radio,#external-radio,#agents-type-select,#internal-dial-btn').prop("disabled", true);
                $('#transfer-type-select').prop("disabled", true);                  
                $('#hang-merge-btn-div,#transfer-btn').addClass('d-none')
                $('#hang-transfer-btn-div').removeClass('d-none')
                socket.emit('transfer',data);
                transfer_ringback_file= document.getElementById("Transfer-Ring-Back");
                transfer_notanswer_file= document.getElementById("Transfer-NotAnswer");
                transfer_notanswer_file.pause();
                transfer_ringback_file.play(); 
                transfer_audio_func=setTimeout(function(){
                    transfer_ringback_file.pause();
                    transfer_notanswer_file.play();
                    $('#queue-radio,#external-radio,#agents-type-select,#internal-dial-btn,#close-popup,#transfer-type-select').prop("disabled", false);
                    $('#hang-transfer-btn-div').addClass('d-none')
                },25000)
            }
            else{
                $('#transfer-error').removeClass('d-none').find('div').text("Please, select agent to make call")
                    setTimeout(function(){
                        $('#transfer-error').addClass('d-none').find('div').text("")
                    }, 3000)              
            }
        }else if ($('input[name=my-radio]:checked').val() == "queue"){
            if($('#queue-type-select').val() != ""){
                $('#close-popup').prop("disabled",true)
                var transfer_agent_number = $('#queue-type-select').val()
                var transfer_type = 'queue'
                $('#external-radio,#internal-radio,#queue-type-select,#queue-dial-btn').prop("disabled", true);
                $('#hang-transfer-btn-div').removeClass('d-none')
                $('#hang-merge-btn-div').addClass('d-none')
                $('#transfer-type-select').prop("disabled", true);                
            }                   
        }else {
            if($('#dial-number-text').val().length >= 9 && $('#dial-number-text').val().length <= 10){
                $('#close-popup').prop("disabled",true)
                $('#queue-radio,#internal-radio,#dial-number-text,#external-dial-btn').prop("disabled", true);
                $('#external-dial-btn').addClass('d-none')
                $('.tc-loader-div').show()
                $('#transfer-type-select').prop("disabled", true); 
                var transfer_agent_number = $('#dial-number-text').val()
                var transfer_type = 'external'                
                var ext_external = sessionStorage.getItem("external_transfer_no")
                if (ext_external != null ) {
                    ext_external+=", "+transfer_agent_number
                }else{
                    ext_external = transfer_agent_number
                }
                sessionStorage.setItem("external_transfer_no", ext_external)
                data={'transfer_to_agent_number':transfer_agent_number}
                data['caller_id']=sessionStorage.getItem("caller_id")
                data['transfer_type']=transfer_type
                data['campaign_name'] = campaign_name
                data['transfer_mode'] = $('#transfer-type-select').val()
                $.extend(data,session_details[extension])            
                $.ajax({
                    type:'post',
                    headers: {"X-CSRFToken": csrf_token},
                    url: '/api/transferagent/',
                    data: data,
                    success: function(data){
                        if('success' in data){
                            $("#call-loader").fadeOut("fast")
                            $('#hang-transfer-btn-div').removeClass('d-none')
                            $('#hang-merge-btn-div').addClass('d-none')
                            if ($('#transfer-type-select').val() == "attr-transfer") { 
                                session_details[extension]['transfer_uuid']=data['transfer_to_agent_uuid']
                            }else{
                                var temp_dict = {}
                                var confDict_index = 0
                                var confDict_exists = false
                                temp_dict[$('#dial-number-text').val()] = data['transfer_to_agent_uuid']
                                if(session_details[extension]['conference_list_uuid'] != undefined && session_details[extension]['conference_list_uuid'].length >= 1) {
                                    session_details[extension]['conference_list_uuid'].filter(function(conf_dict,index){
                                        if($('#dial-number-text').val() in conf_dict){
                                            confDict_exists = true
                                            confDict_index = index
                                        }
                                    })
                                    if(confDict_exists){
                                        session_details[extension]['conference_list_uuid'].splice(confDict_index,1)
                                        session_details[extension]['conference_list_uuid'].push(temp_dict)
                                    }else{
                                        session_details[extension]['conference_list_uuid'].push(temp_dict)
                                    }
                                }else{
                                    session_details[extension]['conference_list_uuid'] = [temp_dict]
                                }
                                session_details[extension]['conference_num_uuid'] = data['transfer_to_agent_uuid']
                            }           
                        }else{
                            $('#transfer-error').removeClass('d-none').find('div').text(data['error'])
                            setTimeout(function(){
                                $('#transfer-error').addClass('d-none').find('div').text("")
                            }, 3000)
                            $('#external-dial-btn').removeClass('d-none')
                            $('#queue-radio,#internal-radio,#dial-number-text,#external-dial-btn').prop("disabled",false);
                            $('#transfer-type-select').prop("disabled", false);
                        }
                        $('.tc-loader-div').hide()     
                    }
                }) 
            }else{
                $('#transfer-error').removeClass('d-none').find('div').text("Enter proper number to dial")
                setTimeout(function(){
                    $('#transfer-error').addClass('d-none').find('div').text("")
                }, 3000)
            }
        }
    }
});


// transfer call hangup btn funcationality
$('#attr-hangup-btn,#3way-hangup-btn').click(function() {
    if ($('input[name=my-radio]:checked').val() == "external"){
        if (session_details[extension]['transfer_uuid'] != "" || session_details[extension]['conference_num_uuid']!=""){
            data=session_details[extension]
            var activity_data = create_agent_activity_data()
            $.extend(data, activity_data)
            if ($('#transfer-type-select').val() == "attr-transfer"){
                data['event'] = 'Transfer Hangup'
            }else{
                data['event'] = 'Conference Hangup'
            }
            $.ajax({
                type:'post',
                headers: {"X-CSRFToken": csrf_token},
                url: '/agent/api/transfer_agentcall_hangup/',
                data: data,
                success: function(data){
                    if('success' in data){
                        if ($('#transfer-type-select').val() == "attr-transfer"){
                            session_details[extension]['transfer_uuid']=""
                        }else{
                            session_details[extension]['conference_num_uuid'] = ""
                        }
                        reset_transfer_popup()
                    }
                }
            });        
        }
    }else if ($('input[name=my-radio]:checked').val() == "internal"){
            var transfer_agent_number = $('#agents-type-select').val()
            var data = {'transfer_type':'internal'}
                data['transfer_to_agent_number']=transfer_agent_number
                data['transfer_from_agent_number']=extension
                data['transfer_from_agent_uuid']=session_details[extension]['Unique-ID']
                data['variable_sip_from_host'] =session_details[extension]['variable_sip_from_host']    
            socket.emit("tr_from_agent_hangup",data)
            transfer_notanswer_file.pause();
            transfer_ringback_file.pause();
            // transfer_busy_file.play();
            var activity_data = create_agent_activity_data(activity_data)
            activity_data['campaign_name'] = $("#select_camp :selected").text()
            $.extend(data,activity_data)
            $.ajax({
                type:'post',
                headers: {"X-CSRFToken": csrf_token},
                url: '/agent/api/transfer_agentcall_hangup/',
                data: data,
                success: function(data){
                    if('success' in data){
                        $('#transfer-type-select,#close-popup').prop("disabled", false);
                        $('#hang-transfer-btn-div,#hang-merge-btn-div,#transfer-btn').addClass('d-none')
                        $('#queue-radio,#external-radio,#agents-type-select,#internal-dial-btn').prop("disabled", false);
                        $('#agents-type-select').prop('selectedIndex', 0)
                    }
                }
            });
    }else{
        $('#external-radio,#internal-radio,#queue-type-select,#queue-dial-btn').prop("disabled", false);
    }   
});
conference_initiated = false
function three_way_calling_method() {
    data={...session_details[extension]}
    if ($('input[name=my-radio]:checked').val() == "internal"){
        clearInterval(transfer_audio_func)
    }
    var current_number = $("#dial-number-text").val()
    var event_data ={'event':'Merge Call', 'campaign_name':campaign_name}
    var agent_activity_data = create_agent_activity_data()
    data["conference_number"] = current_number
    // if (conference_initiated == true) {
    //     data["dialed_uuid"] = ""
    // }
    data["transfer_mode"] = $('#transfer-type-select').val()
    data['conference_uuids'] = add_three_way_conference_vue.getAllConf_uuid()
    $.extend(data, event_data, agent_activity_data)
    $.ajax({
        type:'post',
        headers: {"X-CSRFToken": csrf_token},
        url: '/agent/api/merge_call/',
        data: data,
        success: function(data){
            reset_transfer_popup()
            $("#model-popup-div").modal('hide')
            var conference_list_uuid = session_details[extension]['conference_list_uuid']
            $.each(conference_list_uuid, function(key, dict_data){
                if (current_number in dict_data) {
                    var conf_dict ={'conf_number':current_number}
                    conf_dict['conf_uuid'] = dict_data[current_number]
                    conf_dict['is_mute']=false
                    add_three_way_conference_vue.three_way_list.push(conf_dict)
                }
            });
            if (add_three_way_conference_vue.three_way_list.length == 4 ) {
                disable_conference = true
                $("#btnTransferCall").attr("disabled",true)
            }
            // conference_initiated = true
            $('#btnParkCall').removeClass("active")
            $('#btnTransferCall').val('false')
            isTransferableCall = true
        }
    });
}

function attr_transfer_method() {
    data=session_details[extension]
    if ($('input[name=my-radio]:checked').val() == "internal"){
        clearInterval(transfer_audio_func)
    }
    var event_data ={'event':'Transfered', 'campaign_name':campaign_name, 'transfer_mode':'attr-transfer',
    'contact_id':sessionStorage.getItem("contact_id")}
    var agent_activity_data = create_agent_activity_data()
    $.extend(data, event_data, agent_activity_data)
    $.ajax({
        type:'post',
        headers: {"X-CSRFToken": csrf_token},
        url: '/agent/api/transfer_call/',
        data: data,
        success: function(data){
            if('success' in data){
                $('#speak_timer, #ring_timer, #dialer_timer').countimer('stop');
                if ($("#fb_timer_div").hasClass("d-none")) {
                    $("#fb_timer_div").removeClass("d-none")
                    $("#fb_timer_div strong").text("WrapUp Time :")
                }
                agent_hangup = true
                hangup_time = new Date($.now());
                $("#dialer_timer, #speak_timer, #ring_timer").text("0:0:0")
                $('#dialer_timer').countimer('start');
                $("#call-loader").fadeOut("fast")
                if ($('input[name=my-radio]:checked').val() == "internal"){
                    var transfer_agent_number = $('#agents-type-select').val()
                    var data = {'transfer_type':'internal'}
                    data['transfer_to_agent_number']=transfer_agent_number
                    data['transfer_from_agent_number']=extension
                    data['transfer_number']=session_details[extension]['dial_number']
                    data['dialed_uuid'] = session_details[extension]['dialed_uuid']
                    data['contact_id'] = sessionStorage.getItem("contact_id")
                    data['previous_number'] = sessionStorage.getItem("previous_number")
                    socket.emit("dial_number_transfer_to_agent",data)
                }
            if ('error' in data) {
                showWarningToast(data['error'], 'top-center')
            }
            timer_on_hangup()
            $("#feedback_timer").countimer('start');
            $("#toggleMute").addClass("d-none")
            $('#model-popup-div').modal("toggle");
            $('#btnTransferCall').val('false')
            }else{
                showWarningToast(data['error'], 'top-center')
            }
        }
    });
}
//mssql connection setting method 
function set_mysqldatabase_details(incoming_number){
  data ={'incoming_number':incoming_number,'other_info':crm_field_vue.field_data['other_information']}
   $.ajax({
        type: 'post',
        headers: { "X-CSRFToken": csrf_token },
        url: '/api/set_mysql_contact/',
        data: data,
        success: function(data) {
           if('error' in data){
             showInfoToast("Connection Refused to get CRM Details", 'top-center')   
            }else{
                if('cust_info' in data){
                    $("#editable-form").trigger("reset")
                    showmysqlinfo(data['cust_info'])
                    if (!$('#list_li').hasClass("d-none")) {
                        $('#list_li').addClass("d-none")
                        $("#contact-info").trigger('click')
                    }
                }
            }
        }
    })  
}
//updating the mssql data into database
function update_mysqldatabase_details(mobile_no,feedback,primary_dispo){
    feedback['mobile_no'] = mobile_no;
    feedback['primary_dispo'] = primary_dispo
    $.ajax({
        type: 'post',
        headers: { "X-CSRFToken": csrf_token },
        url: '/api/sql_update_data/',
        data: feedback,
        success: function(data) {
            $("#editable-form").trigger("reset")
            if('error' in data){
                showInfoToast(data["error"], 'top-center')
            }
        },
    })
}
//upating the crm info to sbfc crm 
function update_crmapi_details(feedback, created_date,contact_id){
    $.ajax({
       type: 'post',
        headers: { "X-CSRFToken": csrf_token },
        url: '/api/push_crmdata_back/',
        data: {"customer_raw_data":feedback, "created_date":created_date,"contact_id":contact_id},
        success:function(data){
            if("error" in data){
                showInfoToast(data['error'],'top-center',4000)
            }else if('warning' in data){
                showWarningToast(data['warning'],'top-center',4000)
            }else{
               showInfoToast(data['success'],'top-center',4000)  
            }
        } 
    })
}
//email sending function 
// function update_crmapi_details_for_email_sending(feedback, created_date){
//      $.ajax({
//        type: 'post',
//         headers: { "X-CSRFToken": csrf_token },
//         url: '/api/appointment_email_api/',
//         data: {"customer_raw_data":feedback, "created_date":created_date},
//         success:function(data){
//             if("error" in data){
//                 showInfoToast(data['error'],'top-center')
//             }else{
//                showInfoToast(data['success'],'top-center')  
//             }
//         } 
//     }) 
// }
//transfer and merge btn funcationality
$('#transfer-btn').click(function() {
    if ($('#transfer-type-select').val() == 'attr-transfer') {
        $("#transfer_timer").countimer('stop')
        attr_transfer_method()
    }else{
        three_way_calling_method()

    }
});

$('#close-popup').click(function() {
    $("#transfer_timer").countimer("stop")
    var dialed_uuid = session_details[extension]['dialed_uuid']
    var btn_transfer_call_status = false
    var data = {
        'dialed_uuid': dialed_uuid,
        'transfer_call_status': btn_transfer_call_status,
        'session_uuid':session_details[extension]['Unique-ID'],
        'sip_server': session_details[extension]['variable_sip_from_host'],
        'campaign_name': campaign_name,
        'conf_uuids': add_three_way_conference_vue.getAllConf_uuid()
    }
    $.ajax({
        type: 'post',
        headers: { "X-CSRFToken": csrf_token },
        url: 'api/transfer_park_call/',
        data: data,
        success: function(data) {
            $('#btnParkCall').removeClass("active")
            $('#btnTransferCall').val('false')
            var btn_transfer_call_status = false;            
        },
        error: function(err) {
                $('#btnParkCall').addClass("active")
                $('#btnTransferCall').val('true')
                var btn_transfer_call_status = true;
        }
    });
});

$('#model-popup-div').on('hidden.bs.modal', function () {
    $('#btnParkCall').removeClass("active")
    $('#btnTransferCall').val('false')
});
//transfercall functionality is ends here

// resume and pause inbound call
var ibc_status = false
$('#ibc_btnResumePause').click(function() {
    btn_title = $(this).attr("title")
    if ((extension in session_details && Object.keys(session_details[extension]).length > 0) || btn_title !="Start Inbound"){
        if (btn_title == "Start Inbound") {
            if ($('#list_li').hasClass('d-none') == false) {
                $('#list_li').addClass('d-none')
                $('#list-info, #list-info-tab').removeClass('active show')
            }
            // agent_info_vue.state = 'Inbound Wait'
            set_agentstate('Inbound Wait')
            $(this).removeClass("btn-success").addClass("btn-danger")
            $(this).find('i').removeClass().addClass("fas fa-pause");
            $(this).attr("title", "Stop Inbound");
            $("#MDPhonENumbeR").text("")
            $("#MDPhonENumbeR, #manual-dial-now, #dialpad-toggle,#show-callbacks-campaign,#show-abandonedcalls-campaign, #show-callbacks-active,#show-followups-active, #show-followups-campaign,#flexy-agent-dialpad button").prop("disabled", true);
            $("#btnParkCall, #btnTransferCall").prop("disabled", false);
            ibc_status = true
            $("#btnLogMeOut").attr("disabled", true)
            $("#crm-agent-logout").attr("onclick", "")
            $("#agent_breaks").addClass("restrict-agent_break")
            $("#inbound_timer").countimer('start');
            $('#idle_timer').countimer('stop');
            $("#agent-callbacks-div button, #profile-tab, #show-callbacks-active, #show-callbacks-campaign, #show-abandonedcalls-campaign ,#show-campaign-lead-bucket, #show-campaign-assigned-calls, #show-camp-requeue-lead-bucket, #show-camp-assigned-dialed-calls, #show-camp-assigned-notdialed-calls,#show-Reconfirmappointment-calls").addClass("disabled")
            inbound_time  = sessionStorage.getItem("inbound_time"); 
            agent_timer_data = agent_time_format(inbound_time)
            initiate_agent_timer("#inbound_timer_display", agent_timer_data)
            $('#inbound_timer_div').removeClass('d-none')
            $('#inbound_timer_div strong').text('Inbound Call :')
            $('#inbound_timer_display').countimer('start')
        } else {
            // agent_info_vue.state = 'Idle'
            $("#agent_breaks").removeClass("restrict-agent_break")
            $(this).removeClass("btn-danger").addClass("btn-success")
            $(this).find('i').removeClass().addClass("fas fa-play");
            $(this).attr("title", "Start Inbound");
            $("#MDPhonENumbeR, #manual-dial-now, #dialpad-toggle,#show-callbacks-campaign,#show-abandonedcalls-campaign, #show-callbacks-active,#show-followups-active, #show-followups-campaign, #flexy-agent-dialpad button").prop("disabled", false);
            $("#btnParkCall, #btnTransferCall").prop("disabled", true);
            $("#livecall h3").removeClass().addClass("nolivecall").text("NO LIVE CALL").attr("title", "NO LIVE CALL");
            // agent_info_vue.state = 'Idle'
            set_agentstate('Idle')
            $("#agent-callbacks-div button, #profile-tab, #show-callbacks-active, #show-callbacks-campaign, #show-abandonedcalls-campaign, #show-campaign-lead-bucket, #show-campaign-assigned-calls, #show-camp-requeue-lead-bucket, #show-camp-assigned-dialed-calls, #show-camp-assigned-notdialed-calls,#show-Reconfirmappointment-calls").removeClass("disabled")
            ibc_status = false
            $("#btnLogMeOut").attr("disabled", false)
            $("#crm-agent-logout").attr("onclick", "")
            $("#inbound_timer").countimer('stop');
            $('#inbound_timer_div').addClass('d-none')
            $('#inbound_timer_display').text('00:00:00')
            $('#wait_timer').countimer('stop');
            // sessionStorage.setItem('outbound', '')
            $('#inbound_timer_display').countimer('stop')
        }
        inbound_data = {
            'uuid': session_details[extension]['Unique-ID'],
            'switch': session_details[extension]['variable_sip_from_host'],
            'extension': extension,
            'ibc_status': ibc_status,
            'campaign_name': campaign_name,
            'sip_error': sip_error
        }
        var agent_activity_data = create_agent_activity_data()
        agent_activity_data["inbound_time"] = sessionStorage.getItem("inbound_time")
        agent_activity_data["inbound_wait_time"] = sessionStorage.getItem("wait_time")
        $.extend(inbound_data, agent_activity_data)
        $.ajax({
            type: 'post',
            headers: { "X-CSRFToken": csrf_token },
            url: '/api/start-inbound/',
            data: inbound_data,
            success: function(data) {
                flush_agent_timer()
                $('#wait_timer').text('0:0:0')
                sessionStorage.setItem("wait_time", "0:0:0");
                $("#dialer_timer").countimer('start');
                if ("success" in data) {
                    if (ibc_status == true) {
                        $('#wait_timer').countimer('start');
                        $("#crm-agent-logout").attr("onclick", "")
                        $('#idle_timer').text("0:0:0")
                        sessionStorage.setItem("idle_time", "0:0:0");
                        initiate_agent_timer("#idle_timer", "0:0:0")

                    } else {
                        $("#inbound_timer").text('0:0:0')
                        $('#idle_timer').countimer('start')
                        sessionStorage.setItem("inbound_time", "0:0:0");
                        if (!$("#feedback_tab_link").hasClass("disabled")) {
                            $("#ibc_btnResumePause").prop("disabled", true)
                        }
                    }
                } else {
                    errorAlert('OOPS!!! Something Went Wrong',data["error"]);
                }
            }
        })
    }else{
        showWarningToast('Session details not avaliabe, Re-Login to dialler', 'top-center')
        $('#btnLogMeOut').click()
    }
});


function set_inbound_customer_detail(ic_number,contact_id,do_not_set=false){
    var dialed_uuid = session_details[extension]['dialed_uuid']
    var switch_ip = session_details[extension]["variable_sip_from_host"]
    sessionStorage.setItem('contact_id',contact_id)
    data={"ic_number":ic_number,"contact_id":contact_id,"dialed_uuid":dialed_uuid,"switch_ip":switch_ip, "callmode":callmode, "campaign_id":campaign_id,"third_party_data_fetch":sessionStorage.getItem("third_party_data_fetch","")}
    if (sessionStorage.getItem("prev_selected_contact_id","") != undefined) {
        data["prev_selected_contact_id"] = sessionStorage.getItem("prev_selected_contact_id","")
    }
    $.ajax({
        type: 'post',
        headers: { "X-CSRFToken": csrf_token },
        url: '/api/set_ibc_contact_id/',
        data: data,
        success: function(data) {
            if ('contact_info' in data && 'id' in data['contact_info']){
                sessionStorage.setItem("prev_selected_contact_id", data['contact_info']['id'])
            }
            $("#editable-form").trigger("reset")
            if('contact_info' in data && callmode != 'manual' && do_not_set==false && sessionStorage.getItem("third_party_data_fetch","") == "true"){    
                if(data['contact_info'].length > 0){
                    showmysqlinfo(data['contact_info'])
                    update_sql_database = true
                }
                else {
                    update_sql_database = false
                    $(".mobile_no_search_div").removeClass("d-none")
                }
            }
            else if(do_not_set==false) {
                showcustinfo(data['contact_info'])
            }

            if(callmode=='manual'){
                call_info_vue.callflow = 'Outbound'
            }else{
                call_info_vue.callflow = 'Inbound'
            }
            $("#contact-info").trigger('click')
            // if (!$('#list_li').hasClass("d-none")) {
            //     $('#list_li').addClass("d-none")
            //     // $("#back_to_contact").removeClass("d-none")

            // }
            $('#relation_tag_link,#feedback_tab_link').removeClass('disabled');
            if(sms_templates.send_sms_callrecieve && callmode !="manual"){ 
                setTimeout(sms_templates.sendSMS(campaign_id,sms_templates.selected_template,ic_number), 5000)
            }
            if(email_templates.email_type == '0' && callmode !="manual"){
                setTimeout(email_templates.sendEmail(), 5000)
            }
        }
    })
    thirdparty_module(data)
    // if ("thirdparty_api_status" in data && data["thirdparty_api_status"] == true){
    //     if("dap_status" in data && data["dap_status"] == true ){
    //         if('weburl' in data){
    //             $('#dap_details').removeClass('d-none')
    //             dap_details_data = JSON.parse(data['weburl'])
    //         }
    //     }else{
    //         if('weburl' in data){
    //             open_third_party_api(JSON.parse(data['weburl']))
    //         }
    //     }
    // }
}

$("#back_to_contact").click(function() {
    $('#list_li').removeClass("d-none")
    $("#list-info").trigger("click")
})

// resume and pause inbound call
var blndd_status = false
$('#blndd_btnResumePause').click(function() {
    btn_title = $(this).attr("title")
    if ((extension in session_details && Object.keys(session_details[extension]).length > 0) || btn_title !="Start Blended Mode"){
        if (btn_title == "Start Blended Mode") {
            if ($('#list_li').hasClass('d-none') == false) {
                $('#list_li').addClass('d-none')
                $('#list-info, #list-info-tab').removeClass('active show')
            }
            // agent_info_vue.state = 'Blended Wait'
            set_agentstate('Blended Wait')
            $(this).removeClass("btn-success").addClass("btn-danger")
            $(this).find('i').removeClass().addClass("fas fa-pause");
            $(this).attr("title", "Stop Blended Mode");
            $("#MDPhonENumbeR").text("")
            $("#MDPhonENumbeR, #manual-dial-now, #dialpad-toggle,#show-callbacks-campaign,#show-abandonedcalls-campaign, #show-callbacks-active,#show-followups-active, #show-followups-campaign,#flexy-agent-dialpad button").prop("disabled", true);
            $("#btnParkCall, #btnTransferCall").prop("disabled", false);
            blndd_status = true
            $("#btnLogMeOut").attr("disabled", true)
            $("#crm-agent-logout").attr("onclick", "")
            $("#agent_breaks").addClass("restrict-agent_break")
            $("#blended_timer").countimer('start');
            $('#idle_timer').countimer('stop');
            $("#agent-callbacks-div button, #profile-tab, #show-callbacks-active, #show-callbacks-campaign, #show-abandonedcalls-campaign, #show-campaign-lead-bucket, #show-campaign-assigned-calls, #show-camp-requeue-lead-bucket, #show-camp-assigned-dialed-calls, #show-camp-assigned-notdialed-calls,#show-Reconfirmappointment-calls").addClass("disabled")
            blended_time  = sessionStorage.getItem("blended_time"); 
            agent_timer_data = agent_time_format(blended_time)
            initiate_agent_timer("#blended_timer_display", agent_timer_data)
            $('#blended_timer_div').removeClass('d-none')
            $('#blended_timer_div strong').text('Blended Call :')
            $('#blended_timer_display').countimer('start')
        } else {
            // agent_info_vue.state = 'Idle'
            $("#agent_breaks").removeClass("restrict-agent_break")
            $(this).removeClass("btn-danger").addClass("btn-success")
            $(this).find('i').removeClass().addClass("fas fa-play");
            $(this).attr("title", "Start Blended Mode");
            $("#MDPhonENumbeR, #manual-dial-now, #dialpad-toggle,#show-callbacks-campaign,#show-abandonedcalls-campaign, #show-callbacks-active,#show-followups-active, #show-followups-campaign, #flexy-agent-dialpad button").prop("disabled", false);
            $("#btnParkCall, #btnTransferCall").prop("disabled", true);
            $("#livecall h3").removeClass().addClass("nolivecall").text("NO LIVE CALL").attr("title", "NO LIVE CALL");
            set_agentstate('Idle')
            $("#agent-callbacks-div button, #profile-tab, #show-callbacks-active, #show-callbacks-campaign, #show-abandonedcalls-campaign, #show-campaign-lead-bucket, #show-campaign-assigned-calls, #show-camp-requeue-lead-bucket, #show-camp-assigned-dialed-calls, #show-camp-assigned-notdialed-calls,#show-Reconfirmappointment-calls").removeClass("disabled")
            blndd_status = false
            $("#btnLogMeOut").attr("disabled", false)
            $("#crm-agent-logout").attr("onclick", "")
            $("#blended_timer").countimer('stop');
            $('#blended_timer_div').addClass('d-none')
            $('#blended_timer_display').text('00:00:00')
            $('#wait_timer').countimer('stop');
            $('#blended_timer_display').countimer('stop')
        }
        blended_data = {
            'uuid': session_details[extension]['Unique-ID'],
            'switch': session_details[extension]['variable_sip_from_host'],
            'extension': extension,
            'blndd_status': blndd_status,
            'campaign_name': campaign_name,
            'sip_error': sip_error
        }
        var agent_activity_data = create_agent_activity_data()
        agent_activity_data["blended_time"] = sessionStorage.getItem("blended_time")
        agent_activity_data["blended_wait_time"] = sessionStorage.getItem("wait_time")
        $.extend(blended_data, agent_activity_data)
        $.ajax({
            type: 'post',
            headers: { "X-CSRFToken": csrf_token },
            url: '/api/start-blended-mode/',
            data: blended_data,
            success: function(data) {
                flush_agent_timer()
                $('#wait_timer').text('0:0:0')
                sessionStorage.setItem("wait_time", "0:0:0");
                $("#dialer_timer").countimer('start');
                if ("success" in data) {
                    if (blndd_status == true) {
                        $('#wait_timer').countimer('start');
                        $("#crm-agent-logout").attr("onclick", "")
                        $('#idle_timer').text("0:0:0")
                        sessionStorage.setItem("idle_time", "0:0:0");
                        initiate_agent_timer("#idle_timer", "0:0:0")

                    } else {
                        $("#blended_timer").text('0:0:0')
                        $('#idle_timer').countimer('start')
                        sessionStorage.setItem("blended_time", "0:0:0");
                        if (!$("#feedback_tab_link").hasClass("disabled")) {
                            $("#blndd_btnResumePause").prop("disabled", true)
                        }
                    }
                } else {
                    errorAlert('OOPS!!! Something Went Wrong',data["error"]);
                }
            }
        })
    } else {
        showWarningToast('Session details not avaliabe, Re-Login to dialler', 'top-center')
        $('#btnLogMeOut').click()
    }
});
$("#search_label").on("keyup", function() {
    var value = this.value.toLowerCase().trim();
    if (value){
       $('.collapse-div .card-header > a').attr('data-toggle', 'collapse');
        $(".lista1 .lsname").filter(function() {
            $(this).find('label').css('background-color', '')
            var collapsible_div = $($(this).data('parent')).attr("id")
            $("#"+collapsible_div).addClass("show")
            $('a[href="#' + collapsible_div + '"]').attr("aria-expanded","true");
            var show = false
            $("#"+collapsible_div+" label").filter(function() {
                if($(this).text().trim().toLowerCase().includes(value) == true) {
                    $(this).css('background-color', 'yellow');
                    show = true
                }
                else {
                    $(this).css('background-color', '');
                }
            })
            if (show == false) {
                $("#"+collapsible_div).removeClass("show")
                $('a[href="#' + collapsible_div + '"]').attr("aria-expanded","false");
            }
        })

    }
    else {
       $(".lista1 .lsname").find('label').css('background-color', '')
        $('.sub-dispo-heading').attr('aria-expanded', false);
        $('.collapse-div').removeClass('show')
        $("#section_collaps_basicinfo").collapse('show');
    }
});

//Inbound mobile no search if called from unregistered no
incoming_call_list = []
inbound_all_cust_detail = []
$('#search_contact').click(function(event){
    if($("#mobile_no_search").val() !="") {
        $.ajax({
            type:'post',
            headers: {"X-CSRFToken": csrf_token},
            url: '/api/search-inbound-customer-detail/',
            data: {"search_value":$("#mobile_no_search").val(), "search_field": $("#field_search_by").val()},
            success: function(data){
                if (data['contact_info']) {
                    update_sql_database = true
                    if(data['contact_info'].length > 1){
                        $('#list_li').removeClass('d-none')
                        $('#contact-info, #contact-info-tab').removeClass('active show')
                        $('#list-info, #list-info-tab').addClass('active show')
                        $('.show_inbound_contact_div').removeClass('d-none')
                        list_of_inbound_contacts_table.clear().draw()
                        incoming_call_list.push(data['contact_info'])
                        inbound_all_cust_detail.push(data['customer_detail'])
                        list_of_inbound_contacts_table.rows.add(data['customer_detail']);
                        list_of_inbound_contacts_table.draw();
                        $("#contacts_list_div").addClass("d-none")
                    }
                    else {
                        showmysqlinfo(data['contact_info'])
                    }
                }
                else {
                    update_sql_database = false
                }
                // showcustinfo({"numeric":customer_number})
                $("#mobile_no_search").val("")
            }
        })
    }
    else {
        crm_field_vue.field_data = {}
        // call_info_vue.resetCallInfo()
    }
})
$(document).on('click','#dap_details', function(){
    if(dap_details_data != "" && dap_details_data != null && dap_details_data != undefined){
        open_third_party_api(dap_details_data)
    }
})

function open_third_party_api(data){
    var api_url =""
    if('API-in-Iframe' in data) {
        api_url = data["API-in-Iframe"]
    } else if ('API-in-Tab' in data) {
        api_url = data["API-in-Tab"]
    }
    if(Object.keys(data['parameters']).length > 0){
        if (api_url.indexOf('?') == -1){
            api_url = api_url + '?'
        } else {
            api_url = api_url + '&'
        }
    }
    var usr_fields = ['user_id','username','user_extension','campaign_id', 'campaign_name']
    $.each(Object.keys(data['parameters']),function(index,val){
        api_url = `${api_url}${val}=`
        if(usr_fields.indexOf(val) !== -1){
            switch(val){
                case 'user_id':
                    api_url = api_url + user_id
                    break
                case 'username':
                    api_url = api_url + user_name
                    break
                case 'user_extension':
                    api_url = api_url + extension
                    break
                case 'campaign_id':
                    api_url = api_url + campaign_id
                    break
                case 'campaign_name':
                    api_url = api_url + campaign_name
                    break
            }
        }
        var crm_field = data['parameters'][val].split(':')
        if(crm_field.length > 1){
            if(crm_field[0] in crm_field_vue.field_data && crm_field[1] in crm_field_vue.field_data[crm_field[0]]){
                if(dap_details_data != ""){
                     api_url = api_url + $.base64.encode(crm_field_vue.field_data[crm_field[0]][crm_field[1]])
                }else{
                    api_url = api_url + crm_field_vue.field_data[crm_field[0]][crm_field[1]]
                }
            }
        }
        if (Object.keys(data['parameters']).length-1 != index){
            api_url = api_url + '&'
        }
    })
    if('API-in-Iframe' in data){
        $('#iframe_tab_li').removeClass('d-none')
        $('#iframe_tab_li a').click()
        $('#contact-info,#contact-info-tab,#script-tab,#call-history-tab').removeClass('active show')
        $('#iframe_tab_link, #iframe-tab').addClass('active show')
        $('#iframe-tab').find('iframe').prop("src", api_url)
    }else if('API-in-Tab' in data){
        window.open(api_url, '_blank');
    }
}

function close_agent_sidebar(){
    if($(window).width()<768){
        if ($('#right-sidebar').hasClass('open')) {
            $('#right-sidebar').toggleClass('open')
            $('body').removeClass('agent-sidebar-hidden')
            $('#incoming_call_vue').animate({ 'right': '20px' }, 200)
        }
    }        
}

$(document).on('click', '#agent_to_admin_switchscreen',function(){
    window_reload_stop = true
    form_data = {
        'id':$(this).attr('id')
    }
    var url = '/dashboard/'
    var activity_data = create_agent_activity_data()
    $.extend(form_data, activity_data)
    $('.preloader').fadeIn('fast');
    $.ajax({
        type:'post',
        headers: {
                "X-CSRFToken": $("input[name='csrfmiddlewaretoken']").val()
            },
        url: '/agentscreen/',
        data:form_data,
        success:function(data){
            $('.preloader').fadeOut('fast');
            if(data['return_to_admin']){
                window.location = url
            }
        },
        error:function(data){
            $('.preloader').fadeOut('fast');
            console.log(data)
        }   
    })
})
// static pincode search option for filling the city and state in the crm fields 
$(document).on('change', '.pincode, .Pincode',function(event){
    var pincode = crm_field_vue.field_data['address_details']['pincode']
    if(agent_info_vue.state != 'Idle' && pincode.length >=6 ){
        pincodesearch(pincode) 
    }else{        
        crm_field_vue.field_data['address_details']['city'] = ""
        crm_field_vue.field_data['address_details']['state'] = "" 
    }
})

function pincodesearch(pincode){
 $.ajax({
        type:'get',
        headers: {
                "X-CSRFToken": $("input[name='csrfmiddlewaretoken']").val()
            },
        url:'/api/search-pincode/?search_by='+pincode,
        success:function(data){
            if(data['status'] == 'SERVICEABLE_FLAG'){
                Vue.set(crm_field_vue.field_data['address_details'],'city',  data['data'][0]['city'])
                Vue.set(crm_field_vue.field_data['address_details'],'state',data['data'][0]['state'])
            }else {
               swal({
                    title: 'Non-Serviceable Pincode',
                    text: 'Click OK to close this alert',
                    closeOnClickOutside:false,
                    button: {
                      text: "OK",
                      value: true,
                      visible: true,
                      className: "btn btn-primary"
                    }
                }) 
                Vue.set(crm_field_vue.field_data['address_details'],'city' ,"")
               Vue.set(crm_field_vue.field_data['address_details'],'state' ,"" )
            }
        }, 
        error: function(xhr, status, data) {
            console.log("Non-Serviceable Pincode")
                swal({
                    title: 'Non-Serviceable Pincode',
                    text: 'Click OK to close this alert',
                    closeOnClickOutside:false,
                    button: {
                      text: "OK",
                      value: true,
                      visible: true,
                      className: "btn btn-primary"
                    }
                  })
             Vue.set(crm_field_vue.field_data['address_details'],'city' ,"")
            Vue.set(crm_field_vue.field_data['address_details'],'state' ,"" )   
        } 
    })
}

// static scheme dropdown option for filling the roi,tenure,rebate in the crm fields 
$(document).on('change', '.scheme_type, .Scheme_type',function(event){
    if(agent_info_vue.state != 'Idle'){
        var scheme = $('.scheme_type option:selected').text()
         $.ajax({
            type:'get',
            headers: {
                    "X-CSRFToken": $("input[name='csrfmiddlewaretoken']").val()
                },
            url:'/api/scheme/?search_by='+scheme,
            success:function(data){
                if(data['status'] == "S"){
                    if(data['data'].length > 1){
                         Vue.set(crm_field_vue.field_data['loan_details'],'roi',data['data'][0]['EXTRA_FIELD1'])
                         Vue.set(crm_field_vue.field_data['loan_details'],'tenure',data['data'][0]['EXTRA_FIELD2'])
                         Vue.set(crm_field_vue.field_data['loan_details'],'rebate', data['data'][0]['EXTRA_FIELD3'])
                    }else{
                        Vue.set( crm_field_vue.field_data['loan_details'],'roi', data['data']['EXTRA_FIELD1'])
                         Vue.set(crm_field_vue.field_data['loan_details'],'tenure', data['data']['EXTRA_FIELD2'])
                         Vue.set(crm_field_vue.field_data['loan_details'],'rebate', data['data']['EXTRA_FIELD3'])
                    }
                     $('#scheme-error').addClass('d-none');
                }
                
            }, 
            error: function(xhr, status, data) {
                showInfoToast(data['data'],'top-center')
                Vue.set(crm_field_vue.field_data['loan_details'],'roi' ,"")
                Vue.set(crm_field_vue.field_data['loan_details'],'tenure' ,"" )
                Vue.set(crm_field_vue.field_data['loan_details'],'rebate' ,"" )
            } 
        })
    }
})

$('.mb-filter-btn').click(function(){
    $('#mb_filter_modal').modal('show')
})

$('#mb-profile-toggle a').click(function(){
    $('#left_sidebar').toggleClass('active')
})

var agent_appointment_vue = new Vue({
    el: '#agent_appoinment_vue',
    delimiters: ['${', '}'],
    data: {
        appointment_date: '',
        pincode: '',
        agent_details: [],
        selected_agents: [],
        is_fetching: false,
        is_error: false,
        book_error: '',
        is_book_error: false,
        current_booking_agent: '',
        current_unbooking_agent: '',
        btn_icons: {
            loading_icon: 'fas fa-sync-alt fa-spin',
            initial_icon: 'fas fa-check',
            unblock_icon: 'fas fa-unlock',
        }
    },
    methods: {
        bookAppointment(index, agent_id){
            var vm = this
            vm.current_booking_agent = agent_id
            data = {'appointment_date':vm.appointment_date, 'agent_id':agent_id}
            $.ajax({
                type: 'post',
                headers: { "X-CSRFToken": csrf_token },
                url: '/api/set_agent_schedule_appointment/',
                data: data,
                success: function(data) {
                    if ('RESPONSE' in data){
                        vm.agent_details[index]['status'] = data['RESPONSE']
                        if ('STATUS' in data['RESPONSE'] && data['RESPONSE']['STATUS'] == 'S'){
                            vm.book_error = ''
                            vm.is_book_error = false;
                            let selected_agents_dict = {"agent_cd":agent_id, "schedule_time_from":vm.appointment_date, "schedule_time_to":vm.appointment_date, "agent_name":vm.agent_details[index]['AGENT_NAME'],"agent_branch":vm.agent_details[index]['BRANCH'],"agent_role":vm.agent_details[index]['ROLENAME']}
                            vm.selected_agents.push(selected_agents_dict)
                        }
                    }
                },
                error: function(data) {
                    if ('error' in data['responseJSON']){
                        console.log(data['responseJSON']['error'])
                        vm.is_book_error = true
                        vm.book_error = data['responseJSON']['error']
                    }
                },
                complete: function () {
                    vm.current_booking_agent = ''
                }
            })
        },
        unbookAppointment(index, agent_id=''){
            let vm = this
            vm.current_unbooking_agent = agent_id
            let data = {'schedule_time':vm.appointment_date, 'agent_ids':[agent_id]}
            $.ajax({
                type: 'put',
                headers: { "X-CSRFToken": csrf_token },
                url: '/api/set_agent_schedule_unblock/',
                data: data,
                success: function(data) {
                    console.log(data)
                    if ('RESPONSE' in data){
                        vm.agent_details[index]['status'] = {}
                        vm.selected_agents = vm.selected_agents.filter(val=>val.agent_cd != agent_id)
                    }
                },
                error: function(){
                    if ('error' in data['responseJSON']){
                        console.log(data['responseJSON']['error'])
                    }
                },
                complete: function(){
                    vm.current_unbooking_agent = ''
                }
            })
        },
        udpateAppointment(){
            if (this.selected_agents.length >= 2){
                this.book_error = ''
                this.is_book_error = false;
                Vue.set(crm_field_vue.field_data['appointment_details'],'agent_details',[...this.selected_agents]);
                $('#appoinment_aval_modal').modal('hide')
            } else {
                this.book_error = 'Select Atleast 2 Appraisers/valuators...'
                this.is_book_error = true;
            }
        },
        resetFields(){
            this.appointment_date = '';
            this.pincode = '';
            this.agent_details = [];
            this.selected_agents = [];
            this.is_fetching = false;
            this.is_error = false;
            this.book_error = '';
            this.is_book_error = false;
            this.current_booking_agent = '';
        }
    }
})
$(document).on('click', '#check_appointment_availablity', function () {
    if (crm_field_vue.field_data['appointment_details']['schedule_time'] && crm_field_vue.field_data['address_details']['pincode']){
        $('#check_appointment_error').text('')
        $('#check_appointment_error').addClass('d-none')
        $('#appoinment_aval_modal').modal('show')
    } else if(!crm_field_vue.field_data['appointment_details']['schedule_time']){
        $('#check_appointment_error').text('Schedule Time is required')
        $('#check_appointment_error').removeClass('d-none')
    } else if (!crm_field_vue.field_data['address_details']['pincode']){
        $('#check_appointment_error').text('Pincode from address details is required')
        $('#check_appointment_error').removeClass('d-none')
    }
})

$(document).on('click','#showmaps',function(){
    if(crm_field_vue.field_data['address_details']['landmark'] && crm_field_vue.field_data['address_details']['pincode']){
        $('#mapmyindia_error').text('')
        $('#mapmyindia_error').addClass('d-none')
        $('#mapmyindia_modal').modal('show')
        set_address = document.getElementById('auto')
        $('#auto').val(crm_field_vue.field_data['address_details']['landmark']+","+crm_field_vue.field_data['address_details']['pincode'])
        $('#auto').trigger('click')
        new MapmyIndia.search($('#auto').val(),optional_config,callback);
    } else if(!(crm_field_vue.field_data['address_details']['landmark'])){
        $('#mapmyindia_error').text('LandMark is required')
        $('#mapmyindia_error').removeClass('d-none')
         setTimeout(function(){
            $('#mapmyindia_error').addClass('d-none');
        },3000)         
    } else if (!crm_field_vue.field_data['address_details']['pincode']){
        $('#mapmyindia_error').text('Pincode is required')
        $('#mapmyindia_error').removeClass('d-none')
         setTimeout(function(){
            $('#mapmyindia_error').addClass('d-none');
        },3000)  
    }

})
$('#appoinment_aval_modal').on('show.bs.modal', function (e) {
    agent_appointment_vue.is_fetching = true
    data = {"LATITUDE":"", "Location":""}
    data['DateTime'] = crm_field_vue.field_data['appointment_details']['schedule_time']
    data['Pincode'] = crm_field_vue.field_data['address_details']['pincode']
    data['LONGITUDE'] = crm_field_vue.field_data['other_details']['filler1']
    $.ajax({
        type: 'get',
        headers: { "X-CSRFToken": csrf_token },
        url: '/api/get_agent_availiblity_for_appointment/',
        data: {'data':JSON.stringify(data)},
        success: function(data) {
            console.log(data)
            if ('RESPONSE' in data && 'AGENT_DETAILS' in data['RESPONSE']){
                agent_appointment_vue.appointment_date = crm_field_vue.field_data['appointment_details']['schedule_time']
                agent_appointment_vue.pincode = crm_field_vue.field_data['address_details']['pincode']
                agent_appointment_vue.agent_details = data['RESPONSE']['AGENT_DETAILS'].sort(function(a,b){ if(a.AGENT_DISTANCE == null){a.AGENT_DISTANCE = 0;}return a.AGENT_DISTANCE - b.AGENT_DISTANCE});
            }
        },
        error: function(data) {
            if ('error' in data['responseJSON']){
                console.log(data['responseJSON']['error'])
                agent_appointment_vue.is_error = true
            }
        },
        complete: function (data) {
          agent_appointment_vue.is_fetching = false
        }
    })
})
$('#appoinment_aval_modal').on('hidden.bs.modal',function(e){
    agent_appointment_vue.resetFields()
})
$(document).on('click', '#unbook_appointment', function(){
    let book_agent_ids = []
    if ('appointment_details' in crm_field_vue.field_data && 'agent_details' in crm_field_vue.field_data['appointment_details'] && crm_field_vue.field_data['appointment_details']['agent_details']){
        $('#unbook_appointment').attr('disabled',true).find('i').attr('class','fas fa-sync-alt fa-spin');
        crm_field_vue.field_data['appointment_details']['agent_details'].filter(val => book_agent_ids.push(val['agent_cd']) )
        let data = {'schedule_time': crm_field_vue.field_data['appointment_details']['schedule_time']}
        data['agent_ids'] = book_agent_ids
        $.ajax({
            type: 'put',
            headers: { "X-CSRFToken": csrf_token },
            url: '/api/set_agent_schedule_unblock/',
            data: data,
            success: function(data) {
                console.log(data)
                if ('RESPONSE' in data && data['RESPONSE']['STATUS'] == 'S'){
                    Vue.set(crm_field_vue.field_data['appointment_details'],'agent_details',[]);
                }
            },
            error: function(){
                if ('error' in data['responseJSON']){
                    console.log(data['responseJSON']['error'])
                }
            },
            complete: function(){
                $('#unbook_appointment').attr('disabled',false).find('i').attr('class','fas fa-unlock');
            }
        })
    }
})

function set_agentstate(state){
    if(state){
        agent_info_vue.state = state
    }
    if(agent_info_vue.state == 'InCall'){
         if(!($('#AgentDialPad').is(':visible'))){
            $('#AgentDialPad').slideToggle('fast')
        }
        if($('#flexy-agent-dialpad button').prop('disabled')){
            $('#flexy-agent-dialpad button').prop('disabled',false)
        }
        $('#dialer-pad-clear,#dialer-pad-undo').addClass('d-none')
        $('#dialer-pad-ast,#dialer-pad-hash').removeClass('d-none')
    }else{
        if($('#AgentDialPad').is(':visible')){
            $('#AgentDialPad').slideToggle('fast')
        }
        $('#dialer-pad-clear,#dialer-pad-undo').removeClass('d-none')
        $('#dialer-pad-ast,#dialer-pad-hash').addClass('d-none')
    }
}

