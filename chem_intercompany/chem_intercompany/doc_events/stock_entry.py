import frappe
from frappe import msgprint, _
from frappe.utils import flt
from datetime import timedelta, datetime
from chem_intercompany.controllers.batch_controller import  get_fifo_batches, get_qty_from_sle
from six import itervalues
import json
import math

def validate(self,method):
	validate_date(self)
	set_receive_send_quantity(self)
	set_qty(self)
	

def set_qty(self):
	for row in self.items:
		if row.t_warehouse and row.receive_quantity and row.supplier_quantity:
			row.short_quantity = abs(row.receive_quantity - row.supplier_quantity)

def validate_date(self):
	if self.receive_posting_date:
		posting_date = datetime.strptime(self.posting_date, '%Y-%m-%d').date()
		receive_posting_date = datetime.strptime(self.receive_posting_date, '%Y-%m-%d').date()
		if receive_posting_date < posting_date:
			frappe.throw("Receive posting date should be greater than posting date")

def set_receive_send_quantity(self):
	receive_quantity = 0
	send_quantity = 0
	for item in self.items:
		if item.s_warehouse:
			receive_quantity += item.quantity
		if item.t_warehouse:
			send_quantity += item.quantity
	self.receive_quantity = receive_quantity
	self.send_quantity = send_quantity

def round_down(n, decimals=0):
	multiplier = 10 ** decimals
	return math.floor(n * multiplier) / multiplier

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
		se.series_value = self.jobwork_series_value or self.series_value
		if frappe.db.get_value("Company",self.company,'company_code') == frappe.db.get_value("Company",self.party,'company_code'):
			se.naming_series = self.jobwork_series or "STE.company_series./.fiscal./UII/.###"
		else:
			se.naming_series = self.jobwork_series or "STE.company_series./.fiscal./AII/.###"
		se.stock_entry_type = "Receive Jobwork Raw Material"
		se.purpose = "Material Receipt"
		se.set_posting_time = 1
		se.jw_ref = self.name
		se.posting_date = self.receive_posting_date or self.posting_date
		se.posting_time = self.posting_time
		se.company = self.party
		se.receive_from_party = 1
		se.party_type = self.party_type
		se.party = self.company
		se.to_warehouse = self.to_company_receive_warehouse or job_work_warehouse
		se.letter_head = frappe.db.get_value("Company",self.party,'default_letter_head')
		se.jobwork_invoice_no = self.jobwork_invoice_no
		se.jobwork_invoice_amount = self.jobwork_invoice_amount
		se.jobwork_challan_no = self.jobwork_challan_no
		
		if self.amended_from:
			se.amended_from = frappe.db.get_value("Stock Entry", {'jw_ref': self.amended_from}, "name")
		for row in self.items:
			se.append("items",{
				'item_code': row.item_code,
				't_warehouse':  self.to_company_receive_warehouse or job_work_warehouse,
				'qty': row.qty,
				'quantity':row.quantity,
				'short_quantity':row.short_quantity,
				'amount_difference':row.amount_difference,
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
				'packing_size':row.packing_size,
				'tare_weight':row.tare_weight,
				'no_of_packages':row.no_of_packages,
				'batch_yield':row.batch_yield,
				'concentration': row.party_concentration or row.concentration,
				'actual_qty':row.actual_qty,
				'expense_account': expense_account,
				'cost_center': row.cost_center.replace(source_abbr, target_abbr),
				'supplier_qty':row.supplier_qty,
				'supplier_quantity':row.supplier_quantity,
				'supplier_concentration':row.supplier_concentration,
				'supplier_packing_size':row.supplier_packing_size,
				'supplier_no_of_packages':row.supplier_no_of_packages,
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
		if not self.draft_auto_entry:
			se.submit()

def job_work_repack(self):
	if self.stock_entry_type == "Send Jobwork Finish" and self.purpose == "Material Issue" and self.send_to_party and self.party_type == "Company":
		if not self.finish_item:
			frappe.throw(_("Please define finish Item"))

		if self.bom_no and not self.fg_completed_quantity:
			frappe.throw(_("Please define Bom No and For Quantity"))
		if not self.to_company_receive_warehouse:
			frappe.throw(_("Please define To company warehouse"))
		#create repack
		se = frappe.new_doc("Stock Entry")
		se.stock_entry_type = "Receive Jobwork Return"
		se.naming_series = self.jobwork_series or self.naming_series
		se.series_value = self.jobwork_series_value or self.series_value
		se.purpose = "Repack"
		se.set_posting_time = 1
		se.reference_doctype = self.doctype
		se.reference_docname =self.name
		se.posting_date = self.receive_posting_date or self.posting_date
		se.posting_time = self.posting_time
		se.company = self.party
		se.receive_from_party = 1
		se.party_type = self.party_type
		se.party = self.company
		se.allow_short_qty_consumption = self.allow_short_qty_consumption
		se.letter_head = frappe.db.get_value("Company",self.party,'default_letter_head')
		source_abbr = frappe.db.get_value('Company',self.company,'abbr')
		target_abbr = frappe.db.get_value('Company',self.party,'abbr')
		job_work_out_warehouse = frappe.db.get_value('Company',self.party,'job_work_out_warehouse')
		job_work_in_warehouse = frappe.db.get_value('Company',self.party,'default_warehouse')
		expense_account = frappe.db.get_value('Company',self.party,'job_work_difference_account')
		se.jobwork_invoice_no = self.jobwork_invoice_no
		se.jobwork_invoice_amount = self.jobwork_invoice_amount
		se.jobwork_challan_no = self.jobwork_challan_no

		
		if self.bom_no:
			item_dict = self.get_bom_raw_materials(self.fg_completed_quantity)
			for item in itervalues(item_dict):
				item["from_warehouse"] = job_work_out_warehouse
				item["quantity"] = item["qty"]
				item["concentration"] = 100
				item["cost_center"] = item["cost_center"].replace(source_abbr,target_abbr)
				item["expense_account"] = item["expense_account"].replace(source_abbr,target_abbr)
			se.add_to_stock_entry_detail(item_dict)
			se.set_scrap_items()
			se.set_actual_qty()
			se.set_incoming_rate()
			
		else:
			for item in self.items:	
				se.append("items",{
					'item_code': item.item_code,
					's_warehouse': job_work_out_warehouse,
					'qty': item.qty,
					'quantity': item.quantity,
					'short_quantity':item.short_quantity,
					'amount_difference':item.amount_difference,
					'basic_rate':item.basic_rate,
					'basic_amount':item.basic_amount,
					'additional_cost':item.additional_cost,
					'amount':item.amount,
					'price':item.price,
					'uom':item.uom,
					'stock_uom':item.stock_uom,
					'conversion_factor':item.conversion_factor,
					'transfer_qty':item.transfer_qty,
					'batch_no':item.batch_no,
					'lot_no':item.lot_no,
					'packaging_material':item.packaging_material,
					'received_qty':item.received_qty,
					'packing_size':item.packing_size,
					'tare_weight':item.tare_weight,
					'batch_yield':item.batch_yield,
					'concentration':item.concentration,
					'actual_qty':item.actual_qty,
					'expense_account': expense_account,
					'cost_center': item.cost_center.replace(source_abbr, target_abbr),
					'supplier_qty':item.supplier_qty,
					'supplier_quantity':item.supplier_quantity,
					'supplier_concentration':item.supplier_concentration,
					'supplier_packing_size':item.supplier_packing_size,
					'supplier_no_of_packages':item.supplier_no_of_packages,
					'accepted_qty':item.accepted_qty,
					'accepted_quantity':item.accepted_quantity,
					'accepted_concentration':item.accepted_concentration,
					'accepted_packing_size':item.accepted_packing_size,
					'accepted_no_of_packages':item.accepted_no_of_packages,
					'receive_packing_size':item.receive_packing_size,
					'receive_no_of_packages':item.receive_no_of_packages,
					'receive_qty':item.receive_qty,
					'receive_quantity':item.receive_quantity,
					'received_concentration':item.received_concentration,
				})
		
		se.set_scrap_items()
		se.set_actual_qty()
		se.set_incoming_rate()

		for item in self.items:	
			se.append("items",{
				'item_code': item.item_code,
				't_warehouse': self.to_company_receive_warehouse or job_work_in_warehouse,
				'quantity':item.quantity,
				'qty': item.qty,
				'uom': item.uom,
				'stock_uom': item.stock_uom,
				'conversion_factor': item.conversion_factor,
				'lot_no': item.lot_no,
				'packaging_material': item.packaging_material,
				'packing_size': item.packing_size,
				'no_of_packages': item.no_of_packages,
				'batch_yield': item.batch_yield,
				'concentration': item.party_concentration or  item.concentration
			})
		
		for row in self.additional_costs:
			se.append("additional_costs",{
				'expense_account': row.expense_account.replace(source_abbr,target_abbr),
				'description': row.description,
				'amount': row.amount
			})
		
		job_work_item_reset(se,job_work_out_warehouse,self.company)
		
		se.get_stock_and_rate()
		
		se.save(ignore_permissions=True)
		if not self.draft_auto_entry:
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
			# if not self.fg_completed_qty:
			# 	frappe.throw(_("Please define For Qty"))
			if not self.fg_completed_quantity:
				frappe.throw(_("Please define For Quantity"))

		if self.bom_no:
			item_dict = self.get_bom_raw_materials(self.fg_completed_quantity)
			for item in itervalues(item_dict):
				item["from_warehouse"] = job_work_out_warehouse
				item["quantity"] = item["qty"]
				item["concentration"] = 100
			self.add_to_stock_entry_detail(item_dict)
		else:
			for item in self.items:
				self.append("items",{
					'item_code': item.item_code,
					's_warehouse': job_work_out_warehouse,
					'qty': item.qty,
					'quantity': item.quantity,
					'short_quantity':item.short_quantity,
					'basic_rate':item.basic_rate,
					'basic_amount':item.basic_amount,
					'additional_cost':item.additional_cost,
					'amount':item.amount,
					'price':item.price,
					'uom': frappe.db.get_value("Item",self.finish_item,'stock_uom'),
					'stock_uom': frappe.db.get_value("Item",self.finish_item,'stock_uom'),
					'conversion_factor':1,
					'transfer_qty':item.transfer_qty,
					'batch_no':item.batch_no,
					'lot_no':item.lot_no,
					'packaging_material':item.packaging_material,
					'received_qty':item.received_qty,
					'packing_size':item.packing_size,
					'tare_weight':item.tare_weight,
					'concentration':item.concentration,
					'supplier_concentration':item.supplier_concentration,
					'supplier_quantity':item.supplier_quantity,
					'actual_qty':item.actual_qty,
				})

		self.append("items",{
			'item_code': self.finish_item,
			't_warehouse': self.to_company_receive_warehouse or job_work_in_warehouse,
			'quantity': self.fg_completed_quantity,
			'uom': frappe.db.get_value("Item",self.finish_item,'stock_uom'),
			'stock_uom': frappe.db.get_value("Item",self.finish_item,'stock_uom'),
			'conversion_factor': 1,
			'concentration': 100,
		})
		job_work_item_reset(self,job_work_out_warehouse,self.party)

def job_work_item_reset(self,job_work_out_warehouse,party):
	items = []
	final_items = []
	batch_utilized = {}
	to_remove = []
	
	for d in self.items:
		if not d.t_warehouse:
			if not d.s_warehouse and not d.t_warehouse:
				d.s_warehouse = job_work_out_warehouse
			
			has_batch_no,maintain_as_is_stock = frappe.db.get_value('Item', d.item_code, ['has_batch_no','maintain_as_is_stock'])
			if not has_batch_no:
				item_qty = get_qty_from_sle(d.item_code, d.s_warehouse, party,self.posting_date, self.posting_time)
				if item_qty <= 0:
					if self.allow_short_qty_consumption:
						to_remove.append(d)
						frappe.msgprint(_("Sufficient quantity for item {} is not available in {} warehouse for party {}.".format(frappe.bold(d.item_code), frappe.bold(d.s_warehouse), party)))
					else:
						frappe.throw(_("Sufficient quantity for item {} is not available in {} warehouse for party {}.".format(frappe.bold(d.item_code), frappe.bold(d.s_warehouse),party)))
				elif d.qty > item_qty:
					if self.allow_short_qty_consumption:
						d.qty = item_qty
						frappe.msgprint(_("Only partial quantity is available for item {} in {} warehouse for party {}.".format(frappe.bold(d.item_code), frappe.bold(d.s_warehouse),party)))
					else:
						frappe.throw(_("Only partial quantity is available for item {} in {} warehouse for party {}.".format(frappe.bold(d.item_code), frappe.bold(d.s_warehouse),party)))

				continue

			batch_qty_dict = {}
			batch_qty_dict_post = {}
			batch_concentration_dict = {}

			batches = get_fifo_batches(d.item_code, d.s_warehouse, party ,self.posting_date, self.posting_time)
			#frappe.msgprint(str(batches))
			if not batches:
				if not self.allow_short_qty_consumption:
					frappe.throw(_("Sufficient quantity for item {} is not available in {} warehouse for party {}.".format(frappe.bold(d.item_code), frappe.bold(d.s_warehouse),party)))
				else:
					to_remove.append(d)	
			for batch in batches:	
				if batch.batch_id == d.batch_no or batch.lot_no == d.lot_no:
					batch_qty_dict.update({batch.batch_id:batch.qty})		
				else:
					batch_qty_dict_post.update({batch.batch_id:batch.qty})
				batch_concentration_dict.update({batch.batch_id:batch.concentration})
			batch_qty_dict.update(batch_qty_dict_post)
			
			for batch, qty in batch_utilized.items():
				if batch_qty_dict.get(batch):
					batch_qty_dict[batch] = (flt(batch_qty_dict[batch]) - flt(qty))
					if batch_qty_dict[batch] == 0:
						batch_qty_dict.pop(batch)

			if batch_qty_dict == {}:
				if not self.allow_short_qty_consumption:
					frappe.throw(_("Sufficient quantity for item {} is not available in {} warehouse for party {}.".format(frappe.bold(d.item_code), frappe.bold(d.s_warehouse),party)))
				else:
					to_remove.append(d)
												
			concentration = d.concentration or 100
			if maintain_as_is_stock:	
				remaining_quantity = round(flt(d.qty)*flt(concentration)/100,2)
			else:
				remaining_quantity = round(flt(d.qty),2)

			i = 0
			#frappe.msgprint("last: " + str(batch_qty_dict))
			
			for batch, qty in batch_qty_dict.items():
				# frappe.msgprint(str(batch) + " : " +str(qty))
				if qty > 0:
					concentration = flt(batch_concentration_dict[batch])
					if maintain_as_is_stock:
						remaining_qty = round(flt(remaining_quantity*100 / concentration),2)
					else:
						remaining_qty = round(flt(remaining_quantity),2)

					if remaining_qty == 0:
						continue

					if i == 0:
						if qty >= remaining_qty:
							d.batch_no = batch
							d.concentration = concentration
							d.qty = min(remaining_qty,qty)
							d.quantity = 0 # to avoid calculation of qty from quantity
							if maintain_as_is_stock:
								quantity = round(d.qty * d.concentration /100,2)
							else:
								quantity = d.qty
							batch_utilized[batch] = batch_utilized.get(batch,0) + remaining_qty
						
							break

						else:
							if len(batches) == 1:
								if not self.allow_short_qty_consumption:
									frappe.throw(_("Sufficient quantity for item {} is not available in {} warehouse for party {}.".format(frappe.bold(d.item_code), frappe.bold(d.s_warehouse),party)))
							
							d.batch_no = batch
							d.qty = qty
							d.concentration = concentration
							d.quantity = 0 # to avoid calculation of qty from quantity
							if maintain_as_is_stock:
								quantity = round(d.qty * d.concentration /100,2)
							else:
								quantity = d.qty

							remaining_qty -= round(flt(qty),2)
							remaining_quantity -= round(flt(quantity),2)
							batch_utilized[batch] = batch_utilized.get(batch,0) + qty

							items.append(frappe._dict({
								'item_code': d.item_code,
								's_warehouse': job_work_out_warehouse,
								'qty': remaining_qty,
								'uom': d.uom,
								'stock_uom': d.stock_uom,
								'conversion_factor': d.conversion_factor,
							}))

					else:
						flag = 0
						for x in items[:]:
							if x.get('batch_no'):
								continue
							if x.item_code != d.item_code:
								continue
							if qty >= remaining_qty:
								x.batch_no = batch											
								x.concentration = concentration
							
								x.qty = min(remaining_qty,qty)
								if maintain_as_is_stock:
									quantity = round((x.qty * concentration /100),2)
								else:
									quantity = x.qty									
								batch_utilized[batch] = batch_utilized.get(batch,0) + remaining_qty
								
								flag = 1
								break

							else:
								x.batch_no = batch
								x.qty = qty
								x.concentration = concentration
								if maintain_as_is_stock:
									quantity = round((x.qty * x.concentration /100),2)

								else:
									quantity = x.qty										
								remaining_qty -= round(flt(qty),2)	
								remaining_quantity -= round(flt(quantity),2)						
								batch_utilized[batch] = batch_utilized.get(batch,0) + qty

								items.append(frappe._dict({
									'item_code': d.item_code,
									's_warehouse': job_work_out_warehouse,
									'qty': remaining_qty,
									'uom': d.uom,
									'stock_uom': d.stock_uom,
									'conversion_factor': d.conversion_factor,
								}))

						if flag:
							break
					i += 1
			
			else:
				#frappe.msgprint(str(remaining_quantity))
				if round_down(remaining_quantity,1):
					if self.allow_short_qty_consumption:
						frappe.msgprint(_("_Sufficient quantity for item {} is not available in {} warehouse for party {}.".format(frappe.bold(d.item_code), frappe.bold(d.s_warehouse), party)))
					else:
						frappe.throw(_("Sufficient quantity for item {} is not available in {} warehouse for party {}.".format(frappe.bold(d.item_code), frappe.bold(d.s_warehouse), party)))
			
			if not d.batch_no and self.allow_short_qty_consumption:
				to_remove.append(d)
	
	final_items = [i for i in items if 'batch_no' in i.keys()] 
	# frappe.msgprint(str(final_items))
	for item in self.items:
		if item not in to_remove:
			final_items.append(item.__dict__)
	
	
	self.items = []
	self.extend('items', final_items)
	# for row in self.items:
	# 	frappe.msgprint("Qty: " + str(row.qty) + " Batch: " + str(row.batch_no))