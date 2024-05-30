// script.js
const backendUrl = '';

async function fetchOptions(url, selectId) {
    const response = await fetch(backendUrl + url);
    const options = await response.json();
    const select = document.getElementById(selectId);
    options.forEach(option => {
        const opt = document.createElement('option');
        opt.value = option;
        opt.innerHTML = option;
        select.appendChild(opt);
    });
}

function updateFormVisibility() {
    const category = document.getElementById('category').value;
    const extraFields = document.getElementById('extra_fields');

    if (["連鎖或相關企業的合開發票", "連鎖或相關企業的不合開發票", "達清關係企業"].includes(category)) {
        extraFields.style.display = 'block';
    } else {
        extraFields.style.display = 'none';
        document.getElementById('extra_region_code').value = '';
        document.getElementById('branch_name').value = '';
    }
}

function updateCompanyNameList() {
    const company_name = document.getElementById('company_name').value;
    if (company_name.length > 0) {
        searchCompanyName(company_name);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    fetchOptions('/regions', 'region');
    fetchOptions('/categories', 'category');
});

// script.js

document.getElementById('generate-form').addEventListener('submit', async function(event) {
    event.preventDefault();
    const region = document.getElementById('region').value;
    const category = document.getElementById('category').value;
    const company_name = document.getElementById('company_name').value;
    const extra_region_code = document.getElementById('extra_region_code').value;
    const branch_name = document.getElementById('branch_name').value;

    if (!company_name || (["連鎖或相關企業的合開發票", "連鎖或相關企業的不合開發票", "達清關係企業"].includes(category) && !branch_name)) {
        alert("Company Name 和 Branch Name (若適用) 不能為空。");
        return;
    }

    const response = await fetch(backendUrl + '/preview_customer_id', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            region,
            category,
            company_name,
            extra_region_code,
            branch_name
        })
    });

    const result = await response.json();
    const previewResult = document.getElementById('generate-result');
    previewResult.innerHTML = `Preview Customer ID: ${result.customer_id} <br> 
                               <button id="confirm-button">Confirm</button> 
                               <button id="cancel-button">Cancel</button>`;

    document.getElementById('confirm-button').addEventListener('click', async function() {
        const confirmResponse = await fetch(backendUrl + '/generate_customer_id?confirm=true', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                region,
                category,
                company_name,
                extra_region_code,
                branch_name
            })
        });

        const confirmResult = await confirmResponse.json();
        previewResult.innerHTML = `Generated Customer ID: ${confirmResult.customer_id}`;
    });

    document.getElementById('cancel-button').addEventListener('click', function() {
        previewResult.innerHTML = '';
    });
});

document.getElementById('query-form').addEventListener('submit', async function(event) {
    event.preventDefault();
    const company_name = document.getElementById('query_company_name').value;

    if (!company_name) {
        alert("Company Name 不能為空。");
        return;
    }

    const response = await fetch(backendUrl + `/query_customer_id/${company_name}`, {
        method: 'GET'
    });

    const result = await response.json();
    const queryResult = document.getElementById('query-result');
    queryResult.innerHTML = '';

    if (result.detail === "Customer ID not found") {
        const errorMsg = document.createElement('div');
        errorMsg.className = 'error';
        errorMsg.innerText = 'Customer ID not found';
        queryResult.appendChild(errorMsg);
    } else {
        displayData(result.data);
    }
});

document.getElementById('delete-form').addEventListener('submit', async function(event) {
    event.preventDefault();
    const customer_id = document.getElementById('delete_customer_id').value;

    if (!customer_id) {
        alert("Customer ID 不能為空。");
        return;
    }

    if (!confirm(`Are you sure you want to delete Customer ID: ${customer_id}?`)) {
        return;
    }

    const response = await fetch(backendUrl + `/delete_customer_id/${customer_id}`, {
        method: 'DELETE'
    });

    if (response.status === 404) {
        const result = await response.json();
        document.getElementById('delete-result').innerText = 'Customer ID not found';
        document.getElementById('delete-result').className = 'error';
    } else {
        const result = await response.json();
        document.getElementById('delete-result').innerText = result.detail;
        document.getElementById('delete-result').className = 'result';
    }
});

document.getElementById('export-excel').addEventListener('click', async function() {
    const response = await fetch(backendUrl + '/export_excel', {
        method: 'GET'
    });
    if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = 'customer_ids.xlsx';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    } else {
        alert("Failed to export Excel");
    }
});

document.getElementById('import-form').addEventListener('submit', async function(event) {
    event.preventDefault();
    const fileInput = document.getElementById('import-file');
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    const response = await fetch(backendUrl + '/import_excel', {
        method: 'POST',
        body: formData
    });

    const result = await response.json();
    document.getElementById('import-result').innerText = result.detail;
});

async function searchCompanyName(keyword) {
    const region = document.getElementById('region').value;
    const category = document.getElementById('category').value;

    if (keyword.length < 1) {
        document.getElementById('company_name_list').innerHTML = '';
        return;
    }

    const response = await fetch(`${backendUrl}/search_company_name/?keyword=${keyword}&region=${region}&category=${category}`);
    const result = await response.json();
    const companyNameList = document.getElementById('company_name_list');
    companyNameList.innerHTML = '';

    result.company_names.forEach(name => {
        const div = document.createElement('div');
        div.innerText = name;
        div.addEventListener('click', () => {
            document.getElementById('company_name').value = name;
            companyNameList.innerHTML = '';
        });
        companyNameList.appendChild(div);
    });
}

async function searchAllCompanyNames(keyword) {
    if (keyword.length < 1) {
        document.getElementById('query_company_name_list').innerHTML = '';
        return;
    }

    const response = await fetch(`${backendUrl}/search_all_company_names/?keyword=${keyword}`);
    const result = await response.json();
    const companyNameList = document.getElementById('query_company_name_list');
    companyNameList.innerHTML = '';

    result.company_names.forEach(name => {
        const div = document.createElement('div');
        div.innerText = name;
        div.addEventListener('click', () => {
            document.getElementById('query_company_name').value = name;
            companyNameList.innerHTML = '';
        });
        companyNameList.appendChild(div);
    });
}

async function searchAllCustomerIDs(keyword) {
    if (keyword.length < 1) {
        document.getElementById('delete_customer_id_list').innerHTML = '';
        return;
    }

    const response = await fetch(`${backendUrl}/search_all_customer_ids/?keyword=${keyword}`);
    const result = await response.json();
    const customerIDList = document.getElementById('delete_customer_id_list');
    customerIDList.innerHTML = '';

    result.customer_ids.forEach(id => {
        const div = document.createElement('div');
        div.innerText = id;
        div.addEventListener('click', () => {
            document.getElementById('delete_customer_id').value = id;
            customerIDList.innerHTML = '';
        });
        customerIDList.appendChild(div);
    });
}

function displayData(data) {
    const queryResult = document.getElementById('query-result');
    const pagination = document.getElementById('pagination');
    queryResult.innerHTML = '';
    pagination.innerHTML = '';

    let currentPage = 1;
    const rowsPerPage = 10;
    const totalPages = Math.ceil(data.length / rowsPerPage);

    function renderTable(page) {
        queryResult.innerHTML = '';
        const table = document.createElement('table');
        const headers = ['Region', 'Category', 'CompanyName', 'ExtraRegionCode', 'BranchName', 'CustomerID'];
        const thead = document.createElement('thead');
        const tr = document.createElement('tr');

        headers.forEach(header => {
            const th = document.createElement('th');
            th.innerText = header;
            tr.appendChild(th);
        });

        thead.appendChild(tr);
        table.appendChild(thead);

        const tbody = document.createElement('tbody');
        const start = (page - 1) * rowsPerPage;
        const end = start + rowsPerPage;
        const pageData = data.slice(start, end);

        pageData.forEach(row => {
            const tr = document.createElement('tr');
            headers.forEach(header => {
                const td = document.createElement('td');
                td.innerText = row[header];
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });

        table.appendChild(tbody);
        queryResult.appendChild(table);
    }

    function renderPagination() {
        pagination.innerHTML = '';

        for (let i = 1; i <= totalPages; i++) {
            const button = document.createElement('button');
            button.innerText = i;
            button.addEventListener('click', () => {
                currentPage = i;
                renderTable(currentPage);
            });
            if (i === currentPage) {
                button.style.fontWeight = 'bold';
            }
            pagination.appendChild(button);
        }
    }

    renderTable(currentPage);
    renderPagination();
}
