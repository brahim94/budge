# -*- coding: utf-8 -*-

{
    "name": "Tech Budget",
    "author": "Warlock Technologies",
    "description": """Tech Budget""",
    "summary": """Tech Budget""",
    "version": "1.10",
    "support": "info@warlocktechnologies.com",
    "website": "http://warlocktechnologies.com",
    "license": "LGPL-3",
    "category": "Budget",
    "depends": ["base", "wt_purchase_request_extend"],
    "data": [
        "security/ir.model.access.csv",
        "data/budget_seq.xml",
        "views/tech_budget.xml",
        "views/suivi_engagement_view.xml",
        "views/parameter_nature_view.xml",
        "views/rubrique_budget_view.xml",
        "views/market_execution_view.xml",
    ],
    "demo": [  
    ],
    "installable": True,
}
