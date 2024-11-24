# config.py

# API Configuration
API_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6ImJlbGwwMUBnbWFpbC5jb20iLCJyb2xlIjoiYWRtaW4iLCJCcmFuY2hOYW1lIjoiOTU5MmRiYmUtYmJiNy00OGQ2LWJjMzItZDI5MDJhNWI1YTZhIiwiU2hvcEluZm9JZCI6Ijg4NTNmNjczLWI0ZDEtNGE1YS04NDhkLWY1NTAwMmYyMjU0YiIsIm5iZiI6MTczMjM4NzAxMCwiZXhwIjoxNzMyNDczNDEwLCJpYXQiOjE3MzIzODcwMTB9.CqoTWgm98XT6Hw3yPyUns-veXNM1-RYBVGlJAkzYwXA"

API_HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# API URLs
API_URLS = {
    "search_product": "https://shop.alexrental.app/api/v2/GetProductItems",
    "check_queue": "https://shop.alexrental.app/api/orderdetail/checkq",
    "add_order": "https://shop.alexrental.app/api/v2/AddRentalOrder"
}

# Branch ID
DEFAULT_BRANCH_ID = "9592dbbe-bbb7-48d6-bc32-d2902a5b5a6a"


# User list
allows_users = ["bell01@gmail.com", "bell00@gmail.com"]