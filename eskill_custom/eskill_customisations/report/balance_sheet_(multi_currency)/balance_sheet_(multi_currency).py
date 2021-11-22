# Copyright (c) 2021, Eskill Trading and contributors
# For license information, please see license.txt


from __future__ import unicode_literals

import frappe
from frappe import _

month_str_to_int = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12
}


def execute(filters=None):
    "Main function."

    single_period = False

    accumulated = True if "accumulated" in filters else False
    filters['accumulated'] = accumulated

    start_m, end_m = month_str_to_int[filters['start_m']], month_str_to_int[filters['end_m']]
    if filters['start_y'] == filters['end_y']:
        if start_m == end_m or filters['periodicity'] == "Yearly":
            single_period = True
        elif start_m > end_m:
            frappe.throw(_("Start date must not precede end date."))
    elif filters['start_y'] > filters['end_y']:
        frappe.throw(_("Start date must not precede end date."))

    # Create columns
    columns = [
        {
            'fieldname': "account",
            'label': _("Accounts"),
            'fieldtype': "Link",
            'options': "Account",
            'width': 300
        },
    ]
    columns.extend(get_columns(filters=filters, single_period=single_period))

    # Generate report data
    data = []
    data.extend(get_data(filters=filters, columns=columns, start_m=start_m, end_m=end_m, single_period=single_period, accumulated=filters['accumulated']))

    return columns, data


def get_columns(filters: 'dict[str, ]', single_period: bool = True):
    "Returns list of period based columns."

    if filters['periodicity'] == "Monthly":
        if single_period:
            cols = (
                f"{filters['start_m']} {filters['start_y']} (USD)",
                f"{filters['start_m']} {filters['start_y']} (ZWD)"
            )
        else:
            cols = (
                f"{filters['start_m']} {filters['start_y']} (USD)",
                f"{filters['start_m']} {filters['start_y']} (ZWD)",
                f"{filters['end_m']} {filters['end_y']} (USD)",
                f"{filters['end_m']} {filters['end_y']} (ZWD)"
            )
    else:
        if single_period:
            cols = (
                f"{filters['start_y']} (USD)",
                f"{filters['start_y']} (ZWD)"
            )
        else:
            cols = (
                f"{filters['start_y']} (USD)",
                f"{filters['start_y']} (ZWD)",
                f"{filters['end_y']} (USD)",
                f"{filters['end_y']} (ZWD)"
            )

    columns = []
    for col in cols:
        columns.append({
            'fieldname': col.lower().replace(" ", "_").replace("(", "").replace(")", ""),
            'label': col,
            'fieldtype': "Currency",
            'width': 150
        })

    if filters['accumulated']:
        for i, col in enumerate(columns):
            columns[i]['label'] = "Up to " + col['label']

    return columns


def get_data(start_m: int, end_m: int, filters: 'dict[str, ]', columns: 'list[dict[str, ]]', single_period: bool = False, accumulated: bool = False) -> list:
    "Get report data."

    blank_row = {
        'account': "",
        'account_type': None,
        'header': 0,
        'parent': None,
        'total': 0
    }
    for i in range(1, len(columns)):
        blank_row[columns[i]['fieldname']] = None

    last_day_0 = frappe.db.sql(f"select last_day('{filters['start_y']}-{start_m}-1')")[0][0]
    last_day_1 = frappe.db.sql(f"select last_day('{filters['end_y']}-{end_m}-1')")[0][0]

    if single_period:
        if filters['periodicity'] == "Yearly":
            date_range = [f"year(GLE.posting_date) {'<' if accumulated else ''}= {filters['start_y']}"]
        else:
            if accumulated:
                date_range = [f"GLE.posting_date <= '{last_day_0}'"]
            else:
                date_range = [f"(month(GLE.posting_date) = {start_m} and year(GLE.posting_date) = {filters['start_y']})"]
    else:
        if filters['periodicity'] == "Yearly":
            date_range = [
                f"year(GLE.posting_date) {'<' if accumulated else ''}= {filters['start_y']}",
                f" year(GLE.posting_date) {'<' if accumulated else ''}= {filters['end_y']}"
            ]
        else:
            if accumulated:
                date_range = [
                    f"GLE.posting_date <= '{last_day_0}'",
                    f"GLE.posting_date <= '{last_day_1}'"
                ]
            else:
                date_range = [
                    f"(month(GLE.posting_date) = {start_m} and year(GLE.posting_date) = {filters['start_y']})",
                    f"(month(GLE.posting_date) = {end_m} and year(GLE.posting_date) = {filters['end_y']})"
                ]

    # Create cost center query for where statement
    if "cost_center" in filters:
        cost_center = f" and GLE.cost_center = '{filters['cost_center']}'"
    else:
        cost_center = ""

    # Initialise data
    data = initialise_data(columns, single_period, blank_row)

    # List of documents that affect Asset & Liability
    doc_list = [
        "Delivery Note",
        "Sales Invoice",
        "Landed Cost Voucher",
        "Payment Entry",
        "Purchase Invoice",
        "Purchase Receipt",
        "Stock Entry",
        "Stock Reconciliation"
    ]

    # Get account totals
    for doctype in doc_list:
        new_data = get_account_data([columns[1], columns[2]], date_range[0], cost_center, doctype)
        for i, row in enumerate(new_data):
            index = next(j for j, account in enumerate(data) if account['account'] == row['account'])
            data[index][columns[1]['fieldname']] += row[columns[1]['fieldname']]
            data[index][columns[2]['fieldname']] += row[columns[2]['fieldname']]
        if not single_period:
            new_data = get_account_data([columns[3], columns[4]], date_range[1], cost_center, doctype)
            for i, row in enumerate(new_data):
                index = next(j for j, account in enumerate(data) if account['account'] == row['account'])
                data[index][columns[3]['fieldname']] += row[columns[3]['fieldname']]
                data[index][columns[4]['fieldname']] += row[columns[4]['fieldname']]

    # Get data from journal entries
    new_data = get_journal_data([columns[1], columns[2]], date_range[0], cost_center)
    for i, row in enumerate(new_data):
        index = next(j for j, account in enumerate(data) if account['account'] == row['account'])
        data[index][columns[1]['fieldname']] += row[columns[1]['fieldname']]
        data[index][columns[2]['fieldname']] += row[columns[2]['fieldname']]
    if not single_period:
        new_data = get_journal_data([columns[3], columns[4]], date_range[1], cost_center)
        for i, row in enumerate(new_data):
            index = next(j for j, account in enumerate(data) if account['account'] == row['account'])
            data[index][columns[3]['fieldname']] += row[columns[3]['fieldname']]
            data[index][columns[4]['fieldname']] += row[columns[4]['fieldname']]

    # Calculate header totals
    for i, account in enumerate(data):
        if account['header'] or not account['parent']:
            continue
        index = next(i for i, record in enumerate(data) if record['account'] == account['parent'])
        data[i]['indent'] = data[index]['indent'] + 1
        for j in range(1, len(columns)):
            data[index][columns[j]['fieldname']] += account[columns[j]['fieldname']]
    for account in data:
        if not account['header'] or not account['parent']:
            continue
        index = next(i for i, record in enumerate(data) if record['account'] == account['parent'])
        for i in range(1, len(columns)):
            data[index][columns[i]['fieldname']] += account[columns[i]['fieldname']]

    # Adding in start and end dates for opening ledger report on specific accounts
    first_day = frappe.db.sql(f"select date_format('{filters['start_y']}-{start_m}-1', '%Y-%m-%d')")[0][0]
    for i, account in enumerate(data):
        data[i]['from_date'] = first_day if account['account'] else ""
        data[i]['to_date'] = last_day_1 if account['account'] else ""

    # Calculate totals
    for i, account in enumerate(data):
        if not account['total']:
            continue
        for j in range(i):
            if data[j]['account_type'] != account['account_type'] or data[j]['indent'] != 0:
                continue
            for k in range(1, len(columns)):
                data[i][columns[k]['fieldname']] += data[j][columns[k]['fieldname']]

    # Calculate provisonal profit
    data.append({
        'account': "Provisional Profit/Loss",
        'account_type': None,
        'header': 1,
        'indemt': 0,
        'total': 1
    })
    for i in range(1, len(columns)):
        total = 0
        for j, account in enumerate(data):
            if not account['total'] or columns[i]['fieldname'] not in account:
                continue
            total += account[columns[i]['fieldname']]
        data[-1][columns[i]['fieldname']] = total


    return data


def initialise_data(columns: 'list[dict[str, ]]', single_period: bool, blank_row: 'dict[str, ]') -> list:
    "Initialises data table."

    data = []
    balance_columns = f"0 {columns[1]['fieldname']}, 0 {columns[2]['fieldname']}"
    totals = {
        'assets': {
            'account': "Total Assets",
            'parent': None,
            'total': 1,
            'header': 1,
            'indent': 0,
            'account_type': "Asset"
        },
        'liabilities': {
            'account': "Total Liabilities",
            'parent': None,
            'total': 1,
            'header': 1,
            'indent': 0,
            'account_type': "Liability"
        },
        'equity': {
            'account': "Total Equity",
            'parent': None,
            'total': 1,
            'header': 1,
            'indent': 0,
            'account_type': "Equity"
        },
    }
    for key in totals:
        for i in range(1, len(columns)):
            totals[key][columns[i]['fieldname']] = 0
    if not single_period:
        balance_columns += f", 0 {columns[3]['fieldname']}, 0 {columns[4]['fieldname']}"

    # Assets
    data.extend([
        *frappe.db.sql(f"""\
            select
                name account,
                {balance_columns},
                (case when parent_account then 1 else 0 end) indent,
                (case when is_group then 1 else 0 end) header,
                'Asset' account_type,
                parent_account parent,
                0 total
            from
                tabAccount
            where
                root_type = 'Asset' or account_number like '75%'
            order by
                lft;""",
            as_dict=1
        ),
        totals['assets'],
        blank_row
    ])

    # Liabilities
    data.extend([
        *frappe.db.sql(f"""\
            select
                name account,
                {balance_columns},
                (case when parent_account then 1 else 0 end) indent,
                (case when is_group then 1 else 0 end) header,
                'Liability' account_type,
                parent_account parent,
                0 total
            from
                tabAccount
            where
                root_type = 'Liability'
            order by
                lft;""",
            as_dict=1
        ),
        totals['liabilities'],
        blank_row
    ])

    # Equity
    data.extend([
        *frappe.db.sql(f"""\
            select
                name account,
                {balance_columns},
                (case when parent_account then 1 else 0 end) indent,
                (case when is_group then 1 else 0 end) header,
                'Equity' account_type,
                parent_account parent,
                0 total
            from
                tabAccount
            where
                root_type = 'Equity'
            order by
                lft;""",
            as_dict=1
        ),
        totals['equity'],
        blank_row
    ])

    return data


def get_account_data(columns: 'list[dict[str, ]]', date_range: str, cost_center: str, doctype: str) -> list:
    "Get data based on GL Entries."

    data = []

    has_currency = frappe.db.sql(f"""\
        select
            true
        from
            information_schema.columns
        where
            table_schema = '{frappe.conf.get('db_name')}' and table_name = 'tab{doctype}' and column_name = 'currency'""")

    if len(has_currency):
        column2 = """\
            sum(case when
                    doc.currency = "ZWD"
                then
                    (debit - credit) / doc.conversion_rate
                else
                    (debit - credit) * doc.auction_bid_rate
                end)"""
    else:
        column2 = "sum((debit - credit) * doc.auction_bid_rate)"

    data.extend(frappe.db.sql(f"""\
        select
            GLE.account account,
            sum(debit - credit) {columns[0]['fieldname']},
            {column2} {columns[1]['fieldname']}
        from
            `tabGL Entry` GLE
        join
            tabAccount A on GLE.account = A.name
        join
            `tab{doctype}` doc on GLE.voucher_no = doc.name
        where
            {date_range} and A.report_type = 'Balance Sheet'{cost_center}
        group by
            GLE.account
        having
            {columns[0]['fieldname']} <> 0""",
        as_dict=1))

    return data


def get_journal_data(columns: 'list[dict[str, ]]', date_range: str, cost_center: str) -> list:
    "Get data based from Journal Entries."

    data = []

    data.extend(frappe.db.sql(f"""\
        select
            GLE.account account,
            sum(GLE.debit - GLE.credit) {columns[0]['fieldname']},
            sum((GLE.debit - GLE.credit) * (case
                when
                    doc.multi_currency
                then
                    (case when
                        1 / (select
                            avg(JEA2.exchange_rate)
                        from
                            `tabJournal Entry Account` JEA2
                        where
                            JEA2.parent = GLE.voucher_no and JEA2.account_currency = "ZWD")
                    then
                        1 / (select
                            avg(JEA2.exchange_rate)
                        from
                            `tabJournal Entry Account` JEA2
                        where
                            JEA2.parent = GLE.voucher_no and JEA2.account_currency = "ZWD")
                    else
                        doc.auction_bid_rate
                    end)
                else
                    doc.auction_bid_rate
                end)) {columns[1]['fieldname']}
        from
            `tabGL Entry` GLE
        join
            tabAccount A on GLE.account = A.name
        join
            `tabJournal Entry` doc on GLE.voucher_no = doc.name
        where
            {date_range} and A.report_type = 'Balance Sheet'{cost_center}
        group by
            GLE.account
        having
            {columns[0]['fieldname']} <> 0""",
        as_dict=1))

    return data
