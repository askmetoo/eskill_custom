"Collection of methods to be used in Supplier documents."

from __future__ import unicode_literals

from re import search

import frappe
from frappe import _


@frappe.whitelist()
def account_selector(currency):
    "Returns the creditors' control account for the given currency."

    try:
        creditors_account = frappe.get_all(
            "Account",
            filters={
                'account_currency': currency,
                'creditors_account': 1
            },
            pluck="name"
        )[0]
    except IndexError:
        creditors_account = ""

    return creditors_account


@frappe.whitelist()
def create_secondary_supplier(supplier: str, currency: str):
    "Creates secondary supplier accounts based on the selected currency."

    def set_contact_details(doctype: str, previous_supplier: str, supplier: str):
        documents = frappe.get_all(
            "Dynamic Link",
            filters={
                'link_doctype': "Supplier",
                'link_name': previous_supplier,
                'parenttype': doctype
            },
            pluck="parent"
        )
        for document in documents:
            current_document = frappe.get_doc(doctype, document)
            current_document.append("links", {
                'link_doctype': "Supplier",
                'link_name': supplier
            })
            current_document.save(
                ignore_permissions=True
            )


    try:
        creditors_account = frappe.db.sql(f"""
        select
            name
        from
            tabAccount
        where
            account_currency = '{currency}'
            and creditors_account is true
        limit 1;""")[0][0]
    except IndexError:
        frappe.throw(_(
            "Please configure a creditors control account for "
            "the selected currency before creating suppliers."
        ))

    existing_secondary_currencies = frappe.get_all(
        "Supplier",
        filters={
            'main_account': supplier
        },
        pluck="default_currency",
        group_by="default_currency"
    )
    if currency in existing_secondary_currencies:
        frappe.throw(_("A supplier account already exists for the selected currency."))

    meta = frappe.get_meta("Supplier")
    fields = [
        field.fieldname
        for field in meta.fields
        if field.fieldtype not in (
            "Column Break",
            "Section Break",
            "Table"
        )
    ]


    main_supplier = frappe.get_doc("Supplier", supplier)
    new_supplier = frappe.new_doc("Supplier")
    for field in fields:
        if hasattr(main_supplier, field):
            setattr(new_supplier, field, getattr(main_supplier, field))
    new_supplier.main_account = supplier
    new_supplier.default_currency = currency
    for account in main_supplier.accounts:
        new_supplier.append("accounts", {
            'account': creditors_account,
            'company': account.company
        })

    if search(r"^[A-Z]{3}-\d{3}-[A-Z]{2}$", main_supplier.name):
        new_name = main_supplier.name.split("-")[:2]
        new_name = "-".join(new_name) + "-" + currency[:2]
        new_supplier.insert(
            ignore_permissions=True,
            ignore_if_duplicate=True,
            set_name=new_name
        )
        new_supplier = frappe.get_doc("Supplier", new_name)
    else:
        new_supplier.insert(
            ignore_permissions=True,
            ignore_if_duplicate=True
        )

    for doc in ("Address", "Contact"):
        set_contact_details(doc, main_supplier.name, new_supplier.name)

    return new_supplier.name
