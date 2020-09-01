frappe.pages['support-dashboard'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'support',
		single_column: true
	});
	$(frappe.render_template('support_dashboard')).appendTo(page.body);
}