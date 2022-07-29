"Sets the auction_bid_rate value in the GL Entry table for all historical documents."

import frappe

def execute():
    "Main function to be run by patcher."

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
            AER.exchange_rate is not null;
    """)
    frappe.db.commit()
