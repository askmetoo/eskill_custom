# Copyright (c) 2022, Eskill Trading and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class KBArticle(Document):
    "Server-side script for the KB Article DocType."

    def on_submit(self):
        "Method that runs during the on_submit event."

        if self.corrected_article:
            old_article = frappe.get_doc("KB Article", self.corrected_article)
            if old_article.status == "Current":
                old_article.db_set("status", "Outdated", notify=True)
