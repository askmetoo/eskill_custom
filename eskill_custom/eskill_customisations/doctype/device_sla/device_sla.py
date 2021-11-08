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

        # Sort the devices table based on model, then serial number. Places entries without a serial number at the top
        for i, device in enumerate(sorted(self.devices, key=lambda device: (device.model if device.serial_number else "", device.serial_number if device.serial_number else device.model)), 1):
            device.idx = i

        # Set title based on customer and contract tier
        self.title = f"{self.customer} - {self.contract_tier}"


    def before_submit(self):
        # Check for device entries without serial numbers
        incomplete_devices = [device for device in self.devices if not device.serial_number]

        if len(incomplete_devices) == 1:
            frappe.throw(f"Row {incomplete_devices[0].idx} is missing a serial number in the devices table.")
        elif len(incomplete_devices) > 1:
            message = f"Rows {incomplete_devices[0].idx}"
            for i in range(1, len(incomplete_devices)):
                message += f", {incomplete_devices[i].idx}"
            frappe.throw(message + " are missing serial numbers in the devices table.")


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
