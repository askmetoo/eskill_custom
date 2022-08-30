// This script is dedicated to instantiating a pop-up price lookup
// that can be called from anywhere in the ERPNext desk

frappe.provide("eskill_custom.ui");

// define size and postion of the window
const LOOKUP_WINDOW_PARAMS = `
    width = ${screen.width},
    height = 250,
    left = 0,
    top = ${screen.height - 250}
`;

class PriceLookup {
    constructor() {
        this.params = LOOKUP_WINDOW_PARAMS.replace(/\s/g, "");
    }

    open() {
        if (this.closed()) {
            this.window = window.open(origin + "/app/price-lookup", "priceLookup", this.params);
        } else {
            this.window.focus();
        }
    }

    closed() {
        if (!this.window || this.window.closed) {
            return true;
        }
        return false;
    }

    update_window(item_obj = undefined, item_field = undefined, base_rate_field = undefined) {
        // this method update the item_field in the price-lookup page
        const is_closed = this.closed();

        this.open();
        
        if (item_obj) {
            this.window.current_item = {
                item_obj: item_obj,
                item_field: item_field,
                base_rate_field: base_rate_field
            };
            const set_filters = () => {
                if (item_field) {
                    this.window.cur_page.page.price_lookup.page.item_field.set_value(item_obj[item_field]);
                    if (base_rate_field) {
                        this.window.cur_page.page.price_lookup.page.base_selling_price.set_value(item_obj[base_rate_field]);
                        this.window.cur_page.page.price_lookup.page.match_price_check.set_value(1);
                    } else {
                        this.window.cur_page.page.price_lookup.page.match_price_check.set_value(0);
                    }
                }
            };
    
            if (is_closed) {
                // if the window was not already open, add an event onload to set the item code
                this.window.addEventListener("load", () => {
                    try {
                        // for some reason some browsers have cur_page loaded up in its entirety by the time the load event is triggered
                        set_filters();
                    } catch (error) {
                        // whilst others do not, if the browser does not load cur_page in time, set a timeout of 1.5s and try again
                        setTimeout(() => {
                            set_filters();
                        }, 1500);
                    }
                }, true);
            } else {
                // otherwise immediately set the item code
                set_filters();
            }
        } else {
            this.window.current_item = undefined;
        }
    }
}

eskill_custom.ui.price_dialog = new PriceLookup();