# Copyright (c) 2022, Eskill Trading and contributors
# For license information, please see license.txt

import frappe
from erpnext import get_default_company
from erpnext.accounts.doctype.payment_entry.payment_entry import \
    get_party_details
from eskill_custom.payment_entry import update_payment_receipt
from frappe.model.document import Document


class PaymentReceiptReconciliation(Document):
    "Methods for Payment Receipt Reconciliation DocType."

    @frappe.whitelist()
    def create_entries(self):
        "Create Payment Entries based on the list of unprocessed Payment Receipts."

        entries_created = []

        for row in self.receipts:
            receipt = frappe.get_doc("Payment Receipt", row.receipt)
            entry = frappe.new_doc("Payment Entry")

            entry.naming_series = "REC.########"
            entry.payment_type = "Receive"
            entry.posting_date = receipt.posting_date
            entry.party_type = "Customer"
            entry.party = receipt.party

            party_details = get_party_details(
                company=get_default_company(frappe.session.user),
                party_type=entry.party_type,
                party=entry.party,
                date=entry.posting_date,
                cost_center=entry.cost_center if entry.cost_center else None
            )

            entry.paid_from = party_details['party_account']
            entry.paid_from_account_currency = party_details['party_account_currency']
            entry.paid_from_account_balance = party_details['account_balance']
            entry.paid_amount = receipt.paid_amount

            entry.paid_to = receipt.paid_to
            entry.paid_to_account_currency = receipt.currency
            entry.received_amount = receipt.paid_amount

            for reference in receipt.references:
                entry.append("references", reference.as_dict())

            entry.total_allocated_amount = receipt.total_allocated_amount
            entry.unallocated_amount = receipt.unallocated_amount

            entry.payment_receipt = receipt.name
            entry.reference_no = entry.payment_receipt
            entry.reference_date = entry.posting_date
            entry.remarks = receipt.remarks

            entry.insert()
            entry.submit()

            update_payment_receipt(entry.name)

            entries_created.append(entry.name)

        if len(entries_created) > 0:
            frappe.msgprint(
                f"The following Payment Entries were created:<br>{'<br>'.join(entries_created)}"
            )
        else:
            frappe.msgprint("No entries were created.")


    @frappe.whitelist()
    def get_unprocessed_receipts(self):
        "Get Payment Receipts that have not yet been processed."

        filters = [
            ["Payment Receipt", "docstatus", "=", 1],
            ["Payment Receipt", "posting_date", "<=", self.to_date],
            ["Payment Receipt", "status", "=", "Pending Processing"],
        ]

        if self.from_date:
            filters.append(["Payment Receipt", "posting_date", ">=", self.from_date])

        if self.to_date:
            filters.append(["Payment Receipt", "posting_date", "<=", self.to_date])

        if self.minimum_payment_amount:
            filters.append(["Payment Receipt", "paid_amount", ">=", self.minimum_payment_amount])

        if self.maximum_payment_amount:
            filters.append(["Payment Receipt", "paid_amount", "<=", self.maximum_payment_amount])

        receipts = frappe.get_all(
            doctype="Payment Receipt",
            filters=filters,
            fields=[
                "name",
                "posting_date",
                "party",
                "paid_amount",
                "total_allocated_amount",
                "unallocated_amount"
            ]
        )

        for receipt in receipts:
            self.append("receipts", {
                'receipt': receipt['name'],
                'posting_date': receipt['posting_date'],
                'party': receipt['party'],
                'paid_amount': receipt['paid_amount'],
                'total_allocated_amount': receipt['total_allocated_amount'],
                'unallocated_amount': receipt['unallocated_amount']
            })

        self.notify_update()
