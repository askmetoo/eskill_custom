# Currency Preface

All of the financial reports have been written with a second selectable
currency in mind, however it has been disabled due to the changes needed in
order to make reporting the Zimbabwe Dollar accurate (there are two exchange
rates in play for any given document due to the auction system). To restore the
intended functionality, you simply need to:

1. Unhide the report currency filter
    - Remove/change the default
2. Replace the queries that pull the rates from the documents with ones that
query the rate table
    - Select the most recent rate as of the ledger entry posting date
