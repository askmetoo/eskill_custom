// Copyright (c) 2022, Eskill Trading and contributors
// For license information, please see license.txt

frappe.ui.form.on('Service Order Settings', {
    refresh(frm) {
        account_filters(frm);
        set_breadcrumbs(frm);
    }
});


function account_filters(frm) {
    frm.fields_dict.internal_cos_account.get_query = function() {
        return {
            filters: [
                ["Account", "account_type", "=", "Expense Account"],
                ["Account", "is_group", "=", 0],
                ["Account", "disabled", "=", 0],
            ]
        };
    };
    frm.fields_dict.sla_cos_account.get_query = function() {
        return {
            filters: [
                ["Account", "account_type", "=", "Cost of Goods Sold"],
                ["Account", "is_group", "=", 0],
                ["Account", "disabled", "=", 0],
            ]
        };
    };
    frm.fields_dict.warranty_cos_account.get_query = function() {
        return {
            filters: [
                ["Account", "account_type", "=", "Cost of Goods Sold"],
                ["Account", "is_group", "=", 0],
                ["Account", "disabled", "=", 0],
            ]
        };
    };
}


function set_breadcrumbs(frm) {
    frappe.breadcrumbs.clear();
    frappe.breadcrumbs.set_custom_breadcrumbs({
        route: "/app/support",
        label: "Support"
    });
    frappe.breadcrumbs.set_form_breadcrumb({
        doctype: frm.doc.doctype
    }, "form");
}