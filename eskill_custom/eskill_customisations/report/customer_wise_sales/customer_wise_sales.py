# Copyright (c) 2022, Eskill Trading and contributors
# For license information, please see license.txt

import frappe
from frappe import _

from eskill_custom.report_api import get_descendants


def execute(filters=None):
    "Main function."

    columns, data = [], []

    columns.extend(get_columns(filters))
    data.extend(get_data(filters))

    return columns, data


def get_columns(filters: dict) -> 'list[dict]':
    "Returns a list of columns for the report."

    columns = [
        {
            'fieldname': "customer",
            'label': _("Customer Name"),
            'fieldtype': "Data",
            'width': 500
        },
        {
            'fieldname': "units_sold",
            'label': _("Units Sold"),
            'fieldtype': "Int"
        },
        {
            'fieldname': "net_income",
            'label': _("Net Income"),
            'fieldtype': "Currency",
            'hidden': 0 if "show_profit_info" in filters else 1
        },
        {
            'fieldname': "profit",
            'label': _("Gross Profit"),
            'fieldtype': "Currency",
            'hidden': 0 if "show_profit_info" in filters else 1
        },
        {
            'fieldname': "gp_percentage",
            'label': _("GP as % of Net Income"),
            'fieldtype': "Percent",
            'hidden': 0 if "show_profit_info" in filters else 1
        }
    ]

    return columns


def get_data(filters: dict) -> 'list[dict]':
    "Returns a list of rows populated with data for the report."

    where_statement = get_where_statement(filters)

    data = []
    data.extend(frappe.db.sql(f"""
        select
            C.customer_name customer,
            sum(SII.qty) units_sold,
            sum(SII.base_net_amount) net_income,
            sum(SII.base_net_amount - (DNI.incoming_rate * SII.qty)) profit
        from
            `tabSales Invoice Item` SII
        join
            `tabSales Invoice` SI on SII.parent = SI.name
        join
            `tabDelivery Note Item` DNI on SII.dn_detail = DNI.name
        join
            tabItem I on SII.item_code = I.name
        join
            tabCustomer C on SI.customer = C.name
        {where_statement}
        group by
            `customer`
        having
            `units_sold` <> 0
        order by
            `units_sold` desc, customer;
    """, as_dict=True))

    for i, row in enumerate(data):
        if row['net_income'] and row['profit']:
            data[i]['gp_percentage'] = (row['profit'] / row['net_income']) * 100
        else:
            data[i]['gp_percentage'] = 0

    return data


def get_where_statement(filters: dict) -> str:
    "Returns the where statement for the get_data() query."

    where_list = []

    # product filters
    if "item_code" in filters:
        where_list.append(f"I.name = '{filters['item_code']}'")
    if "item_name" in filters:
        where_list.append(f"I.item_name like '%{filters['item_name']}%'")
    if "brand" in filters:
        where_list.append(f"I.brand = '{filters['brand']}'")
    if len(filters['item_group']) > 0:
        where_list.append(f"I.item_group in ('{filters['item_group'][0]}'")

        descendants = get_descendants(
            "Item Group",
            filters['item_group'][0],
            "parent_item_group"
        )
        for descendant in  descendants:
            where_list[-1] += f", '{descendant}'"

        for i in range(1, len(filters['item_group'])):
            where_list[-1] += f", '{filters['item_group'][i]}'"

            descendants = get_descendants(
                "Item Group",
                filters['item_group'][i],
                "parent_item_group"
            )
            for descendant in  descendants:
                where_list[-1] += f", '{descendant}'"

        where_list[-1] += ")"
    if "stock_items_only" in filters:
        where_list.append("I.is_stock_item")

    # date filters
    if "from_date" in filters:
        where_list.append(f"SI.posting_date >= '{filters['from_date']}'")
    if "to_date" in filters:
        where_list.append(f"SI.posting_date <= '{filters['to_date']}'")


    where_statement = "where SII.docstatus = 1"
    for clause in where_list:
        where_statement += " and " + clause

    return where_statement
