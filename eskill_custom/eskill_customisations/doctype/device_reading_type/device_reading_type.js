// Copyright (c) 2020, Eskill Trading and contributors
// For license information, please see license.txt

frappe.ui.form.on('Device Reading Type', {
	refresh(frm) {
		if (frm.doc.item_code) {
			frm.set_df_property("item_code", "reqd", 1);
		}
	}
});
