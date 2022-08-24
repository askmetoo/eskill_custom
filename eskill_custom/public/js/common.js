// Map keyboard shortcut 'Ctrl + P' for printing
frappe.ui.keys.on('ctrl+p', function(e) {
    e.preventDefault();
    e.currentTarget.cur_frm.print_doc();
    return false;
});

// Get current doctype and apply given form script overrides
route = frappe.get_route()
if (route[0] == "Form") {
    frappe.ui.form.on(route[1], {
        refresh(frm) {
            stock_availability(frm);
        }
    });
}

function check_save(frm) {
    if (frm.is_dirty()) {
        frm.save();
    }
}

function convert_base_to_selected(frm) {
    if (frm.doc.usd_to_currency) {
        frm.set_value('conversion_rate', roundNumber(1 / frm.doc.usd_to_currency, 9));
    } else {
        frm.set_value('conversion_rate', null);
    }
}

function convert_selected_to_base(frm) {
    if (frm.doc.conversion_rate) {
        frm.doc.usd_to_currency = roundNumber(1 / frm.doc.conversion_rate, 4);
        frm.refresh_field('usd_to_currency');
    } else {
        frm.set_value('usd_to_currency', null);
    }
}

function stock_availability(frm) {
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
