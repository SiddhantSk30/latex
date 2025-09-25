# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PurchaseRequisition(models.Model):
    _name = 'purchase.requisition'
    _description = 'Purchase Requisition'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Requisition Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
    )
    partner_id = fields.Many2one('res.partner', string='Vendor')
    date_order = fields.Datetime(
        string='Requisition Date',
        required=True,
        default=fields.Datetime.now
    )
    state = fields.Selection([
        ('draft', 'Preparing Group'),
        ('store', 'Approved by Store Department'),
        ('production', 'Approved by Production'),
        ('gm', 'Approved by GM'),
        ('purchase', 'Purchase Department'),
        ('rfq', 'Final Purchase Department (RFQ)'),
    ], string='Status', default='draft', tracking=True)
    line_ids = fields.One2many('purchase.requisition.line', 'requisition_id', string='Requisition Lines')
    notes = fields.Text(string='Notes')
    purchase_order_id = fields.Many2one('purchase.order', string='RFQ')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq = self.env['ir.sequence'].sudo().next_by_code('purchase.requisition') or _('New')
            vals['name'] = seq
        return super().create(vals)

    def action_store_approve(self):
        for rec in self:
            rec.state = 'store'

    def action_production_approve(self):
        for rec in self:
            if rec.state != 'store':
                raise UserError(_('Requisition must be approved by Store before Production.'))
            rec.state = 'production'

    def action_gm_approve(self):
        for rec in self:
            if rec.state != 'production':
                raise UserError(_('Requisition must be approved by Production before GM approval.'))
            rec.state = 'gm'

    def action_purchase_approve(self):
        for rec in self:
            if rec.state != 'gm':
                raise UserError(_('Requisition must be approved by GM before Purchase department.'))
            rec.state = 'purchase'

    def action_rfq(self):
        """Create a purchase.order (RFQ) from this requisition."""
        PurchaseOrder = self.env['purchase.order']
        PurchaseLine = self.env['purchase.order.line']
        for rec in self:
            if rec.state != 'purchase':
                raise UserError(_('Only requisitions at Purchase Department stage can be converted to RFQ.'))
            if rec.purchase_order_id:
                # already created
                continue

            po_vals = {
                'partner_id': rec.partner_id.id if rec.partner_id else False,
                'origin': rec.name,
                'date_order': fields.Datetime.now(),
                'company_id': rec.env.company.id,
            }
            po = PurchaseOrder.create(po_vals)

            for line in rec.line_ids:
                if not line.product_id:
                    raise UserError(_('All lines should have a product to create RFQ.'))
                pol_vals = {
                    'order_id': po.id,
                    'product_id': line.product_id.id,
                    'name': line.product_id.display_name,
                    'product_qty': line.product_qty,
                    'price_unit': line.price_unit or 0.0,
                    'product_uom': line.product_id.uom_id.id or False,
                    'date_planned': fields.Datetime.now(),
                }
                PurchaseLine.create(pol_vals)

            rec.purchase_order_id = po.id
            rec.state = 'rfq'
        return True


class PurchaseRequisitionLine(models.Model):
    _name = 'purchase.requisition.line'
    _description = 'Purchase Requisition Line'

    requisition_id = fields.Many2one('purchase.requisition', string='Requisition')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_qty = fields.Float(string='Quantity', required=True)
    price_unit = fields.Float(string='Unit Price')
    notes = fields.Char(string='Description')
