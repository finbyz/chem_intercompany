import frappe
from frappe import _
from frappe.utils import flt
from datetime import timedelta

def on_submit(self,method):
	create_stock_entry(self)

def on_cancel(self,method):
	cancel_stock_entry(self)

def on_trash(self,method):
	for row in self.items:
		if row.batch_no:
			doc = frappe.get_doc("Batch",row.batch_no)
			doc.db_set('reference_name', None)
		#	frappe.db.set_value("Batch",row.batch_no,'reference_name',None)

def create_stock_entry(self):
	if self.send_to_party:
		source_abbr = frappe.db.get_value("Company", self.company,'abbr')
		job_work_out_warehouse = frappe.db.get_value("Company", self.company,'job_work_out_warehouse')
		target_abbr = frappe.db.get_value("Company", self.party,'abbr')
		expense_account = frappe.db.get_value('Company',self.company,'job_work_difference_account')
		
		# if not self.set_warehouse:
		# 	frappe.throw(_("Please set Warehouse"))

		if not job_work_out_warehouse:
			frappe.throw(_("Please set Job work out warehouse in company <b>{0}</b>").format(self.company))

		if not expense_account:
			frappe.throw(_("Please set Job work difference account in company <b>{0}</b>").format(self.company))

		if not self.jobwork_series_value:
			frappe.throw(_("Please select Job Work Series Value"))

		se = frappe.new_doc("Stock Entry")
		se.series_value = int(self.jobwork_series_value)
		if frappe.db.get_value("Company",self.company,'company_code') == frappe.db.get_value("Company",self.party,'company_code'):
			se.naming_series = "STE.company_series./.fiscal./UII/.###"
		else:
			se.naming_series = "STE.company_series./.fiscal./AII/.###"
		se.stock_entry_type = "Send to Jobwork"
		se.purpose = "Material Transfer"
		se.set_posting_time = 1
		se.reference_doctype = self.doctype
		se.reference_docname = self.name
		se.send_to_party = 1
		se.party_type = self.party_type
		se.party = self.party
		se.posting_date = self.posting_date
		se.posting_time = self.posting_time + timedelta(minutes=1)
		se.company = self.company
		se.from_warehouse = self.set_warehouse
		se.to_warehouse = job_work_out_warehouse
		se.vehicle_no = self.lr_no
		se.e_way_bill_no = self.eway_bill_no
		se.chemical_process = self.chemical_process
		se.shipping_address_name = self.shipping_address
		se.customer_gstin = self.company_gstin
		se.place_of_supply = self.place_of_supply
		se.shipping_address = self.shipping_address_display
		se.purchase_receipt_number = self.name
		se.letter_head = frappe.db.get_value("Company",self.company,'default_letter_head')
		se.weighing_slip = self.weighing_slip
		for row in self.items:
			if not row.warehouse:
				frappe.throw(_("Please set Warehouse for item {}".format(row.item_code)))
			se.append("items",{
				'item_code': row.item_code,
				's_warehouse': row.warehouse,
				't_warehouse': job_work_out_warehouse,
				'packaging_material': row.packaging_material,
				'batch_no': row.batch_no,
				'packing_size': row.packing_size,
				'no_of_packages': row.no_of_packages,
				'concentration': row.concentration,
				'lot_no': row.lot_no,
				"batch_yield": row.batch_yield,
				'received_qty':row.received_qty,
				'qty': row.qty,
				'quantity':row.quantity,
				'short_quantity':row.short_quantity,
				'amount_difference':row.amount_difference,
				'basic_rate':row.rate,
				'amount':row.amount,
				'price':row.price,
				'expense_account': expense_account,
				'cost_center': row.cost_center,
				'tare_weight':row.tare_weight,
				'purchase_receipt_item_reference':row.name,
				'supplier_qty':row.supplier_qty,
				'supplier_quantity':row.supplier_quantity,
				'supplier_concentration':row.supplier_concentration,
				'supplier_no_of_packages':row.supplier_no_of_packages,
				'supplier_packing_size':row.supplier_packing_size,
				'accepted_qty':row.accepted_qty,
				'accepted_quantity':row.accepted_quantity,
				'accepted_concentration':row.accepted_concentration,
				'accepted_packing_size':row.accepted_packing_size,
				'accepted_no_of_packages':row.accepted_no_of_packages,
				'receive_packing_size':row.receive_packing_size,
				'receive_no_of_packages':row.receive_no_of_packages,
				'receive_qty':row.receive_qty,
				'receive_quantity':row.receive_quantity,
				'received_concentration':row.received_concentration,
			})
		
		# if self.additional_costs:
		# 	for row in self.additional_costs:
		# 		se.append("additional_costs",{
		# 			'expense_account': row.expense_account.replace(source_abbr, target_abbr),
		# 			'description': row.description,
		# 			'amount': row.amount
		# 		})
		
		se.save(ignore_permissions=True)
		# frappe.flags.warehouse_account_map = None
		se.submit()

def cancel_stock_entry(self):
	if self.send_to_party and self.party_type == "Company":
		if frappe.db.exists("Stock Entry",{'reference_doctype': self.doctype,'reference_docname':self.name,'company': self.company}):
			se = frappe.get_doc("Stock Entry",{'reference_doctype': self.doctype,'reference_docname':self.name,'company': self.company})
			se.flags.ignore_permissions = True
			if se.docstatus == 1:
				se.cancel()
			se.db_set('reference_doctype','')
			se.db_set('reference_docname','')  