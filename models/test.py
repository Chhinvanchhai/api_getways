# -*- coding: utf-8 -*-
from odoo import models, fields

class ApiTestModel(models.Model):
    _name = "api.test.model"
    _description = "API Test Model with Attachments"

    name = fields.Char(string="Name", required=True)
    mode = fields.Selection([
        ("draft", "Draft"),
        ("confirm", "Confirm"),
        ("done", "Done"),
    ], string="Mode", default="draft")
    # attachment_ids = fields.Many2many(
    #     "ir.attachment",
    #     string="Attachments"
    # )
    image_1920 = fields.Image(string="Image")  # optional user photo / image
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "api_test_model_attachment_rel",  # table name
        "model_id",                       # column for this model
        "attachment_id",                  # column for ir.attachment
        string="Attachments"
    )

    doc_ids = fields.Many2many(
        "ir.attachment",
        "api_test_model_doc_rel",         # different table name
        "model_id",                       # column for this model
        "attachment_id",                  # column for ir.attachment
        string="Documents"
    )
