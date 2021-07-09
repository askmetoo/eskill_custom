// Copyright (c) 2021, Eskill Trading and contributors
// For license information, please see license.txt

frappe.ui.form.on('Warranty Signup', {
	refresh: function(frm) {
		serial_number_filter(frm);
	},

	before_save: function(frm) {
		validate_date(frm.doc.purchase_date);
		if (frm.doc.provided_serial_no) {
			frm.set_value('provided_serial_no', frm.doc.provided_serial_no.toUpperCase());
		}
		if ((!frm.doc.serial_number || !frm.doc.purchase_receipt || !frm.doc.purchase_date || !frm.doc.reseller) && frm.doc.approved) {
			frm.set_value('approved', 0);
		}
	},

	before_submit(frm) {
		if (!frm.doc.approved) {
			frappe.validated = false;
			frappe.throw("The form has not been approved. To get approval the following are required: Serial Number; Purchase Date; Reseller; Purchase Receipt.");
		}

		if (frm.doc.approved) {
			frm.set_value('status', 'Approved');
		} else {
			frappe.confirm('Are you sure you want to reject this registration?',
				() => {
					frm.set_value('status', 'Rejected');
				}, 
				() => {
					frappe.validated = false;
				}
			);
		}
	},
	
	purchase_date: function(frm) {
		validate_date(frm.doc.purchase_date);
	},

	check_receipt: function(frm) {
		open_purchase_receipt(frm);
	}
});

function serial_number_filter(frm) {
	frm.fields_dict.serial_number.get_query = function () {
		return {
			filters: [
				['Serial No', 'brand', '=', 'Canon']
			]
		};
	};
}

function validate_date(date) {
	frappe.call({
		method: "eskill_custom.api.get_date",
		args: {
			interval: -2,
			interval_type: "week"
		},
		callback: function(data) {
			if (date < data.message) {
				frappe.throw(__("The purchase date must not be more than two weeks prior to today."));
				frappe.validated = false
			} else if (date > frappe.datetime.now_date()) {
				frappe.throw(__("The purchase date can not be in the future."));
				frappe.validated = false
			}
		}
	});
}

function open_purchase_receipt(frm) {
    if (frm.doc.purchase_receipt) {
        window.open(frm.doc.purchase_receipt);
    } else {
        frappe.msgprint("No purchase receipt.");
    }
}
