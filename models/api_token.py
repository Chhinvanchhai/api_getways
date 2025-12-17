from odoo import models, fields

class ApiToken(models.Model):
    _name = "api.token"
    _description = "API Token"

    user_id = fields.Many2one("res.users", required=True)
    role_ids = fields.Many2many(
        "api.role",
        string="API Roles"
    )
    access_token = fields.Text(required=True)
    refresh_token = fields.Text(required=True)
    is_superuser = fields.Boolean(
        default=False,
        help="If true, this token has all permissions."
    )
    allowed_ips = fields.Text(
        help="Comma-separated IPs or CIDR ranges (e.g. 192.168.1.10, 10.0.0.0/24)"
    )

    allowed_domains = fields.Text(
        help="Comma-separated domains (e.g. example.com, app.example.com)"
    )
    permissions = fields.Text(
        help="Comma separated permissions. Example: hr.employee:view,hr.employee:create"
    )

    expire_at = fields.Datetime(required=True)
    active = fields.Boolean(default=True)
