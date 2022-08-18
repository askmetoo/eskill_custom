# -*- coding: utf-8 -*-
# Copyright (c) 2020, Eskill Trading and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from erpnext.accounts.party import get_party_account_currency
from erpnext.setup.utils import get_exchange_rate
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


class WarrantySwapOut(Document):
    "Collection of methods for Warranty Swap Out DocType."

    def on_submit(self):
        "Method run after submitting the document."
        self.update_service_order()


    def after_cancel(self):
        "Method run after cancelling the document."
        self.update_service_order()


    def update_service_order(self):
        "Update the linked Service Order."
        service_device = frappe.get_doc("Service Device", self.service_device)
        if self.docstatus != 2:
            service_device.db_set("swap_out", self.name, notify=True)
        else:
            service_device.db_set("swap_out", None, notify=True)


@frappe.whitelist()
def generate_delivery(source_name, target_doc = None):
    "Generates delivery note based on parts used and time taken."

    delivery = frappe.new_doc("Delivery Note")

    def set_missing_values(source, target):
        service_order = frappe.get_doc("Service Order", source.service_order)

        target.customer = service_order.customer_main_account
        target.customer_name = service_order.customer_name
        target.goodwill = 1
        target.service_order_type = "Warranty"

        company_currency = frappe.get_cached_value(
            'Company',
            target.company,
            "default_currency"
        )

        party_account_currency = get_party_account_currency(
            "Customer",
            target.customer,
            target.company
        )

        target.currency = party_account_currency or company_currency

        if company_currency == target.currency:
            exchange_rate = 1
        else:
            exchange_rate = get_exchange_rate(
                target.currency,
                company_currency,
                target.posting_date,
                args="for_selling"
            )

        target.usd_to_currency = 1 / exchange_rate
        target.conversion_rate = exchange_rate

        target.ignore_pricing_rule = 1

        target.sales_team = []
        if len(service_order.time_taken) > 0:
            for time in service_order.time_taken:
                sales_person = target.append("sales_team", {})
                sales_person.sales_person = time.technician
                if service_order.job_type == "Billable":
                    sales_person.allocated_percentage = (
                        time.billable_hours / service_order.billable_hours
                    ) * 100
                else:
                    sales_person.allocated_percentage = (
                        time.total_hours / service_order.total_hours
                    ) * 100
        else:
            target.append("sales_team", {
                'sales_person': service_order.assigned_technician,
                'allocated_percentage': 100
            })

        model = frappe.get_doc("Item", source.model_out)
        serial_no = frappe.get_doc("Serial No", source.serial_no_out)

        target.append("items", {
            'item_code': source.model_out,
            'item_name': model.item_name,
            'serial_no': source.serial_no_out,
            'warehouse': serial_no.warehouse
        })

        target.run_method("set_missing_values")
        target.run_method("calculate_taxes_and_totals")

    delivery = get_mapped_doc("Warranty Swap Out", source_name, {
        'Warranty Swap Out': {
            'doctype': "Delivery Note",
            'field_map': {
            },
            'validation': {
                'docstatus': ["=", 1],
                'approved': ["=", 1]
            }
        },
    }, target_doc, set_missing_values)

    return delivery
