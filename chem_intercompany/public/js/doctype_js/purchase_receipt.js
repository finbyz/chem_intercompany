frappe.ui.form.on('Purchase Receipt', {
    refresh: function(frm) {
        if (frm.doc.amended_from && frm.doc.__islocal && frm.doc.docstatus == 0){
    frm.set_value("inter_company_receipt_reference", "");
    frm.set_value("pr_ref", "");
    frm.set_value("dn_ref", "");
    }
}
});