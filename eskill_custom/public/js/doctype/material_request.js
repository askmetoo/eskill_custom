frappe.ui.form.on("Material Request", {
    refresh(frm) {
        eskill_custom.form.common.check_price({frm: frm});
    },

    after_cancel(frm) {
        if (frm.doc.service_order) {
            frappe.call({
                method: "eskill_custom.material_request.cancel_part_request",
                args: {
                    document: frm.doc.name
                }
            })
        }
    }
})
