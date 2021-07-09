frappe.init_client_script = () => {
	frappe.web_form.ready = () => {
	}

	frappe.web_form.on('purchase_date', (field, value) => {
		validate_date(value);
	});
};

async function validate_date(date) {
	let data = await frappe.call({
		method: "eskill_custom.api.get_date",
		args: {
			interval: -2,
			interval_type: "week"
		}
	});
	if (date < data.message) {
		frappe.web_form.set_value('purchase_date', '');
		frappe.throw(__("The purchase date must not be more than two weeks prior to today."));
	} else if (date > frappe.datetime.now_date()) {
		frappe.web_form.set_value('purchase_date', '');
		frappe.throw(__("The purchase date can not be in the future."));
	}
}