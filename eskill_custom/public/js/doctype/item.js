frappe.ui.form.on('Item', {
    onload(frm) {
        account_filter(frm);
    },

    refresh(frm) {
        duplicate_item(frm);
        create_asset_code(frm);
    }
});


function account_filter(frm) {
    frm.fields_dict.item_defaults.grid.get_field("expense_account").get_query = function(doc, cdt, cdn) {
        const row = locals[cdt][cdn];
        return {
            filters: {
                account_type: "Cost of Goods Sold",
                company: row.company,
                is_group: 0
            }
        }
    };

    frm.fields_dict.item_defaults.grid.get_field("income_account").get_query = function(doc, cdt, cdn) {
        const row = locals[cdt][cdn];
        return {
            filters: {
                account_type: "Income Account",
                company: row.company,
                is_group: 0
            }
        }
    };
}


function create_asset_code(frm) {
    if (frm.doc.has_serial_no) {
        frm.add_custom_button(__("Create Asset Code"), function() {
            var new_item = frappe.model.copy_doc(frm.doc);
            // Duplicate item could have different name, causing "copy paste" error.
            if (new_item.item_name===new_item.item_code) {
                new_item.item_name = null;
            }
            if (new_item.item_code===new_item.description || new_item.item_code===new_item.description) {
                new_item.description = null;
            }
            new_item.is_fixed_asset = 1;
            new_item.has_serial_no = 0;
            new_item.item_code = new_item.item_code + " - ASSET"
            frappe.set_route("Form", "Item", new_item.name);
        }, "Actions");
    }
}


function duplicate_item(frm) {
    frm.remove_custom_button("Duplicate")
    frm.add_custom_button(__("Duplicate Item"), function() {
        var new_item = frappe.model.copy_doc(frm.doc);
        // Duplicate item could have different name, causing "copy paste" error.
        if (new_item.item_name===new_item.item_code) {
            new_item.item_name = null;
        }
        if (new_item.item_code===new_item.description || new_item.item_code===new_item.description) {
            new_item.description = null;
        }
        frappe.set_route("Form", "Item", new_item.name);
    }, "Actions");
}