from __future__ import unicode_literals
import json

import frappe


@frappe.whitelist()
def update_service_order(invoice_name: str):
    "Updates information on service order to indicate invoice."

    invoice = frappe.get_doc("Sales Invoice", invoice_name)
    service_order = frappe.get_doc("Service Order", invoice.service_order)
    if not invoice.is_return and invoice.docstatus == 1:
        service_order.db_set("billing_status", "Invoiced")
        service_order.add_comment(
            comment_type="Info",
            text="invoiced this service order."
        )
    else:
        service_order.db_set("billing_status", "Pending Invoicing")
    service_order.notify_update()


@frappe.whitelist()
def validate_advance_payment_rate(exchange_rate, advances) -> "str | None":
    "Validate rate on advances."

    # advances table is passed from the front end as a JSON and exchange_rate is passed as a string
    advances = json.loads(advances)
    exchange_rate = float(exchange_rate)

    # append error messages to a list if an exchange rate is found to not match the given rate
    error_list = []
    for advance in advances:
        if advance['allocated_amount'] != 0 and advance['ref_exchange_rate'] != exchange_rate:
            error_list.append(
                f"{advance['reference_name']} in row {advance['idx']}"
                f" has an exchange rate of {round(1 / advance['ref_exchange_rate'], 4)}"
                f" whilst the you are trying to invoice at a rate of {round(1 / exchange_rate, 4)}."
            )

    # return error message by joining list if any errors are found, otherwise return nothing
    if len(error_list) > 0:
        error_list.insert(0, "The below advances are invalid due to mismatched exchange rates:<br>")
        error_message = "<br>".join(error_list)
        return error_message

    return None
