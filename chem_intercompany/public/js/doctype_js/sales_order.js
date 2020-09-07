frappe.ui.form.on('Sales Order', {
    refresh: function(frm) {
    if (frm.doc.amended_from && frm.doc.__islocal && frm.doc.docstatus == 0){
        frm.set_value("inter_company_order_reference", "");
        frm.set_value("po_ref", "");
        frm.set_value("so_ref", "");
        }
    }
});