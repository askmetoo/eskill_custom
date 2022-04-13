"General methods that can be used in various DocTypes."
from __future__ import unicode_literals

import json

import frappe
from erpnext.stock.dashboard.item_dashboard import get_data as get_stock_levels


@frappe.whitelist()
def check_maintain_stock(doctype, item):
    "Return maintain stock status."
    try:
        maintain_stock = frappe.db.sql(f"""\
            select
                is_stock_item
            from
                tabItem
            where
                name = '{item}'
            limit 1;"""
        )
        return maintain_stock
    except:
        return False


@frappe.whitelist()
def sales_invoice_tax(doctype, currency, customer):
    "Return tax template for Sales Invoice."
    try:
        territory = frappe.db.sql(f"""\
            select
                territory
            from
                tabCustomer
            where
                name = '{customer}';"""
        )
        if territory[0][0] != 'Zimbabwe':
            return None
        template = frappe.db.sql(f"""\
            select
                name
            from
                `tabSales Taxes and Charges Template`
            where
                currency = '{currency}'
            limit 1;"""
        )
        return template
    except:
        return None


@frappe.whitelist()
def stock_lookup(item):
    "Returns stock locations and quantities."

    items = [
        {
            'warehouse': record['warehouse'],
            'reserved_qty': record['reserved_qty'],
            'actual_qty': record['actual_qty'],
            'valuation_rate': record['valuation_rate']
        }
        for record in get_stock_levels(item_code=item)
    ]

    return items


@frappe.whitelist()
def auction_rate_lookup(posting_date: str) -> float:
    "Returns the auction rate at the date of SI posting."

    try:
        auction_rate = frappe.db.sql(f"""\
            select
                exchange_rate
            from
                `tabAuction Exchange Rate`
            where
                date < date_add('{posting_date}', interval 1 day)
            order by
                date desc
            limit 1"""
        )
        auction_rate = auction_rate[0][0]
    except:
        auction_rate = 0
    return auction_rate


@frappe.whitelist()
def customer_account_selector(currency):
    "Returns the debtors' control account for the given currency."

    try:
        debtors_account = frappe.db.sql(f"select name from tabAccount where account_currency = '{currency}' and debtors_account is true limit 1;")
        debtors_account = debtors_account[0][0]
    except:
        debtors_account = ""

    return debtors_account


@frappe.whitelist()
def set_invoice_as_credited(credit):
    "Sets the status of the invoice linked to credit note to 'Credit Note Issued'."

    try:
        if credit:
            invoice = frappe.db.sql(f"""\
                select
                    parent Credit,
                    CNI.delivery_note,
                    DN.return_against,
                    SII.Invoice
                from
                    `tabSales Invoice Item` CNI
                join
                    (select
                        name,
                        return_against
                    from
                        `tabDelivery Note`) DN on DN.name = CNI.delivery_note
                join
                    (select
                        parent Invoice,
                        delivery_note
                    from
                        `tabSales Invoice Item`
                    group by
                        parent) SII on SII.delivery_note = DN.return_against
                group by
                    parent
                having
                    Credit = '{credit}'
                order by
                    parent desc
                limit 1;"""
            )
            frappe.db.set_value("Sales Invoice", invoice[0][0], "return_against", invoice[0][3])
            frappe.db.set_value("Sales Invoice", invoice[0][3], "status", "Credit Note Issued")
        else:
            return
    except Exception as error:
        return error


@frappe.whitelist()
def get_date(interval_type: str, interval: int) -> str:
    "Get date based on the provided interval and interval type."

    date = frappe.db.sql(f"select date_format(date_add(curdate(), interval {interval} {interval_type}), '%Y-%m-%d')")[0][0]

    return date


@frappe.whitelist()
def non_billable_item(item_code: str, sla_job: int) -> 'dict[str, str | int]':
    "Returns valuation rate and expense account for SLA and warranty delivery notes."

    results = {}

    valuation = frappe.db.sql(f"""\
        select
            valuation_rate
        from
            `tabStock Ledger Entry` SLE
        where
            item_code = '{item_code}'
        order by
            posting_date desc, posting_time desc
        limit 1;"""
    )

    if len(valuation):
        results['valuation'] = valuation[0][0]
    else:
        results['valuation'] = 0

    item_group = frappe.db.sql(f"""\
        select
            item_group
        from
            tabItem
        where
            name = '{item_code}';"""
    )[0][0]

    item_group = item_group.split(' ')[0]

    expense_account = frappe.db.sql(f"""\
        select
            A.name
        from
            tabAccount A
        where
            account_name like '{'Cost of Sales - SLA ' if int(sla_job) else 'Warranty%'}{item_group}'
            and root_type = 'Expense';"""
    )


    if len(expense_account):
        results['expense_account'] = expense_account[0][0]
    else:
        results['expense_account'] = ''

    return results


@frappe.whitelist()
def stock_availability(doctype: str, items):
    "Returns a message detailing stock locations and available quantities for the given items."

    items = json.loads(items)

    message = """The following items are in stock:<br><br>
        <table id="items" class="layout-table">
            <tbody>
                <tr class="layout-row">
                    <td class="layout-cell" style="width: 40%; text-align: center; border: 1px solid var(--table-border-color);">
                        <div>
                            Item
                        </div>
                    </td>
                    <td class="layout-cell" style="width: 40%; text-align: center; border: 1px solid var(--table-border-color);">
                        <div>
                            Warehouse
                        </div>
                    </td>
                    <td class="layout-cell" style="width: 20%; text-align: center; border: 1px solid var(--table-border-color);">
                        <div>
                            Available Quantity
                        </div>
                    </td>
                </tr>
    """

    if doctype == "Service Order":
        item_list = {row['part'] for row in items if "part" in row}
    else:
        item_list = {row['item_code'] for row in items if "item_code" in row}
    no_items = True
    for item in item_list:
        stock_levels = [
            {
                'warehouse': record['warehouse'],
                'actual_qty': record['actual_qty'],
            }
            for record in get_stock_levels(item_code=item)
            if record['actual_qty'] > 0
        ]
        if len(stock_levels) > 0:
            no_items = False
            for i, row in enumerate(stock_levels):
                message += f"""
                    <tr class="layout-row">
                        <td class="layout-cell" style="border: 1px solid var(--table-border-color); padding-left: 5mm;">
                            <div>
                                {item if i == 0 else ""}
                            <div>
                        </td>
                        <td class="layout-cell" style="border: 1px solid var(--table-border-color); padding-left: 5mm;">
                            <div>
                                {row['warehouse']}
                            <div>
                        </td>
                        <td class="layout-cell" style="text-align: center; border: 1px solid var(--table-border-color);">
                            <div>
                                {row['actual_qty']}
                            <div>
                        </td>
                    </tr>
                """
    message += "</tbody></table>"

    if no_items:
        message = "No items are in stock."
    frappe.msgprint(
        msg=message,
        title="Stock Availability",
        is_minimizable=True,
        wide=True
    )


@frappe.whitelist()
def validate_line_item_gp(doctype: str, exchange_rate, items) -> "str | None":
    "Validates line item GP based on item_group then returns an error message if any bad GPs are found."

    # items table is passed from the front end as a JSON and exchange_rate is passed as a string
    items = json.loads(items)
    exchange_rate = float(exchange_rate)

    # accounting for differing names for the valuation_rate field
    if doctype in ("Delivery Note", "Sales Invoice"):
        valuation_field = "incoming_rate"
    else:
        valuation_field = "valuation_rate"

    # identify the unique Item Groups in the document using a set
    # then create a dictionary with minimum and maximum GPs
    item_groups_set = {
        item['item_group']
        for item in items
    }
    item_groups = {}
    for group in item_groups_set:
        item_group = frappe.get_doc("Item Group", group)
        item_groups[group] = {
            'minimum_gp': item_group.minimum_gp,
            'maximum_gp': item_group.maximum_gp
        }

    # iterate over each item to validate GP based on item_group field
    # append error messages to a list if a GP % is found outside of the given range
    error_list = []
    for item in items:
        if item['override_gp_limit'] or not item[valuation_field]:
            continue
        try:
            gross_profit = round((
                (item['base_net_rate'] - item[valuation_field]) / item['base_net_rate']
            ) * 100, 2)
        except ZeroDivisionError:
            gross_profit = 0.00
        if gross_profit < item_groups[item['item_group']]['minimum_gp']:
            min_price = round(
                (item[valuation_field] / (
                    1 - item_groups[item['item_group']]['minimum_gp'] / 100
                )) * exchange_rate,
                2
            )
            error_list.append(
                f"{item['item_code']} in row {item['idx']} does not meet the minimum gross profit %. "
                f"The minimum price excluding tax is {min_price}."
            )
        elif gross_profit > item_groups[item['item_group']]['maximum_gp']:
            max_price = round(
                (item[valuation_field] / (
                    1 - item_groups[item['item_group']]['maximum_gp'] / 100
                )) * exchange_rate,
                2
            )
            error_list.append(
                f"{item['item_code']} in row {item['idx']} exceeds the maximum gross profit %. "
                f"The maximum price excluding tax is {max_price}."
            )

    # return error message by joining list if any errors are found, otherwise return nothing
    if len(error_list) > 0:
        error_message = "<br>".join(error_list)
        return error_message

    return None
