import frappe
from frappe import _
import json
from datetime import date
import datetime
from frappe.utils import getdate
from frappe.desk.notifications import get_filters_for
from frappe.model.mapper import get_mapped_doc
from frappe.desk.reportview import get_match_cond, get_filters_cond
from erpnext.stock.stock_ledger import get_previous_sle

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

@frappe.whitelist()
def get_challan_no(doctype, txt, searchfield, start, page_len, filters):
	cond = ""
	previous_sle = get_previous_sle({
		"item_code": filters.get("item_code"),
		"warehouse": filters.get("warehouse"),
		"posting_date": filters.get("posting_date"),
		"posting_time": filters.get("posting_time")
	})

	meta = frappe.get_meta("Batch")
	searchfield = meta.get_search_fields()

	searchfields = " or ".join(["batch." + field + " like %(txt)s" for field in searchfield])
	searchfields += " or sle.voucher_no = '{previous_sle}')".format(previous_sle=previous_sle.voucher_no)
	# searchfield_previous_sle = " or ".join(["""sle.voucher_no = '{previous_sle}'""".format(previous_sle=previous_sle.voucher_no)])
	if filters.get("posting_date"):
		cond = "and (batch.expiry_date is null or batch.expiry_date >= %(posting_date)s)"
	batch_nos = None

	args = {
		'item_code': filters.get("item_code"),
		'warehouse': filters.get("warehouse"),
		'posting_date': filters.get('posting_date'),
		'txt': "%{0}%".format(txt),
		"start": start,
		"page_len": page_len
	}

	if args.get('warehouse'):

		batch_nos = frappe.db.sql("""select sle.batch_no, sle.voucher_no, batch.lot_no, batch.concentration,
		CASE
			WHEN i.maintain_as_is_stock=1 THEN round(sum(sle.actual_qty*batch.concentration)/100,2) ELSE round(sum(sle.actual_qty),2)
		END, 
		sle.stock_uom
				from `tabStock Ledger Entry` sle
					INNER JOIN `tabBatch` batch on sle.batch_no = batch.name
					JOIN `tabItem` as i on sle.item_code = i.name
				where
					sle.item_code = %(item_code)s
					and sle.warehouse = %(warehouse)s
					and batch.docstatus < 2
					and (sle.batch_no like %(txt)s or {searchfields}
					{0}
					{match_conditions}
				group by batch_no having sum(sle.actual_qty) > 0
				order by batch.expiry_date, sle.batch_no desc
				limit %(start)s, %(page_len)s""".format(cond, match_conditions=get_match_cond(doctype), searchfields=searchfields), args)

	if batch_nos:
		return batch_nos
	else:
		return frappe.db.sql("""select name, lot_no, concentration, expiry_date from `tabBatch` batch
			where item = %(item_code)s
			and name like %(txt)s
			and docstatus < 2
			{0}
			{match_conditions}
			order by expiry_date, name desc
			limit %(start)s, %(page_len)s""".format(cond, match_conditions=get_match_cond(doctype)), args)
