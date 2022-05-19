// Copyright (c) 2022, Eskill Trading and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payment Receipt', {
    refresh(frm) {
        set_filters(frm);
        if (
            frm.doc.docstatus == 1 && frm.doc.status == "Pending Processing"
            && (frappe.user_roles.includes("Accounts User") || frappe.user_roles.includes("Accounts Manager"))
        ) {
            frm.add_custom_button(__("Create Payment Entry"), () => {
                frappe.model.open_mapped_doc({
                    method: "eskill_custom.eskill_customisations.doctype.payment_receipt.payment_receipt.generate_payment_entry",
                    frm: frm,
                });
            });
        }
    },

    party(frm) {
        frm.clear_table("references");
        frm.refresh_field("references");
        reset_totals(frm);
    },

    paid_amount(frm) {
        frm.clear_table("references");
        frm.refresh_field("references");
        if (frm.doc.paid_amount < 0) {
            frappe.msgprint("You can not receipt a negative amount.");
            frm.set_value("paid_amount", 0);
        }
        reset_totals(frm);
    },

    references(frm) {
        reset_totals(frm);
    },

    get_outstanding_invoice(frm) {
        frappe.call({
            doc: frm.doc,
            method: "get_outstanding_invoices",
            callback: () => {
                frm.refresh();
            }
        });
    },
});

frappe.ui.form.on('Payment Receipt Reference', {
    references_add(frm) {
        reset_totals(frm);
    },

    references_remove(frm) {
        reset_totals(frm);
    },

    allocated_amount(frm, cdt, cdn) {
        if (locals[cdt][cdn].allocated_amount > locals[cdt][cdn].outstanding_amount) {
            locals[cdt][cdn].allocated_amount = locals[cdt][cdn].outstanding_amount;
            frm.refresh_fields();
            frappe.show_alert({
                message: __("Allocated amount can not exceed the outstanding amount."),
                indicator: "red"
            }, 10);
        } else if (locals[cdt][cdn].allocated_amount < 0) {
            locals[cdt][cdn].allocated_amount = 0;
            frm.refresh_fields();
            frappe.show_alert({
                message: __("Allocated amount can not be negative."),
                indicator: "red"
            }, 10);
        }
        reset_totals(frm);
        if (frm.doc.unallocated_amount < 0) {
            locals[cdt][cdn].allocated_amount += frm.doc.unallocated_amount;
            frm.refresh_fields();
            reset_totals(frm);
        }
    }
});

function reset_totals(frm) {
    let allocated_amount = 0;
    frm.doc.references.forEach((row) => {
        allocated_amount += row.allocated_amount
    });
    frm.set_value("total_allocated_amount", allocated_amount);
    frm.set_value("unallocated_amount", frm.doc.paid_amount - allocated_amount);
}

function set_filters(frm) {
    frm.get_field("party").get_query = () => {
        return {
            filters: {
                default_currency: frm.doc.currency
            }
        }
    }

    frm.get_field("references").grid.get_docfield("reference_name").get_query = () => {
        return {
            filters: [
                ["Sales Invoice", "customer", "=", frm.doc.party],
                ["Sales Invoice", "outstanding_amount", ">", 0],                
            ]
        }
    }
    frm.refresh_field("references");
}
