// Copyright (c) 2021, Eskill Trading and contributors
// For license information, please see license.txt

frappe.listview_settings['Service Order'] = {
    add_fields: ["billing_status", "job_status", "job_type"],
    get_indicator(doc) {
        var doc_status = null
        if (doc.job_status == "Open") {
            return [__(doc.job_status + ": " + doc.job_type), "green",]
        } else if (doc.job_type == "Billable") {
            doc_status = __(doc.job_status + ": " + doc.billing_status)
            if (doc.job_status == "On Hold") {
                return [doc_status, "orange"]
            }
            const status_color = {
                "Pending Billing": "red",
                "Delivered": "blue",
                "Invoiced": "dark grey",
            };
            return [doc_status, status_color[doc.billing_status]]
        } else {
            return [__(doc.job_status + ": " + doc.job_type), "dark grey"]
        }
    },
    hide_name_column: true,
    refresh(list) {
        set_breadcrumbs(list)
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
