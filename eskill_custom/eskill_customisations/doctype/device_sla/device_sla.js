// Copyright (c) 2021, Eskill Trading and contributors
// For license information, please see license.txt


frappe.form.link_formatters['Customer'] = (value, doc) => {
    if (value && doc.customer_name && (doc.customer_name != value)) {
        return value + ": " + doc.customer_name;
    } else {
        return value;
    }
}


frappe.form.link_formatters['Item'] = (value, doc) => {
    if (value) {
        if (doc.part_name && doc.part_name != value) {
            return value + ": " + doc.part_name;
        } else if (doc.model_name && doc.model_name != value) {
            return value + ": " + doc.model_name;
        } else {
            return value;
        }
    }
}


frappe.form.link_formatters['Serial No'] = (value, doc) => {
    if (doc.doctype == "Service Device" && value) {
        if (doc.warranty_status) {
            return value + ": " + doc.warranty_status;
        } else {
            return value + ": Warranty Unknown";
        }
    } else {
        return value;
    }
}


frappe.ui.form.on('Device SLA', {
    refresh(frm) {
        customer_filter(frm);
        model_filter(frm);
        serial_filter(frm);
        set_end_date(frm);
        terms_filter(frm);
        frm.fields_dict.devices.grid.get_docfield("add_counter_readings").hidden = 1
        frm.fields_dict.devices.grid.get_docfield("warranty_date_update").hidden = 1
        frm.fields_dict.devices.grid.get_docfield("warranty_swap_out_section").hidden = 1
        frm.fields_dict.devices.grid.grid_rows.forEach( (device) => {
            device.docfields[device.docfields.findIndex( (field) => {
                return field.fieldname == "add_counter_readings"
            })].hidden = 1;
            device.docfields[device.docfields.findIndex( (field) => {
                return field.fieldname == "warranty_date_update"
            })].hidden = 1;
            device.docfields[device.docfields.findIndex( (field) => {
                return field.fieldname == "warranty_swap_out_section"
            })].hidden = 1;
        });
        frm.refresh_field("devices");
    },

    after_save(frm) {
        frm.reload_doc();
    },

    before_submit(frm) {
        set_status(frm);
    },

    breach(frm) {
        breach_contract(frm);
    },

    model(frm) {
        if (!frm.doc.model) {
            frm.set_value('serial_number', null);
        }
    },

    period(frm) {
        set_end_date(frm);
    },

    start_date(frm) {
        set_end_date(frm);
    }
});


frappe.ui.form.on('Service Device', {
    before_devices_remove(frm, cdt, cdn) {
        if (!frappe.user_roles.includes("Support Manager") && locals[cdt][cdn].model) {
            frappe.throw("Please contact a support manager if you wish to remove a device from this issue.");
        }
    },
    
    model(frm, cdt, cdn) {
        if (locals[cdt][cdn].serial_number) {
            locals[cdt][cdn].serial_number = undefined;
            locals[cdt][cdn].warranty_status = undefined;
        }
        if (locals[cdt][cdn].model) {
            serial_filter(frm, cdn);
        } else {
            locals[cdt][cdn].model_name = undefined;
        }
        frm.refresh_fields();
    },
    
    serial_no_report(frm, cdt, cdn) {
        serial_report(locals[cdt][cdn].serial_number);
    },
    
    serial_number(frm, cdt, cdn) {
        if (!locals[cdt][cdn].serial_number) {
            locals[cdt][cdn].warranty_status = undefined;
        } else {
            var duplicate_found = false;
            frm.fields_dict.devices.grid.grid_rows.forEach( (device) => {
                if (device.doc.name != cdn && device.doc.serial_number == locals[cdt][cdn].serial_number) {
                    duplicate_found = true;
                }
            });
            if (duplicate_found) {
                frappe.msgprint(locals[cdt][cdn].serial_number + " is a duplicate serial number.");
                locals[cdt][cdn].serial_number = undefined;
            }
        }
    },

    warranty_date_update(frm, cdt, cdn) {
        warranty_update(frm, locals[cdt][cdn].model, locals[cdt][cdn].serial_number);
    },
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
    frm.fields_dict.devices.grid.fields_map.model.get_query = function() {
        return {
            filters : [
                ['Item', 'has_serial_no', '=', 1]
            ]
        }
    }
}


function serial_filter(frm, devices_row) {
    if (devices_row) {
        frm.fields_dict.devices.grid.grid_rows_by_docname[devices_row].get_field('serial_number').get_query = function() {
            return {
                filters: {
                    'item_code': locals['Service Device'][devices_row].model
                }
            }
        }
    } else {
        var serial_field = frm.fields_dict.devices.grid.get_docfield("serial_number").idx - 1
        frm.fields_dict.devices.grid.grid_rows.forEach( (row) => {
            frm.fields_dict.devices.grid.grid_rows_by_docname[row.doc.name].docfields[serial_field].get_query = function() {
                return {
                    filters: {
                        'item_code': row.doc.model
                    }
                }
            }
        });
    }
    frm.refresh_fields();
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
