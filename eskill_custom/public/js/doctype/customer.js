frappe.ui.form.on('Customer', {
    refresh(frm) {
        if (!frm.doc.__islocal && frm.doc.default_currency == frappe.defaults.get_default('currency')) {
            frm.add_custom_button(__("Secondary Account"), function() {
                create_secondary_account(frm);
            }, "Create");
        }
    },

    onload_post_render(frm) {
        frappe.run_serially([
            () => frm.remove_custom_button("Accounts Receivable", "View"),
            () => frm.add_custom_button(__('Accounts Receivable'), function () {
                frappe.set_route('query-report', 'Accounts Receivable (Multi-Currency)',
                    {customer: frm.doc.name});
            }, __('View')),
            () => frm.add_custom_button(__('Customer Statement'), function () {
                frappe.set_route('query-report', 'Customer Statement',
                    {party_type: 'Customer', party: frm.doc.name});
            }, __('View'))
        ]);
    },

    default_currency(frm) {
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

function create_secondary_account(frm) {
    frappe.prompt([
        {
            fieldname: 'default_currency',
            fieldtype: 'Link',
            get_query: function() {
                return {
                    filters: [
                        ["Currency", "name", "!=", frm.doc.default_currency]
                    ]
                }
            },
            label: 'Account Currency',
            options: 'Currency',
            reqd: 1
        }
    ], (values) => {
        frappe.call({
            method: "eskill_custom.customer.create_secondary_customer",
            args: {
                customer: frm.doc.name,
                currency: values.default_currency
            },
            callback: (response) => {
                frappe.set_route("Form", "Customer", response.message);
            }
        });
    });
}