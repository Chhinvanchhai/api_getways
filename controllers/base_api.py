
import datetime, uuid
from odoo import http
from odoo.http import request
from odoo.addons.api_gateway.lib.jwt import api_jwt
import json
SECRET = "CHANGE_ME"
import logging
_logger = logging.getLogger(__name__)

class BaseApi(http.Controller):
    
    @http.route('/api/v1/health', type='http', auth='none', methods=['get'], csrf=False)
    def health(self):
        return self.response_ok({"status": "ok", "message": "API Gateway ready"})

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

        ir_model = request.env["ir.model"].sudo().search(
            [("model", "=", model)],
            limit=1
        )
        if not ir_model:
            return False

        roles = token.role_ids.filtered(
            lambda r: ir_model in r.model_ids
        )
        if not roles:
            return False

        return any({
            "read": role.can_read,
            "create": role.can_create,
            "write": role.can_write,
            "unlink": role.can_unlink,
        }.get(operation, False) for role in roles)
    
    def response_ok(self, data, type= "http"):
        return request.make_json_response(data, headers=[("Content-Type","application/json")])

    def response_401(self, message="Unauthorized"):
        return request.make_json_response({"error": "Unauthorized", "status": 401, "message": message}, 
            headers=[("Content-Type","application/json")], 
            status=401
        )
        
    def response_400(self, message="Bad Request"):
        return request.make_json_response({"error": "Bad Request", "status": 400, "message": message}, 
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
    
    def _expand_relations(self, records, data, depth=0, max_depth=3):
        params = request.params
        expand = params.get("expand", "false").lower() == "true"
        if not expand or not records or not data or depth >= max_depth:
            return data

        for rec, row in zip(records, data):
            for field_name in list(row.keys()):
                if field_name not in rec._fields:
                    continue

                field = rec._fields[field_name]
                value = rec[field_name]

                # ───────── Handle empty / None values ─────────
                if not value:
                    row[field_name] = None if field.type == "many2one" else []
                    continue

                # ───────── Binary fields → URL ─────────
                if field.type == "binary":
                    row[field_name] = self._binary_to_url(rec._name, rec.id, field_name)
                    continue
                
                if field.type == "many2many" and field.comodel_name == "ir.attachment":
                    continue

                # ───────── Only relation fields ─────────
                if field.type not in ("many2one", "one2many", "many2many"):
                    continue

                # ───────── Fields to expand for this relation ─────────
                sub_fields_param = params.get(field_name)
                sub_fields = (
                    [f.strip() for f in sub_fields_param.split(",")]
                    if sub_fields_param and isinstance(sub_fields_param, str)
                    else ["id", "display_name"]
                )

                # ───────── Nested params like partner_id.create_uid=id,name ─────────
                nested_prefix = f"{field_name}."
                nested_params = {
                    k[len(nested_prefix):]: v
                    for k, v in params.items()
                    if k.startswith(nested_prefix)
                }

                def serialize(record, nested_params):
                    result = {}
                    for f in sub_fields:
                        if f not in record._fields:
                            continue

                        fval = record[f]
                        fdef = record._fields[f]

                        # Binary → URL
                        if fdef.type == "binary" and fval:
                            result[f] = self._binary_to_url(record._name, record.id, f)
                            continue
                        
                        if fdef.type == "many2many" and fdef.comodel_name == "ir.attachment":
                            continue

                        # Nested many2one
                        if fdef.type == "many2one" and nested_params and f in nested_params and fval:
                            nested_field_value = nested_params.get(f)
                            if isinstance(nested_field_value, str):
                                nested_fields = [x.strip() for x in nested_field_value.split(",")]
                            else:
                                nested_fields = ["id", "display_name"]

                            nested_row = {nf: getattr(fval, nf) for nf in nested_fields if nf in fval._fields}

                            self._expand_relations(fval, [nested_row], depth + 1, max_depth)
                            result[f] = nested_row
                        else:
                            result[f] = fval
                    return result

                # ───────── Apply serialization ─────────
                if field.type == "many2one":
                    row[field_name] = serialize(value, nested_params)
                else:
                    row[field_name] = [serialize(r, nested_params) for r in value]

        return data


    def _auto_cast(self,value):
        """Convert string to bool / int / float when possible"""
        if not isinstance(value, str):
            return value

        lv = value.lower()
        if lv == "true":
            return True
        if lv == "false":
            return False

        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value


    def build_domain_from_request(self):
        args = request.httprequest.args

        # 1️⃣ JSON domain (highest priority)
        domain_json = args.get("domain")
        if domain_json:
            try:
                return json.loads(domain_json)
            except Exception:
                raise ValueError("Invalid JSON domain format")

        domain = []

        # 2️⃣ CSV domain
        fields_raw = args.get("domain_field", "")
        ops_raw = args.get("domain_operator", "")
        vals_raw = args.get("domain_value", "")
        logic = args.get("domain_logic")  # | or &

        if not (fields_raw and ops_raw and vals_raw):
            return domain

        fields = [f.strip() for f in fields_raw.split(",")]
        ops = [o.strip() for o in ops_raw.split(",")]
        vals = [v.strip() for v in vals_raw.split(",")]

        if not (len(fields) == len(ops) == len(vals)):
            raise ValueError("domain_field, domain_operator, domain_value length mismatch")

        conditions = []

        for f, op, v in zip(fields, ops, vals):

            # 3️⃣ Support "in" with list values
            if op == "in":
                v = [self._auto_cast(x.strip()) for x in v.split("|")]
            else:
                v = self._auto_cast(v)

            conditions.append((f, op, v))

        # 4️⃣ Logical operators | &
        if logic in ("|", "&") and len(conditions) > 1:
            domain.append(logic)
            domain.extend(conditions)
        else:
            domain.extend(conditions)

        return domain

    
    
    def _get_base_url(self):
        return request.httprequest.host_url.rstrip("/")

    def _binary_to_url(self, model, record_id, field):
        base_url = self._get_base_url()
        return f"{base_url}/web/content/{model}/{record_id}/{field}"

    def _attachment_to_dict(self, attachment):
        base_url = self._get_base_url()
        return {
            "id": attachment.id,
            "name": attachment.name,
            "mimetype": attachment.mimetype,
            "url":  f"{base_url}/web/content/{attachment.id}?access_token={attachment.access_token}" if attachment.access_token else f"{base_url}/web/content/{attachment.id}?download=true",
        }
        
    def _get_record_attachments(self, model, record_id):
        attachments = request.env["ir.attachment"].sudo().search([
            ("res_model", "=", model),
            ("res_id", "=", record_id),
        ])
        return [self._attachment_to_dict(att) for att in attachments]