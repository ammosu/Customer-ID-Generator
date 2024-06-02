from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator, ValidationInfo
import pandas as pd
import numpy as np
import os
import io
import logging
from typing import Optional
from dotenv import load_dotenv
from factory.data_access_factory import DataAccessFactory
from customer_id.customer_id_generator import CustomerIDGenerator

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)

# 使用工廠模式來創建 DataAccess 實例
data_access = DataAccessFactory.get_data_access(
    's3',
    bucket_name=os.getenv('S3_BUCKET_NAME'),
    directory=os.getenv('S3_DIRECTORY'),
    file_name='customer_ids.xlsx',
    region=os.getenv('AWS_REGION'),
    access_key=os.getenv('AWS_ACCESS_KEY_ID'),
    secret_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)
# 初始化 CustomerIDGenerator
generator = CustomerIDGenerator(data_access)

class CustomerRequest(BaseModel):
    region: str = Field(...)
    category: str = Field(...)
    company_name: str = Field(...)
    extra_region_code: Optional[str] = None
    branch_name: Optional[str] = None
    branch_handling: Optional[str] = None

    @field_validator('region')
    def region_must_be_valid(cls, v):
        valid_regions = ["1北投", "2台南", "3高雄"]
        if v not in valid_regions:
            raise ValueError('無效的地區')
        return v

    @field_validator('category')
    def category_must_be_valid(cls, v):
        valid_categories = ["0連鎖或相關企業的合開發票", "1連鎖或相關企業的不合開發票", "2單一客戶", "6機動", "7未定", f"8{os.getenv('DACHING_RELATIONSHIP')}", "9其他"]
        if v not in valid_categories:
            raise ValueError('無效的類別')
        return v

    @field_validator('extra_region_code', mode='before')
    def extra_region_code_must_be_valid(cls, v):
        valid_extra_region_codes = ["0無區分", "1本縣市", "2本縣市", "3本縣市", "4本縣市", "5外縣市", "6外縣市", "7外縣市", "8外縣市", "9外縣市"]
        if v not in valid_extra_region_codes:
            raise ValueError('無效的額外地區代碼')
        return v

    @field_validator('branch_name', mode='before')
    def branch_name_must_be_valid(cls, v, info: ValidationInfo):
        values = info.data
        category = values.get('category')
        branch_handling = values.get('branch_handling')
        
        if category == "0連鎖或相關企業的合開發票" and branch_handling == "以流水號編列此分行" and not v:
            raise ValueError('對於所選類別和分支處理，分支名稱是必需的。')
        return v if v is not None else ""

class UpdateCustomerRequest(BaseModel):
    customer_id: str = Field(...)
    new_company_name: Optional[str] = None
    new_branch_name: Optional[str] = None

class QueryCustomerRequest(BaseModel):
    company_name: str
    branch_handling: str = None

@app.post("/update_customer_info")
def update_customer_info(request: UpdateCustomerRequest):
    try:
        generator.update_customer_info(request.customer_id, request.new_company_name, request.new_branch_name)
        return {"detail": "客戶信息更新成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post("/import_excel")
async def import_excel(file: UploadFile = File(...)):
    content = await file.read()
    df = pd.read_excel(io.BytesIO(content), engine='openpyxl')
    df['CustomerID'] = df['CustomerID'].fillna('').astype(str)
    generator.data = pd.concat([generator.data, df], ignore_index=True).drop_duplicates(subset=['CustomerID'])
    generator.save_to_s3()
    generator.refresh_data()  # 刷新內存中的數據
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
        generator.refresh_data()  # 刷新內存中的數據
        logging.info(f"Deleted Customer ID: {customer_id}")
        return {"detail": "Customer ID deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Customer ID not found")

@app.post("/preview_customer_id")
def preview_customer_id(request: CustomerRequest):
    customer_id = generator.preview_customer_id(
        request.region, request.category, request.company_name, request.extra_region_code, request.branch_name, request.branch_handling)
    return {"customer_id": customer_id}

@app.post("/generate_customer_id")
def generate_customer_id(request: CustomerRequest, confirm: bool = False):
    if confirm:
        customer_id = generator.generate_customer_id(
            request.region, request.category, request.company_name, request.extra_region_code, request.branch_name, request.branch_handling)
        generator.refresh_data()  # 刷新內存中的數據
        return {"customer_id": customer_id, "status": "生成"}
    else:
        customer_id = generator.preview_customer_id(
            request.region, request.category, request.company_name, request.extra_region_code, request.branch_name, request.branch_handling)
        return {"customer_id": customer_id, "status": "預覽"}

@app.post("/query_customer_id")
def query_customer_id(request: QueryCustomerRequest):
    generator.refresh_data()  # 刷新內存中的數據
    result = generator.query_customer_id(request.company_name, request.branch_handling)
    if result.empty:
        return {"detail": "查無此客戶ID", "data": []}
    result = result.replace({np.inf: np.nan, -np.inf: np.nan}).fillna('')
    return {"detail": "查詢成功", "data": result.to_dict(orient='records')}

@app.get("/search_company_name/")
def search_company_name(keyword: str = Query(..., min_length=1), region: str = None, category: str = None):
    company_names = generator.search_company_name(keyword, region, category)
    return {"company_names": company_names}

@app.get("/search_all_company_names/")
def search_all_company_names(keyword: str = Query(..., min_length=1)):
    company_names = generator.search_company_name(keyword)
    return {"company_names": company_names}

@app.get("/search_all_branch_names/")
def search_all_branch_names(keyword: str = Query(..., min_length=1)):
    branch_names = generator.search_branch_name(keyword)
    return {"branch_names": branch_names}

@app.get("/search_all_customer_ids/")
def search_all_customer_ids(keyword: str = Query(..., min_length=1)):
    filtered_data = generator.data[generator.data['CustomerID'].str.contains(keyword, case=False, na=False)]
    customer_ids = filtered_data['CustomerID'].unique().tolist()
    return {"customer_ids": customer_ids}

@app.get("/search_branch_name/")
def search_branch_name(keyword: str = Query(..., min_length=1), region: str = None, category: str = None, company_name: str = None, extra_region_code: str = None):
    branch_names = generator.search_branch_name(keyword, region, category, company_name, extra_region_code)
    return {"branch_names": branch_names}

@app.get("/regions")
def get_regions():
    return ["1北投", "2台南", "3高雄"]

@app.get("/categories")
def get_categories():
    return ["0連鎖或相關企業的合開發票", "1連鎖或相關企業的不合開發票", "2單一客戶", "6機動", "7未定", f"8{os.getenv('DACHING_RELATIONSHIP')}", "9其他"]

@app.get("/extra_region_codes")
def get_extra_region_codes():
    return ["0無區分", "1本縣市", "2本縣市", "3本縣市", "4本縣市", "5外縣市", "6外縣市", "7外縣市", "8外縣市", "9外縣市"]

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse("static/favicon.ico")

app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)
