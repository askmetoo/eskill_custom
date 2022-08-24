frappe.require([
    '/assets/eskill_custom/js/common.js', 
    '/assets/eskill_custom/js/selling.js'
]);

frappe.ui.form.on('Sales Order', {
    refresh(frm) {
        tax_template_filter(frm);
    },
    
    before_save(frm) {
        set_items_delivery_date(frm);
        set_tax_template(frm);
    },

    validate(frm) {
        validate_line_item_gp(frm);
    },

    before_submit(frm) {
        set_tax_template(frm);
    },

    conversion_rate(frm) {
        convert_selected_to_base(frm);
    },

    customer(frm) {
        set_tax_template(frm);
    },

    currency(frm) {
        set_tax_template(frm);
    },

    usd_to_currency(frm) {
        convert_base_to_selected(frm);
    }
});

// sets the delivery_date field in the Sales Order Item child table
function set_items_delivery_date(frm) {
    if(frm.doc.delivery_date) {
        frm.doc.items.forEach((row) => {
            if (!row.delivery_date) {
                row.delivery_date = frm.doc.delivery_date;
            }
        });
    }
}