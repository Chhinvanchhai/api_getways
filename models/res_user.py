class ResUsers(models.Model):
    _inherit = "res.users"

    api_role_id = fields.Many2one("api.role", string="API Role")
