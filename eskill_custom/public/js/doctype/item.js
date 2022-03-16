frappe.ui.form.on('Item', {
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
