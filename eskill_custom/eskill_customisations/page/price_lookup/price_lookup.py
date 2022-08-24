"Server side methods specifically for the Price Lookup page."

import frappe

@frappe.whitelist()
def get_gp_rate(item_code):
    "Returns the minimum gp rate of the given item code."

    try:
        return (frappe.db.sql(f"""
            select
                IG.minimum_gp
            from
                tabItem I
            join
                `tabItem Group` IG on I.item_group = IG.name
            where
                I.name = '{item_code}';
        """)[0][0] / 100) + 1
    except IndexError:
        return 1
