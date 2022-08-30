// specification of borders used in the table for uniformity
const BORDER_SPEC = "solid 3px var(--border-color)"

// tax rate used for calculating the minimum selling price
const TAX_RATE = 1.145;

frappe.pages['price-lookup'].on_page_load = function(wrapper) {
	let page = frappe.ui.make_app_page({
		parent: wrapper,
		show_sidebar: 0,
		single_column: true
	});

	const styles = document.createElement("style");
	styles.setAttribute("type", "text/css");

	styles.innerHTML = `
		.column-head {
			font-weight: bold;
			border-bottom: ${BORDER_SPEC};
			border-right: ${BORDER_SPEC};
			text-align: center;
			padding: 1mm;
		}

		.column-content {
			border-right: ${BORDER_SPEC};
			padding: 1mm;
		}

		.column-content-number {
			text-align: center;
		}

		.column-right {
			border-right: none;
		}

		.no-info {
			color: var(--gray);
		}
	`
	
	document.head.insertAdjacentElement("beforeend", styles);
	// document.getElementsByClassName("page-head")[0].remove(); // this statement needs to commented out if you want to display any buttons
	document.getElementsByClassName("page-head-content")[0].setAttribute("style", "height: 35px;");
	
	$("<div class='price-lookup'></div>").appendTo(page.main);
	wrapper.price_lookup = new PriceLookupPage(wrapper);
}

class PriceLookupPage {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.page = wrapper.page;
		this.body = $(this.wrapper).find(".price-lookup");
		this.min_gp_rate = 1;

		if(!window.hasOwnProperty("current_item")) window.current_item = undefined;

		this.make();
		this.get_data();

		// refresh table continuously as long as the item is unchanged
		setInterval(() => {
			if (current_item && this.page.match_price_check.value) {
				if (this.page.item_field.value == current_item.item_obj[current_item.item_field]) {
					this.page.base_selling_price.set_value(current_item.item_obj[current_item.base_rate_field]);
				}
			}
		}, 1000);

		// add button to resync lookup dialog with the last selected item
		this.page.add_inner_button(__("Refresh"), () => {
			if (!this.page.match_price_check.value) {
				if (!current_item) {
					frappe.msgprint('This lookup window is not linked to a specific item.<br>Please use the "Check Price" button to link to an item.');
				} else {
					this.page.match_price_check.set_value(1);
					this.page.item_field.set_value(current_item.item_obj[current_item.item_field]);
					this.page.base_selling_price.set_value(current_item.item_obj[current_item.base_rate_field]);
				}
			}
		});
	}

	make() {
		const parent = this;
		this.page.item_field = this.page.add_field({
			fieldname: "item_code",
			label: __("Item"),
			fieldtype: "Link",
			options: "Item",
			change() {
				if (current_item) {
					if (this.value != current_item.item_obj[current_item.item_field]) {
						parent.page.match_price_check.set_value(0);
					}
				}

				frappe.call({
					method: "eskill_custom.eskill_customisations.page.price_lookup.price_lookup.get_gp_rate",
					args: {
						item_code: this.value
					},
					callback(response) {
						parent.min_gp_rate = response.message;
						parent.get_data();
					}
				});
			}
		});

		this.page.base_selling_price = this.page.add_field({
			fieldname: "base_selling_price",
			label: __("Base Selling Price"),
			fieldtype: "Currency",
			change() {
				if (current_item) {
					if (this.value != current_item.item_obj[current_item.base_rate_field]) {
						parent.page.match_price_check.set_value(0);
					}
				}

				frappe.call({
					method: "eskill_custom.eskill_customisations.page.price_lookup.price_lookup.get_gp_rate",
					args: {
						item_code: parent.page.item_field.value
					},
					callback(response) {
						parent.min_gp_rate = response.message;
						parent.get_data();
					}
				});
			}
		});

		this.page.match_price_check = this.page.add_field({
			fieldname: "match_price_check",
			fieldtype: "Check",
			default: 0,
			hidden: 1
		});
	}

	get_data() {
		frappe.db.get_list('Bin', {
			fields: [
				"warehouse",
				"actual_qty",
				"reserved_qty",
				"ordered_qty",
				"valuation_rate"
			],
			filters: {
				item_code: this.page.item_field.value
			}
		}).then((bins) => {
			let html_body = "";
			const table_rows = [];
			// const last_details = bins.length > 0 ? bins[0] : {};

			for (let i = 0; i < bins.length; i++) {
				const current_bin = bins[i];

				if ((current_bin.actual_qty + current_bin.reserved_qty + current_bin.ordered_qty) == 0) {
					continue;
				}

				const selling_price = Math.ceil(current_bin.valuation_rate * TAX_RATE * this.min_gp_rate);
				const current_gp_rate = (this.page.base_selling_price.value / TAX_RATE / current_bin.valuation_rate - 1) * 100;

				table_rows.push(`
					<tr>
						<td class="column-content">
							${current_bin.warehouse}
						</td>
						<td class="column-content column-content-number">
							${current_bin.actual_qty}
						</td>
						<td class="column-content column-content-number">
							${current_bin.reserved_qty}
						</td>
						<td class="column-content column-content-number">
							${current_bin.ordered_qty}
						</td>
						<td class="column-content">
							${frappe.format(current_bin.valuation_rate, {fieldtype: "Currency"})}
						</td>
						<td class="column-content">
							${frappe.format(selling_price, {fieldtype: "Currency"})}
						</td>
						<td class="column-content column-right" ${(current_gp_rate / 100 + 1) < this.min_gp_rate ? 'style="color: red;"' : ''}>
							${frappe.format(current_gp_rate, {fieldtype: "Percent"})}
						</td>
					</tr>
				`)
			}

			if (bins.length > 0) {
				html_body += `
					<div class="page-form">
						<table style="width: 100%;">
							<thead>
								<tr>
									<td class="column-head">
										Warehouse
									</td>
									<td class="column-head">
										Actual Qty
									</td>
									<td class="column-head">
										Reserved Qty
									</td>
									<td class="column-head">
										Ordered Qty
									</td>
									<td class="column-head">
										Cost Price
									</td>
									<td class="column-head">
										Min. Selling Price
									</td>
									<td class="column-head column-right">
										GP %
									</td>
								</tr>
							</thead>
							<tbody>
				`;

				for (let i = 0; i < table_rows.length; i++) {
					html_body += table_rows[i];
				}

				html_body += "</tbody></table></div>"
			} else {
				html_body += `
					<div class="page-form no-info">
						There is no information to show...
					</div>
				`
			}

			this.body[0].innerHTML = html_body;
		});
	}
}
