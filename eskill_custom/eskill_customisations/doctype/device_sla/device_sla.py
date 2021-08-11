# Copyright (c) 2021, Eskill Trading and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class DeviceSLA(Document):
    def __init__(self, *args, **kwargs) -> None:
        super(DeviceSLA, self).__init__(*args, **kwargs)
        
    @frappe.whitelist()
    def get_terms(self) -> str:
        "Gets the selected terms and conditions template and returns it with the values filled in."
        pass

def update_status():
    "Updates SLA status based on date."

    frappe.db.sql("""\
        update
            `tabDevice SLA`
        set
            status = 'Active'
        where
            start_date <= curdate() and end_date >= curdate() and status <> 'Breached' and docstatus = 1;""")

    frappe.db.sql("""\
        update
            `tabDevice SLA`
        set
            status = 'Expired'
        where
            end_date < curdate() and status <> 'Breached' and docstatus = 1;""")

    frappe.db.commit()

    return frappe.db.sql("select * from `tabDevice SLA`;", as_dict=1)
