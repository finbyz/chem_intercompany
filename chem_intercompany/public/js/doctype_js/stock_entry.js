// cur_frm.fields_dict.to_company_receive_warehouse.get_query = function (doc) {
//     if (doc.party_type == 'Company') {  
//         return {
//             filters: {
//                 "company": doc.party
//             }
//         }
//     }
// };

frappe.ui.form.on('Stock Entry', {
    onload: function(frm) {
        frm.fields_dict.to_company_receive_warehouse.get_query = function (doc) {
            if (doc.party_type == 'Company') {  
                return {
                    filters: {
                        "company": doc.party
                    }
                }
            }
        };
        
    },
    refresh: function(frm){
        if (frm.doc.amended_from && frm.doc.__islocal && frm.doc.docstatus == 0) {
            if (frm.doc.jw_ref) {
                if (frm.doc.stock_entry_type == "Send to Jobwork" || frm.doc.stock_entry_type == "Receive Jobwork Raw Material") {
                    frm.set_value("jw_ref", null);
                }
            } 
        }
    },
    validate: function (frm) { 
        console.log(frappe.utils.sum((frm.doc.items || []).map(row => row.qty)));
        //frm.trigger('stock_entry_type')
    },
    
    stock_entry_type: function (frm) {
        if(frm.doc.stock_entry_type == "Send Jobwork Finish") {
            frm.set_value('from_bom',1)
        }
    },
    get_bom_items: function(frm){
        frappe.call({
            doc: frm.doc,
            method: "get_bom_items",
            freeze : true,
            callback: function (r) {
                if(!r.exc) refresh_field("items");
               // console.log(r.message)
            }
        });
    }
});