# Copyright (c) 2021, Eskill Trading and contributors
# For license information, please see license.txt


from random import randint

import frappe
from frappe.model.document import Document


class StocktakeSheet(Document):
    "Server-side script for the Stocktake Sheet DocType."

    @frappe.whitelist()
    def check_count(self) -> "None | str":
        "Check the counts on the given sheet, if there is a variance create a new sheet."

        if self.count_type == "Initial":
            variances = [{
                'warehouse': item.warehouse,
                'item_code': item.item_code,
                'current_qty': item.current_qty,
                'previous_qty': item.counted_qty
            } for item in self.items if item.counted_qty != item.current_qty]

            self.db_set("count_complete", 1)
            if len(variances) == 0:
                self.db_set("status", "No Variances")
                return None

            self.db_set("status", "Recount Needed")

            self.notify_update()

            new_sheet = frappe.new_doc("Stocktake Sheet")
            new_sheet.master = self.master
            new_sheet.count_type = "Recount"
            new_sheet.last_count = self.name
            current_user_idx = frappe.db.get_value(
                "Stocktake User List",
                filters={
                    'parent': self.master,
                    'user': self.counter
                },
                fieldname="idx"
            )
            user_list = frappe.db.get_all(
                "Stocktake User List",
                filters={
                    'parent': self.master
                },
                fields=[
                    "idx",
                    "user"
                ],
                order_by="idx"
            )
            if len(user_list) == 1:
                new_sheet.counter = self.counter
            elif current_user_idx == len(user_list):
                new_sheet.counter = user_list[0].user
            else:
                new_sheet.counter = user_list[current_user_idx].user

            for item in variances:
                new_sheet.append("items", item)

            new_sheet.insert(ignore_permissions=True)
            new_sheet.submit()

            return new_sheet.name

        variance_count = len([
            item
            for item in self.items
            if item.counted_qty != item.current_qty
        ])
        # for item in self.items:
        #     if item.counted_qty != item.current_qty:
        #         variances.append({
        #             'warehouse': item.warehouse,
        #             'item_code': item.item_code,
        #             'reported_qty': item.current_qty,
        #             'first_count_qty': item.previous_qty,
        #             'recount_qty': item.counted_qty,
                    # 'remarks': (
                    #     "Probable miscount. The counts do not match each other."
                    #     if item.previous_qty != item.counted_qty else
                    #     "Variance found. The counts do match."
                    # )
        #         })

        self.db_set("count_complete", 1)
        self.db_set("status", "No Variances" if variance_count == 0 else "Variances Found")

        outstanding_sheets = frappe.db.count("Stocktake Sheet", filters={
            'count_complete': 0,
            'docstatus': 1
        })

        if outstanding_sheets == 0:
            master = frappe.get_doc("Stocktake Master", self.master)
            master.db_set("count_complete", 1)

        return None
