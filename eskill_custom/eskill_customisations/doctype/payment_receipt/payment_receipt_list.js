// Copyright (c) 2022, Eskill Trading and contributors
// For license information, please see license.txt

frappe.listview_settings['Payment Receipt'] = {
    add_fields: ["status"],
    colwidths: {
        name: 1
    },
    get_indicator(doc) {
        const colour = {
                'Pending Processing': "red",
                'Processed': "green",
        }[doc.status];
        return [doc.status, colour];
    },
};
