$.fn.datetimepicker.Constructor.Default.icons = {
    time: 'fas fa-clock',
    date: 'fas fa-calendar',
    up: 'fas fa-arrow-up',
    down: 'fas fa-arrow-down',
    previous: 'fas fa-chevron-left',
    next: 'fas fa-chevron-right',
    today: 'fas fa-calendar-check-o',
    clear: 'far fa-trash-alt',
    close: 'far fa-times'
}
Vue.filter('replace',function(value){
    if (!value) return ''
    value = value.toString()
    return value.replace(/ /g,"_");
});
Vue.filter('lowercase',function(value){
    if (!value) return ''
    value = value.toString()
    return value.toLowerCase();
});

Vue.filter('replace_undersquare',function(value){
    if (!value) return ''
    value = value.toString()
    return value.replace(/#|_/g, " ")
});
Vue.component('disposition-component',{
    template: '#sub_dispo_template',
    delimiters: ['${', '}'],
    props:['sub_dispo','dispo_data'],
    data: function(){
        return{
            selected_children :null,
            multi_selected_children:[],
            select_checkbox:false,
            select_radio:null,
            select_dropdown:"",
            select_multicheckbox:[],
            select_multiselect:[],
        }
    },
    methods:{
        itemsContains(val,list) {
            return list.indexOf(val) > -1
        },
        multiselectOptions: function(value){
            var option_list = []
            value.filter(val=> option_list.push(val.name))
            return option_list
        },
        selectChildren(value){
            var vm = this
            vm.selected_children = value
            vm.dispo_data = {}
            let selected_childDict = vm.sub_dispo.children.filter(child => child.name == value)
            if($.inArray(selected_childDict[0].type,["","dropdown","multifield"]) == -1){
                vm.dispo_data[value]=""
            }else{
                if(selected_childDict[0].children.length != 0){
                    vm.dispo_data[value] = {}
                    if(selected_childDict[0].type == "multifield"){
                        selected_childDict[0].children.filter(function(child,index){
                            if($.inArray(child.type,["","dropdown","multifield","checkbox"]) == -1){
                                vm.dispo_data[value][child.name] = ""
                            }else if(child.type == 'checkbox'){
                                vm.dispo_data[value][child.name] = false
                            }else{
                                vm.dispo_data[value][child.name] = {}
                            }
                        })
                    }
                }else{
                    vm.dispo_data = value
                }
            }
        },
        selectMultiChildren(value){
            var vm = this
            vm.multi_selected_children = value
            vm.dispo_data = {}
            vm.sub_dispo.children.filter(function(multi_child,index){
                if(jQuery.inArray(multi_child.name,value) != -1){
                    if($.inArray(multi_child.type,["","dropdown","multifield"]) == -1){
                        vm.dispo_data[multi_child.name]=""
                    }else{
                        if(multi_child.children.length != 0){
                            vm.dispo_data[multi_child.name] = {}
                            if(multi_child.type == "multifield"){
                                multi_child.children.filter(function(child,index){
                                    if($.inArray(child.type,["","dropdown","multifield","checkbox"]) == -1){
                                        vm.dispo_data[multi_child.name][child.name] = ""
                                    }else if(child.type == 'checkbox'){
                                        vm.dispo_data[multi_child.name][child.name] = false
                                    }else{
                                        vm.dispo_data[multi_child.name][child.name] = {}
                                    }
                                })
                            }
                        }else{
                            if(multi_child.type == 'multiselectcheckbox'){
                                vm.dispo_data[multi_child.name] = false
                            }else{
                                vm.dispo_data[multi_child.name] = {}
                            }
                        }
                    }
                }else{
                    if(multi_child.type == 'multiselectcheckbox'){
                        vm.dispo_data[multi_child.name] = false
                    }
                }
            })
        },
    },
    watch:{
        dispo_data:function(val){
            this.$emit('child-input',val)
        },
        select_checkbox(val){
            var vm=this
            vm.dispo_data = {}
            if(val){
                if(vm.sub_dispo.children.length !=0){
                    vm.selected_children = val
                    vm.dispo_data = {}
                    vm.sub_dispo.children.filter(function(child,index){
                        if($.inArray(child.type,["","dropdown","multifield","checkbox"]) == -1){
                            vm.dispo_data[child.name] = ""
                        }else if(child.type == 'checkbox'){
                            vm.dispo_data[child.name] = false
                        }else{
                            vm.dispo_data[child.name] = {}
                        }
                    })
                }else{
                    vm.dispo_data = val
                    vm.selected_children=null
                }
            }else{
                vm.dispo_data = val
                vm.selected_children=null
            }
        },
        select_radio(val){
            this.selectChildren(val)
        },
        select_dropdown(val){
            this.selectChildren(val)
        },
        select_multicheckbox(val){
            this.selectMultiChildren(val)
        },
        select_multiselect(val){
            this.selectMultiChildren(val)
        }
    }
})
Vue.component('primary-dispo-btn',{
    delimiters: ['${', '}'],
    props:['dispo_name','dispo_color'],
    template:'#primary_dispo_btn',
    data: function(){
        return {
            btn_style : 'color: '+this.dispo_color+'!important'
        }
    },
    methods:{
        dispo_hover:function(){
            this.btn_style = 'background: '+this.dispo_color+'!important'
        },
        dipo_leave:function(){
            this.btn_style = 'color: '+this.dispo_color+'!important'
        }
    },
    computed:function(){
        this.btn_style = 'color: '+this.dispo_color+'!important'
    }
})
var dispo_vue = new Vue({
    el: '#dispo_vue',           //element on whiche vue will intiaize
    delimiters: ['${', '}'],    //to access vue object on html
    data: {
        on_call_dispo   : false,
        dispo_schema    : {},
        selectedTag     : null,
        secondry_dispo  : {},
        selected_children:{},
        primaryDispo_key :'',
        selected_pd     : '',
        selected_sd     : '',
        dispo_data      :{},
        on_call_dispositions :{},
        not_on_call_dispostion: {},
        primaryDispo_type : 'dropdown',
        slideTransition : 'slide-left',
        static_dispo:false,
        showLeadUser    : false,
        lead_user       : [],
        last_lead_agent : [],
        assigned_lead_user : [],
        reconfirm_disp:false,
    },
    methods:{
        // to active selected primary dispostion button
        selectedClass(key){
            return {
                'active': this.selectedTag === key,
                '': !(this.selectedTag === key)
            }
        },
        // to split string of option tag in dropdown
        split_string: function(string_option){
            if ( string_option !== '') {
                return string_option.split(',')
            }
        },
        reset_dispoform(){
            this.slideTransition = 'slide-right'
            this.primaryDispo_key = '';
            this.primaryDispo_type = 'dropdown';
            this.selectedTag    = null;
            this.secondry_dispo ={};
            this.selected_pd    ='';
            this.selected_sd    ='';
            this.dispo_data     = {};
            this.selected_children={};
        },
        selectSubdispo(index){
            this.dispo_data = {}
            if (index){
                this.selected_children = this.secondry_dispo[index-1]
                if($.inArray(this.selected_children.type,["","dropdown","multifield","checkbox"]) == -1){
                    this.dispo_data[this.selected_children.name] = ""
                }else if(this.selected_children.type == 'checkbox'){
                    this.dispo_data[this.selected_children.name] = false
                }else{
                    this.dispo_data[this.selected_children.name] = {}
                }
            }
            else{
                this.selected_children = {}
            }
        },
        primaryDispo(value){
             var vm = this
            if(value){
                vm.slideTransition = 'slide-left'
                vm.selected_pd = ''
                vm.selected_sd = ''
                vm.selectedTag = value-1;
                vm.secondry_dispo = {};
                vm.dispo_data = {};
                vm.selected_children = {}
                vm.selected_pd = vm.dispo_schema[value-1].name
                let sec = vm.dispo_schema[value-1]
                vm.secondry_dispo = sec.dispos
                vm.primaryDispo_type = sec.dispo_type
                vm.showLeadUser = sec.updatelead
                vm.reconfirm_disp = sec.reconfirm
                if(agent_info_vue.state == 'Feedback'){
                    $('#submit_customer_info').attr('disabled',false)
                }
                if(sec.dispo_type == 'multifield'){
                    vm.secondry_dispo.filter(function(multi_child,index){
                        if($.inArray(multi_child.type,["","dropdown","multifield"]) == -1){
                            vm.dispo_data[multi_child.name]=""
                        }
                        else{
                            if(multi_child.children.length != 0){
                                vm.dispo_data[multi_child.name] = {}
                                if(multi_child.type == "multifield"){
                                    multi_child.children.filter(function(child,index){
                                        if($.inArray(child.type,["","dropdown","multifield","checkbox"]) == -1){
                                            vm.dispo_data[multi_child.name][child.name] = ""
                                        }else if(child.type == 'checkbox'){
                                            vm.dispo_data[multi_child.name][child.name] = false
                                        }else{
                                            vm.dispo_data[multi_child.name][child.name] = {}
                                        }
                                    })
                                }
                            }else{
                                if(multi_child.type == 'multiselectcheckbox'){
                                    vm.dispo_data[multi_child.name] = false
                                }else{
                                    vm.dispo_data[multi_child.name] = {}
                                }
                            }
                        }
                    })
                }
                if (sessionStorage.getItem("third_party_data_fetch","") == "true" && callflow == "inbound") {
                    vm.static_dispo = true
                }
                else {
                    vm.static_dispo=false
                }
            }
        }
    },
    watch:{
        // on change or selection of perimary disposition
        on_call_dispo:{
            handler(){
                if(this.on_call_dispo == true){
                    this.dispo_schema = this.on_call_dispositions
                }else{
                    this.dispo_schema = this.not_on_call_dispostion
                }
            }
        },
        secondry_dispo:{
            handler(){
                $('#extra-info-collaps').addClass('show')
                $('#extra-info-heading').find('h6').find('a').attr("aria-expanded",true)
            },
            deep: true
        },
        selected_sd:function(value){
            if (value){
                this.selected_children = this.secondry_dispo[value]
            }
            else{
                this.selected_children = {}
            }
        },
        // primaryDispo_key:function(value){
        //     var vm = this
        //     if(value){
        //         vm.selected_pd = ''
        //         vm.selected_sd = ''
        //         vm.selectedTag = value-1;
        //         vm.secondry_dispo = {};
        //         vm.dispo_data = {};
        //         vm.selected_children = {}
        //         vm.selected_pd = vm.dispo_schema[value-1].name
        //         let sec = vm.dispo_schema[value-1]
        //         vm.secondry_dispo = sec.dispos
        //         vm.primaryDispo_type = sec.dispo_type
        //         if(agent_info_vue.state == 'Feedback'){
        //             $('#submit_customer_info').attr('disabled',false)
        //         }
        //         if(sec.dispo_type == 'multifield'){
        //             vm.secondry_dispo.filter(function(multi_child,index){
        //                 if($.inArray(multi_child.type,["","dropdown","multifield"]) == -1){
        //                     vm.dispo_data[multi_child.name]=""
        //                 }
        //                 else{
        //                     if(multi_child.children.length != 0){
        //                         vm.dispo_data[multi_child.name] = {}
        //                         if(multi_child.type == "multifield"){
        //                             multi_child.children.filter(function(child,index){
        //                                 if($.inArray(child.type,["","dropdown","multifield","checkbox"]) == -1){
        //                                     vm.dispo_data[multi_child.name][child.name] = ""
        //                                 }else if(child.type == 'checkbox'){
        //                                     vm.dispo_data[multi_child.name][child.name] = false
        //                                 }else{
        //                                     vm.dispo_data[multi_child.name][child.name] = {}
        //                                 }
        //                             })
        //                         }
        //                     }else{
        //                         if(multi_child.type == 'multiselectcheckbox'){
        //                             vm.dispo_data[multi_child.name] = false
        //                         }else{
        //                             vm.dispo_data[multi_child.name] = {}
        //                         }
        //                     }
        //                 }
        //             })
        //         }
        //     }
        // }
    },
})
var hasDupsSimple = function(array, value) {
    for (var i = 0; i < array.length; i++) {
        if(array[i]['id']==value){
            return false
        }
    }
    return true
}

var crm_field_vue = new Vue({
    el: '#vue',
    delimiters: ['${', '}'],
    data:{
            field_schema:[],
            basic_field_data:{
                numeric:'',
                first_name:'',
                last_name:'',
                email:'',
                status:''
            },
            field_data:{},
            temp_data:{},
            edit_field:null,
            edit_basic_field:null,
            update_crm: false,
            created_date: null,
            required_fields:[],
            required_crm:false,
        // formData: {}
    },
    computed: {
        book_agents_name: function(){
            let agents_name = ''
            if('appointment_details' in this.field_data && 'agent_details' in this.field_data['appointment_details'] && this.field_data['appointment_details']['agent_details']){
                this.field_data['appointment_details']['agent_details'].filter(val=>agents_name += val['agent_name']+', ')
            }
            return agents_name
        }
    },
    methods:{
        col_span(span_val){
            return{
                'col-sm-12': span_val === "3",
                'col-sm-8' : span_val === "2",
                'col-sm-4' : span_val === "1",
            }
        },
        // to split string of option tag in dropdown
        split_string: function(string_option){
            if ( string_option !== '') {
                return string_option.split(',')
            }
        },
       
        // to sort section priority wise in custom crm fields
        ordered_section: function (schema) {
            return _.sortBy(schema, 'section_priority')
        },
        // to sort fields priority wise in custom crm fields
        ordered_field: function(schema){
            return _.sortBy(schema, 'priority')
        },
        editField(event, sec_name, index, editable,field_type){
            if (!editable) 
            return
            this.edit_field = sec_name + index
            this.update_crm = true
            this.$nextTick(() => {
                if ($.inArray(field_type,['datefield','datetimefield','timefield']) == -1){
                    this.$refs[sec_name][index].focus()
                } else {
                    $(this.$refs[sec_name][index].$el).find('input').focus()
                }
            })
        },
        editBasicField(field_name){
            this.edit_basic_field = field_name
            this.$nextTick(() => {
                this.$refs[field_name].focus()
            })
        },
        resetBasicField(){
            this.basic_field_data = {
                numeric:'',
                first_name:'',
                last_name:'',
                email:'',
                status:''
            }
        },
        resetExtraField(){
            this.field_data = {}
            this.created_date = null
        },
        isLetter(e, field_name){
            if (!['first_name','last_name','middle_name'].includes(field_name)) return true;
            let char = String.fromCharCode(e.keyCode);
            if(/^[A-Za-z]+$/.test(char)) return true;
            else e.preventDefault();
        }
    },
    watch: {
        temp_data : function(value){
            var vm = this
            vm.$nextTick(function () {
                crm_field_vue.field_data = JSON.parse(JSON.stringify(value))
            })
        },
        field_data:function(value){
            var vm = this
            if(Object.keys(vm.temp_data).length != 0 && Object.keys(value).length == 0){
                crm_field_vue.field_data = JSON.parse(JSON.stringify(vm.temp_data))
            }else if (Object.keys(vm.temp_data).length != 0){
                if($(Object.keys(vm.temp_data)).not(Object.keys(value)).length >0){
                    $.each($(Object.keys(vm.temp_data)).not(Object.keys(value)), function(index,sec_key){
                        value[sec_key] = {}
                        $.each(Object.keys(vm.temp_data[sec_key]) , function(index,field_key){
                            value[sec_key][field_key] = null;
                        })
                    })
                }
                if('appointment_details' in value){
                    if(!('schedule_time' in value['appointment_details'])){
                        vm.$set(vm.field_data['appointment_details'],'schedule_time',null)
                    }
                    if(!('type' in value['appointment_details'])){
                        vm.$set(vm.field_data['appointment_details'],'type','')
                    } 
                    // else {
                    //     // vm.field_data['appointment_details']['type'] = 'New';
                    // }
                    var crm_ref_no = ('crm_ref_no' in value['appointment_details'])?value['appointment_details']['crm_ref_no']:'';
                    if(!('crm_ref_no_old' in value['appointment_details'])){
                        vm.$set(vm.field_data['appointment_details'],'crm_ref_no_old',crm_ref_no)
                    }else{
                        vm.$set(vm.field_data['appointment_details'],'crm_ref_no_old',crm_ref_no)
                    }
                    if(!('agent_details' in value['appointment_details'])){
                        vm.$set(vm.field_data['appointment_details'],'agent_details',[])
                    }
                }
            }
        },
    }
});
var call_info_vue = new Vue({
    // el: '#call_statusinfo',
    delimiters: ['${', '}'],
    data:{
        numeric: null,
        alt_numeric: [],
        callflow:'Outbound',
        status: 'Dialed',
        show_call_info:false,
        new_alt_numeric:null,
        selected_alt_numeric:'',
        selected_alt_dict:{},
        dailed_numeric:'',
        primary_dial: false,
        alt_dial: false,
        show_alt_dial_btn : false,
        show_caret: false,
    },
    methods:{
        resetCallInfo(){
            this.numeric = null
            this.alt_numeric = []
            this.callflow ='Outbound'
            this.status = 'Dialed'
            this.show_call_info = false
            this.show_alt_dial_btn = false
            this.dailed_numeric='';
        },
        createAlternateDict(value){
            let vm = this
            vm.alt_numeric = []
            $.each(value, function(key,val){
                let temp_dict = {}
                temp_dict['alt_label'] = key
                temp_dict['alt_value'] = val
                vm.alt_numeric.push(temp_dict)
            })
        },
        alternateNameNumber(alt_num_dict){
            return alt_num_dict['alt_label'] + ' : ' + alt_num_dict['alt_value']
        },
        addAlternateNumber(index){
            let check_input = this.alt_numeric.filter(val=>val['alt_label'] == '' || val['alt_value'] == '')
            if (check_input.length >= 1) 
            return
            this.alt_numeric.push({'alt_label':'alt_num_'+(index+1),'alt_value':''})
        },
        removeAlternateNumber(index){
            this.alt_numeric.splice(index,1)
        },
        makeAlternateCall(dial_primary=false){
            if(agent_info_vue.state == 'Feedback'){
                this.alt_dial = true
                if (dial_primary){
                    this.primary_dial = true
                }
                $("#submit_customer_info").click()
                $('#fb_timer_div,#skip_btn_div,#pause_pro_div').addClass('d-none')
            }
        },
    },
    watch:{
        numeric(val){
            // sms_templates.selected_template = [];
            $.each(sms_templates.templates,function(index, value){
                sms_dict={}
                if($("#sms_template"+value.id).prop('checked')){
                    if (hasDupsSimple(sms_templates.selected_template, value.id)) {
                        sms_dict['id']= value.id
                        sms_dict['text'] = $('#sms_text'+value.id).text()
                        sms_templates.selected_template.push(sms_dict)
                    }
                }
            })
            if(val != null){
                this.show_call_info = true
                sms_templates.customer_mo_no = val
                if(sms_templates.is_manual_sms &&  Isprogressive == false && IsPreview == false) {
                    $('#sms_tab').removeClass('d-none')
                }
            }else{
                this.show_call_info = false
                sms_templates.customer_mo_no = ''
                if(sms_templates.is_manual_sms) {
                    $('#sms_tab').addClass('d-none')
                }
            }
        },
        alt_numeric(value){
            if(value.length > 0 && this.selected_alt_numeric == ""){
                this.selected_alt_numeric = value[0]['alt_value']
            }else if(value.length == 0 && this.selected_alt_numeric != ""){
                this.selected_alt_numeric = ''
            }
        },
        selected_alt_numeric(value){
            if(value != "" && value != this.dailed_numeric && agent_info_vue.state == 'Feedback'){
                this.show_alt_dial_btn = true
            }else{
                this.show_alt_dial_btn = false
            }
        },
        dailed_numeric(value){
            let vm = this
            if(vm.numeric != value){
                $.each(vm.alt_numeric,function(key,item){
                    if(item['alt_value'] == value){
                        vm.selected_alt_numeric = value
                        vm.show_caret = true
                        vm.show_alt_dial_btn = false
                        return false;
                    }
                })
            }else{
                vm.show_caret = false
            }
            if(agent_info_vue.isMobile()){
                if (value){
                    $('#mb-call-flow').html("<i class='fas fa-phone fa-rotate-90 mr-1'></i>"+vm.callflow).removeClass('d-none')
                    $("#mb-call-number").text(value)
                } else {
                    $('#mb-call-flow').html('').addClass('d-none')
                    $("#mb-call-number").text(value)
                }
            }
        }
    }
})
// select2 multiple select component in vue
Vue.component('select2', {
    props: ['options', 'value'],
    template: '<select v-bind:name="name" class="form-control"></select>',
    mounted: function () {
        var vm = this
        $(this.$el)
      // init select2
      .select2({ data: this.options })
      .val(this.value)
      .trigger('change')
      // emit event on change.
      .on('change', function () {
        vm.$emit('input', $(this).val())
        vm.$emit('blur', null)
      })
      },
      watch: {
        value: function (value) {
          // update value
          if ([...value].sort().join(",") !== [...$(this.$el).val()].sort().join(",")){
              $(this.$el)
              .val(value)
              .trigger('change')
          }
        },
        options: function (options) {
          // update options
          $(this.$el).select2({ data: options })
        }
    },
    destroyed: function () {
        $(this.$el).off().select2('destroy')
    }
})

// bootstrap timepicker component in vue
Vue.component('timepicker',{
    props: ['name','target','value','isRequired'],
    template: `<div class="input-group date timefield" data-target-input="nearest">
                <div class="input-group" :data-target=this.target data-toggle="datetimepicker">
                <input type="text" :name=this.name placeholder="HH:mm" :data-target="this.target"
                class="form-control crm-form-control datetimepicker-input" :data-validation="[isRequired ? 'required' : '']"/> 
                <div class="input-group-addon input-group-append">
            </div></div></div>`,
    mounted: function(){
        var vm = this
        vm.$nextTick(function () {
            $(vm.$el)
            .datetimepicker({
                format:'hh:mm A'
            })
            $(vm.$el).data("datetimepicker").date(this.value);
            $(vm.$el).on('change.datetimepicker' ,function(e){
                vm.$emit('set-time', e.date.format("hh:mm A"))
                vm.$emit('blur', null)
            })
        })
    },
    watch:{
        value: function (value){
            // update value
            $(this.$el).data("datetimepicker")
            .date(value)
        }
    },
})
// bootstrap datetimepicker component in vue
Vue.component('datetimepicker',{
    props: ['name','target','value','isRequired','previous_disabled'],
    template: `<div class="input-group date" data-target-input="nearest">
                <div class="input-group" :data-target=this.target data-toggle="datetimepicker">
                <input type="text" :name="this.name" placeholder="YYYY-MM-DD HH:mm" :data-target="this.target"
                class="form-control crm-form-control datetimepicker-input" :data-validation="[isRequired ? 'required' : '']" readonly/>
                <div class="input-group-addon input-group-append">
            </div></div></div>`,
    mounted: function(){
        var vm = this
        vm.$nextTick(function () {
            if(vm.previous_disabled){
                $(vm.$el)
                .datetimepicker({
                    allowInputToggle:true,
                    ignoreReadonly: true,
                    format: 'YYYY-MM-DD HH:mm',
                    sideBySide: true,
                    buttons:{
                        showClear: true,
                    },
                    minDate: new Date(),
                });
            } else {
                $(vm.$el)
                .datetimepicker({
                    allowInputToggle:true,
                    ignoreReadonly: true,
                    format: 'YYYY-MM-DD HH:mm',
                    sideBySide: true,
                    buttons:{
                        showClear: true,
                    },
                });
            }
            $(vm.$el).data("datetimepicker").date(vm.value);
            $(vm.$el).on('change.datetimepicker' ,function(e){
                vm.$emit('set-datetime', e.date.format("YYYY-MM-DD HH:mm"))
            })
            $($(vm.$el).find('input')).on('blur' ,function(e){
               vm.$emit('set-datetime',$(vm.$el).find('input').val());
               vm.$emit('blur', null)
            })
        })
    },
    watch:{
        value: function (value){
            // update value
           $(this.$el).data("datetimepicker")
            .date(value)
        }
    },
})
Vue.component('datepicker',{
    props: ['value','isRequired','name','previous_disabled'],
    template: `<div class="input-group date datepicker p-0">
                <input type="text" class="form-control crm-form-control" placeholder="yyyy-mm-dd"
                :data-validation="[isRequired ? 'required' : '']" :name="this.name" readonly>
                <span class="input-group-addon input-group-append">
                </span>
            </div>`,
    mounted: function(){
        var vm = this
        vm.$nextTick(function () {
            if(vm.previous_disabled){
                $(vm.$el)
                .datepicker({
                    useStrict: true,
                    enableOnReadonly: true,
                    todayHighlight: true,
                    autoclose: true,
                    clearBtn: true,
                    format: "yyyy-mm-dd",
                    startDate : new Date(),
                });
            } else {
                $(vm.$el)
                .datepicker({
                    enableOnReadonly: true,
                    todayHighlight: true,
                    autoclose: true,
                    format: "yyyy-mm-dd",
                    clearBtn: true,
                });
            }
            $(vm.$el).datepicker('update', this.value);
            $(vm.$el).on('changeDate' ,function(e){
                vm.$emit('set-date', e.format("yyyy-mm-dd"))
            })
            $($(vm.$el).find('input')).on('blur', function(){
                vm.$emit('blur', null)
            })
        })
    },
    watch:{
        value: function (value){
            // update value
            $(this.$el).datepicker('update',value);
        }
    },
})
Vue.component('cb-datetimepicker',{
    props: ['name','target','value','id','db_name','is_required'],
    template: `<div class="input-group date" data-target-input="nearest" :id="this.id|replace">
                <div class="input-group" :data-target=this.target|replace data-toggle="datetimepicker">
                <input type="text" :name="this.name" placeholder="YYYY-MM-DD HH:mm" :data-target="this.target|replace"
                class="form-control crm-form-control datetimepicker-input" :data-validation="is_required ? 'required':''" :data-label="this.db_name" readonly/> 
                <div class="input-group-addon input-group-append">
            </div></div></div>`,
    mounted: function(){
        var vm = this
        vm.$nextTick(function () {
            $(vm.$el)
            .datetimepicker({
                format: 'YYYY-MM-DD HH:mm',
                ignoreReadonly: true,
                allowInputToggle:true,
                sideBySide: true,
                minDate: new Date(),
                buttons:{
                    showClear: true,
                },
            });
            $(vm.$el).data("datetimepicker").date(vm.value);
            $(vm.$el).on('change.datetimepicker' ,function(e){
                if ('date' in e && e.date){
                    vm.$emit('set-datetime', e.date.format("YYYY-MM-DD HH:mm"))
                    vm.$emit('blur', null)
                }else{
                    vm.$emit('set-datetime', null)
                    vm.$emit('blur', null)
                }
            })
        })
    },
    watch:{
        value: function (value){
            // update value
           $(this.$el).data("datetimepicker")
            .date(value)
        }
    },
})
Vue.component('cb_datepicker',{
    props: ['name'],
    template: '<div id="datepicker-popup" class="date input-group datepicker">'+
                '<input type="text" class="form-control crm-form-control" :name="this.name" placeholder="YYYY-MM-DD" readonly>'+
                '<span class="input-group-addon input-group-append">'+
                        '</span>'+
             '</div>',

    mounted: function(){
        var vm = this
        $(this.$el).find('input').val(moment(new Date()).format("YYYY-MM-DD"));
        $(this.$el).datepicker({
            enableOnReadonly: true,
            todayHighlight: true,
            format: 'yyyy-mm-dd',
            orientation: 'auto',
            autoclose: true,
            forceParse : true,
            startDate : new Date(),
        })
    }
})
Vue.component('cb_timepicker',{
    props: ['name','target'],
    template: '<div class="input-group date timefield" data-target-input="nearest">'+
                '<div class="input-group" :data-target=this.target data-toggle="datetimepicker">'+
                '<input type="text" :name=this.name placeholder="HH:mm" :data-target="this.target"'+ 
                'class="form-control crm-form-control datetimepicker-input"/>'+ 
                '<div class="input-group-addon input-group-append">'+
            '</div></div></div>',
    mounted: function(){
        var vm = this
        $(this.$el).find('input').val(moment(new Date()).format("HH:mm"));
        $(this.$el)
        .datetimepicker({
            format:'HH:mm'
        })
    }
})
Vue.component('single-select', {
    props: ['options', 'value'],
    template: `<select><slot></slot></select>`,
    mounted: function() {
        var vm = this
        $(this.$el)
            // init select2
            .select2({
                data: this.options
            })
            .val(this.value)
            .trigger('change')
            // emit event on change.
            .on('change', function() {
                if ($(this).val() != null) {
                    vm.$emit('input', $(this).val())
                    vm.$emit('blur', null)
                    vm.$emit('where-change')
                }
            })
    },
    watch: {
        value: function(value) {
            // update value
            if (Array.isArray(value)){
                if (value[0] !== $(this.$el).val()) {
                    $(this.$el)
                    .val(value[0])
                    .trigger('change')
                }
            } else {
                if (value !== $(this.$el).val()) {
                    $(this.$el)
                    .val(value)
                    .trigger('change')
                }
            }
        },
        options: function(options) {
            // update options
            $(this.$el).select2({
                data: options
            })
        }
    },
    destroyed: function() {
        $(this.$el).off().select2('destroy')
    }
})
// for datepicker in crm field
$(document).on('focus',".datepicker", function(){
    if($(this).length){
        $(this).datepicker({
            enableOnReadonly: true,
            todayHighlight: true,
            format: 'yyyy-mm-dd',
            orientation: 'auto',
            autoclose: true,
        });
    }
})
// for timepicker in crm field
$(document).on('focus',".datetimefield", function(){
    if($(this).length){
    $(this).datetimepicker();
    }
});
$.fn.select2.amd.require(['select2/selection/search'], function (Search) {
    var oldRemoveChoice = Search.prototype.searchRemoveChoice;

    Search.prototype.searchRemoveChoice = function () {
        oldRemoveChoice.apply(this, arguments);
        this.$search.val('');
    };
    $('.crm-multiselect').select2();
});

// this function is to show customer information on crm fields
function showcustinfo(data){
    if(data.length != 0){
        crm_field_vue.update_crm = false
        cust_info = data;
        sessionStorage.setItem("unique_id",cust_info["uniqueid"])
        $.each(crm_field_vue.basic_field_data,function(key,value){
            crm_field_vue.basic_field_data[key] = cust_info[key]
            $('#script_description').find('[data-id="'+key+'"]').text(cust_info[key])
            $.each(sms_templates.templates,function(index, value){
                $('#sms_text'+value.id).find('[data-id="'+key+'"]').text(cust_info[key])
            })
            $.each(email_templates.templates,function(index, value){
                $('#email_body_'+value.id).find('[data-id="'+key+'"]').text(cust_info[key])
            })
        })
        call_info_vue.numeric = cust_info['numeric']
        call_info_vue.createAlternateDict(cust_info['alt_numeric'])
        call_info_vue.status = cust_info['status']
        email_templates.customer_email = cust_info['email']
        if(email_templates.email_type=='2' &&  Isprogressive == false && IsPreview == false){
            $('#email_tab').removeClass('d-none')
        }else{
            $('#email_tab').addClass('d-none')
        }
        if ('contact_info' in cust_info){
            var extra_data = cust_info["contact_info"];
            crm_field_vue.field_data = extra_data
            crm_field_vue.created_date = cust_info['created_date']
            $.each(crm_field_vue.temp_data,function(sec_key, sec_value){
                if(sec_key in extra_data){
                    $.each(sec_value,function(field_key, field_value){
                        if(field_key in extra_data[sec_key]){
                            var script_field = sec_key+':'+field_key
                            $('#script_description').find('[data-id="'+script_field+'"]').text(extra_data[sec_key][field_key])
                            $.each(sms_templates.templates,function(key, value){
                                $('#sms_text'+value.id).find('[data-id="'+script_field+'"]').text(extra_data[sec_key][field_key])
                            })
                            $.each(email_templates.templates,function(index, value){
                                $('#email_body_'+value.id).find('[data-id="'+script_field+'"]').text(extra_data[sec_key][field_key])
                            })
                        }
                    })
                }
            })
        }
        if('address_details' in crm_field_vue.field_data){
            if(crm_field_vue.field_data['address_details']["pincode"] != '' && crm_field_vue.field_data['address_details']["city"] != '' && crm_field_vue.field_data['address_details']["city"] != ''){    
                pincodesearch(crm_field_vue.field_data['address_details']["pincode"]) 
            }
        }
         if('sms_status' in crm_field_vue.field_data){
            if('status' in crm_field_vue.field_data['sms_status'] && crm_field_vue.field_data['sms_status']['status']){
                $('.send_sms_btn').text('Re-Send Link')
            }else{
                $('.send_sms_btn').text('Send')
            }
        }
        if(sms_templates.send_sms_callrecieve){
            sms_templates.selected_template = []
            $.each(sms_templates.templates,function(index, value){
                console.log(value.id)
                sms_dict= {}
                sms_dict['id'] = value.id
                sms_dict['text'] = $('#sms_text'+value.id).attr('title');
                sms_templates.selected_template.push(sms_dict)
            })
        }
        if(email_templates.email_type == '0'){
            email_templates.selected_template = []
            $.each(email_templates.templates,function(index,value){
                email_dict = {}
                email_dict['id'] = value['id']
                email_dict['email_subject'] = $('#email_subject_'+value['id']).text()
                email_dict['email_body'] = $('#email_body_'+value['id']).text()
                email_templates.selected_template.push(email_dict)
            })
        }
        if ('last_verified_by' in cust_info && cust_info['last_verified_by'] && user_role !='Agent'){
            if (user_role == 'Supervisor'){
                var last_verified_user = cust_info['last_verified_by']['created_by']
            } else {
                var last_verified_user = cust_info['last_verified_by']['last_verified_by']
            }
            dispo_vue.lead_user = [
                {'text':'Assigned Lead To','children':[...dispo_vue.assigned_lead_user]},
                {'text':'Assigned Lead To Reverify','children':[{'id':last_verified_user,'text':last_verified_user,'data-reverify':true}]}
            ]
        } else {
            dispo_vue.lead_user = [{'text':'Assigned Lead To','children':[...dispo_vue.assigned_lead_user]}]
        }
    }
}

function showmysqlinfo(data){
    if(data.length > 0){
        cust_info = data[0];
        if ('customer_information' in cust_info){
            var extra_data = cust_info;
            crm_field_vue.field_data = extra_data
        }
    }
}
inbound_dialed_uuid = ""
inbound_action = ""
function incoming_call_functionality(inbound_dialed_uuid, action){
    session_details[extension]['dialed_uuid'] = ic_vue.incomingCall_data[inbound_dialed_uuid].dialed_uuid
    details = JSON.stringify(session_details[extension])
    destination_number = ic_vue.incomingCall_data[inbound_dialed_uuid].destination_number
    sessionStorage.setItem('previous_number',destination_number)
    var call_data ={'user_extension':extension, 'action':action,
            'session_details':details, 'destination_number':destination_number,'campaign_name':campaign_name}
    var agent_activity_data = create_agent_activity_data()
    $.extend(call_data, agent_activity_data)
    // ajax call for accept or reject incoming call
    $.ajax({
         type:'POST',
         headers: {"X-CSRFToken":csrf_token},
         url: '/api/incomingCall/',
         data: call_data,
         success: function(data){
            ic_vue.incomingCall = false;
            Vue.delete(ic_vue.incomingCall_data, inbound_dialed_uuid)
            inbound_dialed_uuid = ""
            inbound_action = ""
            if(sessionStorage.getItem('previous_number')===destination_number){
                if(data['success']){
                    dispo_vue.on_call_dispo = true
                    $("#call-loader").fadeIn("fast")
                    $('#idle_timer,#dialer_timer').text("00:00:00")
                    // agent_info_vue.state = 'InCall'
                    set_agentstate('InCall')
                    init_time = new Date($.now());
                    ring_time = new Date($.now());
                    callflow = callmode =  'inbound';
                    $('#SecondsDISP,#dialer_timer,#speak_timer').countimer('start');
                    $("#call_duration_timer").removeClass('d-none')
                    $("#ring_timer").countimer('stop')
                    connect_time = new Date($.now());
                    if (sessionStorage.getItem('can_transfer') == "true"){
                        $("#btnTransferCall").removeClass("d-none").prop('disabled', false)
                    }
                    $("#btnParkCall").prop('disabled', false);
                    $("#call-loader").fadeOut("slow")
                    $('#cust_basic_info a').editable('setValue', '');
                    $("#editable-form").trigger("reset")
                    HangupCss()
                    $("#profile-tab").addClass("disabled")
                    $("#btnResumePause,#ibc_btnResumePause,#blndd_btnResumePause").addClass("d-none")
                    $("#btnLogMeOut").attr("disabled", true)
                    $("#btnTransferCall, #btnParkCall").removeClass("d-none")
                    $("#livecall h3").removeClass().addClass("text-success").text("LIVE CALL").attr("title","LIVE CALL");
                    $("#dialer_timer,#idle_timer").countimer('stop')
                    ic_vue.incomingCall_data = {}
                    ic_vue.rejectCall_data = {}
                    agent_hangup = false 
                    temp_cust_data = data['contact_info']
                    if(data['contact_count'] > 1){
                        if('contact_info' in data){
                            $('#list_li').removeClass('d-none')
                            $('#contact-info, #contact-info-tab').removeClass('active show')
                            $('#list-info, #list-info-tab').addClass('active show')
                            list_of_contacts_table.clear().draw()
                            list_of_contacts_table.rows.add(data['contact_info']);
                            list_of_contacts_table.draw();
                        }else if('error' in data){
                            showWarningToast('Contact Info is Not avaliabe', 'top-right')
                        }
                    }else{
                        var contact_id = ""
                        if('contact_info' in data && data['contact_info'].length > 0){
                            contact_id = data['contact_info'][0]['id']
                        }
                        if('contact_info' in data && sessionStorage.getItem("third_party_data_fetch","") == "true"){    
                            if(data['contact_info'].length > 0){
                                showmysqlinfo(data['contact_info'])
                                update_sql_database = true
                            }
                            else {
                                update_sql_database = false
                                $(".mobile_no_search_div").removeClass("d-none")
                            }
                            showcustinfo({"numeric":destination_number})
                            set_inbound_customer_detail(destination_number,contact_id,do_not_set=true)
                        } else{
                            set_inbound_customer_detail(destination_number,contact_id)
                        }
                    }
                    thirdparty_module(data)
                    //thirdparty and dap functionality 
                 //    if ("thirdparty_api_status" in data && data["thirdparty_api_status"] == true){
                 //        if("dap_status" in data && data["dap_status"] == true ){
                 //            if('weburl' in data){
                 //                $('#dap_details').removeClass('d-none')
                 //                dap_details_data = data['weburl']
                 //            }
                 //        }else{
                 //            if('weburl' in data){
                 //                open_third_party_api(data['weburl'])
                 //            }
                 //        }
                 // }

                    if(sessionStorage.getItem("outbound") == "Preview" || sessionStorage.getItem("outbound") == "Progressive") {
                        $("#btnNextCall").addClass("d-none")
                    }
                    
                }
                else if(data['error']){
                    showInfoToast(data["error"],'top-center')
                    $("#call-loader").fadeOut("fast")
                }
            }
        }
    })
}
// 
Vue.component('avatar',VueAvatar.Avatar);
// this vue is to show and handle incoming call popup
var ic_vue = new Vue({
    el: '#incoming_call_vue',
    delimiters: ['${', '}'],
    data:{
        incomingCall : false,
        incomingCall_data: {},
        rejectCall_data: {},
    },
    watch:{
        inbound_dialed_uuid(value){
            if(Object.keys(value).length === 0){
                this.incomingCall = false
            }
        }
    },
    methods:{
        ic_activity(action,dialed_uuid){
            var vm = this
            var details = '';
            var destination_number = '';
            inbound_dialed_uuid = dialed_uuid
            inbound_action = action
            if(action == 'reject'){
                vm.rejectCall_data[dialed_uuid] = {...vm.incomingCall_data[dialed_uuid]}
                Vue.delete(vm.incomingCall_data, dialed_uuid)
            }
            else if(action == 'accept'){
                if($.inArray(agent_info_vue.state,['InCall','Feedback']) == -1){
                    inboundCall_picked = true
                    if (Isprogressive == true || IsPreview == true) {
                        $("#skip_btn").trigger('click')
                    }
                    else {
                        incoming_call_functionality(inbound_dialed_uuid, inbound_action)
                    }
                }else{
                    if(agent_info_vue.state == 'InCall'){
                        showWarningToast('You already in call...', 'top-center')
                    }
                    else{
                        showWarningToast('Submit feedback first...', 'top-center')
                    }
                }
            }
        }
    }
});

// this vue is to show and handle transfer call popup
var ic_vue_transfer = new Vue({
    el: '#transfer_call_vue',
    delimiters: ['${', '}'],
    data:{
        transfercall : false,
        transfercall_data: {},
    },
    methods:{
        ic_activity(action,dialed_uuid){
            var vm = this
            var details = '';
            var destination_number = '';
            clearInterval(transfer_popup)            
            if(action == 'reject'){
                this.transfercall_data[dialed_uuid]['status']="notanswered"
                socket.emit("transfer_to_agent_rejected",this.transfercall_data[dialed_uuid])
                Vue.delete(vm.transfercall_data, dialed_uuid)
                if(Object.keys(this.transfercall_data).length == 0){
                    vm.transfercall = false;
                }
                transferCall_picked = false;
                var data ={'event':'Transfer Not Answered', 'campaign_name':campaign_name}
                var agent_activity_data = create_agent_activity_data()
                $.extend(data, agent_activity_data)
                 $.ajax({
                        type:'POST',
                        headers: {"X-CSRFToken":csrf_token},
                        url: '/api/transferagent/',
                        data: data,
                        success: function(data){

                        }
                    })
            }
            else if(action == 'accept'){
                if($.inArray(agent_info_vue.state,['InCall','Feedback','Predictive Wait','Blended Wait','Inbound Wait']) == -1){
                    if($('#skip_btn_div').hasClass('d-none') == false){
                        $('#skip_btn').trigger('click')
                    }
                    $("#call-loader").fadeIn("fast")
                    $('#idle_timer,#dialer_timer').text("00:00:00")
                    $('#SecondsDISP,#speak_timer,#dialer_timer').countimer('start');
                    $("#call_duration_timer").removeClass('d-none')
                    $("#call-loader").fadeOut("slow")
                     $("#ring_timer").countimer('stop')
                    // agent_info_vue.state = 'InCall'
                    set_agentstate('InCall')
                    init_time = new Date($.now());
                    ring_time = new Date($.now());
                    callflow = 'transfer';
                    callmode = 'inbound transfer'
                    connect_time = new Date($.now());                                 
                    transferCall_picked = true
                    HangupCss()
                    $('#btnDialHangup').prop('title','Transferhangup');
                    $("#profile-tab").addClass("disabled")
                    $("#btnResumePause, #blndd_btnResumePause, #ibc_btnResumePause").addClass("d-none")
                    $("#btnLogMeOut").attr("disabled", true)
                    $("#toggleMute").removeClass("d-none")
                    $("#livecall h3").removeClass().addClass("text-success").text("LIVE CALL").attr("title","LIVE CALL");

                    this.transfercall_data[dialed_uuid]['status']="answered"
                    transfer_from_agent_number = this.transfercall_data[dialed_uuid].transfer_from_agent_number
                    session_details[extension]['transfer_from_agent_uuid'] = this.transfercall_data[dialed_uuid].transfer_from_agent_uuid
                    session_details[extension]['dial_number'] = this.transfercall_data[dialed_uuid].transfer_number
                    session_details[extension]['transfer_from_agent_number']=transfer_from_agent_number
                    var rej_data = {...this.transfercall_data}
                    delete rej_data[dialed_uuid]
                    for(var key in rej_data) {
                        socket.emit("transfer_to_agent_rejected",rej_data[key])
                    } 
                    destination_number = this.transfercall_data[dialed_uuid].transfer_number
                    $("#dialer_timer,#idle_timer").countimer('stop')
                    var call_data ={'user_extension':extension, 'action':action,'transfer_type':this.transfercall_data[dialed_uuid].transfer_type
                        ,'destination_number':destination_number,'campaign_name':campaign_name, 'event':'Transfer Answered'}
                    var agent_activity_data = create_agent_activity_data()
                    $.extend(call_data, agent_activity_data,session_details[extension])
                    $.ajax({
                        type:'POST',
                        headers: {"X-CSRFToken":csrf_token},
                        url: '/api/transferagent/',
                        data: call_data,
                        success: function(data){
                            vm.transfercall = false;
                            vm.transfercall_data = {}
                            if(session_details[extension]['dial_number']===destination_number){
                                 if(data['success']){
                                    socket.emit('tr_internal_agent_answer',data);
                                    if(sessionStorage.getItem("outbound") == "Preview" || sessionStorage.getItem("outbound") == "Progressive") {
                                        $("#btnNextCall").addClass("d-none")
                                    }
                                    data = [{'numeric':transfer_from_agent_number,'first_name':''}]
                                    showcustinfo(data)
                                    call_info_vue.callflow = 'Internal' 
                                }
                                else if(data['error']){
                                    showInfoToast(data["error"],'top-center')
                                    $("#call-loader").fadeOut("fast")
                                }
                            }
                        }
                    });
                }
                else{
                    if(agent_info_vue.state == 'InCall'){
                        showWarningToast('You already in call...', 'top-center')
                    }
                    else if(agent_info_vue.state == 'Feedback'){
                        showWarningToast('Submit feedback first...', 'top-center')
                    }else{
                      showWarningToast('You are in Predictive or Inbound or Blended Mode, please stop it and accept', 'top-center')  
                    }
                }
            }
             
        }
    },
});

var agent_info_vue = new Vue({
    // el: "#agent_info_vue",
    delimiters: ['${', '}'],
    data: {
        camp_name :'',
        show_camp : false,
        is_portfolio:false,
        on_break: false,
        selected_status: 'NotReady',
        agent_breaks: [],
        breakexceed : false,
        state: 'Idle',
        mode_list:[],
        break_timing:[],
    },
    watch:{
        camp_name: function(value){
            if(value === ""){
                this.show_camp = false
                this.selected_status = 'NotReady'
            }
            else{
                this.show_camp = true
                this.selected_status = 'Ready'
            }
            this.on_break = false
        },
        selected_status: function(value){
            if (value === 'NotReady'){
                this.resetAgentInfo()
            }
            if(value === 'Ready'){
                this.state = 'Idle'
                this.on_break = false
            }
        },
        state: function(value){
            setAgentStatus({status:this.selected_status, state:value})
            if(value == 'Feedback' && dispo_vue.selected_pd !=''){
                $('#submit_customer_info').attr('disabled',false)
            }
            if(value == 'Feedback'){
                if(call_info_vue.selected_alt_numeric != "" 
                    && call_info_vue.selected_alt_numeric != call_info_vue.dailed_numeric)
                {
                    call_info_vue.show_alt_dial_btn = true
                }else{
                    call_info_vue.show_alt_dial_btn = false
                }
            }
            if (value == 'Idle' && agent_info_vue.isMobile()){
                $('.mb-manual-dial-div').removeClass('d-none')
            } else if(agent_info_vue.isMobile()) {
                $('.mb-manual-dial-div').addClass('d-none')
            }
        }
    },
    methods:{
        isMobile() {
           if($(window).width() < 576) {
             return true
           } else {
             return false
           }
         },
        resetAgentInfo :function(){
            this.camp_name ='';
            this.show_camp = false;
            this.on_break = false
            this.state = ""
            // this.selected_status= 'NotReady';
            this.mode_list =[];
        },
        changeStatus: function(status_val){
            this.selected_status = status_val
        },
        selectBreak: function(break_name="Ready",break_time="00:00:00", break_inactive=true){
            var vm = this
            if(vm.selected_status === 'Ready'|| vm.selected_status === 'NotReady'){
                previous_break = ''
            }
            else{
                previous_break = vm.selected_status
            }
            var break_time = break_time.split(":")
            break_time = break_time[0]+":"+break_time[1]
            vm.selected_status = break_name  
            $("#reverse-break-time").click()
            $("#reverse-break-time").remove()
            $("#rbreak").append('<span id="reverse-break-time"></span>')
            $(".agent-break-status").removeClass("d-none")
            if(vm.selected_status === 'Ready') {
                $("#idle_timer").countimer('start')
            }
            // $("#idle_timer").countimer('stop')
            $("#wait_timer").text('0:0:0')
            sessionStorage.setItem("wait_time", "0:0:0");
            var uuid = '';
            var sip_ip = '';
            // Do something with the previous_break value after the change
            if(session_details[extension] != undefined){
                uuid = session_details[extension]['Unique-ID'];
                sip_ip = session_details[extension]['variable_sip_from_host'];
            }
            var agent_activity_data = create_agent_activity_data()
            agent_activity_data["campaign_name"] = this.camp_name
            agent_activity_data["break_name"] = break_name
            agent_activity_data["extension"] = extension
            agent_activity_data['break_type'] = vm.selected_status
            if (previous_break) {
                agent_activity_data["event"] = "End Break"
                agent_activity_data["break_type"] = previous_break
                agent_activity_data["break_time"] = sessionStorage.getItem("break_time");
                agent_activity_data["tos_time"] = sessionStorage.getItem("break_time");
            }

            else {
                $('#break_timer').countimer('stop');
                agent_activity_data["event"] = "Start Break"
            }
            if (vm.breakexceed){
                agent_activity_data["event"] = "Break Exceed"
                sessionStorage.setItem("break_time",'0:0:0');
            }
            if(agent_activity_data['event']==="Start Break" &&  call_type==='webrtc' && sip_login===true && vm.selected_status!=='Ready' && vm.selected_status!=='NotReady'){
                sipStack.stop();
            }

            agent_activity_data['uuid'] = uuid;
            agent_activity_data['sip_ip'] = sip_ip;
            agent_activity_data['call_type'] = call_type;

            $.ajax({
                type:'post',
                headers: {"X-CSRFToken":csrf_token},
                url: '/CRM/save-agent-breaks/',
                data: agent_activity_data,
                success: function(data){
                    flush_agent_timer()
                    if(agent_activity_data['event']!=='Start Break' && call_type!=='webrtc'){
                        if(data.uuid!==''){
                            session_details[extension]['Unique-ID'] = data.uuid
                        }else{
                           errorAlert("Sip intiation Error", "Sip is not initiated properly");
                           $('#btnLogMeOut').click();
                        }
                    }
                    if (vm.selected_status === 'Ready'){
                        $('#dialer_timer').countimer('start')
                    }else if(vm.selected_status === 'NotReady'){
                        $('#app_timer').countimer('start')
                    }
                    $("#break_timer").text('0:0:0')
                }
            })
            if($.inArray(break_name, ["Ready","NotReady"])==-1){
                vm.state = 'OnBreak'
                vm.on_break = true
                $("#idle_timer").countimer('stop')
                $("#idle_timer").text('0:0:0')
                $('#break_timer').countimer('start');
                if (break_time) {
                    var swal_sec = moment.duration(break_time).asSeconds()
                    var swal_millsec = swal_sec*1000;
                    if(break_inactive){
                        break_time = break_time.split(":")
                        $("#reverse-break-time").countdowntimer({
                            hours : break_time[0],
                            minutes : break_time[1],
                            size : "lg",
                            timeUp:stopped_break_func,
                            stopButton : "reverse-break-time"
                        });
                        swal({
                        icon:'info',
                        title: "You are on "+break_name,
                        text: "Do You Want to end the Break ?",
                        timer: swal_millsec,
                        closeOnClickOutside:false,
                        button: {
                            text: "Yes ,Finish it!",
                            value: true,
                            visible: true,
                            className: "btn btn-primary",
                            closeModal: true
                        },
                    })
                    .then(
                        function(dismiss){
                            if(!dismiss){
                                vm.breakexceed = true
                            }
                            $('#agent_breaks').val('')
                            $(".agent-break-status").addClass("d-none")
                            $('#break_timer').countimer('stop');
                            $('#idle_timer').countimer('start');
                            if(call_type==="webrtc" && sip_login===true){
                                sipStack.start();
                            }
                            if (vm.camp_name){
                                vm.selectBreak()
                            }else{
                                vm.selectBreak("NotReady",'00:00:00',true)
                            }
                            showbreaksonagentsdashboard()
                        }
                    );
                    }else{
                       $("#reverse-break-time").countimer({
                            autoStart: false,
                            enableEvents: true,
                            initHours: "00",
                            initMinutes: "00",
                            initSeconds: "00",
                            stopButton : "reverse-break-time",
                        });
                        $("#reverse-break-time").countimer('start')
                         swal({
                        icon:'info',
                        title: "You are on "+break_name,
                        text: "Do You Want to end the Break ?",
                        closeOnClickOutside:false,
                        button: {
                            text: "Yes ,Finish it!",
                            value: true,
                            visible: true,
                            className: "btn btn-primary",
                            closeModal: true
                        },
                    })
                    .then(
                        function(dismiss){
                            // if(!dismiss){
                            //     vm.breakexceed = true
                            // }
                            $('#agent_breaks').val('')
                            $(".agent-break-status").addClass("d-none")
                            $('#break_timer').countimer('stop');
                            $('#idle_timer').countimer('start');
                            if(call_type==="webrtc" && sip_login===true){
                                sipStack.start();
                            }
                            if (vm.camp_name){
                                vm.selectBreak()
                            }else{
                                vm.selectBreak("NotReady",'00:00:00',true)
                            }
                            showbreaksonagentsdashboard()
                        }
                    );
                    }
                }
            }
            else if (vm.breakexceed){
                if (vm.camp_name){
                    $("#btnLogMeOut").trigger('click');
                    $('#crm-agent-logout').removeClass('disabled')
                }
                window.location.href = "/logout/makeInactive/"
            }
            else {
                $('#break_timer').countimer('stop');    
                $('#idle_timer').countimer('start');
                $(".agent-break-status").addClass("d-none")
            }

        }
    }
})

function showbreaksonagentsdashboard(){
 $.ajax({
        type: 'post',
        headers: {
            "X-CSRFToken": csrf_token
        },
        url: '/api/get-agent-breaks/',
        success: function(data) {
            agent_info_vue.break_timing=data['break']
        },
        error: function(data) {
            console.log(data);
        }
    }) 
}

var agent_relationtag_vue = new Vue({
    el: '#relation-tag-tab',
    delimiters: ['${', '}'],
    data: {
        relationTag_list :[],
        primaryTag_index :"",
        secondryTag:[],
        taggingData_list:[],
        selected_subtag:{},
        relation_data :{},
        relation_type:'dropdown',
    },
    watch:{
        primaryTag_index(value){
            if(value){
                this.relation_type = this.relationTag_list[value-1].relation_type
                this.secondryTag = this.relationTag_list[value-1].relation_fields
            }
        }
    },
    methods:{
        addRelationTag(){
            var relation_form = $("#relation_tag_form")
            if(relation_form.isValid()){
                var vm = this
                var tagging_data = {}
                var formData = relation_form.serializeArray()
                var primaryTag = $("#primary_tagging :selected").text()
                $.each(formData, function(_,kv){
                    if(kv.name == 'primary_tagging'){
                        tagging_data[kv.name] = primaryTag
                    }else{
                        tagging_data[kv.name] = kv.value
                    }
                })
                vm.taggingData_list.push(tagging_data)
                vm.resetRelationForm()
            }
        },
        resetRelationForm(){
            this.primaryTag_index =""
            this.secondryTag=[]
            this.tagging_data={}
            this.relation_data = {}
            this.relation_type = 'dropdown'
        },
        selectSubtag(index){
            var vm = this
            vm.relation_data = {}
            if (index){
                vm.selected_subtag = this.secondryTag[index-1]
                if($.inArray(vm.selected_subtag.type,["","dropdown","multifield","checkbox"]) == -1){
                    vm.relation_data[vm.selected_subtag.name] = ""
                }else if(this.selected_subtag.type == 'checkbox'){
                    vm.relation_data[vm.selected_subtag.name] = false
                }else{
                    vm.relation_data[vm.selected_subtag.name] = {}
                }
            }
            else{
                vm.selected_subtag = {}
            }
        }

    }

})

add_three_way_conference_vue = new Vue({
    el: '#three_way_conference_div',
    delimiters: ["${","}"],
    data:{ 
        three_way_list: [],
    },
    methods: {
        confMute: function(index){
            var vm  = this
            var mute_data = {}
            mute_data['conf_uuid'] = vm.three_way_list[index]['conf_uuid']
            mute_data['conf_mute'] = !vm.three_way_list[index]['is_mute']
            mute_data['sip_server'] = session_details[extension]['variable_sip_from_host']
            $.ajax({
                type: 'post',
                headers: { "X-CSRFToken": csrf_token },
                url:'/api/conference_mute/',
                data: mute_data,
                success: function(data){
                    if(data['success']){
                        vm.three_way_list[index]['is_mute'] = !vm.three_way_list[index]['is_mute']
                    }
                }
            })
        },
        confHangup : function(index) {
            var vm  = this
            var conf_uuids = vm.three_way_list[index]['conf_uuid']
            var hangup_data = {'conf_uuids':conf_uuids}
            hangup_data['sip_server'] = session_details[extension]['variable_sip_from_host']
            $.ajax({
                type: 'post',
                headers: { "X-CSRFToken": csrf_token },
                url:'/api/conference_hangup/',
                data: hangup_data,
                success: function(data) {
                    disable_conference = false
                    $("#btnTransferCall").attr("disabled",false)
                }
            })
        },
        confHangupAll:function(){
            var vm = this
            var conf_uuids = vm.getAllConf_uuid()
            var hangup_data = {'conf_uuids':conf_uuids}
            hangup_data['sip_server'] = session_details[extension]['variable_sip_from_host']
            $.ajax({
                type: 'post',
                headers: { "X-CSRFToken": csrf_token },
                url:'/api/conference_hangup/',
                data: hangup_data,
                success: function(data) {
                    disable_conference = false
                    $("#btnTransferCall").attr("disabled",false)
                    vm.three_way_list = []
                }
            })
        },
        getAllConf_uuid:function(){
            var uuids = []
            this.three_way_list.filter(function(item){
                uuids.push(item.conf_uuid)
            })
            return uuids.join()
        },
        removeHangupedDict: function(index){
            this.three_way_list.splice(index, 1);
        },
    }
})



var agent_info_vue_mode = new Vue({
    el: "#agent_info_vue_mode",
    delimiters: ['${', '}'],
    data: {
        show_modes : false,
        mode_list:[],
    },
});


function setAgentStatus(data){
    $.ajax({
        type: 'post',
        headers: { "X-CSRFToken": csrf_token },
        url: '/api/change-agent-state/',
        data: data,
        success: function(data) {
            if(data!=" "){
            if (data['success']) {
                console.log("succccccccessss")
            }
        }
        },
        error: function(data) {
            
        }
    })
}


var sms_templates = new Vue({
    el: "#sms_templates",
    delimiters: ['${', '}'],
    data: {
        templates:[],
        customer_name:'',
        customer_mo_no:'',
        selected_template:[],
        is_manual_sms:false,
        send_sms_callrecieve:false,
        send_sms_on_dispo:false
    },
    methods:{
        sendSMS(campaign_id, selected_template, customer_mo_no,primary_dispo='') {
            $(".send_sms_btn").addClass("disabled")
            session_uuid = session_details[extension]['dialed_uuid']
            post_contact_id = sessionStorage.getItem("prev_selected_contact_id")
            if(post_contact_id == null || post_contact_id == undefined){
                post_contact_id = sessionStorage.getItem("contact_id")
            }
            if(campaign_id && selected_template.length>0 && customer_mo_no && session_uuid){
                $.ajax({
                    type: 'post',
                    headers: { "X-CSRFToken": csrf_token },
                    url: '/api/send_sms/',
                    data: {
                        numeric:customer_mo_no,
                        campaign_id:parseInt(campaign_id),
                        templates:JSON.stringify(selected_template),
                        dispo_submit:sms_templates.send_sms_on_dispo,
                        primary_dispo:primary_dispo,
                        session_uuid:session_uuid,
                        contact_id:post_contact_id
                    },
                    success: function(data) {
                        showSuccessToast(data['status'], 'top-center')
                        $(".send_sms_btn").removeClass("disabled")
                        $('.send_sms_btn').text('Re-Send Link')
                        sent_sms_flag = true

                    },
                    error: function(data) {
                        
                    },
                    complete: function (data) {
                      
                    }
                })
            }else{
                if(sms_templates.is_manual_sms) {
                    showDangerToast('You Cant Sent Message, All Field Are medatory', 'top-center')
                }
            }
        },
        setTemplateValue(id){
            sms_templates.selected_template = [];
            sms_dict = {}
            sms_dict['id'] = id
            sms_dict['text'] = $('#sms_text'+id).attr('title')  
            sms_templates.selected_template.push(sms_dict)
        }
    }
});

$(document).on('click','#sms_tab',function(){
    sms_templates.selected_template = [];
    let sms_select_temp = sms_templates.templates.slice(-1)
    $.each(sms_select_temp,function(index, value){
        sms_dict = {}
        sms_dict['id'] = value.id
        sms_dict['text'] = $('#sms_text'+value.id).attr('title')
        sms_templates.selected_template.push(sms_dict)
    })
})


var email_templates = new Vue({
    el: "#email_templates",
    delimiters: ['${', '}'],
    data: {
        gateway_id : null,
        templates:[],
        selected_template:[],
        email_type:'',
        email_dispositions:[],
        customer_email:''
    },
    methods:{
        sendEmail(){
            var vm = this
            $(".send_email_btn").addClass("disabled")
            if(vm.selected_template.length>0 && vm.customer_email){
                $.ajax({
                    type: 'post',
                    headers: { "X-CSRFToken": csrf_token },
                    url: '/api/send_email/',
                    data: {
                        'gateway_id': vm.gateway_id,
                        'to_email':vm.customer_email,
                        'templates':JSON.stringify(vm.selected_template),
                    },
                    success: function(data) {
                        showSuccessToast(data['success'], 'top-right')
                        $(".send_email_btn").removeClass("disabled")
                        vm.selected_template = []

                    },
                    error: function(data) {
                        $(".send_email_btn").removeClass("disabled")
                        if ('configuration_error' in data['responseJSON']){
                            showDangerToast('configuration_error',data['responseJSON']['configuration_error'], 'top-right')
                        }else{
                            showDangerToast('error',data['responseJSON']['error'], 'top-right')
                        }
                    },
                    complete: function (data) {
                      
                    }
                })
            }else{
                if(vm.email_type =='2') {
                    showDangerToast('You Cant Sent email, All Field Are medatory', 'top-center')
                }
            }
        },
        setTemplateValue(id){
            this.selected_template = [];
            email_dict = {}
            email_dict['id'] = id
            email_dict['email_subject'] = $('#email_subject_'+id).text()
            email_dict['email_body'] = $('#email_body_'+id).text()
            this.selected_template.push(email_dict)
        },
        restetEmailTemplate(){
            this.gateway_id = null;
            this.templates = [];
            this.selected_template = [];
            this.email_type = '';
            this.email_dispositions = [];
            this.customer_email = '';
        }
    }
})

function thirdparty_module(data){
//thirdparty and dap functionality 
if ("thirdparty_api_status" in data && data["thirdparty_api_status"] == true){
        if("click_for_details" in data && data['click_for_details'] == true && data["dynamic_api"] == false){
            if('weburl' in data){
                $('#dap_details').removeClass('d-none')
                if(callflow == 'inbound' || callmode == 'blended-inbound'){
                    dap_details_data = data['weburl']
                }else{
                    dap_details_data = JSON.parse(data['weburl'])
                }
            }
        }else if (data['click_for_details'] == true && data['dynamic_api'] == true){
            if('weburl' in data){
                $('#dap_details').removeClass('d-none')
                if(callflow == 'inbound' || callmode == 'blended-inbound'){
                    dap_details_data = data['weburl']
                }else{
                    dap_details_data = JSON.parse(data['weburl'])
                }
            }
        }
        else if("dynamic_api" in data && data["dynamic_api"] == true && data['click_for_details'] == false){
            if('weburl' in data){
                if(callflow == 'inbound' || callmode == 'blended-inbound'){
                     open_third_party_api(data['weburl'])
                }else{
                    open_third_party_api(JSON.parse(data['weburl']))
                }
            }

        }else{
            if('weburl' in data){
               if(callflow == 'inbound' || callmode == 'blended-inbound'){
                     open_third_party_api(data['weburl'])
                }else{
                    open_third_party_api(JSON.parse(data['weburl']))
                }
            }
        }
    }
}

var crm_data_vue = new Vue({
    el: "#crm_data_template",
    delimiters: ['${', '}'],
    data: {
        crm_data : {}
    }
})


function getBroadCastMessages() {
    $.ajax({
        type: 'GET',
        url: '/api/get-broadcastmessages/',
        cache: false,
        timeout: 5000,
        success: function(data) {
            broadcast_vue.broadcast_messages = data['b_messages']
        }
    })
}

var broadcast_vue = new Vue({
    // this vue is related to call_notififcations
    el: '#broadcast_messages',
    delimiters: ['${', '}'],
    data: {
        broadcast_messages: [],
    },
     filters: {
        format_date: function(date) {
            return moment().from(date, true);
        },
        read_more:function(message){
            if (message.length > 50){
                return message.substring(0,30)+"..Read More";
            }
            else{
               return message 
            }
        }
    },
    methods:{
        ReadBroadcast(index){
            if(index != '' || index != 'undefined' || index != undefined){  
                broad_cast_data = this.broadcast_messages[index]
                $('#broadcast_model').modal('toggle')
                $('#broadcast_sender').text(broad_cast_data['sent_by'])
                $('#broadcast_message_content').text(broad_cast_data['message'])
                $.ajax({
                    type: 'post',
                    headers: {"X-CSRFToken":csrf_token},
                    url: '/api/get-broadcastmessages/',
                    cache: false,
                    timeout: 5000,
                    data:broad_cast_data,
                    success: function(data) {
                       if(data['b_messages']){
                           broadcast_vue.broadcast_messages.splice(index,1)
                       }else{
                            showInfoToast(data['err'],'top-center')
                       }
                    }
                })
            }else{
                console.log("missed the index key")
            }
        },
    }
});

var kyc_document_vue = new Vue({
    el: '#kycdocuments_vue',
    delimiters: ['${', '}'],
    data: {
        documents: [],
        doc_is_error:false,
        doc_is_fetching:false 
    },
    methods:{
        opendocument(img){
            let win =  window.open()
            win.document.write('<img src="' + img  + '" width:75%; height:100%;></img>');
        }
    } 
})

var kyc_document_vue_1 = new Vue({
    el: '#kycdocuments_vue_1',
    delimiters: ['${', '}'],
    data: {
        documents: [],
        doc_is_error:false,
        doc_is_fetching:false 
    },
    methods:{
        opendocument(img){
            let win =  window.open()
            win.document.write('<img src="' + img  + '" width:75%; height:100%;></img>');
        }
    } 
})

$(document).on('click','#documents_tab',function(){
    kyc_document_vue.doc_is_fetching = true
    kyc_document_vue.documents = []
    if('appointment_details' in crm_field_vue.field_data){
        if('crm_ref_no' in crm_field_vue.field_data['appointment_details'] && crm_field_vue.field_data['appointment_details']['crm_ref_no'] != ''){
           $.ajax({
                type:'get',
                headers: {"X-CSRFToken":csrf_token},
                url:'/api/show-documents/',
                data:{'crm_ref_no':crm_field_vue.field_data['appointment_details']['crm_ref_no']},
                success:function(data){
                    if('success' in data){
                        kyc_document_vue.documents = data['success']
                        $('#kycdocument_modal').modal('show')
                    }else{
                        showInfoToast(data['error'],'top-center')
                    }
                },
                error:function(data){
                    if ('error' in data['responseJSON']){
                        console.log(data['responseJSON']['error'])
                        kyc_document_vue.doc_is_error = true
                    }
                },
                complete:function(data){
                    kyc_document_vue.doc_is_fetching = false
                }
           }) 
        }
    }
})

function kycdocview(crm_ref_no){
    kyc_document_vue_1.doc_is_fetching = true
    kyc_document_vue_1.documents = []
    $.ajax({
        type:'get',
        headers: {"X-CSRFToken":csrf_token},
        url:'/api/show-documents/',
        data:{'crm_ref_no':crm_ref_no},
        success:function(data){
            if('success' in data){
                kyc_document_vue_1.documents = data['success']
                $('#kycdocument_modal').modal('show')
                
            }else{
                showInfoToast(data['error'],'top-center')
            }
        },
        error:function(data){
            if ('error' in data['responseJSON']){
                kyc_document_vue_1.doc_is_error = true
            }
        },
        complete:function(data){
            kyc_document_vue_1.doc_is_fetching = false
        }

   }) 
}
