from __future__ import unicode_literals

import frappe


@frappe.whitelist()
def link_service_order(quotation: str, service_order: str):
    "Link Service Order DocType in service_order field on Quotation."

    quotation = frappe.get_doc("Quotation", quotation)
    quotation.db_set("service_order", service_order, notify=True)
    quotation.notify_update()
