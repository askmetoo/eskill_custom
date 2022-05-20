# Copyright (c) 2022, Eskill Trading and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from erpnext.accounts.doctype.payment_entry.payment_entry import get_party_details
from erpnext import get_default_company

class PaymentReceipt(Document):
    "Methods for the Payment Receipt DocType."

    def validate(self):
        "Method run during the validation event."

        # remove all references with an allocated amount of less than or equal to zero
        self.references = [
            reference
            for reference in self.references
            if reference.allocated_amount > 0
        ]

        # remove duplicate lines
        referenced_invoices = set()
        references = []
        for reference in self.references:
            if reference.reference_name in referenced_invoices:
                continue
            references.append(reference)
            referenced_invoices.add(reference.reference_name)
        self.references = references

        self.total_allocated_amount = sum([invoice.allocated_amount for invoice in references], 0)
        self.unallocated_amount = self.paid_amount - self.total_allocated_amount
        if (self.paid_amount or self.total_allocated_amount or self.unallocated_amount) < 0:
            frappe.throw("You can not have a negative amount.")
        if (self.total_allocated_amount + self.unallocated_amount) != self.paid_amount:
            frappe.throw(
                "The sum of the total allocated amount and the unallocated amount "
                "should equal the paid amount."
            )


    @frappe.whitelist()
    def get_outstanding_invoices(self):
        "Populates refences table with all customer invoices that have an outsanding amount."

        self.references = None
        self.total_allocated_amount = 0
        self.unallocated_amount = self.paid_amount

        invoices = frappe.get_all(
            doctype="Sales Invoice",
            fields=[
                "name",
                "grand_total",
                "outstanding_amount",
                "conversion_rate"
            ],
            filters=[
                ["Sales Invoice", "customer", "=", self.party],
                ["Sales Invoice", "outstanding_amount", ">", 0],
                ["Sales Invoice", "docstatus", "=", 1]
            ]
        )

        for invoice in invoices:
            amount_used = (
                self.unallocated_amount
                if invoice['outstanding_amount'] > self.unallocated_amount
                else invoice['outstanding_amount']
            )
            self.unallocated_amount -= amount_used
            self.total_allocated_amount += amount_used
            self.append("references", {
                'reference_doctype': "Sales Invoice",
                'reference_name': invoice['name'],
                'total_amount': invoice['grand_total'],
                'outstanding_amount': invoice['outstanding_amount'],
                'exchange_rate': invoice['conversion_rate'],
                'allocated_amount': amount_used
            })

            if self.unallocated_amount == 0:
                break

        self.notify_update()


@frappe.whitelist()
def generate_payment_entry(source_name, target_doc = None):
    "Generates quote based on parts used and time taken."

    def set_missing_values(source, target):
        target.payment_type = "Receive"
        target.party_type = "Customer"

        party_details = get_party_details(
            company=get_default_company(frappe.session.user),
            party_type=target.party_type,
            party=target.party,
            date=target.posting_date,
            cost_center=target.cost_center if target.cost_center else None
        )

        target.paid_from = party_details['party_account']
        target.paid_from_account_currency = party_details['party_account_currency']
        target.paid_from_account_balance = party_details['account_balance']
        target.received_amount = target.paid_amount

        target.reference_no = target.payment_receipt
        target.reference_date = target.posting_date

    payment_entry = get_mapped_doc("Payment Receipt", source_name, {
        "Payment Receipt": {
            "doctype": "Payment Entry",
            "field_map": {
                "name": "payment_receipt",
                "currency": "paid_to_account_currency",
                "paid_amount": "paid_amount",
            },
            "validation": {
                "docstatus": ["=", 1]
            }
        },
        "Payment Receipt Reference": {
            "doctype": "Payment Entry Reference",
        }
    }, target_doc, set_missing_values)

    return payment_entry
