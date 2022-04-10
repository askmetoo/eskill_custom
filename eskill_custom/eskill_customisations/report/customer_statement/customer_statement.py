# Copyright (c) 2022, Eskill Trading and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    "Main function."
    columns = []
    columns.extend(get_columns())

    data = []
    data.extend(get_data(filters))

    return columns, data


def get_columns():
    "Returns a list of columns."

    columns = [
        {
            'fieldname': "posting_date",
            'label': _("Posting Date"),
            'fieldtype': "Date",
            'width': 105
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
            'width': 250
        },
        {
            'fieldname': "currency",
            'label': _("Account Currency"),
            'fieldtype': "Link",
            'options': "Currency",
            'hidden': 1,
            'print_hide': 1
        },
        {
            'fieldname': "debit",
            'label': _("Debit"),
            'fieldtype': "Currency",
            'options': "currency",
            'width': 250
        },
        {
            'fieldname': "credit",
            'label': _("Credit"),
            'fieldtype': "Currency",
            'options': "currency",
            'width': 250
        },
        {
            'fieldname': "balance",
            'label': _("Balance"),
            'fieldtype': "Currency",
            'options': "currency",
            'width': 250
        },
        {
            'fieldname': "against_voucher_type",
            'label': _("Against Voucher Type"),
            'fieldtype': "Data",
        },
        {
            'fieldname': "against_voucher",
            'label': _("Against Voucher"),
            'fieldtype': "Dynamic Link",
            'options': "against_voucher_type",
            'width': 400
        },
    ]

    return columns


def get_data(filters: 'dict[str, ]') -> list:
    "Get report data."

    opening = {
        'voucher_no': "Opening",
        'debit': 0,
        'credit': 0,
        'balance': 0
    }
    data = frappe.db.sql(f"""\
        select
            ifnull(sum(debit_in_account_currency), 0) debit,
            ifnull(sum(credit_in_account_currency), 0) credit
        from
            `tabGL Entry`
        where
            party = '{filters['party']}'
            and posting_date < '{filters['from_date']}'
            and docstatus = 1
            and is_cancelled = 0;""",
        as_dict=1
    )
    if len(data[0]) > 0:
        for _, row in enumerate(data):
            opening['debit'] = row['debit']
            opening['credit'] = row['credit']
            opening['balance'] = row['debit'] - row['credit']
            break

    data = frappe.db.sql(f"""\
        select
            posting_date,
            voucher_type,
            voucher_no,
            sum(debit_in_account_currency) debit,
            sum(credit_in_account_currency) credit,
            0 balance,
            against_voucher_type,
            against_voucher
        from
            `tabGL Entry`
        where
            party = '{filters['party']}'
            and posting_date >= '{filters['from_date']}'
            and posting_date <= '{filters['to_date']}'
            and docstatus = 1
            and is_cancelled = 0
        group by
            voucher_no
        order by
            posting_date, voucher_no;""",
        as_dict=1
    )

    total = {
        'voucher_no': "Total",
        'debit': 0,
        'credit': 0,
        'balance': 0
    }
    for i, row in enumerate(data):
        if i == 0:
            data[i]['balance'] = row['debit'] - row['credit'] + opening['balance']
        else:
            data[i]['balance'] = row['debit'] - row['credit'] + data[i - 1]['balance']
        total['debit'] += row['debit']
        total['credit'] += row['credit']
    total['balance'] = total['debit'] - total['credit']
    closing = {
        'voucher_no': "Closing (Opening + Total)",
        'debit': opening['debit'] + total['debit'],
        'credit': opening['credit'] + total['credit'],
    }
    closing['balance'] = closing['debit'] - closing['credit']

    data.insert(0, opening)
    data.append(total)
    data.append(closing)

    for i, _ in enumerate(data):
        data[i]['currency'] = filters['account_currency']

    return data
