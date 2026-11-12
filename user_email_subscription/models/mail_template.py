from odoo import fields, models


class MailTemplate(models.Model):
    _inherit = 'mail.template'

    is_user_subscribable = fields.Boolean(
        string='User Subscription Possible',
        help='Users can opt out of this template on their user profile.',
    )
    # Pivot table: one row = one user who opted out of this template.
    # Same table as res.users.unsubscribed_template_ids, seen from the other side.
    unsubscribed_user_ids = fields.Many2many(
        'res.users',
        relation='user_email_subscription_optout_rel',
        column1='template_id',
        column2='user_id',
        string='Unsubscribed Users',
        copy=False,  # a duplicated template starts without opt-outs
    )
    email_subscription_ids = fields.One2many('user.email.subscription', 'template_id')
    unsubscribed_count = fields.Integer(compute='_compute_unsubscribed_count')

    def _compute_unsubscribed_count(self):
        for template in self:
            template.unsubscribed_count = len(
                template.email_subscription_ids.filtered(lambda row: not row.is_subscribed))
