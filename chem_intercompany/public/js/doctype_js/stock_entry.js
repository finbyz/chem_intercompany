cur_frm.fields_dict.to_company_receive_warehouse.get_query = function (doc) {
    if (doc.party_type == 'Company') {  
        return {
            filters: {
                "company": doc.party
            }
        }
    }
};

frappe.ui.form.on('Stock Entry', {
    onload: function(frm){
        frm.set_query("bom_no", function (doc) {
            if (doc.stock_entry_type == 'Send Jobwork Finish') {  
                return {
                    filters: {
                        "item": doc.finish_item,
                        'is_active': 1,
                        'docstatus': 1,
                        "company": doc.company
                    }
                }  
            }
            else {
                return {
                    filters: {
                        "company": doc.company,
                        'is_active': 1,
                        'docstatus': 1
                    }
                } 
            }
        })
    },
    validate: function (frm) { 
        frm.trigger('stock_entry_type')
    },
    
    stock_entry_type: function (frm) {
        if(frm.doc.stock_entry_type == "Send Jobwork Finish") {
            frm.set_value('from_bom',1)
        }
    },
    refresh: function(frm){
        if (frm.doc.amended_from && frm.doc.__islocal && frm.doc.docstatus == 0) {
            if (frm.doc.jw_ref) {
                if (frm.doc.stock_entry_type == "Send to Jobwork" || frm.doc.stock_entry_type == "Receive Jobwork Raw Material") {
                    frm.set_value("jw_ref", null);
                }
            } 
        }
    }
});