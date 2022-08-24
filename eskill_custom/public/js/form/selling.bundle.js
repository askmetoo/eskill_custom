frappe.provide("eskill_custom.form.selling");

eskill_custom.form.selling.document_gp_lookup = (frm) => {
    if (frm.fields_dict.hasOwnProperty("items") && frm.doctype != "Service Order") {
        frm.add_custom_button(__("Document GP"), () => {
            if (frm.doc.items.length) {
                var exchange_rate = 1;

                // if the DocType has the exchange_rate field, use it for the exchange rate otherwise use the conversion_rate field
                if (frm.fields_dict.hasOwnProperty("exchange_rate")) {
                    exchange_rate = frm.doc.exchange_rate;
                } else if (frm.fields_dict.hasOwnProperty("conversion_rate")) {
                    exchange_rate = frm.doc.conversion_rate;
                }

                frappe.call({
                    method: "eskill_custom.api.document_gp_lookup",
                    args: {
                        doctype: route[1],
                        exchange_rate: exchange_rate,
                        items: frm.doc.items
                    }
                });
            }
        }, __("View"));
    }
}

eskill_custom.form.selling.set_tax_template = (frm) => {
    if (frm.doc.customer && frm.doc.currency) {
        frappe.call({
            method: "eskill_custom.api.sales_invoice_tax",
            args: {
                "doctype": frm.doctype,
                "currency": frm.doc.currency,
                "customer": frm.doc.customer
            },
            callback: function(data) {
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

eskill_custom.form.selling.tax_template_filter = (frm) => {
    frm.fields_dict.taxes_and_charges.get_query = function() {
        return {
            filters: [
                ["Sales Taxes and Charges Template", "currency", "=", frm.doc.currency]
            ]
        };
    };
}

eskill_custom.form.selling.validate_line_item_gp = (frm) => {
    if (!frm.doc.is_return && !frm.is_new()) {
        frappe.call({
            method: "eskill_custom.api.validate_line_item_gp",
            args: {
                doctype: frm.doctype,
                exchange_rate: frm.doc.usd_to_currency,
                items: frm.doc.items,
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