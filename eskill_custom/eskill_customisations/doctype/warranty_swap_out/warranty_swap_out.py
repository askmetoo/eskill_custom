# -*- coding: utf-8 -*-
# Copyright (c) 2020, Eskill Trading and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe.model.document import Document


class WarrantySwapOut(Document):
    @frappe.whitelist()
    def update_service_order(self):
        service_device = frappe.get_doc("Service Device", self.service_device)
        if self.docstatus != 2:
            service_device.db_set("swap_out", self.name)
        else:
            service_device.db_set("swap_out", None)
