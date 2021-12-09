# Copyright (c) 2021, Eskill Trading and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class StocktakeMaster(Document):
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
                t1.item_code,
                t1.warehouse,
                t1.posting_date,
                t1.qty_after_transaction current_qty
            from
                `tabStock Ledger Entry` t1
            join
                (select
                    time_table.item_code,
                    time_table.warehouse,
                    time_table.posting_date,
                    max(time_table.posting_time) posting_time
                from
                    `tabStock Ledger Entry` time_table
                join
                    (select
                        item_code,
                        warehouse,
                        max(posting_date) posting_date
                    from
                        `tabStock Ledger Entry`
                    group by
                        item_code, warehouse) date_table on
                    time_table.item_code = date_table.item_code
                    and time_table.warehouse = date_table.warehouse
                    and time_table.posting_date = date_table.posting_date
                group by
                    item_code, warehouse) t2 on
                t1.item_code = t2.item_code
                and t1.warehouse = t2.warehouse
                and t1.posting_date = t2.posting_date
                and t1.posting_time = t2.posting_time
            where
                t1.warehouse in {warehouses}
            group by
                t1.item_code, t1.warehouse
            having
                current_qty <> 0
            order by
                t1.warehouse, t1.item_code;""",
            as_dict=1
        )

        dividend, remainder = divmod(len(stock_list), len(self.user_list))

        stocktake_sheets = {
            self.user_list[i].user: stock_list[
                i * dividend + min(i, remainder):
                (i + 1) * dividend + min(i + 1, remainder)
            ]
            for i in range(len(self.user_list))
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
                    'current_qty': item['current_qty']
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
