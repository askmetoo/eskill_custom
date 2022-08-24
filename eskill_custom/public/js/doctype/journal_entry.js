frappe.ui.form.on('Journal Entry', {
});

frappe.ui.form.on('Journal Entry Account', {
    exchange_rate(frm, cdt, cdn) {
        convert_selected_to_base(frm, cdt, cdn);
    },

    usd_to_currency(frm, cdt, cdn) {
        convert_base_to_selected(frm, cdt, cdn);
    }
});

function convert_base_to_selected(frm, cdt, cdn) {
    if (locals[cdt][cdn].usd_to_currency) {
        console.log(locals[cdt][cdn].usd_to_currency)
        frappe.model.set_value(cdt, cdn, 'exchange_rate', roundNumber(1 / locals[cdt][cdn].usd_to_currency, 9));
    } else {
        frappe.model.set_value(cdt, cdn, 'exchange_rate', null);
    }
}

function convert_selected_to_base(frm, cdt, cdn) {
    if (locals[cdt][cdn].exchange_rate) {
        locals[cdt][cdn].usd_to_currency = roundNumber(1 / locals[cdt][cdn].exchange_rate, 4);
        frm.fields_dict.accounts.grid.grid_rows_by_docname[cdn].refresh_field("usd_to_currency");
    } else {
        frappe.model.set_value(cdt, cdn, 'usd_to_currency', null);
    }
}