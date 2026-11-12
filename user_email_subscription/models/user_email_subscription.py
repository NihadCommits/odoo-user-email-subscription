from odoo import Command, fields, models
from odoo.tools import SQL


class UserEmailSubscription(models.Model):
    """One row per internal user x subscribable template, with its on/off state.

    Nothing is stored here: the rows come from the SQL query below, which reads
    the opt-out pivot table. A template without an opt-out row is "subscribed".
    """
    _name = 'user.email.subscription'
    _description = 'User Email Subscription'
    _auto = False  # no table of its own, see _table_query
    _order = 'user_id, template_id'

    user_id = fields.Many2one('res.users', string='User', readonly=True)
    template_id = fields.Many2one('mail.template', string='Template', readonly=True)
    is_subscribed = fields.Boolean(string='Subscribed')

    # Tells Odoo which pending changes to save to the database before reading
    # this query, so it never shows an outdated state.
    _depends = {
        'res.users': ['active', 'share', 'unsubscribed_template_ids'],
        'mail.template': ['active', 'is_user_subscribable'],
    }

    @property
    def _table_query(self):
        # shortcut: id = user_id * 100000 + template_id (user 5, template 12 -> 500012)
        # stays unique while template ids < 100000; use a real table if that ever changes.
        return SQL("""
            SELECT u.id::bigint * 100000 + t.id AS id,
                   u.id AS user_id,
                   t.id AS template_id,
                   NOT EXISTS (
                       SELECT 1 FROM user_email_subscription_optout_rel optout
                        WHERE optout.user_id = u.id AND optout.template_id = t.id
                   ) AS is_subscribed
              FROM res_users u
             CROSS JOIN mail_template t
             WHERE t.is_user_subscribable AND t.active
               AND u.active AND NOT u.share
        """)

    def write(self, vals):
        # A query cannot be updated, so a toggle becomes an insert or delete
        # in the pivot table. Record rules decide whose rows may be changed;
        # sudo(False) because the profile form saves through sudo() (see res_users.py).
        self.sudo(False).check_access('write')
        if 'is_subscribed' in vals:
            command = Command.unlink if vals['is_subscribed'] else Command.link
            for row in self:
                row.user_id.sudo().unsubscribed_template_ids = [command(row.template_id.id)]
        self.invalidate_recordset()  # re-read the query on next access
        return True

    # Bulk actions: header buttons of the list, run on the selected rows.
    def action_subscribe(self):
        self.write({'is_subscribed': True})

    def action_unsubscribe(self):
        self.write({'is_subscribed': False})
