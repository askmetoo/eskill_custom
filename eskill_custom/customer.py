"Collection of methods to be used in Customer documents."

from __future__ import unicode_literals
import json

from re import search

import frappe
from frappe import _


@frappe.whitelist()
def create_secondary_customer(customer: str, currency: str):
    "Creates secondary customer accounts based on the selected currency."

    def set_contact_details(doctype: str, previous_customer: str, customer: str):
        documents = frappe.get_all(
            "Dynamic Link",
            filters={
                'link_doctype': "Customer",
                'link_name': previous_customer,
                'parenttype': doctype
            },
            pluck="parent"
        )
        for document in documents:
            current_document = frappe.get_doc(doctype, document)
            current_document.append("links", {
                'link_doctype': "Customer",
                'link_name': customer
            })
            current_document.save(
                ignore_permissions=True
            )

    try:
        debtors_account = frappe.db.sql(f"""
        select
            name
        from
            tabAccount
        where
            account_currency = '{currency}'
            and debtors_account is true
        limit 1;""")[0][0]
    except IndexError:
        frappe.throw(_(
            "Please configure a debtors control account for "
            "the selected currency before creating customers."
        ))

    existing_secondary_currencies = frappe.get_all(
        "Customer",
        filters={
            'main_account': customer
        },
        pluck="default_currency",
        group_by="default_currency"
    )
    if currency in existing_secondary_currencies:
        frappe.throw(
            _("A customer account already exists for the selected currency."))

    meta = frappe.get_meta("Customer")
    fields = [
        field.fieldname
        for field in meta.fields
        if field.fieldtype not in (
            "Column Break",
            "Section Break",
            "Table"
        )
    ]

    main_customer = frappe.get_doc("Customer", customer)
    new_customer = frappe.new_doc("Customer")
    for field in fields:
        if hasattr(main_customer, field):
            setattr(new_customer, field, getattr(main_customer, field))
    new_customer.main_account = customer
    new_customer.default_currency = currency
    for account in main_customer.accounts:
        new_customer.append("accounts", {
            'account': debtors_account,
            'company': account.company
        })

    if search(r"^[A-Z]{3}-\d{3}-[A-Z]{2}$", main_customer.name):
        new_name = main_customer.name.split("-")[:2]
        new_name = "-".join(new_name) + "-" + currency[:2]
        new_customer.insert(
            ignore_permissions=True,
            ignore_if_duplicate=True,
            set_name=new_name
        )
        new_customer = frappe.get_doc("Customer", new_name)
    else:
        new_customer.insert(
            ignore_permissions=True,
            ignore_if_duplicate=True
        )

    for doc in ("Address", "Contact"):
        set_contact_details(doc, main_customer.name, new_customer.name)

    return new_customer.name


@frappe.whitelist()
def set_new_customer_info(values):
    """Sets the dynamic links for the given address and
    contact documents to link them to the new customer account."""

    results = json.loads(values)

    address = frappe.new_doc("Address")
    address.address_line1 = results['address_line1']
    if "address_line2" in results:
        address.address_line2 = results['address_line2']
    address.city = results['city']
    address.country = results['country']
    address.is_primary_address = 1
    address.is_shipping_address = 1
    address.append("links", {
        'link_doctype': "Customer",
        'link_name': results['customer_code'],
    })
    address.insert(ignore_permissions=True)

    contact = frappe.new_doc("Contact")
    contact.first_name = results['first_name']
    contact.last_name = results['last_name']
    contact.is_billing_contact = 1
    contact.is_primary_contact = 1
    contact.append("email_ids", {
        'email_id': results['email_id'],
        'is_primary': 1,
    })
    contact.append("phone_nos", {
        'phone': results['phone'],
        'is_primary_phone':  1 if "is_primary_phone" in results else 0,
        'is_primary_mobile_no': 1 if "is_primary_mobile_no" in results else 0,
    })
    contact.append("links", {
        'link_doctype': "Customer",
        'link_name': results['customer_code'],
    })
    contact.insert(ignore_permissions=True)

    customer = frappe.get_doc("Customer", results['customer_code'])
    customer.customer_primary_address = address.name
    customer.customer_primary_contact = contact.name
    customer.save()
