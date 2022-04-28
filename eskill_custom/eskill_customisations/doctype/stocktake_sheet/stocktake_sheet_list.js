// Copyright (c) 2022, Eskill Trading and contributors
// For license information, please see license.txt

frappe.listview_settings['Stocktake Sheet'] = {
    get_indicator(doc) {
        const colour = {
            'Count in Progress': "blue",
            'No Variances': "green",
            'Recount Needed': "red",
            'Variances Found': "red",
        }[doc.status];
        return [doc.status, colour];
    }
};
