# How to run : $ pytest test_date.py -v
# test_date_extractor.py
import pytest
from datetime import datetime
from date_extractor import extract_dates_from_text  # แก้ชื่อ module ตามที่คุณตั้งไว้

@pytest.fixture
def test_cases():
    """Test cases with expected results"""
    return [
        # 1. รูปแบบพื้นฐาน
        {
            'name': 'basic_format',
            'text': """
                ส่งชุด 24 พ.ย. 67 :เที่ยงวัน (แมส)
                คืนชุด 25 พ.ย. 67 :เที่ยงครึ่ง (แมส)
            """,
            'expected': {
                'pickup_date': '2024-11-24',
                'return_date': '2024-11-25'
            }
        },
        # 2. ตัวย่อเดือนแบบต่างๆ
        {
            'name': 'month_abbreviations',
            'text': """
                ส่งชุด 24 พย 67
                คืนชุด 25 พ.ย. 67
            """,
            'expected': {
                'pickup_date': '2024-11-24',
                'return_date': '2024-11-25'
            }
        },
        # 3. ชื่อเดือนเต็ม
        {
            'name': 'full_month_name',
            'text': """
                ส่งชุด 24 พฤศจิกายน 67
                คืนชุด 25 พฤศจิกายน 67
            """,
            'expected': {
                'pickup_date': '2024-11-24',
                'return_date': '2024-11-25'
            }
        },
        # 4. รูปแบบผสม
        {
            'name': 'mixed_formats',
            'text': """
                ส่งชุด 24 พย 67
                คืนชุด 25 พฤศจิกายน 67
            """,
            'expected': {
                'pickup_date': '2024-11-24',
                'return_date': '2024-11-25'
            }
        },
        # 5. ข้ามเดือน
        {
            'name': 'different_months',
            'text': """
                ส่งชุด 30 พ.ย. 67
                คืนชุด 1 ธ.ค. 67
            """,
            'expected': {
                'pickup_date': '2024-11-30',
                'return_date': '2024-12-01'
            }
        },
        # 6. หลายวันที่ในบรรทัดเดียว
        {
            'name': 'multiple_dates_per_line',
            'text': "ใช้งาน 23 พ.ย. 67 ส่งชุด 24 พ.ย. 67 คืนชุด 25 พ.ย. 67",
            'expected': {
                'pickup_date': '2024-11-24',
                'return_date': '2024-11-25'
            }
        },
        # 7. วันที่ไม่ถูกต้อง
        {
            'name': 'invalid_dates',
            'text': """
                ส่งชุด 32 พ.ย. 67
                คืนชุด 31 พ.ย. 67
            """,
            'expected': {
                'pickup_date': None,
                'return_date': None
            }
        }
    ]

# Basic test functions
def test_basic_format(test_cases):
    case = next(c for c in test_cases if c['name'] == 'basic_format')
    result = extract_dates_from_text(case['text'])
    assert result == case['expected']

def test_month_abbreviations(test_cases):
    case = next(c for c in test_cases if c['name'] == 'month_abbreviations')
    result = extract_dates_from_text(case['text'])
    assert result == case['expected']

def test_full_month_name(test_cases):
    case = next(c for c in test_cases if c['name'] == 'full_month_name')
    result = extract_dates_from_text(case['text'])
    print(f"test_full_month_name >>> {result}")
    assert result == case['expected']

# def test_mixed_formats(test_cases):
#     case = next(c for c in test_cases if c['name'] == 'mixed_formats')
#     result = extract_dates_from_text(case['text'])
#     print(f"test_mixed_formats >>> {result}")
#     assert result == case['expected']

def test_different_months(test_cases):
    case = next(c for c in test_cases if c['name'] == 'different_months')
    result = extract_dates_from_text(case['text'])
    print(f"test_different_months ::: case >>> {case}")
    print(f"test_different_months >>> {result}")
    assert result == case['expected']

# def test_multiple_dates_per_line(test_cases):
#     case = next(c for c in test_cases if c['name'] == 'multiple_dates_per_line')
#     result = extract_dates_from_text(case['text'])
#     print(f"test_multiple_dates_per_line >>> {result}")
#     assert result == case['expected']

def test_invalid_dates(test_cases):
    case = next(c for c in test_cases if c['name'] == 'invalid_dates')
    result = extract_dates_from_text(case['text'])
    assert result == case['expected']

# Additional validation tests
def test_empty_input():
    """Test with empty input"""
    result = extract_dates_from_text("")
    assert result == {'pickup_date': None, 'return_date': None}

def test_no_dates():
    """Test with text containing no dates"""
    result = extract_dates_from_text("ไม่มีวันที่ในข้อความ")
    assert result == {'pickup_date': None, 'return_date': None}

def test_date_format_validation():
    """Validate date format"""
    text = "ส่งชุด 24 พ.ย. 67"
    result = extract_dates_from_text(text)
    if result['pickup_date']:
        try:
            datetime.strptime(result['pickup_date'], '%Y-%m-%d')
        except ValueError:
            pytest.fail("Invalid date format")

# Run specific test cases
if __name__ == "__main__":
    # สามารถรันเฉพาะ test case ที่ต้องการได้
    pytest.main(['-v', '-k', 'test_invalid_dates'])