
import datetime, uuid
from odoo import http
from odoo.http import request
from odoo.addons.api_gateway.lib.jwt import api_jwt
import json
from functools import wraps
SECRET = "CHANGE_ME"
from .decorators import require_auth 
from .base_api import BaseApi
from .helpers import get_request_data


class AuthApi(BaseApi):
    API_PREFIX = "/api/v1/auth"
    
    @http.route(f"{API_PREFIX}/login", type="http", auth="none", methods=["POST"], csrf=False)
    def login(self, **kwargs):
        try:
            data = get_request_data()
            login = data.get("login")
            password = data.get("password")

            if not login or not password:
                return self.response_400("Missing login or password")

            db_name = request.env.cr.dbname
            credential = {'login': login, 'password': password, 'type': 'password'}
            auth_info = request.session.authenticate(db_name, credential)

            if not auth_info or not auth_info.get("uid"):
                return self.response_error("Invalid credentials", 401)

            uid = auth_info["uid"]
            user = request.env["res.users"].sudo().browse(uid)
            exp = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
            access_token = api_jwt.encode(
                {"uid": uid, "exp": exp},
                SECRET,
                algorithm="HS256"
            )
            refresh_token = api_jwt.encode(
                {"uid": uid, "jti": uuid.uuid4().hex},
                SECRET,
                algorithm="HS256"
            )
            token = request.env["api.token"].sudo().search([("user_id", "=", uid)], limit=1)
            if not token:
                request.env["api.token"].sudo().create({
                    "user_id": uid,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expire_at": exp,
                    "active": True
                })
            else: 
                token.write({
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expire_at": exp,
                    "active": True
                })
            response = {
                "status": 200,
                "result": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_in": 1800,
                }
              
            }
            return self.response_ok(response)

        except Exception as e:
            return self.response_error(str(e), 500)



    @http.route(f"{API_PREFIX}/refresh", type="http", auth="none", methods=["POST"], csrf=False)
    def refresh(self, **kwargs):
        try:
            data = get_request_data()
            refresh_token = data.get("refresh_token")
            try:
                payload = api_jwt.decode(refresh_token, SECRET, algorithms=["HS256"])
            except Exception:
                return {"error": "Invalid refresh token"}

            token = request.env["api.token"].sudo().search([
                ("refresh_token", "=", refresh_token),
                ("active", "=", True)
            ], limit=1)
            if not token:
                return {"error": "Token revoked"}

            new_payload = {
                "uid": payload["uid"],
                "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
            }
            new_access = api_jwt.encode(new_payload, SECRET, algorithm="HS256")
            token.access_token = new_access
            token.expire_at = new_payload["exp"]

            response = {
                "status": 200,
                "result": {
                    "access_token": new_access, "expires_in": 1800
                }    
            } # HOUR
            return self.response_ok(response)
        except Exception as e:
            return self.response_error(e)

