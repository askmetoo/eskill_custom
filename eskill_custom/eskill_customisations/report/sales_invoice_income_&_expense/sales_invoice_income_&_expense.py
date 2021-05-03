# Copyright (c) 2013, Eskill Trading and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _


def execute(filters=None):
	if filters:
		conditions = get_conditions(filters)
	else:
		conditions= ''

	columns = [{
			"fieldname": "invoice",
			"label": _("Invoice"),
			"fieldtype": "Link",
			"options": "Sales Invoice",
			"width": 100
		},
		{
			"fieldname": "customer",
			"label": _("Customer"),
			"fieldtype": "Link",
			"options": "Customer",
			"width": 400
		},
		{
			"fieldname": "customer_code",
			"label": _("Customer Code"),
			"fieldtype": "Text",
			"width": 100
		},
		{
			"fieldname": "posting_date",
			"label": _("Posting Date"),
			"fieldtype": "Date",
			"width": 120
		},
		{
			"fieldname": "currency",
			"label": _("Invoice Currency"),
			"fieldtype": "Text",
			"width": 50
		},
		{
			"fieldname": "cos_usd",
			"label": _("Cost of Sales (USD)"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "net_total_usd",
			"label": _("Income Excl. VAT (USD)"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "total_usd",
			"label": _("Income Incl. VAT (USD)"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "rate",
			"label": _("Rate (Auction/Exchange)"),
			"fieldtype": "Text",
			"width": 60
		},
		{
			"fieldname": "cos_rtgs",
			"label": _("Cost of Sales (RTGS)"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "net_total_rtgs",
			"label": _("Income Excl. VAT (RTGS)"),
			"fieldtype": "Currency",
			"options": "",
			"width": 120
		},
		{
			"fieldname": "total_rtgs",
			"label": _("Income Incl. VAT (RTGS)"),
			"fieldtype": "Currency",
			"width": 120
		}
	]
	data = frappe.db.sql(f"""select
	`tabSales Invoice`.name as invoice,
	`tabSales Invoice`.customer_name as customer,
	tabCustomer.customer_code as customer_code,
	`tabSales Invoice`.posting_date as posting_date,
	`tabSales Invoice`.currency as currency,
	(case when `tabSales Invoice`.is_return then GL.credit * -1 else GL.debit end) as cos_usd,
	`tabSales Invoice`.base_net_total as net_total_usd,
	`tabSales Invoice`.base_total as total_usd,
	rate.rate as rate,
	(case when `tabSales Invoice`.is_return then (GL.credit * rate.rate) * -1 else (GL.debit * rate.rate) end) as cos_rtgs,
	(`tabSales Invoice`.base_net_total * rate.rate) as net_total_rtgs,
	(`tabSales Invoice`.base_total * rate.rate) as total_rtgs
from
	`tabSales Invoice`
left join
	tabCustomer on tabCustomer.name = `tabSales Invoice`.customer 
join
	(select
		parent invoice,
		delivery_note
	from
		`tabSales Invoice Item`
	where
		item_code is not null
	group by
		invoice) as link on `tabSales Invoice`.name = link.invoice
left join
	(select
		voucher_no,
		sum(debit) debit,
		sum(credit) credit
	from
		`tabGL Entry`
	where
		account like '%Cost of Sales%' and voucher_type = 'Delivery Note'
	group by
		voucher_no) as GL on GL.voucher_no = link.delivery_note
join
	(select
		name invoice,
		(case when currency = 'USD' then auction_bid_rate else 1 / conversion_rate end) rate
	from
		`tabSales Invoice`) as rate on rate.invoice = `tabSales Invoice`.name 
where
	`tabSales Invoice`.docstatus = 1 {conditions}
order by
	`tabSales Invoice`.name desc
""", as_dict=1)

	return columns, data

def get_conditions(filters):
	"Return conditions for query."

	conditions = ""

	if filters.get("customer"):
		conditions += f" and customer = '{filters['customer']}'"
	if filters.get("customer_code"):
		conditions += f" and customer_code like '%{filters['customer_code']}%'"
	if filters.get("currency"):
		conditions += f" and currency = '{filters['currency']}'"
	conditions += f" and (posting_date >= '{filters['start_date']}' and posting_date <= '{filters['end_date']}')"

	return conditions
