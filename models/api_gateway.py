
from odoo import models, fields

class ApiGateway(models.Model):
    _name = "api.gateway"
    _description = "API Gateway"

    name = fields.Char(required=True)
    base_url = fields.Char()
    token = fields.Char()
    active = fields.Boolean(default=True)
