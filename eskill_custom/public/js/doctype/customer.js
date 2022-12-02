frappe.ui.form.on("Customer", {
  refresh(frm) {
    if (
      !frm.doc.__islocal &&
      frm.doc.default_currency == frappe.defaults.get_default("currency") &&
      frm.doc.approved
    ) {
      frm.add_custom_button(
        __("Secondary Account"),
        function () {
          create_secondary_account(frm);
        },
        "Create"
      );
    }
    frappe.run_serially([
      () => frm.remove_custom_button("Accounts Receivable", "View"),
      () =>
        frm.add_custom_button(
          __("Accounts Receivable"),
          function () {
            frappe.set_route(
              "query-report",
              "Accounts Receivable (Multi-Currency)",
              { customer: frm.doc.name }
            );
          },
          __("View")
        ),
      () =>
        frm.add_custom_button(
          __("Customer Statement"),
          function () {
            frappe.set_route("query-report", "Customer Statement", {
              party_type: "Customer",
              party: frm.doc.name,
            });
          },
          __("View")
        ),
    ]);

    if (frm.is_new()) {
      frm.set_df_property("approved", "hidden", 1);
    }
  },

  before_save(frm) {
    set_customer_code(frm);
  },

  approved(frm) {
    if (frm.doc.approved) {
      frm.set_value("approved_by", frappe.session.user);
    }
  },

  default_currency(frm) {
    if (frm.doc.default_currency) {
      frappe.call({
        method: "eskill_custom.api.customer_account_selector",
        args: {
          currency: frm.doc.default_currency,
        },
        callback: function (response) {
          frm.clear_table("accounts");
          if (response.message) {
            let debtors_account = frappe.model.add_child(
              frm.doc,
              "Party Account",
              "accounts"
            );
            debtors_account.company =
              frappe.defaults.get_user_default("Company");
            debtors_account.account = response.message;
          }
          frm.refresh_fields();
        },
      });
    } else {
      frm.clear_table("accounts");
      frm.refresh_field("accounts");
    }
  },
});

// creates a secondary customer account based on the given currency
function create_secondary_account(frm) {
  frappe.prompt(
    [
      {
        fieldname: "default_currency",
        fieldtype: "Link",
        get_query: function () {
          return {
            filters: [["Currency", "name", "!=", frm.doc.default_currency]],
          };
        },
        label: "Account Currency",
        options: "Currency",
        reqd: 1,
      },
    ],
    (values) => {
      frappe.call({
        method: "eskill_custom.customer.create_secondary_customer",
        args: {
          customer: frm.doc.name,
          currency: values.default_currency,
        },
        callback: (response) => {
          frappe.set_route("Form", "Customer", response.message);
        },
      });
    }
  );
}

// prompt the user to set the customer code if this is the first save
function set_customer_code(frm) {
  if (frm.is_new() && !frm.doc.__newname) {
    frappe.validated = false;
    const customer_code_prefix = frm.doc.customer_name
      .replace(/[\W\d]{1}/gm, "")
      .substring(0, 3)
      .toUpperCase();
    const customer_code_suffix = frm.doc.default_currency
      .substring(0, 2)
      .toUpperCase();

    frappe.db
      .get_list("Customer", {
        fields: ["name"],
        filters: [
          ["Customer", "name", "like", `${customer_code_prefix}%`],
          ["Customer", "default_currency", "=", frm.doc.default_currency],
        ],
      })
      .then((customers) => {
        const existing_customers = [];
        customers.forEach((customer) => {
          existing_customers.push(customer.name);
        });

        const numeric_portion = `000${existing_customers.length + 1}`;
        const default_code = `${customer_code_prefix}-${numeric_portion.substring(
          numeric_portion.length - 3
        )}-${customer_code_suffix}`;

        frappe.prompt(
          [
            {
              fieldname: "customer_code",
              fieldtype: "Data",
              label: "Customer Code",
              default: default_code,
              read_only: 1,
            },
            {
              fieldtype: "Section Break",
              label: "Address",
            },
            {
              fieldname: "address_line1",
              fieldtype: "Data",
              label: "Address Line 1",
              reqd: 1,
            },
            {
              fieldname: "address_line2",
              fieldtype: "Data",
              label: "Address Line 2",
            },
            {
              fieldname: "city",
              fieldtype: "Data",
              label: "City/Town",
              reqd: 1,
            },
            {
              fieldname: "country",
              fieldtype: "Link",
              label: "Country",
              options: "Country",
              reqd: 1,
            },
            {
              fieldtype: "Section Break",
              label: "Primary Contact",
            },
            {
              fieldname: "first_name",
              fieldtype: "Data",
              label: "First Name",
              reqd: 1,
            },
            {
              fieldname: "last_name",
              fieldtype: "Data",
              label: "Last Name",
              reqd: 1,
            },
            {
              fieldname: "email_id",
              fieldtype: "Data",
              label: "Email Address",
              options: "Email",
              reqd: 1,
            },
            {
              fieldname: "phone",
              fieldtype: "Data",
              label: "Phone Number",
              options: "Phone",
              reqd: 1,
            },
            {
              fieldname: "is_primary_phone",
              fieldtype: "Check",
              label: "Is Primary Phone",
            },
            {
              fieldname: "is_primary_mobile_no",
              fieldtype: "Check",
              label: "Is Primary Mobile",
            },
          ],
          (values) => {
            frm.doc.__newname = values.customer_code;
            frm.save().then(() => {
              frappe.call({
                method: "eskill_custom.customer.set_new_customer_info",
                args: {
                  values: values,
                },
                callback: (response) => {
                  location.reload();
                },
              });
            });
          },
          "Set Account Information"
        );
      });
  }
}
