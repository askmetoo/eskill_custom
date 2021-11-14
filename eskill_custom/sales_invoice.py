from __future__ import unicode_literals

import frappe


@frappe.whitelist()
def update_service_order(invoice_name: str):
    "Updates information on service order to indicate invoice."

    invoice = frappe.get_doc("Sales Invoice", invoice_name)
    service_order = frappe.get_doc("Service Order", invoice.service_order)
    if not invoice.is_return and invoice.docstatus == 1:
        service_order.db_set("billing_status", "Invoiced")
        service_order.add_comment(
            comment_type="Info",
            text="invoiced this service order."
        )
    else:
        service_order.db_set("billing_status", "Delivered")
