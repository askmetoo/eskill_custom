from __future__ import unicode_literals
import frappe
from frappe.model.document import Document


@frappe.whitelist()
def issue_total_hours(doctype, filters):
    "Return all time related to the given issue."
    try:
        hours_worked = frappe.db.sql(
            "select round(sum(hours), 3) total, round(sum(billing_hours), 3) billable from `tabTimesheet Detail` where activity_doctype = 'Issue' and activity_document = '%s' and docstatus <> 2" % filters, as_dict=True)
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
            f"select name from `tabSales Taxes and Charges Template` where currency = '{currency}' limit 1;")
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

@frappe.whitelist()
def auction_rate_lookup(doctype, si_posting_date):
    "Returns the auction rate at the date of SI posting."

    try:
        auction_rate = frappe.db.sql(
            f"select exchange_rate from `tabAuction Exchange Rate` where date < "
            f"date_add('{si_posting_date}', interval 1 day) order by date desc limit 1"
        )
        auction_rate = auction_rate[0][0]
    except:
        auction_rate = 0
    return auction_rate

@frappe.whitelist()
def customer_account_selector(currency):
    "Returns the debtors' control account for the given currency."

    try:
        debtors_account = frappe.db.sql(f"select name from tabAccount where account_currency = '{currency}' and debtors_account is true limit 1;")
        debtors_account = debtors_account[0][0] 
    except:
        debtors_account = ""

    return debtors_account

@frappe.whitelist()
def set_invoice_as_credited(credit):
    "Sets the status of the invoice linked to credit note to 'Credit Note Issued'."

    try:
        if credit:
            invoice = frappe.db.sql(
                "select parent Credit, CNI.delivery_note, DN.return_against, SII.Invoice from `tabSales Invoice Item` CNI "
                "join (select name, return_against from `tabDelivery Note`) DN on DN.name = CNI.delivery_note "
                "join (select parent Invoice, delivery_note from `tabSales Invoice Item` group by parent) SII on SII.delivery_note = DN.return_against "
                "group by parent "
                f"having Credit = '{credit}' "
                "order by parent desc "
                "limit 1;")
            frappe.db.set_value("Sales Invoice", invoice[0][0], "return_against", invoice[0][3])
            frappe.db.set_value("Sales Invoice", invoice[0][3], "status", "Credit Note Issued")
        else:
            return
    except Exception as error:
        return error
