// Copyright (c) 2021, Eskill Trading and contributors
// For license information, please see license.txt


frappe.require([
    '/assets/eskill_custom/js/common.js',
    '/assets/eskill_custom/js/selling.js'
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
            return value;
        }
    }
}


frappe.form.link_formatters['Material Request'] = (value, doc) => {
    if (value) {
        return value + ": " + doc.status;
    } else {
        return doc.status;
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


frappe.ui.form.on('Service Order', {
    refresh(frm) {
        set_breadcrumbs(frm);
        if (frm.doc.docstatus == 1) {
            if (!frm.doc.parts_returned && frm.doc.items.length) {
                request_parts(frm);
                receive_parts(frm);
                return_unused_parts(frm);
            }
            generate_quote(frm);
            if (frm.doc.parts_returned && frm.doc.job_status == "Closed") {
                generate_delivery(frm);
            }
            update_job_status(frm);
            if (frm.doc.job_status != "Closed" && (frappe.user_roles.includes("Support Manager") || frappe.user_roles.includes("System Manager"))) {
                update_job_type(frm);
            }
        } else {
            customer_filter(frm);
        }
        limit_devices_table(frm);
        limit_editing_readings_table(frm);
        model_filter(frm);
        serial_filter(frm);
        sla_filter(frm);
        warehouse_filter(frm);
    },

    before_save(frm) {
        if(frm.doc.edit_start_date) {
            frm.set_value("edit_start_date", 0)
        }
    },

    after_save(frm) {
        frm.reload_doc();
    },

    before_submit(frm) {
        frm.set_value("job_status", "Open");
        if (frm.doc.sla) {
            frappe.confirm(
                'You have selected an SLA for this service order, would you like to set job as "SLA" type?',
                () => {
                    frm.set_value("job_type", "SLA");
                }
            );
        }
    },

    customer(frm) {
        if (frm.doc.sla) {
            frm.set_value("sla", null);
        }
        if (frm.doc.customer) {
            frappe.db.get_value("Customer", frm.doc.customer, "main_account").then(
                (response) => {
                    let main_account = response.message.main_account;
                    if (main_account) {
                        frm.set_value("customer_main_account", main_account);
                    } else {
                        frm.set_value("customer_main_account", frm.doc.customer);
                    }
                }
            );
        } else {
            frm.set_value("customer_main_account", undefined);
        }
    },

    sla(frm) {
        if (frm.doc.sla) {
            frappe.run_serially([
                () => get_sla_devices(frm),
                () => {
                    frappe.confirm(
                        "You have selected an SLA for this job. Will the job be covered under the SLA?",
                        () => {
                            frm.set_value("job_type", "SLA");
                        },
                        () => {
                            if (frm.doc.job_type != "Billable") {
                                frm.set_value("job_type", "Billable");
                            }
                        }
                    )
                }
            ])
        } else {
            if (frm.doc.job_type == "SLA") {
                frm.set_value("job_type", "Billable");
            }
        }
        limit_devices_table(frm);
    },

    search(frm) {
        stock_lookup(frm);
    },
});


frappe.ui.form.on('Service Device', {
    devices_add(frm, cdt, cdn) {
        if (frm.doc.sla) {
            frm.fields_dict.devices.grid.grid_rows_by_docname[cdn].remove();
            frappe.msgprint("You can not add a device when SLA is selected.");
        } else {
            frm.fields_dict.devices.grid.grid_rows_by_docname[cdn].docfields[frm.fields_dict.devices.grid.grid_rows_by_docname[cdn].docfields.findIndex( (field) => {
                return field.fieldname == "add_counter_readings"
            })].hidden = 1;
        }
    },

    before_devices_remove(frm, cdt, cdn) {
        if (!frappe.user_roles.includes("Support Manager") && locals[cdt][cdn].model) {
            frappe.throw("Please contact a support manager if you wish to remove a device from this issue.");
        }
    },

    add_counter_readings(frm, cdt, cdn) {
        add_device_readings(frm, cdn, locals[cdt][cdn].serial_number);
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
    
    request_swap_out: function(frm, cdt, cdn) {
       request_swap(frm, locals[cdt][cdn]);
    },

});


frappe.ui.form.on('Device Reading', {
    delete_entry(frm, cdt, cdn) {
        console.log(locals[cdt][cdn])
    }, 
});


frappe.ui.form.on('Part List', {
    before_items_remove(frm, cdt, cdn) {
        if (locals[cdt][cdn].status != "Not Requested") {
            frappe.throw("You can not delete " + cdt + " " + cdn)
        }
    }, 
});


function add_device_readings(frm, device, serial_number) {
    frappe.prompt({
        label: "Number of Records",
        fieldname: "qty",
        fieldtype: "Int",
        default: 1
    }, (values) => {
        for (let i = 0; i < values.qty; i++) {
            frm.add_child("device_reading", {
                serial_number: serial_number,
                service_device: device
            });
        }
        frm.refresh_field("device_reading");
    });
}


function customer_filter(frm) {
    frm.fields_dict.customer.get_query = function() {
        return {
            filters: [
                ["Customer", "disabled", "=", 0]
            ]
        };
    };
}


function generate_delivery(frm) {
    frm.add_custom_button("Delivery Note", () => {
        frappe.model.open_mapped_doc({
            method: "eskill_custom.eskill_customisations.doctype.service_order.service_order.generate_delivery",
            frm: frm,
        });
    }, "Billing");
}


function generate_quote(frm) {
    if (frm.doc.job_type == "Billable" && frm.doc.billing_status == "Pending Billing") {
        frm.add_custom_button("Quotation", () => {
            frappe.model.open_mapped_doc({
                method: "eskill_custom.eskill_customisations.doctype.service_order.service_order.generate_quote",
                frm: frm,
            });
        }, "Billing");
    }
}


function get_sla_devices(frm) {
    if (frm.doc.devices.length) {
        frm.clear_table("devices");
        frm.refresh_field("devices");
    }
    frappe.call({
        doc: frm.doc,
        method: "get_sla_devices",
        callback: (response) => {
            const table_data = JSON.parse(JSON.stringify(response.message));
            const table_fields = [
                {
                    fieldname: "model",
                    fieldtype: "Link",
                    in_list_view: 1,
                    label: "Model",
                    options: "Item",
                },
                {
                    fieldname: "serial_number",
                    fieldtype: "Link",
                    in_list_view: 1,
                    label: "Serial Number",
                    options: "Serial No",
                }
            ];
            const dialog = new frappe.ui.Dialog({
                title: __("Devices on SLA"),
                static: true,
                fields: [
                    {
                        cannot_add_rows: true,
                        data: table_data,
                        description: "Please select all devices that are to be serviced on this order.",
                        fieldname: "devices",
                        fields: table_fields,
                        fieldtype: "Table",
                        in_place_edit: true,
                    }
                ],
                primary_action: () => {
                    console.log(response.message);
                    dialog.fields_dict.devices.grid.get_selected_children().forEach( (device) => {
                        frm.add_child("devices", {
                            model: response.message[device.row_number].model,
                            model_name: response.message[device.row_number].model_name,
                            serial_number: response.message[device.row_number].serial_number
                        });
                    });
                    frm.set_df_property("devices", "cannot_add_rows", 1);
                    frm.refresh_field("devices");
                    dialog.hide();
                },
                primary_action_label: "Select"
            });
            dialog.show();
        }
    });
}


function limit_devices_table(frm) {
    if (frm.doc.sla) {
        frm.set_df_property("devices", "cannot_add_rows", 1);
        frm.fields_dict.devices.grid.get_docfield("model").read_only = 1;
        frm.fields_dict.devices.grid.update_docfield_property("model", "read_only", 1);
        frm.fields_dict.devices.grid.get_docfield("serial_number").read_only = 1;
        frm.fields_dict.devices.grid.update_docfield_property("serial_number", "read_only", 1);
        if (!frm.doc.docstatus) {
            frm.fields_dict.devices.grid.add_custom_button("Add Rows", () => {
                get_sla_devices(frm);
            });
        }
    } else {
        frm.set_df_property("devices", "cannot_add_rows", 0);
        frm.fields_dict.devices.grid.get_docfield("model").read_only = 0;
        frm.fields_dict.devices.grid.update_docfield_property("model", "read_only", 0);
        frm.fields_dict.devices.grid.get_docfield("serial_number").read_only = 0;
        frm.fields_dict.devices.grid.update_docfield_property("serial_number", "read_only", 0);

    }
}


function limit_editing_readings_table(frm) {
    frm.set_df_property("device_reading", "cannot_add_rows", 1);
    frm.refresh_field("device_reading");
}


function model_filter(frm) {
    frm.fields_dict.devices.grid.fields_map.model.get_query = function() {
        return {
            filters: [
                ["Item", "has_serial_no", "=", 1]
            ]
        };
    };
}


function receive_parts(frm) {
    if (frm.doc.job_status == "Open" && frm.doc.items) {
        frm.add_custom_button("Receive Parts", () => {
            if (frm.is_dirty()) {
                frappe.throw("Please save before receiving parts.");
            }
            frappe.call({
                doc: frm.doc,
                method: "parts_receipt",
                callback: (response) => {
                    if (response.message.receive) {
                        response.message.receipts.forEach((part) => {
                            var dialog = new frappe.ui.Dialog({
                                title: __("Receive " + part[0]),
                                fields: [
                                    {
                                        label: "Part",
                                        fieldname: "part",
                                        fieldtype: "Link",
                                        read_only: 1,
                                        options: "Item",
                                        default: part[0]
                                    },
                                    {
                                        fieldname: "part_list",
                                        fieldtype: "Data",
                                        default: part[5],
                                        hidden: 1
                                    },
                                    {
                                        fieldname: "column_break_1",
                                        fieldtype: "Column Break"
                                    },
                                    {
                                        label: "Part Name",
                                        fieldname: "part_name",
                                        fieldtype: "Data",
                                        default: part[1],
                                        read_only: 1
                                    },
                                    {
                                        fieldname: "section_break_1",
                                        fieldtype: "Section Break"
                                    },
                                    {
                                        label: "Requested Qty",
                                        fieldname: "qty",
                                        fieldtype: "Data",
                                        default: part[2],
                                        read_only: 1
                                    },
                                    {
                                        label: "Parts Released So Far",
                                        fieldname: "released",
                                        fieldtype: "Data",
                                        default: part[3],
                                        read_only: 1
                                    },
                                    {
                                        label: "Parts Received So Far",
                                        fieldname: "received",
                                        fieldtype: "Data",
                                        default: part[4] ? part[4] : "0",
                                        read_only: 1
                                    },
                                    {
                                        fieldname: "column_break_4",
                                        fieldtype: "Column Break"
                                    },
                                    {
                                        label: "New Parts Accepted",
                                        fieldname: "accepted",
                                        fieldtype: "Float",
                                        reqd: 1,
                                        onchange: () => {
                                            const max_value = dialog.fields_dict.released.value - dialog.fields_dict.received.value
                                            if ((dialog.fields_dict.accepted.value > max_value) || (dialog.fields_dict.accepted.value < 0)) {
                                                dialog.set_value('accepted', 0);
                                                frappe.msgprint({
                                                    title: "Invalid Value",
                                                    message: max_value == 1 ? "There is 1 to be accepted." : "There are " + max_value + " to be accepted."
                                                });
                                            }
                                        }
                                    }
                                ],
                                primary_action: (receipt) => {
                                    if (receipt.accepted) {
                                        frappe.call({
                                            doc: frm.doc,
                                            method: "receive_part",
                                            args: {
                                                part: receipt.part_list,
                                                received: receipt.accepted
                                            },
                                            callback: () => {
                                                frm.reload_doc();
                                            }
                                        });
                                    }
                                    dialog.hide();
                                },
                                primary_action_label: "Receive"
                            });
                            dialog.show();
                        });
                    }
                }
            });
        }, "Parts");
    }
}


function request_parts(frm) {
    if (frm.doc.job_status == "Open" && frm.doc.items) {
        frm.add_custom_button("Request Parts", () => {
            if (frm.is_dirty()) {
                frappe.throw("Please save before requesting parts.");
            }
            frappe.call({
                doc: frm.doc,
                method: "parts_request",
                callback: function(response) {
                    frappe.msgprint(response.message);
                    frm.reload_doc();
                }
            });
        }, "Parts");
    }
}


function request_swap(frm, device) {
    if (frm.is_dirty()) {
        frm.save();
    }
    var swap_out = frappe.model.get_new_doc("Warranty Swap Out");
    swap_out.service_order = frm.doc.name;
    swap_out.service_device = device.name;
    swap_out.model_in = device.model;
    swap_out.serial_no_in = device.serial_number;
    frappe.db.insert(swap_out).then(function(doc) {
        frappe.set_route("Form", "Warranty Swap Out", doc.name);
    });
}


function return_unused_parts(frm) {
    frm.add_custom_button("Return Unused Parts", () => {
        if (!frm.is_dirty()) {
            frappe.call({
                doc: frm.doc,
                method: "return_parts_table",
                callback: (response) => {
                    const table_fields = [
                        {
                            fieldname: "part_list",
                            fieldtype: "Link",
                            options: "Part List",
                            hidden: 1
                        },
                        {
                            fieldname: "part",
                            fieldtype: "Link",
                            options: "Item",
                            label: "Part",
                            in_list_view: 1,
                        },
                        {
                            fieldname: "warehouse",
                            fieldtype: "Link",
                            options: "Warehouse",
                            label: "Warehouse",
                            in_list_view: 1,
                        },
                        {
                            fieldname: "qty",
                            fieldtype: "Float",
                            label: "Requested",
                            in_list_view: 1,
                        },
                        {
                            fieldname: "received_qty",
                            fieldtype: "Float",
                            label: "Received",
                            in_list_view: 1,
                        },
                        {
                            fieldname: "used_qty",
                            fieldtype: "Float",
                            label: "Used",
                            in_list_view: 1,
                        },
                    ];
                    var dialog = new frappe.ui.Dialog({
                        title: __("Return Unused Parts"),
                        static: true,
                        fields: [
                            {
                                fieldname: "disclaimer",
                                fieldtype: "Data",
                                read_only: 1,
                                default: "All unused parts will be returned to Stores, therefore will be unavailable for billing."
                            },
                            {
                                fieldname: "part_quantities",
                                fieldtype: "Table",
                                label: "Part Quantities",
                                cannot_add_rows: true,
                                in_place_edit: false,
                                read_only: 1,
                                data: response.message,
                                fields: table_fields,
                                description: "Please enter quantities used for each line item."
                            }
                        ],
                        primary_action: function() {
                            dialog.hide();
                            var used_parts = {}
                            dialog.fields[1].data.forEach( (row) => {
                                if (row.used_qty) {
                                    if ((row.used_qty > response.message[row.idx - 1].received_qty) || (row.used_qty < 0)) {
                                        console.log(row, response.message)
                                        frappe.throw("You can not have used " + row.used_qty + " " + response.message[row.idx - 1].part + ".");
                                    } else {
                                        used_parts[row.part_list] = row.used_qty;
                                    }
                                }
                            });
                            frappe.call({
                                doc: frm.doc,
                                method: "return_parts",
                                args: {
                                    used_parts: used_parts
                                },
                                callback: (response2) => {
                                    frm.reload_doc();
                                }
                            });
                        },
                        primary_action_label: "Return"
                    });
                    dialog.fields_dict.part_quantities.grid.wrapper.find('.btn-open-row').hide();
                    dialog.fields_dict.part_quantities.grid.wrapper.find('.edit-grid-row').hide();
                    dialog.fields_dict.part_quantities.grid.wrapper.find('.sortable-handle').hide();
                    dialog.show();
                }
            });
        } else {
            frappe.msgprint("Please save before returning parts.");
        }
    }, "Parts");
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
}


function serial_report(s_number) {
    if (s_number) {
        window.open(window.location.origin + "/api/method/frappe.utils.print_format.download_pdf?doctype=Serial No&name=" + s_number + "&format=Eskill Serial Number History");
    } else {
        frappe.msgprint("No serial number.");
    }
}


function set_breadcrumbs(frm) {
    frappe.breadcrumbs.clear();
    frappe.breadcrumbs.set_custom_breadcrumbs({
        route: "/app/support",
        label: "Support"
    });
    frappe.breadcrumbs.set_custom_breadcrumbs({
        route: "/app/service-order",
        label: "Service Order"
    });
    frappe.breadcrumbs.set_form_breadcrumb({
        doctype: frm.doc.doctype
    }, "form");
}


function sla_filter(frm) {
    frm.fields_dict.sla.get_query = function() {
        return {
            filters: {
                customer: frm.doc.customer_main_account,
                docstatus: 1,
                status: "Active"
            }
        }
    }
}


function update_job_status(frm) {
    if (frm.doc.job_status == "Open") {
        frm.add_custom_button("Put On Hold", () => {
            set_status(frm, "On Hold");
        }, "Job Status");
        frm.add_custom_button("Close Job", () => {
            if (!frm.doc.parts_returned && frm.doc.items.length) {
                frappe.throw(__("You must return all unused parts before closing the job."));
            } else {
                set_status(frm, "Closed");
            }
        }, "Job Status");
    } else {
        frm.add_custom_button("Re-Open Job", () => {
            set_status(frm, "Open");
        });
    }

    function set_status(frm, status) {
        if (status == "On Hold") {
            frappe.prompt([
                {
                    label: "Reason on Hold",
                    fieldname: "reason_on_hold",
                    fieldtype: "Link",
                    options: "Service Order On Hold Type",
                    description: "Please select a reason for the job being put on hold.",
                    reqd: 1
                }
            ], (values) => {
                frappe.call({
                    doc: frm.doc,
                    method: "set_job_status",
                    args: {
                        status: status,
                        reason: values.reason_on_hold
                    },
                    callback: () => {
                        frm.reload_doc();
                    }
                });
            });
        } else {
            frappe.call({
                doc: frm.doc,
                method: "set_job_status",
                args: {
                    status: status
                },
                callback: () => {
                    frm.reload_doc();
                }
            });
        }
    }
}


function update_job_type(frm) {
    if (frm.doc.job_type == "Billable") {
        frm.add_custom_button("SLA", () => {
            set_type(frm, "SLA");
        }, "Job Type");
        frm.add_custom_button("Warranty", () => {
            set_type(frm, "Warranty");
        }, "Job Type");
    } else if (frm.doc.job_type == "SLA") {
        frm.add_custom_button("Billable", () => {
            set_type(frm, "Billable");
        }, "Job Type");
        frm.add_custom_button("Warranty", () => {
            set_type(frm, "Warranty");
        }, "Job Type");
    } else {
        frm.add_custom_button("Billable", () => {
            set_type(frm, "Billable");
        }, "Job Type");
        frm.add_custom_button("SLA", () => {
            set_type(frm, "SLA");
        }, "Job Type");
    }

    function set_type(frm, job_type) {
        frappe.call({
            doc: frm.doc,
            method: "set_job_type",
            args: {
                job_type: job_type
            },
            callback: () => {
                frm.reload_doc();
            }
        });
    }
}


function warehouse_filter(frm) {
    frm.fields_dict.items.grid.fields_map.warehouse.get_query = function() {
        return {
            filters: [
                ["Warehouse", "warehouse_type", "=", "Technician"]
            ]
        };
    };
}


function warranty_update(frm, model, serial_number) {
    check_save(frm);
    var warranty_get, item_warranty;
    frappe.run_serially([
        () => warranty_get = frappe.db.get_value("Item", model, "warranty_period"),
        () => item_warranty = warranty_get.responseJSON.message.warranty_period,
        () => frappe.prompt([
            {
                label: "Date of Purchase",
                fieldname: "purchase_date",
                fieldtype: "Date",
                description: "From dealer",
                reqd: 1
            },
            {
                label: "Warranty Period(Days)",
                fieldname: "warranty_period",
                fieldtype: "Int",
                default: item_warranty
            },
        ], (values) => {
            frappe.call({
                doc: frm.doc,
                method: "warranty_update",
                args: {
                    serial_number: serial_number,
                    owned_by: frm.doc.customer,
                    purchase_date: values.purchase_date || false,
                    warranty_period: values.warranty_period || 0
                },
                callback: (response) => {
                    frm.reload_doc();
                    frappe.msgprint(response.message);
                }
            });
        }),
    ]);
}
