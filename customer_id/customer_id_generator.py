import os
import pandas as pd
import logging

class CustomerIDGenerator:
    def __init__(self, data_access):
        self.data_access = data_access
        if not self.data_access.file_exists():
            self.data = pd.DataFrame(columns=['Region', 'Category', 'CompanyName', 'ExtraRegionCode', 'BranchName', 'BranchHandling', 'CustomerID'])
            self.data_access.save(self.data)
        else:
            self.data = self.data_access.load()

    def refresh_data(self):
        self.data = self.data_access.load()

    def preview_customer_id(self, region, category, company_name, extra_region_code=None, branch_name=None, branch_handling=None):
        return self._generate_customer_id(region, category, company_name, extra_region_code, branch_name, branch_handling, preview=True)

    def generate_customer_id(self, region, category, company_name, extra_region_code=None, branch_name=None, branch_handling=None):
        customer_id = self._generate_customer_id(region, category, company_name, extra_region_code, branch_name, branch_handling, preview=False)
        if customer_id:
            if self._is_customer_id_exists(customer_id):
                logging.warning(f"Customer ID {customer_id} already exists. Skipping insertion.")
                return customer_id
            new_entry = {
                'Region': region,
                'Category': category,
                'CompanyName': company_name,
                'ExtraRegionCode': extra_region_code,
                'BranchName': branch_name,
                'BranchHandling': branch_handling,
                'CustomerID': customer_id
            }
            self.data = pd.concat([self.data, pd.DataFrame([new_entry])], ignore_index=True)
            self.data_access.save(self.data)
            logging.info(f"Generated Customer ID: {customer_id} for {company_name}")
        return customer_id

    def _is_customer_id_exists(self, customer_id):
        return not self.data[self.data['CustomerID'] == customer_id].empty

    def _generate_customer_id(self, region, category, company_name, extra_region_code=None, branch_name=None, branch_handling=None, preview=False):
        existing_record = self.data[
            (self.data['Region'] == region) &
            (self.data['Category'] == category) &
            (self.data['CompanyName'] == company_name) &
            (self.data['ExtraRegionCode'] == extra_region_code) &
            (self.data['BranchName'] == branch_name) &
            (self.data['BranchHandling'] == branch_handling)
        ]

        if not existing_record.empty:
            return existing_record['CustomerID'].iloc[0]

        region_codes = {'1北投': '1', '2台南': '2', '3高雄': '3'}
        category_codes = {
            '0連鎖或相關企業的合開發票': '0',
            '1連鎖或相關企業的不合開發票': '1',
            '2單一客戶': '2',
            '6機動': '6',
            '7未定': '7',
            f"8{os.getenv('DACHING_RELATIONSHIP')}": '8',
            '9其他': '9'
        }

        extra_region_codes = {
            "0無區分": "0", "1本縣市": "1", "2本縣市": "2", "3本縣市": "3",
            "4本縣市": "4", "5外縣市": "5", "6外縣市": "6", "7外縣市": "7",
            "8外縣市": "8", "9外縣市": "9"
        }

        region_code = region_codes.get(region, '0')
        category_code = category_codes.get(category, '9')
        region_serial = extra_region_codes.get(extra_region_code, '0')

        if category_code == '0' and branch_handling == '00開立發票客編':
            company_serial = self._get_company_serial(region, category, company_name, extra_region_code, 3)
            customer_id = f"{region_code}{category_code}{company_serial}{region_serial}00"
        elif category_code in ['0', '1', '8']:
            company_serial = self._get_company_serial(region, category, company_name, extra_region_code, 3)
            branch_serial = self._get_branch_serial(region, category, company_name, extra_region_code, branch_name)
            customer_id = f"{region_code}{category_code}{company_serial}{region_serial}{branch_serial}"
        else:
            company_serial = self._get_company_serial(region, category, company_name, extra_region_code, 6)
            customer_id = f"{region_code}{category_code}{company_serial}"

        if preview:
            return customer_id
        return customer_id

    def _get_company_serial(self, region, category, company_name, extra_region_code, length):
        existing_company = self.data[
            (self.data['Region'] == region) &
            (self.data['Category'] == category) &
            (self.data['CompanyName'] == company_name) &
            (self.data['ExtraRegionCode'] == extra_region_code)
        ]
        if not existing_company.empty:
            return existing_company['CustomerID'].iloc[0][2:2+length]
        max_serial = self.data[
            (self.data['Region'] == region) &
            (self.data['Category'] == category) &
            (self.data['ExtraRegionCode'] == extra_region_code)
        ]['CustomerID'].str[2:2+length].astype(int).max()
        return f"{(max_serial + 1) if pd.notna(max_serial) else 1:0{length}d}"

    def _get_branch_serial(self, region, category, company_name, extra_region_code, branch_name):
        existing_branches = self.data[
            (self.data['Region'] == region) &
            (self.data['Category'] == category) &
            (self.data['CompanyName'] == company_name) &
            (self.data['ExtraRegionCode'] == extra_region_code)
        ]
        if not existing_branches.empty:
            max_branch_serial = existing_branches['CustomerID'].str[-2:].astype(int).max()
            return f"{(max_branch_serial + 1) if pd.notna(max_branch_serial) else 1:02d}"
        return '00' if not branch_name else '01'

    def query_customer_id(self, company_name, branch_handling=None):
        result = self.data[self.data['CompanyName'] == company_name]
        if branch_handling:
            result = result[result['BranchHandling'] == branch_handling]
        return result

    def search_company_name(self, keyword: str):
        result = self.data[self.data['CompanyName'].str.contains(keyword, case=False, na=False)]
        return result['CompanyName'].unique().tolist()

    def search_branch_name(self, keyword: str):
        result = self.data[self.data['BranchName'].str.contains(keyword, case=False, na=False)]
        return result['BranchName'].unique().tolist()

    def update_customer_info(self, customer_id, new_company_name=None, new_branch_name=None):
        if customer_id not in self.data['CustomerID'].values:
            raise ValueError("客戶ID不存在")

        if new_company_name:
            self.data.loc[self.data['CustomerID'] == customer_id, 'CompanyName'] = new_company_name
        if new_branch_name:
            self.data.loc[self.data['CustomerID'] == customer_id, 'BranchName'] = new_branch_name

        self.data_access.save(self.data)
        logging.info(f"Updated Customer ID: {customer_id} with new company name: {new_company_name} and new branch name: {new_branch_name}")
