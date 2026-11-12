from odoo import fields, models
from odoo.tools.mail import email_normalize, email_split_and_format


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

    def _get_unsubscribed_recipients(self):
        """Partner ids and normalized e-mails of the users who opted out.

        Used by both send hooks. Empty when the admin has not flagged the template:
        the opt-outs are then kept but ignored, so the template reaches everyone.
        """
        if not self.is_user_subscribable:
            return set(), set()
        partners = self.sudo().unsubscribed_user_ids.partner_id
        return set(partners.ids), {email for email in partners.mapped('email_normalized') if email}

    def send_mail_batch(self, res_ids, force_send=False, raise_exception=False, email_values=None,
                        email_layout_xmlid=False):
        # Hook A (direct sending, e.g. a report cron): let Odoo build the mails
        # without sending, remove opted-out users, then send what is left.
        mails = super().send_mail_batch(
            res_ids, force_send=False, raise_exception=raise_exception,
            email_values=email_values, email_layout_xmlid=email_layout_xmlid)
        partner_ids, emails = self._get_unsubscribed_recipients()
        if partner_ids:
            for mail in mails:
                mail.recipient_ids = mail.recipient_ids.filtered(
                    lambda partner: partner.id not in partner_ids and partner.email_normalized not in emails)
                mail.email_to = self._remove_emails(mail.email_to, emails)
                mail.email_cc = self._remove_emails(mail.email_cc, emails)
                if not (mail.recipient_ids or mail.email_to or mail.email_cc):
                    mail.cancel()  # nobody left: shows as "Cancelled" instead of a send error
        if force_send:
            mails.send(raise_exception=raise_exception)
        return mails

    def _remove_emails(self, addresses, emails):
        """'"Marc" <marc@x.com>, anna@y.com' without marc@x.com -> 'anna@y.com'"""
        kept = [address for address in email_split_and_format(addresses or '')
                if email_normalize(address) not in emails]
        return ', '.join(kept)
