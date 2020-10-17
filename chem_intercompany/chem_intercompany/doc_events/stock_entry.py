import frappe
from frappe import msgprint, _
from frappe.utils import flt
from datetime import timedelta
from chem_intercompany.controllers.batch_controller import  get_fifo_batches
from six import itervalues
import json

def on_submit(self,method):
	create_job_work_receipt_entry(self)
	job_work_repack(self)

def on_cancel(self,method):
	cancel_job_work(self)
	cancel_repack_entry(self)

def on_trash(self,method):
	delete_all(self)

def create_job_work_receipt_entry(self):
	if self.stock_entry_type == "Send to Jobwork" and self.purpose == "Material Transfer" and self.send_to_party and self.party_type == "Company":
		source_abbr = frappe.db.get_value("Company", self.company,'abbr')
		target_abbr = frappe.db.get_value("Company", self.party,'abbr')
		expense_account = frappe.db.get_value('Company',self.party,'job_work_difference_account')
		job_work_warehouse = frappe.db.get_value('Company',self.party,'job_work_warehouse')

		if not expense_account or not job_work_warehouse:
			frappe.throw(_("Please set Job work difference account and warehouse in company <b>{0}</b>").format(self.party))
		

		se = frappe.new_doc("Stock Entry")
		se.series_value = self.series_value
		if frappe.db.get_value("Company",self.company,'company_code') == frappe.db.get_value("Company",self.party,'company_code'):
			se.naming_series = "STE.company_series./.fiscal./UII/.###"
		else:
			se.naming_series = "STE.company_series./.fiscal./AII/.###"
		se.stock_entry_type = "Receive Jobwork Raw Material"
		se.purpose = "Material Receipt"
		se.set_posting_time = 1
		se.jw_ref = self.name
		se.posting_date = self.posting_date
		se.posting_time = self.posting_time
		se.company = self.party
		se.receive_from_party = 1
		se.party_type = self.party_type
		se.party = self.company
		se.to_warehouse = self.to_company_receive_warehouse or job_work_warehouse
		se.letter_head = frappe.db.get_value("Company",self.party,'default_letter_head')

		if self.amended_from:
			se.amended_from = frappe.db.get_value("Stock Entry", {'jw_ref': self.amended_from}, "name")
		for row in self.items:
			se.append("items",{
				'item_code': row.item_code,
				't_warehouse':  self.to_company_receive_warehouse or job_work_warehouse,
				'qty': row.qty,
				'quantity':row.quantity,
				'short_quantity':row.short_quantity,
				'basic_rate':row.basic_rate,
				'basic_amount':row.basic_amount,
				'additional_cost':row.additional_cost,
				'amount':row.amount,
				'price':row.price,
				'uom':row.uom,
				'stock_uom':row.stock_uom,
				'conversion_factor':row.conversion_factor,
				'transfer_qty':row.transfer_qty,
				'batch_no':row.batch_no,
				'lot_no':row.lot_no,
				'packaging_material':row.packaging_material,
				'received_qty':row.received_qty,
				'received_quantity':row.received_quantity,
				'packing_size':row.packing_size,
				'tare_weight':row.tare_weight,
				'no_of_packages':row.no_of_packages,
				'batch_yield':row.batch_yield,
				'concentration':row.concentration,
				'supplier_concentration':row.supplier_concentration,
				'supplier_quantity':row.supplier_quantity,
				'actual_qty':row.actual_qty,
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

		# if not self.bom_no or not self.fg_completed_qty:
		# 	frappe.throw(_("Please define Bom No and For Qty"))
		if not self.to_company_receive_warehouse:
			frappe.throw(_("Please define To company warehouse"))
		#create repack
		se = frappe.new_doc("Stock Entry")
		se.stock_entry_type = "Receive Jobwork Return"
		se.purpose = "Repack"
		se.set_posting_time = 1
		se.reference_doctype = self.doctype
		se.reference_docname =self.name
		se.posting_date = self.posting_date
		se.posting_time = self.posting_time
		se.company = self.party
		se.receive_from_party = 1
		se.party_type = self.party_type
		se.party = self.company
		se.letter_head = frappe.db.get_value("Company",self.party,'default_letter_head')
		source_abbr = frappe.db.get_value('Company',self.company,'abbr')
		target_abbr = frappe.db.get_value('Company',self.party,'abbr')
		job_work_out_warehouse = frappe.db.get_value('Company',self.party,'job_work_out_warehouse')
		job_work_in_warehouse = frappe.db.get_value('Company',self.party,'job_work_warehouse')
		expense_account = frappe.db.get_value('Company',self.party,'job_work_difference_account')

		if self.bom_no:
			item_dict = self.get_bom_raw_materials(self.fg_completed_qty)
			for item in itervalues(item_dict):
				item["from_warehouse"] = job_work_out_warehouse
				item["cost_center"] = item["cost_center"].replace(source_abbr,target_abbr)
				item["expense_account"] = item["expense_account"].replace(source_abbr,target_abbr)
			se.add_to_stock_entry_detail(item_dict)

		else:
			for item in self.items:	
				se.append("items",{
					'item_code': item.item_code,
					's_warehouse': job_work_out_warehouse,
					'qty': item.qty,
					'quantity':item.quantity,
					'short_quantity':item.short_quantity,
					'basic_rate':item.basic_rate,
					'basic_amount':item.basic_amount,
					'additional_cost':item.additional_cost,
					'amount':item.amount,
					'price':item.price,
					'uom':item.uom,
					'stock_uom':item.stock_uom,
					'conversion_factor':item.conversion_factor,
					'transfer_qty':item.transfer_qty,
					'lot_no':item.lot_no,
					'packaging_material':item.packaging_material,
					'received_qty':item.received_qty,
					'received_quantity':item.received_quantity,
					'packing_size':item.packing_size,
					'tare_weight':item.tare_weight,
					'no_of_packages':item.no_of_packages,
					'batch_yield':item.batch_yield,
					'concentration':item.concentration,
					'supplier_concentration':item.supplier_concentration,
					'supplier_quantity':item.supplier_quantity,
					'actual_qty':item.actual_qty,
					'expense_account': expense_account, # Ask to sir 
					'cost_center': item.cost_center.replace(source_abbr, target_abbr)
				})

		for item in self.items:	
			se.append("items",{
				'item_code': item.item_code,
				't_warehouse': self.to_company_receive_warehouse or job_work_in_warehouse,
				'qty': item.qty,
				'uom': item.uom,
				'stock_uom': item.stock_uom,
				'conversion_factor': item.conversion_factor,
				'lot_no': item.lot_no,
				'packaging_material': item.packaging_material,
				'packing_size': item.packing_size,
				'no_of_packages': item.no_of_packages,
				'batch_yield': item.batch_yield,
				'concentration': item.concentration,
			})

		for row in self.additional_costs:
			se.append("additional_costs",{
				'expense_account': row.expense_account.replace(source_abbr,target_abbr),
				'description': row.description,
				'amount': row.amount
			})

		items = []

		for d in se.items:
			if not d.t_warehouse:
				if not d.s_warehouse and not d.t_warehouse:
					d.s_warehouse = job_work_out_warehouse

			
				has_batch_no = frappe.db.get_value('Item', d.item_code, 'has_batch_no')

				if not has_batch_no:
					continue

				batches = get_fifo_batches(d.item_code, d.s_warehouse, self.company)
				if not batches:
					frappe.throw(_("Sufficient quantity for item {} is not available in {} warehouse.".format(frappe.bold(d.item_code), frappe.bold(d.s_warehouse))))

				remaining_qty = d.qty

				for i, batch in enumerate(batches):
					if i == 0:
						if batch.qty >= remaining_qty:
							d.batch_no = batch.batch_id
							break

						else:
							if len(batches) == 1:
								frappe.throw(_("Sufficient quantity for item {} is not available in {} warehouse.".format(frappe.bold(d.item_code), frappe.bold(d.s_warehouse))))

							remaining_qty -= flt(batch.qty)
							d.qty = batch.qty
							d.batch_no = batch.batch_id

							items.append(frappe._dict({
								'item_code': d.item_code,
								's_warehouse': job_work_out_warehouse,
								'qty': remaining_qty,
							}))

					else:
						flag = 0
						for x in items[:]:
							if x.get('batch_no'):
								continue

							if batch.qty >= remaining_qty:
								x.batch_no = batch.batch_id
								flag = 1
								break
							
							else:
								remaining_qty -= flt(batch.qty)
								
								x.qty = batch.qty
								x.batch_no = batch.batch_id
								
								items.append(frappe._dict({
									'item_code': d.item_code,
									's_warehouse': job_work_out_warehouse,
									'qty': remaining_qty,
								}))

						if flag:
							break

				else:
					if remaining_qty:
						frappe.throw(_("Sufficient quantity for item {} is not available in {} warehouse.".format(frappe.bold(d.item_code), frappe.bold(d.s_warehouse))))

		se.extend('items', items)

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
			se = frappe.get_doc("Stock Entry",{'reference_doctype': self.doctype,'reference_docname':self.name,'company': self.party})
			se.flags.ignore_permissions = True
			if se.docstatus == 1:
				se.cancel()
			se.db_set('reference_doctype','')
			se.db_set('reference_docname','')   
	
def delete_all(self):
	if self.jw_ref:
		jw_ref = [self.jw_ref,self.name]
		frappe.db.set_value(self.doctype, self.name, 'jw_ref', None)
		frappe.db.set_value(self.doctype, self.jw_ref, 'jw_ref', None)
		for se in jw_ref:
			frappe.delete_doc("Stock Entry", se)

@frappe.whitelist()
def get_bom_items(self):
	if self.stock_entry_type == "Receive Jobwork Return":
		self.set('items', [])
		if not self.finish_item:
			frappe.throw(_("Please define finish Item"))
		job_work_in_warehouse = frappe.db.get_value('Company',self.company,'job_work_warehouse')
		job_work_out_warehouse = frappe.db.get_value('Company',self.company,'job_work_out_warehouse')

		if self.bom_no:
			item_dict = self.get_bom_raw_materials(self.fg_completed_qty)
			for item in itervalues(item_dict):
				item["from_warehouse"] = job_work_out_warehouse
			self.add_to_stock_entry_detail(item_dict)

		else:	
			self.append("items",{
				'item_code':  self.finish_item,
				's_warehouse': job_work_out_warehouse,
				'qty': self.fg_completed_qty,
				'quantity': self.fg_completed_qty or self.fg_completed_quantity,
				'uom': frappe.db.get_value("Item",self.finish_item,'stock_uom'),
				'stock_uom': frappe.db.get_value("Item",self.finish_item,'stock_uom'),
				'conversion_factor': 1,
			})

		self.append("items",{
			'item_code': self.finish_item,
			't_warehouse': self.to_company_receive_warehouse or job_work_in_warehouse,
			'qty': self.fg_completed_qty,
			'quantity': self.fg_completed_qty or self.fg_completed_quantity,
			'uom': frappe.db.get_value("Item",self.finish_item,'stock_uom'),
			'stock_uom': frappe.db.get_value("Item",self.finish_item,'stock_uom'),
			'conversion_factor': 1,
			'concentration': 100,
		})
		
		items = []

		for d in self.items:
			if not d.t_warehouse:
				if not d.s_warehouse and not d.t_warehouse:
					d.s_warehouse = job_work_out_warehouse
	
				has_batch_no = frappe.db.get_value('Item', d.item_code, 'has_batch_no')

				if not has_batch_no:
					continue

				batches = get_fifo_batches(d.item_code, d.s_warehouse, self.party)
				if not batches:
					frappe.throw(_("Sufficient quantity for item {} is not available in {} warehouse.".format(frappe.bold(d.item_code), frappe.bold(d.s_warehouse))))

				remaining_qty = d.qty

				for i, batch in enumerate(batches):
					if i == 0:
						if batch.qty >= remaining_qty:
							d.batch_no = batch.batch_id
							break

						else:
							if len(batches) == 1:
								frappe.throw(_("Sufficient quantity for item {} is not available in {} warehouse.".format(frappe.bold(d.item_code), frappe.bold(d.s_warehouse))))

							remaining_qty -= flt(batch.qty)
							d.qty = batch.qty
							d.batch_no = batch.batch_id

							items.append(frappe._dict({
								'item_code': d.item_code,
								's_warehouse': job_work_out_warehouse,
								'qty': remaining_qty,
							}))

					else:
						flag = 0
						for x in items[:]:
							if x.get('batch_no'):
								continue

							if batch.qty >= remaining_qty:
								x.batch_no = batch.batch_id
								flag = 1
								break
							
							else:
								remaining_qty -= flt(batch.qty)
								
								x.qty = batch.qty
								x.batch_no = batch.batch_id
								
								items.append(frappe._dict({
									'item_code': d.item_code,
									's_warehouse': job_work_out_warehouse,
									'qty': remaining_qty,
								}))

						if flag:
							break

				else:
					if remaining_qty:
						frappe.throw(_("Sufficient quantity for item {} is not available in {} warehouse.".format(frappe.bold(d.item_code), frappe.bold(d.s_warehouse))))

		#return items
		self.extend('items', items)
		#self.save()

