// This script is dedicated to instantiating a pop-up price lookup
// that can be called from anywhere in the ERPNext desk

frappe.provide("eskill_custom.ui");

// params are pointless right now, need to figure out why they're not working
const LOOKUP_WINDOW_PARAMS = `
    width = ${screen.width},
    height = 300,
    left = 0,
    top = ${screen.height - 300}
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
}

eskill_custom.ui.price_dialog = new PriceLookup();