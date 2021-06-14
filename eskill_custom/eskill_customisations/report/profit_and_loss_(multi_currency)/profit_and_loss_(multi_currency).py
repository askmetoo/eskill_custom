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
        if start_m == end_m:
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
            'width': 240
        },
    ]
    columns.extend(get_columns(filters=filters, single_period=single_period))

    data = []
    data.extend(get_data(filters=filters, columns=columns, start_m=start_m, end_m=end_m, single_period=single_period))

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
        columns.extend([{
            'fieldname': col.lower().replace(" ", "_").replace("(", "").replace(")", ""),
            'label': col,
            'fieldtype': "Currency",
            'width': 190
        }])

    if filters['accumulated']:
        for i in range(len(columns)):
            columns[i]['label'] = "Up to " + columns[i]['label']

    return columns


def get_data(start_m: int, end_m: int, filters: dict, columns: list, single_period: bool = False):
    "Get report data."

    data = []
    blank_row = {'account': ""}
    for i in range(1, len(columns)):
        blank_row[columns[i]['fieldname']] = None

    if filters['accumulated']:
        last_day_0 = frappe.db.sql(f"select last_day('{filters['start_y']}-{start_m}-1')")[0][0]
        last_day_1 = frappe.db.sql(f"select last_day('{filters['end_y']}-{end_m}-1')")[0][0]

    if single_period:
        if filters['periodicity'] == "Yearly":
            date_range = [f"year(GLE.posting_date) {'<' if filters['accumulated'] else ''}= {filters['start_y']}"]
        else:
            if filters['accumulated']:
                date_range = [f"GLE.posting_date <= '{last_day_0}'"]
            else:
                date_range = [f"(month(GLE.posting_date) = {start_m} and year(GLE.posting_date) = {filters['start_y']})"]
    else:
        if filters['periodicity'] == "Yearly":
            date_range = [
                f"year(GLE.posting_date) {'<' if filters['accumulated'] else ''}= {filters['start_y']}",
                f" year(GLE.posting_date) {'<' if filters['accumulated'] else ''}= {filters['end_y']}"
            ]
        else:
            if filters['accumulated']:
                date_range = [
                    f"GLE.posting_date <= '{last_day_0}'",
                    f"GLE.posting_date <= '{last_day_1}'"
                ]
            else:
                date_range = [
                    f"(month(GLE.posting_date) = {start_m} and year(GLE.posting_date) = {filters['start_y']})",
                    f"(month(GLE.posting_date) = {end_m} and year(GLE.posting_date) = {filters['end_y']})"
                ]

    period_rate = get_period_rate(single_period=single_period, filters=filters, start_m=start_m, end_m=end_m)

    income_headers = []
    income_headers.extend(get_headers(root_type="Income", date_range=date_range, columns=columns, rate=period_rate))

    for header in income_headers:
        data.extend([header])
        data.extend(get_sub_accounts(parent_account=header['account'], columns=columns, date_range=date_range, rate=period_rate))

    total_income = {'account': "Total Income"}
    for i in range(1, len(columns)):
        total_income[columns[i]['fieldname']] = 0
        for header in income_headers:
            total_income[columns[i]['fieldname']] += header[columns[i]['fieldname']]

    data.extend([total_income, blank_row])

    expense_headers = []
    expense_headers.extend(get_headers(root_type="Expense", date_range=date_range, columns=columns, rate=period_rate))

    for header in expense_headers:
        data.extend([header])
        data.extend(get_sub_accounts(parent_account=header['account'], columns=columns, date_range=date_range, rate=period_rate))

    total_expense = {'account': "Total Expense"}
    for i in range(1, len(columns)):
        total_expense[columns[i]['fieldname']] = 0
        for header in expense_headers:
            total_expense[columns[i]['fieldname']] += header[columns[i]['fieldname']]

    data.extend([total_expense, blank_row])

    net_profit = {'account': "Net Profit / Loss"}
    for i in range(1, len(columns)):
        net_profit[columns[i]['fieldname']] = 0
        net_profit[columns[i]['fieldname']] += total_income[columns[i]['fieldname']]
        net_profit[columns[i]['fieldname']] += total_expense[columns[i]['fieldname']]

    data.extend([blank_row, net_profit])

    return data


def get_period_rate(single_period: bool, filters: dict, start_m: int, end_m: int):
    "Get average rate for the period."

    rate = [0, 0]
    group_by = ""
    where = ""

    if filters['accumulated']:
        last_day_0 = frappe.db.sql(f"select last_day('{filters['start_y']}-{start_m}-1')")[0][0]
        last_day_1 = frappe.db.sql(f"select last_day('{filters['end_y']}-{end_m}-1')")[0][0]

    if filters['periodicity'] == "Monthly":
        group_by = "month(date)"
        if single_period:
            if filters['accumulated']:
                where = [f"date <= '{last_day_0}"]
            else:
                where = [f"month(date) = {start_m} and year(date) = {filters['start_y']}"]
        else:
            if filters['accumulated']:
                where = [f"date <= '{last_day_0}", f"date <= '{last_day_1}"]
            else:
                where = [
                    f"month(date) = {start_m} and year(date) = {filters['start_y']}",
                    f"month(date) = {end_m} and year(date) = {filters['end_y']}"
                ]
    else:
        group_by = "year(date)"
        if single_period:
            where = [f"year(date) {'<' if filters['accumulated'] else ''}= {filters['start_y']}"]
        else:
            where = [
                f"year(date) {'<' if filters['accumulated'] else ''}= {filters['start_y']}",
                f"year(date) {'<' if filters['accumulated'] else ''}= {filters['end_y']}"
            ]

    for i in range(len(where)):
        try:
            val = frappe.db.sql(f"""\
select
	avg(exchange_rate)
from
	`tabAuction Exchange Rate`
where
	{where[i]}
group by
    {group_by}""")
            rate[i] = val[0][0]
        except:
            pass

    return rate


def get_headers(root_type: str, date_range: list, columns: list, rate: list):
    "Return account parents."

    headers = []

    if len(date_range) == 1:
        headers.extend(frappe.db.sql(f"""\
select
    A.parent_account account, sum(credit - debit) {columns[1]['fieldname']}, sum((credit - debit) * ifnull(AER.exchange_rate, {rate[0]})) {columns[2]['fieldname']}, 1 parent_account
from
    `tabGL Entry` GLE
join
    tabAccount A on GLE.account = A.name
left outer join
    `tabAuction Exchange Rate` AER on (case when WEEKDAY(posting_date) >= 4 then WEEK(posting_date) = week(date) else week(posting_date) - 1 = week(date) end)
where
    A.root_type = '{root_type}' and {date_range[0]}
group by
    A.parent_account""", as_dict=1))
    else:
        headers.extend(frappe.db.sql(f"""\
select
    tab1.account account, {columns[1]['fieldname']}, {columns[2]['fieldname']}, {columns[3]['fieldname']}, {columns[4]['fieldname']}
from
    (select
        A.parent_account account, sum(credit - debit) {columns[1]['fieldname']}, sum((credit - debit) * ifnull(AER.exchange_rate, {rate[0]})) {columns[2]['fieldname']}
    from
        `tabGL Entry` GLE
    join
        tabAccount A on GLE.account = A.name
    left outer join
    	`tabAuction Exchange Rate` AER on (case when WEEKDAY(posting_date) >= 4 then WEEK(posting_date) = week(date) else week(posting_date) - 1 = week(date) end)
    where
        A.root_type = '{root_type}' and {date_range[0]}
    group by
        A.parent_account) tab1
join
    (select
        A.parent_account account, sum(credit - debit) {columns[3]['fieldname']}, sum((credit - debit) * ifnull(AER.exchange_rate, {rate[1]})) {columns[4]['fieldname']}
    from
        `tabGL Entry` GLE
    join
        tabAccount A on GLE.account = A.name
    left outer join
    	`tabAuction Exchange Rate` AER on (case when WEEKDAY(posting_date) >= 4 then WEEK(posting_date) = week(date) else week(posting_date) - 1 = week(date) end)
    where
        A.root_type = '{root_type}' and {date_range[1]}
    group by
        A.parent_account) tab2 on tab1.account = tab2.account""", as_dict=1))

    return headers


def get_sub_accounts(parent_account: str, columns: list, date_range: list, rate: list):
    "Get data for the sub accounts."

    data = []

    if len(date_range) == 1:
        data.extend(frappe.db.sql(f"""\
select
    A.name account, sum(credit - debit) {columns[1]['fieldname']}, sum((credit - debit) * ifnull(AER.exchange_rate, {rate[0]})) {columns[2]['fieldname']}, A.root_type account_type
from
    `tabGL Entry` GLE
join
    tabAccount A on GLE.account = A.name
left outer join
    `tabAuction Exchange Rate` AER on (case when WEEKDAY(posting_date) >= 4 then WEEK(posting_date) = week(date) else week(posting_date) - 1 = week(date) end)
where
    A.parent_account = '{parent_account}' and {date_range[0]}
group by
    A.name""", as_dict=1))
    else:
        data.extend(frappe.db.sql(f"""\
select
    tab1.account account, {columns[1]['fieldname']}, {columns[2]['fieldname']}, {columns[3]['fieldname']}, {columns[4]['fieldname']}
from
    (select
        A.name account, sum(credit - debit) {columns[1]['fieldname']}, sum((credit - debit) * ifnull(AER.exchange_rate, {rate[0]})) {columns[2]['fieldname']}
    from
        `tabGL Entry` GLE
    join
        tabAccount A on GLE.account = A.name
    left outer join
    	`tabAuction Exchange Rate` AER on (case when WEEKDAY(posting_date) >= 4 then WEEK(posting_date) = week(date) else week(posting_date) - 1 = week(date) end)
    where
        A.parent_account = '{parent_account}' and {date_range[0]}
    group by
        A.name) tab1
join
    (select
        A.name account, sum(credit - debit) {columns[3]['fieldname']}, sum((credit - debit) * ifnull(AER.exchange_rate, {rate[1]})) {columns[4]['fieldname']}
    from
        `tabGL Entry` GLE
    join
        tabAccount A on GLE.account = A.name
    left outer join
    	`tabAuction Exchange Rate` AER on (case when WEEKDAY(posting_date) >= 4 then WEEK(posting_date) = week(date) else week(posting_date) - 1 = week(date) end)
    where
        A.parent_account = '{parent_account}' and {date_range[1]}
    group by
        A.name) tab2 on tab1.account = tab2.account""", as_dict=1))


    return data
