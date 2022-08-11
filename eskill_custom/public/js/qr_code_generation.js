// Generate a QR code for the Serial Number History Print Format and provide popout asking for confirmation for printing it
function generate_serial_history_qr(serial_number) {
    frappe.call({
        method: "eskill_custom.utils.qr_code_generation.generate_serial_qr",
        args: {
            serial_number: serial_number,
            site: window.origin
        },
        callback(response) {
            let img = response.message;

            frappe.confirm("Print the following QR Code?<br>" + img,
            () => {
                let print_doc = window.open("", "");
                print_doc.document.write("<html><body>" + img + "</body></html>");
                print_doc.document.close();
                print_doc.print();
            });
        }
    });
}
