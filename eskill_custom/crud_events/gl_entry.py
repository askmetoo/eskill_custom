"Methods to be run on CRUD evnts via hooks for the GL Entry DocType."

import frappe


def set_auction_bid_rate(doc, method = None):
    "Set the auction bid rate on new GL Entries."

    try:
        auction_rate = frappe.db.sql(f"""
            select
                AER.exchange_rate
            from
                `tabAuction Exchange Rate` AER
            where
                '{doc.posting_date}' >= AER.date
                and AER.date = (
                    select
                        max(tab1.date)
                    from
                        `tabAuction Exchange Rate` tab1
                    where
                        tab1.date <= '{doc.posting_date}'
                );
            """)[0][0]
    except IndexError:
        return

    doc.auction_bid_rate = auction_rate


def test(doc, method = None):
    "Test function."

    frappe.throw(f"{doc.account}\n{method}")
