from __future__ import unicode_literals

import frappe


@frappe.whitelist()
def cancel_part_request(document: str):
    "Used to clear request details in service order part list when material request is cancelled."
    
    material_request = frappe.get_doc("Material Request", document)

    for item in material_request.items:
        if item.part_list:
            part = frappe.get_doc("Part List", item.part_list)
            part.request = None
            part.status = "Not Requested"
            part.save()

@frappe.whitelist()
def update_part(doc: str):
    "Updates released quantities on Service Order part lists based on Stock Entry submission."
    
    stock_entry = frappe.get_doc("Stock Entry", doc)

    service_orders_affected = []
    if stock_entry.docstatus == 1:
        for line in stock_entry.items:
            if line.part_list:
                part_list = frappe.get_doc("Part List", line.part_list)
                transfer_qty = (
                    line.transfer_qty
                    if line.t_warehouse == part_list.warehouse
                    else 0 - line.transfer_qty
                )
                part_list.released_qty += transfer_qty
                if part_list.released_qty == part_list.qty:
                    part_list.status = "Released"
                elif part_list.released_qty > 0:
                    part_list.status = "Partially Released"
                else:
                    part_list.status = "Requested"
                part_list.save(ignore_permissions=True)
                service_order = frappe.get_doc("Service Order", part_list.parent)
                total_released_qty = 0
                if len(service_order.items) > 0:
                    for item in service_order.items:
                        total_released_qty += item.released_qty
                service_order.db_set("total_released_qty", total_released_qty, notify=True)

                if transfer_qty:
                    comment = f"has released {transfer_qty} {part_list.part}: {part_list.part_name}."
                else:
                    comment = f"has reversed all transfers of {part_list.part}: {part_list.part_name} for this order."
                service_order = frappe.get_doc("Service Order", part_list.parent)
                service_order.add_comment(
                    comment_type="Info",
                    text=comment,
                    link_doctype="Material Request",
                    link_name=part_list.request
                )

                if part_list.parent not in service_orders_affected:
                    service_orders_affected.append(part_list.parent)

                if transfer_qty > 0:
                    frappe.publish_realtime(
                        event="msgprint",
                        message=f"{line.transfer_qty} {part_list.part} are ready for collection.",
                        user=part_list.owner
                    )
    else:
        for line in stock_entry.items:
            if line.part_list:
                part_list = frappe.get_doc("Part List", line.part_list)
                transfer_qty = (
                    0 - line.transfer_qty
                    if line.t_warehouse == part_list.warehouse
                    else line.transfer_qty
                )
                part_list.released_qty += transfer_qty
                if part_list.released_qty == part_list.qty:
                    part_list.status = "Released"
                elif part_list.released_qty > 0:
                    part_list.status = "Partially Released"
                else:
                    part_list.status = "Requested"
                part_list.save(ignore_permissions=True)
                service_order = frappe.get_doc("Service Order", part_list.parent)
                total_released_qty = 0
                if len(service_order.items) > 0:
                    for item in service_order.items:
                        total_released_qty += item.released_qty
                service_order.db_set("total_released_qty", total_released_qty, notify=True)

                if part_list.parent not in service_orders_affected:
                    service_orders_affected.append(part_list.parent)


    return service_orders_affected
