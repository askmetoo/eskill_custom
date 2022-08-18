// Copyright (c) 2020, Eskill Trading and contributors
// For license information, please see license.txt

frappe.ui.form.on('Warranty Swap Out', {
    refresh(frm) {
        // allow approval of Warranty Swap Out if document has been submitted and hasn't yet been approved
        if (frm.doc.docstatus && !frm.doc.approved) {
            approve_swap(frm);
        }
        if (frm.doc.approved && frm.doc.status == "Pending Processing") {
            deliver_swapped_device(frm);        
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

    before_submit(frm) {
        if (!frm.doc.swap_out_reason) {
            frappe.throw(__("Before submitting you must provide an explanation for the swap out."));
        }

        if (!frm.doc.model_out || !frm.doc.serial_no_out) {
            frappe.throw(__("Before submitting, you must select a device to replace the customer's device."));
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


function approve_swap(frm) {
    frm.add_custom_button(__("Approve"), () => {
        frm.set_value("approved", 1).then(() => {
            frm.save_or_update();
        });
    });
}


function deliver_swapped_device(frm) {
    frm.add_custom_button("Delivery Note", () => {
        frappe.model.open_mapped_doc({
            method: "eskill_custom.eskill_customisations.doctype.warranty_swap_out.warranty_swap_out.generate_delivery",
            frm: frm,
        });
    });
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
