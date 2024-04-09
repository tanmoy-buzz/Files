var login_agent_table, active_agent_table
var csrf_token = $("input[name='csrfmiddlewaretoken']").val()
    // var ld_interval;
function checkTime(i) {
    if (i < 10) {
        i = "0" + i;
    }
    return i;
}

function startTime(data) {
    var curr_date = new Date();
    var today = new Date(curr_date.valueOf() - data);
    var h = today.getUTCHours();
    var m = today.getUTCMinutes();
    var s = today.getUTCSeconds();
    // add a zero in front of numbers<10
    h = checkTime(h);
    m = checkTime(m);
    s = checkTime(s);
    var time = h + ":" + m + ":" + s;
    return time.toString()
}

function loginDuration(time) {
    return moment.utc(moment(new Date(), "HH:mm:ss").diff(moment(time, "HH:mm:ss"))).format("HH:mm:ss")
}

function get_updates() {
    $.ajax({
        type: 'GET',
        url: location.href,
        timeout: 5000,
        cache: false,
        success: function(data) {
            $('#dashboard-noti-count').text(data["noti_count"])
            $('#dashboard-download-count').text(data["down_count"])
            $('#live_agent_count').text(data['live_agent_count'])
            $('#login_count').text(data['login_count'])
            $('#agent_count').text(data['total_agent_c'])
            $('#dialer_count').text(data['dialer_count'])
            $('#break_count').text(data['break_count'])
            $('#logout_count').text(data['logout_count'])
            $('#oncall_count').text(data['oncall_count'])
            $('#inbound_count').text(data['inbound_count'])
            $('#preview_count').text(data['preview_count'])
            $('#progressive_count').text(data['progressive_count'])
            $('#predictive_count').text(data['predictive_count'])
            $('#manual_count').text(data['manual_count'])
            $('#a_camp_count').text(data['a_camp_count'])
            $('#lead_list_count').text(data['lead_list_count'])
            $('#al_list_count').text(data['al_list_count'])
            $('#ll_data_count').text(data['ll_data_count'])
            trunk_status_table.clear();
            trunk_status_table.rows.add(data['trunks_data']).draw(false).columns.adjust()
        }
    })
}

var live_data = new Vue({
    el: '#live_data', //element on whiche vue will intiaize
    delimiters: ['${', '}'], //to access vue object on html
    data: {
        table_head: [],
        selected_card: '',
        card_title: '',
        call_data: {},
        o_datatable: null,
        ct_row_data: {},
        ct_action_type: '',
        ct_actions: ['Listen', 'Whisper', 'Barge'],
        ct_remaning_action: [],
        ld_interval: null,
        timer_interval: null,
        pagination_data: {
            total_records: 0,
            total_pages: 0,
            page: 1,
            has_next: false,
            has_prev: false,
            start_index: 0,
            end_index: 0,
        },
        camp_table_page_num: null,
        camp_table_page_len: 10,
        camp_table_filter: null,
        // formData: {}
    },
    methods: {
        resetCampPagination(){
            this.pagination_data.total_records = 0
            this.pagination_data.total_pages = 0
            this.pagination_data.page = 1
            this.pagination_data.has_next = false
            this.pagination_data.has_prev = false
            this.pagination_data.start_index = 0
            this.pagination_data.end_index = 0
            this.camp_table_page_num = null
            this.camp_table_page_len = 10
            this.camp_table_filter = null
        },
        selectedCard(id) {
            let vm = this;
            vm.resetCampPagination()
            if (vm.selected_card === id) {
                $('#table_div').slideUp('slow', function() {
                    active_agent_table.clear().draw();
                    login_agent_table.clear().draw();
                    campaign_table.clear().draw();
                });
                vm.selected_card = ''
                clearInterval(vm.ld_interval);
                clearInterval(vm.timer_interval);
            } else {
                $('#ls_agent_table, #ls_campaign_table, #ls_call_table')
                    .parents('div.dataTables_wrapper')
                    .addClass('d-none')
                if (id === 'active_agent') {
                    $('#ls_call_table').parents('div.dataTables_wrapper').removeClass('d-none')
                    vm.card_title = 'Agents'
                    clearInterval(vm.ld_interval)
                    vm.getActiveAgentData()
                    // vm.ld_interval = setInterval(() => {
                    //     vm.getActiveAgentData()
                    // }, 5000);
                } else if (id === 'login_agent') {
                    $('#ls_agent_table').parents('div.dataTables_wrapper').removeClass('d-none')
                    vm.card_title = 'Login Agents'
                    clearInterval(vm.ld_interval)
                    login_agent_table.processing(true)
                    vm.getAgentData()
                    vm.ld_interval = setInterval(() => {
                        vm.getAgentData()
                    }, 5000);
                } else if (id === 'campaign') {
                    $('#ls_campaign_table').parents('div.dataTables_wrapper').removeClass('d-none')
                    vm.card_title = 'Campaign'
                    clearInterval(vm.ld_interval)
                    campaign_table.processing(true)
                    vm.camp_table_page_num = 1
                    // vm.getCampaignData(vm.camp_table_page_num)
                    vm.ld_interval = setInterval(() => {
                        vm.getCampaignData(vm.camp_table_page_num, vm.camp_table_page_len, vm.camp_table_filter) // user paging is not reset on reload
                    }, 15000);
                }
                vm.selected_card = id;
                $('#table_div').slideDown('slow');
            }
        },
        getAgentData() {
            let vm = this;
            $.ajax({
                type: 'GET',
                url: '/api/get-loginAgent-data/',
                success: function(data) {
                    login_agent_table.clear();
                    login_agent_table.rows.add(data['la_data']).draw(false).columns.adjust()
                },
                complete: function(){
                    login_agent_table.processing(false)
                }
            })
        },
        getActiveAgentData() {
            active_agent_table.processing(true)
            let vm = this;
            $.ajax({
                type: 'GET',
                url: '/api/get-activeAgent-data/',
                success: function(data) {
                    active_agent_table.clear();
                    active_agent_table.rows.add(data['active_agent_data']).columns.adjust().draw(false)
                },
                complete: function(){
                    active_agent_table.processing(false)
                }
            })
        },
        filterCampTable(){
            if (this.camp_table_filter != null) {
                campaign_table.processing(true)
                this.getCampaignData(this.camp_table_page_num, this.camp_table_page_len, this.camp_table_filter)
            }
        },
        getCampaignData(page=1, page_len=10, campaign=null) {
            let vm = this;
            $.ajax({
                type: 'GET',
                url: '/api/get-activeCampaign-data/',
                data: {'page':page, 'paginate_by': page_len, 'campaign': campaign},
                success: function(data) {
                    campaign_table.clear();
                    campaign_table.rows.add(data['liveCamp_data']).columns.adjust().draw(false)
                    vm.pagination_data = data['pagination_data']
                },
                complete: function(){
                    campaign_table.processing(false)
                }
            })
        }
    },
    beforeCreate() {
        $('#ls_agent_table, #ls_campaign_table, #ls_call_table').parents('div.dataTables_wrapper').addClass('d-none')
    },
    updated() {
        this.$nextTick(function() {})
    },
    watch: {
        call_data: function(val) {
            if (!(this.ct_row_data['extension'] in val)) {
                if (isModelshow) {
                    $('#eavesdrop_dissconnect').trigger('click');
                }
                // ct_remaning_action = []
                // $("#live_call_model").modal('hide')
            }
            let callData = []
            $.each(val, function(index, value) {
                value['extension'] = index
                callData.push(value);
            });
            active_agent_table.clear();
            active_agent_table.rows.add(callData).draw(false)

        },
        ct_action_type: function(val) {
            let vm = this;
            vm.ct_remaning_action = []
            $.each(vm.ct_actions, function(key, value) {
                if (value != val) {
                    vm.ct_remaning_action.push(value)
                }
            })
        },
        camp_table_page_num(value){
            if (value) {
                campaign_table.processing(true)
                this.getCampaignData(value, this.camp_table_page_len, this.camp_table_filter)
            }
        },
        camp_table_page_len(value){
            if (value) {
                campaign_table.processing(true)
                this.getCampaignData(this.camp_table_page_num, value, this.camp_table_filter)
            }
        }
    }
})

$(document).ready(function() {
    // live screen login agent detail table 
    login_agent_table = $('#ls_agent_table').DataTable({
        scrollX:true,
        overflowX:'auto',
        processing: true,
        language: {
            processing: '<i class="fa fa-spinner fa-spin fa-3x fa-fw"></i><span class="sr-only">Loading...</span> '
        },
        columnDefs: [{
            "targets":'_all',
            "defaultContent": '',
        },
        {
            "targets": "extension",
            "visible": false,
        },
        {
            "targets": "role_name",
            "visible": false,
        },
        {
            "targets": "status_col",
            render: function(data) {
                if(data=='Ready'){
                    return `<h4 class='badge badge-success badge-pill font-weight-bold py-1 mb-0'>${data}</h4>`;
                } else if (data=="NotReady"){
                    return `<h4 class='badge badge-danger badge-pill font-weight-bold py-1 mb-0'>${data}</h4>`;
                } else {
                    return `<h4 class='badge badge-primary badge-pill font-weight-bold py-1 mb-0'>${data}</h4>`;
                }
            }
        }, {
            "targets": "state_col",
            render: function(data) {
                if($.inArray(data, ['Progressive Dialling', "Preview Dialling", "Predictive Wait", "Inbound Wait", "Idle"]) != -1){
                    return `<h4 class='badge badge-warning badge-pill font-weight-bold py-1 mb-0'>${data}</h4>`;
                } else if (data=="onBreak"){
                    return `<h4 class='badge badge-dark badge-pill font-weight-bold py-1 mb-0'>${data}</h4>`;
                } else if (data=="Feedback") {
                    return `<h4 class='badge badge-primary badge-pill font-weight-bold py-1 mb-0'>${data}</h4>`;
                } else {
                    return `<h4 class='badge badge-success badge-pill font-weight-bold py-1 mb-0'>${data}</h4>`
                }
            }
        }, {
            "targets": "duration-col",
            render: function(data) {
                if (data) {
                    return data;
                } else {
                    return ""
                }
            },
            "searchable": false,
            "orderable": false,
            "width": "1%",
        }, {
            "targets": "login-time-col",
            render: function(data) {
                if(data){
                    return data.substring(0, 5)
                }
                return '';
            }
        },{
            "targets": "action-col",
            render: function(data, type, row){
                render_string = ''
                if(data == 'InCall'){
                    render_string = render_string + `<div class="d-inline oct_button"><button id="listen-btn" class="btn btn-link text-primary btn-rounded p-0 mr-1" title="Listen"><i class="fas fa-headphones-alt"></i></button> <button id="whisper-btn" class="btn btn-link text-success btn-rounded p-0 mr-1" title="Whisper"><i class="fas fa-headset"></i></button> <button id="barge-btn" class="btn btn-link text-info btn-rounded p-0 mr-1" title="Barge"><i class="fas fa-users"></i></button></div> `
                } 
                if(row['username']!=user_name) {
                    render_string = render_string + `<button id="forceLogout-btn" class="btn btn-link text-danger btn-rounded forceLogout-btn p-0 mr-1" title="Force Logout" data-extension="${row['extension']}"><i class="fas fa-sign-out-alt"></i></button>`;
                }
                return render_string
            }
        },{
            "targets": ['duration-col', 'login-time-col','action-col'],
            "searchable": false,
            "orderable": false,
            "width" : "1%"
        }
        ],

    });

    login_agent_table.columns().every(function() {
      var that = this;

          $('input', this.footer()).on('keyup change', function() {
            if (that.search() !== this.value) {
              that
                .search(this.value)
                .draw();
            }
          });
      });

    // End of Agent Table 

    // live screen on call agent table
    active_agent_table = $('#ls_call_table').DataTable({
        scrollX:true,
        overflowX:'auto',
        processing: true,
        language: {
            processing: '<i class="fa fa-spinner fa-spin fa-3x fa-fw"></i><span class="sr-only">Loading...</span> '
        },
        "order": [[ 1, "asc" ]],
         columnDefs: [
         {
            "targets": "extension",
            "visible": false,
        },
        {
           "targets": "live_username",
            render: function(data) {
                return '<a class="name-el" onclick="showUserwiseLead(\''+data+'\')">'+data+'</a>'
            }

        },
        {
            "targets": "state_col",
            "orderable": false,
            render: function(data) {
                if(data == "Logout"){
                    return `<span class='state-dot' style='background-color: #FF5E6D;'></span>`
                } else if (data=="OnBreak"){
                    return `<span class='state-dot' style='background-color: #3a3f51;'></span>`;
                } else if($.inArray(data, ['Progressive Dialling', "Preview Dialling", "Predictive Wait", "Inbound Wait", "Idle", "Feedback"]) != -1) {
                    return `<span class='state-dot' style='background-color: #F5A623;'></span>`
                } else {
                    return `<span class='state-dot' style='background-color: #04B76B;'></span>`
                }
            }
        },
        {
            "targets": "action-col",
            "orderable": false,
            render: function(data, type, row){
                if(data != 'Logout' && row['username']!=user_name){
                   return `<button id="forceLogout-btn" class="btn btn-link text-danger btn-rounded forceLogout-btn p-0 mr-1" title="Force Logout" data-extension="${row['extension']}"><i class="fas fa-sign-out-alt"></i></button>`;
                } else {
                    return ''
                }
            }
        }]
    });


    active_agent_table.columns().every(function() {
      var that = this;

          $('input', this.footer()).on('keyup change', function() {
            if (that.search() !== this.value) {
              that
                .search(this.value)
                .draw();
            }
          });
      });

    //End of call table

    // live screen campaign table
    campaign_table = $('#ls_campaign_table').DataTable({
        bPaginate: false,
        searching: false,
        ordering: false,
        processing: true,
        info: false,
        language: {
            processing: '<i class="fa fa-spinner fa-spin fa-3x fa-fw"></i><span class="sr-only">Loading...</span> '
        },
        scrollX:true,
        overflowX:'auto',
        columnDefs: [{
            targets: [0],
            className: 'text-left',
            render: function(data) {
                return '<a class="name-el" onclick="showCampaignLead(\''+data+'\')">'+data+'</a>'
            }

        },
        {
            targets: '_all',
            className: "text-center"
        }]
    })

    Vue.component('campaign-table-pagination',{
        props: ['total_records', 'total_pages', 'page', 'has_next', 'has_prev', 'start_index', 'end_index'],
        template: `<div class="row pt-1">
                    <div class="col-md-5">
                        <div class="custome_pagination_info">
                            Showing {{start_index}} to {{end_index}} of {{total_records}} entries
                        </div>
                    </div>
                    <div class="col-md-7">
                        <ul class="pagination separated d-flex justify-content-end ">
                            <li :class="[has_prev=='true' ? 'page-item':'page-item disabled']">
                                <a class="page-link" @click="changePage(page-1)">Previous</a>
                            </li>
                            <li v-if="page-4 > 1" class="page-item"><a class="page-link" @click="changePage(page-5)">&hellip;</a></li>
                            <template v-for="n in total_pages">
                                <li v-if="n==page" class="page-item active">
                                    <a class="page-link">{{n}}</a>
                                </li>
                                <li v-else-if="n > page-3 && n < page+3">
                                    <a class="page-link" @click="changePage(n)">{{n}}</a>
                                </li>
                            </template>
                            <li v-if="total_pages > (page+4)" class="page-item"><a class="page-link" @click="changePage(page+5)">&hellip;</a></li>
                            <li :class="[has_next=='true' ? 'page-item':'page-item disabled']">
                                <a class="page-link" @click="changePage(page+1)">Next</a>
                            </li>
                        </ul>
                    </div>
                </div>`,
        methods:{
            changePage(value){
                this.$emit('set-page', value)
            }
        }
    })
    // campaign_table.columns().every(function() {
    //   var that = this;

    //       $('input', this.footer()).on('keyup change', function() {
    //         if (that.search() !== this.value) {
    //           that
    //             .search(this.value)
    //             .draw();
    //         }
    //       });
    //   });

    //End of campaign table
    trunk_status_table = $('#trunk_status_table').DataTable({
        scrollX:true,
        overflowX:'auto',
        searching: false,
        lengthChange: false,
        columnDefs: [{
            "targets": "action_btn",
            orderable: false,
            render: function(data) {
                return `<button class="btn btn-link btn-rounded reset_trunk_channels" data-trunk_id="${data}" title="Reset Channels count"><i class="fas fa-sync-alt"></i></button>`;
            }
        }]
    })

    $(document).on('click', '.reset_trunk_channels', function(){
        trunk_id = $(this).data('trunk_id')
        swal({
            title: 'Are you sure?',
            text: "It will reset channels count to 0 even if agents are on call",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#3f51b5',
            cancelButtonColor: '#ff4081',
            confirmButtonText: 'Great ',
            buttons: {
                cancel: {
                    text: "Cancel",
                    value: null,
                    visible: true,
                    className: "btn btn-danger",
                    closeModal: true,
                },
                confirm: {
                    text: "OK",
                    value: true,
                    visible: true,
                    className: "btn btn-primary",
                    closeModal: true
                }
            }
        }).then(
            function(confirm) {
                if (confirm) {
                    $.ajax({
                        type: 'post',
                        headers: { "X-CSRFToken": $("input[name='csrfmiddlewaretoken']").val() },
                        url: '/api/reset_trunk_channels_count/',
                        data: {'trunk_id':trunk_id},
                        success: function(data) {
                            console.log(data)
                        }
                    })
                }
        })
    })
    setInterval(function (){
        if(location.pathname.indexOf("dashboard")!=-1){
            get_updates();
        }
    },5000);
})

Vue.component('model', {
    template: '#model-template'
})
var isModelshow = false
$("#live_call_model").on('shown.bs.modal', function() {
    isModelshow = true
})

$(document).on('click', '.oct_button button', function() {
    if (jQuery.isEmptyObject(session_details)) {
        errorAlert("Session Error","You dont have active session, kindly active call session and try again")
    } else {
        live_data.ct_action_type = $(this).attr('title')
        if (!('bs.modal' in $("#live_call_model").data())) {
            live_data.ct_row_data = login_agent_table.row($(this).parents('tr')).data()
        } else {
            if ($("#live_call_model").data('bs.modal')._isShown == false) {
                live_data.ct_row_data = login_agent_table.row($(this).parents('tr')).data()
            }
        }
        $.ajax({
            type: 'post',
            headers: {
                "X-CSRFToken": $("input[name='csrfmiddlewaretoken']").val()
            },
            url: '/api/eavesdrop_activity/',
            data: {
                'title': live_data.ct_action_type,
                'extension': live_data.ct_row_data['extension'],
                'dialerSession_uuid': live_data.ct_row_data['dialerSession_uuid'],
                'Unique-ID': session_details[extension]['Unique-ID'],
                'switch': session_details[extension]['variable_sip_from_host'],
                'isModelshow': isModelshow
            },
            success: function(data) {
                $("#live_call_model").modal('show')
                if (data['title'] == 'dissconnect' && data['isModelshow'] == 'true') {
                    $("#live_call_model").modal('hide')
                    isModelshow = false
                    live_data.ct_row_data = {}
                    live_data.ct_action_type = ''
                    live_data.ct_remaning_action = []
                }
            }

        })
    }
})

// force logout button
$(document).on('click', '#forceLogout-btn', function() {
    data = {'role_name':''}
    extension = $(this).data('extension')
    confirmEmergencyLogout(extension, user_name, user_role, data["role_name"])
})


function LiveCampaignseries() {
    $.ajax({
        type: 'GET',
        url: location.href,
        success: function(data) {
            $.each(data['total_camp_call'], function(k, v) {
                live_chart.addSeries({
                    name: v['campaign']
                })
            })
        }
    })
}
