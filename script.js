const backendUrl = '';

const translations = {
    en: {
        title: "Customer ID Generator",
        generateCustomerId: "Generate Customer ID",
        region: "Region:",
        category: "Category:",
        companyName: "Company Name:",
        extraRegionCode: "Extra Region Code:",
        branchHandling: "Branch Handling:",
        branchName: "Branch Name:",
        generate: "Generate",
        queryCustomerId: "Query Customer ID",
        queryCompanyName: "Company Name:",
        query: "Query",
        updateCustomerInfo: "Update Customer Info",
        newCompanyName: "New Company Name:",
        newBranchName: "New Branch Name:",
        update: "Update",
        deleteCustomerId: "Delete Customer ID",
        deleteCustomerIdLabel: "Customer ID:",
        delete: "Delete",
        importExportExcel: "Import/Export Excel",
        exportExcel: "Export Excel",
        importExcel: "Import Excel"
    },
    zh: {
        title: "客戶ID生成器",
        generateCustomerId: "生成客戶ID",
        region: "地區:",
        category: "類別:",
        companyName: "公司名稱:",
        extraRegionCode: "額外區域代碼:",
        branchHandling: "分支處理:",
        branchName: "分支名稱:",
        generate: "生成",
        queryCustomerId: "查詢客戶ID",
        queryCompanyName: "公司名稱:",
        query: "查詢",
        updateCustomerInfo: "更新客戶信息",
        newCompanyName: "新公司名稱:",
        newBranchName: "新分支名稱:",
        update: "更新",
        deleteCustomerId: "刪除客戶ID",
        deleteCustomerIdLabel: "客戶ID:",
        delete: "刪除",
        importExportExcel: "導入/導出 Excel",
        exportExcel: "導出 Excel",
        importExcel: "導入 Excel"
    }
};

function setLanguage(language) {
    localStorage.setItem('language', language);
    applyTranslations(language);
    document.getElementById('btn-en').classList.toggle('active', language === 'en');
    document.getElementById('btn-zh').classList.toggle('active', language === 'zh');
}

function applyTranslations(language) {
    const elements = document.querySelectorAll('[data-translate]');
    elements.forEach(element => {
        const key = element.getAttribute('data-translate');
        element.innerText = translations[language][key];
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const savedLanguage = localStorage.getItem('language') || 'en';
    setLanguage(savedLanguage);
});

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
    const branchHandling = document.getElementById('branch_handling');
    const branchHandlingLabel = document.getElementById('branch_handling_label');
    const branchName = document.getElementById('branch_name');
    const branchNameLabel = document.getElementById('branch_name_label');

    if (category === "0連鎖或相關企業的合開發票") {
        extraFields.style.display = 'block';
        branchHandling.style.display = 'block';
        branchHandlingLabel.style.display = 'block';
        branchHandling.value = '00開立發票客編';
        updateBranchHandling();
    } else if (["0連鎖或相關企業的合開發票", "1連鎖或相關企業的不合開發票", "8達清關係企業"].includes(category)) {
        extraFields.style.display = 'block';
        branchHandling.style.display = 'none';
        branchHandlingLabel.style.display = 'none';
        branchName.style.display = 'block';
        branchNameLabel.style.display = 'block';
    } else {
        extraFields.style.display = 'none';
        branchHandling.style.display = 'none';
        branchHandlingLabel.style.display = 'none';
        branchName.style.display = 'none';
        branchNameLabel.style.display = 'none';
        
        // 清除不相關字段的值
        document.getElementById('extra_region_code').value = '';
        document.getElementById('branch_handling').value = '';
        document.getElementById('branch_name').value = '';
    }
}

function updateBranchHandling() {
    const branchHandling = document.getElementById('branch_handling').value;
    const branchName = document.getElementById('branch_name');
    const branchNameLabel = document.getElementById('branch_name_label');

    if (branchHandling === "00開立發票客編") {
        branchName.style.display = 'none';
        branchNameLabel.style.display = 'none';
        branchName.value = ''; // 清除分支名稱的值
    } else {
        branchName.style.display = 'block';
        branchNameLabel.style.display = 'block';
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

    // Initially hide branch handling select and its label
    document.getElementById('branch_handling').style.display = 'none';
    document.getElementById('branch_handling_label').style.display = 'none';
    updateFormVisibility(); // Initialize form visibility based on default category
});

document.getElementById('generate-form').addEventListener('submit', async function(event) {
    event.preventDefault();
    const region = document.getElementById('region').value;
    const category = document.getElementById('category').value;
    const company_name = document.getElementById('company_name').value;
    let extra_region_code = document.getElementById('extra_region_code').value;
    let branch_handling = document.getElementById('branch_handling').value;
    let branch_name = document.getElementById('branch_name').value;

    // 清除不需要的字段
    if (document.getElementById('extra_fields').style.display === 'none') {
        extra_region_code = null;
    }
    if (document.getElementById('branch_handling').style.display === 'none') {
        branch_handling = null;
    }
    if (document.getElementById('branch_name').style.display === 'none') {
        branch_name = null;
    }

    // 構建請求數據
    const requestData = {
        region,
        category,
        company_name
    };

    if (extra_region_code !== null) {
        requestData.extra_region_code = extra_region_code;
    }
    if (branch_handling !== null) {
        requestData.branch_handling = branch_handling;
    }
    if (branch_name !== null) {
        requestData.branch_name = branch_name;
    }

    if (!company_name || (category === "0連鎖或相關企業的合開發票" && branch_handling === "以流水號編列此分行" && !branch_name)) {
        alert("公司名稱和分支名稱（若適用）不能為空。");
        return;
    }

    if (branch_handling === "00開立發票客編") {
        branch_name = ''; // 設置為空字符串
    }

    const response = await fetch(backendUrl + '/preview_customer_id', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
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
            body: JSON.stringify(requestData)
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

document.getElementById('update-form').addEventListener('submit', async function(event) {
    event.preventDefault();
    const customer_id = document.getElementById('update_customer_id').value;
    const new_company_name = document.getElementById('new_company_name').value;
    const new_branch_name = document.getElementById('new_branch_name').value;

    const requestData = {
        customer_id,
        new_company_name,
        new_branch_name
    };

    const response = await fetch(backendUrl + '/update_customer_info', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    });

    const result = await response.json();
    const updateResult = document.getElementById('update-result');
    if (response.ok) {
        updateResult.innerHTML = `更新成功: ${result.detail}`;
        updateResult.className = 'result';
    } else {
        updateResult.innerHTML = `更新失敗: ${result.detail}`;
        updateResult.className = 'error';
    }
});



async function searchCompanyName(keyword) {
    if (keyword.length < 1) {
        document.getElementById('company_name_list').innerHTML = '';
        return;
    }

    const response = await fetch(`${backendUrl}/search_all_company_names/?keyword=${keyword}`);
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
    if (keyword.length < 1) {
        document.getElementById('branch_name_list').innerHTML = '';
        return;
    }

    const response = await fetch(`${backendUrl}/search_all_branch_names/?keyword=${keyword}`);
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

document.getElementById('company_name').addEventListener('input', function() {
    searchCompanyName(this.value);
});

document.getElementById('branch_name').addEventListener('input', function() {
    searchBranchName(this.value);
});

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
        const headers = ['Region', 'Category', 'CompanyName', 'ExtraRegionCode', 'BranchName', 'CustomerID', 'Actions'];
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
                if (header === 'Actions') {
                    const editButton = document.createElement('button');
                    editButton.innerText = '修改';
                    editButton.addEventListener('click', () => {
                        enableEditing(tr, row.CustomerID);
                    });
                    td.appendChild(editButton);
                } else if (header === 'CompanyName' || header === 'BranchName') {
                    const span = document.createElement('span');
                    span.innerText = row[header];
                    span.dataset.field = header;
                    td.appendChild(span);
                } else {
                    td.innerText = row[header];
                }
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
                updatePagination();
            });
            if (i === currentPage) {
                button.classList.add('current-page');
            }
            pagination.appendChild(button);
        }
    }

    function updatePagination() {
        const buttons = pagination.querySelectorAll('button');
        buttons.forEach(button => {
            if (parseInt(button.innerText) === currentPage) {
                button.classList.add('current-page');
            } else {
                button.classList.remove('current-page');
            }
        });
    }

    renderTable(currentPage);
    renderPagination();
}

function populateUpdateForm(row) {
    document.getElementById('update_customer_id').value = row.CustomerID;
    document.getElementById('new_company_name').value = row.CompanyName;
    document.getElementById('new_branch_name').value = row.BranchName;
    document.getElementById('update-section').style.display = 'block';
}

function enableEditing(row, customerID) {
    const companyNameCell = row.querySelector('span[data-field="CompanyName"]');
    const branchNameCell = row.querySelector('span[data-field="BranchName"]');
    const actionsCell = row.querySelector('td:last-child');

    const companyNameInput = document.createElement('input');
    companyNameInput.type = 'text';
    companyNameInput.value = companyNameCell.innerText;
    companyNameInput.dataset.field = 'CompanyName';

    const branchNameInput = document.createElement('input');
    branchNameInput.type = 'text';
    branchNameInput.value = branchNameCell.innerText;
    branchNameInput.dataset.field = 'BranchName';

    companyNameCell.replaceWith(companyNameInput);
    branchNameCell.replaceWith(branchNameInput);

    actionsCell.innerHTML = '';
    const saveButton = document.createElement('button');
    saveButton.innerText = '儲存';
    saveButton.addEventListener('click', () => {
        updateCustomerInfo(customerID, row);
    });
    const cancelButton = document.createElement('button');
    cancelButton.innerText = '取消';
    cancelButton.addEventListener('click', () => {
        cancelEditing(row, companyNameCell, branchNameCell);
    });
    actionsCell.appendChild(saveButton);
    actionsCell.appendChild(cancelButton);
}

function cancelEditing(row, companyNameCell, branchNameCell) {
    const companyNameInput = row.querySelector('input[data-field="CompanyName"]');
    const branchNameInput = row.querySelector('input[data-field="BranchName"]');

    companyNameInput.replaceWith(companyNameCell);
    branchNameInput.replaceWith(branchNameCell);

    const actionsCell = row.querySelector('td:last-child');
    actionsCell.innerHTML = '';
    const editButton = document.createElement('button');
    editButton.innerText = '修改';
    editButton.addEventListener('click', () => {
        enableEditing(row, row.querySelector('td:last-child').dataset.customerId);
    });
    actionsCell.appendChild(editButton);
}

async function updateCustomerInfo(customerID, row) {
    const newCompanyName = row.querySelector('input[data-field="CompanyName"]').value;
    const newBranchName = row.querySelector('input[data-field="BranchName"]').value;

    const requestData = {
        customer_id: customerID,
        new_company_name: newCompanyName,
        new_branch_name: newBranchName
    };

    const response = await fetch(backendUrl + '/update_customer_info', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    });

    const result = await response.json();
    const updateResult = document.createElement('div');
    updateResult.className = response.ok ? 'result' : 'error';
    updateResult.innerText = response.ok ? `更新成功: ${result.detail}` : `更新失敗: ${result.detail}`;

    // 清除之前的更新結果提示
    const previousUpdateResult = row.querySelector('.result, .error');
    if (previousUpdateResult) {
        previousUpdateResult.remove();
    }

    row.querySelector('td:last-child').appendChild(updateResult);

    if (response.ok) {
        const companyNameCell = document.createElement('span');
        companyNameCell.innerText = newCompanyName;
        companyNameCell.dataset.field = 'CompanyName';

        const branchNameCell = document.createElement('span');
        branchNameCell.innerText = newBranchName;
        branchNameCell.dataset.field = 'BranchName';

        cancelEditing(row, companyNameCell, branchNameCell);
    }
}