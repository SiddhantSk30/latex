{
    'name': 'Purchase Requisition New',
    'version': '16.0.1.0.0',
    'category': 'Purchases',
    'summary': 'Custom Purchase Requisition Workflow',
    'description': 'Adds purchase requisition workflow and approval groups.',
    'author': 'Your Company',
    'depends': ['base', 'mail', 'purchase', 'product'],
    'data': [
        'security/groups.xml',
        'data/sequence.xml',
        'views/purchase_requisition_menu.xml',
        'views/purchase_requisition_action.xml',
        'views/purchase_requisition_view.xml',
        # Access rights must be last so models are loaded before CSV is processed
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
}