frappe.ui.form.on('Purchase Order', {
    conversion_rate(frm) {
        eskill_custom.form.common.convert_selected_to_base(frm);
    },

    usd_to_currency(frm) {
        eskill_custom.form.common.convert_base_to_selected(frm);
    }
});