"Print format methods for sales documents."

import frappe


def company_tax_numbers(doc):
    "Fetch the correct company tax numbers to display based on company and currency."

    output_string = """
        <p>VAT Number: {tax_id}</p>
        <p>BP Number: {bp_number}</p>
    """

    company = frappe.get_doc("Company", doc.company)

    tax_numbers = {
        "tax_id": company.tax_id,
        "bp_number": company.bp_number,
    }

    company_tax_number_filter = {
        "parent": company.name,
        "currency": doc.currency,
    }

    if doc.currency != company.default_currency and frappe.db.exists(
        "Company Tax Number",
        company_tax_number_filter,
    ):
        currency_tax_numbers = frappe.get_doc(
            "Company Tax Number",
            company_tax_number_filter,
        )

        tax_numbers["tax_id"] = currency_tax_numbers.tax_id or tax_numbers["tax_id"]
        tax_numbers["bp_number"] = (
            currency_tax_numbers.bp_number or tax_numbers["bp_number"]
        )

    return output_string.format(
        tax_id=tax_numbers["tax_id"], bp_number=tax_numbers["bp_number"]
    )
