// Copyright (c) 2020, Eskill Trading and contributors
// For license information, please see license.txt

frappe.ui.form.on('Warranty Swap Out', {
    refresh(frm) {
        if (!frm.doc.docstatus && frm.doc.serial_no_out && !frm.doc.new_delivery_note) {
            frm.add_custom_button(__("Delivery Note"), function() {
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
        frm.fields_dict.issue.get_query = function() {
            return {
                filters: [
                    ['Issue', "serial_number", "is", "set"]
                ]
            };
        };
        frm.fields_dict.customer.get_query = function() {
            return{
                filters: [
                    ['Customer', 'disabled', '=', false]
                ]
            };
        };
        if (frm.doc.new_delivery_note) {
            
        }
        claim_filter(frm);
        model_out_filter(frm);
        serial_out_filter(frm);
        product_out_read_only(frm);
    },
    
    before_submit(frm) {
        if (!frm.doc.new_delivery_note) {
            validated = false;
            frappe.throw("Delivery note for outgoing product is required!");
        }
        if (!frm.doc.serial_no_out) {
            validated = false;
            frappe.throw("Serial number for outgoing product is required!");
        }
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

function claim_filter(frm) {
    if (frm.doc.customer) {
        frm.fields_dict.warranty_claim.get_query = function() {
            return{
                filters: [
                    ['Warranty Claim', 'customer', '=', frm.doc.customer],
                    ['Warranty Claim', 'status', '!=', 'Cancelled']
                ]
            };
        };
    } else {
        frm.fields_dict.warranty_claim.get_query = function() {
            return {
                filters: [
                    ['Warranty Claim', 'status', '!=', 'Cancelled']
                ]
            };
        };
    }
}

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