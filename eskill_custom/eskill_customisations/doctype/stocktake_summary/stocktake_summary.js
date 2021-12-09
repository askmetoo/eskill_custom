// Copyright (c) 2021, Eskill Trading and contributors
// For license information, please see license.txt

frappe.ui.form.on('Stocktake Summary', {
    refresh(frm) {
        restrict_items_access(frm);
        if (frm.doc.items.length != 0 && !frm.doc.closed) {
            frm.add_custom_button(__("Reconcile Variances"), () => {
                let selected_rows = frm.fields_dict.items.grid.get_selected();
                console.log(selected_rows)
                if (selected_rows.length != 0) {
                    frappe.run_serially([
                        () => frappe.call({
                            doc: frm.doc,
                            method: "set_rows_to_reconcile",
                            args: {
                                rows: selected_rows
                            },
                            callback: () => {
                                frm.reload_doc();
                            }
                        }),
                        () => frappe.model.open_mapped_doc({
                            method: "eskill_custom.eskill_customisations.doctype.stocktake_summary.stocktake_summary.generate_reconciliation",
                            frm: frm
                        })
                    ]);
                }
            });
        }
    }
});


frappe.ui.form.on("Stocktake Summary Item", {
    form_render(frm, cdt, cdn) {
        frm.fields_dict.items.grid.get_row(cdn).wrapper.find(".grid-delete-row").hide();
        frm.fields_dict.items.grid.get_row(cdn).wrapper.find(".grid-move-row").hide();
    }
});


function restrict_items_access(frm) {
    frm.fields_dict.items.grid.cannot_add_rows = true;
    frm.fields_dict.items.grid.wrapper.find(".grid-move-row").hide();
    frm.fields_dict.items.grid.wrapper.find(".grid-remove-rows").hide();
    frm.fields_dict.items.grid.wrapper.find(".grid-remove-all-rows").hide();
    frm.refresh_field("items");
}
