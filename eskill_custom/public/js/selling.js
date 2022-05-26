// Get current doctype and apply given form script overrides
route = frappe.get_route()
if (route[0] == "Form") {
    frappe.ui.form.on(route[1], {
        refresh(frm) {
            document_gp_lookup(frm);
        }
    });
}

function document_gp_lookup(frm) {
    if (frm.fields_dict.hasOwnProperty("items") && frm.doctype != "Service Order") {
        frm.add_custom_button(__("Document GP"), () => {
            if (frm.doc.items.length) {
                frappe.call({
                    method: "eskill_custom.api.document_gp_lookup",
                    args: {
                        doctype: route[1],
                        exchange_rate: frm.doc.usd_to_currency,
                        items: frm.doc.items
                    }
                });
            }
        }, __("View"));
    }
}

function limit_rate(frm) {
    if (frm.doc.auction_bid_rate && frm.doc.currency == "ZWD" && frm.doc.conversion_rate) {
        if (frm.doc.conversion_rate > roundNumber(1 / roundNumber(frm.doc.auction_bid_rate * 1.08, 4), 9)) {
            frm.set_value('conversion_rate', null);
            frappe.validated = false;
            frappe.throw("The minimum USD to selected currency rate is: ".concat(roundNumber(frm.doc.auction_bid_rate * 1.08, 4)));
        }
    }
}

function set_tax_template(frm) {
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

function tax_template_filter(frm) {
    frm.fields_dict.taxes_and_charges.get_query = function() {
        return {
            filters: [
                ["Sales Taxes and Charges Template", "currency", "=", frm.doc.currency]
            ]
        };
    };
}

function validate_line_item_gp(frm) {
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