import json
from functools import wraps
from odoo.http import request
from .helpers import (
    get_client_ip,
    get_request_domain,
    is_ip_allowed,
    is_domain_allowed,
)



def require_auth(scope=None, type="http"):
    """
    Decorator to check JWT authentication for routes.
    Automatically returns 401 if auth fails.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            controller = args[0]  # self
            res = controller._auth(scope=scope)
            if not res:
                return request.make_response(
                    json.dumps({"error": "Unauthorized", "status": 401}),
                    headers=[("Content-Type", "application/json")],
                    status=401
                )
                
            token_rec = res.get("token")
            
            client_ip = get_client_ip()
            domain = get_request_domain()

            if  token_rec.allowed_ips and not is_ip_allowed(client_ip, token_rec.allowed_ips):
                return request.make_response(
                    json.dumps({"error": "IP not allowed", "ip": client_ip, "status": 403}),
                    status=403,
                    headers=[("Content-Type", "application/json")],
                )

            if  token_rec.allowed_domains and not is_domain_allowed(domain, token_rec.allowed_domains):
                return request.make_response(
                    json.dumps({"error": "Domain not allowed", "domain": domain, "status": 403}),
                    status=403,
                    headers=[("Content-Type", "application/json")],
                )

            if not res.get("user"):
                return request.make_response(
                    json.dumps({"error": "Unauthorized", "status": 401}),
                    headers=[("Content-Type", "application/json")],
                    status=401
                )
            return f(*args, **kwargs)
        return wrapper
    return decorator

def require_permission(model, action):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            self = args[0]
            user, token = self._auth()

            if not user:
                return self.response_error("Unauthorized", 401)

            if not self.has_permission(token, model, action):
                return self.response_error("Forbidden", 403)

            return f(*args, **kwargs)
        return wrapper
    return decorator
