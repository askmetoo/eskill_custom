# Copyright (c) 2022, Eskill Trading and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _

from eskill_custom.report_api import get_descendants

def execute(filters: dict = None):
    "Generate report."

    columns = get_columns(filters)

    data = get_data(filters, columns)

    return columns, data


def get_columns(filters: dict) -> 'list[dict]':
    "Returns a list of columns for the report."

    columns = [
        {
            'fieldname': "item_code",
            'label': _("Item Code"),
            'fieldtype': "Link",
            'options': "Item",
            'width': 500
        },
        {
            'fieldname': "item_name",
            'label': _("Item Name"),
            'fieldtype': "Text",
            'width': 400,
            'hidden': 1
        },
        {
            'fieldname': "item_group",
            'label': _("Item Group"),
            'fieldtype': "Link",
            'options': "Item Group",
            'width': 300,
            'hidden': 0 if "show_item_group" in filters else 1
        },
        {
            'fieldname': "brand",
            'label': _("Brand"),
            'fieldtype': "Text",
            'width': 120,
            'hidden': 0 if "show_brand" in filters else 1
        },
        {
            'fieldname': "warehouse",
            'label': _("Warehouse"),
            'fieldtype': "Link",
            'options': "Warehouse",
            'width': 200,
            'hidden': 0 if "show_warehouse" in filters else 1
        },
        {
            'fieldname': "actual_qty",
            'label': _("Actual Qty"),
            'fieldtype': "Float",
            'width': 120
        },
        {
            'fieldname': "ordered_qty",
            'label': _("Ordered Qty"),
            'fieldtype': "Float",
            'width': 120
        },
        {
            'fieldname': "reserved_qty",
            'label': _("Reserved Qty"),
            'fieldtype': "Float",
            'width': 120
        },
        {
            'fieldname': "projected_qty",
            'label': _("Projected Qty"),
            'fieldtype': "Float",
            'width': 120
        },
        {
            'fieldname': "valuation_rate",
            'label': _("Cost Price"),
            'fieldtype': "Currency",
            'options': "Company:company:default_currency",
            'width': 120,
            'hidden': 0 if "show_valuation_rate" in filters else 1
        },
    ]

    return columns


def get_data(filters: dict, columns: 'list[dict]') -> 'list[dict]':
    "Generates report data."

    data = initialise_data(filters, columns)

    if "item_code" in filters:
        data = [
            row
            for i, row in enumerate(data)
            if row['item_code'] == filters['item_code']
        ]

    if "item_group" in filters:
        descendants = get_descendants(
            "Item Group",
            filters['item_group'],
            "parent_item_group"
        )
        data = [
            row
            for i, row in enumerate(data)
            if (
                (row['item_group'] == filters['item_group'])
                or (row['item_group'] in descendants)
            )
        ]

    if "brand" in filters:
        data = [
            row
            for i, row in enumerate(data)
            if row['brand'] == filters['brand']
        ]

    if "warehouse" in filters:
        descendants = get_descendants(
            "Warehouse",
            filters['warehouse'],
            "parent_warehouse"
        )
        data = [
            row
            for i, row in enumerate(data)
            if (
                (row['warehouse'] == filters['warehouse'])
                or (row['warehouse'] in descendants)
            )
        ]

    if "warehouse_type" in filters:
        data = [
            row
            for i, row in enumerate(data)
            if row['warehouse_type'] == filters['warehouse_type']
        ]

    if "show_warehouse" not in filters:
        data = group_by_item_code(data)

    if "items_in_stock" in filters:
        data = [
            row
            for i, row in enumerate(data)
            if row['actual_qty'] > 0
        ]

    return data


def initialise_data(filters: dict, columns: 'list[dict]'):
    "Initialise report data."

    data = frappe.db.sql(
        f"""
            select
                B.item_code,
                I.item_name,
                I.item_group,
                I.brand,
                B.warehouse,
                W.warehouse_type,
                B.actual_qty,
                B.ordered_qty,
                B.reserved_qty,
                (B.actual_qty + B.ordered_qty - B.reserved_qty) projected_qty,
                B.valuation_rate
            from
                tabBin B
            join
                tabItem I on B.item_code = I.name
            join
                tabWarehouse W on W.name = B.warehouse
            having
                (actual_qty <> 0
                or ordered_qty <> 0
                or reserved_qty <> 0
                or projected_qty <> 0)
                and warehouse_type in ('Sales', 'Service')
                {
                    "and item_name like '%" + filters['item_name'] + "%'"
                    if "item_name" in filters
                    else ""
                }
            order by
                item_code, warehouse;
        """,
        as_dict=1
    )

    return data


def group_by_item_code(data: 'list[dict]') -> 'list[dict]':
    "Group given data by item code and return new data."

    unique_items = sorted({row['item_code'] for row in data})

    new_data = []
    for i, item in enumerate(unique_items):
        first_record = data[next(i for i, row in enumerate(data) if row['item_code'] == item)]
        new_data.append({
            'item_code': item,
            'item_name': first_record['item_name'],
            'item_group': first_record['item_group'],
            'brand': first_record['brand'],
            'warehouse': None,
            'warehouse_type': None,
            'actual_qty': 0,
            'ordered_qty': 0,
            'reserved_qty': 0,
            'projected_qty': 0,
            'valuation_rate': 0
        })

        for row in data:
            if row['item_code'] == item:
                new_data[i]['ordered_qty'] += row['ordered_qty']
                new_data[i]['reserved_qty'] += row['reserved_qty']
                new_data[i]['projected_qty'] += row['projected_qty']
                try:
                    new_data[i]['valuation_rate'] = (
                        (
                            (
                                new_data[i]['actual_qty'] * new_data[i]['valuation_rate']
                                + row['actual_qty'] * row['valuation_rate']
                            )
                        ) / (new_data[i]['actual_qty'] + row['actual_qty'])
                    )
                except ZeroDivisionError:
                    new_data[i]['valuation_rate'] = 0
                new_data[i]['actual_qty'] += row['actual_qty']

    return new_data
