frappe.pages["project-dashboard"].on_page_load = function(wrapper) {
        var page = frappe.ui.make_app_page({
                parent: wrapper,
                title: "Projects",
                single_column: true
        });
        $(frappe.render_template("project_dashboard")).appendTo(page.body).height("75vh").width("100%");

        var time = new Date().getTime();
        $(document.body).bind("mousemove keypress", function(e) {
                time = new Date().getTime();
        });

        function refresh() {
                if(new Date().getTime() - time >= 60000) 
                        window.location.reload(true);
                else 
                        setTimeout(refresh, 10000);
        }

        setTimeout(refresh, 10000);
}