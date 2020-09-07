# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "chem_intercompany"
app_title = "Chem InterCompany"
app_publisher = "FinByz Tech Pvt. Ltd."
app_description = "To manage inter company transactions for chemical"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "info@finbyz.com"
app_license = "GPL 3.0"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/chem_intercompany/css/chem_intercompany.css"
# app_include_js = "/assets/chem_intercompany/js/chem_intercompany.js"

# include js, css files in header of web template
# web_include_css = "/assets/chem_intercompany/css/chem_intercompany.css"
# web_include_js = "/assets/chem_intercompany/js/chem_intercompany.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

doctype_js = {
	"Delivery Note": "public/js/doctype_js/delivery_note.js",
	"Purchase Receipt": "public/js/doctype_js/purchase_receipt.js",
	"Sales Invoice": "public/js/doctype_js/sales_invoice.js",
	"Purchase Invoice": "public/js/doctype_js/purchase_invoice.js",	
	"Purchase Order": "public/js/doctype_js/purchase_order.js",	
	"Sales Order": "public/js/doctype_js/sales_order.js",
	"Stock Entry": "public/js/doctype_js/stock_entry.js",
	"Company": "public/js/doctype_js/company.js",
}

doc_events = {
	"Purchase Order":{
		"on_submit": "chem_intercompany.chem_intercompany.doc_events.purchase_order.on_submit",
		"on_cancel": "chem_intercompany.chem_intercompany.doc_events.purchase_order.on_cancel",
		"on_trash": "chem_intercompany.chem_intercompany.doc_events.purchase_order.on_trash",

	},
	"Company": {
		"on_update": "chem_intercompany.chem_intercompany.doc_events.company.on_update",
	},
	"Delivery Note": {
		"on_submit": "chem_intercompany.chem_intercompany.doc_events.delivery_note.on_submit",
		"on_cancel": "chem_intercompany.chem_intercompany.doc_events.delivery_note.on_cancel",
		"on_trash": "chem_intercompany.chem_intercompany.doc_events.delivery_note.on_trash",
	},
	"Sales Invoice": {
		"on_submit": "chem_intercompany.chem_intercompany.doc_events.sales_invoice.on_submit",
		"on_cancel": "chem_intercompany.chem_intercompany.doc_events.sales_invoice.on_cancel",
		"on_trash": "chem_intercompany.chem_intercompany.doc_events.sales_invoice.on_trash",
	},
	"Stock Entry":{
		"on_submit": "chem_intercompany.chem_intercompany.doc_events.stock_entry.on_submit",
		"on_cancel": "chem_intercompany.chem_intercompany.doc_events.stock_entry.on_cancel",
	}
}
# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "chem_intercompany.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "chem_intercompany.install.before_install"
# after_install = "chem_intercompany.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "chem_intercompany.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"chem_intercompany.tasks.all"
# 	],
# 	"daily": [
# 		"chem_intercompany.tasks.daily"
# 	],
# 	"hourly": [
# 		"chem_intercompany.tasks.hourly"
# 	],
# 	"weekly": [
# 		"chem_intercompany.tasks.weekly"
# 	]
# 	"monthly": [
# 		"chem_intercompany.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "chem_intercompany.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "chem_intercompany.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "chem_intercompany.task.get_dashboard_data"
# }

