frappe.require([
    '/assets/eskill_custom/js/common.js'
]);

frappe.ui.form.on('Purchase Receipt', {
    before_submit(frm) {
        get_bid_rate(frm, frm.doc.posting_date);
    }
});