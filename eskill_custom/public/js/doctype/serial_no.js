// Copyright (c) 2021, Eskill Trading and contributors
// For license information, please see license.txt


frappe.form.link_formatters['Customer'] = (value, doc) => {
    if (value == doc.owned_by && value != doc.owned_by_name) {
        return value + ": " + doc.owned_by_name;
    } else if (value == doc.customer && value != doc.customer_name) {
        return value + ": " + doc.customer_name;
    } else {
        return value;
    }
}


frappe.ui.form.on('Serial No', {
});
