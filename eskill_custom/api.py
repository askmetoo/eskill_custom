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
        maintain_stock = frappe.db.sql(
            "select is_stock_item from tabItem where name = '%s' limit 1;" % item)
        return maintain_stock
    except:
        return False


@frappe.whitelist()
def sales_invoice_tax(doctype, currency, customer):
    "Return tax template for Sales Invoice."
    try:
        territory = frappe.db.sql(
            f"select territory from tabCustomer where name = '{customer}';")
        if territory[0][0] != 'Zimbabwe':
            return None
        template = frappe.db.sql(
            f"select name from `tabSales Taxes and Charges Template` where name like '%{currency}%' limit 1;")
        return template
    except:
        return None

@frappe.whitelist()
def stock_lookup(doctype, user, item):
    "Returns stock locations and quantities."
    try:
        stock = frappe.db.sql(
            f"select (case when (W.warehouse_type in (select for_value from `tabUser Permission` where allow = 'Warehouse Type' and user = '{user}')"
            f" or W.name in (select for_value from `tabUser Permission` where allow = 'Warehouse' and user = '{user}')) or"
            f" ((select count(*) from `tabUser Permission` where (allow = 'Warehouse Type' or allow = 'Warehouse') and user = '{user}') = 0) then W.name else 'Other' end) location,"
            f" sum(actual_qty) quantity"
            f" from `tabStock Ledger Entry` as SLE"
            f" join `tabItem` as I on SLE.item_code = I.name"
            f" join `tabWarehouse` as W on SLE.warehouse =  W.name "
            f" where I.is_stock_item and I.name = '{item}' and W.disabled = 0"
            f" group by location"
            f" having quantity > 0 or location = 'Other'"
            f" order by (case when location = 'Other' then 1 else 0 end), quantity desc, location", as_dict = True
        )
        return stock
    except:
        return None

@frappe.whitelist()
def item_price_lookup(doctype, currency, price_list, item):
    "Returns the price of a given item."
    try:
        price = frappe.db.sql(
            f"select round(price_list_rate, 2)"
            f" from `tabItem Price`"
            f" where item_code = '{item}' and price_list = '{price_list}' and currency = '{currency}'"
            f" order by creation desc"
            f" limit 1"
        )
        return price if price else "Unavailable"
    except:
        return "Unavailable"
