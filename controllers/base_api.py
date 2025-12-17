
import datetime, uuid
from odoo import http
from odoo.http import request
from odoo.addons.api_gateway.lib.jwt import api_jwt
import json
SECRET = "CHANGE_ME"
import logging
_logger = logging.getLogger(__name__)

class BaseApi(http.Controller):

    def _decode(self, token):
        return api_jwt.decode(token, SECRET, algorithms=["HS256"])

    def _auth(self, scope=None):
        try: 
            auth = request.httprequest.headers.get("Authorization")
            if not auth:
                return None

            token_str = auth.replace("Bearer ", "")
            try:
                payload = self._decode(token_str)
            except Exception as e:
                _logger.error("JWT decode error: %s", e)
                return None

            token = request.env["api.token"].sudo().search([
                ("access_token", "=", token_str),
                ("active", "=", True)
            ], limit=1)

            if not token:
                return None

            request.update_env(user=payload["uid"])
            self._current_token = token_str  # 🔥 store token

            return {
                "user": request.env.user,
                "token": token
            }
        except Exception as e:
            _logger.error("Authentication error: %s", e)
            return None


    def has_permission(self, token, model, action):
            perms = token.role_id.permissions or ""

            if perms == "*:*":
                return True

            allowed = {p.strip() for p in perms.split(",")}
            return f"{model}:{action}" in allowed
        
    def check_model_permission(self, model, operation):
        token = request.env["api.token"].sudo().search([
            ("access_token", "=", self._current_token),
            ("active", "=", True)
        ], limit=1)

        if not token:
            return False
        
        if token.is_superuser:
            return {
                "read": True,
                "create": True,
                "write": True,
                "unlink": True,
            }.get(operation, False)

        # Match by technical model name
        roles = token.role_ids.filtered(lambda r: r.model_id.model == model)
        if not roles:
            return False

        role = roles[0]
        

        return {
            "read": role.can_read,
            "create": role.can_create,
            "write": role.can_write,
            "unlink": role.can_unlink,
        }.get(operation, False)

    
    def response_ok(self, data, type= "http"):
        if type == "json":
            return data
        return request.make_response(json.dumps(data), headers=[("Content-Type","application/json")])

    def response_401(self, message="Unauthorized"):
        return request.make_response(
            json.dumps({"error": "Unauthorized", "status": 401, "message": message}), 
            headers=[("Content-Type","application/json")], 
            status=401
        )
    def response_400(self, message="Bad Request"):
        return request.make_response(
            json.dumps({"error": "Bad Request", "status": 400, "message": message}), 
            headers=[("Content-Type","application/json")], 
            status=400
        )
           
        
    def response_error(self, exception, status=400):
        msg = str(exception)
        # optionally log the exception here
        return request.make_response(
            json.dumps({"error": msg}),
            headers=[("Content-Type", "application/json")],
            status=status
        )
    
    
    
    

    