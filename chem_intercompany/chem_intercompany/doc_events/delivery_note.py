# Copyright (c) 2020, Finbyz Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.contacts.doctype.address.address import get_company_address
from frappe.utils import get_url_to_form
from frappe.model.utils import get_fetch_values

# from engineering.api import update_discounted_amount

# def before_validate(self, method):
# 	update_discounted_amount(self)

def on_submit(self, method):
	create_purchase_receipt(self)

def create_purchase_receipt(self):
	def get_purchase_receipt_entry(source_name, target_doc=None, ignore_permissions= True):
		def set_missing_value(source, target):
			target.company = source.customer
			target.supplier = source.company

			target_company_abbr = frappe.db.get_value("Company", target.company, "abbr")
			source_company_abbr = frappe.db.get_value("Company", source.company, "abbr")

			if source.taxes_and_charges:
				target_taxes_and_charges = source.taxes_and_charges.replace(source_company_abbr, target_company_abbr)
				if frappe.db.exists("Sales Taxes and Charges Template", target_taxes_and_charges):
					target.taxes_and_charges = target_taxes_and_charges

			if self.amended_from:
				name = frappe.db.get_value("Purchase Receipt", {'dn_ref': self.amended_from}, "name")
				target.amended_from = name
			
			target.set_posting_time = 1

			target.run_method("set_missing_values")
			target.run_method("calculate_taxes_and_charges")

		def update_items(source_doc, target_doc, source_parent):
			source_company_abbr = frappe.db.get_value("Company", source_parent.company, "abbr")
			target_company_abbr = frappe.db.get_value("Company", source_parent.customer, "abbr")

			if source_doc.warehouse:
				target_doc.warehouse = source_doc.warehouse.replace(source_company_abbr, target_company_abbr)

		def update_taxes(source_doc, target_doc, source_parent):
			source_company_abbr = frappe.db.get_value("Company", source_parent.company, "abbr")
			target_company_abbr = frappe.db.get_value("Company", source_parent.customer, "abbr")

			if source_doc.account_head:
				target_doc.account_head = source_doc.account_head.replace(source_company_abbr, target_company_abbr)

			if source_doc.cost_center:
				target_doc.cost_center = source_doc.cost_center.replace(source_company_abbr, target_company_abbr)

		fields = {
			"Delivery Note": {
				"doctype": "Purchase Receipt",
				"field_map": {
					"name": "supplier_delivery_note",
					"selling_price_list": "buying_price_list",
					"posting_date": "posting_date",
					"posting_time": "posting_time",
					"ignore_pricing_rule": "ignore_pricing_rule"
				},
				"field_no_map": [
					"taxes_and_charges",
					"series_value",
				]
			},
			"Delivery Note Item": {
				"doctype": "Purchase Receipt Item",
				"field_map": {
					"purchase_order_item": "purchase_order_item",
					"serial_no": "serial_no",
					"batch_no": "batch_no",
				},
				"field_no_map": [
					"warehouse",
					"cost_center",
					"expense_account",
					"income_account",
				],
				"postprocess": update_items,
			},
			"Sales Taxes and Charges": {
				"doctype": "Purchase Taxes and Charges",
				"postprocess": update_taxes,
			}
		}

		doc = get_mapped_doc(
			"Delivery Note",
			source_name,
			fields,
			target_doc,
			set_missing_value,
			ignore_permissions=ignore_permissions
		)

		return doc

	check_inter_company_transaction = None
	if frappe.db.exists("Company", self.customer):
		check_inter_company_transaction = frappe.get_value("Company", self.customer, "allow_inter_company_transaction")
	
	if check_inter_company_transaction:
		company = frappe.get_doc("Company", self.customer)
		inter_company_list = [item.company for item in company.allowed_to_transact_with]

		if self.company in inter_company_list:
			pr = get_purchase_receipt_entry(self.name)
			pr.save(ignore_permissions = True)

			for index, item in enumerate(self.items):
				price_list = self.selling_price_list
				if price_list:
					valid_price_list = frappe.db.get_value("Price List", {"name": price_list, "buying": 1, "selling": 1})
				else:
					frappe.throw(_("Selected Price List should have buying and selling fields checked."))

				if not valid_price_list:
					frappe.throw(_("Selected Price List should have buying and selling fields checked."))

				against_sales_order = self.items[index].against_sales_order

				purchase_order = None
				if frappe.db.exists("Sales Order", against_sales_order):
					purchase_order = frappe.db.get_value("Sales Order", against_sales_order, 'inter_company_order_reference')

				if purchase_order:
					pr.items[index].schedule_date = frappe.db.get_value("Purchase Order", purchase_order, 'schedule_date')
					pr.items[index].purchase_order = purchase_order
					frappe.db.set_value("Delivery Note Item", self.items[index].name, 'pr_detail', pr.items[index].name)
			
			pr.save(ignore_permissions = True)

			self.db_set('inter_company_receipt_reference', pr.name)
			self.db_set('pr_ref', pr.name)

			pr.db_set('inter_company_delivery_reference', self.name)
			pr.db_set('supplier_delivery_note', self.name)
			pr.db_set('dn_ref', self.name)

			pr.submit()

			url = get_url_to_form("Purchase Receipt", pr.name)
			frappe.msgprint(_("Purchase Receipt <b><a href='{url}'>{name}</a></b> has been created successfully!".format(url=url, name=frappe.bold(pr.name))), title="Purchase Receipt Created", indicator="green")


def get_invoiced_qty_map(delivery_note):
	"""returns a map: {dn_detail: invoiced_qty}"""

	invoiced_qty_map = {}

	for dn_detail, qty in frappe.db.sql("""select dn_detail, qty from `tabSales Invoice Item`
		where delivery_note=%s and docstatus=1""", delivery_note):
			if not invoiced_qty_map.get(dn_detail):
				invoiced_qty_map[dn_detail] = 0
			invoiced_qty_map[dn_detail] += qty

	return invoiced_qty_map

def get_returned_qty_map(delivery_note):
	"""returns a map: {so_detail: returned_qty}"""
	
	returned_qty_map = frappe._dict(frappe.db.sql("""select dn_item.item_code, sum(abs(dn_item.qty)) as qty
		from `tabDelivery Note Item` dn_item, `tabDelivery Note` dn
		where dn.name = dn_item.parent
			and dn.docstatus = 1
			and dn.is_return = 1
			and dn.return_against = %s
		group by dn_item.item_code
	""", delivery_note))

	return returned_qty_map

# All Whitelisted Method:

@frappe.whitelist()
def submit_purchase_receipt(pr_number):
	pr = frappe.get_doc("Purchase Receipt", pr_number)
	pr.flags.ignore_permissions = True
	pr.submit()
	frappe.db.commit()

	url = get_url_to_form("Purchase Receipt", pr.name)
	msg = "Purchase Receipt <b><a href='{url}'>{name}</a></b> has been created successfully!".format(url=url, name=frappe.bold(pr.name))
	frappe.msgprint(_(msg), title="Purchase Receipt Created", indicator="green")

