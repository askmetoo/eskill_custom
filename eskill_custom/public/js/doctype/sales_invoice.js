frappe.require([
    '/assets/eskill_custom/js/common.js', 
    '/assets/eskill_custom/js/selling.js'
]);

frappe.ui.form.on('Sales Invoice', {
    refresh(frm) {
        stock_item_filter(frm);
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
        assign_sales_person(frm);
        if (frm.doc.stock_item) {
            frm.doc.stock_item = undefined;
        }
        get_bid_rate(frm, frm.doc.posting_date);
        limit_rate(frm);
    },

    before_submit(frm) {
        assign_sales_person(frm);
    },
    
    after_save(frm) {
        if (frm.doc.issue){
            issue_billing_update(frm, "invoice");
        }
    },
    
    on_submit(frm) {
        link_credit_to_invoice(frm);
        if (frm.doc.issue){
            issue_billing_update(frm, "invoice");
        }
    },
    
    on_update(frm) {
        if (frm.doc.issue){
            issue_billing_update(frm, "invoice");
        }
    },
    
    after_cancel(frm) {
        if (frm.doc.issue){
            issue_billing_update(frm, "invoice");
        }
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

    is_return: function(frm) {
        naming_series_set(frm);
    },

    posting_date: function(frm) {
        if (frm.doc.posting_date) {
            get_bid_rate(frm, frm.doc.posting_date);
        }
    },

    search: function(frm) {
        if (frm.doc.stock_item) {
            stock_lookup(frm);
        } else {
            frappe.throw("You must select a stocked item before performing a stock lookup.");
        }
    },

    usd_to_currency: function(frm) {
        convert_base_to_selected(frm);
    }
});

function link_credit_to_invoice(frm) {
    if (frm.doc.is_return) {
        frappe.call({
            method: "eskill_custom.api.set_invoice_as_credited",
            args: {
                credit: frm.doc.name
            },
            callback: function (message) {
                if (message) {
                    console.log(message);
                }
            }
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