frappe.require([
    '/assets/eskill_custom/js/common.js'
]);

frappe.ui.form.on('Payment Entry', {
    refresh(frm) {
        name_series(frm);
        party_filter(frm);
    },
    
    before_save(frm) {
        get_bid_rate(frm, frm.doc.posting_date);
    },
    
    payment_type: function(frm) {
        name_series(frm);
    }
});

function name_series(frm) {
    if (frm.doc.payment_type == "Receive") {
        frm.set_value('naming_series', "REC.########");
        frm.set_df_property('naming_series', 'read_only', 1);
    } else if (frm.doc.payment_type == "Pay") {
        frm.set_value('naming_series', "PYE.########");
        frm.set_df_property('naming_series', 'read_only', 1);
    }
}

function party_filter(frm) {
    frm.fields_dict.party_type.get_query = function() {
        return {
            filters: [
                ["DocType", "name", "in", ["Customer", "Supplier", "Employee", "Shareholder"]],
            ],
        };
    };
}