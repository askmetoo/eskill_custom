// Copyright (c) 2021, Eskill Trading and contributors
// For license information, please see license.txt

frappe.ui.form.on("Stocktake Sheet", {
    refresh(frm) {
        restrict_items_access(frm);
        submit_sheet(frm);
    }
});


frappe.ui.form.on("Stocktake Sheet Item", {
    form_render(frm, cdt, cdn) {
        frm.fields_dict.items.grid.get_row(cdn).toggle_view();
    }
});


function restrict_items_access(frm) {
    if ((frm.doc.counter != frappe.session.user) && frappe.user_roles.includes("Stocktake User")) {
        frm.set_df_property("items", "hidden", 1);
    }
    if (!frappe.user_roles.includes("Stocktake User") || frm.doc.count_complete) {
        frm.fields_dict.items.grid.update_docfield_property("counted_qty", "read_only", 1);
    }
    if (frm.doc.count_complete) {
        frm.set_df_property("items", "read_only", 1);
    } else {
        frm.fields_dict.items.grid.cannot_add_rows = true;
        frm.fields_dict.items.grid.wrapper.find(".grid-move-row").hide();
        frm.fields_dict.items.grid.wrapper.find(".grid-remove-rows").hide();
        frm.fields_dict.items.grid.wrapper.find(".grid-remove-all-rows").hide();
    }
    frm.refresh_field("items");
}


function submit_sheet(frm) {
    if (!frm.doc.count_complete) {
        frm.add_custom_button(__("Submit Sheet"), () => {
            if (frm.is_dirty()) {
                frappe.msgprint(__("Please save before submitting your count."));
            } else {
                frappe.confirm(
                    "Are you sure that you are ready to proceed?",
                    () => {
                        frappe.call({
                            doc: frm.doc,
                            method: "check_count",
                            callback: (response) => {
                                if (response.message) {
                                    frm.reload_doc();
                                    frappe.set_route("Form", "Stocktake Sheet", response.message);
                                } else {
                                    frm.reload_doc();
                                }
                            }
                        });
                    }
                );
            }
        });
    }
}
