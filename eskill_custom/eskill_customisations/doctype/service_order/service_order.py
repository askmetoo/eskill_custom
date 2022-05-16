# Copyright (c) 2021, Eskill Trading and contributors
# For license information, please see license.txt

import frappe
from erpnext.accounts.party import get_party_account_currency
from erpnext.setup.utils import get_exchange_rate
from frappe import _
from frappe.exceptions import DoesNotExistError
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


class ServiceOrder(Document):
    "Service Order DocType."
    def before_save(self):
        "Method run before saving."
        # Ensure that data set by the system is not overwritten when the form is saved
        if not self.get("__islocal"):
            old_order = frappe.get_doc("Service Order", self.name)
            if self.time_taken != old_order.time_taken:
                self.time_taken = old_order.time_taken
                self.total_hours = old_order.total_hours
                self.billable_hours = old_order.billable_hours

            if self.items != old_order.items:
                for i, _ in enumerate(self.items):
                    for part in old_order.items:
                        if self.items[i].name == part.name:
                            self.items[i] = part
                            break


    def validate(self):
        "Method run during validation before saving."
        # Remove entries with duplicate serial numbers or invalid serial numbers
        known_serials = set()
        accepted_devices = list()
        serial_devices = dict()
        for device in sorted(
            self.devices,
            key=lambda device: (device.name if "New" not in device.name else ""),
            reverse=True
        ):
            if device.serial_number:
                if not frappe.db.exists("Serial No", device.serial_number):
                    continue

                serial_number = frappe.get_doc("Serial No", device.serial_number)
                if (
                    device.serial_number not in known_serials
                    and device.model == serial_number.item_code
                ):
                    known_serials.add(device.serial_number)
                    serial_devices[device.serial_number] = device.name
                else:
                    continue
            accepted_devices.append(device)

        self.devices = accepted_devices

        # Delete readings linked to deleted devices
        if len(self.devices) > 0 and len(self.device_reading) > 0:
            self.device_reading = [
                reading
                for i, reading in enumerate(self.device_reading)
                if reading.serial_number in known_serials
            ]
            for i, reading in enumerate(self.device_reading):
                self.device_reading[i].service_device = serial_devices[reading.serial_number]
        elif len(self.device_reading) > 0:
            self.device_reading.clear()

        # Sort the readings table based on serial number, reading type, and date & time
        for i, item in enumerate(
            sorted(
                self.device_reading,
                key=lambda item: (
                    item.serial_number,
                    item.reading_type,
                    item.reading_time
                )
            ),
            1
        ):
            item.idx = i

        # Sort the devices table based on model, then serial number
        for i, item in enumerate(
            sorted(
                self.devices,
                key=lambda item: (
                    item.model if item.serial_number else "",
                    item.serial_number if item.serial_number else item.model
                )
            ),
            1
        ):
            item.idx = i


    def before_submit(self):
        "Method run before submission."
        # Throw an exception if there are serial numbers missing
        devices = {}
        for device in self.devices:
            if not device.serial_number:
                item = frappe.get_doc("Item", device.model)
                if item.has_serial_no:
                    devices[device.idx] = device.model

        if len(devices) > 0:
            if len(devices) == 1:
                for key, val in devices.items():
                    message = f"Serial number is missing for model {val} in row {key}."
            else:
                message = "Serial numbers are missing:<br>"
                for key, val in sorted(devices.items()):
                    message += f"<li>In row {key}, for model {val}</li>"

            frappe.throw(_(message))


    def on_update_after_submit(self):
        "Run methods after document has been updated in db."
        total_requested_qty = 0
        for item in self.items:
            total_requested_qty += item.qty
        self.db_set("total_requested_qty", total_requested_qty, notify=True)


    @frappe.whitelist()
    def get_sla_devices(self):
        "Returns list of SLA devices based on selected SLA."
        sla = frappe.get_doc("Device SLA", self.sla)

        device_list = [
            {
                'name': device.name,
                'model': device.model,
                'model_name': device.model_name,
                'serial_number': device.serial_number
            }
            for device in sla.devices
        ]

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
                pending_receipts.append(
                    [
                        part.part,
                        part.part_name,
                        part.qty,
                        part.released_qty,
                        part.received_qty,
                        part.name
                    ]
                )
                response_table.append(
                    [
                        part.part,
                        part.part_name,
                        part.qty,
                        part.released_qty,
                        part.received_qty
                    ]
                )

        if len(pending_receipts) > 0:
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
        received_qty = part_list.received_qty + received
        if received_qty > part_list.released_qty:
            frappe.throw(_("You can not receive more parts than have been released."))
        if received_qty == part_list.qty:
            part_list.db_set("status", "Received")
        elif (received_qty < part_list.qty) and (part_list.released_qty == part_list.qty):
            part_list.db_set("status", "Partially Received")
        part_list.db_set("received_qty", received_qty, notify=True)

        self.reload()
        total_received_qty = 0
        for item in self.items:
            total_received_qty += item.received_qty
        self.db_set("total_received_qty", total_received_qty, notify=True)

        self.add_comment(
            comment_type="Info",
            text=(
                f"received {received} {part_list.part}: {part_list.part_name}"
                f" into the {part_list.warehouse} location."
            )
        )


    @frappe.whitelist()
    def return_parts_table(self):
        "Generate table for part return dialog."

        response = {
            'parts_returnable': True,
            'message': ""
        }
        returnable_qty = self.total_received_qty - (self.total_used_qty + self.total_returned_qty)
        if returnable_qty > 0:
            response["message"] = """\
                Are you sure that you want to return the following?<br>
                <br>
                <table id="items" class="layout-table">
                    <tbody>
                        <tr class="layout-row">
                            <td class="layout-cell" style="width: 20%; text-align: center;">
                                <div>
                                    Quantity
                                </div>
                            </td>
                            <td class="layout-cell">
                                <div>
                                    Line Item
                                </div>
                            </td>
                        </tr>"""
            for part in self.items:
                part_returnable_qty = part.received_qty - (part.used_qty + part.returned_qty)
                if part_returnable_qty > 0:
                    response['message'] += f"""
                        <tr class="layout-row">
                            <td class="layout-cell" style="text-align: center;">
                                <div>
                                    {part_returnable_qty}
                                </div>
                            </td>
                            <td class="layout-cell">
                                <div>
                                    <strong>{part.part}</strong>: {part.part_name}
                                </div>
                            </td>
                        </tr>"""
            response['message'] += "</tbody></table>"
        else:
            response["parts_returnable"] = False
            response["message"] = "There are no parts to return."

        return response


    @frappe.whitelist()
    def return_parts(self):
        "Generate the Material Request to return unused parts to storage."

        message = """
            Returned:<br><br>
            <table id="items" class="layout-table">
                <tbody>
                    <tr class="layout-row">
                        <td class="layout-cell" style="width: 20%; text-align: center;">
                            <div>
                                Quantity
                            </div>
                        </td>
                        <td class="layout-cell">
                            <div>
                                Line Item
                            </div>
                        </td>
                    </tr>"""

        request = frappe.new_doc("Material Request")
        request.material_request_type = "Material Transfer"
        request.service_order = self.name

        for item in self.items:
            if (item.received_qty - (item.used_qty + item.returned_qty)) > 0:
                request_item = request.append("items", {})
                request_item.item_code = item.part
                request_item.from_warehouse = item.warehouse
                request_item.uom = item.uom
                request_item.qty = item.received_qty - (item.used_qty + item.returned_qty)
                message += f"""
                    <tr class="layout-row">
                        <td class="layout-cell" style="text-align: center;">
                            <div>
                                {request_item.qty}
                            </div>
                        </td>
                        <td class="layout-cell">
                            <div>
                                <strong>{item.part}</strong>: {item.part_name}
                            </div>
                        </td>
                    </tr>"""
                frappe.db.set_value(
                    dt="Part List",
                    dn=item.name,
                    field="returned_qty",
                    val=request_item.qty,
                    debug=True
                )

        request.insert(ignore_permissions=True)
        request.submit()

        message += "</tbody></table>"
        self.add_comment(
            comment_type="Info",
            text=message
        )

        self.reload()
        total_returned_qty = 0
        for item in self.items:
            total_returned_qty += item.returned_qty
        self.db_set("total_returned_qty", total_returned_qty, notify=True)

        return message


    @frappe.whitelist()
    def set_job_status(self, status: str, reason: str = None):
        "Updates the status of the job and adds comment to describe who updated it."

        self.job_status = status
        self.reason_on_hold = reason
        if status == "Closed":
            self.closing_date = frappe.utils.today()
            if self.goodwill and (self.total_used_qty <= 0):
                self.billing_status = "Billing Not Required"
        self.save(ignore_permissions=True)
        self.notify_update()


    @frappe.whitelist()
    def set_job_type(self, job_type: str):
        "Updates the billability of the job and adds comment to describe who updated it."

        self.job_type = job_type

        if job_type == "Warranty":
            self.goodwill = 1
        else:
            self.goodwill = 0

        self.save(ignore_permissions=True)

        self.add_comment(
            comment_type="Info",
            text=f"set job as \"{job_type}\"."
        )


    @frappe.whitelist()
    def update_customer_billing_currency(self, currency: str):
        "Updates the customer field to reflect the change in currency."

        new_customer = "-".join((*self.customer_main_account.split("-")[0:2], currency[0:2]))
        if new_customer != self.customer:
            if new_customer == self.customer_main_account:
                self.db_set("customer", new_customer)
                self.update_modified()
            else:
                customer_list = frappe.get_list(
                    "Customer",
                    filters={
                        'main_account': self.customer_main_account
                    },
                    pluck="name"
                )

                if new_customer in customer_list:
                    self.db_set("customer", new_customer)
                    self.update_modified()
                else:
                    frappe.throw(_("Customer account does not exist."))


    @frappe.whitelist()
    def use_part(self, part: str, used):
        "Update used quantity for the given part."

        part_list = frappe.get_doc("Part List", part)
        used_qty = part_list.used_qty + used
        if used_qty > part_list.received_qty:
            frappe.throw(_("You can not use more parts than have been released."))
        if used_qty == part_list.received_qty:
            part_list.db_set("status", "Used")
        elif (
            (used_qty < part_list.received_qty)
            and (part_list.received_qty == part_list.released_qty)
        ):
            part_list.db_set("status", "Partially Used")
        part_list.db_set("used_qty", used_qty, notify=True)

        self.reload()
        total_used_qty = 0
        for item in self.items:
            total_used_qty += item.used_qty
        self.db_set("total_used_qty", total_used_qty, notify=True)

        self.add_comment(
            comment_type="Info",
            text=f"used {used} {part_list.part}: {part_list.part_name}"
        )


    @frappe.whitelist()
    def warranty_update(
        self,
        serial_number: str,
        owned_by: str,
        purchase_date,
        warranty_period: int = 0
    ):
        "Updates ownership and warranty details for serial number."

        serial_no = frappe.get_doc("Serial No", serial_number)
        serial_no.owned_by = self.customer_main_account
        message = f"Item {serial_number} is now owned by {self.customer_main_account} in our records."
        if warranty_period > 0 and purchase_date:
            serial_no.warranty_expiry_date = frappe.utils.add_to_date(
                date=purchase_date,
                days=warranty_period
            )
            message = (
                f"Item {serial_number} is now owned by {self.customer_main_account} in our records."
                f" The warranty period will expire on date {serial_no.warranty_expiry_date}."
            )

        serial_no.save(ignore_permissions=True)

        serial_no.add_comment(
            comment_type="Info",
            text=(
                f"set {owned_by} as owner;"
                f" set warranty expiry date to {serial_no.warranty_expiry_date}."
            )
        )
        serial_no.reload()
        index = next(i for i, row in enumerate(self.devices) if row.serial_number == serial_number)
        self.devices[index].warranty_status = serial_no.maintenance_status
        self.save(ignore_permissions=True)
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
        quotation = frappe.get_last_doc(
            "Quotation",
            filters={
                'service_order': source_name,
                'docstatus': 1
            }
        )
    except DoesNotExistError:
        quotation = None

    def set_missing_values(source, target):
        if not quotation:
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
        else:
            service_order = frappe.get_doc("Service Order", source.service_order)
            encountered_items = set()
            for part in service_order.items:
                if (part.used_qty - part.delivered_qty) <= 0:
                    continue
                index = None
                if part.part not in encountered_items:
                    encountered_items.add(part.part)
                    try:
                        index = next(
                            i
                            for i, row in enumerate(target.items)
                            if row.item_code == part.part
                        )
                    except StopIteration:
                        pass
                if index is not None:
                    target.items[index].qty = part.used_qty - part.delivered_qty
                    target.items[index].warehouse = part.warehouse
                    target.items[index].part_list = part.name
                else:
                    target.append("items", {
                        'item_code': part.part,
                        'warehouse': part.warehouse,
                        'qty': part.used_qty - part.delivered_qty,
                        'service_order': part.parent,
                        'part_list': part.name,
                        'uom': part.uom
                    })

        target.ignore_pricing_rule = 1

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

        if len(target.get("items")) == 0:
            frappe.msgprint(_("There are no deliverable items."))

        target.run_method("set_missing_values")
        target.run_method("calculate_taxes_and_totals")

    def update_item(source_doc, target_doc, source_parent):
        if quotation:
            if target_doc.part_list:
                part_list = frappe.get_doc("Part List", target_doc.part_list)
                target_doc.qty = (part_list.used_qty - part_list.delivered_qty)
            else:
                target_doc.qty = source_doc.qty
        else:
            target_doc.qty = (source_doc.used_qty - source_doc.delivered_qty)

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
                    "service_order": "service_order",
                    "part_list": "part_list"
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
                "filter": lambda d: (d.used_qty - d.delivered_qty) <= 0
            }
        }, target_doc, set_missing_values)

    return delivery


@frappe.whitelist()
def generate_quote(source_name, target_doc = None):
    "Generates quote based on parts used and time taken."

    def set_missing_values(source, target):
        company_currency = frappe.get_cached_value('Company',  target.company,  "default_currency")

        party_account_currency = get_party_account_currency(
            "Customer",
            target.party_name,
            target.company
        )

        target.currency = party_account_currency or company_currency

        if company_currency == target.currency:
            exchange_rate = 1
        else:
            exchange_rate = get_exchange_rate(
                target.currency,
                company_currency,
                target.transaction_date,
                args="for_selling"
            )

        target.usd_to_currency = 1 / exchange_rate
        target.conversion_rate = exchange_rate
        target.ignore_pricing_rule = 1

        if len(target.get("items")) == 0:
            frappe.msgprint(_("There are no remaining parts to quote."))

        target.run_method("set_missing_values")
        target.run_method("calculate_taxes_and_totals")

    def update_item(source_doc, target_doc, source_parent):
        target_doc.qty = source_doc.used_qty if source_doc.used_qty else source_doc.qty

    def get_quote_qty(item_row):
        return item_row.used_qty if item_row.used_qty else item_row.qty

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
