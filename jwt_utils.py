from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel

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
    roleName: list[RoleName]
    userBranch: list[UserBranch]
    token: str
    tokenExpire: str
    shopInfoId: str

class JWTUtils:
    def __init__(self):
        self._user_data: Dict[str, UserData] = {}
    
    def store_user_info(self, login_response: dict) -> None:
        """เก็บข้อมูล user จาก login response"""
        user = UserData(**login_response)
        self._user_data[user.token] = user
    
    def get_user_info(self, token: str) -> Optional[UserData]:
        """ดึงข้อมูล user จาก token"""
        return self._user_data.get(token)
    
    def get_branch_id(self, token: str) -> Optional[str]:
        """ดึง branch ID จากข้อมูล user"""
        user = self._user_data.get(token)
        if user and user.userBranch:
            return user.userBranch[0].branchId
        return None
    
    def is_admin(self, token: str) -> bool:
        """ตรวจสอบว่า user มี role เป็น admin หรือไม่"""
        user = self._user_data.get(token)
        if user and user.roleName:
            return any(role.roleName == "admin" for role in user.roleName)
        return False
    
    def is_token_expired(self, token: str) -> bool:
        """ตรวจสอบว่า token หมดอายุหรือยัง"""
        user = self._user_data.get(token)
        if not user:
            return True
            
        try:
            expire_date = datetime.fromisoformat(user.tokenExpire.replace('Z', '+00:00'))
            return datetime.now() > expire_date
        except:
            return True

# สร้าง global instance
jwt_utils = JWTUtils()