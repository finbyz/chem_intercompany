cur_frm.fields_dict.job_work_warehouse.get_query = function (doc) {   
    return {
        filters: {
            "company": doc.name
        }
    }   
};
cur_frm.fields_dict.job_work_out_warehouse.get_query = function (doc) {
    return {
        filters: {
            "company": doc.name
        }
    }
};

cur_frm.fields_dict.job_work_difference_account.get_query = function (doc) {
    return {
        filters: {
            "company": doc.name
        }
    }
};

