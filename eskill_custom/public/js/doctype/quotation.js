frappe.require([
    '/assets/eskill_custom/js/common.js',
    '/assets/eskill_custom/js/selling.js'
]);

frappe.ui.form.on('Quotation', {
    refresh(frm) {
        stock_item_filter(frm);
        tax_template_filter(frm);
        get_bid_rate(frm, frm.doc.transaction_date);
        link_service_order(frm);
    },
    
    before_save(frm) {
        set_tax_template(frm);
        if (frm.doc.stock_item) {
            frm.doc.stock_item = undefined;
        }
        limit_rate(frm);
    },

    validate(frm) {
        validate_line_item_gp(frm);
    },
    
    before_submit(frm) {
        set_tax_template(frm);
    },

    party_name: function(frm) {
        set_tax_template(frm);
    },

    conversion_rate: function(frm) {
        limit_rate(frm);
        convert_selected_to_base(frm);
    },
    
    currency: function(frm) {
        get_bid_rate(frm, frm.doc.transaction_date);
        if (frm.doc.party_name) {
            set_tax_template(frm);
        }
    },
    
    search: function(frm) {
        if (frm.doc.stock_item) {
            stock_lookup(frm);
        } else {
            frappe.throw("You must select a stocked item before performing a stock lookup.");
        }
    },

    transaction_date: function(frm) {
        if (frm.doc.transaction_date) {
            get_bid_rate(frm, frm.doc.transaction_date);
        }
    },

    usd_to_currency: function(frm) {
        convert_base_to_selected(frm);
    }
});

function link_service_order(frm) {
    if (!frm.doc.service_order && frm.doc.docstatus == 1 && ["Open", "Expired"].includes(frm.doc.status)) {
        frm.add_custom_button(__("Link Service Order"), () => {
            frappe.prompt([
                {
                    label: __("Service Order"),
                    fieldname: "service_order",
                    fieldtype: "Link",
                    options: "Service Order",
                    reqd: 1,
                    get_query: () => {
                        return {
                            filters: [
                                ["Service Order", "customer", "=", frm.doc.party_name],
                                ["Service Order", "billing_status", "=", "Pending Delivery"],
                                ["Service Order", "goodwill", "=", 0],
                                ["Service Order", "job_type", "!=", "Warranty"]
                            ]
                        };
                    }
                }
            ], (values) => {
                frappe.call({
                    method: "eskill_custom.quotation.link_service_order",
                    args: {
                        quotation: frm.doc.name,
                        service_order: values.service_order
                    },
                    callback: () => {
                        frm.reload_doc();
                    }
                });
            });
        });
    }
}

// Overwrites library function due to difference in field name for customer
function set_tax_template(frm) {
    frappe.call({
        method: "eskill_custom.api.sales_invoice_tax",
        args: {
            "doctype": frm.doctype,
            "currency": frm.doc.currency,
            "customer": frm.doc.party_name
        },
        callback: function (data) {
            var template = data.message[0][0];
            if (template) {
                frappe.run_serially([
                    () => frm.set_value("taxes_and_charges", template),
                    () => frm.trigger("taxes_and_charges")
                ]);
            } else {
                frappe.msgprint("No Tax Template was detected.");
            }
        }
    });
}