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
    simpleSearch: bool = False

class ProductItem(BaseModel):
    productItemId: str
    name: str
    code: str
    rentalPrice: float
    bail: float
    mainImage: Optional[str] = None 

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
    item: Optional[ProductItem] = None
    summary_prices: Optional[SummaryPrices] = None
    rental_dates: Optional[RentalDates] = None
    queue_check: Optional[QueueCheckResult] = None  # เพิ่มฟิลด์นี้
    
    
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

async def search_product(code: str) -> SearchResult:
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
                item=ProductItem(
                    productItemId=item["productItemId"],
                    name=item["name"],
                    code=item["code"],
                    rentalPrice=item["rentalPrice"],
                    bail=item["bail"],
                    mainImage=item["mainImage"]
                ),
                summary_prices=SummaryPrices()
            )
            
    except Exception as e:
        return SearchResult(
            success=False,
            message=f"Error: {str(e)}",
            summary_prices=SummaryPrices()
        )

# @app.get("/")
# async def home(request: Request):
#     return templates.TemplateResponse(
#         "search.html",
#         {"request": request}
#     )
   
# With AUTH 
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

@app.post("/search")
async def search(request: Request, summary_text: str = Form(...)):
    # Extract code from summary text
    code = extract_code_from_text(summary_text)
    
    token = request.cookies.get("auth_token")
    user = jwt_utils.get_user_info(token)
    # API_HEADERS = {
    #     "Authorization": f"Bearer {API_TOKEN}",
    #     "Content-Type": "application/json"
    # }
    API_HEADERS["Authorization"] = f"Bearer {token}"
    

    print(f"API_HEADERS >>> {API_HEADERS}")
    
    
    if not code:
        return templates.TemplateResponse(
            "search.html",
            {
                "request": request,
                "result": SearchResult(
                    success=False,
                    message="ไม่พบรหัสสินค้าในข้อความ",
                    summary_prices=SummaryPrices(),
                    rental_dates=RentalDates(),  # เพิ่ม default rental dates
                ),
                "summary_text": summary_text
            }
        )

    # Extract all information from summary text
    summary_prices = extract_prices_from_text(summary_text)  # ดึงข้อมูลราคา
    rental_dates = extract_dates_from_text(summary_text)     # ดึงข้อมูลวันที่
    
    # print(f"rental_dates >>> {rental_dates}")
    # Search product from API
    result = await search_product(code)
    
    if result.success:
        # Update result with extracted information
        result.summary_prices = summary_prices
        result.rental_dates = RentalDates(**rental_dates)  # แปลง dict เป็น RentalDates model
    
        # ถ้ามีวันที่รับและคืน ให้เช็คคิว
        if rental_dates.get('pickup_date') and rental_dates.get('return_date'):
            # print(f"productItemId >>> {result.item.productItemId}  pickup_date >>> {rental_dates['pickup_date']} return_date >>>  {rental_dates['return_date']}")
            queue_result = await check_queue(
                result.item.productItemId,
                rental_dates['pickup_date'],
                rental_dates['return_date']
            )
            result.queue_check = queue_result
            
            order_json = create_order_json(summary_text, result.dict())
            
            print(f"result.queue_check >>> {queue_result}")
    
    else:
        # กรณีค้นหาไม่สำเร็จ ก็ยังใส่ข้อมูลวันที่ไว้
        result.rental_dates = RentalDates(**rental_dates)
        
    
    return templates.TemplateResponse(
        "search.html",
        {
            "request": request,
            "result": result,
            "summary_text": summary_text,
            "order_json": order_json,
            "api_config": api_config
            
        }
    )
    
def extract_customer_info(text: str) -> dict:
    """Extract customer information from summary text"""
    lines = text.split('\n')
    customer_info = {}
    
    # Find customer name and phone line
    for line in lines:
        if '(' in line and ')' in line and any(c.isdigit() for c in line):
            # Extract name (up to 20 chars after 'K.')
            name_part = line.split('(')[0].strip()
            if name_part.startswith('K.'):
                customer_info['customerName'] = name_part[:20]
            
            # Extract phone
            phone = line[line.find('(')+1:line.find(')')]
            customer_info['customerPhone'] = phone
            
            # Get address from next line
            if len(lines) > lines.index(line) + 1:
                customer_info['customerAddress'] = lines[lines.index(line) + 1].strip()
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

def create_order_json(text: str, result: dict) -> dict:
    """Create order JSON from summary text and API result"""
    customer_info = extract_customer_info(text)
    
    # Calculate discounts
    rental_discount = result['item']['rentalPrice'] - float(result['summary_prices']['rental_price'])
    bail_discount = result['item']['bail'] - float(result['summary_prices']['bail_price'])
    
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
            "remark1": "",
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
    
    return order_json