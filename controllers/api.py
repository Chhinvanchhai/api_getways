
from odoo import http
from odoo.http import request

class ApiController(http.Controller):

    @http.route('/api/v1/ping', type='json', auth='none', methods=['POST'], csrf=False)
    def ping(self):
        return {"status": "ok", "message": "API Gateway ready"}
