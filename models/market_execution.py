# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError, ValidationError


class MarketExecution(models.Model):
    _inherit = 'market.execution'
    _description = 'Market Execution'

	#Budgets Ids
    type_budget = fields.Selection([('chb', 'CHB'), ('functionment', 'Fonctionnement'), ('investment', 'Investissement')],string="Type Budget")
    tech_budget_id = fields.Many2one('tech.budget', string="Budget / Programme")
    nature_id = fields.Many2one('parameter.nature', string="Nature")
    rubrique_id = fields.Many2one('rubrique.budget', string="Rubrique")
    plafond_nature = fields.Float('Plafond Nature', related="tech_budget_id.plafond_nature")
    credit_inscrit = fields.Float(string='Crédit inscrit', compute="_compute_inscrit_and_engage")
    total_engage = fields.Float(string='Total Engagé', compute="_compute_inscrit_and_engage")
    credit_disponible = fields.Float(string='Crédit Disponible', compute="_compute_credit_disponible")

    def action_engager(self):
        res = super(MarketExecution, self).action_engager()
        if not self.engagement_number or not self.enagagement_date or not self.engagement_amount or not self.tech_budget_id or not self.nature_id or not self.rubrique_id:
            raise ValidationError(_('Données Engagement incomplétes.'))
        elif self.engagement_amount > self.credit_disponible:
            raise ValidationError(_("Le montant d'engagement déngagement dépasse le crédit disponible de la rubrique budgétaire"))
        elif (self.engagement_amount + self.total_engage) > self.plafond_nature:
            raise ValidationError(_("Dépassement plafond Nature"))

        purchase_requisition = False
        if self.purchase_requisition:
            purchase_requisition = self.purchase_requisition
        elif self.purchase_requisition_bc:
            purchase_requisition = self.purchase_requisition_bc
        elif self.contrat_convention_id:
            purchase_requisition = self.contrat_convention_id
        elif self.contrat_regie_id:
            purchase_requisition = self.contrat_regie_id

        suivi_engagement = self.env['suivi.engagements'].search([('tech_budget_id', '=', self.tech_budget_id.id)], limit=1)
        if not suivi_engagement:
            raise ValidationError(_("no any engagement available for selected budget !"))

        engagement_log = self.env['engagement.log'].create({
            'dengagement': self.engagement_number,
            'date': self.enagagement_date,
            'montant_dengagement': self.engagement_amount,
            'contrat_type_id': purchase_requisition.type_id.id if purchase_requisition else False,
            'ref_operation': purchase_requisition.name if purchase_requisition else False,
            'type_budget': self.type_budget,
            'tech_budget_id': self.tech_budget_id.id if self.tech_budget_id else false,
            'nature_id': self.nature_id.id if self.nature_id else False,
            'rubrique_id': self.rubrique_id.id if self.rubrique_id else False,
            'suivi_engagements_id': suivi_engagement.id,
        })
        
        return res
    
    @api.depends('rubrique_id')
    def _compute_inscrit_and_engage(self):
        for rec in self:
            total_credit_inscrit = 0.0
            total_engage = 0.0
            if rec.rubrique_id:
                total_credit_inscrit = sum(rec.tech_budget_id.tech_budget_line.filtered(lambda x: x.rubrique_id == rec.rubrique_id).mapped('credit_inscrit'))
                logs = self.env['engagement.log'].search([('tech_budget_id', '=', rec.tech_budget_id.id), ('rubrique_id', '=', rec.rubrique_id.id)])
                total_engage = sum(logs.mapped('montant_dengagement'))
            rec.credit_inscrit = total_credit_inscrit           
            rec.total_engage = total_engage 
            
    @api.depends('credit_inscrit', 'total_engage')
    def _compute_credit_disponible(self):
        for record in self:
            record.credit_disponible = record.credit_inscrit - record.total_engage
            
    # @api.onchange('tech_budget_id')
    # def _onchange_tech_budget_id(self):
    #     if self.tech_budget_id:
    #         nature_ids = self.tech_budget_id.tech_budget_line.mapped('nature_id').ids   
    #         return {'domain': {'nature_id': [('id', 'in', nature_ids)]}}
    #     return {}

    @api.onchange('tech_budget_id')
    def _onchange_budget_id(self):
        if self.tech_budget_id:
            rubrique_ids = self.tech_budget_id.tech_budget_line.mapped('rubrique_id').ids   
            return {'domain': {'rubrique_id': [('id', 'in', rubrique_ids)]}}
        return {}

    # def button_dummy(self):
    #     self._compute_inscrit_and_engage()
    #     return True
