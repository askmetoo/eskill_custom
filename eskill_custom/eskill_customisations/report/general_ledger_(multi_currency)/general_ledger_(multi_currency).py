# Copyright (c) 2021, Eskill Trading and contributors
# For license information, please see license.txt


from __future__ import unicode_literals

from datetime import datetime

import frappe
from frappe import _


def execute(filters=None):
    "Main function."

    if "from_date" in filters and filters['from_date'] > filters['to_date']:
        frappe.throw(_("Start date must not precede end date."))

    # Create columns
    columns = []
    columns.extend(get_columns(filters=filters))

    # Generate report data
    data = []
    data.extend(get_data(filters=filters, columns=columns))

    return columns, data


def get_columns(filters: 'dict[str, ]'):
    "Returns list of period based columns."

    columns = [
        {
            'fieldname': "account",
            'label': _("Account / Document"),
            'fieldtype': "Dynamic Link",
            'options': "document_type",
            'width': 300
        },
        {
            'fieldname': "document_type",
            'label': _("Voucher Type"),
            'fieldtype': "Link",
            'options': "DocType"
        },
        {
            'fieldname': "posting_date",
            'label': _("Posting Date"),
            'fieldtype': "Date"
        },
        {
            'fieldname': f"debit_{filters['base_currency'].lower()}",
            'label': _(f"Debit ({filters['base_currency']})"),
            'fieldtype': "Currency",
            'width': 120
        },
        {
            'fieldname': f"credit_{filters['base_currency'].lower()}",
            'label': _(f"Credit ({filters['base_currency']})"),
            'fieldtype': "Currency",
            'width': 120
        },
        {
            'fieldname': f"balance_{filters['base_currency'].lower()}",
            'label': _(f"Balance ({filters['base_currency']})"),
            'fieldtype': "Currency",
            'width': 120
        },
    ]

    if "currency" in filters:
        columns.extend([
            {
                'fieldname': f"debit_{filters['currency'].lower()}",
                'label': _(f"Debit ({filters['currency']})"),
                'fieldtype': "Currency",
                'options': "second_currency",
                'width': 120
            },
            {
                'fieldname': f"credit_{filters['currency'].lower()}",
                'label': _(f"Credit ({filters['currency']})"),
                'fieldtype': "Currency",
                'options': "second_currency",
                'width': 120
            },
            {
                'fieldname': f"balance_{filters['currency'].lower()}",
                'label': _(f"Balance ({filters['currency']})"),
                'fieldtype': "Currency",
                'options': "second_currency",
                'width': 120
            },
            {
                'fieldname': "second_currency",
                'fieldtype': "Link",
                'options': "Currency",
                'hidden': 1,
            }
        ])

    columns.extend([
        {
            'fieldname': "party",
            'label': _("Party"),
            'fieldtype': "Dynamic Link",
            'options': "party_type",
            'hidden': 1 if "accounts_only" in filters else 0,
            'width': 150
        },
        {
            'fieldname': "party_type",
            'label': _("Party Type"),
            'fieldtype': "Link",
            'options': "DocType",
            'hidden': 1
        },
        {
            'fieldname': "cost_center",
            'label': _("Cost Center"),
            'fieldtype': "Link",
            'options': "Cost Center",
            'hidden': 1 if "accounts_only" in filters or "cost_center" in filters else 0,
            'width': 150
        },
        {
            'fieldname': "remarks",
            'label': _("Remarks"),
            'fieldtype': "Text",
            'hidden': 1 if "accounts_only" in filters else 0,
            'width': 400
        }
    ])

    return columns


def get_data(filters: 'dict[str, ]', columns: 'list[dict[str, ]]') -> list:
    "Get report data."

    # Initialise data
    data = initialise_data(columns, filters)

    base_bal_col = f"balance_{filters['base_currency'].lower()}"
    base_cre_col = f"credit_{filters['base_currency'].lower()}"
    base_deb_col = f"debit_{filters['base_currency'].lower()}"

    new_data = []
    if "currency" in filters:
        bal_col = f"balance_{filters['currency'].lower()}"
        cre_col = f"credit_{filters['currency'].lower()}"
        deb_col = f"debit_{filters['currency'].lower()}"

        for account in data:
            account_entries = get_account_data(account, filters)
            if account['account_type'] == "Asset" or account['account_type'] == "Expense":
                for i, entry in enumerate(account_entries):
                    if i == 0:
                        account_entries[i][base_bal_col] = entry[base_deb_col] - entry[base_cre_col]
                        account_entries[i][bal_col] = entry[deb_col] - entry[cre_col]
                    else:
                        account_entries[i][base_bal_col] = (
                            account_entries[i - 1][base_bal_col] +
                            (entry[base_deb_col] - entry[base_cre_col])
                        )
                        account_entries[i][bal_col] = (
                            account_entries[i - 1][bal_col] +
                            (entry[deb_col] - entry[cre_col])
                        )
                    account[base_cre_col] += account_entries[i][base_cre_col]
                    account[base_deb_col] += account_entries[i][base_deb_col]
                    account[cre_col] += account_entries[i][cre_col]
                    account[deb_col] += account_entries[i][deb_col]
            else:
                for i, entry in enumerate(account_entries):
                    if i == 0:
                        account_entries[i][base_bal_col] = entry[base_cre_col] - entry[base_deb_col]
                        account_entries[i][bal_col] = entry[cre_col] - entry[deb_col]
                    else:
                        account_entries[i][base_bal_col] = (
                            account_entries[i - 1][base_bal_col] +
                            (entry[base_cre_col] - entry[base_deb_col])
                        )
                        account_entries[i][bal_col] = (
                            account_entries[i - 1][bal_col] +
                            (entry[cre_col] - entry[deb_col])
                        )
                    account[base_cre_col] += account_entries[i][base_cre_col]
                    account[base_deb_col] += account_entries[i][base_deb_col]
                    account[cre_col] += account_entries[i][cre_col]
                    account[deb_col] += account_entries[i][deb_col]
            new_data.append(account)
            new_data.extend(account_entries)
    else:
        for account in data:
            account_entries = get_account_data(account, filters)
            if account['account_type'] == "Asset" or account['account_type'] == "Expense":
                for i, entry in enumerate(account_entries):
                    if i == 0:
                        account_entries[i][base_bal_col] = entry[base_deb_col] - entry[base_cre_col]
                    else:
                        account_entries[i][base_bal_col] = (
                            account_entries[i - 1][base_bal_col] +
                            (entry[base_deb_col] - entry[base_cre_col])
                        )
                    account[base_cre_col] += account_entries[i][base_cre_col]
                    account[base_deb_col] += account_entries[i][base_deb_col]
            else:
                for i, entry in enumerate(account_entries):
                    if i == 0:
                        account_entries[i][base_bal_col] = entry[base_cre_col] - entry[base_deb_col]
                    else:
                        account_entries[i][base_bal_col] = (
                            account_entries[i - 1][base_bal_col] +
                            (entry[base_cre_col] - entry[base_deb_col])
                        )
                    account[base_cre_col] += account_entries[i][base_cre_col]
                    account[base_deb_col] += account_entries[i][base_deb_col]
            new_data.append(account)
            new_data.extend(account_entries)

    data = new_data

    def update_parents(account: 'dict[str,]') -> 'list[dict[str,]]':
        "Recursively updates account headers."

        if account['parent']:
            base_cre_col = f"credit_{filters['base_currency'].lower()}"
            base_deb_col = f"debit_{filters['base_currency'].lower()}"

            index = next(
                i
                for i, record in enumerate(data)
                if record['account'] == account['parent']
            )
            data[index][base_cre_col] += account[base_cre_col]
            data[index][base_deb_col] += account[base_deb_col]
            if "currency" in filters:
                cre_col = f"credit_{filters['currency'].lower()}"
                deb_col = f"debit_{filters['currency'].lower()}"
                data[index][cre_col] += account[cre_col]
                data[index][deb_col] += account[deb_col]

            update_parents(data[index])


    for i, account in enumerate(data):
        if not account['document_type'] and account['parent']:
            update_parents(account)

    if "currency" in filters:
        for i, account in enumerate(data):
            if "account_type" in account:
                if account['account_type'] == "Asset" or account['account_type'] == "Expense":
                    data[i][base_bal_col] = account[base_deb_col] - account[base_cre_col]
                    data[i][bal_col] = account[deb_col] - account[cre_col]
                else:
                    data[i][base_bal_col] = account[base_cre_col] - account[base_deb_col]
                    data[i][bal_col] = account[cre_col] - account[deb_col]
    else:
        for i, account in enumerate(data):
            if "account_type" in account:
                if account['account_type'] == "Asset" or account['account_type'] == "Expense":
                    data[i][base_bal_col] = account[base_deb_col] - account[base_cre_col]
                else:
                    data[i][base_bal_col] = account[base_cre_col] - account[base_deb_col]

    if "accounts_only" in filters:
        data = [record for record in data if "account_type" in record]
        columns[1]['hidden'] = 1
        columns[2]['hidden'] = 1
    if "currency" in filters:
        for i, record in enumerate(data):
            data[i]['second_currency'] = filters['currency']
    if "from_date" in filters:
        from_date = datetime.strptime(filters['from_date'], "%Y-%m-%d").date()
        data = [
            record
            for record in data
            if not record['posting_date'] or record['posting_date'] >= from_date
        ]
        for i, record in enumerate(data):
            data[i]['from_date'] = filters['from_date']
    for i, record in enumerate(data):
        data[i]['to_date'] = filters['to_date']

    return data


def initialise_data(columns: 'list[dict[str,]]', filters: 'dict[str,]') -> list:
    "Initialises data table."

    data = []

    data.extend(frappe.db.sql("""\
        select
            name account,
            0 indent,
            is_group,
            root_type account_type,
            parent_account parent
        from
            tabAccount
        where
            not disabled
        order by
            lft;""",
        as_dict=1
    ))

    if len(filters['accounts_to_report']) > 0:
        old_data = data
        def find_parents(account: 'dict[str,]'):
            "Returns a list of parents to insert into new_data."

            if not account['parent']:
                return [account]

            index = next(
                i
                for i, record in enumerate(old_data)
                if record['account'] == account['parent']
            )
            return [*find_parents(old_data[index]), account]

        data = []
        for i, account in enumerate(old_data):
            if account['account'] in filters['accounts_to_report']:
                if len(data) == 0:
                    data.extend(find_parents(account))
                else:
                    for record in find_parents(account):
                        if record not in data:
                            data.append(record)

    base_bal_col = f"balance_{filters['base_currency'].lower()}"
    base_cre_col = f"credit_{filters['base_currency'].lower()}"
    base_deb_col = f"debit_{filters['base_currency'].lower()}"

    if "currency" in filters:
        bal_col = f"balance_{filters['currency'].lower()}"
        cre_col = f"credit_{filters['currency'].lower()}"
        deb_col = f"debit_{filters['currency'].lower()}"

    for i, account in enumerate(data):
        data[i][base_bal_col] = 0
        data[i][base_cre_col] = 0
        data[i][base_deb_col] = 0
        if "currency" in filters:
            data[i][bal_col] = 0
            data[i][cre_col] = 0
            data[i][deb_col] = 0
        for column in columns:
            if column['fieldname'] not in account:
                data[i][column['fieldname']] = None

        if account['parent']:
            parent = next(
                i
                for i, record in enumerate(data)
                if record['account'] == account['parent']
            )
            data[i]['indent'] = data[parent]['indent'] + 1

    return data


def get_account_data(account: 'dict[str,]', filters: 'dict[str,]') -> list:
    "Get data based on GL Entries."

    base_cre_col = f"credit_{filters['base_currency'].lower()}"
    base_deb_col = f"debit_{filters['base_currency'].lower()}"

    data = []

    cost_center = (
        "and cost_center = '{}'".format(filters['cost_center'])
        if "cost_center" in filters else
        ""
    )

    if "currency" in filters:
        cre_col = f"credit_{filters['currency'].lower()}"
        deb_col = f"debit_{filters['currency'].lower()}"

        data.extend(frappe.db.sql(f"""\
            select
                GLE.voucher_no account,
                GLE.voucher_type document_type,
                GLE.posting_date,
                GLE.debit {base_deb_col},
                GLE.credit {base_cre_col},
                (case when A.account_currency = '{filters['currency']}' then GLE.debit_in_account_currency else 0 end) {deb_col},
                (case when A.account_currency = '{filters['currency']}' then GLE.credit_in_account_currency else 0 end) {cre_col},
                GLE.party,
                GLE.party_type,
                GLE.cost_center,
                GLE.remarks,
                A.account_currency
            from
                `tabGL Entry` GLE
            join
                tabAccount A on GLE.account = A.name
            where
                GLE.account = '{account['account']}'
                and GLE.posting_date <= '{filters['to_date']}'
                and not GLE.is_cancelled {cost_center}
            order by
                GLE.posting_date, GLE.creation, GLE.voucher_no;""", as_dict=1))

        if len(filters['selected_documents']) > 0:
            data = [
                record
                for record in data
                if record['document_type'] in filters['selected_documents']
            ]

        basic_docs = {
            "Delivery Note",
            "Purchase Invoice",
            "Purchase Receipt",
            "Sales Invoice"
        }

        for i, record in enumerate(data):
            if record['account_currency'] != filters['currency']:
                if record['document_type'] in basic_docs:
                    exchange_rate = frappe.db.sql(f"""\
                        select
                            (case when currency = '{filters['currency']}' then 1 / conversion_rate else auction_bid_rate end)
                        from
                            `tab{record['document_type']}`
                        where
                            name = '{record['account']}';""")[0][0]
                elif record['document_type'] == "Payment Entry":
                    exchange_rate = frappe.db.sql(f"""\
                        select
                            (case when
                                paid_from = '{account['account']}' and paid_from_account_currency = '{filters['currency']}'
                            then
                                1 / source_exchange_rate
                            else
                                (case when
                                    paid_to_account_currency = '{filters['currency']}'
                                then
                                    1 / target_exchange_rate
                                else
                                    auction_bid_rate
                                end)
                            end)
                        from
                            `tab{record['document_type']}`
                        where
                            name = '{record['account']}';""")[0][0]
                elif record['document_type'] == "Journal Entry":
                    exchange_rate = frappe.db.sql(f"""\
                        select
                            (case when
                                not JE.multi_currency
                            then
                                JE.auction_bid_rate
                            else
                                (case when
                                    JEA.account_currency = '{filters['currency']}'
                                then
                                    1 / avg(JEA.exchange_rate)
                                else
                                    JE.auction_bid_rate
                                end)
                            end)
                        from
                            `tab{record['document_type']}` JE
                        join
                            `tabJournal Entry Account` JEA on JE.name = JEA.parent
                        where
                            JE.name = '{record['account']}'
                            and JEA.account = '{account['account']}';""")[0][0]
                else:
                    exchange_rate = frappe.db.sql(f"""\
                        select
                            auction_bid_rate
                        from
                            `tab{record['document_type']}`
                        where
                            name = '{record['account']}';""")[0][0]
                data[i][deb_col] = data[i][base_deb_col] * exchange_rate
                data[i][cre_col] = data[i][base_cre_col] * exchange_rate
    else:
        data.extend(frappe.db.sql(f"""\
            select
                GLE.voucher_no account,
                GLE.voucher_type document_type,
                GLE.posting_date,
                GLE.debit {base_deb_col},
                GLE.credit {base_cre_col},
                GLE.party,
                GLE.party_type,
                GLE.cost_center,
                GLE.remarks,
                A.account_currency
            from
                `tabGL Entry` GLE
            join
                tabAccount A on GLE.account = A.name
            where
                GLE.account = '{account['account']}'
                and GLE.posting_date <= '{filters['to_date']}'
                and not GLE.is_cancelled {cost_center}
            order by
                GLE.posting_date, GLE.voucher_no;""", as_dict=1))

        if len(filters['selected_documents']) > 0:
            data = [
                record
                for record in data
                if record['document_type'] in filters['selected_documents']
            ]

    for i, record in enumerate(data):
        data[i]['parent'] = account['account']
        data[i]['indent'] = account['indent'] + 1

    return data
