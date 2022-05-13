# -*- coding: utf-8 -*-
# Copyright (c) 2020, Eskill Trading and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe.model.document import Document


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
