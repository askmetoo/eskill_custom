frappe.provide("eskill_custom.form.common")

eskill_custom.form.common.check_price = ({frm, table = "items", item_field = "item_code"} = {}) => {
    // the default table is "items" and the default item field is "item_code"
    if (frm.fields_dict.hasOwnProperty(table)) {
        frm.get_field(table).grid.add_custom_button(__("Check Price"), () => {
            const selected = frm.get_field(table).grid.get_selected_children();
            if (selected.length > 0 && selected[0].hasOwnProperty(item_field)) {
                eskill_custom.ui.price_dialog.update_window(selected[0][item_field]);
            }
        });
    }
}

eskill_custom.form.common.convert_base_to_selected = (frm) => {
    if (frm.doc.usd_to_currency) {
        frm.set_value('conversion_rate', roundNumber(1 / frm.doc.usd_to_currency, 9));
    } else {
        frm.set_value('conversion_rate', null);
    }
}

eskill_custom.form.common.convert_selected_to_base = (frm) => {
    if (frm.doc.conversion_rate) {
        frm.doc.usd_to_currency = roundNumber(1 / frm.doc.conversion_rate, 4);
        frm.refresh_field('usd_to_currency');
    } else {
        frm.set_value('usd_to_currency', null);
    }
}

eskill_custom.form.common.stock_availability = (frm) => {
    if (frm.fields_dict.hasOwnProperty("items")) {
        frm.add_custom_button(__("Stock Availability"), () => {
            if (frm.doc.items.length) {
                frappe.call({
                    method: "eskill_custom.api.stock_availability",
                    args: {
                        doctype: route[1],
                        items: frm.doc.items
                    }
                });
            }
        }, __("View"));
    }
}
