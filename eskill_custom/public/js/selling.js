function assign_sales_person(frm) {
    // frappe.call({
    //     method: "eskill_custom.api.invoice_sales_person",
    //     args: {
    //         user: frappe.session.user,
    //         service_invoice: (frm.doc.issue) ? true : false,
    //         issue: (frm.doc.issue) ? frm.doc.issue : ""
    //     },
    //     callback: function(response) {
    //         frm.clear_table('sales_team');
    //         response.message.forEach( function(person) {
    //             frm.add_child('sales_team', {
    //                 'sales_person': person.sales_person,
    //                 'allocated_percentage': person.contribution
    //             });
    //         });
    //         frm.refresh_field('sales_team');
    //     }
    // });
}

function issue_billing_update(frm, dtype) {
    // frappe.call({
    //     method: "eskill_custom.api.update_issue_billing",
    //     args: {
    //         docfield: dtype,
    //         docname: frm.doc.name,
    //         docfield_status: frm.doc.status,
    //         issue: frm.doc.issue
    //     },
    //     callback: function(response) {
    //         if (response.message != 1) {
    //             frappe.throw(__("Error encountered when updating issue."));
    //         }
    //     }
    // });
}

function limit_rate(frm) {
    if (frm.doc.auction_bid_rate && frm.doc.currency == "ZWD" && frm.doc.conversion_rate) {
        if (frm.doc.conversion_rate > roundNumber(1 / roundNumber(frm.doc.auction_bid_rate * 1.08, 4), 9)) {
            frm.set_value('conversion_rate', null);
            frappe.validate = false;
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
    console.log(frm.doc.items)
    frappe.call({
        method: "eskill_custom.api.validate_line_item_gp",
        args: {
            items: frm.doc.items,
            exchange_rate: frm.doc.conversion_rate
        },
        callback: (response) => {
            if (response.message) {
                frappe.validated = false;
                frappe.throw(response.message);
            }
        }
    });
}