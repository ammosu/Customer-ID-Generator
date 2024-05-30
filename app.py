from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
import pandas as pd
import numpy as np
import os
import io
import logging
from dotenv import load_dotenv
import boto3

# 加載 .env 文件
load_dotenv()

# 獲取環境變數
daching_relationship = os.getenv('DACHING_RELATIONSHIP')
s3_bucket_name = os.getenv('S3_BUCKET_NAME')
s3_region = os.getenv('AWS_REGION')
s3_directory = os.getenv('S3_DIRECTORY')

# 初始化 S3 客戶端
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=s3_region
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)

class CustomerIDGenerator:
    def __init__(self, excel_file):
        self.excel_file = f"{s3_directory}/{excel_file}"  # 使用指定的S3目錄
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

    def load_from_s3(self):
        response = s3_client.get_object(Bucket=s3_bucket_name, Key=self.excel_file)
        return pd.read_excel(io.BytesIO(response['Body'].read()), engine='openpyxl')

    def generate_customer_id(self, region, category, company_name, extra_region_code=None, branch_name=None):
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
            daching_relationship: '8',
            '其他': '9'
        }

        region_code = region_codes.get(region, '0')
        category_code = category_codes.get(category, '9')

        if category_code in ['0', '1', daching_relationship]:
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

excel_file = 'customer_ids.xlsx'
generator = CustomerIDGenerator(excel_file)

class CustomerRequest(BaseModel):
    region: str
    category: str
    company_name: str
    extra_region_code: str = None
    branch_name: str = None

    @field_validator('region')
    def region_must_be_valid(cls, v):
        valid_regions = ["北投", "台南", "高雄"]
        if v not in valid_regions:
            raise ValueError('Invalid region')
        return v

    @field_validator('category')
    def category_must_be_valid(cls, v):
        valid_categories = ["連鎖或相關企業的合開發票", "連鎖或相關企業的不合開發票", "單一客戶", "機動", "未定", daching_relationship, "其他"]
        if v not in valid_categories:
            raise ValueError('Invalid category')
        return v

@app.post("/import_excel")
async def import_excel(file: UploadFile = File(...)):
    content = await file.read()
    df = pd.read_excel(io.BytesIO(content), engine='openpyxl')
    df['CustomerID'] = df['CustomerID'].fillna('').astype(str)
    generator.data = pd.concat([generator.data, df], ignore_index=True).drop_duplicates(subset=['CustomerID'])
    generator.save_to_s3()
    return {"detail": "Excel file imported successfully"}

@app.get("/export_excel")
def export_excel():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        generator.data.to_excel(writer, index=False)
    output.seek(0)
    headers = {
        'Content-Disposition': 'attachment; filename="customer_ids.xlsx"',
        'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    }
    return StreamingResponse(output, headers=headers)

@app.delete("/delete_customer_id/{customer_id}")
def delete_customer_id(customer_id: str):
    if customer_id in generator.data['CustomerID'].values:
        generator.data = generator.data[generator.data['CustomerID'] != customer_id]
        generator.save_to_s3()
        logging.info(f"Deleted Customer ID: {customer_id}")
        return {"detail": "Customer ID deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Customer ID not found")

@app.post("/generate_customer_id")
def generate_customer_id(request: CustomerRequest):
    customer_id = generator.generate_customer_id(
        request.region, request.category, request.company_name, request.extra_region_code, request.branch_name)
    return {"customer_id": customer_id}

@app.get("/query_customer_id/{company_name}")
def query_customer_id(company_name: str):
    result = generator.query_customer_id(company_name)
    if result.empty:
        return {"detail": "Customer ID not found", "data": []}
    # Clean the data to avoid JSON serialization issues
    result = result.replace({np.inf: np.nan, -np.inf: np.nan}).fillna('')
    return {"detail": "Customer ID found", "data": result.to_dict(orient='records')}

@app.get("/search_company_name/")
def search_company_name(keyword: str = Query(..., min_length=1), region: str = None, category: str = None):
    company_names = generator.search_company_name(keyword, region, category)
    return {"company_names": company_names}

@app.get("/search_branch_name/")
def search_branch_name(keyword: str = Query(..., min_length=1), region: str = None, category: str = None, company_name: str = None):
    branch_names = generator.search_branch_name(keyword, region, category, company_name)
    return {"branch_names": branch_names}

@app.get("/regions")
def get_regions():
    return ["北投", "台南", "高雄"]

@app.get("/categories")
def get_categories():
    return ["連鎖或相關企業的合開發票", "連鎖或相關企業的不合開發票", "單一客戶", "機動", "未定", daching_relationship, "其他"]

app.mount("/", StaticFiles(directory=".", html=True), name="static")

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app)