from odoo import models


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _notify_get_recipients(self, message, msg_vals=False, **kwargs):
        # Hook B, part 2 (chatter messages): Odoo collects the direct recipients
        # and the followers here. A mail.message does not know its template, so
        # the composer passes the template id in the context (part 1, wizard/).
        recipients = super()._notify_get_recipients(message, msg_vals=msg_vals, **kwargs)
        template_id = self.env.context.get('user_email_subscription_template_id')
        if not template_id:
            return recipients
        partner_ids, emails = self.env['mail.template'].browse(template_id)._get_unsubscribed_recipients()
        # Removed before Odoo splits into e-mail and inbox, so both channels are skipped.
        return [recipient for recipient in recipients
                if recipient['id'] not in partner_ids and recipient['email_normalized'] not in emails]
