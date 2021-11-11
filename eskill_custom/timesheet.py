from __future__ import unicode_literals

import frappe


@frappe.whitelist()
def service_order_time(timesheet: str, timesheet_detail: str = None, service_order: str = None):
    "Updates time in linked service order."
    
    if service_order:
        service_orders = ((service_order),)
    else:
        service_orders = frappe.db.sql(f"""\
            select
                activity_document
            from
                `tabTimesheet Detail`
            where
                parent = '{timesheet}'
                and activity_doctype = 'Service Order'
                and completed
            group by
                activity_document;""")

    if not service_orders:
        return 0

    updated_orders = []
    for order in service_orders:
        if isinstance(order, list) or isinstance(order, tuple):
            order = order[0]
        technician_time = frappe.db.sql(f"""\
            select
                round(sum(TD.billing_hours), 2) billable_time,
                SP.name technician,
                round(sum(TD.hours), 2) total_time
            from
                tabTimesheet T
            join
                `tabTimesheet Detail` TD on T.name = TD.parent
            join
                `tabSales Person` SP on T.employee = SP.employee
            where
                TD.completed
                and TD.activity_document = '{order}'
                {'and TD.name != "' + timesheet_detail + '"' if timesheet_detail else ''}
            group by
                technician;""", as_dict=1)
        
        frappe.db.sql(f"""\
            delete from
                `tabService Order Time`
            where
                parent = '{order}';""")

        for technician in technician_time:
            order_time = frappe.new_doc("Service Order Time")
            order_time.technician = technician['technician']
            order_time.total_hours = technician['total_time']
            order_time.billable_hours = technician['billable_time']
            order_time.parenttype = "Service Order"
            order_time.parent = order
            order_time.parentfield = "time_taken"
            order_time.insert(ignore_permissions=True, ignore_mandatory=True)
        
        updated_orders.append(order)

    for order in updated_orders:
        frappe.db.sql(f"""\
            update
                `tabService Order`
            set
                total_hours = (
                    select
                        ifnull(round(sum(hours), 2), 0)
                    from
                        `tabTimesheet Detail`
                    where
                        completed
                        and activity_document = '{order}'
                        {'and name != "' + timesheet_detail + '"' if timesheet_detail else ''}
                    ),
                billable_hours = (
                    select
                        ifnull(round(sum(billing_hours), 2), 0)
                    from
                        `tabTimesheet Detail`
                    where
                        completed
                        and activity_document = '{order}'
                        {'and name != "' + timesheet_detail + '"' if timesheet_detail else ''}
                )
            where
                name = '{order}';""")

    frappe.db.commit()

    if updated_orders:
        frappe.msgprint(updated_orders, "Updated Service Orders")

    return updated_orders
