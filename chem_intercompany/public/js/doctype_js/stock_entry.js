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
            frm.set_query("batch_no", "items", function (doc, cdt, cdn) {
                let d = locals[cdt][cdn];
                if (!d.item_code) {
                    frappe.msgprint(__("Please select Item Code"));
                }
                else if (!d.s_warehouse) {
                    frappe.msgprint(__("Please select source warehouse"));
                }
                else {
                    return {
                        query: "chem_intercompany.api.get_challan_no",
                        filters: {
                            'item_code': d.item_code,
                            'warehouse': d.s_warehouse,
                            'posting_date':frm.doc.posting_date,
                            'posting_time':frm.doc.posting_time
                        }
                    }
                }
            });
        if (frm.doc.docstatus == 0){
            frm.trigger('stock_entry_type')
        } 
        if(frm.doc.party && frm.doc.docstatus==1){
            cur_frm.set_df_property("party_type", "read_only",1);
            cur_frm.set_df_property("party", "read_only",1);
        }
    },
    refresh: function(frm){
        if (frm.doc.amended_from && frm.doc.__islocal && frm.doc.docstatus == 0) {
            if (frm.doc.jw_ref) {
                if (frm.doc.stock_entry_type == "Send to Jobwork" || frm.doc.stock_entry_type == "Receive Jobwork Raw Material") {
                    frm.set_value("jw_ref", null);
                }
            }
            if(frm.doc.docstatus == 0){
                frm.trigger('stock_entry_type')
            }
        }
    },
    validate: function (frm) { 
        console.log(frappe.utils.sum((frm.doc.items || []).map(row => row.qty)));
        frm.set_value('total_qty',frappe.utils.sum((frm.doc.items || []).map(row => row.qty)))
        //frm.trigger('stock_entry_type')
    },
    
    stock_entry_type: function (frm) {
        if(frm.doc.stock_entry_type == "Send Jobwork Finish") {
           // frm.set_value('from_bom',1)
        }
        if(frm.doc.purpose == "Material Transfer" || frm.doc.purpose == "Material Issue"){
            frappe.meta.get_docfield("Stock Entry Detail","party_concentration", cur_frm.doc.name).hidden = 0;
        }
        else{
            frappe.meta.get_docfield("Stock Entry Detail","party_concentration", cur_frm.doc.name).hidden = 1;
        }
        if(frm.doc.purpose == "Material Receipt" || frm.doc.purpose == "Repack"){
            frappe.meta.get_docfield("Stock Entry Detail","receive_packing_size", cur_frm.doc.name).read_only = 0;

            frappe.meta.get_docfield("Stock Entry Detail","tare_weight", cur_frm.doc.name).read_only = 0;

            frappe.meta.get_docfield("Stock Entry Detail","receive_no_of_packages", cur_frm.doc.name).read_only = 0;

            frappe.meta.get_docfield("Stock Entry Detail","received_qty", cur_frm.doc.name).read_only = 0;


            frappe.meta.get_docfield("Stock Entry Detail","receive_qty", cur_frm.doc.name).read_only = 0;

            frappe.meta.get_docfield("Stock Entry Detail","received_concentration", cur_frm.doc.name).read_only = 0;

            frappe.meta.get_docfield("Stock Entry Detail","receive_quantity", cur_frm.doc.name).read_only = 0;

            frappe.meta.get_docfield("Stock Entry Detail","supplier_no_of_packages", cur_frm.doc.name).read_only = 0;

            frappe.meta.get_docfield("Stock Entry Detail","supplier_packing_size", cur_frm.doc.name).read_only = 0;

            frappe.meta.get_docfield("Stock Entry Detail","supplier_concentration", cur_frm.doc.name).read_only = 0;

            frappe.meta.get_docfield("Stock Entry Detail","supplier_qty", cur_frm.doc.name).read_only = 0;

            frappe.meta.get_docfield("Stock Entry Detail","supplier_quantity", cur_frm.doc.name).read_only = 0;

            frappe.meta.get_docfield("Stock Entry Detail","accepted_qty", cur_frm.doc.name).read_only = 0;

            frappe.meta.get_docfield("Stock Entry Detail","accepted_concentration", cur_frm.doc.name).read_only = 0;

            frappe.meta.get_docfield("Stock Entry Detail","accepted_quantity", cur_frm.doc.name).read_only = 0;

            frappe.meta.get_docfield("Stock Entry Detail","accepted_packing_size", cur_frm.doc.name).read_only = 0;

            frappe.meta.get_docfield("Stock Entry Detail","accepted_no_of_packages", cur_frm.doc.name).read_only = 0;
            
            frappe.meta.get_docfield("Stock Entry Detail","short_quantity", cur_frm.doc.name).read_only = 0;
            
            frappe.meta.get_docfield("Stock Entry Detail","amount_difference", cur_frm.doc.name).read_only = 0;
        }
        else{
            frappe.meta.get_docfield("Stock Entry Detail","receive_packing_size", cur_frm.doc.name).read_only = 1;

            frappe.meta.get_docfield("Stock Entry Detail","tare_weight", cur_frm.doc.name).read_only = 1;

            frappe.meta.get_docfield("Stock Entry Detail","receive_no_of_packages", cur_frm.doc.name).read_only = 1;

            frappe.meta.get_docfield("Stock Entry Detail","received_qty", cur_frm.doc.name).read_only = 1;

            frappe.meta.get_docfield("Stock Entry Detail","receive_qty", cur_frm.doc.name).read_only = 1;

            frappe.meta.get_docfield("Stock Entry Detail","received_concentration", cur_frm.doc.name).read_only = 1;

            frappe.meta.get_docfield("Stock Entry Detail","receive_quantity", cur_frm.doc.name).read_only = 1;

            frappe.meta.get_docfield("Stock Entry Detail","supplier_no_of_packages", cur_frm.doc.name).read_only = 1;

            frappe.meta.get_docfield("Stock Entry Detail","supplier_packing_size", cur_frm.doc.name).read_only = 1;

            frappe.meta.get_docfield("Stock Entry Detail","supplier_concentration", cur_frm.doc.name).read_only = 1;

            frappe.meta.get_docfield("Stock Entry Detail","supplier_qty", cur_frm.doc.name).read_only = 1;

            frappe.meta.get_docfield("Stock Entry Detail","supplier_quantity", cur_frm.doc.name).read_only = 1;

            frappe.meta.get_docfield("Stock Entry Detail","accepted_qty", cur_frm.doc.name).read_only = 1;

            frappe.meta.get_docfield("Stock Entry Detail","accepted_concentration", cur_frm.doc.name).read_only = 1;

            frappe.meta.get_docfield("Stock Entry Detail","accepted_quantity", cur_frm.doc.name).read_only = 1;

            frappe.meta.get_docfield("Stock Entry Detail","accepted_packing_size", cur_frm.doc.name).read_only = 1;

            frappe.meta.get_docfield("Stock Entry Detail","accepted_no_of_packages", cur_frm.doc.name).read_only = 1;

            frappe.meta.get_docfield("Stock Entry Detail","short_quantity", cur_frm.doc.name).read_only = 1;

            frappe.meta.get_docfield("Stock Entry Detail","amount_difference", cur_frm.doc.name).read_only = 1;
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
    },
});

frappe.ui.form.on("Stock Entry Detail", {
    form_render:function(frm,cdt,cdn){
        frm.events.stock_entry_type(frm)
    },
    item_code: function(frm,cdt,cdn){
        frm.events.stock_entry_type(frm)
    },

});