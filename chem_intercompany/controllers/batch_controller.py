from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cstr

@frappe.whitelist()
def get_fifo_batches(item_code, warehouse, party, posting_date, posting_time):
	batches = frappe.db.sql("""
		select 
			bt.batch_id, sum(sle.actual_qty) as qty, bt.concentration
		from `tabBatch` as bt
		join `tabStock Ledger Entry` as sle ignore index (item_code, warehouse) 
		on (bt.batch_id = sle.batch_no)
		JOIN `tabStock Entry` as se ON se.name = sle.voucher_no
		where 
			sle.item_code = %s 
			and sle.warehouse = %s 
			and (bt.expiry_date >= CURDATE() or bt.expiry_date IS NULL)
			and se.party = %s
			and concat(sle.posting_date, ' ', sle.posting_time) <= %s %s
		group by sle.batch_no
		having sum(sle.actual_qty) > 0 
		order by sle.posting_date, bt.name """, (item_code, warehouse, party, posting_date, posting_time), as_dict=True)

	batches_now_date = frappe.db.sql("""
		select 
			bt.batch_id, sum(sle.actual_qty) as qty, bt.concentration
		from `tabBatch` as bt
		join `tabStock Ledger Entry` as sle ignore index (item_code, warehouse) 
		on (bt.batch_id = sle.batch_no)
		JOIN `tabStock Entry` as se ON se.name = sle.voucher_no
		where 
			sle.item_code = %s 
			and sle.warehouse = %s 
			and (bt.expiry_date >= CURDATE() or bt.expiry_date IS NULL)
			and se.party = %s
		group by sle.batch_no
		having sum(sle.actual_qty) > 0 
		order by sle.posting_date, bt.name """, (item_code, warehouse, party), as_dict=True)

	batches_nowdate_dict = {}
	for batch in batches_now_date:
		batches_nowdate_dict.update({batch.batch_id:batch.qty})

	for batch in batches:
		if batches_nowdate_dict.get(batch.batch_id):
			if batch.qty > batches_nowdate_dict[batch.batch_id]:
				batch.qty = batches_nowdate_dict[batch.batch_id]
		else:
			batches.remove(batch)

	return batches

def get_qty_from_sle(item_code, warehouse, party, posting_date, posting_time):
	qty = frappe.db.sql("""
	select 
		sum(sle.actual_qty) as qty
	from 
		`tabStock Ledger Entry` as sle
	JOIN `tabStock Entry` as se ON se.name = sle.voucher_no
	where 
		item_code=%s and warehouse=%s and se.party = %s 
		and concat(sle.posting_date, ' ', sle.posting_time) <= %s %s""", (item_code, warehouse, party, posting_date, posting_time))[0][0]

	if qty!=None:
		return qty
	else:
		return 0