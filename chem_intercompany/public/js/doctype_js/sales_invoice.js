frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {
    if (frm.doc.amended_from && frm.doc.__islocal && frm.doc.docstatus == 0){
        frm.set_value("inter_company_invoice_reference", "");
        frm.set_value("pi_ref", "");
        frm.set_value("si_ref", "");
        }
    }
});