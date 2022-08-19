const BORDER_SPEC = "solid 3px var(--border-color)"

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
	document.getElementsByClassName("page-head")[0].remove();
	
	$("<div class='price-lookup'></div>").appendTo(page.main);
	wrapper.price_lookup = new PriceLookupPage(wrapper);
}

class PriceLookupPage {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.page = wrapper.page;
		this.body = $(this.wrapper).find(".price-lookup");
		this.make();
		this.get_data();
	}

	make() {
		let parent = this;
		this.page.item_field = this.page.add_field({
			fieldname: 'item_code',
			label: __('Item'),
			fieldtype:'Link',
			options:'Item',
			change() {
				parent.get_data();
			}
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
						<td class="column-content column-right">
							${frappe.format(current_bin.valuation_rate, {fieldtype: "Currency"})}
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
									<td class="column-head column-right">
										Cost Price
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