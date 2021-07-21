# -*- coding: utf-8 -*-
# Copyright (c) 2021, Eskill Trading and contributors
# For license information, please see license.txt
from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.document import Document


class WarrantySignup(Document):
	pass


@frappe.whitelist()
def update_serial_warranty() -> int:
	"Update Serial No warranty expiry date, as well as owner."

	return 1
