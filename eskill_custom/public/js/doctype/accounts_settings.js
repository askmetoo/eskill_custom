// Copyright (c) 2021, Eskill Trading and contributors
// For license information, please see license.txt


frappe.ui.form.on("Accounts Settings", {
    refresh(frm) {
        frm.add_custom_button(__("Set Customer Accounts"), () => {
            frappe.call({
                method: "eskill_custom.accounts_settings.set_customer_debtors",
                args: {
                    company: frappe.user_defaults.company
                }
            });
        });
    }
});
