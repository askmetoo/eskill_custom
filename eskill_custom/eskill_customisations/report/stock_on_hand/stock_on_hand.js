// Copyright (c) 2022, Eskill Trading and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Stock On Hand"] = {
    "filters": [
        {
            fieldname: "item_code",
            label:  __("Item Code"),
            fieldtype:  "Link",
            options:  "Item"
        },
        {
            fieldname: "item_name",
            label:  __("Item Name"),
            fieldtype:  "Data",
        },
		{
			fieldname: "item_group",
			label: __("Item Group"),
			fieldtype: "MultiSelectList",
			options: "Item Group",
			get_data(txt) {
				return frappe.db.get_link_options("Item Group", txt);
			}
		},
        {
            fieldname: "brand",
            label:  __("Brand"),
            fieldtype:  "Link",
            options:  "Brand"
        },
        {
            fieldname: "warehouse",
            label:  __("Warehouse"),
            fieldtype:  "Link",
            options:  "Warehouse",
            get_query: () => {
                return {
                    filters: [
                        ["Warehouse", "warehouse_type", "in", [
                            "Sales",
                            "Service"
                        ]]
                    ]
                }
            },
            default: "Stores - ET"
        },
        {
            fieldname: "warehouse_type",
            label:  __("Warehouse Type"),
            fieldtype:  "Link",
            options:  "Warehouse Type",
            get_query: () => {
                return {
                    filters: [
                        ["Warehouse Type", "name", "in", [
                            "Sales",
                            "Service"
                        ]]
                    ]
                }
            }
        },
        {
            fieldname: "items_in_stock",
            label:  __("Only Items in Stock"),
            fieldtype:  "Check"
        },
        {
            fieldname: "show_item_group",
            label:  __("Show Item Group"),
            fieldtype:  "Check"
        },
        {
            fieldname: "show_brand",
            label:  __("Show Brand"),
            fieldtype:  "Check"
        },
        {
            fieldname: "show_warehouse",
            label:  __("Show Warehouse"),
            fieldtype:  "Check"
        },
        {
            fieldname: "show_valuation_rate",
            label:  __("Show Cost Price"),
            fieldtype:  "Check"
        },
    ],
    formatter: (value, row, column, data, default_formatter) => {
        value = default_formatter(value, row, column, data);
        if (data.projected_qty < 0) {
            value = "<span style='color: red !important; font-weight: bold;'>" + value + "</span>";
        }
        return value;
    },
    name_field: "item_code"
}