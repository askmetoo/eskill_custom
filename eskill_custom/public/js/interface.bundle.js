frappe.require([
    "/assets/eskill_custom/js/utils/price_lookup.js"
]);

// Map keyboard shortcut 'Ctrl + P' for printing
frappe.ui.keys.on('ctrl+p', function(e) {
    e.preventDefault();
    e.currentTarget.cur_frm.print_doc();
    return false;
});

frappe.provide("eskill_custom.ui.price_dialog");