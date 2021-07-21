frappe.ui.form.on('Customer', {
    default_currency: function(frm) {
        if (frm.doc.default_currency) {
            frappe.call({
                method: "eskill_custom.api.customer_account_selector",
                args: {
                    currency: frm.doc.default_currency
                },
                callback: function(response) {
                    frm.clear_table('accounts');
                    if (response.message) {
                        var debtors_account = frappe.model.add_child(frm.doc, "Party Account", "accounts");
                        debtors_account.company = frappe.defaults.get_user_default('Company');
                        debtors_account.account = response.message;
                    }
                    frm.refresh_fields();
                }
            });
        } else {
            frm.clear_table('accounts');
            frm.refresh_field('accounts');
        }
    }
});