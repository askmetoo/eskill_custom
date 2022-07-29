"""This is meant to be a scheduled task to correct the auction bid rate on GL Entries
in the case that there was a delay in getting the new rate."""

import frappe


def execute():
    "Main function to be run by the scheduler."

    frappe.db.sql("""
        update
            `tabGL Entry` GLE
        join
            `tabAuction Exchange Rate` AER
        on
            GLE.posting_date >= AER.date
            and AER.date = (
                select
                    max(tab1.date)
                from
                    `tabAuction Exchange Rate` tab1
                where
                    tab1.date <= GLE.posting_date
            )
        set
            GLE.auction_bid_rate = AER.exchange_rate
        where 
            GLE.auction_bid_rate <> AER.exchange_rate
            and AER.exchange_rate is not null
            and datediff(current_date(), GLE.posting_date) <= 30;
    """)
    frappe.db.commit()
