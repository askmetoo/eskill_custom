// Copyright (c) 2020, Eskill Trading and contributors
// For license information, please see license.txt

frappe.ui.form.on('Warranty Swap Out', {
    refresh(frm) {
        if (frm.doc.docstatus && frm.doc.serial_no_out && !frm.doc.new_delivery_note) {
            frm.add_custom_button(__("Issue Swap Out"), function() {
                const delivery = frappe.model.get_new_doc("Delivery Note");
                console.log("Delivery Note started.");
                delivery.naming_series = "DN.########";
                delivery.posting_date = frappe.datetime.nowdate();
                delivery.company = "Eskill Trading (Pvt) Ltd";
                delivery.customer = frm.doc.customer;
                var replacement = frappe.model.add_child(delivery, "Delivery Note Item", "items");
                frappe.model.with_doc("Item", frm.doc.model_out, function() {
                    var item = frappe.model.get_doc("Item", frm.doc.model_out);
                    replacement.item_code = item.name;
                    replacement.item_name = item.item_name;
                    replacement.description = item.description;
                    replacement.qty = 1;
                    replacement.schedule_date = delivery.schedule_date;
                    replacement.uom = item.stock_uom;
                    replacement.stock_uom = item.stock_uom;
                    replacement.conversion_factor = 1;
                    replacement.serial_no = frm.doc.serial_no_out;
                    replacement.expense_account = "20400 - Warranty Claims - ET";
                });
                frappe.db.insert(delivery).then( function(note) {
                    frm.doc.new_delivery_note = note.name;
                    frm.save();
                });
                console.log("Delivery Note created.");
            });
        }
        if (frm.doc.new_delivery_note) {
            
        }
        model_out_filter(frm);
        serial_out_filter(frm);
        product_out_read_only(frm);
    },

    before_save(frm) {
        if (frm.doc.edit_posting_date) {
            frm.doc.edit_posting_date = 0;
        }
    },

    after_save(frm) {
        update_service_order();
    },
    
    before_submit(frm) {
        if (!frm.doc.swap_out_reason) {
            frappe.throw(__("Before submitting you must provide an explanation for the swap out."));
        }
    },

    after_cancel(frm) {
        update_service_order();
    },
    
    customer: function(frm) {
        claim_filter(frm);
    },
    
    model_in: function(frm) {
        model_out_filter(frm);
    },
    
    model_out: function(frm) {
        serial_out_filter(frm);
    }
});


function model_out_filter(frm) {
    if (frm.doc.model_in) {
        frappe.model.with_doc('Item', frm.doc.model_in, function() {
            frm.fields_dict.model_out.get_query = function() {
                return {
                    filters: [
                        ['Item', 'item_group', '=', frappe.model.get_doc('Item', frm.doc.model_in).item_group],
                        ['Item', 'disabled', '=', false]
                    ]
                };
            };
        });
    } else {
        frm.fields_dict.model_out.get_query = function() {
            return {
                filters: [
                    ['Item', 'disabled', '=', false]
                ]
            };
        };
    }
}


function serial_out_filter(frm) {
    if (!frm.doc.model_out) {
        if (frm.doc.serial_no_out) {
            frm.doc.serial_no_out = undefined;
        }
    } else {
        frm.fields_dict.serial_no_out.get_query = function() {
            return {
                filters: [
                    ['Serial No', 'item_code', '=', frm.doc.model_out],
                    ['Serial No', 'status', '=', 'Active']
                ]
            };
        };
    }
}


function product_out_read_only(frm) {
    if (frm.doc.new_delivery_note) {
        frm.set_df_property("model_out", "read_only", 1);
        frm.set_df_property("serial_no_out", "read_only", 1);
    }
}


function update_service_order() {
    frappe.call({
        method: "update_service_order"
    });
}
