frappe.require([
    '/assets/eskill_custom/js/common.js',
    '/assets/eskill_custom/js/selling.js'
]);

frappe.ui.form.on('Issue', {
    refresh(frm) {
        frm.clear_custom_buttons();
        var exclusion_list = [
            "resolution_details",
            "opening_date",
            "opening_time",
            "resolution_date"
        ];
        frm.fields.forEach( function(field) {
            if (exclusion_list.includes(field.df.fieldname)) {
                frm.set_df_property(field.df.fieldname, "read_only", 0);
            }
        });
        if (frm.doc.status == "Closed") {
            if (frappe.user_roles.includes("Support Manager")) {
                frm.add_custom_button(__("Reopen"), function() {
                    frm.set_value("status", "Open");
                    frm.save();
                });
            }
            frm.fields.forEach( function(field) {
                if (!exclusion_list.includes(field.df.fieldname)) {
                    frm.set_df_property(field.df.fieldname, "read_only", 1);
                }
            });
        } else {
            frm.add_custom_button(__("Close"), function() {
                frm.set_value("status", "Closed");
                frm.save();
            });
        }
        frm.add_custom_button(__("KB Articles"), function() {
            check_save(frm);
            frappe.route_options = {
                "area": "Technical",
                "type": "Product",
                "product": frm.doc.model
            };
            frappe.set_route("List", "KBA");
        });
        frm.add_custom_button(__("Timesheets"), function() {
            check_save(frm);
            frappe.set_route("List", "Timesheet");
        });
        if (!frm.doc.warranty_job && !frm.doc.sla_job && !frm.doc.delivery_note) {
                frm.add_custom_button(__("Quotation"), function() {
                    create_quote(frm);
                }, "Billing");
        }
        if (frm.doc.status == "Closed" && (!frm.doc.delivery_note || frm.doc.delivery_note_status == "Cancelled") && (frm.doc.quotation  || ((frm.doc.warranty_job || frm.doc.sla_job)))) {
            frm.add_custom_button(__("Delivery Note"), function() {
                create_delivery(frm);
            }, "Billing");
        }
        if (frm.doc.status != "Closed") {
            frm.add_custom_button(__("Parts Request"), function() {
                check_save(frm);
                var parts_requested = 0;
                if (frm.doc.part_list) {
                    const request = frappe.model.get_new_doc("Material Request");
                    request.naming_series = "MAT-MR-.YYYY.-";
                    request.schedule_date = frappe.datetime.nowdate();
                    request.transaction_date = frappe.datetime.nowdate();
                    request.material_request_type = "Material Transfer";
                    request.company = "Eskill Trading (Pvt) Ltd";
                    request.requested_by = frappe.session.user;
                    request.issue = frm.doc.name;
                    request.docstatus = 1;
                    request.status = "Submitted";
                    frm.doc.part_list.forEach(function(row) {
                        if (row.status == "Not Requested") {
                            parts_requested++;
                            var part = frappe.model.add_child(request, "Material Request Item", "items");
                            part.item_code = row.part;
                            part.qty = row.qty;
                            part.description = row.description;
                            part.schedule_date = request.schedule_date;
                            part.uom = row.uom;
                            part.stock_uom = row.uom;
                            part.warehouse = row.warehouse;
                            part.conversion_factor = 1;
                        }
                    });
                    if (parts_requested) {
                        frappe.db.insert(request).then(function(doc) {
                            const new_request = doc.name;
                            frm.doc.part_list.forEach(function(row) {
                                if (row.status == "Not Requested") {
                                    row.status = "Requested";
                                    row.request = new_request;
                                }
                            });
                            check_save(frm);
                        });
                    } else {
                        frappe.msgprint("No parts to request.");
                    }
                } else {
                    frappe.msgprint("Populate parts list to request items.");
                }
            });
            if (frm.doc.model) {
                serial_filter(frm, frm.doc.model, frm.fields_dict.serial_number);
            }
            frm.get_field("part_list").grid.fields_map.warehouse.get_query = function() {
                return {
                    filters: {
                        'disabled': 0,
                        'warehouse_type': 'Technician'
                    }
                };
            };
            model_filter(frm);
            if (frm.doc.total_hours != 0) {
                frm.set_df_property("expected_hours", "read_only", 1);
            }
            if (frm.doc.quotation || frm.doc.order || frm.doc.invoice) {
                frm.set_df_property("customer", "read_only", 1);
            }
            labour_filter(frm);
            current_technician_filter(frm);
            stock_item_filter(frm);
            if (frm.doc.swap_out) {
                device_read_only(frm);
            }
            single_or_multiple_devices(frm);
            device_list_refresh(frm);
        }
        if (frm.doc.serial_number) {
            serial_status(frm);
        }
        frm.get_field("part_list").grid.grid_rows.forEach(function(row) {
            if (row.doc.status == "Requested") {
                var request = row.doc.request;
                frappe.model.with_doc("Material Request", request, function() {
                    request = frappe.model.get_doc("Material Request", request);
                    var item = request.items[row.doc.row];
                    if (item.ordered_qty == item.stock_qty) {
                        row.doc.status = "Released";
                    }
                });
            }
        });
        frm.refresh_fields();
    },

    before_save: function(frm) {
        if (frm.doc.serial_number && !frm.doc.model) {
            frm.doc.serial_number = undefined;
        }
        if (frm.doc.stock_item) {
            frm.doc.stock_item = undefined;
        }
        if (frm.doc.multiple_devices) {
            device_list_validation_before_save(frm);
        }
        time_worked(frm);
    },
    
    multiple_devices: function(frm) {
        single_or_multiple_devices(frm);
        model_filter(frm);
    },

    serial_number: function(frm) {
        serial_status(frm);
    },

    serial_no_report: function(frm) {
        serial_report(frm, frm.doc.serial_number);
    },

    warranty_date_update: function(frm) {
        warranty_date_update(frm, frm.doc.model, frm.doc.serial_number);
    },

    request_swap_out: function(frm) {
        request_swap(frm, frm.doc.model, frm.doc.serial_number);
    },

    email_account: function(frm) {
        if (frm.doc.email_account == 'Zabbix Internal Issues') {
            frm.set_value("issue_type", "Internal Software Support");
            frm.set_value("priority", "High");
            check_save(frm);
        }
    },

    search: function(frm) {
        if (frm.doc.stock_item) {
            stock_lookup(frm);
        } else {
            frappe.throw("You must select a stocked item before performing a stock lookup.");
        }
    },

    kba_creation: function(frm) {
        check_save(frm);
        frappe.db.insert({
            doctype: 'KBA',
            topic: frm.doc.subject,
            area: 'Technical',
            type: 'Product',
            product: frm.doc.model,
            details: frm.doc.resolution_details,
            parent_kba: 'KBA-20-Other-00000036'
        });
        frappe.msgprint("KBA created.");
    },

    model: function(frm) {
        serial_filter(frm, frm.doc.model, frm.fields_dict.serial_number);
    },

    service_level_agreement: function(frm) {
        if (frm.doc.service_level_agreement) {
            frm.set_value('sla_job', 1);
        } else {
            frm.set_value('sla_job', 0);
        }
    },

    swap_out: function(frm) {
        if (frm.doc.swap_out) {
            device_read_only(frm);
        }
    },
});

frappe.ui.form.on('Part List', {
    before_part_list_remove: function(frm, cdt, cdn) {
        if (!frappe.user_roles.includes("System Administrator") && locals[cdt][cdn].status != "Not Requested") {
            frappe.throw(__("Unable to delete row {0}. Only a system administrator may remove an entry for a requested part.", [locals[cdt][cdn].idx]));
        }
    },
    
    received_button: function(frm, cdt, cdn) {
        const row = frappe.get_doc(cdt, cdn);
        frm.get_field("part_list").grid.grid_rows[row.idx - 1].doc.status = "Received";
        frm.get_field("part_list").grid.grid_rows[row.idx - 1].refresh_field("status");
        check_save(frm);
    },
});

frappe.ui.form.on('Issue Machines', {
    before_device_list_remove: function(frm, cdt, cdn) {
        if (!frappe.user_roles.includes("Support Manager") && locals[cdt][cdn].model) {
            frappe.throw("Please contact a support manager if you wish to remove a device from this issue.");
        }
    },
    
    model: function(frm, cdt, cdn) {
        if (locals[cdt][cdn].serial_number) {
            locals[cdt][cdn].serial_number = undefined;
        }
        if (locals[cdt][cdn].model) {
            serial_filter(frm, locals[cdt][cdn].model, frm.get_field("device_list").grid.grid_rows_by_docname[cdn].docfields[1]);
        }
        frm.refresh_fields();
    },

    serial_no_report: function(frm, cdt, cdn) {
        serial_report(frm, locals[cdt][cdn].serial_number);
    },

    warranty_date_update: function(frm, cdt, cdn) {
        warranty_date_update(frm, locals[cdt][cdn].model, locals[cdt][cdn].serial_number);
    },
    
    // The following code has been commented out as it is not currently functioning, and is not immediately necessary.
    //
    //request_swap_out: function(frm, cdt, cdn) {
    //    request_swap(frm, locals[cdt][cdn].model, locals[cdt][cdn].serial_number, 1, locals[cdt][cdn]);
    //},

});

function create_quote(frm) {
    check_save(frm);
    if ((frm.doc.expected_hours > 0) || (frm.doc.billable_time > 0)) {
        var quote = frappe.model.get_new_doc("Quotation");
        quote.naming_series = "SQ.########";
        quote.quotation_to = "Customer";
        quote.party_name = frm.doc.customer;
        quote.order_type = "Support";
        quote.company = frappe.user_defaults.company;
        quote.issue = frm.doc.name;
        quote.transaction_date = frappe.datetime.nowdate();
        quote.valid_till = frappe.datetime.add_days(frappe.datetime.nowdate(), 1);
        quote.selling_price_list = frappe.user_defaults.selling_price_list;
        var time = frappe.model.add_child(quote, "Quotation Item", "items");
        var time_value = 1;
        if (frm.doc.billable_time === 0) {
            time_value = Math.ceil(frm.doc.expected_hours);
            time.qty = time_value;
            time.stock_qty = time_value;
            time.conversion_factor = 1;
            frappe.model.with_doc("Item", frm.doc.labour_code, function () {
                const labour = frappe.model.get_doc("Item", frm.doc.labour_code);
                time.item_code = labour.name;
                time.item_name = labour.item_name;
                time.description = labour.description;
                time.uom = labour.stock_uom;
                time.stock_uom = labour.stock_uom;
            });
        } else {
            time_value = Math.ceil(frm.doc.billable_time);
            time.qty = time_value;
            time.stock_qty = time_value;
            time.conversion_factor = 1;
            frappe.model.with_doc("Item", frm.doc.labour_code, function () {
                const labour = frappe.model.get_doc("Item", frm.doc.labour_code);
                time.item_code = labour.name;
                time.item_name = labour.item_name;
                time.description = labour.description;
                time.uom = labour.stock_uom;
                time.stock_uom = labour.stock_uom;
            });
        }
        time_value = undefined;
        if (frm.doc.part_list.length) {
            frm.doc.part_list.forEach(function (row) {
                var part = frappe.model.add_child(quote, "Quotation Item", "items");
                part.item_code = row.part;
                part.item_name = row.part_name;
                part.qty = row.qty;
                part.description = row.description;
                part.uom = row.uom;
                part.stock_uom = row.uom;
                part.conversion_factor = 1;
                part.warehouse = row.warehouse;
            });
        }
        frappe.set_route("Form", "Quotation", quote.name);
    } else {
        frappe.throw("Must have expected job completion time or billable time in order to quote.");
    }
}

function device_list_validation_before_save(frm) {
    frm.doc.device_list.forEach(function(row) {
        if (locals[row.doctype][row.name].serial_number) {
            if (!locals[row.doctype][row.name].model) {
                locals[row.doctype][row.name].serial_number = undefined;
            } else {
                frappe.db.get_value("Serial No", locals[row.doctype][row.name].serial_number, "item_code").then( function(response) {
                    if (response.message.item_code != locals[row.doctype][row.name].model) {
                        locals[row.doctype][row.name].serial_number = undefined;
                    }
                })
            }
        }
    });
}

function model_filter(frm) {
    if (frm.doc.multiple_devices) {
        frm.get_field("device_list").grid.fields_map.model.get_query = function() {
            return {
                filters: [
                    ["Item", "has_serial_no", "=", 1]
                ]
            };
        };
    } else {
        frm.fields_dict.model.get_query = function() {
            return {
                filters: [
                    ["Item", "has_serial_no", "=", 1]
                ]
            };
        };
    }
}

function device_list_refresh(frm) {
    frm.doc.device_list.forEach(function(row) {
        if (locals[row.doctype][row.name].model) {
            serial_filter(frm, locals[row.doctype][row.name].model, frm.get_field("device_list").grid.grid_rows_by_docname[row.name].docfields[1]);
        }
    });
    frm.refresh_fields();
}

function request_swap(frm, model, s_number) {
    check_save(frm).then(function() {
        var swap_out = frappe.model.get_new_doc("Warranty Swap Out");
        swap_out.issue = frm.doc.name;
        swap_out.model_in = model;
        swap_out.serial_no_in = s_number;
        frappe.db.insert(swap_out).then(function(doc) {
            frm.doc.swap_out = doc.name;
            check_save(frm);
            frappe.set_route("Form", "Warranty Swap Out", doc.name);
        });
    });
}

function warranty_date_update(frm, model, s_number) {
    check_save(frm);
    if (s_number) {
        var warranty_get, item_warranty, name_get, customer_name;
        frappe.run_serially([
            () => warranty_get = frappe.db.get_value("Item", model, "warranty_period"),
            () => item_warranty = warranty_get.responseJSON.message.warranty_period,
            () => name_get = frappe.db.get_value("Customer", frm.doc.customer, "customer_name"),
            () => customer_name = name_get.responseJSON.message.customer_name,
            () => frappe.prompt([
                {
                    label: 'Date of Purchase',
                    fieldname: 'purchase_date',
                    fieldtype: 'Date',
                    description: 'From dealer',
                    reqd: true
                },
                {
                    label: 'Warranty Period(Days)',
                    fieldname: 'warranty_period',
                    fieldtype: 'Int',
                    reqd: item_warranty ? false : true
                },
            ], (values) => {
                if (values.warranty_period) {
                    frappe.call({
                        "method": "frappe.client.set_value",
                        "args": {
                            "doctype": "Serial No",
                            "name": s_number,
                            "fieldname": {
                                "customer": frm.doc.customer,
                                "customer_name": customer_name,
                                "warranty_expiry_date": frappe.datetime.add_days(values.purchase_date, values.warranty_period),
                            },
                        }
                    });
                } else if (item_warranty) {
                    frappe.call({
                        "method": "frappe.client.set_value",
                        "args": {
                            "doctype": "Serial No",
                            "name": s_number,
                            "fieldname": {
                                "customer": frm.doc.customer,
                                "customer_name": customer_name,
                                "warranty_expiry_date": frappe.datetime.add_days(values.purchase_date, item_warranty),
                            },
                        }
                    });
                } else {
                    frappe.throw("No warranty period has been defined for the item.");
                }
            }),
        ]);
    } else {
        frappe.msgprint("No serial number.");
    }
}

function current_technician_filter(frm) {
    frm.fields_dict.current_technician.get_query = function() {
        return {
            filters: [
                ["Employee", "status", "=", "Active"]
            ],
        };
    };
}

function create_delivery(frm) {
    check_save(frm);
    var delivery = frappe.model.get_new_doc("Delivery Note");
    delivery.naming_series = "DN.########";
    delivery.posting_date = frappe.datetime.nowdate();
    delivery.company = frappe.user_defaults.company;
    delivery.customer = frm.doc.customer;
    delivery.issue = frm.doc.name;
    if (!frm.doc.sla_job && !frm.doc.warranty_job) {
        frappe.model.with_doc("Quotation", frm.doc.quotation, function() {
            const quote = frappe.model.get_doc("Quotation", frm.doc.quotation);
            delivery.selling_price_list = quote.selling_price_list;
            delivery.currency = quote.currency;
            delivery.conversion_rate = quote.conversion_rate;
            quote.items.forEach(function(quote_item) {
                var note_item = frappe.model.add_child(delivery, "Delivery Note Item", "items");
                note_item.item_code = quote_item.item_code;
                note_item.item_name = quote_item.item_name;
                note_item.description = quote_item.description;
                note_item.qty = quote_item.qty;
                note_item.stock_qty = quote_item.qty;
                note_item.schedule_date = delivery.schedule_date;
                note_item.uom = quote_item.uom;
                note_item.stock_uom = quote_item.uom;
                note_item.conversion_factor = 1;
                note_item.rate = quote_item.rate;
                note_item.warehouse = quote_item.warehouse;
            });
        });
    } else {
        delivery.selling_price_list = frappe.user_defaults.selling_price_list;
        delivery.currency = frappe.user_defaults.currency;
        delivery.sla_issue = frm.doc.sla_job ? 1 : 0;
        delivery.warranty_issue = frm.doc.warranty_job ? 1 : 0;
        // Labour will be put in here when valuation for labour is implemented
        if (frm.doc.part_list.length) {
            frm.doc.part_list.forEach(function (row) {
                if (row.status = "Received") {
                    frappe.call({
                        method: "eskill_custom.api.non_billable_item",
                        args: {
                            item_code: row.part,
                            sla_job: frm.doc.sla_job
                        },
                        callback: function(data) {
                            if (data.message) {
                                if (data.message.valuation && data.message.expense_account) {
                                    var note_item = frappe.model.add_child(delivery, "Delivery Note Item", "items");
                                    note_item.item_code = row.part;
                                    note_item.item_name = row.part_name;
                                    note_item.description = row.description;
                                    note_item.schedule_date = delivery.schedule_date;
                                    note_item.qty = row.qty;
                                    note_item.stock_qty = row.qty;
                                    note_item.uom = row.uom;
                                    note_item.stock_uom = row.uom;
                                    note_item.conversion_factor = 1;
                                    note_item.warehouse = row.warehouse;
                                    note_item.expense_account = data.message.expense_account;
                                    note_item.rate = data.message.valuation;
                                } else {
                                    console.log(data);
                                    frappe.throw("Failed to get valuation rate and expense account for ".concat(row.part));
                                }
                            } else {
                                console.log(data);
                                frappe.throw("Failed to get valuation rate and expense account for ".concat(row.part));
                            }
                        }
                    });
                }
            });
        }
    }
    frappe.set_route("Form", "Delivery Note", delivery.name);
}

function single_or_multiple_devices(frm) {
    if (frm.doc.multiple_devices) {
        frm.set_df_property("device_details", "hidden", 1);
        frm.set_df_property("devices", "hidden", 0);
        frm.doc.model = "";
        frm.doc.serial_number = "";
        frm.refresh_fields();
    } else {
        frm.set_df_property("device_details", "hidden", 0);
        frm.set_df_property("devices", "hidden", 1);
        frm.clear_table("device_list");
        frm.refresh_fields();
    }
}

function labour_filter(frm) {
    frm.fields_dict.labour_code.get_query = function() {
        return {
            filters: [
                ["Item", "item_group", "like", "%Services%"],
                ["Item", "disabled", "=", false],
            ],
        }
    }
}

function serial_filter(frm, model, s_number) {
    s_number.get_query = function() {
        return {
            filters: {
                'item_code': model
            }
        };
    };
    frm.refresh_fields();
}

function serial_status(frm) {
    var status;
    frappe.run_serially([
        () => frappe.call({
            method: "frappe.client.get_value",
            args: {
                "doctype": "Serial No",
                "filters": {
                    'name': frm.doc.serial_number // where Clause 
                },
                "fieldname": ['maintenance_status'], // fieldname to be fetched
                "limit": 1
            },
            callback: function(data) {
                status = data.message.maintenance_status;
            }
        }),
        () => frm.set_df_property("serial_number", "description", status ? status : "Unknown")
    ]);
}

function device_read_only(frm) {
    frm.set_df_property("model", "read_only", 1);
    frm.set_df_property("serial_number", "read_only", 1);
    frm.set_df_property("warranty_job", "read_only", 1);
    frm.set_df_property("multiple_devices", "read_only", 1);
    frm.set_df_property("device_list", "read_only", 1);
}

function time_worked(frm) {
    frappe.call({
        method: "eskill_custom.api.issue_total_hours",
        args: {
            doctype: frm.doctype,
            filters: frm.doc.name,
        },
        callback: function(data) {
            if (data.message) {
                if (data.message[0].total != frm.doc.total_time) {
                    frm.doc.total_time = data.message[0].total;
                }
                if (data.message[0].billable != frm.doc.billable_time) {
                    frm.doc.billable_time = data.message[0].billable;
                }
            } else {
                frm.doc.total_time = 0;
                frm.doc.billable_time = 0;
            }
        }
    });
}

function serial_report(frm, s_number) {
    check_save(frm);
    if (s_number) {
        window.open(window.location.origin + "/api/method/frappe.utils.print_format.download_pdf?doctype=Serial No&name=" + s_number + "&format=Eskill Serial Number History");
    } else {
        frappe.msgprint("No serial number.");
    }
}