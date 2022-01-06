"Collection of methods to be used in the Accounts Settings document."

from __future__ import unicode_literals

import frappe
from frappe import _

@frappe.whitelist()
def set_customer_debtors(company: str):
    "Sets debtors' control account for customers."

    customers_without_account = frappe.db.sql(
        f"""select
            name
        from
            `tabCustomer`
        where
            name not in (
                select
                    parent
                from
                    `tabParty Account`
                where
                    company = '{company}'
                    and parenttype = 'Customer'
            );"""
    )
    customers_without_account = [customer[0] for customer in customers_without_account]

    debtors_accounts = frappe.db.sql(
        f"""select
            name,
            account_currency currency
        from
            tabAccount
        where
            not disabled
            and company = '{company}'
            and debtors_account;""",
        as_dict=True
    )
    debtors_accounts = {account['currency']: account['name'] for account in debtors_accounts}

    failed_customers = list()

    for customer_name in customers_without_account:
        customer = frappe.get_doc("Customer", customer_name)
        if customer.default_currency in debtors_accounts:
            customer.append("accounts", {
                'account': debtors_accounts[customer.default_currency],
                'company': company
            })
            customer.save(ignore_permissions=True)
        else:
            failed_customers.append("<li>{}: {} | {}</li>".format(
                customer.name,
                customer.customer_name,
                customer.default_currency
            ))

    if len(failed_customers) > 0:
        message = (
            "The following customers could not have their account "
            "set as there are no debtors' accounts with their currency:<br>"
        )
        for customer in failed_customers:
            message += customer
        frappe.msgprint(_(message))
    else:
        frappe.msgprint(_("All customers have a debtors' control account set."))
