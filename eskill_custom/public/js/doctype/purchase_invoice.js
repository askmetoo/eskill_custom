frappe.ui.form.on("Purchase Invoice", {
  refresh(frm) {
    original_po_filter(frm);
  },

  conversion_rate(frm) {
    eskill_custom.form.common.convert_selected_to_base(frm);
  },

  usd_to_currency(frm) {
    eskill_custom.form.common.convert_base_to_selected(frm);
  },
});

// sets the filters on the `original_purchase_order` field
function original_po_filter(frm) {
  frm.fields_dict.original_purchase_order.get_query = function () {
    return {
      filters: [
        ["Purchase Order", "docstatus", "=", 1],
        ["Purchase Order", "supplier", "!=", frm.doc.supplier],
      ],
    };
  };
}
