frappe.ui.form.on('Item Group', {
    validate(frm) {
        if (frm.doc.minimum_gp >= frm.doc.maximum_gp) {
            frappe.validated = false;
            frappe.throw("Maximum GP must be greater than the minimum GP.");
        }
    },
});