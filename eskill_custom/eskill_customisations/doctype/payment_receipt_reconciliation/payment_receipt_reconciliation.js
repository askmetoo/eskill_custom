// Copyright (c) 2022, Eskill Trading and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payment Receipt Reconciliation', {
    refresh(frm) {
        frm.disable_save();
        frm.set_df_property('receipts', 'cannot_add_rows', true);

        get_unprocessed_receipts(frm);
        create_entries(frm);
    },

    from_date(frm) {
        validate_date_filters(frm);
    },

    minimum_payment_amount(frm) {
        validate_payment_filters(frm)
    },

    maximum_payment_amount(frm) {
        validate_payment_filters(frm)
    },

    receipt_book(frm) {
        if (!frm.doc.receipt_book) {
            frm.reload_doc();
        }
    },

    to_date(frm) {
        validate_date_filters(frm);
    }
});

function create_entries(frm) {
    frm.add_custom_button(__("Create Entries"), () => {
        if (frm.doc.receipt_book) {
            frappe.call({
                doc: frm.doc,
                method: "create_entries",
                callback: () => {
                    frm.reload_doc();
                }
            });
        }
    });
}

function get_unprocessed_receipts(frm) {
    frm.add_custom_button(__("Get Unprocessed Receipts"), () => {
        frm.clear_table("receipts");
        if (frm.doc.receipt_book) {
            frappe.call({
                doc: frm.doc,
                method: "get_unprocessed_receipts",
                callback: () => {
                    if (!frm.doc.receipts.length) {
                        frappe.throw(__("There are no Payments Receipts pending processing."));
                    } else {
                        frm.refresh();
                    }
                }
            });
        }
    });
}

function validate_date_filters(frm) {
    if (frm.doc.from_date > frm.doc.to_date) {
        frm.set_value("to_date", null);
        frappe.throw(__("To date can not precede from date."));
    }
}

function validate_payment_filters(frm) {
    if (frm.doc.minimum_payment_amount > frm.doc.maximum_payment_amount) {
        frm.set_value("maximum_payment_amount", null);
        frappe.throw(__("Maximum payment amount can not be less than the minimum payment amount."));
    }
}
