frappe.ui.form.on('Task', {
	refresh(frm) {
	    if (frm.doc.status == 'Completed') {
            frm.add_custom_button("Reopen", function() {
                frm.set_value("status", "Open");
                frm.set_value("progress", 95);
                frm.save();
            });
	    } else if (frm.doc.status == 'Cancelled'){
            frm.add_custom_button("Reopen", function() {
                frm.set_value("status", "Open");
                frm.save();
            });
	    } else if (frm.doc.status == "Open") {
            frm.add_custom_button("Working", function() {
                frm.set_value("status", "Working");
                frm.save();
            }, "Set Status");
            frm.add_custom_button("Pending Review", function() {
                frm.set_value("status", "Pending Review");
                frm.save();
            }, "Set Status");
            frm.add_custom_button("Cancel", function() {
                frm.set_value("status", "Cancelled");
                frm.save();
            }, "Set Status");
            frm.add_custom_button("Complete", function() {
                frm.set_value("status", "Completed");
                frm.save();
            }, "Set Status");
	    } else if (frm.doc.status == "Working") {
            frm.add_custom_button("Open", function() {
                frm.set_value("status", "Open");
                frm.save();
            }, "Set Status");
            frm.add_custom_button("Pending Review", function() {
                frm.set_value("status", "Pending Review");
                frm.save();
            }, "Set Status");
            frm.add_custom_button("Cancel", function() {
                frm.set_value("status", "Cancelled");
                frm.save();
            }, "Set Status");
            frm.add_custom_button("Complete", function() {
                frm.set_value("status", "Completed");
                frm.save();
            }, "Set Status");
	    } else if (frm.doc.status == "Pending Review") {
            frm.add_custom_button("Open", function() {
                frm.set_value("status", "Open");
                frm.save();
            }, "Set Status");
            frm.add_custom_button("Working", function() {
                frm.set_value("status", "Working");
                frm.save();
            }, "Set Status");
            frm.add_custom_button("Cancel", function() {
                frm.set_value("status", "Cancelled");
                frm.save();
            }, "Set Status");
            frm.add_custom_button("Complete", function() {
                frm.set_value("status", "Completed");
                frm.save();
            }, "Set Status");
	    } else if (frm.doc.status == "Overdue") {
            frm.add_custom_button("Cancel", function() {
                frm.set_value("status", "Cancelled");
                frm.save();
            }, "Set Status");
            frm.add_custom_button("Complete", function() {
                frm.set_value("status", "Completed");
                frm.save();
            }, "Set Status");
	    }
	},
	
	status: function(frm) {
	    if (frm.doc.status != "Completed") {
	        frm.set_value("completed_by", "");
	    } else {
	        frm.set_value("completed_by", frappe.session.user);
	    }
	    if (frm.doc.status == "Working" && frm.doc.progress === 0) {
	        frm.set_value("progress", 5);
	    }
	}
});