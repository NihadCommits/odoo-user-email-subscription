{
    'name': 'User Email Subscription',
    'version': '19.0.1.0.0',
    'summary': 'Users can opt out of selected mail templates on their profile',
    'category': 'Productivity/Discuss',
    'author': 'NihadCommits',
    'depends': ['mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/user_email_subscription_security.xml',
        'views/user_email_subscription_views.xml',  # first: defines the action the others use
        'views/mail_template_views.xml',
        'views/res_users_views.xml',
    ],
    'license': 'LGPL-3',
}
