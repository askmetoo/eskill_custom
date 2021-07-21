frappe.ui.form.on('Item', {
    refresh(frm) {
        frm.add_custom_button(__("KB Articles"), function() {
            frm.save();
            frappe.route_options = {
                "type": "Product",
                "product": cur_frm.doc.item_code
            };
            frappe.set_route("List", "KBA", "List");
        });
        frm.add_custom_button(__("New KBA"), function() {
            frm.save();
            frappe.route_options = {
                "type": "Product",
                "product": cur_frm.doc.item_code
            };
            frappe.set_route("Form", "KBA", "New KBA");
        });
    }
});