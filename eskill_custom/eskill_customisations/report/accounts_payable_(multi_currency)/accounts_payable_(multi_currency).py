# Copyright (c) 2022, Eskill Trading and contributors
# For license information, please see license.txt

from datetime import date
from decimal import DivisionByZero
from locale import currency

import frappe
from frappe import _


def execute(filters=None):
    "Main function."

    columns = []
    columns.extend(get_columns(filters))

    data = []
    data.extend(get_data(filters, columns))

    for index, record in enumerate(data):
        for col in columns:
            if col['fieldname'] not in record:
                data[index][col['fieldname']] = ""

    chart = get_chart_data(filters, data, columns)

    return columns, data, None, chart


def get_columns(filters: 'dict[str, ]'):
    "Returns a list of columns."

    columns = [
        {
            'fieldname': "posting_date",
            'label': _("Posting Date"),
            'fieldtype': "Date",
            'width': 105
        },
        {
            'fieldname': "due_date",
            'label': _("Due Date"),
            'fieldtype': "Date",
            'width': 105,
            'hidden': 0 if "show_due_date" in filters else 1
        },
        {
            'fieldname': "supplier",
            'label': _("Supplier"),
            'fieldtype': "Link",
            'options': "Supplier",
            'width': 115
        },
        {
            'fieldname': "supplier_name",
            'label': _("Supplier Name"),
            'fieldtype': "Text",
            'width': 300
        },
        {
            'fieldname': "currency",
            'label': _("Account Currency"),
            'fieldtype': "Link",
            'options': "Currency"
        },
        {
            'fieldname': "report_currency",
            'label': _("Report Currency"),
            'fieldtype': "Link",
            'options': "Currency",
            'hidden': 1
        },
        {
            'fieldname': "voucher_type",
            'label': _("Voucher Type"),
            'fieldtype': "Data",
        },
        {
            'fieldname': "voucher_no",
            'label': _("Voucher No"),
            'fieldtype': "Dynamic Link",
            'options': "voucher_type",
            'width': 120
        },
        {
            'fieldname': 'cost_center',
            'label': _("Cost Center"),
            'fieldtype': "Link",
            'options': "Cost Center",
            'hidden': 0 if "show_cost_center" in filters else 1
        },
        {
            'fieldname': 'supplier_group',
            'label': _("Supplier Group"),
            'fieldtype': "Link",
            'options': "Supplier Group",
            'hidden': 0 if "show_supplier_group" in filters else 1
        },
        {
            'fieldname': "age",
            'label': _("Age (Days)"),
            'fieldtype': "Data",
            'width': 95
        },
        {
            'fieldname': "exchange_rate",
            'label': _("Exchange Rate"),
            'fieldtype': "Float",
            'precision': 4
        },
        {
            'fieldname': "total_credit",
            'label': _("Total Credit (Base)"),
            'fieldtype': "Currency",
            'options': "Company:company:default_currency",
            'default': 0
        },
        {
            'fieldname': "total_credit_account",
            'label': _(f"Total Credit ({filters['currency'] if 'currency' in filters else 'Account'})"),
            'fieldtype': "Currency",
            'options': 'report_currency' if 'currency' in filters else 'currency',
            'default': 0
        },
        {
            'fieldname': "range1_base",
            'label': _(f"0-{filters['range1']} Base"),
            'fieldtype': "Currency",
            'options': "Company:company:default_currency",
            'default': 0,
            'urgency': 1
        },
        {
            'fieldname': "range1_account",
            'label': _(f"0-{filters['range1']} {filters['currency'] if 'currency' in filters else 'Account'}"),
            'fieldtype': "Currency",
            'options': 'report_currency' if 'currency' in filters else 'currency',
            'default': 0,
            'urgency': 1
        },
        {
            'fieldname': "range2_base",
            'label': _(f"{filters['range1'] + 1}-{filters['range2']} Base"),
            'fieldtype': "Currency",
            'options': "Company:company:default_currency",
            'default': 0,
            'urgency': 2
        },
        {
            'fieldname': "range2_account",
            'label': _(f"{filters['range1'] + 1}-{filters['range2']} {filters['currency'] if 'currency' in filters else 'Account'}"),
            'fieldtype': "Currency",
            'options': 'report_currency' if 'currency' in filters else 'currency',
            'default': 0,
            'urgency': 2
        },
        {
            'fieldname': "range3_base",
            'label': _(f"{filters['range2'] + 1}-{filters['range3']} Base"),
            'fieldtype': "Currency",
            'options': "Company:company:default_currency",
            'default': 0,
            'urgency': 3
        },
        {
            'fieldname': "range3_account",
            'label': _(f"{filters['range2'] + 1}-{filters['range3']} {filters['currency'] if 'currency' in filters else 'Account'}"),
            'fieldtype': "Currency",
            'options': 'report_currency' if 'currency' in filters else 'currency',
            'default': 0,
            'urgency': 3
        },
        {
            'fieldname': "range4_base",
            'label': _(f"{filters['range3'] + 1}-{filters['range4']} Base"),
            'fieldtype': "Currency",
            'options': "Company:company:default_currency",
            'default': 0,
            'urgency': 4
        },
        {
            'fieldname': "range4_account",
            'label': _(f"{filters['range3'] + 1}-{filters['range4']} {filters['currency'] if 'currency' in filters else 'Account'}"),
            'fieldtype': "Currency",
            'options': 'report_currency' if 'currency' in filters else 'currency',
            'default': 0,
            'urgency': 4
        },
        {
            'fieldname': "range5_base",
            'label': _(f"{filters['range4'] + 1}-Above Base"),
            'fieldtype': "Currency",
            'options': "Company:company:default_currency",
            'default': 0,
            'urgency': 5
        },
        {
            'fieldname': "range5_account",
            'label': _(f"{filters['range4'] + 1}-Above {filters['currency'] if 'currency' in filters else 'Account'}"),
            'fieldtype': "Currency",
            'options': 'report_currency' if 'currency' in filters else 'currency',
            'default': 0,
            'urgency': 5
        },
    ]

    return columns


def get_data(filters: 'dict[str, ]', columns: 'list[dict]') -> list:
    "Get report data."

    total_columns = list(columns[-10:])

    data = initialise_data(filters, columns)
    if "currency" in filters and filters['currency'] != "ZWL":
        rates = get_exchange_rates(filters)

    values = get_debts(filters)
    if values:
        for value in values:
            if value['against_voucher']:
                try:
                    index = next(
                        i
                        for i, record in enumerate(data)
                        if record['voucher_no'] == value['against_voucher']
                        and record['supplier'] == value['supplier']
                    )
                except StopIteration:
                    index = next(
                        i
                        for i, record in enumerate(data)
                        if record['voucher_no'] == value['voucher_no']
                        and record['supplier'] == value['supplier']
                    )
            else:
                index = next(
                    i
                    for i, record in enumerate(data)
                    if record['voucher_no'] == value['voucher_no']
                    and record['supplier'] == value['supplier']
                )
            data[index]['total_credit'] += value['main']
            if "currency" in filters and filters['currency'] != data[index]['currency']:
                if filters['currency'] == "ZWL":
                    data[index]['total_credit_account'] += (
                        value['main']
                        * data[index]['exchange_rate']
                    )
                    continue
                if rates:
                    try:
                        data[index]['total_credit_account'] += value['main'] * next(
                            record['rate']
                            for record in rates
                            if record['date'] <= value['posting_date']
                        )
                    except StopIteration:
                        data[index]['total_credit_account'] += value['main'] * rates[-1]['rate']
            else:
                data[index]['total_credit_account'] += value['account']

    if "currency" in filters and filters['currency'] != "ZWL" and not rates:
        frappe.msgprint(f"There are no exchange rates to convert to {filters['currency']}")

    data = [
        record
        for record in data
        if round(record['total_credit'], 2) or round(record['total_credit_account'], 2)
    ]
    for i, row in enumerate(data):
        if row['voucher_no'] is not None and row['currency'] == filters['currency']:
            try:
                data[i]['exchange_rate'] = (
                    row['total_credit_account']
                    / row['total_credit']
                )
            except DivisionByZero:
                data[i]['exchange_rate'] = 0

    if "cost_center" in filters:
        data = [record for record in data if record['cost_center'] == filters['cost_center']]
    if "supplier" in filters:
        data = [record for record in data if record['supplier'] == filters['supplier']]
    if "supplier_group" in filters:
        data = [record for record in data if record['supplier_group'] == filters['supplier_group']]

    for index, record in enumerate(data):
        if record['age'] <= filters['range1']:
            age_range = 0
        elif record['age'] <= filters['range2']:
            age_range = 2
        elif record['age'] <= filters['range3']:
            age_range = 4
        elif record['age'] <= filters['range4']:
            age_range = 6
        else:
            age_range = 8

        data[index][total_columns[age_range]['fieldname']] = record['total_credit']
        data[index][total_columns[age_range + 1]['fieldname']] = record['total_credit_account']

    if len(data) > 0:
        if 'group_by_party' in filters:
            old_data = data
            data = [old_data[0]]

            supplier_total = {
                'currency': data[0]['currency'],
                'supplier': data[0]['supplier'],
                'supplier_name': data[0]['supplier_name'],
                'posting_date': data[0]['posting_date'],
                'total': 1,
                'total_credit': data[0]['total_credit'],
                'total_credit_account': data[0]['total_credit_account']
            }
            for col in total_columns:
                supplier_total[col['fieldname']] = data[0][col['fieldname']]

            for index, record in enumerate(old_data[1:]):
                if supplier_total['supplier_name'] == record['supplier_name']:
                    if record['posting_date'] > supplier_total['posting_date']:
                        supplier_total['posting_date'] = record['posting_date']
                    supplier_total['total_credit'] += record['total_credit']
                    supplier_total['total_credit_account'] += record['total_credit_account']
                    for col in total_columns:
                        supplier_total[col['fieldname']] += record[col['fieldname']]
                else:
                    data.append(supplier_total)
                    data.append({})
                    supplier_total = {
                        'currency': record['currency'],
                        'supplier': record['supplier'],
                        'supplier_name': record['supplier_name'],
                        'posting_date': record['posting_date'],
                        'total': 1,
                        'total_credit': record['total_credit'],
                        'total_credit_account': record['total_credit_account']
                    }
                    for col in total_columns:
                        supplier_total[col['fieldname']] = record[col['fieldname']]
                data.append(record)
            data.append(supplier_total)

        data.extend([{}, add_total_row(data, columns)])
        data[-1][columns[0]['fieldname']] = date(*[
            int(i)
            for i in filters['report_date'].split("-")
        ])
        data[-1]['supplier'] = "Final Total"

    if "currency" in filters:
        for index, record in enumerate(data):
            data[index]['report_currency'] = filters['currency']

    return data


def initialise_data(filters: 'dict[str, ]', columns: 'list[dict]'):
    "Initialise report data."

    age_query = f"datediff('{filters['report_date']}', GLE.posting_date)" if filters['aging_based_on'] == "Posting Date" else f"datediff('{filters['report_date']}', ifnull(GLE.due_date, GLE.posting_date))"

    data = frappe.db.sql(f"""\
        select
            {age_query} age,
            A.account_currency currency,
            GLE.cost_center,
            GLE.party supplier,
            S.supplier_name,
            S.supplier_group,
            GLE.due_date,
            GLE.posting_date,
            0 total,
            GLE.voucher_no,
            GLE.voucher_type
        from
            `tabGL Entry` GLE
        join
            tabAccount A on GLE.account = A.name
        join
            tabSupplier S on GLE.party = S.name
        where
            A.creditors_account and GLE.posting_date <= '{filters['report_date']}'
        group by
            GLE.party, GLE.voucher_no
        order by
            S.supplier_name, GLE.posting_date, GLE.voucher_no;""", as_dict=1)

    for i, row in enumerate(data):
        if "currency" in filters and filters['currency'] == "ZWL" and row['currency'] != "ZWL":
            data[i]['exchange_rate'] = frappe.get_value(
                row['voucher_type'],
                row['voucher_no'],
                "auction_bid_rate"
            )
        for col in columns:
            if col['fieldname'] in data[i]:
                if not data[i][col['fieldname']]:
                    data[i][col['fieldname']] = 0
            else:
                data[i][col['fieldname']] = 0

    return data


def get_exchange_rates(filters: 'dict[str, ]'):
    "Return list of applicable exchange rates."

    rates = []

    if "currency" in filters:
        currency = frappe.db.sql(f"""\
            select
                default_currency
            from
                tabCompany
            where
                name = '{filters['company']}';""")[0][0]

        rates.extend(frappe.db.sql(f"""\
            select
                date,
                max(exchange_rate) rate
            from
                `tabCurrency Exchange`
            where
                date <= '{filters['report_date']}' and from_currency = '{currency}' and to_currency = '{filters['currency']}'
            group by
                date
            order by
                date desc;""", as_dict=1))

    return rates


def get_debts(filters: 'dict[str, ]'):
    "Return list of entry values."

    data = []

    data.extend(frappe.db.sql(f"""\
        select
            round(sum(GLE.credit_in_account_currency - GLE.debit_in_account_currency), 2) account,
            GLE.against_voucher,
            GLE.against_voucher_type,
            GLE.party supplier,
            round(sum(GLE.credit - GLE.debit), 2) main,
            GLE.posting_date,
            GLE.voucher_no
        from
            `tabGL Entry` GLE
        join
            tabAccount A on GLE.account = A.name
        where
            A.creditors_account and GLE.posting_date <= '{filters['report_date']}'
        group by
            GLE.party, GLE.posting_date, GLE.voucher_no, GLE.against_voucher;""", as_dict=1))

    return data


def add_total_row(data: 'list[dict]', columns: 'list[dict]') -> 'dict[str, ]':
    "Returns grand total row."

    total_row = {}

    for col in columns:
        if col['fieldtype'] == "Currency":
            total_row[col['fieldname']] = 0
            for record in data:
                if 'total' in record:
                    if not record['total']:
                        total_row[col['fieldname']] += record[col['fieldname']]

    total_row['total'] = 1

    return total_row


def get_chart_data(filters: 'dict[str]', data: 'list[dict]', columns: 'list[dict]'):
    "Returns chart data for visualising debt age."

    chart = {}

    if "group_by_party" in filters:
        rows = []
        rows.append({
            'values': [
                record['total_credit']
                for record in data[:-1]
                if "total" in record and record['total']
            ]
        })
        column_labels = [
            record['supplier_name']
            for record in data
            if "total" in record and record['total']
        ]

        chart = {
            'barOptions': {
                'spaceRatio': 0.2,
            },
            'colors': [
                "#00FF00"
            ],
            'data': {
                'labels': column_labels,
                'datasets': rows
            },
            'title': "Accounts Payable",
            'type': "bar"
        }

    return chart
