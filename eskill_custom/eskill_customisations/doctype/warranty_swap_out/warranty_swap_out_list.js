// Copyright (c) 2021, Eskill Trading and contributors
// For license information, please see license.txt

frappe.listview_settings["Warranty Swap Out"] = {
    add_fields: ["billing_status", "customer_name", "job_status", "job_type", "reason_on_hold"],
    colwidths: {
        name: 1
    },
    get_indicator(doc) {
        let colour = {
            'Pending Processing': "red",
            Processed: "green"
        }[doc.status]
        return [doc.status, colour];
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
        route: "/app/warranty-swap-out",
        label: "Warranty Swap Out"
    });
}
