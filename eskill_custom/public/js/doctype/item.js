frappe.ui.form.on('Item', {
    refresh(frm) {
        kba_buttons(frm);
    },

    onload(frm) {
        account_filter(frm);
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


function kba_buttons(frm) {
    frm.add_custom_button(__("KB Articles"), function () {
        frm.save();
        frappe.route_options = {
            "type": "Product",
            "product": cur_frm.doc.item_code
        };
        frappe.set_route("List", "KBA", "List");
    });
    frm.add_custom_button(__("New KBA"), function () {
        frm.save();
        frappe.route_options = {
            "type": "Product",
            "product": cur_frm.doc.item_code
        };
        frappe.set_route("Form", "KBA", "New KBA");
    });
}
