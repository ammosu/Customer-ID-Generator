# app.py
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
from customer_id_generator import CustomerIDGenerator

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
        valid_categories = ["連鎖或相關企業的合開發票", "連鎖或相關企業的不合開發票", "單一客戶", "機動", "未定", os.getenv('DACHING_RELATIONSHIP'), "其他"]
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

@app.post("/preview_customer_id")
def preview_customer_id(request: CustomerRequest):
    customer_id = generator.preview_customer_id(
        request.region, request.category, request.company_name, request.extra_region_code, request.branch_name)
    return {"customer_id": customer_id}

# 修改原有的生成ID的路由
@app.post("/generate_customer_id")
def generate_customer_id(request: CustomerRequest, confirm: bool = False):
    if confirm:
        customer_id = generator.generate_customer_id(
            request.region, request.category, request.company_name, request.extra_region_code, request.branch_name)
        return {"customer_id": customer_id, "status": "generated"}
    else:
        customer_id = generator.preview_customer_id(
            request.region, request.category, request.company_name, request.extra_region_code, request.branch_name)
        return {"customer_id": customer_id, "status": "preview"}

@app.get("/query_customer_id/{company_name}")
def query_customer_id(company_name: str):
    result = generator.query_customer_id(company_name)
    if result.empty:
        return {"detail": "Customer ID not found", "data": []}
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
    return ["連鎖或相關企業的合開發票", "連鎖或相關企業的不合開發票", "單一客戶", "機動", "未定", os.getenv('DACHING_RELATIONSHIP'), "其他"]

app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)
