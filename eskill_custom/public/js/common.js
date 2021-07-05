function check_save(frm) {
    if (frm.doc.__unsaved) {
        frm.save();
    }
}

function get_bid_rate(frm) {
    if (frm.doc.currency == "USD") {
        frappe.call({
            method: "eskill_custom.api.auction_rate_lookup",
            args: {
                posting_date: frm.doc.posting_date
            },
            callback: function(data) {
                frm.set_value("auction_bid_rate", data.message);
            }
        });
        console.log("Got bid rate.");
    }
}

function get_bid_rate(frm) {
    frappe.call({
        method: "eskill_custom.api.auction_rate_lookup",
        args: {
            posting_date: frm.doc.posting_date
        },
        callback: function(data) {
            frm.set_value("auction_bid_rate", data.message);
        }
    });
    console.log("Got bid rate.");
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
    const table_fields = [
        {
            fieldname: "location", fieldtype: "Text",
            in_list_view: 1, label: "Location",
            options: "Warehouse", read_only: 1
        },
        {
            fieldname: "quantity", fieldtype: "Float",
            in_list_view: 1, label: "Quantity",
            read_only: 1
        }
    ];
    frappe.call({
        method: "eskill_custom.api.stock_lookup",
        args: {
            doctype: frm.doctype,
            user: frappe.session.user,
            item: frm.doc.stock_item
        },
        callback: function (data) {
            if (data.message) {
                const results = data.message;
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
                            fieldname: "sb1",
                            fieldtype: "Section Break"
                        },
                        {
                            fieldname: "currency",
                            label: "Currency",
                            fieldtype: "Link",
                            options: "Currency",
                            change: function() {
                                frappe.call({
                                    method: "eskill_custom.api.item_price_lookup",
                                    args: {
                                        doctype: frm.doctype,
                                        currency: dialog.fields_dict.currency.value,
                                        price_list: "Standard Selling",
                                        item: frm.doc.stock_item
                                    },
                                    callback: function(data) {
                                        if (data.message) {
                                            if (data.message == "Unavailable") {
                                                dialog.set_value("price", data.message);
                                            } else {
                                                dialog.set_value("price", data.message[0][0]);
                                            }
                                        } else {
                                            dialog.set_value("price", "Unavailable");
                                        }
                                    }
                                });
                            }
                        },
                        {
                            fieldname: "cb1",
                            fieldtype: "Column Break"
                        },
                        {
                            fieldname: "price",
                            label: "Price",
                            fieldtype: "Data",
                            read_only: 1
                        },
                        {
                            fieldname: "sb2",
                            fieldtype: "Section Break"
                        },
                        {
                            fieldname: "stock_levels",
                            fieldtype: "Table",
                            label: "Stock Levels",
                            cannot_add_rows: true,
                            in_place_edit: false,
                            read_only: 1,
                            data: results,
                            fields: table_fields
                        }
                    ],
                    primary_action: function() {
                        dialog.hide();
                    },
                    primary_action_label: "Close"
                });
                dialog.fields_dict.currency.get_query = function() {
                    return {
                        filters: [
                            ["Currency", "enabled", "=", true]
                        ]
                    };
                };
                dialog.show();
            } else {
                frappe.message("There is no available stock.");
            }
        }
    });
}
