"Server side customisations for the Purchase Receipt DocType."

import frappe
from frappe.model.mapper import get_mapped_doc


@frappe.whitelist()
def make_landed_cost_voucher(source_name, target_doc = None):
    "Map Purchase Receipt DocType onto the Landed Cost Voucher DocType."

    def set_missing_values(source, target):
        target.append("purchase_receipts", {
            'receipt_document_type': "Purchase Receipt",
            'receipt_document': source.name,
            'supplier': source.supplier,
            'posting_date': source.posting_date,
            'grand_total': source.base_grand_total
        })

    landed_cost_voucher = get_mapped_doc("Purchase Receipt", source_name, {
        "Purchase Receipt": {
            "doctype": "Landed Cost Voucher",
            "field_map": {},
            "validation": {
                "docstatus": ["=", 1]
            }
        }
    }, target_doc, set_missing_values)

    return landed_cost_voucher
