# Copyright (c) 2021, Eskill Trading and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class DeviceSLA(Document):
    def __init__(self, *args, **kwargs) -> None:
        super(DeviceSLA, self).__init__(*args, **kwargs)


    def validate(self):
        # Remove entries with duplicate serial numbers or invalid serial numbers
        known_serials = set()
        accepted_devices = list()
        for device in sorted(self.devices, key=lambda device: (device.name if "New" not in device.name else ""), reverse=True):
            if device.serial_number:
                if not frappe.db.exists("Serial No", device.serial_number):
                    continue

                serial_number = frappe.get_doc("Serial No", device.serial_number)
                if device.serial_number not in known_serials and device.model == serial_number.item_code:
                    known_serials.add(device.serial_number)
                else:
                    continue
            accepted_devices.append(device)
        
        self.devices = accepted_devices


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
