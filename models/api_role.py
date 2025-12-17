from odoo import models, fields

class ApiRole(models.Model):
    _name = "api.role"
    _description = "API Role"

    name = fields.Char(required=True)
    code = fields.Char(required=True, help="Unique code for the API role")
    model_id = fields.Many2one(
        "ir.model",
        string="Model",
        ondelete="set null",  # ⚠️ important for ir.model
        help="Select the Odoo model this role applies to"
    )

    can_read = fields.Boolean(default=True)
    can_create = fields.Boolean(default=False)
    can_write = fields.Boolean(default=False)
    can_unlink = fields.Boolean(default=False)
