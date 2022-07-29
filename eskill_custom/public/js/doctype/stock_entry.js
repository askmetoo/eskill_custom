frappe.require([
    '/assets/eskill_custom/js/common.js'
]);


frappe.ui.form.on('Stock Entry', {
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