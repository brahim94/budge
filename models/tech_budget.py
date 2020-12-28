# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class EngagementLog(models.Model):
    _name = 'engagement.log'
    _description = 'Engagement Log'

    dengagement = fields.Char(string="N° d'engagement")
    date = fields.Datetime(string="Date d'engagement")
    montant_dengagement = fields.Float(string="Montant d'engagement")
    contrat_type_id = fields.Many2one('purchase.requisition.type', string="Type Contrat")
    ref_operation = fields.Char(string="Ref Opération")
    type_budget = fields.Selection([('chb', 'CHB'), ('functionment', 'Fonctionnement'), ('investment', 'Investissement')],string="Type Budget")
    tech_budget_id = fields.Many2one('tech.budget', string="Budget")
    nature_id = fields.Many2one('parameter.nature', string="Nature")
    rubrique_id = fields.Many2one('rubrique.budget', string="Rubrique")
    # state = fields.Selection([('new', 'New')], default="new", string="State")
    suivi_engagements_id = fields.Many2one('suivi.engagements', string="Suivi Engagements")
    
    # @api.depends("tech_budget_id")
    # def _compute_suivi_engagements_id(self):
    #     suivi_obj = self.env['suivi.engagements']
    #     for rec in self:
    #         suivi_engagement = suivi_obj.search([('tech_budget_id', '=', rec.tech_budget_id.id)], limit=1)

    #         if rec and suivi_engagement:
    #             rec.suivi_engagements_id = suivi_engagement.id


class SuiviEngagements(models.Model):
    _name = 'suivi.engagements'
    _description = 'Suivi Engagements'
    _rec_name = 'tech_budget_id'

    tech_budget_id = fields.Many2one('tech.budget', string="Budget", required="True")
    credit_inscrit = fields.Integer(string='Crédit Inscrit', required="True", compute="_compute_credit_inscrit")
    total_engage = fields.Integer(string='Total Engagé', required="True", compute="_compute_credit_inscrit")
    credit_disponible = fields.Integer(string='Crédit Disponible', required="True", compute="_compute_credit_inscrit")
    engagement_log_ids = fields.One2many('engagement.log', 'suivi_engagements_id', string="Suivi Engagements")
    type_budget = fields.Selection([('chb', 'CHB'), ('functionment', 'Fonctionnement'), ('investment', 'Investissement')], default="chb", required=True, string="Type Budget")

    @api.depends("engagement_log_ids")
    def _compute_credit_inscrit(self):
        for rec in self:
            credit_inscrit, total_engage = 0.0, 0.0
            for log in rec.engagement_log_ids:
                if log.tech_budget_id and log.tech_budget_id.tech_budget_line:
                    credit_inscrit += sum([line.credit_inscrit for line in log.tech_budget_id.tech_budget_line])
                if log.montant_dengagement:
                    total_engage += log.montant_dengagement
            rec.credit_inscrit = credit_inscrit
            rec.total_engage = total_engage
            rec.credit_disponible = credit_inscrit - total_engage

    @api.constrains('tech_budget_id')
    def _constraint_tech_budget(self):
        for record in self:
            if record and self.search_count([('tech_budget_id', '=' , record.tech_budget_id.id)]) > 1:
                raise UserError(_("engager is already listed with selected Budget!"))


class ParameterNature(models.Model):
    _name = 'parameter.nature'
    _description = 'Parameter Nature'

    name = fields.Char(string='Nom', required="True")
    code = fields.Char(string='Code', required="True")


class ParameterRubriques(models.Model):
    _name = 'rubrique.budget'
    _description = 'Rubriques Budgétaire'

    name = fields.Char(string='Nom', required="True")
    code = fields.Char(compute='_compute_rubrique_code', string='Code')
    type_budget = fields.Selection([('chb', 'CHB'), ('functionment', 'Fonctionnement'), ('investment', 'Investissement')], default="chb", string='Type', required="True")
    # nature_id = fields.Many2one('parameter.nature', string='Nature', required="True")
    cgnc = fields.Char(string='CGNC')
    paragraphe = fields.Char(string='Paragraphe')
    ligne = fields.Char(string='Ligne')

    @api.depends('cgnc', 'paragraphe', 'ligne')
    def _compute_rubrique_code(self):
        for record in self:
            name = ''
            name += record.cgnc or ''
            name += ('-' + record.paragraphe) if name and record.paragraphe else (record.paragraphe or '')
            name += ('-' + record.ligne) if name and record.ligne else (record.ligne or '')
            record.code = name


class TechBudget(models.Model):
    _name = 'tech.budget'
    _description = 'Tech Budget'

    @api.model
    def create(self, vals):
        vals['sequence'] = self.env["ir.sequence"].next_by_code("tech.budget")
        return super(TechBudget, self).create(vals)

    state = fields.Selection([('actif', 'Actif'), ('ferme', 'fermé')], default="actif", string="State")
    sequence = fields.Char(string='Sequence', readonly="1")
    name = fields.Char(string='Référence', readonly="1", compute="_compute_is_name")
    list_of_years = fields.Integer(string='Année', required="True")
    type_budget = fields.Selection([('chb', 'CHB'), ('functionment', 'Fonctionnement'), ('investment', 'Investissement')], default='chb', string='Type', required="True")
    date_debut = fields.Date(string="Date Début")   
    date_fin = fields.Date('Date fin')
    plafond_nature = fields.Float('Plafond Nature')
    tech_budget_line = fields.One2many('tech.budget.line', 'tech_budget_id', string="Budget Line")

    @api.constrains('date_debut', 'date_fin')
    def _constraint_date(self):
        for record in self:
            if record.date_debut and record.date_fin and not (record.date_debut < record.date_fin):
                raise UserError(_("You can not add start date greater than to end date !"))

    @api.depends("sequence", "list_of_years", "type_budget")
    def _compute_is_name(self):
        for rec in self:
            type_budget = ''
            if rec.type_budget == 'chb':
                type_budget = 'C'
            elif rec.type_budget == 'functionment':
                type_budget = 'F'
            elif rec.type_budget == 'investment':
                type_budget = 'I'
            rec.name = str(type_budget) + '-' + str(rec.list_of_years) + '-' + str(rec.sequence)


class TechBudgetLine(models.Model):
    _name = 'tech.budget.line'
    _description = 'Tech Budget Line'

    # nature_id = fields.Many2one('parameter.nature', string='Nature', required=True)
    rubrique_id = fields.Many2one('rubrique.budget', string='Rubrique', required=True)
    credit_inscrit = fields.Float(string='Crédit inscrit', required=True)
    tech_budget_id = fields.Many2one('tech.budget', string='Budget')
    type_budget = fields.Selection(related='tech_budget_id.type_budget', string='Type Budget')

    # @api.onchange('nature_id')
    # def _onchange_nature_id(self):
    #     if self.nature_id:
    #         rubrique_lists = []
    #         rubrique_ids = self.env['rubrique.budget'].search([])   
    #         for rubrique in rubrique_ids:
    #             if rubrique.type_budget == self.tech_budget_id.type_budget:
    #                 rubrique_lists.append(rubrique.id)
    #         return {'domain': {'rubrique_id': [('id', 'in', rubrique_lists)]}}
    #     return {}
