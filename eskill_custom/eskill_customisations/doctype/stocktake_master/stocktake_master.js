// Copyright (c) 2021, Eskill Trading and contributors
// For license information, please see license.txt

frappe.ui.form.on('Stocktake Master', {
    refresh(frm) {
        warehouse_filter(frm);
        if (frm.doc.count_complete && !frm.doc.report_generated) {
            frm.add_custom_button(__("Generate Summary"), () => {
                frappe.call({
                    doc: frm.doc,
                    method: "generate_summary",
                    callback: (response) => {
                        frm.reload_doc();
                        if (response.message) {
                            frappe.set_route("Form", "Stocktake Summary", response.message);
                        } else {
                            frappe.msgprint("An error occurred when generating the summary.");
                        }
                    }
                })
            });
        }
    },

    report_date(frm) {
        frm.clear_table("warehouse_list");
        frm.refresh_fields();
    }
});


function warehouse_filter(frm) {
    frm.fields_dict.warehouse_list.grid.fields_map.warehouse.get_query = function() {
        return {
            filters: [
                ["Warehouse", "disabled", "=", 0]
            ]
        };
    };
}
