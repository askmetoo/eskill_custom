frappe.provide("eskill_custom.form.common");

eskill_custom.form.common.check_price = ({
  frm,
  table = "items",
  item_field = "item_code",
  base_rate_field = "base_rate",
} = {}) => {
  // the default table is "items" and the default item field is "item_code"
  if (frm.fields_dict.hasOwnProperty(table)) {
    frm.get_field(table).grid.add_custom_button(__("Check Price"), () => {
      const selected = frm.get_field(table).grid.get_selected_children();
      if (selected.length > 0) {
        item_field = selected[0].hasOwnProperty(item_field)
          ? item_field
          : undefined;
        base_rate_field = selected[0].hasOwnProperty(base_rate_field)
          ? base_rate_field
          : undefined;
        eskill_custom.ui.price_dialog.update_window(
          selected[0],
          item_field,
          base_rate_field
        );

        // clear the select box of the first row
        frm
          .get_field("items")
          .grid.grid_rows_by_docname[selected[0].name].select();
        frm.refresh();
      }
    });
  }
};

eskill_custom.form.common.convert_base_to_selected = (frm) => {
  if (frm.doc.usd_to_currency) {
    frm.set_value(
      "conversion_rate",
      roundNumber(1 / frm.doc.usd_to_currency, 9)
    );
  } else {
    frm.set_value("conversion_rate", null);
  }
};

eskill_custom.form.common.convert_selected_to_base = (frm) => {
  if (frm.doc.conversion_rate) {
    frm.doc.usd_to_currency = roundNumber(1 / frm.doc.conversion_rate, 4);
    frm.refresh_field("usd_to_currency");
  } else {
    frm.set_value("usd_to_currency", null);
  }
};

eskill_custom.form.common.stock_availability = (frm) => {
  if (frm.fields_dict.hasOwnProperty("items")) {
    frm.add_custom_button(
      __("Stock Availability"),
      () => {
        if (frm.doc.items.length) {
          frappe.call({
            method: "eskill_custom.api.stock_availability",
            args: {
              doctype: frm.doctype,
              items: frm.doc.items,
            },
          });
        }
      },
      __("View")
    );
  }
};
