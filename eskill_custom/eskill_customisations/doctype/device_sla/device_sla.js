// Copyright (c) 2021, Eskill Trading and contributors
// For license information, please see license.txt

frappe.ui.form.on('Device SLA', {
    refresh : function(frm) {
        customer_filter(frm);
        model_filter(frm);
        serial_filter(frm);
        set_end_date(frm);
        terms_filter(frm);
    },

    before_submit : function(frm) {
        set_status(frm);
    },

    breach : function(frm) {
        breach_contract(frm);
    },

    model : function(frm) {
        if (!frm.doc.model) {
            frm.set_value('serial_number', null);
        }
    },

    period : function(frm) {
        set_end_date(frm);
    },

    start_date : function(frm) {
        set_end_date(frm);
    }
});

function breach_contract(frm) {
    frappe.confirm(
        "You are about to breach the SLA. Are you sure that you wish to proceed?",
        () => {
            frappe.run_serially([
                () => frm.set_value('status', 'Breached'),
                () => frm.save_or_update(),
                () => frappe.show_alert("Contract breached.", 10),
            ]);
        },
        () => {
            frappe.show_alert("Contract not breached.", 10);
        }
    );
}

function customer_filter(frm) {
    frm.fields_dict.customer.get_query = function() {
        return {
            filters : [
                ['Customer', 'default_currency', '=', frappe.defaults.get_global_default('currency')]
            ]
        }
    }
}

function model_filter(frm) {
    frm.fields_dict.model.get_query = function() {
        return {
            filters : [
                ['Item', 'item_group', 'like', '%Hardware'],
                ['Item', 'has_serial_no', '=', 1]
            ]
        }
    }
}

function serial_filter(frm) {
    frm.fields_dict.serial_number.get_query = function() {
        return {
            filters : [
                ['Serial No', 'item_code', '=', frm.doc.model]
            ]
        }
    }
}

function set_end_date(frm) {
    frm.set_value('end_date', frappe.datetime.add_months(frm.doc.start_date, frm.doc.period));
}

function set_status(frm) {
    if (frappe.datetime.now_date() < frm.doc.start_date) {
        frm.set_value('status', 'Inactive');
    } else if (frappe.datetime.now_date() >= frm.doc.start_date && frappe.datetime.now_date() <= frm.doc.end_date) {
        frm.set_value('status', 'Active');
    } else {
        frm.set_value('status', 'Expired');
    }
}

function terms_filter(frm) {
    frm.fields_dict.cp_name.get_query = function() {
        return {
            filters : [
                ['Terms and Conditions', 'name', 'like', '%Cover Page'],
                ['Terms and Conditions', 'sla', '=', 1],
                ['Terms and Conditions', 'sla_level', '=', frm.doc.contract_tier],
            ]
        }
    }
    frm.fields_dict.tc_name.get_query = function() {
        return {
            filters : [
                ['Terms and Conditions', 'name', 'not like', '%Cover Page'],
                ['Terms and Conditions', 'sla', '=', 1],
                ['Terms and Conditions', 'sla_level', '=', frm.doc.contract_tier],
            ]
        }
    }
}