from odoo import fields, models


class ResUsers(models.Model):
    _name = 'res.users'
    # mail.thread gives users their own chatter for the audit trail
    # (standard Odoo users have none; the partner's chatter is a different record).
    _inherit = ['res.users', 'mail.thread']

    # Same pivot table as mail.template.unsubscribed_user_ids, columns swapped.
    unsubscribed_template_ids = fields.Many2many(
        'mail.template',
        relation='user_email_subscription_optout_rel',
        column1='user_id',
        column2='template_id',
        string='Unsubscribed Templates',
        copy=False,  # a duplicated user starts subscribed to everything
    )
    # The rows of the "Notifications" tab, one per subscribable template.
    email_subscription_ids = fields.One2many(
        'user.email.subscription', 'user_id', string='Email Subscriptions')
    unsubscribed_count = fields.Integer(compute='_compute_unsubscribed_count')

    def _compute_unsubscribed_count(self):
        for user in self:
            user.unsubscribed_count = len(
                user.email_subscription_ids.filtered(lambda row: not row.is_subscribed))

    # Employees may not edit res.users. These lists let them read and save the
    # tab on their own profile ("Preferences"); Odoo then writes with sudo().
    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ['email_subscription_ids']

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ['email_subscription_ids']
