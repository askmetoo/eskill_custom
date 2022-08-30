frappe.ui.form.on('Stock Entry', {
    refresh(frm) {
        eskill_custom.form.common.check_price({frm: frm});
        eskill_custom.form.common.stock_availability(frm);
    },

    on_submit(frm) {
        if (frm.doc.stock_entry_type == "Material Transfer") {
            release_parts(frm);
        }
    },

    after_cancel(frm) {
        if (frm.doc.stock_entry_type == "Material Transfer") {
            release_parts(frm);
        }
    },
});


function release_parts(frm) {
    frappe.call({
        method: "eskill_custom.material_request.update_part",
        args: {
            doc: frm.doc.name,
        },
    });
}