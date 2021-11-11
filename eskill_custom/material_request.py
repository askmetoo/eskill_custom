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
    for line in stock_entry.items:
        if line.part_list:
            transferred_qty = frappe.db.sql(f"""\
                select
                    ifnull(sum(transfer_qty), 0) total
                from
                    `tabStock Entry Detail`
                where
                    docstatus = 1
                    and part_list = '{line.part_list}';""")[0][0]
            part_list = frappe.get_doc("Part List", line.part_list)
            part_list.released_qty = transferred_qty
            if part_list.released_qty == part_list.qty:
                part_list.status = "Released"
            elif part_list.released_qty > 0:
                part_list.status = "Partially Released"
            else:
                part_list.status = "Requested"
            part_list.save(ignore_permissions=True)

            if transferred_qty:
                comment = f"has released {transferred_qty} {part_list.part}: {part_list.part_name}."
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

            if stock_entry.docstatus == 1:
                frappe.publish_realtime(
                    event="msgprint",
                    message=f"{line.transfer_qty} {part_list.part} are ready for collection.",
                    user=part_list.owner
                )

    return service_orders_affected
