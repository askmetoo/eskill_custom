frappe.pages['credit-notes'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Credit Notes',
		single_column: true
	});
	$(frappe.render_template('credit_notes')).appendTo(page.body).height('80vh');

	var time = new Date().getTime();
	$(document.body).bind("mousemove keypress", function(e) {
		time = new Date().getTime();
	});

	function refresh() {
		if(new Date().getTime() - time >= 60000) 
			window.location.reload(true);
		else 
			setTimeout(refresh, 10000);
	}

	setTimeout(refresh, 10000);
}