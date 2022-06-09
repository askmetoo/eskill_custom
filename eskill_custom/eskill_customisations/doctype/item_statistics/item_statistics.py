# Copyright (c) 2022, Eskill Trading and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from numpy import average


class ItemStatistics(Document):
    "Methods for Item Statistics single DocType"

    @frappe.whitelist()
    def get_statistics(self):
        "Populate the statistics tables."

        period = frappe.db.sql(
            f"""select
                timestampdiff(
                    {self.periodicity[:-1]}, '{self.from_date}', '{self.to_date}'
                ) + 1;"""
        )[0][0]

        # conversion variable used to convert days into the given unit of date
        if self.periodicity == "Months":
            period_conversion = 30
        elif self.periodicity == "Years":
            period_conversion = 365
        else:
            period_conversion = 1

        self.get_sales_data(period)
        self.get_purchase_data(period_conversion)
        self.get_service_data(period)

        return self.periodicity[:-1]


    def get_purchase_data(self, period_conversion: int):
        "Get purchase data and populate relevant fields."

        self.qty_purchased = 0
        self.cost_increase_per_period = 0

        data = frappe.db.sql(f"""
            select
                PR.posting_date date,
                PRI.parent purchase_receipt,
                PRI.stock_qty qty_received,
                PRI.base_rate unit_cost,
                PRI.base_amount total_value
            from
                `tabPurchase Receipt Item` PRI
            join
                `tabPurchase Receipt` PR on PRI.parent = PR.name
            where
                PRI.docstatus = 1
                and PRI.item_code = "{self.item_code}"
                and PR.posting_date >= "{self.from_date}"
                and PR.posting_date <= "{self.to_date}"
            order by
                date;
        """, as_dict=True)

        for row in data:
            self.append("item_statistics_purchase_receipts", row)
            self.qty_purchased += row['qty_received']

        if len(self.item_statistics_purchase_receipts) > 1:
            costs = tuple({
                'date': row.date,
                'unit_cost': row.unit_cost
            } for row in self.item_statistics_purchase_receipts)
            cost_changes = [] # list of cost changes

            for i in range(1, len(costs)):
                date_difference = (costs[i]['date'] - costs[i - 1]['date']).days / period_conversion
                if date_difference > 0:
                    change = (costs[i]['unit_cost'] - costs[i - 1]['unit_cost']) / date_difference
                    cost_changes.append(change)

            if len(cost_changes) > 0:
                self.cost_increase_per_period = average(cost_changes)


    def get_sales_data(self, period: int):
        "Get sales data and populate relevant fields."

        self.qty_sold = 0
        self.avg_qty_sold = 0


        data = frappe.db.sql(f"""
            select
                tab1.main_account customer,
                C.customer_name,
                sum(tab1.qty) qty_sold,
                sum(tab1.qty) / {period} avg_qty_sold,
                sum(tab1.total) / sum(tab1.qty) avg_price,
                sum(tab1.total) total_value
            from
                (select
                    C.name customer,
                    (case
                        when C.main_account is not null then C.main_account else C.name
                    end) main_account,
                    sum(SII.qty) qty,
                    sum(SII.base_net_amount) total
                from
                    `tabSales Invoice Item` SII
                join
                    `tabSales Invoice` SI on SII.parent = SI.name
                join
                    tabCustomer C on SI.customer = C.name
                where
                    SII.item_code = "{self.item_code}"
                    and SII.docstatus = 1
                    and SI.posting_date >= "{self.from_date}"
                    and SI.posting_date <= "{self.to_date}"
                group by
                    C.name) tab1
            join
                tabCustomer C on tab1.main_account = C.name
            group by
                tab1.main_account
            order by
                qty_sold desc, avg_price desc, customer;
        """, as_dict=True)

        for row in data:
            self.append("item_statistics_sold_to_customers", row)
            self.qty_sold += row['qty_sold']

        self.avg_qty_sold = self.qty_sold / period


    def get_service_data(self, period: int):
        "Get service data and populate relevant fields."

        self.service_order_qty = 0
        self.frequent_serial_number = None
        self.max_services = 0
        self.number_of_warranties = 0
        self.avg_service_length = 0

        data = frappe.db.sql(f"""
            select
                SO.start_date date,
                SO.closing_date,
                SD.parent service_order,
                SO.job_type,
                SD.serial_number,
                SO.assigned_technician
            from
                `tabService Device` SD
            join
                `tabService Order` SO on SD.parent = SO.name
            where
                SD.model = "{self.item_code}"
                and SD.docstatus = 1
                and SO.start_date >= "{self.from_date}"
                and SO.start_date <= "{self.to_date}"
            order by
                date, service_order, serial_number
        """, as_dict=True)

        for row in data:
            self.append("item_statistics_service_orders", row)
            self.service_order_qty += 1

        if len(self.item_statistics_service_orders) > 0:
            most_frequent_device = {
                'services': 0,
                'serial_number': ""
            }
            serials = set()
            serial_visits = {}

            service_order_durations = []

            for row in self.item_statistics_service_orders:
                if row.serial_number in serials:
                    serial_visits[row.serial_number] += 1
                else:
                    serial_visits[row.serial_number] = 1
                    serials.add(row.serial_number)
                if row.closing_date:
                    service_order_durations.append((row.closing_date - row.date).days)

            for serial, services in serial_visits.items():
                if services > most_frequent_device['services']:
                    most_frequent_device['serial_number'] = serial
                    most_frequent_device['services'] = services

            warranties = [
                row.service_order
                for row in self.item_statistics_service_orders
                if row.job_type == "Warranty"
            ]

            if most_frequent_device['services'] > 1:
                self.frequent_serial_number = most_frequent_device['serial_number']
            self.max_services = most_frequent_device['services']
            self.number_of_warranties = len(warranties)

            self.avg_services = self.service_order_qty / period
            self.avg_service_length = (
                average(service_order_durations)
                if len(service_order_durations) > 0
                else 0
            )
