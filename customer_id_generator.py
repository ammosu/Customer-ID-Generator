import pandas as pd
import os
import io
import logging
import boto3
from dotenv import load_dotenv

load_dotenv()

s3_bucket_name = os.getenv('S3_BUCKET_NAME')
s3_region = os.getenv('AWS_REGION')
s3_directory = os.getenv('S3_DIRECTORY')

s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=s3_region
)

class CustomerIDGenerator:
    def __init__(self, excel_file):
        self.excel_file = f"{s3_directory}/{excel_file}"
        if not self.file_exists_in_s3():
            self.data = pd.DataFrame(columns=['Region', 'Category', 'CompanyName', 'ExtraRegionCode', 'BranchName', 'BranchHandling', 'CustomerID'])
            self.save_to_s3()
        else:
            self.data = self.load_from_s3()

    def file_exists_in_s3(self):
        try:
            s3_client.head_object(Bucket=s3_bucket_name, Key=self.excel_file)
            return True
        except Exception as e:
            logging.error(f"Error checking if file exists in S3: {e}")
            return False

    def save_to_s3(self):
        try:
            with io.BytesIO() as output:
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    self.data.to_excel(writer, index=False)
                output.seek(0)
                s3_client.put_object(Bucket=s3_bucket_name, Key=self.excel_file, Body=output.read())
        except Exception as e:
            logging.error(f"Error saving to S3: {e}")

    def load_from_s3(self):
        try:
            response = s3_client.get_object(Bucket=s3_bucket_name, Key=self.excel_file)
            data = pd.read_excel(io.BytesIO(response['Body'].read()), engine='openpyxl')
            data['CustomerID'] = data['CustomerID'].astype(str)
            return data
        except Exception as e:
            logging.error(f"Error loading from S3: {e}")
            return pd.DataFrame(columns=['Region', 'Category', 'CompanyName', 'ExtraRegionCode', 'BranchName', 'BranchHandling', 'CustomerID'])

    def refresh_data(self):
        self.data = self.load_from_s3()

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
            self.save_to_s3()
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
