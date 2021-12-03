# Copyright (c) 2021, Eskill Trading and contributors
# For license information, please see license.txt

import frappe
from erpnext.accounts.party import get_party_account_currency
from erpnext.setup.utils import get_exchange_rate
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


class ServiceOrder(Document):
    def before_save(self):
        # Ensure that data set by the system is not overwritten when the form is saved
        if not self.get("__islocal"):
            old_order = frappe.get_doc("Service Order", self.name)
            if self.time_taken != old_order.time_taken:
                self.time_taken = old_order.time_taken
                self.total_hours = old_order.total_hours
                self.billable_hours = old_order.billable_hours

            if self.items != old_order.items:
                for index in range(len(self.items)):
                    for part in old_order.items:
                        if self.items[index].name == part.name:
                            self.items[index] = part
                            break


    def validate(self):
        # Remove entries with duplicate serial numbers or invalid serial numbers
        known_serials = set()
        accepted_devices = list()
        serial_devices = dict()
        for device in sorted(self.devices, key=lambda device: (device.name if "New" not in device.name else ""), reverse=True):
            if device.serial_number:
                if not frappe.db.exists("Serial No", device.serial_number):
                    continue

                serial_number = frappe.get_doc("Serial No", device.serial_number)
                if device.serial_number not in known_serials and device.model == serial_number.item_code:
                    known_serials.add(device.serial_number)
                    serial_devices[device.serial_number] = device.name
                else:
                    continue
            accepted_devices.append(device)
        
        self.devices = accepted_devices

        # Delete readings linked to deleted devices
        if len(self.devices) and len(self.device_reading):
            self.device_reading = [reading for i, reading in enumerate(self.device_reading) if reading.serial_number in known_serials]
            for i, reading in enumerate(self.device_reading):
                self.device_reading[i].service_device = serial_devices[reading.serial_number]
        elif len(self.device_reading):
            self.device_reading.clear()

        # Sort the readings table based on serial number, reading type, and date & time
        for i, item in enumerate(sorted(self.device_reading, key=lambda item: (item.serial_number, item.reading_type, item.reading_time)), 1):
            item.idx = i

        # Sort the devices table based on model, then serial number. Places entries without a serial number at the top
        for i, item in enumerate(sorted(self.devices, key=lambda item: (item.model if item.serial_number else "", item.serial_number if item.serial_number else item.model)), 1):
            item.idx = i


    def before_submit(self):
        # Throw an exception if there are serial numbers missing
        devices = dict()
        for device in self.devices:
            if not device.serial_number:
                item = frappe.get_doc("Item", device.model)
                if item.has_serial_no:
                    devices[device.idx] = device.model

        if len(devices) > 0:
            if len(devices) == 1:
                for key in devices:
                    message = f"Serial number is missing for model {devices[key]} in row {key}."
            else:
                message = "Serial numbers are missing:<br>"
                for key in sorted(devices):
                    message += f"<li>In row {key}, for model {devices[key]}</li>"

            frappe.throw(_(message))        


    @frappe.whitelist()
    def get_sla_devices(self):
        "Returns list of SLA devices based on selected SLA."
        sla = frappe.get_doc("Device SLA", self.sla)

        device_list = [{'name': device.name, 'model': device.model, 'model_name': device.model_name, 'serial_number': device.serial_number} for device in sla.devices]

        for i, device in enumerate(device_list):
            device_list[i]['row_number'] = i
        
        return device_list


    @frappe.whitelist()
    def parts_receipt(self):
        "Generate list of pending parts."

        pending_receipts = []
        response = {
            'receipts': [],
            'receive': False
        }

        response_table = [["Part", "Part Name", "Requested", "Released", "Already Received"]]
        for part in self.items:
            if part.released_qty > part.received_qty:
                pending_receipts.append([part.part, part.part_name, part.qty, part.released_qty, part.received_qty, part.name])
                response_table.append([part.part, part.part_name, part.qty, part.released_qty, part.received_qty])

        if len(pending_receipts):
            response['receipts'] = pending_receipts
            response['receive'] = True
        else:
            frappe.msgprint(
                title="Parts Pending Receipt",
                msg="No parts were received."
            )

        return response


    @frappe.whitelist()
    def parts_request(self):
        "Generate material transfer request for service order."

        parts_required = False

        for part in self.items:
            if part.status == "Not Requested":
                parts_required = True
                break

        if not parts_required:
            return "There were no parts pending request."

        request = frappe.new_doc("Material Request")
        request.material_request_type = "Material Transfer"
        request.service_order = self.name

        requested_parts = []
        for part in self.items:
            if part.status != "Not Requested":
                continue
            request_item = request.append("items", {})
            request_item.item_code = part.part
            request_item.qty = part.qty
            request_item.uom = part.uom
            request_item.warehouse = part.warehouse
            request_item.service_order = self.name
            request_item.part_list = part.name

            requested_parts.append(part.name)

        request.insert(ignore_permissions=True)
        request.submit()
        
        for part in requested_parts:
            line = frappe.get_doc("Part List", part)
            line.request = request.name
            line.status = "Requested"
            line.save(ignore_permissions=True)

        return "Parts were requested."


    @frappe.whitelist()
    def receive_part(self, part: str, received):
        "Update received quantity for the given part."

        part_list = frappe.get_doc("Part List", part)
        part_list.received_qty += received
        if part_list.received_qty == part_list.qty:
            part_list.status = "Received"
        elif (part_list.received_qty < part_list.qty) and (part_list.released_qty == part_list.qty):
            part_list.status = "Partially Received"
        part_list.save(ignore_permissions=True)

        self.add_comment(
            comment_type="Info",
            text=f"received {received} {part_list.part}: {part_list.part_name} into the {part_list.warehouse} location."
        )


    @frappe.whitelist()
    def return_parts_table(self):
        "Generate table for part return dialog."

        table = []
        for part in self.items:
            table.append({
                'part_list': part.name,
                'part': part.part,
                'warehouse': part.warehouse,
                'qty': part.qty,
                'received_qty': part.received_qty,
                'used_qty': part.used_qty
            })

        return table


    @frappe.whitelist()
    def return_parts(self, used_parts: dict):
        "Generate the Material Request to return unused parts to storage."

        parts_unused = False
        message = "used all requested parts."
        for item in self.items:
            if item.name in used_parts:
                item.used_qty = used_parts[item.name]
            if (item.released_qty - item.used_qty) > 0:
                parts_unused = True
            item.save(ignore_permissions=True)

        if parts_unused:
            message = "returned- "

            request = frappe.new_doc("Material Request")
            request.material_request_type = "Material Transfer"
            request.service_order = self.name

            for item in self.items:
                request_item = request.append("items", {})
                request_item.item_code = item.part
                request_item.from_warehouse = item.warehouse
                request_item.uom = item.uom
                request_item.qty = item.released_qty - item.used_qty
                message += f"{item.part_name}: {request_item.qty}; "

            request.insert(ignore_permissions=True)
            request.submit()

        self.db_set('parts_returned', 1)

        self.add_comment(
            comment_type="Info",
            text=message
        )

        return message


    @frappe.whitelist()
    def set_job_status(self, status: str):
        "Updates the status of the job and adds comment to describe who updated it."

        self.job_status = status
        if status == "Closed":
            self.closing_date = frappe.utils.today()
            self.parts_returned = 1
        self.save(ignore_permissions=True)

        self.add_comment(
            comment_type="Info",
            text=f"set job as \"{status}\"."
        )


    @frappe.whitelist()
    def set_job_type(self, job_type: str):
        "Updates the billability of the job and adds comment to describe who updated it."

        self.db_set("job_type", job_type)

        self.add_comment(
            comment_type="Info",
            text=f"set job as \"{job_type}\"."
        )


    @frappe.whitelist()
    def warranty_update(self, serial_number: str, owned_by: str, purchase_date, warranty_period: int = 0):
        "Updates ownership and warranty details for serial number."

        serial_no = frappe.get_doc("Serial No", serial_number)
        serial_no.owned_by = self.customer
        message = f"Item {serial_number} is now owned by {self.customer} in our records."
        if warranty_period > 0 and purchase_date:
            serial_no.warranty_expiry_date = frappe.utils.add_to_date(date=purchase_date, days=warranty_period)
            message = f"Item {serial_number} is now owned by {self.customer} in our records. The warranty period will expire on date {serial_no.warranty_expiry_date}."
            
        serial_no.save(ignore_permissions=True)

        serial_no.add_comment(
            comment_type="Info",
            text=f"set {owned_by} as owner; set warranty expiry date to {serial_no.warranty_expiry_date}."
        )
        self.add_comment(
            comment_type="Info",
            text=f"updated ownership and warranty of serial number {serial_number}."
        )

        return message


@frappe.whitelist()
def generate_delivery(source_name, target_doc = None):
    "Generates delivery note based on parts used and time taken."

    delivery = frappe.new_doc("Delivery Note")

    try:
        quotation = frappe.get_last_doc("Quotation", filters={'service_order': source_name, 'docstatus': 1})
    except:
        quotation = None

    def set_missing_values(source, target):
        if not quotation:
            company_currency = frappe.get_cached_value('Company',  target.company,  "default_currency")

            party_account_currency = get_party_account_currency("Customer", target.customer, target.company)

            target.currency = party_account_currency or company_currency

            if company_currency == target.currency:
                exchange_rate = 1
            else:
                exchange_rate = get_exchange_rate(target.currency, company_currency, target.posting_date, args="for_selling")

            target.usd_to_currency = 1 / exchange_rate
            target.conversion_rate = exchange_rate

        target.ignore_pricing_rule = 1

        for time in service_order.time_taken:
            sales_person = target.append("sales_team", {})
            sales_person.sales_person = time.technician
            if service_order.job_type == "Billable":
                sales_person.allocated_percentage = (time.billable_hours / service_order.billable_hours) * 100
            else:
                sales_person.allocated_percentage = (time.total_hours / service_order.total_hours) * 100

        if len(target.get("items")) == 0:
            frappe.msgprint(_("There are no deliverable items."))

        target.run_method("set_missing_values")
        target.run_method("calculate_taxes_and_totals")

    def update_item(source_doc, target_doc, source_parent):
        if quotation:
            if target_doc.part_list:
                part_list = frappe.get_doc("Part List", target_doc.part_list)
                target_doc.qty = part_list.used_qty
            else:
                target_doc.qty = source_doc.qty
        else:
            target_doc.qty = source_doc.used_qty

    service_order = frappe.get_doc("Service Order", source_name)

    if quotation:
        delivery = get_mapped_doc("Quotation", quotation.name, {
            "Quotation": {
                "doctype": "Delivery Note",
                "field_map": {
                    "party_name": "customer"
                },
                "validation": {
                    "docstatus": ["=", 1]
                }
            },
            "Quotation Item": {
                "doctype": "Delivery Note Item",
                "field_map": {
                },
                "postprocess": update_item,
            }
        }, target_doc, set_missing_values)
    else:
        delivery = get_mapped_doc("Service Order", source_name, {
            "Service Order": {
                "doctype": "Delivery Note",
                "field_map": {
                },
                "validation": {
                    "docstatus": ["=", 1]
                }
            },
            "Part List": {
                "doctype": "Delivery Note Item",
                "field_map": {
                    "name": "part_list",
                    "parent": "service_order",
                    "part": "item_code",
                },
                "postprocess": update_item,
                "filter": lambda d: d.used_qty <= 0
            }
        }, target_doc, set_missing_values)

    return delivery


@frappe.whitelist()
def generate_quote(source_name, target_doc = None):
    "Generates quote based on parts used and time taken."

    def set_missing_values(source, target):
        company_currency = frappe.get_cached_value('Company',  target.company,  "default_currency")

        party_account_currency = get_party_account_currency("Customer", target.party_name, target.company)

        target.currency = party_account_currency or company_currency

        if company_currency == target.currency:
            exchange_rate = 1
        else:
            exchange_rate = get_exchange_rate(target.currency, company_currency, target.transaction_date, args="for_selling")

        target.usd_to_currency = 1 / exchange_rate
        target.conversion_rate = exchange_rate
        target.ignore_pricing_rule = 1

        if len(target.get("items")) == 0:
            frappe.msgprint(_("There are no remaining parts to quote."))

        target.run_method("set_missing_values")
        target.run_method("calculate_taxes_and_totals")

    def update_item(source_doc, target_doc, source_parent):
        target_doc.qty = source_doc.used_qty if source_parent.parts_returned else source_doc.qty

    def get_quote_qty(item_row):
        return item_row.used_qty if service_order.parts_returned else item_row.qty

    service_order = frappe.get_doc("Service Order", source_name)

    quotation = get_mapped_doc("Service Order", source_name, {
        "Service Order": {
            "doctype": "Quotation",
            "field_map": {
                "name": "service_order",
                "customer": "party_name"
            },
            "validation": {
                "docstatus": ["=", 1]
            }
        },
        "Part List": {
            "doctype": "Quotation Item",
            "field_map": {
                "name": "part_list",
                "parent": "service_order",
                "part": "item_code",
            },
            "postprocess": update_item,
            "filter": lambda d: get_quote_qty(d) <= 0
        }
    }, target_doc, set_missing_values)

    return quotation
