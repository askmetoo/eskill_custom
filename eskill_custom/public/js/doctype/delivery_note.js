frappe.require([
    '/assets/eskill_custom/js/common.js',
    '/assets/eskill_custom/js/selling.js'
]);

frappe.ui.form.on('Delivery Note', {
    refresh(frm) {
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
    },

    validate(frm) {
        validate_line_item_gp(frm);
    },

    after_save(frm) {
        set_non_billable_accounts(frm);
    },
    
    before_submit(frm) {
        set_tax_template(frm);
    },
        
    on_submit(frm) {
        if (frm.doc.warranty_swap_out) {
            update_warranty_swap_out(frm);
        }

        if (frm.doc.service_order) {
            update_service_order(frm);
            if (frm.doc.goodwill) {
                service_delivery_unbillable(frm);
            } else {
                frappe.model.open_mapped_doc({
                    method: "eskill_custom.delivery_note.make_service_invoice",
                    frm: frm,
                });
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

    conversion_rate(frm) {
        convert_selected_to_base(frm);
    },

    currency(frm) {
        if (frm.doc.customer) {
            set_tax_template(frm);
        }
    },
    
    customer(frm) {
        set_tax_template(frm);
    },

    usd_to_currency(frm) {
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
    if (frm.doc.service_order && frm.doc.service_order_type != "Billable") {
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
    if (!frm.doc.goodwill) {
        frappe.call({
            method: "eskill_custom.api.sales_invoice_tax",
            args: {
                "doctype": frm.doctype,
                "currency": frm.doc.currency,
                "customer": frm.doc.customer
            },
            callback (data) {
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
    if (frm.doc.service_order) {
        frappe.call({
            method: "eskill_custom.delivery_note.update_service_order",
            args: {
                delivery_name: frm.doc.name
            }
        });
    }
}


function update_warranty_swap_out(frm) {
    if (frm.doc.warranty_swap_out) {
        frappe.call({
            method: "eskill_custom.delivery_note.update_warranty_swap_out",
            args: {
                delivery_name: frm.doc.name
            }
        });
    }
}