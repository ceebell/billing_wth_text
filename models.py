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