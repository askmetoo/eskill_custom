frappe.ui.form.on('Timesheet', {
    refresh(frm) {
        frm.add_custom_button(__("Issues"), function() {
            frm.save();
            frappe.route_options = {
                "name": '',
                "subject": '',
                "customer": '',
                "serial_number": '',
                "project": '',
                "status": '',
                "priority": '',
                "technician_name": ''
            };
            frappe.set_route("List", "Issue");
        });
        frm.add_custom_button(__("Tasks"), function() {
            frm.save();
            frappe.route_options = {
                "name": '',
                "subject": '',
                "project": '',
                "status": '',
                "priority": ''
            };
            frappe.set_route("List", "Task");
        });
        activity_doctype_filter(frm);
    }
});

function activity_doctype_filter(frm) {
    frm.get_field("time_logs").grid.fields_map.activity_doctype.get_query = function () {
        return {
            filters: [["DocType", "name", "in", ["Issue", "Quotation", "Sales Invoice", "Sales Order"]]]
        };
    };
}