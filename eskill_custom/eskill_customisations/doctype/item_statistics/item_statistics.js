// Copyright (c) 2022, Eskill Trading and contributors
// For license information, please see license.txt

const CURRENT_DATE = new Date();
const DYNAMIC_LABELS = ["avg_qty_sold", "cost_increase_per_period", "avg_services"]

frappe.form.link_formatters['Customer'] = (value, doc) => {
	return doc.customer_name;
}	

frappe.ui.form.on('Item Statistics', {
	refresh(frm) {
		frm.disable_save();
		frm.get_field("item_code").get_query = () => {
			return {
				filters: {
					disabled: 0,
					is_stock_item: 1
				}
			}
		}
		set_default_dates(frm);
		get_statistics(frm);
	},

	from_date(frm) {
		if (frm.doc.from_date && frm.doc.from_date > frm.doc.to_date) {
			frm.set_value("from_date", null);
			frappe.msgprint("The from date can not exceed the to date.");
		}
	},

	to_date(frm) {
		if (frm.doc.to_date && frm.doc.to_date < frm.doc.from_date) {
			frm.set_value("to_date", null);
			frappe.msgprint("The to date can not be less than the from date.");
		}
	}
});

function get_statistics(frm) {
	frm.add_custom_button(__("Get Statistics"), () => {
		frm.clear_table("item_statistics_sold_to_customers");
		frm.clear_table("item_statistics_purchase_receipts");
		frm.clear_table("item_statistics_service_orders");
		frappe.call({
			doc: frm.doc,
			method: "get_statistics",
			callback: (response) => {
				if (frm.get_field("avg_qty_sold").df.label.includes("Period")) {
					DYNAMIC_LABELS.forEach((row) => {
						frm.set_df_property(row, "label", frm.get_field(row).df.label.replace("Period", response.message));
					});
					frm.grids[0].grid.visible_columns[2][0].label = frm.grids[0].grid.visible_columns[2][0].label.replace("Period", response.message);
				} else if (frm.get_field("avg_qty_sold").df.label.includes("Day")) {
					DYNAMIC_LABELS.forEach((row) => {
						frm.set_df_property(row, "label", frm.get_field(row).df.label.replace("Day", response.message));
					});
					frm.grids[0].grid.visible_columns[2][0].label = frm.grids[0].grid.visible_columns[2][0].label.replace("Day", response.message);
				} else if (frm.get_field("avg_qty_sold").df.label.includes("Month")) {
					DYNAMIC_LABELS.forEach((row) => {
						frm.set_df_property(row, "label", frm.get_field(row).df.label.replace("Month", response.message));
					});
					frm.grids[0].grid.visible_columns[2][0].label = frm.grids[0].grid.visible_columns[2][0].label.replace("Month", response.message);
				} else {
					DYNAMIC_LABELS.forEach((row) => {
						frm.set_df_property(row, "label", frm.get_field(row).df.label.replace("Year", response.message));
					});
					frm.grids[0].grid.visible_columns[2][0].label = frm.grids[0].grid.visible_columns[2][0].label.replace("Year", response.message);
				}
				frm.refresh_fields();
			}
		});
	});
}

function set_default_dates(frm) {
	frm.set_value("from_date", CURRENT_DATE.getFullYear() + "-01-01");
	frm.set_value("to_date", CURRENT_DATE.getFullYear() + "-12-31");
}
