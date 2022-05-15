"Generic methods that can be used in various Reports."


import frappe


def get_descendants(doctype: str, name: str, parent_field: str = "parent") -> set:
    "Returns a set of all descendants of a given Document."

    descendants = set()
    meta = frappe.get_doc("DocType", doctype)
    if not meta.is_tree:
        return descendants

    child_docs = frappe.get_all(
        doctype=doctype,
        filters={
            parent_field: name
        },
        fields=[
            "name",
            "is_group"
        ]
    )
    for child in child_docs:
        descendants.add(child.name)
        if child.is_group:
            for sub_child in get_descendants(doctype, child.name, parent_field):
                descendants.add(sub_child)

    return descendants
