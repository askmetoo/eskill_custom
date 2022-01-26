# Copyright (c) 2013, Eskill Trading and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from datetime import datetime

import frappe
from frappe import _


def execute(filters: dict = None):
    "Generate report."

    columns = get_columns(filters)

    data = get_data(filters, columns)

    for i, row in enumerate(data):
        data[i]['report_currency'] = filters['secondary_currency']

    return columns, data


def get_columns(filters: dict) -> 'list[dict]':
    "Returns a list of columns for the report."

    columns = [
        {
            'fieldname': "invoice",
            'label': _("Invoice"),
            'fieldtype': "Link",
            'options': "Sales Invoice",
            'width': 110
        },
        {
            'fieldname': "customer",
            'label': _("Customer"),
            'fieldtype': "Link",
            'options': "Customer",
            'width': 110
        },
        {
            'fieldname': "customer_name",
            'label': _("Customer Name"),
            'fieldtype': "Text",
            'width': 400
        },
        {
            'fieldname': "posting_date",
            'label': _("Posting Date"),
            'fieldtype': "Date",
            'width': 120
        },
        {
            'fieldname': "currency",
            'label': _("Invoice Currency"),
            'fieldtype': "Text",
            'width': 50
        },
        {
            'fieldname': "sales_person",
            'label': _("Sales Person"),
            'fieldtype': "Link",
            'options': "Sales Person"
        },
        {
            'fieldname': "cos",
            'label': _("Cost of Sales (USD)"),
            'fieldtype': "Currency",
            'options': "Company:company:default_currency",
            'width': 120
        },
        {
            'fieldname': "net_total",
            'label': _("Income Excl. VAT (USD)"),
            'fieldtype': "Currency",
            'options': "Company:company:default_currency",
            'width': 120
        },
        {
            'fieldname': "total",
            'label': _("Income Incl. VAT (USD)"),
            'fieldtype': "Currency",
            'options': "Company:company:default_currency",
            'width': 120
        },
        {
            'fieldname': "rate",
            'label': _("Rate (Auction/Exchange)"),
            'fieldtype': "Float",
            'precision': 4
        },
        {
            'fieldname': "cos_secondary",
            'label': _(f"Cost of Sales ({filters['secondary_currency']})"),
            'fieldtype': "Currency",
            'options': "report_currency",
            'width': 120
        },
        {
            'fieldname': "net_total_secondary",
            'label': _(f"Income Excl. VAT ({filters['secondary_currency']})"),
            'fieldtype': "Currency",
            'options': "report_currency",
            'width': 120
        },
        {
            'fieldname': "total_secondary",
            'label': _(f"Income Incl. VAT ({filters['secondary_currency']})"),
            'fieldtype': "Currency",
            'options': "report_currency",
            'width': 120
        },
        {
            'fieldname': "gross_profit",
            'label': _("Gross Profit %"),
            'fieldtype': "Percent"
        }
    ]

    return columns


def get_data(filters: dict, columns: 'list[dict]') -> 'list[dict]':
    "Generates report data."

    data = initialise_data(filters, columns)

    if "customer" in filters:
        data = [
            row
            for i, row in enumerate(data)
            if row['customer'] == filters['customer']
        ]

    if "sales_person" in filters:
        data = [
            row
            for i, row in enumerate(data)
            if row['sales_person'] == filters['sales_person']
        ]

    if "currency" in filters:
        data = [
            row
            for i, row in enumerate(data)
            if row['currency'] == filters['currency']
        ]

    if "start_date" in filters:
        start_date = datetime.strptime(filters['start_date'], "%Y-%m-%d").date()
        data = [
            row
            for i, row in enumerate(data)
            if row['posting_date'] >= start_date
        ]
    if "end_date" in filters:
        end_date = datetime.strptime(filters['end_date'], "%Y-%m-%d").date()
        data = [
            row
            for i, row in enumerate(data)
            if row['posting_date'] <= end_date
        ]

    invoices = tuple({row['invoice'] for row in data})

    if len(invoices) > 0:
        deliveries = get_deliveries(invoices)
        for delivery in deliveries:
            index = next(i for i, row in enumerate(data) if row['invoice'] == delivery['invoice'])
            data[index]['cos'] = delivery['cos']
            data[index]['cos_secondary'] = delivery['cos'] * data[index]['rate']

        for i, row in enumerate(data):
            data[i]['gross_profit'] = (row['total'] - row['cos']) / row['total'] * 100
            data[i]['minimum_gp'] = filters['minimum_gp']

        total_row = {'invoice': "Total", 'total': 1}
        for column in columns:
            if column['fieldtype'] == "Currency":
                total_row[column['fieldname']] = 0
                for i, row in enumerate(data):
                    total_row[column['fieldname']] += row[column['fieldname']]
        total_row['gross_profit'] = (
            (total_row['total'] - total_row['cos'])
            / total_row['total']
            * 100
        )
        data.extend(({}, total_row))

    return data


def initialise_data(filters: dict, columns: 'list[dict]'):
    "Initialise report data."

    if "customer_name" in filters:
        customer_filter = f"and C.customer_name like '%{filters['customer_name']}%'"
    else:
        customer_filter = ""

    data = frappe.db.sql(f"""
        select
            SI.name invoice,
            SI.customer,
            C.customer_name,
            SI.posting_date,
            SI.currency,
            tab1.sales_person,
            (case when
                SI.currency = 'ZWL'
            then
                1 / SI.conversion_rate
            else
                SI.auction_bid_rate
            end) rate,
            SI.base_net_total net_total,
            SI.base_grand_total total,
            (case when
                SI.currency = 'ZWL'
            then
                SI.net_total
            else
                SI.base_net_total * SI.auction_bid_rate
            end) net_total_secondary,
            (case when
                SI.currency = 'ZWL'
            then
                SI.grand_total
            else
                SI.base_grand_total * SI.auction_bid_rate
            end) total_secondary
        from
            `tabSales Invoice` SI
        join
            tabCustomer C on SI.customer = C.name
        left join
            (select
                parent,
                sales_person,
                max(allocated_percentage)
            from
                `tabSales Team`
            group by
                parent) tab1 on SI.name = tab1.parent
        where
            SI.docstatus = 1
            and is_opening = 'No'
            {customer_filter}
        order by
            SI.posting_date;""", as_dict=1)

    for i, row in enumerate(data):
        for column in columns:
            if column['fieldname'] not in row:
                data[i][column['fieldname']] = 0

    return data


def get_deliveries(invoices: tuple):
    "Get cost of sales information from delivery notes."

    data = frappe.db.sql(f"""
        select
            SII.parent invoice,
            sum(DNI.incoming_rate * SII.qty) cos
        from
            `tabSales Invoice Item` SII
        join
            `tabDelivery Note Item` DNI on SII.dn_detail = DNI.name
        where
            SII.parent in {invoices}
        group by
            SII.parent
        having
            cos <> 0;""", as_dict=1)

    return data
