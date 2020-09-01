frappe.pages['gross-profit'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Gross Profit',
		single_column: true
	});
	$(frappe.render_template('gross_profit')).appendTo(page.body);
}