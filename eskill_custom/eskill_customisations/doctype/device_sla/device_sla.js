// Copyright (c) 2021, Eskill Trading and contributors
// For license information, please see license.txt

frappe.require([
    "/assets/eskill_custom/js/qr_code_generation.js"
]);


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
            return value + ": " + doc.item_name;
        }
    }
}


frappe.ui.form.on('Device SLA', {
    refresh(frm) {
        customer_filter(frm);
        model_filter(frm);
        serial_filter(frm);
        terms_filter(frm);
        update_readings(frm);
        process_billing(frm);
        renew_sla(frm);
        frm.get_field("readings").grid.cannot_add_rows = true;
        frm.refresh_field("readings");
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

    add_counter_readings(frm, cdt, cdn) {
        add_device_readings(frm, cdn, locals[cdt][cdn].serial_number);
    },

    generate_serial_no_qr(frm, cdt, cdn) {
        generate_serial_history_qr(locals[cdt][cdn].serial_number);
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
});

frappe.ui.form.on('SLA Device Reading', {
    initial_reading(frm, cdt, cdn) {
        locals[cdt][cdn].previous_reading = locals[cdt][cdn].initial_reading
        locals[cdt][cdn].current_reading = locals[cdt][cdn].initial_reading
        frm.refresh_fields();
    }
});

frappe.ui.form.on('SLA Additional Billing Items', {
    item_code(frm, cdt, cdn) {
        locals[cdt][cdn].item_name = null;        
        locals[cdt][cdn].description = null;
        frm.refresh_fields();
    },

    qty(frm, cdt, cdn) {
        if (locals[cdt][cdn].qty && locals[cdt][cdn].rate) {
            locals[cdt][cdn].amount = locals[cdt][cdn].qty * locals[cdt][cdn].rate;
            frm.refresh_fields();
        }
    },

    rate(frm, cdt, cdn) {
        if (locals[cdt][cdn].qty && locals[cdt][cdn].rate) {
            locals[cdt][cdn].amount = locals[cdt][cdn].qty * locals[cdt][cdn].rate;
            frm.refresh_fields();
        }
    },
});

frappe.ui.form.on('SLA Renewals', {
    view_letter(frm, cdt, cdn) {
        window.open(window.location.origin + locals[cdt][cdn].renewal_letter);
    }
});

function add_device_readings(frm, device, serial_number) {
    frappe.prompt({
        label: "Number of Records",
        fieldname: "qty",
        fieldtype: "Int",
        default: 1
    }, (values) => {
        for (let i = 0; i < values.qty; i++) {
            frm.add_child("readings", {
                serial_number: serial_number,
                service_device: device
            });
        }
        frm.refresh_field("readings");
    });
}

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
    frm.get_field("devices").grid.fields_map.model.get_query = function() {
        return {
            filters : [
                ['Item', 'has_serial_no', '=', 1]
            ]
        }
    }
}

function process_billing(frm) {
    frm.add_custom_button(__("Process Billing"), () => {
        if (!frm.doc.current_readings_invoiced) {
            frappe.model.open_mapped_doc({
                method: "eskill_custom.eskill_customisations.doctype.device_sla.device_sla.make_delivery_note",
                frm: frm,
            });
        }
    });
}

function renew_sla(frm) {
    if (frm.doc.docstatus == 1
        && ["Active", "Expired"].includes(frm.doc.status)
        && frappe.datetime.get_today() > frappe.datetime.add_months(frm.doc.end_date, -1)) {
        frm.add_custom_button(__("Renew SLA"), () => {
            frappe.prompt(
                [
                    {
                        fieldname: "renewal_letter",
                        label: __("Renewal Letter"),
                        fieldtype: "Attach",
                        reqd: 1
                    },
                    {
                        fieldname: "start_date",
                        label: __("Renewal Date"),
                        fieldtype: "Date",
                        default: "Today",
                        reqd: 1
                    },
                    {
                        fieldname: "period",
                        label: __("New Contract Period"),
                        fieldtype: "Int",
                        description: "The new contract period defined in months.",
                        reqd: 1,
                    },
                ], (values) => {
                    if (values.start_date < frm.doc.end_date) {
                        frappe.throw(__("The renewed start date can not precede the current end date of the contract."));
                    }

                    if (values.period < 1) {
                        frappe.throw(__("The minimum allowable period is 1 month."));
                    }

                    var renewal = {
                        renewal_letter: values.renewal_letter,
                        start_date: values.start_date,
                        period: values.period,
                        end_date: frappe.datetime.add_months(values.start_date, values.period)
                    };

                    if (renewal.end_date <= frappe.datetime.get_today()) {
                        frappe.throw(__("The new end date can be ealier than today's date."));
                    }

                    frm.add_child("sla_renewals", renewal);
                    frm.set_value("end_date", renewal.end_date);

                    if (frappe.datetime.get_today() <= renewal.end_date) {
                        frm.set_value("status", "Active");
                    }

                    frm.refresh_fields();
                }
            );
        });
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
    frm.set_value('initial_end_date', frappe.datetime.add_months(frm.doc.start_date, frm.doc.period));
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

function update_readings(frm) {
    if (frm.doc.readings.length > 0) {
        frm.add_custom_button(__("Update Readings"), () => {
            frappe.call({
                method: "update_readings",
                doc: frm.doc,
                callback: () => {
                    frm.reload_doc();
                }
            });
        });
    }
}
