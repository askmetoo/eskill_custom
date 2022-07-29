frappe.require([
    '/assets/eskill_custom/js/common.js'
]);

frappe.ui.form.on('Payment Entry', {
    refresh(frm) {
        name_series(frm);
        party_filter(frm);
    },

    on_submit(frm) {
        update_payment_receipt(frm);
    },

    after_cancel(frm) {
        update_payment_receipt(frm);
    },
    
    payment_type(frm) {
        name_series(frm);
    },

    source_exchange_rate(frm) {
        convert_selected_to_base(frm, true);
    },

    source_usd_to_currency(frm) {
        convert_base_to_selected(frm, true);
    },

    target_exchange_rate(frm) {
        convert_selected_to_base(frm, false);
    },

    target_usd_to_currency(frm) {
        convert_base_to_selected(frm, false);
    },
});

function convert_base_to_selected(frm, source) {
    if (source) {
        if (frm.doc.source_usd_to_currency) {
            frm.set_value('source_exchange_rate', roundNumber(1 / frm.doc.source_usd_to_currency, 9));
        } else {
            frm.set_value('source_exchange_rate', null);
        }
    } else {
        if (frm.doc.target_usd_to_currency) {
            frm.set_value('target_exchange_rate', roundNumber(1 / frm.doc.target_usd_to_currency, 9));
        } else {
            frm.set_value('target_exchange_rate', null);
        }
    }
}

function convert_selected_to_base(frm, source) {
    if (source) {
        if (frm.doc.source_exchange_rate) {
            frm.doc.source_usd_to_currency = roundNumber(1 / frm.doc.source_exchange_rate, 4);
            frm.refresh_field('source_usd_to_currency');
        } else {
            frm.set_value('source_usd_to_currency', null);
        }
    } else {
        if (frm.doc.target_exchange_rate) {
            frm.doc.target_usd_to_currency = roundNumber(1 / frm.doc.target_exchange_rate, 4);
            frm.refresh_field('target_usd_to_currency');
        } else {
            frm.set_value('target_usd_to_currency', null);
        }
    }
}

function name_series(frm) {
    if (frm.doc.payment_type == "Receive") {
        frm.set_value('naming_series', "REC.########");
        frm.set_df_property('naming_series', 'read_only', 1);
    } else if (frm.doc.payment_type == "Pay") {
        frm.set_value('naming_series', "PYE.########");
        frm.set_df_property('naming_series', 'read_only', 1);
    } else {
        frm.set_value('naming_series', "INTER-CO-.########");
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

function update_payment_receipt(frm) {
    if (frm.doc.payment_receipt) {
        frappe.call({
            method: "eskill_custom.payment_entry.update_payment_receipt",
            args: {
                payment_entry: frm.doc.name
            }
        });
    }
}