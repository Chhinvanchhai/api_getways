
import datetime, uuid
from odoo import http
from odoo.http import request
from odoo.addons.api_gateway.lib.jwt import api_jwt
import json
from functools import wraps
SECRET = "CHANGE_ME"
from .decorators import require_auth 
from .base_api import BaseApi



class EmployeeApi(BaseApi):

    @http.route("/api/v1/employees", type="http", auth="none", methods=["GET"], csrf=False)
    @require_auth(scope="employees:read")  
    def employees(self, page=1, limit=20, name=None):
        try: 
            domain = []
            if name:
                domain.append(("name", "ilike", name))
            # ✅ Use search_count for total (fast SQL COUNT)
            total = request.env["hr.employee"].sudo().search_count(domain)
            offset = (int(page) - 1) * int(limit)
            employees = request.env["hr.employee"].sudo().search(domain, offset=offset, limit=int(limit))
            # data = employees.read(["name", "work_phone", "mobile_phone", "work_contact_id",])
            result = []
            for emp in employees:
                contact = emp.work_contact_id
                result.append({
                    "name": emp.name,
                    "work_phone": emp.work_phone,
                    "mobile_phone": emp.mobile_phone,
                    "contact": {
                        "id": contact.id if contact else None,
                        "name": contact.name if contact else None,
                        "email": contact.email if contact else None,
                        "phone": contact.phone if contact else None,
                        "mobile": contact.mobile if contact else None,
                    }
                })
            response = {
                "page": int(page),
                "limit": int(limit),
                "total": total,
                "data": result
            }
            return self.response_ok(response)
        except Exception as e:
            return self.response_error(e)

    @http.route("/api/docs/openapi.json", type="http", auth="none", methods=["GET"], csrf=False)
    def openapi(self):
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Odoo Mobile API", "version": "1.0"},
            "paths": {
                "/api/v1/login": {"post": {"summary": "Login"}},
                "/api/v1/refresh": {"post": {"summary": "Refresh token"}},
                "/api/v1/employees": {"post": {"summary": "List employees"}}
            }
        }
        return self.response_ok(spec)
