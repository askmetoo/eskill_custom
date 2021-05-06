import frappe

@frappe.whitelist()
def get_issue_list(doc):
    return frappe.db.sql(
        "select I.name, subject, technician_name, customer, opening_date, service_level_agreement "
        "from tabIssue I "
        "left join `tabIssue Machines` IM on IM.parent = I.name "
        "where I.serial_number = '{0}' or IM.serial_number = '{0}' "
        "group by I.name, IM.serial_number;".format(doc.name),
        as_dict=1
    )
