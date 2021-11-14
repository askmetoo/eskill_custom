frappe.ui.form.on('Timesheet', {
    refresh(frm) {
        frm.add_custom_button(__("Issues"), function() {
            frm.save();
            frappe.set_route("List", "Issue");
        });
        frm.add_custom_button(__("Tasks"), function() {
            frm.save();
            frappe.set_route("List", "Task");
        });
        frm.remove_custom_button("Create Sales Invoice");
        frm.remove_custom_button("Create Salary Slip");
        activity_doctype_filter(frm);
    },

    after_save(frm) {
        frappe.call({
            method: "eskill_custom.timesheet.service_order_time",
            args: {
                timesheet: frm.doc.name
            },
            callback: (response) => {
                if (response.message) {
                    frappe.msgprint(response.message, "Updated Service Orders")
                }
            }
        });
    }
});

frappe.ui.form.on('Timesheet Detail', {
    before_time_logs_remove: function(frm, cdt, cdn) {
        if (locals[cdt][cdn].activity_doctype == "Service Order") {
            frappe.call({
                method: "eskill_custom.timesheet.service_order_time",
                args: {
                    timesheet: frm.doc.name,
                    timesheet_detail: cdn,
                    service_order: locals[cdt][cdn].activity_document
                },
                callback: (response) => {
                    console.log(response.message);
                }
            });
        }
    }
});

function activity_doctype_filter(frm) {
    frm.get_field("time_logs").grid.fields_map.activity_doctype.get_query = function () {
        return {
            filters: [
                ["DocType", "name", "in", ["Issue", "Quotation", "Sales Invoice", "Sales Order", "Service Order"]]
            ]
        };
    };
}