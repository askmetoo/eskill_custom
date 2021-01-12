from __future__ import unicode_literals
import frappe
from frappe.model.document import Document


@frappe.whitelist()
def issue_total_hours(doctype, filters):
    "Return all time related to the given issue."
    try:
        hours_worked = frappe.db.sql(
            "select round(sum(total_hours), 3) total, round(sum(total_billable_hours), 3) billable from tabTimesheet where issue = '%s' and docstatus <> 2" % filters, as_dict=True)
        return hours_worked
    except:
        return False

@frappe.whitelist()
def check_maintain_stock(doctype, item):
    "Return maintain stock status."
    try:
        maintain_stock = frappe.db.sql("select is_stock_item from tabItem where name = '%s' limit 1;" % item)
        return maintain_stock
    except:
            return False
