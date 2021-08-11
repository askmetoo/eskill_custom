// Copyright (c) 2021, Eskill Trading and contributors
// For license information, please see license.txt

frappe.listview_settings['Device SLA'] = {
    get_indicator: function(doc) {
        var status_color = {
            "Inactive": "darkgrey",
            "Active": "green",
            "Expired": "red",
            "Breached": "red",
        };
        return [__(doc.status), status_color[doc.status], "state,=,"+doc.status];
    },
};
