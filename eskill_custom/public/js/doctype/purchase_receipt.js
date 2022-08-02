frappe.require([
    '/assets/eskill_custom/js/common.js'
]);

frappe.ui.form.on('Purchase Receipt', {
    refresh(frm) {
        make_landed_cost_voucher(frm);
    },

    on_submit(frm) {
        frappe.msgprint("Don't forget to process a Landed Cost Voucher if there are any additional costs on the received stock, e.g. freight. Press the following buttons to do this:<br><br>Create > Landed Cost Voucher");
    },

    conversion_rate(frm) {
        convert_selected_to_base(frm);
    },

    usd_to_currency(frm) {
        convert_base_to_selected(frm);
    }
});

// add button to map the current Purchase Receipt onto a new Landed Cost Voucher
function make_landed_cost_voucher(frm) {
    if (frm.doc.docstatus == 1) {
        frm.add_custom_button(__("Landed Cost Voucher"), () => {
            frappe.model.open_mapped_doc({
                method: "eskill_custom.purchase_receipt.make_landed_cost_voucher",
                frm: frm,
            });
        }, __("Create"));
    }
}
