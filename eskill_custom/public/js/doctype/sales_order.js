frappe.ui.form.on('Sales Order', {
    refresh(frm) {
        eskill_custom.form.selling.tax_template_filter(frm);
        eskill_custom.form.common.check_price({frm: frm});
        eskill_custom.form.selling.document_gp_lookup(frm);
        eskill_custom.form.common.stock_availability(frm);
    },
    
    before_save(frm) {
        set_items_delivery_date(frm);
        eskill_custom.form.selling.set_tax_template(frm);
    },

    validate(frm) {
        eskill_custom.form.selling.validate_line_item_gp(frm);
    },

    before_submit(frm) {
        eskill_custom.form.selling.set_tax_template(frm);
    },

    conversion_rate(frm) {
        eskill_custom.form.common.convert_selected_to_base(frm);
    },

    customer(frm) {
        eskill_custom.form.selling.set_tax_template(frm);
    },

    currency(frm) {
        eskill_custom.form.selling.set_tax_template(frm);
    },

    usd_to_currency(frm) {
        eskill_custom.form.common.convert_base_to_selected(frm);
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