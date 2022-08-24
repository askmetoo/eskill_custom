frappe.require([
    '/assets/eskill_custom/js/common.js', 
    '/assets/eskill_custom/js/selling.js'
]);

frappe.ui.form.on('Sales Invoice', {
    refresh(frm) {
        tax_template_filter(frm);
        setTimeout(() => {
            frm.remove_custom_button("Work Order", 'Create');
            frm.remove_custom_button("Project", 'Create'); 
            frm.remove_custom_button("Subscription", 'Create');
            frm.remove_custom_button("Return / Credit Note", 'Create');
        }, 500);
        naming_series_set(frm);
    },
    
    before_save(frm) {
        set_tax_template(frm);
    },

    validate(frm) {
        validate_line_item_gp(frm);
        validate_advance_payment_rate(frm);
    },

    after_save(frm) {
        link_credit_to_invoice(frm);
    },

    before_submit(frm) {
        if (!frm.doc.return_against && frm.doc.is_return) {
            frappe.validated = false;
            frm.add_custom_button(__("Return Against Invoice"), () => {
                link_credit_to_invoice(frm);
            });
            frappe.throw("Return against invoice is required.");
        }
    },
    
    on_submit(frm) {
        update_service_order(frm);
        update_sla_billing(frm);
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

    is_return(frm) {
        naming_series_set(frm);
    },

    usd_to_currency(frm) {
        convert_base_to_selected(frm);
    }
});

function link_credit_to_invoice(frm) {
    if (frm.doc.is_return && !frm.doc.return_against) {
        frappe.prompt([
            {
                fieldname: 'invoice',
                fieldtype: 'Link',
                get_query: () => {
                    return {
                        filters: [
                            ["Sales Invoice", "customer", "=", frm.doc.customer],
                            ["Sales Invoice", "posting_date", "<=", frm.doc.posting_date],
                            ["Sales Invoice", "currency", "=", frm.doc.currency],
                            ["Sales Invoice", "conversion_rate", "=", frm.doc.conversion_rate],
                            ["Sales Invoice", "is_return", "=", 0],
                            ["Sales Invoice", "docstatus", "=", 1],
                            ["Sales Invoice", "status", "!=", "Credit Note Issued"],
                            ["Sales Invoice", "total", ">=", frm.doc.total],
                        ]
                    }
                },
                label: 'Sales Invoice',
                options: 'Sales Invoice',
                reqd: 1
            }
        ], (values) => {
            frappe.run_serially([
                () => frm.set_value("return_against", values.invoice),
                () => frm.save(),
                () => frm.reload_doc(),
            ]);
        });
    }
}

function naming_series_set(frm) {
    if (frm.doc.is_return) {
        frm.set_value("naming_series", "CN.########");
    } else {
        frm.set_value("naming_series", "SI.########");
    }
}

function update_service_order(frm) {
    if (frm.doc.service_order) {
        frappe.call({
            method: "eskill_custom.sales_invoice.update_service_order",
            args: {
                invoice_name: frm.doc.name
            }
        });
    }
}

function update_sla_billing(frm) {
    if (frm.doc.sla) {
        frappe.call({
            method: "eskill_custom.eskill_customisations.doctype.device_sla.device_sla.update_billing_information",
            args: {
                sla: frm.doc.sla,
                date: frm.doc.posting_date
            }
        });
    }
}

function validate_advance_payment_rate(frm) {
    if (!frappe.user_roles.includes("Accounts Manager") && frm.doc.currency != frappe.sys_defaults.currency) {
        frappe.call({
            method: "eskill_custom.sales_invoice.validate_advance_payment_rate",
            args: {
                exchange_rate: frm.doc.conversion_rate,
                advances: frm.doc.advances,
            },
            callback: (response) => {
                if (response.message) {
                    frappe.validated = false;
                    frappe.throw(response.message);
                }
            }
        });
    }
}
