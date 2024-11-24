from fastapi import Request
from fastapi.responses import RedirectResponse
from jwt_utils import jwt_utils  #

class AuthMiddleware:
    def __init__(self):
        self.exclude_paths = ["/login", "/static"]
    
    async def __call__(self, request: Request, call_next):
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        token = request.cookies.get("auth_token")
        if not token or jwt_utils.is_token_expired(token):
            return RedirectResponse(url="/login")

        try:
            user_data = jwt_utils.get_user_info(token)
            if user_data:
                request.state.user = user_data
                request.state.branch_id = jwt_utils.get_branch_id(token)
                request.state.user_role = jwt_utils.is_admin(token)
            
            response = await call_next(request)
            return response
            
        except Exception:
            return RedirectResponse(url="/login")