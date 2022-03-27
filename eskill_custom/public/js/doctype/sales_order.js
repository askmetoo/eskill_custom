frappe.require([
    '/assets/eskill_custom/js/common.js', 
    '/assets/eskill_custom/js/selling.js'
]);

frappe.ui.form.on('Sales Order', {
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

    conversion_rate: function(frm) {
        limit_rate(frm);
        convert_selected_to_base(frm);
    },

    customer: function(frm) {
        set_tax_template(frm);
    },

    currency: function(frm) {
        get_bid_rate(frm, frm.doc.transaction_date);
        set_tax_template(frm);
    },

    posting_date: function(frm) {
        get_bid_rate(frm, frm.doc.transaction_date);
    },
    
    search: function(frm) {
        stock_lookup(frm);
    },

    usd_to_currency: function(frm) {
        convert_base_to_selected(frm);
    }
});