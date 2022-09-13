# Copyright (c) 2022, Eskill Trading and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters: dict = None):
    "Main function."

    columns, data, summary = [], [], []

    columns.extend(get_columns())
    data.extend(get_data(filters))
    summary.extend(get_summary(data))

    return columns, data, None, None, summary


def get_columns() -> 'list[dict]':
    "Returns a list of columns"

    columns = [
        {
            'fieldname': "service_order",
            'label': _("Service Order"),
            'fieldtype': "Link",
            'options': "Service Order",
            'width': 125
        },
        {
            'fieldname': "customer",
            'label': _("Customer"),
            'fieldtype': "Text",
            'width': 300
        },
        {
            'fieldname': "start_date",
            'label': _("Start Date"),
            'fieldtype': "Date",
            'width': 105
        },
        {
            'fieldname': "days_open",
            'label': _("Days Open"),
            'fieldtype': "Int",
            # 'width': 105
        },
        {
            'fieldname': "job_type",
            'label': _("Job Type"),
            'fieldtype': "Text",
        },
        {
            'fieldname': "job_status",
            'label': _("Job Status"),
            'fieldtype': "Text",
            'width': 270
        },
        {
            'fieldname': "assigned_technician",
            'label': _("Assigned Technician"),
            'fieldtype': "Link",
            'options': "Sales Person"
        },
    ]

    return columns


def get_data(filters: dict) -> 'list[dict]':
    "Returns a list containing the report data."

    where_statement = get_where_statement(filters)

    data = frappe.db.sql(f"""
        select
            SO.name service_order,
            SO.customer_name customer,
            SO.start_date,
            tab2.days_open,
            SO.job_type,
            (case
                when
                    SO.job_status = "On Hold"
                then
                    concat(SO.job_status, ": ", SO.reason_on_hold)
                else
                    (case
                        when
                            SO.job_status = "Closed"
                        then
                            concat(SO.job_status, ": ", SO.billing_status)
                        else
                            SO.job_status
                    end)
            end) job_status,
            SO.assigned_technician,
            (case
                when
                    SO.job_status = "Open"
                then
                    (case
                        when
                            (SO.job_type in ("SLA", "Warranty")
                            and tab2.days_open > 2)
                            or (SO.job_type = "Billable"
                            and tab2.days_open > 7)
                        then
                            1
                        else
                            0
                    end)
                else
                    0
            end) overdue
        from
            `tabService Order` SO
        join
            (select
                name,
                (case
                    when
                        job_status = "Closed"
                        and closing_date = '{filters['report_date']}'
                    then
                        datediff(closing_date, start_date)
                    else
                        datediff('{filters['report_date']}', start_date)
                end) days_open
            from
                `tabService Order`) tab2 on SO.name = tab2.name
        {where_statement}
        order by
            job_type desc, days_open desc, job_status, `customer`;
    """, as_dict=True)

    return data


def get_where_statement(filters: dict) -> str:
    "Generates a where statement based on the given filters."

    # get a list of conditions
    where_list = []
    if "report_date" in filters:
        where_list.append(f"SO.start_date <= '{filters['report_date']}'")
        where_list.append(f"""
            (case
                when
                    SO.job_status = "Closed"
                then
                    SO.closing_date = '{filters['report_date']}'
                else
                    true
            end)
        """)

    if "customer" in filters:
        where_list.append(f"SO.customer = '{filters['customer']}'")
    if "customer_name" in filters:
        where_list.append(f"SO.customer_name like '%{filters['customer_name']}%'")

    if "job_type" in filters:
        where_list.append(f"SO.job_type = '{filters['job_type']}'")
    if "technician" in filters:
        where_list.append(f"SO.assigned_technician = '{filters['technician']}'")

    # convert the list of conditions into a single where statement string
    where_statement = ""
    if len(where_list) > 0:
        where_statement += f"where {where_list[0]}"
        for i in range(1, len(where_list)):
            where_statement += f" and {where_list[i]}"

    return where_statement


def get_summary(data: 'list[dict]') -> 'list[dict]':
    "Returns a list of summary dicts based on a given data set."

    num_open, num_on_hold, num_closed, num_overdue = 0, 0, 0, 0
    days_open = 0

    for __, row in enumerate(data):
        current_status = row['job_status'].split(":")[0]
        if current_status == "Open":
            num_open += 1
        elif current_status == "On Hold":
            num_on_hold += 1
        else:
            num_closed += 1

        if row.overdue:
            num_overdue += 1

        days_open += row['days_open']

    average_days = round(days_open / len(data), 3) if len(data) > 0 else 0
    summary = [
        {
            'label': _("Open Orders"),
            'value': frappe.format(num_open, {'fieldtype': "Int"})
        },
        {
            'label': _("On Hold Orders"),
            'value': frappe.format(num_on_hold, {'fieldtype': "Int"})
        },
        {
            'label': _("Closed Orders"),
            'value': frappe.format(num_closed, {'fieldtype': "Int"})
        },
        {
            'label': _("Orders Overdue"),
            'value': frappe.format(num_overdue, {'fieldtype': "Int"})
        },
        {
            'label': _("Average Days Open"),
            'value': frappe.format(average_days, {'fieldtype': "Float"})
        },
    ]

    return summary
