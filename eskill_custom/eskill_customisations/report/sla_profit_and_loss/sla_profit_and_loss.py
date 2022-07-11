# Copyright (c) 2022, Eskill Trading and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils.data import today
from numpy import average
from copy import deepcopy
from datetime import datetime

MONTHS = (
    "jan", "feb", "mar",
    "apr", "may", "jun",
    "jul", "aug", "sep",
    "oct", "nov", "dec"
)


def execute(filters=None):
    "Report main function."

    columns, data = [], []

    columns.extend(get_columns(filters))
    data.extend(get_data(filters, columns))

    chart = get_chart(filters, data)

    summary = get_summary(filters, data)

    return columns, data, None, chart, summary


def get_columns(filters: dict) -> 'list[dict]':
    "Returns a list of columns for the report."

    columns = [
        {
            'fieldname': "sla",
            'label': _("SLA"),
            'fieldtype': "Link",
            'options': "Device SLA"
        },
        {
            'fieldname': "customer",
            'label': _("Customer"),
            'fieldtype': "Link",
            'options': "Customer",
            'width': 340
        },
        {
            'fieldname': "customer_name",
            'label': _("Customer Name"),
            'fieldtype': "Data",
            'hidden': 1
        },
        {
            'fieldname': "contract_tier",
            'label': _("Contract Tier"),
            'fieldtype': "Link",
            'options': "SLA Level"
        },
        {
            'fieldname': "start_date",
            'label': _("Start Date"),
            'fieldtype': "Date"
        },
        {
            'fieldname': "end_date",
            'label': _("End Date"),
            'fieldtype': "Date"
        },
        {
            'fieldname': "days_remaining",
            'label': _("Days Remaining"),
            'fieldtype': "Int"
        },
        {
            'fieldname': "last_invoiced",
            'label': _("Last Invoiced"),
            'fieldtype': "Date"
        },
        {
            'fieldname': "jan",
            'label': _("January"),
            'fieldtype': "Currency",
            'hidden': 0 if "display_months" in filters else 1
        },
        {
            'fieldname': "feb",
            'label': _("February"),
            'fieldtype': "Currency",
            'hidden': 0 if "display_months" in filters else 1
        },
        {
            'fieldname': "mar",
            'label': _("March"),
            'fieldtype': "Currency",
            'hidden': 0 if "display_months" in filters else 1
        },
        {
            'fieldname': "apr",
            'label': _("April"),
            'fieldtype': "Currency",
            'hidden': 0 if "display_months" in filters else 1
        },
        {
            'fieldname': "may",
            'label': _("May"),
            'fieldtype': "Currency",
            'hidden': 0 if "display_months" in filters else 1
        },
        {
            'fieldname': "jun",
            'label': _("June"),
            'fieldtype': "Currency",
            'hidden': 0 if "display_months" in filters else 1
        },
        {
            'fieldname': "jul",
            'label': _("July"),
            'fieldtype': "Currency",
            'hidden': 0 if "display_months" in filters else 1
        },
        {
            'fieldname': "aug",
            'label': _("August"),
            'fieldtype': "Currency",
            'hidden': 0 if "display_months" in filters else 1
        },
        {
            'fieldname': "sep",
            'label': _("September"),
            'fieldtype': "Currency",
            'hidden': 0 if "display_months" in filters else 1
        },
        {
            'fieldname': "oct",
            'label': _("October"),
            'fieldtype': "Currency",
            'hidden': 0 if "display_months" in filters else 1
        },
        {
            'fieldname': "nov",
            'label': _("November"),
            'fieldtype': "Currency",
            'hidden': 0 if "display_months" in filters else 1
        },
        {
            'fieldname': "dec",
            'label': _("December"),
            'fieldtype': "Currency",
            'hidden': 0 if "display_months" in filters else 1
        },
        {
            'fieldname': "total_cost",
            'label': _("Total Cost"),
            'fieldtype': "Currency",
        },
        {
            'fieldname': "total_income",
            'label': _("Total Income"),
            'fieldtype': "Currency",
        },
        {
            'fieldname': "profit",
            'label': _("Profit"),
            'fieldtype': "Currency",
        },
    ]

    for i, row in enumerate(columns):
        if row['fieldtype'] == "Currency":
            columns[i]['width'] = 116
        elif row['fieldtype'] == "Date":
            columns[i]['width'] = 115

    for month in MONTHS:
        index = next(i for i, row in enumerate(columns) if row['fieldname'] == month)

        # Add income column for month
        columns.insert(index, deepcopy(columns[index]))
        columns[index]['fieldname'] += "_income"
        columns[index]['label'] += _(" Income")
        # columns[index]['hidden'] = 1

        # Add cost column for month
        columns.insert(index, deepcopy(columns[index + 1]))
        columns[index]['fieldname'] += "_cost"
        columns[index]['label'] += _(" Cost")
        # columns[index]['hidden'] = 1

    return columns


def get_data(filters: dict, columns: 'list[dict]') -> 'list[dict]':
    "Returns the report data."

    data = initialise_data(filters, columns)

    if data:
        data = get_costs(filters, data)
        data = get_income(filters, data)

    for i, row in enumerate(data):
        data[i]['profit'] = round(row['total_income'] - row['total_cost'], 2)

    return data


def initialise_data(filters: dict, columns: 'list[dict]') -> 'list[dict]':
    "Returns an initialised data grid."

    data = frappe.db.sql(f"""
        select
            name sla,
            customer,
            customer_name,
            contract_tier,
            start_date,
            end_date,
            datediff(end_date, current_date) days_remaining,
            last_invoiced
        from
            `tabDevice SLA`
        where
            customer_name like '%{filters['customer_name'] if "customer_name" in filters else ""}%'
            {"and year(start_date) <= " + filters['year'] if "year" in filters else ""};
    """, as_dict=True)

    if "sla" in filters:
        data = [
            row
            for i, row in enumerate(data)
            if row['sla'] == filters['sla']
        ]

    if "contract_tier" in filters:
        data = [
            row
            for i, row in enumerate(data)
            if row['contract_tier'] == filters['contract_tier']
        ]

    if "customer" in filters:
        data = [
            row
            for i, row in enumerate(data)
            if row['customer'] == filters['customer']
        ]

    data = filter_device(filters, data)

    for i, _ in enumerate(data):
        for col in columns:
            if col['fieldtype'] == "Currency":
                data[i][col['fieldname']] = 0

    return data


def filter_device(filters: dict, data: 'list[dict]') -> 'list[dict]':
    "Using the provided filters, filter the provided data collection based on device information."

    if any(key in filters for key in ("model", "model_name")):
        if "model" in filters:
            model_set = frappe.db.sql(f"""
                select
                    distinct parent
                from
                    `tabService Device`
                where
                    parenttype = "Device SLA"
                    and model = "{filters['model']}";
            """)
        else:
            model_set = frappe.db.sql(f"""
                select
                    distinct parent
                from
                    `tabService Device`
                where
                    parenttype = "Device SLA"
                    and model_name like "%{filters['model_name']}%";
            """)

        model_set = {row[0] for row in model_set}

        data = [row for row in data if row['sla'] in model_set]

    return data


def get_costs(filters: dict, data: 'list[dict]') -> 'list[dict]':
    "Updates the table with the cost values."

    for i, row in enumerate(data):
        try:
            costs = frappe.db.sql(f"""
                select
                    ifnull(sum(case when month(GLE.posting_date) = 1 then debit - credit else 0 end), 0) jan,
                    ifnull(sum(case when month(GLE.posting_date) = 2 then debit - credit else 0 end), 0) feb,
                    ifnull(sum(case when month(GLE.posting_date) = 3 then debit - credit else 0 end), 0) mar,
                    ifnull(sum(case when month(GLE.posting_date) = 4 then debit - credit else 0 end), 0) apr,
                    ifnull(sum(case when month(GLE.posting_date) = 5 then debit - credit else 0 end), 0) may,
                    ifnull(sum(case when month(GLE.posting_date) = 6 then debit - credit else 0 end), 0) jun,
                    ifnull(sum(case when month(GLE.posting_date) = 7 then debit - credit else 0 end), 0) jul,
                    ifnull(sum(case when month(GLE.posting_date) = 8 then debit - credit else 0 end), 0) aug,
                    ifnull(sum(case when month(GLE.posting_date) = 9 then debit - credit else 0 end), 0) sep,
                    ifnull(sum(case when month(GLE.posting_date) = 10 then debit - credit else 0 end), 0) oct,
                    ifnull(sum(case when month(GLE.posting_date) = 11 then debit - credit else 0 end), 0) nov,
                    ifnull(sum(case when month(GLE.posting_date) = 12 then debit - credit else 0 end), 0) 'dec'
                from
                    `tabDelivery Note` DN
                join
                    `tabGL Entry` GLE on DN.name = GLE.voucher_no
                join
                    `tabAccount` A on GLE.account = A.name
                where
                    DN.sla = '{row['sla']}'
                    {"and year(GLE.posting_date) = " + filters['year'] if "year" in filters else ""}
                    and A.root_type = 'Expense'
                    and GLE.is_cancelled = 0;
            """, as_dict=True)[0]
        except IndexError:
            continue

        for month in MONTHS:
            data[i][month + "_cost"] += round(costs[month], 2)
            data[i][month] -= round(costs[month], 2)
            data[i]['total_cost'] += round(costs[month], 2)

    return data


def get_income(filters: dict, data: 'list[dict]') -> 'list[dict]':
    "Updates the table with the income values."

    for i, row in enumerate(data):
        try:
            income = frappe.db.sql(f"""
                select
                    ifnull(sum(case when month(GLE.posting_date) = 1 then credit - debit else 0 end), 0) jan,
                    ifnull(sum(case when month(GLE.posting_date) = 2 then credit - debit else 0 end), 0) feb,
                    ifnull(sum(case when month(GLE.posting_date) = 3 then credit - debit else 0 end), 0) mar,
                    ifnull(sum(case when month(GLE.posting_date) = 4 then credit - debit else 0 end), 0) apr,
                    ifnull(sum(case when month(GLE.posting_date) = 5 then credit - debit else 0 end), 0) may,
                    ifnull(sum(case when month(GLE.posting_date) = 6 then credit - debit else 0 end), 0) jun,
                    ifnull(sum(case when month(GLE.posting_date) = 7 then credit - debit else 0 end), 0) jul,
                    ifnull(sum(case when month(GLE.posting_date) = 8 then credit - debit else 0 end), 0) aug,
                    ifnull(sum(case when month(GLE.posting_date) = 9 then credit - debit else 0 end), 0) sep,
                    ifnull(sum(case when month(GLE.posting_date) = 10 then credit - debit else 0 end), 0) oct,
                    ifnull(sum(case when month(GLE.posting_date) = 11 then credit - debit else 0 end), 0) nov,
                    ifnull(sum(case when month(GLE.posting_date) = 12 then credit - debit else 0 end), 0) 'dec'
                from
                    `tabSales Invoice` SI
                join
                    `tabGL Entry` GLE on SI.name = GLE.voucher_no
                join
                    `tabAccount` A on GLE.account = A.name
                where
                    SI.sla = '{row['sla']}'
                    {"and year(GLE.posting_date) = " + filters['year'] if "year" in filters else ""}
                    and A.root_type = 'Income'
                    and GLE.is_cancelled = 0
            """, as_dict=True)[0]
        except IndexError:
            continue

        for month in MONTHS:
            data[i][month + "_income"] += round(income[month], 2)
            data[i][month] += round(income[month], 2)
            data[i]['total_income'] += round(income[month], 2)

    return data


def get_chart(filters: dict, data: 'list[dict]') -> dict or None:
    "Returns a dictionary that describes the chart to be displayed."

    chart = None
    if data:
        if "display_months" in filters:
            chart = {
                'title': "SLA Month on Month Comparison",
                'data': {
                    'labels': [month.upper() for month in MONTHS],
                    'datasets': [
                        {
                            'name': row['sla'],
                            'values': [row[month] for month in MONTHS]
                        } for row in data
                    ]
                },
                'type': 'line',
            }
        else:
            chart = {
                'title': "SLA P&L Comparison",
                'data': {
                    'labels': [row.sla for row in data],
                    'datasets': [
                        {
                            'name': _("Cost"),
                            'values': [row['total_cost'] for row in data]
                        },
                        {
                            'name': _("Income"),
                            'values': [row['total_income'] for row in data]
                        },
                        {
                            'name': _("Profit"),
                            'values': [row['profit'] for row in data]
                        },
                    ]
                },
                'type': "bar",
                # 'barOptions': {
                #     'stacked': 1
                # },
                'colors': ["red", "green", "#ffbd20"],
            }

    return chart


def get_summary(filters: dict, data: 'list[dict]') -> 'list[dict]':
    "Returns a list of dictionaries to be represented as the report summary."

    summary = [{
        'label': _("Number of SLAs"),
        'value': len(data),
        'indicator': "red" if len(data) < 1 else ""
    }]

    if data:
        monthly_costs, monthly_income = [], []
        for month in MONTHS:
            monthly_costs.append(sum([
                row[month + "_cost"]
                for row in data
            ]))
            monthly_income.append(sum([
                row[month + "_income"]
                for row in data
            ]))
        if "year" in filters and datetime.today().year != int(filters['year']):
            avg_cost = round(average(monthly_costs), 2)
            avg_income = round(average(monthly_income), 2)
        else:
            avg_cost = round(average(monthly_costs[: datetime.today().month]), 2)
            avg_income = round(average(monthly_income[: datetime.today().month]), 2)

        summary.extend([
            {
                'label': _("Average Monthly Costs"),
                'value': frappe.format_value(avg_cost, {'fieldtype': "Currency"}),
                'indicator': "red" if avg_cost > avg_income else ""
            },
            {
                'label': _("Average Monthly Income"),
                'value': frappe.format_value(avg_income, {'fieldtype': "Currency"}),
                'indicator': (
                    "red" if avg_income < avg_cost else (
                        "green" if avg_income > avg_cost * 1.5 else ""
                    )
                )
            },
        ])
    return summary
