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

    update_window(item_code) {
        // this method update the item_field in the price-lookup page
        const is_closed = this.closed();

        this.open();
        
        if (is_closed) {
            // if the window was not already open, add an event onload to set the item code
            this.window.addEventListener("load", () => {
                try {
                    // for some reason some browsers have cur_page loaded up in its entirety by the time the load event is triggered
                    this.window.cur_page.page.price_lookup.page.item_field.set_value(item_code);
                } catch (error) {
                    // whilst others do not, if the browser does not load cur_page in time, set a timeout of 1.5s and try again
                    setTimeout(() => {
                        this.window.cur_page.page.price_lookup.page.item_field.set_value(item_code);
                    }, 1500);
                }
            }, true);
        } else {
            // otherwise immediately set the item code
            this.window.cur_page.page.price_lookup.page.item_field.set_value(item_code);
        }
    }
}

eskill_custom.ui.price_dialog = new PriceLookup();