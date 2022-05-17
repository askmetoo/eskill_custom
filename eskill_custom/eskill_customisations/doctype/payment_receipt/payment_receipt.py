# Copyright (c) 2022, Eskill Trading and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


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

        self.save()
        self.notify_update()
