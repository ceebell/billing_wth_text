import re
from datetime import datetime
from typing import Optional, Dict

# # Pattern Components
# PICKUP_KEYWORDS = r'(?:วันรับชุด|รับชุด|ลูกค้ารับชุด|ส่งชุดให้ลูกค้า)'
# RETURN_KEYWORDS = r'(?:วันคืนชุด|คืนชุด|ลูกค้าส่งชุดคืน|ส่งคืน|ลูกค้าส่งชุดคืน)'
    
# # Pattern สำหรับวันที่ภาษาไทย - แยกส่วนเพื่อความชัดเจน
# DAY_PATTERN = r'(\d{1,2})(?:\s*,\s*\d{1,2})*'  # รองรับ "8,9" หรือ "8, 9"
# MONTH_PATTERN = (
#     r'(?:'
#     r'[มกพคมิยสตธ]{1,2}\.?[คพยญ]{0,2}\.?|'  # รูปแบบตัวย่อ
#     r'มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|'  # ชื่อเต็ม
#     r'กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม'  # ชื่อเต็ม
#     r')'
# )
# YEAR_PATTERN = r'(\d{2,4})'  # ปี 2-4 หลัก

def convert_buddhist_year(year_str: str) -> Optional[str]:
    """Convert Buddhist year to Christian year"""
    try:
        if len(year_str) == 2:
            buddhist_year = int('25' + year_str)
        else:
            buddhist_year = int(year_str)
        return str(buddhist_year - 543)
    except ValueError:
        return None

def convert_thai_month(thai_month: str) -> Optional[str]:
    """Convert Thai month name/abbreviation to month number"""
    month_mapping = {
        # มกราคม
        'มค': '01', 'ม.ค.': '01', 'มค.': '01', 'ม.ค': '01', 
        'มกรา': '01', 'มกราคม': '01',
        
        # กุมภาพันธ์
        'กพ': '02', 'ก.พ.': '02', 'กพ.': '02', 'ก.พ': '02', 
        'กุมภา': '02', 'กุมภาพันธ์': '02',
        
        # มีนาคม
        'มีค': '03', 'มี.ค.': '03', 'มีค.': '03', 'มี.ค': '03', 
        'มีนา': '03', 'มีนาคม': '03',
        
        # เมษายน
        'เมย': '04', 'เม.ย.': '04', 'เมย.': '04', 'เม.ย': '04', 
        'เมษา': '04', 'เมษายน': '04',
        
        # พฤษภาคม
        'พค': '05', 'พ.ค.': '05', 'พค.': '05', 'พ.ค': '05', 
        'พฤษภา': '05', 'พฤษภาคม': '05',
        
        # มิถุนายน
        'มิย': '06', 'มิ.ย.': '06', 'มิย.': '06', 'มิ.ย': '06', 
        'มิถุนา': '06', 'มิถุนายน': '06',
        
        # กรกฎาคม
        'กค': '07', 'ก.ค.': '07', 'กค.': '07', 'ก.ค': '07', 
        'กรกฎา': '07', 'กรกฎาคม': '07',
        
        # สิงหาคม
        'สค': '08', 'ส.ค.': '08', 'สค.': '08', 'ส.ค': '08', 
        'สิงหา': '08', 'สิงหาคม': '08',
        
        # กันยายน
        'กย': '09', 'ก.ย.': '09', 'กย.': '09', 'ก.ย': '09', 
        'กันยา': '09', 'กันยายน': '09',
        
        # ตุลาคม
        'ตค': '10', 'ต.ค.': '10', 'ตค.': '10', 'ต.ค': '10', 
        'ตุลา': '10', 'ตุลาคม': '10',
        
        # พฤศจิกายน
        'พย': '11', 'พ.ย.': '11', 'พย.': '11', 'พ.ย': '11', 
        'พฤศจิกา': '11', 'พฤศจิกายน': '11',
        
        # ธันวาคม
        'ธค': '12', 'ธ.ค.': '12', 'ธค.': '12', 'ธ.ค': '12', 
        'ธันวา': '12', 'ธันวาคม': '12'
    }
    
    # ลบช่องว่างและแปลงเป็นข้อความ
    thai_month = str(thai_month).strip()
    
    # ส่งคืนค่าจาก mapping
    return month_mapping.get(thai_month)

def is_valid_date(day: str, month: str, year: str) -> bool:
    """ตรวจสอบความถูกต้องของวันที่"""
    try:
        day = int(day)
        month = int(month)
        year = int(year)
        
        if not (1 <= day <= 31) or not (1 <= month <= 12):
            return False
            
        datetime(year, month, day)
        return True
    except ValueError:
        return False
    
# def create_date_pattern(keyword_pattern: str) -> str:
#     """
#     สร้าง pattern สำหรับการค้นหาวันที่ที่ตามหลังคำสำคัญ
    
#     Args:
#         keyword_pattern (str): Pattern ของคำสำคัญ (เช่น รับชุด, คืนชุด)
        
#     Returns:
#         str: Pattern สมบูรณ์สำหรับการค้นหาวันที่
#     """
#     return (
#         f"{keyword_pattern}"  # คำสำคัญ
#         r"[:\s]+"  # เครื่องหมาย : หรือ space อย่างน้อย 1 ตัว
#         f"{DAY_PATTERN}"  # วันที่
#         r"\s*"  # เว้นวรรคระหว่างวันและเดือน
#         f"{MONTH_PATTERN}"  # เดือน
#         r"\s*"  # เว้นวรรคระหว่างเดือนและปี
#         f"{YEAR_PATTERN}"  # ปี
#     )

def extract_date_from_match(match: re.Match) -> Optional[str]:
    """Extract and validate date from regex match"""
    day, month, year = match.groups()
    
    # Convert month
    month_num = convert_thai_month(month)
    if not month_num:
        return None
        
    # Convert year
    year_ce = convert_buddhist_year(year)
    if not year_ce:
        return None
        
    # Validate date
    if not is_valid_date(day, month_num, year_ce):
        return None
        
    return f"{year_ce}-{month_num}-{day.zfill(2)}"




def extract_dates_from_text(text: str) -> Dict[str, Optional[str]]:
    """Extract pickup and return dates from summary text."""
    dates = {
        'pickup_date': None,
        'return_date': None
    }
    
    
    
    # คำที่ใช้ระบุวันรับชุด
    # pickup_keywords = r'(?:วันรับชุด|รับชุด|ลูกค้ารับชุด|ส่งชุดให้ลูกค้า)'
    
    # คำที่ใช้ระบุวันคืนชุด
    return_keywords = r'(?:วันคืนชุด|คืนชุด|ลูกค้าส่งชุดคืน|ส่งคืน|ลูกค้าส่งชุดคืน)'

    # Pattern สำหรับวันที่ภาษาไทย
    date_pattern = (
        r'(\d{1,2})'  # วันที่ 1-2 หลัก
        r"[:\s]+"  # เว้นวรรค
        r'('  # กลุ่มเดือน
        r'[มกพคมิยสตธเมมี]{1,2}\.?[คพยญ]{0,2}\.?|'  # รูปแบบตัวย่อ
        r'มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|'  # ชื่อเต็ม
        r'กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม'  # ชื่อเต็ม
        r')'
        r'\s*'  # เว้นวรรค
        r'(\d{2,4})'  # ปี 2-4 หลัก
    )
    
    
    

    # Variables สำหรับวันรับชุด
    pickup_day = None
    pickup_month = None
    pickup_year = None
    pickup_month_num = None
    pickup_year_ce = None

    # Variables สำหรับวันคืนชุด
    return_day = None
    return_month = None
    return_year = None
    return_month_num = None
    return_year_ce = None

    # แยกบรรทัดและประมวลผล
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    for line in lines:
       
        # ค้นหาวันรับชุด
        pickup_pattern = (
            # r'(?:วันรับชุด|รับชุด|ลูกค้ารับชุด|ส่งชุดให้ลูกค้า)' + 
            r'(?:ส่งชุดจริง|ส่งชุดให้ลูกค้า|ส่งชุด)' + 
            r'\s*(?::\s*|\s+)' +
            r'(?:[^\d]*)?' + 
            r'(\d{1,2})'+  # วันที่ 1-2 หลัก
            r"[:\s]+"+  # เว้นวรรค
            r'('  # กลุ่มเดือน
            r'[มกพคมิยสตธเมมี]{1,2}\.?[คพยญ]{0,2}\.?|' + # รูปแบบตัวย่อ
            r'มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|'+  # ชื่อเต็ม
            r'กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม' + # ชื่อเต็ม
            r')'+
            r'\s*'+  # เว้นวรรค
            r'(\d{2,4})'  # ปี 2-4 หลัก
        )
            
        pickup_match = re.search(pickup_pattern, line, re.IGNORECASE)
        
       
        
        if pickup_match:
            # print(f"=============== รับชุด ===============")
            # print(f"pickup_match {pickup_match}")
            
            pickup_day, pickup_month, pickup_year = pickup_match.groups()
            pickup_month_num = convert_thai_month(pickup_month)
            pickup_year_ce = convert_buddhist_year(pickup_year)
            # print(f"***** Pickup Date: {pickup_day}-{pickup_month_num}-{pickup_year_ce}")
            
            if (pickup_month_num and pickup_year_ce and 
                is_valid_date(pickup_day, pickup_month_num, pickup_year_ce)):
                dates['pickup_date'] = (
                    f"{pickup_year_ce}-{pickup_month_num}-{pickup_day.zfill(2)}"
                )

        # ค้นหาวันคืนชุด
        # return_date_pattern = (return_keywords +   r'\s*(?::\s*|\s+)(?:วันที่\s*)?' + date_pattern  )
        
        # ค้นหาวันคืนชุด
        return_pattern = (
            r'(?:วันคืนชุด|คืนชุด|ลูกค้าส่งชุดคืน|ส่งคืน|ลูกค้าส่งชุดคืน)' + 
            r'\s*(?::\s*|\s+)' +
            r'(?:[^\d]*)?' + 
            r'(\d{1,2})'+  # วันที่ 1-2 หลัก
            r"[:\s]+"+  # เว้นวรรค
            r'('  # กลุ่มเดือน
            r'[มกพคมิยสตธเมมี]{1,2}\.?[คพยญ]{0,2}\.?|' + # รูปแบบตัวย่อ
            r'มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|'+  # ชื่อเต็ม
            r'กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม' + # ชื่อเต็ม
            r')'+
            r'\s*'+  # เว้นวรรค
            r'(\d{2,4})'  # ปี 2-4 หลัก
        )
        
       
        
        return_match = re.search(return_pattern, line, re.IGNORECASE)
        if return_match:
            # print(f"=============== คืนชุด ===============")
            # print(f">>>>> return_match : {return_match}")

            return_day, return_month, return_year = return_match.groups()
            return_month_num = convert_thai_month(return_month)
            return_year_ce = convert_buddhist_year(return_year)
            
            # print(f"***** Return Date: {return_day}-{return_month_num}-{return_year_ce}")
            
            if (return_month_num and return_year_ce and 
                is_valid_date(return_day, return_month_num, return_year_ce)):
                dates['return_date'] = (
                    f"{return_year_ce}-{return_month_num}-{return_day.zfill(2)}"
                )

    # ถ้าไม่พบทั้งวันรับและวันคืน หรือวันที่ไม่ถูกต้อง ให้คืนค่า None ทั้งคู่
    if not dates['pickup_date'] or not dates['return_date']:
        return {'pickup_date': None, 'return_date': None}
    
    # print(f"RESULT OF date >>> ",dates)

    return dates

# # Test function
# if __name__ == "__main__":
#     test_cases = [
#         # ทดสอบข้ามเดือน
#         """
#         รับชุด 30 พ.ย. 67
#         คืนชุด 1 ธ.ค. 67
#         """,
#         # ทดสอบวันที่ไม่ถูกต้อง
#         # """
#         # รับชุด 32 พ.ย. 67
#         # คืนชุด 31 พ.ย. 67
#         # """,
#         # # ทดสอบรูปแบบผสม
#         # """
#         # รับชุด 24 พย 67
#         # คืนชุด 25 พฤศจิกายน 67
#         # """
#     ]
    
#     for i, test_text in enumerate(test_cases, 1):
#         print(f"\nTest case {i}:")
#         print(test_text.strip())
#         result = extract_dates_from_text(test_text)
#         print("Result:", result)
        
        


