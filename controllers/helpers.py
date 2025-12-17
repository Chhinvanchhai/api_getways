import json
from odoo.http import request
import ipaddress

def get_request_data():
    """
    Safely extract request data for type='http' routes.

    Supports:
    - application/json
    - application/x-www-form-urlencoded
    - query parameters
    """
    req = request.httprequest

    # JSON body
    if req.content_type and "application/json" in req.content_type:
        try:
            return json.loads(req.data.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return {}

    # Form data
    if req.form:
        return req.form.to_dict()

    # Query params (?a=1&b=2)
    return request.params


def get_client_ip():
    """
    Get real client IP (supports proxy headers)
    """
    headers = request.httprequest.headers

    if headers.get("X-Forwarded-For"):
        return headers.get("X-Forwarded-For").split(",")[0].strip()

    return request.httprequest.remote_addr


def get_request_domain():
    """
    Extract domain from Origin or Host
    """
    headers = request.httprequest.headers

    origin = headers.get("Origin")
    if origin:
        return origin.replace("https://", "").replace("http://", "").split("/")[0]

    return headers.get("Host")

def is_ip_allowed(client_ip, allowed_ips):
    if not allowed_ips:
        return True  # no restriction

    for ip in allowed_ips.split(","):
        ip = ip.strip()
        try:
            if "/" in ip:
                if ipaddress.ip_address(client_ip) in ipaddress.ip_network(ip):
                    return True
            else:
                if client_ip == ip:
                    return True
        except Exception:
            continue

    return False


def is_domain_allowed(domain, allowed_domains):
    if not allowed_domains:
        return True  # no restriction

    for d in allowed_domains.split(","):
        d = d.strip().lower()
        if domain and domain.lower().endswith(d):
            return True

    return False
