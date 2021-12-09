frappe.require([
    '/assets/eskill_custom/js/common.js'
]);

frappe.ui.form.on('Stock Reconciliation', {
    before_submit(frm) {
        get_bid_rate(frm, frm.doc.posting_date);
    },

    on_submit(frm) {
        update_stocktake_summary(frm);
    }
});


function update_stocktake_summary(frm) {
    if (frm.doc.stocktake_summary) {
        frappe.call({
            method: "eskill_custom.eskill_customisations.doctype.stocktake_summary.stocktake_summary.update_reconciliations",
            args: {
                summary: frm.doc.stocktake_summary,
                reconciliation: frm.doc.name
            }
        })
    }
}
