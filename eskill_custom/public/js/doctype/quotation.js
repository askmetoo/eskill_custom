frappe.ui.form.on('Quotation', {
    refresh(frm) {
        eskill_custom.form.selling.tax_template_filter(frm);
        link_service_order(frm);
        fetch_default_currency(frm);
        eskill_custom.form.common.check_price({frm: frm});
        eskill_custom.form.selling.document_gp_lookup(frm);
        eskill_custom.form.common.stock_availability(frm);
    },

    before_save(frm) {
        set_tax_template(frm);
    },

    validate(frm) {
        eskill_custom.form.selling.validate_line_item_gp(frm);
    },

    before_submit(frm) {
        set_tax_template(frm);
    },

    conversion_rate(frm) {
        eskill_custom.form.common.convert_selected_to_base(frm);
    },

    currency(frm) {
        if (frm.doc.party_name) {
            set_tax_template(frm);
        }
    },

    party_name(frm) {
        set_tax_template(frm);
    },

    quotation_to(frm) {
        fetch_default_currency(frm);
    },

    usd_to_currency(frm) {
        eskill_custom.form.common.convert_base_to_selected(frm);
    }
});

function fetch_default_currency(frm) {
    // clear existing fetch definition for the currency field
    if (frm.fetch_dict['*'] && frm.fetch_dict['*'].party_name) {
        delete frm.fetch_dict['*'].party_name;
    }

    // if the quotation_to field is set to "Customer" then fetch the default currency from the linked field
    if (frm.doc.quotation_to == "Customer") {
        frm.add_fetch("party_name", "default_currency", "currency");
    }
}

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
    const args = {
        "doctype": frm.doctype,
        "currency": frm.doc.currency,
    };

    // this is to allow for quotes without a customer account, i.e. quotes generated from leads
    if (frm.doc.quotation_to == "Customer") {
        args.customer = frm.doc.party_name;
    }

    frappe.call({
        method: "eskill_custom.api.sales_invoice_tax",
        args: args,
        callback(data) {
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