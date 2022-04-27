// Copyright (c) 2022, Eskill Trading and contributors
// For license information, please see license.txt

frappe.ui.form.on('KB Article', {
    refresh(frm) {
        set_filters(frm);
        correct_article(frm);
    },

    before_save(frm) {
        if (frm.doc.kba_type == "Product") {
            frm.set_value("title", frm.doc.item + ": " + frm.doc.subject);
        } else if (frm.doc.kba_type == "Process") {
            frm.set_value("title", frm.doc.article_doctype + ": " + frm.doc.subject);
        }
        frm.refresh();
    },

    invalidated(frm) {
        console.log(frm.doc)
        frm.set_value("status", "Invalidated");
    },

    kba_type(frm) {
        frm.set_value("article_doctype", undefined);
        frm.set_value("item", undefined);
        frm.set_value("subject", undefined);
    },
});


function correct_article(frm) {
    if (frm.doc.docstatus == 1) {
        frm.add_custom_button(__("Update Information"), () => {
            var new_article = frappe.model.copy_doc(frm.doc);
            new_article.corrected_article = frm.doc.name;
            if (new_article.invalidated) {
                new_article.invalidated = 0;
            }
            new_article.status = "Current";
            frappe.set_route("Form", "KB Article", new_article.name);
        });
    }
}


function set_filters(frm) {
    frm.fields_dict.subject.get_query = () => {
        return {
            filters: [
                ["KB Subject", "kba_type", "=", frm.doc.kba_type]
            ]
        };
    };
    frm.fields_dict.article_doctype.get_query = () => {
        return {
            filters: [
                ["DocType", "istable", "=", 0]
            ]
        };
    };
}
