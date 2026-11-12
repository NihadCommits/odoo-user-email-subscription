from odoo import models


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def _action_send_mail_comment(self, res_ids):
        # Hook B, part 1: the composer is the last place that still knows the
        # template. Pass it on to mail.thread._notify_get_recipients (part 2).
        if self.template_id:
            self = self.with_context(user_email_subscription_template_id=self.template_id.id)
        return super()._action_send_mail_comment(res_ids)
