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

function stock_item_filter(frm) {
    frm.fields_dict.stock_item.get_query = function () {
        return {
            filters: [
                ["Item", "is_stock_item", "=", true],
                ["Item", "disabled", "=", false],
            ],
        };
    };
}

function stock_lookup(frm) {
    if (frm.doc.stock_item) {
        frappe.call({
            method: "eskill_custom.api.stock_lookup",
            args: {
                item: frm.doc.stock_item
            },
            callback: (response) => {
                if (response.message) {
                    const table_fields = [
                        {
                            fieldname: "warehouse",
                            fieldtype: "Text",
                            in_list_view: 1,
                            label: "Location",
                            options: "Warehouse",
                            read_only: 1
                        },
                        {
                            fieldname: "reserved_qty",
                            fieldtype: "Float",
                            in_list_view: 1,
                            label: "Reserved Qty",
                            read_only: 1
                        },
                        {
                            fieldname: "actual_qty",
                            fieldtype: "Float",
                            in_list_view: 1,
                            label: "Actual Qty",
                            read_only: 1
                        },
                        {
                            fieldname: "valuation_rate",
                            label: "Cost Price",
                            fieldtype: "Currency",
                            options: frappe.sys_defaults.currency,
                            in_list_view: 1,
                            read_only: 1
                        }
                    ];
                    const dialog = new frappe.ui.Dialog({
                        title: __("Stock Availability"),
                        static: true,
                        fields: [
                            {
                                fieldname: "item",
                                label: "Item",
                                fieldtype: "Link",
                                options: "Item",
                                default: frm.doc.stock_item,
                                read_only: 1
                            },
                            {
                                fieldname: "section_break_3",
                                fieldtype: "Section Break"
                            },
                            {
                                fieldname: "stock_levels",
                                fieldtype: "Table",
                                label: "Stock Levels",
                                cannot_add_rows: true,
                                in_place_edit: false,
                                read_only: 1,
                                data: response.message,
                                fields: table_fields
                            }
                        ],
                        primary_action: () => {
                            dialog.hide();
                        },
                        primary_action_label: "Close"
                    });
                    // dialog.show();
                } else {
                    frappe.message("There is no available stock.");
                }
            }
        });
    } else {
        frappe.msgprint("Please select a stock item to lookup first.");
    }
}
