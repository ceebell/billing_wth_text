from pydantic import BaseModel
from typing import Optional, List

# Models เดิมที่มีอยู่แล้ว ...

# เพิ่ม models สำหรับ user
class UserBranch(BaseModel):
    branchId: str
    branchName: str
    flag1: str

class RoleName(BaseModel):
    roleName: str

class UserData(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    username: str
    roleName: List[RoleName]
    userBranch: List[UserBranch]
    token: str
    tokenExpire: str
    shopInfoId: str
    
class SearchResult(BaseModel):
    success: bool
    message: str
    # item: Optional[ProductItem] = None           # ใช้ในกรณีมีรายการเดียว (หรือเพื่ออ้างอิงหลังจากเลือก)
    items: Optional[List[ProductItem]] = None      # สำหรับเก็บรายการสินค้าทั้งหมด
    summary_prices: Optional[SummaryPrices] = None
    rental_dates: Optional[RentalDates] = None
    queue_check: Optional[QueueCheckResult] = None
    search_params: Optional[dict] = None           # สำหรับเก็บ mapping parameters เมื่อไม่พบ code
