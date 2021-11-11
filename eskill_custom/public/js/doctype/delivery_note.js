frappe.require([
    '/assets/eskill_custom/js/common.js',
    '/assets/eskill_custom/js/selling.js'
]);

frappe.ui.form.on('Delivery Note', {
    refresh: function(frm) {
        tax_template_filter(frm);
        if (frm.doc.service_order && frm.doc.docstatus == 1 && frm.doc.status == "To Bill") {
            setTimeout(() => {
                frm.remove_custom_button("Sales Invoice", 'Create');
            }, 500);
            frm.add_custom_button(__("Service Invoice"), function() {
                frappe.model.open_mapped_doc({
                    method: "eskill_custom.delivery_note.make_service_invoice",
                    frm: frm,
                });
            }, "Create");
        }
        if (frm.doc.customer && frm.doc.currency && !frm.doc.taxes_and_charges && !frm.doc.taxes.length) {
            set_tax_template(frm);
        }
    },
    
    before_save(frm) {
        set_tax_template(frm);
        assign_sales_person(frm);
        limit_rate(frm);
    },

    after_save(frm) {
        set_non_billable_accounts(frm);
    },
    
    before_submit(frm) {
        get_bid_rate(frm, frm.doc.posting_date);
        set_tax_template(frm);
        assign_sales_person(frm);
    },
        
    on_submit(frm) {
        if (frm.doc.service_order) {
            update_service_order(frm);
            if (frm.doc.service_order_type == "Billable") {
                frappe.model.open_mapped_doc({
                    method: "eskill_custom.delivery_note.make_service_invoice",
                    frm: frm,
                });
            } else {
                service_delivery_unbillable(frm);
            }
        } else {
            frappe.model.open_mapped_doc({
                method: "erpnext.stock.doctype.delivery_note.delivery_note.make_sales_invoice",
                frm: frm,
            });
        }
    },

    after_cancel(frm) {
        update_service_order(frm);
    },

    conversion_rate: function(frm) {
        limit_rate(frm);
        convert_selected_to_base(frm);
    },

    currency: function(frm) {
        get_bid_rate(frm, frm.doc.posting_date);
        if (frm.doc.customer) {
            set_tax_template(frm);
        }
    },
    
    customer: function(frm) {
        set_tax_template(frm);
    },

    posting_date: function(frm) {
        if (frm.doc.posting_date) {
            get_bid_rate(frm, frm.doc.posting_date);
        }
    },

    usd_to_currency: function(frm) {
        convert_base_to_selected(frm);
    }
});


function service_delivery_unbillable(frm) {
    frappe.call({
        method: "eskill_custom.delivery_note.set_non_billable_status",
        args: {
            delivery_name: frm.doc.name,
        },
        callback: () => {
            frm.reload_doc();
        }
    });
}


function set_non_billable_accounts(frm) {
    if (frm.doc.service_order_type != "Billable") {
        frappe.call({
            method: "eskill_custom.delivery_note.set_non_billable_accounts",
            args: {
                delivery_name: frm.doc.name
            },
            callback: () => {
                frm.reload_doc();
            }
        });
    }
}


function set_tax_template(frm) {
    if (frm.doc.service_order_type == "Billable") {
        frappe.call({
            method: "eskill_custom.api.sales_invoice_tax",
            args: {
                "doctype": frm.doctype,
                "currency": frm.doc.currency,
                "customer": frm.doc.customer
            },
            callback: function (data) {
                var template = data.message[0][0];
                if (template) {
                    frappe.run_serially([
                        () => frm.set_value("taxes_and_charges", template),
                        () => frm.trigger("taxes_and_charges")
                    ]);
                } else {
                    frappe.msgprint("No Tax Template detected.");
                }
            }
        });
    }
}


function update_service_order(frm) {
    frappe.call({
        method: "eskill_custom.delivery_note.update_service_order",
        args: {
            delivery_name: frm.doc.name
        }
    });
}
