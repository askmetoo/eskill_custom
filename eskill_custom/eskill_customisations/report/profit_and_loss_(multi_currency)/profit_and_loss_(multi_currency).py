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

    data = []
    data.extend(get_data(filters=filters, columns=columns, start_m=start_m, end_m=end_m, single_period=single_period, accumulated=filters['accumulated']))

    return columns, data, None, None


def get_columns(filters: dict, single_period: bool = True):
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
        for i in range(len(columns)):
            columns[i]['label'] = "Up to " + columns[i]['label']

    return columns


def get_data(start_m: int, end_m: int, filters: dict, columns: list, single_period: bool = False, accumulated: bool = False) -> list:
    "Get report data."

    blank_row = {'account': ""}
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

    # Initialise data
    headers, data = initialise_data(columns, date_range, single_period, blank_row)

    # List of documents that affect Income & Expense
    doc_list = [
        "Delivery Note",
        "Journal Entry",
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
        new_data = get_account_data([columns[1], columns[2]], date_range[0], doctype)
        for i in range(len(new_data)):
            index = next(j for j, account in enumerate(data) if account['account'] == new_data[i]['account'])
            data[index][columns[1]['fieldname']] += new_data[i][columns[1]['fieldname']]
            data[index][columns[2]['fieldname']] += new_data[i][columns[2]['fieldname']]
        if not single_period:
            new_data = get_account_data([columns[3], columns[4]], date_range[1], doctype)
            for i in range(len(new_data)):
                index = next(j for j, account in enumerate(data) if account['account'] == new_data[i]['account'])
                data[index][columns[3]['fieldname']] += new_data[i][columns[3]['fieldname']]
                data[index][columns[4]['fieldname']] += new_data[i][columns[4]['fieldname']]

    # Calculate header totals
    for header in headers:
        index = next(i for i, account in enumerate(data) if account['account'] == header['account'])
        for account in data:
            if not account['header'] and not account['total'] and account['account']:
                if account['parent'] == header['account']:
                    data[index][columns[1]['fieldname']] += account[columns[1]['fieldname']]
                    data[index][columns[2]['fieldname']] += account[columns[2]['fieldname']]
                    if not single_period:
                        data[index][columns[3]['fieldname']] += account[columns[3]['fieldname']]
                        data[index][columns[4]['fieldname']] += account[columns[4]['fieldname']]

    # Adding in start and end dates for opening ledger report on specific accounts
    first_day = frappe.db.sql(f"select date_format('{filters['start_y']}-{start_m}-1', '%Y-%m-%d')")[0][0]
    for i, account in enumerate(data):
        data[i]['from_date'] = first_day if account['account'] else ""
        data[i]['to_date'] = last_day_1 if account['account'] else ""

    # Calculate net profit
    index = next(i for i, account in enumerate(data) if account['total'])
    for i, account in enumerate(data):
        if account['header']:
            data[index][columns[1]['fieldname']] += account[columns[1]['fieldname']]
            data[index][columns[2]['fieldname']] += account[columns[2]['fieldname']]
            if not single_period:
                data[index][columns[3]['fieldname']] += account[columns[3]['fieldname']]
                data[index][columns[4]['fieldname']] += account[columns[4]['fieldname']]

    return data


def initialise_data(columns, date_range, single_period, blank_row) -> list:
    "Initialises data table."

    headers, data =  [], []

    if single_period:
        headers.extend(frappe.db.sql(f"""\
select
    A.parent_account account,
    0 {columns[1]['fieldname']},
    0 {columns[2]['fieldname']},
    1 header,
    A.root_type account_type
from 
    `tabGL Entry` GLE
join
    tabAccount A on GLE.account = A.name
where
    (A.root_type = 'Income' or A.root_type = 'Expense') and {date_range[0]}
group by
    A.parent_account
order by
    A.parent_account""", as_dict=1))

        for header in headers:
            data.append(header)
            data.extend(frappe.db.sql(f"""\
select
    A.name account,
    0 {columns[1]['fieldname']},
    0 {columns[2]['fieldname']},
    A.parent_account parent,
    A.root_type account_type,
    1 indent
from 
    `tabGL Entry` GLE
join
    tabAccount A on GLE.account = A.name
where
    A.root_type = '{header['account_type']}' and {date_range[0]}
group by
    A.name""", as_dict=1))
            data.append(blank_row)
    else:
        headers.extend(frappe.db.sql(f"""\
select
    A.parent_account account,
    0 {columns[1]['fieldname']},
    0 {columns[2]['fieldname']},
    0 {columns[3]['fieldname']},
    0 {columns[4]['fieldname']},
    1 header,
    A.root_type account_type
from 
    `tabGL Entry` GLE
join
    tabAccount A on GLE.account = A.name
where
    (A.root_type = 'Income' or A.root_type = 'Expense') and ({date_range[0]} or {date_range[1]})
group by
    A.parent_account
order by
    A.parent_account""", as_dict=1))

        for header in headers:
            data.append(header)
            data.extend(frappe.db.sql(f"""\
select
    A.name account,
    0 {columns[1]['fieldname']},
    0 {columns[2]['fieldname']},
    0 {columns[3]['fieldname']},
    0 {columns[4]['fieldname']},
    A.parent_account parent,
    A.root_type account_type,
    1 indent
from 
    `tabGL Entry` GLE
join
    tabAccount A on GLE.account = A.name
where
    A.root_type = '{header['account_type']}' and ({date_range[0]} or {date_range[1]})
group by
    A.name""", as_dict=1))
            data.append(blank_row)

    total_row = {'account': 'Net Profit', 'total': 1}
    for i in range(1, len(columns)):
        total_row[columns[i]['fieldname']] = 0

    data.append(total_row)

    for i, row in enumerate(data):
        if 'header' not in row:
            data[i]['header'] = 0
        if 'parent' not in row:
            data[i]['parent'] = ''
        if 'account_type' not in row:
            data[i]['account_type'] = ''
        if 'total' not in row:
            data[i]['total'] = 0

    return headers, data


def get_account_data(columns: list, date_range: str, doctype: str) -> list:
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
    {date_range} and (A.root_type = 'Income' or A.root_type = 'Expense')
group by
    GLE.account
having
    {columns[0]['fieldname']} <> 0""", as_dict=1))

    return data
