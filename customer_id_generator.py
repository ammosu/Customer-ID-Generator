# customer_id_generator.py
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
            self.data = pd.DataFrame(columns=['Region', 'Category', 'CompanyName', 'ExtraRegionCode', 'BranchName', 'CustomerID'])
            self.save_to_s3()
        else:
            self.data = self.load_from_s3()

    def file_exists_in_s3(self):
        try:
            s3_client.head_object(Bucket=s3_bucket_name, Key=self.excel_file)
            return True
        except:
            return False

    def save_to_s3(self):
        with io.BytesIO() as output:
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                self.data.to_excel(writer, index=False)
            output.seek(0)
            s3_client.put_object(Bucket=s3_bucket_name, Key=self.excel_file, Body=output.read())
            
    def refresh_data(self):
        self.data = self.load_from_s3()

    def load_from_s3(self):
        response = s3_client.get_object(Bucket=s3_bucket_name, Key=self.excel_file)
        return pd.read_excel(io.BytesIO(response['Body'].read()), engine='openpyxl')

    def preview_customer_id(self, region, category, company_name, extra_region_code=None, branch_name=None):
        self.data['CustomerID'] = self.data['CustomerID'].astype(str)
        existing_record = self.data[
            (self.data['Region'] == region) &
            (self.data['Category'] == category) &
            (self.data['CompanyName'] == company_name) &
            (self.data['ExtraRegionCode'] == extra_region_code) &
            (self.data['BranchName'] == branch_name)
        ]

        if not existing_record.empty:
            return existing_record['CustomerID'].iloc[0]

        region_codes = {'北投': '1', '台南': '2', '高雄': '3'}
        category_codes = {
            '連鎖或相關企業的合開發票': '0',
            '連鎖或相關企業的不合開發票': '1',
            '單一客戶': '2',
            '機動': '6',
            '未定': '7',
            os.getenv('DACHING_RELATIONSHIP'): '8',
            '其他': '9'
        }

        region_code = region_codes.get(region, '0')
        category_code = category_codes.get(category, '9')

        if category_code in ['0', '1', os.getenv('DACHING_RELATIONSHIP')]:
            existing_company = self.data[(self.data['Region'] == region) & (self.data['Category'] == category) & (self.data['CompanyName'] == company_name)]
            if not existing_company.empty:
                company_serial = existing_company['CustomerID'].iloc[0][2:5]
            else:
                max_serial = self.data[(self.data['Region'] == region) & (self.data['Category'] == category)]['CustomerID'].str[2:5].astype(int).max()
                company_serial = f"{(max_serial + 1) if pd.notna(max_serial) else 1:03d}"

            region_serial = '1' if extra_region_code == '本縣市' else '5'
            branch_serial = f"{len(existing_company) + 1:02d}" if branch_name else '00'

            customer_id = f"{region_code}{category_code}{company_serial}{region_serial}{branch_serial}"
        else:
            existing_company = self.data[(self.data['Region'] == region) & (self.data['Category'] == category) & (self.data['CompanyName'] == company_name)]
            if not existing_company.empty:
                company_serial = existing_company['CustomerID'].iloc[0][2:8]
            else:
                max_serial = self.data[(self.data['Region'] == region) & (self.data['Category'] == category)]['CustomerID'].str[2:8].astype(int).max()
                company_serial = f"{(max_serial + 1) if pd.notna(max_serial) else 1:06d}"

            customer_id = f"{region_code}{category_code}{company_serial}"

        return customer_id
    
    def generate_customer_id(self, region, category, company_name, extra_region_code=None, branch_name=None):
        self.data['CustomerID'] = self.data['CustomerID'].astype(str)
        existing_record = self.data[
            (self.data['Region'] == region) &
            (self.data['Category'] == category) &
            (self.data['CompanyName'] == company_name) &
            (self.data['ExtraRegionCode'] == extra_region_code) &
            (self.data['BranchName'] == branch_name)
        ]

        if not existing_record.empty:
            return existing_record['CustomerID'].iloc[0]

        region_codes = {'北投': '1', '台南': '2', '高雄': '3'}
        category_codes = {
            '連鎖或相關企業的合開發票': '0',
            '連鎖或相關企業的不合開發票': '1',
            '單一客戶': '2',
            '機動': '6',
            '未定': '7',
            os.getenv('DACHING_RELATIONSHIP'): '8',
            '其他': '9'
        }

        region_code = region_codes.get(region, '0')
        category_code = category_codes.get(category, '9')

        if category_code in ['0', '1', os.getenv('DACHING_RELATIONSHIP')]:
            existing_company = self.data[(self.data['Region'] == region) & (self.data['Category'] == category) & (self.data['CompanyName'] == company_name)]
            if not existing_company.empty:
                company_serial = existing_company['CustomerID'].iloc[0][2:5]
            else:
                max_serial = self.data[(self.data['Region'] == region) & (self.data['Category'] == category)]['CustomerID'].str[2:5].astype(int).max()
                company_serial = f"{(max_serial + 1) if pd.notna(max_serial) else 1:03d}"

            region_serial = '1' if extra_region_code == '本縣市' else '5'
            branch_serial = f"{len(existing_company) + 1:02d}" if branch_name else '00'

            customer_id = f"{region_code}{category_code}{company_serial}{region_serial}{branch_serial}"
        else:
            existing_company = self.data[(self.data['Region'] == region) & (self.data['Category'] == category) & (self.data['CompanyName'] == company_name)]
            if not existing_company.empty:
                company_serial = existing_company['CustomerID'].iloc[0][2:8]
            else:
                max_serial = self.data[(self.data['Region'] == region) & (self.data['Category'] == category)]['CustomerID'].str[2:8].astype(int).max()
                company_serial = f"{(max_serial + 1) if pd.notna(max_serial) else 1:06d}"

            customer_id = f"{region_code}{category_code}{company_serial}"

        new_entry = {
            'Region': region,
            'Category': category,
            'CompanyName': company_name,
            'ExtraRegionCode': extra_region_code,
            'BranchName': branch_name,
            'CustomerID': customer_id
        }
        self.data = pd.concat([self.data, pd.DataFrame([new_entry])], ignore_index=True)
        self.save_to_s3()
        logging.info(f"Generated Customer ID: {customer_id} for {company_name}")
        return customer_id

    def query_customer_id(self, company_name):
        result = self.data[self.data['CompanyName'] == company_name]
        return result

    def search_company_name(self, keyword: str, region: str = None, category: str = None):
        filtered_data = self.data
        if region:
            filtered_data = filtered_data[filtered_data['Region'] == region]
        if category:
            filtered_data = filtered_data[filtered_data['Category'] == category]
        result = filtered_data[filtered_data['CompanyName'].str.contains(keyword, case=False, na=False)]
        return result['CompanyName'].unique().tolist()

    def search_branch_name(self, keyword: str, region: str, category: str, company_name: str):
        filtered_data = self.data[
            (self.data['Region'] == region) &
            (self.data['Category'] == category) &
            (self.data['CompanyName'] == company_name)
        ]
        result = filtered_data[filtered_data['BranchName'].str.contains(keyword, case=False, na=False)]
        return result['BranchName'].unique().tolist()
