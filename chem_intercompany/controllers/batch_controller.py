from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cstr

@frappe.whitelist()
def get_fifo_batches(item_code, warehouse):
	batches = frappe.db.sql("""
		select 
			bt.batch_id, sum(sle.actual_qty) as qty 
        from `tabBatch` as bt
        join `tabStock Ledger Entry` as sle ignore index (item_code, warehouse) 
		on (bt.batch_id = sle.batch_no )
		where 
			sle.item_code = %s 
			and sle.warehouse = %s 
			and (bt.expiry_date >= CURDATE() or bt.expiry_date IS NULL)
		group by sle.batch_no
		having sum(sle.actual_qty) > 0 
		order by sle.posting_date """, (item_code, warehouse), as_dict=True)

	return batches