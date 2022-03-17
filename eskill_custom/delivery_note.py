from __future__ import unicode_literals

import frappe
from erpnext.stock.doctype.serial_no.serial_no import \
    get_delivery_note_serial_no
from frappe.contacts.doctype.address.address import get_company_address
from frappe.model.mapper import get_mapped_doc
from frappe.model.utils import get_fetch_values
from frappe.utils import flt


def get_invoiced_qty_map(delivery_note):
    """returns a map: {dn_detail: invoiced_qty}"""
    invoiced_qty_map = {}

    for dn_detail, qty in frappe.db.sql("""select dn_detail, qty from `tabSales Invoice Item`
        where delivery_note=%s and docstatus=1""", delivery_note):
            if not invoiced_qty_map.get(dn_detail):
                invoiced_qty_map[dn_detail] = 0
            invoiced_qty_map[dn_detail] += qty

    return invoiced_qty_map


def get_returned_qty_map(delivery_note):
    """returns a map: {so_detail: returned_qty}"""
    returned_qty_map = frappe._dict(frappe.db.sql("""select dn_item.item_code, sum(abs(dn_item.qty)) as qty
        from `tabDelivery Note Item` dn_item, `tabDelivery Note` dn
        where dn.name = dn_item.parent
            and dn.docstatus = 1
            and dn.is_return = 1
            and dn.return_against = %s
        group by dn_item.item_code
    """, delivery_note))

    return returned_qty_map


@frappe.whitelist()
def make_service_invoice(source_name, target_doc=None):
    "This is a copy of the built-in ERPNext method for creating a Sales invoice from a delivery note to allow the creation of a Service Invoice."

    doc = frappe.get_doc('Delivery Note', source_name)

    to_make_invoice_qty_map = {}
    returned_qty_map = get_returned_qty_map(source_name)
    invoiced_qty_map = get_invoiced_qty_map(source_name)

    def set_missing_values(source, target):
        target.ignore_pricing_rule = 1
        target.run_method("set_missing_values")
        target.run_method("set_po_nos")

        if len(target.get("items")) == 0:
            frappe.throw(_("All these items have already been invoiced"))

        target.run_method("calculate_taxes_and_totals")

        # set company address
        if source.company_address:
            target.update({'company_address': source.company_address})
        else:
            # set company address
            target.update(get_company_address(target.company))

        if target.company_address:
            target.update(get_fetch_values("Sales Invoice", 'company_address', target.company_address))

    def update_item(source_doc, target_doc, source_parent):
        target_doc.qty = to_make_invoice_qty_map[source_doc.name]

        if source_doc.serial_no and source_parent.per_billed > 0:
            target_doc.serial_no = get_delivery_note_serial_no(source_doc.item_code,
                target_doc.qty, source_parent.name)

    def get_pending_qty(item_row):
        pending_qty = item_row.qty - invoiced_qty_map.get(item_row.name, 0)

        returned_qty = 0
        if returned_qty_map.get(item_row.item_code, 0) > 0:
            returned_qty = flt(returned_qty_map.get(item_row.item_code, 0))
            returned_qty_map[item_row.item_code] -= pending_qty

        if returned_qty:
            if returned_qty >= pending_qty:
                pending_qty = 0
                returned_qty -= pending_qty
            else:
                pending_qty -= returned_qty
                returned_qty = 0

        to_make_invoice_qty_map[item_row.name] = pending_qty

        return pending_qty

    doc = get_mapped_doc("Delivery Note", source_name, {
        "Delivery Note": {
            "doctype": "Sales Invoice",
            "field_map": {
                "is_return": "is_return",
                "service_order": "service_order"
            },
            "validation": {
                "docstatus": ["=", 1]
            }
        },
        "Delivery Note Item": {
            "doctype": "Sales Invoice Item",
            "field_map": {
                "name": "dn_detail",
                "parent": "delivery_note",
                "so_detail": "so_detail",
                "against_sales_order": "sales_order",
                "serial_no": "serial_no",
                "cost_center": "cost_center"
            },
            "postprocess": update_item,
            "filter": lambda d: get_pending_qty(d) <= 0 if not doc.get("is_return") else get_pending_qty(d) > 0
        },
        "Sales Taxes and Charges": {
            "doctype": "Sales Taxes and Charges",
            "add_if_empty": True
        },
        "Sales Team": {
            "doctype": "Sales Team",
            "field_map": {
                "incentives": "incentives"
            },
            "add_if_empty": True
        }
    }, target_doc, set_missing_values)

    return doc


@frappe.whitelist()
def set_non_billable_accounts(delivery_name: str):
    "If the linked service order is non-billable, set expense accounts to the relevant ones."

    delivery = frappe.get_doc("Delivery Note", delivery_name)
    service_order_settings = frappe.get_doc("Service Order Settings")
    if delivery.docstatus == 0:
        expense_account = str({
            'Internal': service_order_settings.internal_cos_account,
            'SLA': service_order_settings.sla_cos_account,
            'Warranty': service_order_settings.warranty_cos_account
        }[delivery.service_order_type])
        for delivery_item in delivery.items:
            delivery_item.expense_account = expense_account
            delivery_item.save(ignore_permissions=True)


@frappe.whitelist()
def set_non_billable_status(delivery_name: str):
    "Sets Delivery Note status to 'Completed' upon submission if it is non-billable."

    delivery = frappe.get_doc("Delivery Note", delivery_name)
    delivery.set_status(update=True, status="Closed")
    delivery.notify_update()
    clear_doctype_notifications(delivery)


@frappe.whitelist()
def update_service_order(delivery_name: str):
    "Updates information on service order to indicate delivery."

    delivery = frappe.get_doc("Delivery Note", delivery_name)
    service_order = frappe.get_doc("Service Order", delivery.service_order)
    if delivery.docstatus == 2 and service_order.billing_status == "Delivered":
        service_order.db_set("billing_status", "Pending Billing")
    elif service_order.billing_status != "Invoiced":
        service_order.db_set("billing_status", "Delivered")

    for item in delivery.items:
        if item.part_list:
            part = frappe.get_doc("Part List", item.part_list)
            if delivery.docstatus == 2:
                part.delivered_qty -= item.qty
            else:
                part.delivered_qty += item.qty
            part.save(ignore_permissions=True)

    service_order.add_comment(
        comment_type="Info",
        text="delivered this service order."
    )
    
    try:
        quotation = frappe.get_last_doc("Quotation", filters={'service_order': service_order.name, 'docstatus': 1})
        quotation.db_set("status", "Ordered", commit=True)
        quotations = frappe.db.get_list("Quotation",
            filters={
                'service_order': service_order.name
            },
            fields=['name', 'status']
        )
        for quote in quotations:
            if quote['status'] != "Ordered" and quote['status'] != "Expired":
                quotation = frappe.get_doc("Quotation", quote['name'])
                quotation.db_set("status", "Expired", commit=True)
    except:
        pass
