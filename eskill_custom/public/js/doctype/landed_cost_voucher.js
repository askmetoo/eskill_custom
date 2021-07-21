frappe.require([
    '/assets/eskill_custom/js/common.js'
]);

frappe.ui.form.on('Landed Cost Voucher', {
    before_save(frm) {
        get_bid_rate(frm, frm.doc.posting_date);
    }
});