frappe.require([
    '/assets/eskill_custom/js/common.js'
]);

frappe.ui.form.on('Purchase Invoice', {
    before_submit(frm) {
        get_bid_rate(frm, frm.doc.posting_date);
    },

    conversion_rate(frm) {
        convert_selected_to_base(frm);
    },

    usd_to_currency(frm) {
        convert_base_to_selected(frm);
    }
});