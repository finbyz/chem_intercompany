import frappe
from frappe import msgprint, _
from frappe.utils import flt
from datetime import timedelta

def on_submit(self,method):
	create_job_work_receipt_entry(self)
	job_work_repack(self)

def on_cancel(self,method):
	cancel_job_work(self)
	cancel_repack_entry(self)

def create_job_work_receipt_entry(self):
	if self.stock_entry_type == "Send to Jobwork" and self.purpose == "Material Transfer" and self.send_to_party and self.party_type == "Company":
		source_abbr = frappe.db.get_value("Company", self.company,'abbr')
		target_abbr = frappe.db.get_value("Company", self.party,'abbr')
		expense_account = frappe.db.get_value('Company',self.party,'job_work_difference_account')
		job_work_warehouse = frappe.db.get_value('Company',self.party,'job_work_warehouse')

		if not expense_account or not job_work_warehouse:
			frappe.throw(_("Please set Job work difference account and warehouse in company <b>{0}</b>").format(self.party))

		se = frappe.new_doc("Stock Entry")
		se.stock_entry_type = "Receive Jobwork Raw Material"
		se.purpose = "Material Receipt"
		se.set_posting_time = 1
		se.jw_ref = self.name
		se.posting_date = self.posting_date
		se.posting_time = self.posting_time
		se.company = self.party
		se.to_warehouse = self.to_company_receive_warehouse or job_work_warehouse

		if self.amended_from:
			se.amended_from = frappe.db.get_value("Stock Entry", {'jw_ref': self.amended_from}, "name")
		for row in self.items:
			se.append("items",{
				'item_code': row.item_code,
				't_warehouse':  self.to_company_receive_warehouse or job_work_warehouse,
				'batch_no': row.batch_no,
				'qty': row.qty,
				'expense_account': expense_account,
				'cost_center': row.cost_center.replace(source_abbr, target_abbr)
			})
		
		if self.additional_costs:
			for row in self.additional_costs:
				se.append("additional_costs",{
					'expense_account': row.expense_account.replace(source_abbr, target_abbr),
					'description': row.description,
					'amount': row.amount
				})
		
		se.save(ignore_permissions=True)
		self.db_set('jw_ref', se.name)
		# frappe.flags.warehouse_account_map = None
		self.jw_ref = se.name
		se.submit()

def job_work_repack(self):
	if self.stock_entry_type == "Send Jobwork Finish" and self.purpose == "Material Issue" and self.send_to_party and self.party_type == "Company":
		if not self.finish_item:
			frappe.throw(_("Please define finish Item"))
		if not self.bom_no or not self.fg_completed_qty:
			frappe.throw(_("Please define Bom No and For Qty"))
		if not self.to_company_receive_warehouse:
			frappe.throw(_("Please define To company warehouse"))
		#create repack
		se = frappe.new_doc("Stock Entry")
		se.stock_entry_type = "Repack"
		se.purpose = "Repack"
		se.set_posting_time = 1
		se.reference_doctype = self.doctype
		se.reference_docname =self.name
		se.posting_date = self.posting_date
		se.posting_time = self.posting_time + timedelta(minutes=1)
		se.company = self.party
		source_abbr = frappe.db.get_value('Company',self.company,'abbr')
		target_abbr = frappe.db.get_value('Company',self.party,'abbr')
		item_dict = self.get_bom_raw_materials(self.fg_completed_qty)
		
		se.add_to_stock_entry_detail(item_dict)
		se.append("items",{
			'item_code': self.finish_item,
			't_warehouse': self.to_company_receive_warehouse,
			'qty': self.fg_completed_qty,
			'lot_no': self.items[0].lot_no,
			'packaging_material': self.items[0].packaging_material,
			'packing_size': self.items[0].packing_size,
			'no_of_packages': self.items[0].no_of_packages,
			'batch_yield': self.items[0].batch_yield,
			'concentration': self.items[0].concentration
		})
		for row in self.additional_costs:
			se.append("additional_costs",{
				'expense_account': row.expense_account.replace(source_abbr,target_abbr),
				'description': row.description,
				'amount': row.amount
			})
		
		se.save(ignore_permissions=True)
		se.get_stock_and_rate()
		se.save(ignore_permissions=True)
		se.submit()
		
def cancel_job_work(self):
	if self.jw_ref:
		jw_doc = frappe.get_doc("Stock Entry", self.jw_ref)
		if jw_doc.docstatus == 1:
			jw_doc.cancel()
		#self.db_set('jw_ref','')

def cancel_repack_entry(self):
	if self.send_to_party and self.party_type == "Company":
		if frappe.db.exists("Stock Entry",{'reference_doctype': self.doctype,'reference_docname':self.name,'company': self.party}):
			se = frappe.get_doc("Stock Entry",{'reference_doctype': self.doctype,'reference_docname':self.name,'company': self.job_work_company})
			se.flags.ignore_permissions = True
			if se.docstatus == 1:
				se.cancel()
			se.db_set('reference_doctype','')
			se.db_set('reference_docname','')   