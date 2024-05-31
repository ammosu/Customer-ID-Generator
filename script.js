const backendUrl = '';

async function fetchOptions(url, selectId) {
    const response = await fetch(backendUrl + url);
    const options = await response.json();
    const select = document.getElementById(selectId);
    select.innerHTML = '';  // Clear existing options
    options.forEach(option => {
        const opt = document.createElement('option');
        opt.value = opt.textContent = option;
        select.appendChild(opt);
    });

    // If this is the category select element, trigger the visibility update
    if (selectId === 'category') {
        updateFormVisibility();
    }
}

function updateFormVisibility() {
    const category = document.getElementById('category').value;
    const extraFields = document.getElementById('extra_fields');

    if (["0連鎖或相關企業的合開發票", "1連鎖或相關企業的不合開發票", "8達清關係企業"].includes(category)) {
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
    fetchOptions('/extra_region_codes', 'extra_region_code');
    document.getElementById('category').addEventListener('change', updateFormVisibility);

    // Initially show extra fields
    document.getElementById('extra_fields').style.display = 'block';
});

document.getElementById('generate-form').addEventListener('submit', async function(event) {
    event.preventDefault();
    const region = document.getElementById('region').value;
    const category = document.getElementById('category').value;
    const company_name = document.getElementById('company_name').value;
    const extra_region_code = document.getElementById('extra_region_code').value;
    const branch_name = document.getElementById('branch_name').value;

    if (!company_name || (["0連鎖或相關企業的合開發票", "1連鎖或相關企業的不合開發票", "8達清關係企業"].includes(category) && !branch_name)) {
        alert("公司名稱和分支名稱（若適用）不能為空。");
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
    previewResult.innerHTML = `預覽客戶ID: ${result.customer_id} <br> 
                               <button id="confirm-button">確認</button> 
                               <button id="cancel-button">取消</button>`;

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
        previewResult.innerHTML = `已生成客戶ID: ${confirmResult.customer_id}`;
    });

    document.getElementById('cancel-button').addEventListener('click', function() {
        previewResult.innerHTML = '';
    });
});

document.getElementById('query-form').addEventListener('submit', async function(event) {
    event.preventDefault();
    const company_name = document.getElementById('query_company_name').value;

    if (!company_name) {
        alert("公司名稱不能為空。");
        return;
    }

    const response = await fetch(backendUrl + '/query_customer_id', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ company_name })
    });

    const result = await response.json();
    const queryResult = document.getElementById('query-result');
    queryResult.innerHTML = '';

    if (result.detail === "查無此客戶ID") {
        const errorMsg = document.createElement('div');
        errorMsg.className = 'error';
        errorMsg.innerText = '查無此客戶ID';
        queryResult.appendChild(errorMsg);
    } else {
        displayData(result.data);
    }
});

document.getElementById('delete-form').addEventListener('submit', async function(event) {
    event.preventDefault();
    const customer_id = document.getElementById('delete_customer_id').value;

    if (!customer_id) {
        alert("客戶ID不能為空。");
        return;
    }

    if (!confirm(`您確定要刪除客戶ID: ${customer_id} 嗎？`)) {
        return;
    }

    const response = await fetch(backendUrl + `/delete_customer_id/${customer_id}`, {
        method: 'DELETE'
    });

    if (response.status === 404) {
        const result = await response.json();
        document.getElementById('delete-result').innerText = '查無此客戶ID';
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
        alert("匯出Excel失敗");
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

async function searchBranchName(keyword) {
    const region = document.getElementById('region').value;
    const category = document.getElementById('category').value;
    const company_name = document.getElementById('company_name').value;
    const extra_region_code = document.getElementById('extra_region_code').value;

    if (keyword.length < 1) {
        document.getElementById('branch_name_list').innerHTML = '';
        return;
    }

    const response = await fetch(`${backendUrl}/search_branch_name/?keyword=${keyword}&region=${region}&category=${category}&company_name=${company_name}&extra_region_code=${extra_region_code}`);
    const result = await response.json();
    const branchNameList = document.getElementById('branch_name_list');
    branchNameList.innerHTML = '';

    result.branch_names.forEach(name => {
        const div = document.createElement('div');
        div.innerText = name;
        div.addEventListener('click', () => {
            document.getElementById('branch_name').value = name;
            branchNameList.innerHTML = '';
        });
        branchNameList.appendChild(div);
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
