// Copyright (c) 2021, Eskill Trading and contributors
// For license information, please see license.txt

frappe.listview_settings['Service Order'] = {
    add_fields: ["billing_status", "customer_name", "job_status", "job_type", "reason_on_hold"],
    colwidths: {
        name: 1
    },
    get_indicator(doc) {
        var doc_status = doc.job_status + ": ";
        var colour = "green";
        if (doc.job_status == "Open") {
            doc_status = __(doc_status + doc.job_type);
        } else if (doc.job_status == "On Hold") {
            doc_status = __(doc_status + doc.reason_on_hold);
            colour = "orange";
        } else {
            doc_status = __(doc_status + doc.billing_status)
            if (doc.job_type == "Billable") {
                colour = {
                    "Pending Billing": "red",
                    "Delivered": "blue",
                    "Invoiced": "dark grey",
                }[doc.billing_status];
            } else {
                colour = {
                    "Pending Billing": "red",
                    "Delivered": "dark grey",
                }[doc.billing_status];
            }
        }
        return [doc_status, colour];
    },
    hide_name_column: true,
    refresh(list) {
        set_breadcrumbs(list);
    }
};


function set_breadcrumbs(list) {
    frappe.breadcrumbs.clear();
    frappe.breadcrumbs.set_custom_breadcrumbs({
        route: "/app/support",
        label: "Support"
    });
    frappe.breadcrumbs.set_custom_breadcrumbs({
        route: "/app/service-order",
        label: "Service Order"
    });
}
