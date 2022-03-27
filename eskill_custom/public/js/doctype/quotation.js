frappe.require([
    '/assets/eskill_custom/js/common.js',
    '/assets/eskill_custom/js/selling.js'
]);

frappe.ui.form.on('Quotation', {
    refresh(frm) {
        stock_item_filter(frm);
        tax_template_filter(frm);
        get_bid_rate(frm, frm.doc.transaction_date);
    },
    
    before_save(frm) {
        set_tax_template(frm);
        assign_sales_person(frm);
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
        assign_sales_person(frm);
    },
    
    after_save(frm) {
        if (frm.doc.issue){
            issue_billing_update(frm, "quotation");
        }
    },
    
    on_submit(frm) {
        if (frm.doc.issue){
            issue_billing_update(frm, "quotation");
        }
    },
    
    on_update(frm) {
        if (frm.doc.issue){
            issue_billing_update(frm, "quotation");
        }
    },
    
    after_cancel(frm) {
        if (frm.doc.issue){
            issue_billing_update(frm, "quotation");
        }
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