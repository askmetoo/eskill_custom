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
        }, __("Customer Validation"));
        frm.add_custom_button(__("Create Secondary Customers"), () => {
            frappe.prompt([
                {
                    fieldname : 'default_currency',
                    fieldtype : 'Link',
                    get_query : function() {
                        return {
                            filters : [
                                ["Currency", "name", "!=", frappe.sys_defaults.currency]
                            ]
                        }
                    },
                    label : 'Account Currency',
                    options : 'Currency',
                    reqd : 1
                }
            ], (values) => {
                frappe.call({
                    method: "eskill_custom.accounts_settings.create_secondary_customers",
                    args: {
                        base_currency: frappe.sys_defaults.currency,
                        currency: values.default_currency
                    }
                })
            })
        }, __("Customer Validation"));
    }
});
