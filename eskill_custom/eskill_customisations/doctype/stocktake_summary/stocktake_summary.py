# Copyright (c) 2021, Eskill Trading and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


class StocktakeSummary(Document):
    "Server-side script for the Stocktake Summary DocType."

    def on_cancel(self):
        "Method that runs after the cancel event."
        master = frappe.get_doc("Stocktake Master", self.master)
        master.db_set("report_generated", 0)


    @frappe.whitelist()
    def set_rows_to_reconcile(self, rows: "list[str]"):
        "Check the reconcile check box of selected rows."
        for row in rows:
            item = frappe.get_doc("Stocktake Summary Item", row)
            if not item.reconciled and not item.miscounted:
                item.db_set("reconcile", 1)


@frappe.whitelist()
def generate_reconciliation(source_name, target_doc = None):
    "Generates stock reconciliation based on variances in summary."

    def set_missing_values(source, target):
        target.purpose = "Stocktake Correction"
        target.set_posting_time = 1
        target.run_method("set_missing_values")
        target.expense_account = None

    def update_item(source_doc, target_doc, source_parent):
        target_doc.qty = source_doc.recount_qty
        item = frappe.get_doc("Stocktake Summary Item", source_doc.name)
        item.db_set("reconcile", 0)

    reconciliation = get_mapped_doc("Stocktake Summary", source_name, {
        'Stocktake Summary': {
            'doctype': "Stock Reconciliation",
            'field_map': {
                'name': "stocktake_summary",
                'report_date': "posting_date"
            },
            'validation': {
                'docstatus': ["=", 1]
            }
        },
        'Stocktake Summary Item': {
            'doctype': "Stock Reconciliation Item",
            'field_map': {
                'name': "stocktake_summary_item"
            },
            'postprocess': update_item,
            'filter': lambda d: d.reconcile != 1
        }
    }, target_doc, set_missing_values)

    return reconciliation


@frappe.whitelist()
def update_reconciliations(summary: str, reconciliation: str):
    "Update records to indicate that they have been reconciled."

    reconciliation = frappe.get_doc("Stock Reconciliation", reconciliation)

    for row in reconciliation.items:
        if row.stocktake_summary_item:
            item = frappe.get_doc("Stocktake Summary Item", row.stocktake_summary_item)
            item.db_set("reconciled", 1)
            if item.recount_qty != row.qty:
                item.db_set("miscounted", 1)
            item.notify_update()

    summary = frappe.get_doc("Stocktake Summary", summary)

    reconciled_count = len([item for item in summary.items if item.reconciled or item.miscounted])
    if reconciled_count == len(summary.items):
        summary.db_set("closed", 1, notify=True)
