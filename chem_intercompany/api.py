import frappe
from frappe import _
import json
from datetime import date
import datetime

from frappe.desk.notifications import get_filters_for
from frappe.model.mapper import get_mapped_doc

from frappe.utils import getdate

def get_inter_company_details(doc, doctype):
	party = None
	company = None

	if doctype in ["Sales Invoice", "Delivery Note", "Sales Order"]:
		party = frappe.db.get_value("Supplier", {"disabled": 0, "is_internal_supplier": 1, "represents_company": doc.company}, "name")
		company = frappe.get_cached_value("Customer", doc.customer, "represents_company")
	elif doctype in ["Purchase Order", "Purchase Receipt", "Purchase Invoice"]:
		party = frappe.db.get_value("Customer", {"disabled": 0, "is_internal_customer": 1, "represents_company": doc.company}, "name")
		company = frappe.get_cached_value("Supplier", doc.supplier, "represents_company")

	return {
		"party": party,
		"company": company
	}
    
def validate_inter_company_transaction(doc, doctype):
	price_list = None
	details = get_inter_company_details(doc, doctype)

	if doctype in ["Sales Invoice", "Delivery Note", "Sales Order"]:
		price_list = doc.selling_price_list
	elif doctype in ["Purchase Order", "Purchase Receipt", "Purchase Invoice"]:
		price_list = doc.buying_price_list
	
	if price_list:
		valid_price_list = frappe.db.get_value("Price List", {"name": price_list, "buying": 1, "selling": 1})
	else:
		frappe.throw(_("Selected Price List should have buying and selling fields checked."))
	
	if not valid_price_list:
		frappe.throw(_("Selected Price List should have buying and selling fields checked."))
	
	party = details.get("party")
	if not party:
		partytype = "Supplier" if doctype in ["Sales Invoice", "Delivery Note", "Sales Order"] else "Customer"
		frappe.throw(_("No {0} found for Inter Company Transactions.").format(partytype))
	
	company = details.get("company")
	if company:
		default_currency = frappe.get_cached_value('Company', company, "default_currency")
		if default_currency != doc.currency:
			frappe.throw(_("Company currencies of both the companies should match for Inter Company Transactions."))
	else:
		frappe.throw(_("Company currencies of both the companies should match for Inter Company Transactions."))
	
	return

# whitelist functions
@frappe.whitelist()
def check_counter_series(name, company_series = None, date = None):
	
	if not date:
		date = datetime.date.today()
	
	
	fiscal = get_fiscal(date)
	
	name = naming_series_name(name, fiscal, company_series)
	
	check = frappe.db.get_value('Series', name, 'current', order_by="name")
	
	if check == 0:
		return 1
	elif check == None:
		frappe.db.sql(f"insert into tabSeries (name, current) values ('{name}', 0)")
		return 1
	else:
		return int(frappe.db.get_value('Series', name, 'current', order_by="name")) + 1
