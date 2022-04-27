// Copyright (c) 2022, Eskill Trading and contributors
// For license information, please see license.txt

frappe.listview_settings['KB Article'] = {
    add_fields: ["status"],
    colwidths: {
        name: 1
    },
    get_indicator(doc) {
        const colour = {
                'Current': "green",
                'Outdated': "orange",
                'Invalidated': "red",
        }[doc.status];
        return [doc.status, colour];
    },
    hide_name_column: true,
    onload(list) {
        frappe.route_options = {
            status: "Current",
            docstatus: 1
        };
    }
};
