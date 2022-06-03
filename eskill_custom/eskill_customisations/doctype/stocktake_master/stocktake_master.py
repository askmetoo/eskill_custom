# Copyright (c) 2021, Eskill Trading and contributors
# For license information, please see license.txt

from random import random

import frappe
from frappe.model.document import Document


class StocktakeMaster(Document):
    "Server-side script for the Stocktake Master DocType."

    def validate(self):
        "Methods to be run during the saving process."

        if not self.user_list:
            self.get_user_list()
        if not self.warehouse_list:
            self.get_warehouse_list()


    def on_submit(self):
        "Methods to run after the document has been submitted."

        self.create_stocktake_sheets()


    def create_stocktake_sheets(self):
        "Uses the list of users and warehouses to create a stocktake sheet for each user."

        warehouses = "("
        for i, record in enumerate(self.warehouse_list):
            warehouses += f"'{record.warehouse}'"
            if i != len(self.warehouse_list) - 1:
                warehouses += ", "
        warehouses += ")"

        stock_list = frappe.db.sql(
            f"""select
                bal.item_code,
                W.warehouse_name warehouse,
                sum(bal.current_qty) qty
            from
                (select
                    SLE.item_code,
                    SLE.warehouse,
                    SLE.posting_date,
                    (select
                        t2.qty_after_transaction
                    from
                        `tabStock Ledger Entry` t2
                    where
                        t2.item_code = SLE.item_code and t2.warehouse = SLE.warehouse
                    order by
                        concat(t2.posting_date, t2.posting_time) desc, t2.creation desc
                    limit 1) current_qty
                from
                    `tabStock Ledger Entry` SLE
                where
                    SLE.warehouse in {warehouses}
                group by
                    SLE.item_code, SLE.warehouse
                having
                    current_qty <> 0) bal
            join
                tabWarehouse W on bal.warehouse = W.name
            group by
                bal.item_code, W.warehouse_name, W.warehouse_type
            order by
                W.warehouse_type, warehouse, item_code;""",
            as_dict=1
        )

        dividend, remainder = divmod(len(stock_list), len(self.user_list))

        stocktake_sheets = {
            user.user: stock_list[
                i * dividend + min(i, remainder):
                (i + 1) * dividend + min(i + 1, remainder)
            ]
            for i, user in enumerate(sorted(self.user_list, key=lambda _: random()))
        }

        for user in stocktake_sheets:
            sheet = frappe.new_doc("Stocktake Sheet")
            sheet.master = self.name
            sheet.report_date = self.report_date
            sheet.counter = user
            for item in stocktake_sheets[user]:
                sheet.append("items", {
                    'warehouse': item['warehouse'],
                    'item_code': item['item_code'],
                    'current_qty': item['qty']
                })
            sheet.insert(ignore_permissions=True)
            sheet.submit()


    @frappe.whitelist()
    def generate_summary(self) -> str:
        "Generate report of variances from stocktake."

        summary = frappe.new_doc("Stocktake Summary")
        summary.master = self.name

        variance_list = frappe.db.sql(
            f"""select
                SSI.warehouse warehouse,
                SSI.item_code item_code,
                SS.previous_counter_full_name first_counter,
                SS.full_name recounter,
                SSI.current_qty reported_qty,
                SSI.previous_qty first_count_qty,
                SSI.counted_qty recount_qty
            from
                `tabStocktake Sheet` SS
            join
                `tabStocktake Sheet Item` SSI on SS.name = SSI.parent
            where
                SS.count_type = 'Recount'
                and SS.master = '{self.name}'
                and SS.docstatus = 1
            having
                recount_qty <> reported_qty
            order by
                SSI.warehouse, SSI.item_code;""",
            as_dict=1
        )

        for variance in variance_list:
            item = summary.append("items", variance)
            item.remarks = (
                "Probable miscount. The counts do not match each other."
                if variance.first_count_qty != variance.recount_qty else
                "Variance found. The counts do match."
            )
        summary.total_variances = len(variance_list)
        if summary.total_variances == 0:
            summary.closed = 1

        summary.insert(ignore_permissions=True)
        summary.submit()

        self.db_set("report_generated", 1)

        return summary.name


    def get_user_list(self):
        "Updates the user_list table with all valid users."

        user_list = frappe.db.sql(
            """select distinct
                HR.parent user
            from
                `tabHas Role` HR
            join
                tabUser U on HR.parent = U.name
            where
                HR.parenttype = 'User'
                and HR.role = 'Stocktake User'
                and U.enabled;""",
            as_dict=1
        )

        for record in user_list:
            self.append("user_list", {
                'user': record['user']
            })


    def get_warehouse_list(self):
        "Updates the warehouse_list table with a list of Sales and Service warehouses with stock."

        warehouse_list = list(frappe.db.sql(
            f"""select
                SLE.warehouse warehouse,
                W.warehouse_type warehouse_type,
                sum(SLE.actual_qty) total_stock
            from
                `tabStock Ledger Entry` SLE
            join
                `tabWarehouse` W on SLE.warehouse = W.name
            where
                not W.disabled
                and W.warehouse_type in ('Sales', 'Service')
                and SLE.posting_date <= '{self.report_date}'
            group by
                SLE.warehouse
            having
                total_stock <> 0;""",
            as_dict=1
        ))

        for record in warehouse_list:
            self.append("warehouse_list", {
                'warehouse': record['warehouse'],
                'warehouse_type': record['warehouse_type']
            })
