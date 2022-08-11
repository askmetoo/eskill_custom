"This module handles the generation of QR codes."

import lxml.etree as ET
import qrcode
import qrcode.image.svg

import frappe


@frappe.whitelist()
def generate_serial_history_qr(serial_number: str, site: str):
    "Generate a QR Code for a given Serial No DocType."

    url = (
        f"{site}/api/method/frappe.utils.print_format.download_pdf?doctype=Serial%20No"
        f"&name={serial_number}&format=Eskill%20Serial%20Number%20History"
    )

    factory = qrcode.image.svg.SvgImage

    code_image = qrcode.make(url, image_factory=factory)

    return ET.tostring(code_image.get_image(), encoding="unicode")
