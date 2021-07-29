frappe.ui.form.on('Customer', {
    refresh : function(frm) {
        if (!frm.doc.__islocal && frm.doc.default_currency == frappe.defaults.get_default('currency')) {
            frm.add_custom_button(__("Secondary Account"), function() {
                create_secondary_account(frm);
            }, "Create");
        }
    },

    default_currency : function(frm) {
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
            fieldname : 'default_currency',
            fieldtype : 'Link',
            get_query : function() {
                return {
                    filters : [
                        ["Currency", "name", "!=", frm.doc.default_currency]
                    ]
                }
            },
            label : 'Account Currency',
            options : 'Currency',
            reqd : 1
        }
    ], (values) => {
        var new_customer = frappe.model.get_new_doc("Customer");
        frappe.run_serially([
            () => Object.keys(frm.fields_dict).forEach( function(field) {
                if (!["Column Break", "Currency", "Section Break", "Table"].includes(frm.fields_dict[field].df.fieldtype)) {
                    new_customer[field] = frm.doc[field];
                }
            }),
            () => {
                new_customer.customer_code = frm.doc.customer_code + values.default_currency[0];
                new_customer.default_currency = values.default_currency;
                new_customer.main_account = frm.doc.name;
            },
            () => {
                if (frm.doc.companies.length) {
                    frm.doc.companies.forEach( function(row) {
                        var companies = frappe.model.add_child(new_customer, "Allowed To Transact With", "companies");
                        companies.company = row.company;
                    });
                }
                if (frm.doc.sales_team.length) {
                    frm.doc.sales_team.forEach( function(row) {
                        var sales_team = frappe.model.add_child(new_customer, "Sales Team", "sales_team");
                        sales_team.sales_person = row.sales_person;
                        sales_team.contact_no = row.contact_no;
                        sales_team.allocated_percentage = row.allocated_percentage;
                        sales_team.commission_rate = row.commission_rate;
                    });
                }
            },
            () => frappe.call({
                method: "eskill_custom.api.customer_account_selector",
                args: {
                    currency: values.default_currency
                },
                callback: function(response) {
                    var debtors_account = frappe.model.add_child(new_customer, "Party Account", "accounts");
                    debtors_account.company = frappe.defaults.get_user_default('Company');
                    debtors_account.account = response.message;
                }
            }),
            () => frappe.db.insert(new_customer),
            () => frappe.msgprint("Customer account " + new_customer.customer_code + " created.")
        ]);
    });
}