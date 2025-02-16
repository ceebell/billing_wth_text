from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import httpx
import re
from typing import Optional, Dict, List
from pydantic import BaseModel

from datetime import datetime
from date_extractor import extract_dates_from_text 
from config import API_HEADERS, API_URLS, DEFAULT_BRANCH_ID, allows_users

from middleware import AuthMiddleware
from jwt_utils import jwt_utils 
import json

from fastapi.responses import RedirectResponse



app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")



# Login routes
@app.get("/login")
async def login_page(request: Request):
    """แสดงหน้า login"""
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )

@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """จัดการการ login"""
    try:
        # เรียก Login API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://shop.alexrental.app/api/user/login",
                json={
                    "username": username,
                    "password": password
                }
            )
            
            if username not in allows_users:
                # กรณี login ไม่สำเร็จ
                return templates.TemplateResponse(
                    "login.html",
                    {
                        "request": request,
                        "error": "Login failed. Please try again.",
                        "username": username
                    }
                )
                

            
            if response.status_code == 200:
                user_data = response.json()
                print(f"user_data >>> {user_data}")
                
                # เก็บข้อมูล user
                jwt_utils.store_user_info(user_data)
                
                
                token = request.cookies.get("auth_token")
                API_HEADERS["Authorization"] = f"Bearer {token}"
                
                # redirect พร้อม set cookie
                redirect = RedirectResponse(url="/", status_code=303)
                redirect.set_cookie(
                    key="auth_token",
                    value=user_data["token"],
                    httponly=True,
                    max_age=1800  # 30 minutes
                )
                return redirect
                
            # กรณี login ไม่สำเร็จ
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "error": "Login failed. Please try again.",
                    "username": username
                }
            )
            
    except Exception as e:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": str(e),
                "username": username
            }
        )
        
@app.post("/logout")
async def logout():
    """จัดการการออกจากระบบ"""
    response = RedirectResponse(url="/login", status_code=303)
    # Clear the cookie
    response.delete_cookie("auth_token")
    return response      
        
# ตัวอย่างการใช้งานใน route อื่น
@app.get("/protected")
async def protected_route(request: Request):
    # ดึง token จาก cookie
    token = request.cookies.get("auth_token")
    if not token or jwt_utils.is_token_expired(token):
        return RedirectResponse(url="/login")
    
    # ดึงข้อมูล user
    user = jwt_utils.get_user_info(token)
    branch_id = jwt_utils.get_branch_id(token)
    is_admin = jwt_utils.is_admin(token)
    
    return {
        "username": user.username,
        "branch_id": branch_id,
        "is_admin": is_admin
    }

# Import other modules and routes...


app.mount("/static", StaticFiles(directory="static"), name="static")

# API Configuration
API_TOKEN = ""
API_HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Prepare API configuration for frontend
api_config = {
    "headers": API_HEADERS,
    "urls": API_URLS
}

# Model สำหรับการเช็คคิว
class QueueCheckItem(BaseModel):
    productItemId: str
    pickupDate: str
    returnDate: str
    branchId: str = "9592dbbe-bbb7-48d6-bc32-d2902a5b5a6a"
    qty: int = 1
class QueueCheckResponse(BaseModel):
    result: int  # 0 = ไม่ว่าง, 1 = ว่าง
    message: Optional[str] = None

# ปรับ Model สำหรับ Queue Check
# ปรับ Model สำหรับ Queue Check
class QueueCheckResult(BaseModel):
    success: bool
    result: Optional[int] = None  # 0 = ไม่ว่าง, 1 = ว่าง
    message: Optional[str] = None

async def check_queue(product_id: str, pickup_date: str, return_date: str) -> QueueCheckResult:
    """
    Check product queue availability
    Returns:
        QueueCheckResult with:
        - success: API call success status
        - result: 1 = available, 0 = unavailable
        - message: Additional message or error detail
    """
    url = "https://shop.alexrental.app/api/orderdetail/checkq"
    
    check_items = [
        {
            "productItemId": product_id,
            "pickupDate": pickup_date,
            "returnDate": return_date,
            "branchId": "9592dbbe-bbb7-48d6-bc32-d2902a5b5a6a",
            "qty": 1
        }
    ]
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=check_items,
                headers=API_HEADERS
            )
            
            if response.status_code == 200:
                response_data = response.json()
                # เก็บ response_data ไว้ใน result
                # if isinstance(response_data, list) and len(response_data) > 0:
                #     first_item = response_data[0]
                #     if isinstance(first_item, dict):
                #         return QueueCheckResult(
                #             success=True,
                #             result=first_item.get('result', 0),
                #             message=first_item.get('message', 'ไม่สามารถจองได้ในช่วงเวลานี้'),
                #             raw_response=response_data  # เก็บ response ดิบ
                #         )
                
                # print(f"CEHCK QUQUQUQUQU RESP >>> {response_data}")
                
                return response_data
            else:
                return QueueCheckResult(
                    success=False,
                    result=0,
                    message=f"API Error: Status code {response.status_code}",
                    raw_response=None
                )
                
    except Exception as e:
        return QueueCheckResult(
            success=False,
            result=0,
            message=f"Error: {str(e)}"
        )

# Example of handling different response formats:
def parse_queue_check_response(response_data) -> QueueCheckResult:
    """Helper function to parse different response formats"""
    try:
        if isinstance(response_data, list):
            if len(response_data) > 0:
                first_item = response_data[0]
                if isinstance(first_item, dict):
                    return QueueCheckResult(
                        success=True,
                        result=first_item.get('result', 0),
                        message=first_item.get('message', 'ไม่สามารถจองได้ในช่วงเวลานี้')
                    )
                else:
                    return QueueCheckResult(
                        success=False,
                        result=0,
                        message="Invalid response format"
                    )
            else:
                return QueueCheckResult(
                    success=False,
                    result=0,
                    message="Empty response"
                )
        elif isinstance(response_data, dict):
            return QueueCheckResult(
                success=True,
                result=response_data.get('result', 0),
                message=response_data.get('message', 'ไม่สามารถจองได้ในช่วงเวลานี้')
            )
        else:
            return QueueCheckResult(
                success=False,
                result=0,
                message="Unexpected response format"
            )
    except Exception as e:
        return QueueCheckResult(
            success=False,
            result=0,
            message=f"Error parsing response: {str(e)}"
        )





# Pydantic models
class ProductSearchRequest(BaseModel):
    filter: bool = True
    pageNumber: int = 1
    pageSize: int = 50
    showNotAvailable: bool = True
    branchId: str = "9592dbbe-bbb7-48d6-bc32-d2902a5b5a6a"
    keyword: str
    color: Optional[str] = None
    size: Optional[str] = None
    simpleSearch: bool = False

class ProductItem(BaseModel):
    productItemId: str
    name: str
    code: str
    size: Optional[str]
    color: Optional[str]
    rentalPrice: float
    bail: float
    mainImage: Optional[str] = None 
    queue_check: Optional[QueueCheckResult] = None  # เพิ่มฟิลด์นี้
    rental_discount: Optional[float] = None  # เพิ่มส่วนลดค่าเช่า
    bail_discount: Optional[float] = None  # เพิ่มส่วนลดค่าประกัน

class SummaryPrices(BaseModel):
    rental_price: Optional[float] = None
    bail_price: Optional[float] = None
    
class RentalDates(BaseModel):
    pickup_date: Optional[str] = None
    return_date: Optional[str] = None
    
class QueueCheckResult(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[List[Dict]] = None

class SearchResult(BaseModel):
    success: bool
    message: str
    # item: Optional[ProductItem] = None           # ใช้ในกรณีมีรายการเดียว (หรือเพื่ออ้างอิงหลังจากเลือก)
    items: Optional[List[ProductItem]] = None      # สำหรับเก็บรายการสินค้าทั้งหมด
    summary_prices: Optional[SummaryPrices] = None
    rental_dates: Optional[RentalDates] = None
    queue_check: Optional[QueueCheckResult] = None
    search_params: Optional[dict] = None           # สำหรับเก็บ mapping parameters เมื่อไม่พบ code
    
    
# def convert_buddhist_year(year_str: str) -> str:
#     """Convert Buddhist year to Christian year"""
#     if len(year_str) == 2:
#         buddhist_year = int('25' + year_str)
#     else:
#         buddhist_year = int(year_str)
#     return str(buddhist_year - 543)

# def convert_thai_month(thai_month: str) -> str:
#     """Convert Thai month abbreviation to month number"""
#     month_mapping = {
#         'ม.ค.': '01', 'ก.พ.': '02', 'มี.ค.': '03', 'เม.ย.': '04',
#         'พ.ค.': '05', 'มิ.ย.': '06', 'ก.ค.': '07', 'ส.ค.': '08',
#         'ก.ย.': '09', 'ต.ค.': '10', 'พ.ย.': '11', 'ธ.ค.': '12',
#         'มกราคม': '01', 'กุมภาพันธ์': '02', 'มีนาคม': '03', 'เมษายน': '04',
#         'พฤษภาคม': '05', 'มิถุนายน': '06', 'กรกฎาคม': '07', 'สิงหาคม': '08',
#         'กันยายน': '09', 'ตุลาคม': '10', 'พฤศจิกายน': '11', 'ธันวาคม': '12'
#     }
#     return month_mapping.get(thai_month, '01')

# def extract_dates_from_text(text: str) -> Dict[str, Optional[str]]:
#     """
#     Extract pickup and return dates from summary text.
#     Returns dates in YYYY-MM-DD format.
#     """
#     dates = {
#         'pickup_date': None,
#         'return_date': None
#     }

#     # คำที่ใช้ระบุวันรับชุด
#     pickup_keywords = r'(?:วันรับชุด|รับชุด|ลูกค้ารับชุด)'
    
#     # คำที่ใช้ระบุวันคืนชุด
#     return_keywords = r'(?:วันคืนชุด|คืนชุด|ลูกค้าส่งชุดคืน|ส่งคืน)'

#     # Pattern สำหรับวันที่
#     date_pattern = r'\s*:?\s*(\d{1,2})\s*(ม\.ค\.|ก\.พ\.|มี\.ค\.|เม\.ย\.|พ\.ค\.|มิ\.ย\.|ก\.ค\.|ส\.ค\.|ก\.ย\.|ต\.ค\.|พ\.ย\.|ธ\.ค\.)\s*(\d{2,4})'
    
#     # Pattern สำหรับเวลา
#     time_pattern = r'(\d{1,2}:\d{2})'

#     # แยกข้อความเป็นบรรทัด
#     lines = text.split('\n')
    
#     for line in lines:
#         # ค้นหาวันรับชุด
#         pickup_match = re.search(f"{pickup_keywords}{date_pattern}", line, re.IGNORECASE)
#         if pickup_match:
#             day = pickup_match.group(1).zfill(2)
#             month = convert_thai_month(pickup_match.group(2))
#             year = convert_buddhist_year(pickup_match.group(3))
#             dates['pickup_date'] = f"{year}-{month}-{day}"

#         # ค้นหาวันคืนชุด
#         return_match = re.search(f"{return_keywords}{date_pattern}", line, re.IGNORECASE)
#         if return_match:
#             day = return_match.group(1).zfill(2)
#             month = convert_thai_month(return_match.group(2))
#             year = convert_buddhist_year(return_match.group(3))
#             dates['return_date'] = f"{year}-{month}-{day}"
            
#             # ค้นหาเวลา (ถ้ามี)
#             time_match = re.search(time_pattern, line)
#             if time_match:
#                 dates['return_time'] = time_match.group(1)

#     return dates
    
def extract_code_from_text(text: str) -> Optional[str]:
    """
    Extract product code from summary text.
    Pattern: 'code:' followed by one or more spaces, 
    then alphanumeric characters until next space
    """
    pattern = r'code:\s+([^\s]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

def extract_prices_from_text(text: str) -> SummaryPrices:
    """Extract rental and bail prices from summary text."""
    rental_pattern = r'ค่าเช่า\s+(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+(?:\.\d{2})?)\s*บาท'
    bail_pattern = r'ค่าประกัน\s+(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+(?:\.\d{2})?)\s*บาท'
    
    rental_price = None
    bail_price = None
    
    # Find rental price
    rental_match = re.search(rental_pattern, text)
    if rental_match:
        price_str = rental_match.group(1).replace(',', '')
        rental_price = float(price_str)
    
    # Find bail price
    bail_match = re.search(bail_pattern, text)
    if bail_match:
        price_str = bail_match.group(1).replace(',', '')
        bail_price = float(price_str)
    
    return SummaryPrices(rental_price=rental_price, bail_price=bail_price)

# [V1.0]
# async def search_product(code: str) -> SearchResult:
#     """Search product from API."""
#     url = "https://shop.alexrental.app/api/v2/GetProductItems"
#     search_data = ProductSearchRequest(keyword=code)
    
#     try:
#         async with httpx.AsyncClient() as client:
#             response = await client.post(
#                 url, 
#                 json=search_data.dict(),
#                 headers=API_HEADERS
#             )
            
#             if response.status_code == 401:
#                 return SearchResult(
#                     success=False,
#                     message="Authentication error: Invalid token",
#                     summary_prices=SummaryPrices()
#                 )
            
#             if response.status_code != 200:
#                 return SearchResult(
#                     success=False,
#                     message=f"API Error: Status code {response.status_code}",
#                     summary_prices=SummaryPrices()
#                 )
            
#             data = response.json()
            
#             if not data.get("itemList") or len(data["itemList"]) == 0:
#                 return SearchResult(
#                     success=False,
#                     message="ไม่พบข้อมูลสินค้า",
#                     summary_prices=SummaryPrices()
#                 )
            
#             item = data["itemList"][0]
            
#             if item["code"] != code:
#                 return SearchResult(
#                     success=False,
#                     message=f"รหัสสินค้าไม่ตรงกัน (ได้รับ: {item['code']}, ต้องการ: {code})",
#                     summary_prices=SummaryPrices()
#                 )
            
#             return SearchResult(
#                 success=True,
#                 message="พบข้อมูลสินค้า",
#                 item=ProductItem(
#                     productItemId=item["productItemId"],
#                     name=item["name"],
#                     code=item["code"],
#                     rentalPrice=item["rentalPrice"],
#                     bail=item["bail"],
#                     mainImage=item["mainImage"]
#                 ),
#                 summary_prices=SummaryPrices()
#             )
            
#     except Exception as e:
#         return SearchResult(
#             success=False,
#             message=f"Error: {str(e)}",
#             summary_prices=SummaryPrices()
#         )


# [V2.0]
async def search_product(summary_text: str) -> SearchResult:
    """Search product from API."""
    url = "https://shop.alexrental.app/api/v2/GetProductItems"
    code = extract_code_from_text(summary_text)
    
    if not code:
        search_params = extract_search_params(summary_text)
        print(f"search_params >>> {search_params}")
        search_data = ProductSearchRequest(**search_params)
        print(f"search_data >>> {search_data}")
    else:
        search_data = ProductSearchRequest(keyword=code)
        print(f"search_data >>> {search_data}")
    

    print(f"search_data >>> {search_data}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, 
                json=search_data.dict(),
                headers=API_HEADERS
            )
            
            # print(f"API_HEADERS >>> {API_HEADERS}")
            
            if response.status_code == 401:
                return SearchResult(
                    success=False,
                    message="Authentication error: Invalid token",
                    summary_prices=SummaryPrices()
                )
            
            if response.status_code != 200:
                return SearchResult(
                    success=False,
                    message=f"API Error: Status code {response.status_code}",
                    summary_prices=SummaryPrices()
                )
            
            data = response.json()
            items_data = data.get("itemList")
            if not items_data or len(items_data) == 0:
                return SearchResult(
                    success=False,
                    message="ไม่พบข้อมูลสินค้า",
                    summary_prices=SummaryPrices()
                )
            
            product_items = []
            for item in items_data:
                product_item = ProductItem(
                    productItemId=item["productItemId"],
                    name=item["name"],
                    code=item["code"],
                    color=item["color"],
                    size=item["size"],
                    rentalPrice=item["rentalPrice"],
                    bail=item["bail"],
                    mainImage=item.get("mainImage")
                )
                product_items.append(product_item)
                
            # print(f"product_items >>> {product_items}")
            
            return SearchResult(
                success=True,
                message="พบข้อมูลสินค้า",
                items=product_items,
                summary_prices=SummaryPrices()
            )
            
    except Exception as e:
        return SearchResult(
            success=False,
            message=f"Error: {str(e)}",
            summary_prices=SummaryPrices()
        )


async def search_product_with_code(code: str) -> SearchResult:
    """Search product from API."""
    url = "https://shop.alexrental.app/api/v2/GetProductItems"
    search_data = ProductSearchRequest(keyword=code)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, 
                json=search_data.dict(),
                headers=API_HEADERS
            )
            
            if response.status_code == 401:
                return SearchResult(
                    success=False,
                    message="Authentication error: Invalid token",
                    summary_prices=SummaryPrices()
                )
            
            if response.status_code != 200:
                return SearchResult(
                    success=False,
                    message=f"API Error: Status code {response.status_code}",
                    summary_prices=SummaryPrices()
                )
            
            data = response.json()
            
            
            
            if not data.get("itemList") or len(data["itemList"]) == 0:
                return SearchResult(
                    success=False,
                    message="ไม่พบข้อมูลสินค้า",
                    summary_prices=SummaryPrices()
                )
            
            item = data["itemList"][0]
            
            if item["code"] != code:
                return SearchResult(
                    success=False,
                    message=f"รหัสสินค้าไม่ตรงกัน (ได้รับ: {item['code']}, ต้องการ: {code})",
                    summary_prices=SummaryPrices()
                )
            
            return SearchResult(
                success=True,
                message="พบข้อมูลสินค้า",
                items=[ProductItem(
                    productItemId=item["productItemId"],
                    name=item["name"],
                    code=item["code"],
                    color=item["color"],
                    size=item["size"],
                    rentalPrice=item["rentalPrice"],
                    bail=item["bail"],
                    mainImage=item["mainImage"]
                )],
                summary_prices=SummaryPrices()
            )
            
    except Exception as e:
        return SearchResult(
            success=False,
            message=f"Error: {str(e)}",
            summary_prices=SummaryPrices()
        )


@app.get("/")
async def home(request: Request):
    # ตรวจสอบว่า auth_token มีอยู่ใน cookie หรือไม่
    token = request.cookies.get("auth_token")
    if not token:
        # ถ้าไม่มี token ให้ redirect ไปยังหน้า login
        return RedirectResponse(url="/login", status_code=303)
    
    # หากมี token ให้แสดงหน้า search.html
    return templates.TemplateResponse(
        "search.html",
        {"request": request}
    )




def extract_search_params(text: str) -> dict:
    """
    สกัด mapping parameters จากข้อความสรุปยอด
    โดยจะค้นหาบรรทัดที่ขึ้นต้นด้วย "ชื่อ"
    และสกัด category จาก token แรก และ keyword จาก token ที่สอง
    """
    lines = text.splitlines()
    for line in lines:
        if line.strip().startswith("ชื่อ"):
            content = line.strip()[len("ชื่อ"):].strip()  # ลบคำว่า "ชื่อ"
            parts = content.split('/')
            if len(parts) >= 3:
                category = parts[0].strip()
                keyword = parts[1].strip()
                size_raw = parts[3].strip() if len(parts) >= 4 else ""
                size_param = ""
                if size_raw.lower().startswith("size"):
                    size_param = size_raw[len("size"):].strip()
                else:
                    size_param = size_raw
                    
                # แปลงค่า size ให้เป็นตัวพิมพ์ใหญ่
                if size_param in ["one size", "onesize", "ONE SIZE", "One size"]:
                    size_param = "OS"
                    
                size_param = size_param.upper()
                
                print(f"keyword >>> {keyword}")
                print(f"size_param >>> {size_param}")
                
                print(f"keyword >>> {keyword}")
                
                return {
                    "filter": True,
                    "showNotAvailable": False,
                    "branchId": "9592dbbe-bbb7-48d6-bc32-d2902a5b5a6a",
                    "keyword": keyword,
                    "size": size_param,        # หากต้องการสกัดข้อมูลเพิ่มเติม สามารถปรับแก้ได้
                    "color": "",
                    "category": "",
                    "texture": "",
                    "simpleSearch": False,
                    "pageNumber": 1,
                    "pageSize": 15
                }
            break
    return {}


# [V2.0]
@app.post("/search")
async def search(request: Request, summary_text: str = Form(...)):
    
    
    token = request.cookies.get("auth_token")
    user = jwt_utils.get_user_info(token)
    API_HEADERS["Authorization"] = f"Bearer {token}"
    
    selected_products = []
    
    order_json = None  # Default value for order_json
    
    summary_text = summary_text.replace("(blue dot dress)", "note:")
    
    # Extract code from summary text
    code = extract_code_from_text(summary_text)

    # IN CASE: PRODUCT CODE IS FOUND
    if code:
        print(f"CODEEEEEEEEEEEEEEEEEEEE >>> {code}")
        result = await search_product_with_code(code)
        print(f"result >>> {result}")
        selected_products = result.items
        
        
        print(f"selected_products >>> {selected_products}")
        
        # ดึงข้อมูลราคาและวันที่จาก summary_text (ถ้ามี)
        summary_prices = extract_prices_from_text(summary_text) if summary_text else None
        rental_dates_dict = extract_dates_from_text(summary_text) if summary_text else {}
        rental_dates = RentalDates(**rental_dates_dict) if rental_dates_dict else None
        
        
        # หากมีวันที่รับและคืน ให้ทำการเช็ค queue และคำนวณส่วนลดสำหรับทุกชิ้น
        if rental_dates and rental_dates_dict.get('pickup_date') and rental_dates_dict.get('return_date'):
            
            for product in selected_products:
                # เช็คคิวสำหรับแต่ละสินค้า
                queue_result = await check_queue(
                    product.productItemId,
                    rental_dates_dict['pickup_date'],
                    rental_dates_dict['return_date']
                )
                
               
                product.queue_check = queue_result
                
                # คำนวณส่วนลด สำหรับค่าเช่า และค่าประกัน
                if summary_prices:
                    product.rental_discount = product.rentalPrice - summary_prices.rental_price if summary_prices.rental_price is not None else 0
                    product.bail_discount = product.bail - summary_prices.bail_price if summary_prices.bail_price is not None else 0

                order_json = create_order_json(summary_text, {
                        "item": selected_products[0].dict(),
                        "summary_prices": summary_prices.dict(),
                        "rental_dates": rental_dates.dict()
                    })
        
        return templates.TemplateResponse(
            "view_information.html",
            {
                    "request": request,
                    "result": {
                        "products": selected_products,
                        "summary_prices": summary_prices,
                        "rental_dates": rental_dates
                    },
                    "summary_text": summary_text.strip(),
                    "order_json": order_json,         
                    "api_config": api_config
            }
        )
        
        
    
    # ดึงข้อมูลราคาและวันที่จากข้อความสรุปยอด
    summary_prices = extract_prices_from_text(summary_text)
    rental_dates = extract_dates_from_text(summary_text)
    
    # ค้นหาสินค้าจาก API
    result = await search_product(summary_text)
    
    
    # print(f"result >>> {result}")
    
    # if result.success:
    #     result.summary_prices = summary_prices
    #     result.rental_dates = RentalDates(**rental_dates)
        
    #     # หากพบรายการสินค้าเพียงรายการเดียว ให้ทำการตรวจสอบ queue
    #     if result.items and len(result.items) == 1:
    #         product = result.items[0]
    #         result.item = product  # สำหรับใช้อ้างอิงในส่วนอื่น ๆ
    #         if rental_dates.get('pickup_date') and rental_dates.get('return_date'):
    #             queue_result = await check_queue(
    #                 product.productItemId,
    #                 rental_dates['pickup_date'],
    #                 rental_dates['return_date']
    #             )
    #             result.queue_check = queue_result
    #             order_json = create_order_json(summary_text, {
    #                 "item": product.dict(),
    #                 "summary_prices": summary_prices.dict(),
    #                 "rental_dates": rental_dates
    #             })
    #     # หากพบหลายรายการ เราแค่แสดงรายการให้เลือก (ไม่ตรวจ queue อัตโนมัติ)
    # else:
    #     # กรณีค้นหาไม่สำเร็จก็ยังใส่ข้อมูลวันที่ไว้
    #     result.rental_dates = RentalDates(**rental_dates)
    
    
    if result.success:
        result.summary_prices = summary_prices
        result.rental_dates = RentalDates(**rental_dates)
        
        # หากมีวันที่รับและคืน ให้ทำการเช็ค queue สำหรับสินค้าทุกชิ้น
        if result.items and rental_dates.get('pickup_date') and rental_dates.get('return_date'):
            queue_checks = []
            for product in result.items:
                queue_result = await check_queue(
                    product.productItemId,
                    rental_dates['pickup_date'],
                    rental_dates['return_date']
                )
                # เพิ่ม attribute queue_check ให้กับ product (เพื่อส่งไปแสดงใน template)
                product.queue_check = queue_result
                queue_checks.append(queue_result)
            # เก็บผลลัพธ์ทั้งหมดไว้ใน result.queue_check (เป็น list ของผลลัพธ์การเช็ค)
            result.queue_check = queue_checks
            
            # ถ้ามีแค่สินค้าเดียว ให้กำหนด result.item และสร้าง order_json ได้ (ตามที่เคยทำ)
            # if len(result.items) == 1:
            #     result.item = result.items[0]
            #     order_json = create_order_json(summary_text, {
            #         "item": result.items[0].dict(),
            #         "summary_prices": summary_prices.dict(),
            #         "rental_dates": rental_dates
            #     })
    else:
        # กรณีค้นหาไม่สำเร็จ ก็ยังใส่ข้อมูลวันที่ไว้
        result.rental_dates = RentalDates(**rental_dates)
    
        
    return templates.TemplateResponse(
        "search.html",
        {
            "request": request,
            "result": result,
            "summary_text": summary_text.strip(),
            "order_json": order_json,
            "api_config": api_config
        }
    )
    
 
async def get_product_detail(request: Request, productCode: str) -> ProductItem:
    """
    Fetch detailed product information from the API using product_id.
    Adjust the method and payload according to the API documentation.
    """
    # Check if the correct URL is provided
    print(f"productCode >>> {productCode}")
    
    url = "https://shop.alexrental.app/api/v2/GetProductItems"
    
    params = ProductSearchRequest(keyword=productCode) 
    
    


    # print(f"params >>> {params}  type >>> {type(params)}")

    token = request.cookies.get("auth_token")
    API_HEADERS["Authorization"] = f"Bearer {token}"
    
    try:
        async with httpx.AsyncClient() as client:
            # Try using GET instead of POST if that's required
            response = await client.post(url, json=params.dict(), headers=API_HEADERS)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=f"Error fetching product detail: {response.status_code}")
            data = response.json()
            
            
            
            dataItem = data["itemList"][0]
            
            product_detail = ProductItem(
                productItemId=dataItem["productItemId"],
                name=dataItem["name"],
                code=dataItem["code"],
                size=dataItem.get("size"),
                color=dataItem.get("color"),
                rentalPrice=dataItem["rentalPrice"],
                bail=dataItem["bail"],
                mainImage=dataItem.get("mainImage")
            )
            
            print(f"data of RESPONSE  product_detail >>> {product_detail}")
            
            return product_detail
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching product detail: {str(e)}")


# [V2.0]
@app.post("/view-information")
async def view_information(
        request: Request, 
        productCodes: List[str] = Form(...), 
        summary_text: str = Form(...)
    ):
    """
    แสดงหน้ารายละเอียดสินค้าที่เลือกไว้
    productIds: เป็น comma-separated string ของ productItemId ที่เลือกไว้
    summary_text: สามารถส่งข้อมูลสรุปยอดเพื่อดึงข้อมูลราคา/วันที่ (ถ้ามี)
    """
    
    order_json = None  # Default value for order_json
    summary_text = summary_text.replace("(blue dot dress)", "note:")
    # print(f"summary_text >>> {summary_text}")
    
    # ทำการแปลง List[str] เป็น comma-separated string หรือวนลูปตามที่ต้องการ
    # ตัวอย่างเช่น:
    # print("Product Codes:", productCodes)
    # ดึงรายละเอียดของสินค้าตามที่เลือกไว้
    selected_products = []
    for pcode in productCodes:
        product_detail = await get_product_detail(request, pcode)
        selected_products.append(product_detail)
        
        
    
    # ดึงข้อมูลราคาและวันที่จาก summary_text (ถ้ามี)
    summary_prices = extract_prices_from_text(summary_text) if summary_text else None
    rental_dates_dict = extract_dates_from_text(summary_text) if summary_text else {}
    rental_dates = RentalDates(**rental_dates_dict) if rental_dates_dict else None

    # หากมีวันที่รับและคืน ให้ทำการเช็ค queue และคำนวณส่วนลดสำหรับทุกชิ้น
    if rental_dates and rental_dates_dict.get('pickup_date') and rental_dates_dict.get('return_date'):
        
        
        for product in selected_products:
            # เช็คคิวสำหรับแต่ละสินค้า
            queue_result = await check_queue(
                product.productItemId,
                rental_dates_dict['pickup_date'],
                rental_dates_dict['return_date']
            )
            
            # print(f"VIEW::: CEHCK QUQUQUQUQU RESP >>> {queue_result}")
            
            # เพิ่ม attribute queue_check ให้กับ product
            product.queue_check = queue_result
            
            # คำนวณส่วนลด สำหรับค่าเช่า และค่าประกัน
            if summary_prices:
                product.rental_discount = product.rentalPrice - summary_prices.rental_price if summary_prices.rental_price is not None else 0
                product.bail_discount = product.bail - summary_prices.bail_price if summary_prices.bail_price is not None else 0

            order_json = create_order_json(summary_text, {
                    "item": selected_products[0].dict(),
                    "summary_prices": summary_prices.dict(),
                    "rental_dates": rental_dates.dict()
                })
    
    # print(f"order_json >>> {order_json}")
    # print(f"summary_prices >>> {summary_prices}")
    # print(f"rental_dates >>> {rental_dates}")
    
    
    
    
    
    
    return templates.TemplateResponse(
        "view_information.html",
        {
                "request": request,
                "result": {
                    "products": selected_products,
                    "summary_prices": summary_prices,
                    "rental_dates": rental_dates
                },
                "summary_text": summary_text.strip(),
                "order_json": order_json,         
                "api_config": api_config
        }
    )
   

# [v1.0]
# @app.post("/view-information")
# async def view_information(
#     request: Request, 
#     summary_text: str = Form(...),
#     productCodes: List[str] = Form(...)
# ):
#     print("<<<<<<<<<<<<<<<< U R IN /view-information/ >>>>>>>>>>>>>>>>")
#     product_details = []
#     for productCode in productCodes:
#         product_detail = await get_product_detail(request, productCode)
#         product_details.append(product_detail)
#         print(f"product_detail >>> {product_detail}")
    
#     return templates.TemplateResponse(
#         "view_information.html",
#         {
#             "request": request,
#             "result": {"items": product_details},
#             "summary_text": summary_text
#         }
#     ) 
    


import re

def extract_customer_info(text: str) -> dict:
    """Extract customer information from summary text with new rules."""
    lines = text.split('\n')
    customer_info = {
        "customerName": "",
        "customerPhone": "",
        "customerAddress": ""
    }
    
    for line in lines:
        # Extract customerName (up to 90 characters)
        name_match = re.search(r"(K\.|k\.).*", line, re.IGNORECASE)
        if name_match:
            customer_info["customerName"] = name_match.group(0).strip()  # ดึงข้อมูลทั้งหมดที่ match
        
        # Extract customerPhone (up to 30 characters)
        phone_match = re.search(r"tel\s*[:：]?\s*(.{1,30})", line, re.IGNORECASE)
        if phone_match:
            customer_info["customerPhone"] = phone_match.group(1).strip()
        
        # Extract customerAddress (up to 400 characters)
        addr_match = re.search(r"(?:address)\s*[:：]?\s*(.{1,400})", line, re.IGNORECASE)
        if addr_match:
            customer_info["customerAddress"] = addr_match.group(1).strip()
    
    # If address not found explicitly, use the next line after phone
    if not customer_info["customerAddress"] and customer_info["customerPhone"]:
        for i, line in enumerate(lines):
            if customer_info["customerPhone"] in line:
                # Try to get the next line as address
                if i + 1 < len(lines):
                    customer_info["customerAddress"] = lines[i + 1].strip()
                break

    return customer_info





def extract_receiving_method(text: str) -> str:
    """Extract receiving method based on keywords"""
    text = text.lower()
    if 'แมส' in text:
        return "Line Man"
    elif 'ems' in text:
        return "ขนส่งอื่น"
    elif 'flash' in text:
        return "Flash"
    
    return "Flash"  # default


def extract_remark(text: str) -> str:
    """Extract remark from text"""
    match = re.search(r"note\s*[:：]\s*(.*)", text, re.IGNORECASE)
    return match.group(1).strip() if match else ""

def create_order_json(text: str, result: dict) -> dict:
    """Create order JSON from summary text and API result"""
    customer_info = extract_customer_info(text)
    remark = extract_remark(text)
    
    
    # Calculate discounts
    rental_discount = result['item']['rentalPrice'] - float(result['summary_prices']['rental_price'])
    bail_discount = result['item']['bail'] - float(result['summary_prices']['bail_price'])
    
    # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    
    # print(f"customer_info.get('customerName', '') >>> {customer_info.get('customerName', '')}")
    # print(f"customer_info.get('customerAddress', '') >>> {customer_info.get('customerAddress', '')}")
    # print(f"customer_info.get('customerPhone', '') >>> {customer_info.get('customerPhone', '')}")
    
    # print(f"result['rental_dates']['pickup_date'] >>> {result['rental_dates']['pickup_date']}")
    # print(f"result['rental_dates']['pickup_date'] >>> {result['rental_dates']['pickup_date']}")
    
    # print(f"result['item']['productItemId'] >>> {result['item']['productItemId']}")
    
    # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    
    
    # Create order JSON
    order_json = {
        "orderDetail": {
            "branchId": "9592dbbe-bbb7-48d6-bc32-d2902a5b5a6a",
            "customerId": "",
            "customerName": customer_info.get('customerName', ''),
            "customerAddress": customer_info.get('customerAddress', ''),
            "customerPhone": customer_info.get('customerPhone', ''),
            "lineId": "",
            "birthDate": "1800-01-01T00:00:00.000Z",
            "howToKnowShop": "",
            "accountNumber": "",
            "accountName": "",
            "bankName": "",
            "startDate": result['rental_dates']['pickup_date'],
            "endDate": result['rental_dates']['return_date'],
            "receivingMethod": extract_receiving_method(text),
            "remark1": remark,
            "rentalPaymentMethod": "โอนเงิน",
            "bailPaymentMethod": "โอนเงิน",
            "pointDiscount": 0,
            "voucherDiscount": 0,
            "bailDiscount": str(bail_discount),
            "rentalDiscount": str(rental_discount),
            "useFreeItemPromotion": True,
            "useDiscountPromotion": True
        },
        "orderItems": [
            {
                "productItemId": result['item']['productItemId'],
                "reservedQuantity": 1
            }
        ]
    }
    
    # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    # print(order_json)
    # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    
    return order_json