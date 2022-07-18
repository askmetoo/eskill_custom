"""This is meant to be a scheduled task to correct the auction bid rate in DocTypes that have it
in the case that there was a delay in getting the new rate."""

import frappe

# DocTypes with the standard auction_bid_rate float field in the standard form
DOCTYPES = {
    'Quotation': "transaction_date",
    'Sales Order': "transaction_date",
    'Delivery Note': "posting_date",
    'Sales Invoice': "posting_date",
    'Purchase Receipt': "posting_date",
    'Purchase Invoice': "posting_date",
    'Landed Cost Voucher': "posting_date",
    'Journal Entry': "posting_date",
    'Payment Entry': "posting_date",
    'Stock Entry': "posting_date",
    'Stock Reconciliation': "posting_date"
}

def execute():
    "Main function to be run by the scheduler."

    for doctype, date_field in DOCTYPES.items():
        correct_doctype(doctype, date_field)
        print(f"{doctype} auction rate corrected.")


def correct_doctype(doctype: str, date_field: str):
    """Corrects the auction_bid_rate field for all records in the given table
    that have been posted in the past month."""

    frappe.db.sql(f"""
        update
            `tab{doctype}` doc
        join
            `tabAuction Exchange Rate` AER
        on
            doc.{date_field} >= AER.date
            and AER.date = (
                select
                    max(tab1.date)
                from
                    `tabAuction Exchange Rate` tab1
                where
                    tab1.date <= doc.{date_field}
            )
        set
            doc.auction_bid_rate = AER.exchange_rate
        where 
            doc.auction_bid_rate <> AER.exchange_rate
            and datediff(current_date(), doc.{date_field}) <= 30;
    """, debug=True)
    frappe.db.commit()
