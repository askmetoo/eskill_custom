frappe.ui.form.on('Supplier', {
    refresh: function(frm) {
        if (!frm.doc.__islocal && frm.doc.default_currency == frappe.defaults.get_default('currency')) {
            frm.add_custom_button(__("Secondary Account"), function() {
                create_secondary_account(frm);
            }, "Create");
        }
    },

    default_currency: function(frm) {
        if (frm.doc.default_currency) {
            frappe.call({
                method: "eskill_custom.supplier.account_selector",
                args: {
                    currency: frm.doc.default_currency
                },
                callback: function(response) {
                    frm.clear_table('accounts');
                    if (response.message) {
                        var creditors_account = frappe.model.add_child(frm.doc, "Party Account", "accounts");
                        creditors_account.company = frappe.defaults.get_user_default('Company');
                        creditors_account.account = response.message;
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
            method: "eskill_custom.supplier.create_secondary_supplier",
            args: {
                supplier: frm.doc.name,
                currency: values.default_currency
            },
            callback: (response) => {
                frappe.set_route("Form", "Supplier", response.message);
            }
        });
    });
}