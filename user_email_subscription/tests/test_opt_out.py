from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestOptOut(TransactionCase):
    """Anna stays subscribed, Ben opts out. Template sends to both."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.anna = new_test_user(cls.env, login='anna', email='anna@example.com')
        cls.ben = new_test_user(cls.env, login='ben', email='ben@example.com')
        cls.template = cls.env['mail.template'].create({
            'name': 'Report',
            'model_id': cls.env['ir.model']._get_id('res.partner'),
            'subject': 'Report',
            'use_default_to': False,  # Odoo 19 default: ignore partner_to, send to the record
            'partner_to': f'{cls.anna.partner_id.id},{cls.ben.partner_id.id}',
            'is_user_subscribable': True,
        })
        cls.ben.unsubscribed_template_ids = cls.template
        cls.customer = cls.env['res.partner'].create({'name': 'Customer'})

    def test_direct_send_skips_opted_out_user(self):
        mail = self.template.send_mail_batch(self.customer.ids)
        self.assertEqual(mail.recipient_ids, self.anna.partner_id)

    def test_follower_notification_skips_opted_out_user(self):
        self.customer.message_subscribe((self.anna | self.ben).partner_id.ids)
        message = self.customer.message_post_with_source(self.template, subtype_xmlid='mail.mt_comment')
        self.assertEqual(message.notification_ids.res_partner_id, self.anna.partner_id)

    def test_nobody_left_cancels_mail(self):
        self.anna.unsubscribed_template_ids = self.template
        mail = self.template.send_mail_batch(self.customer.ids)
        self.assertEqual(mail.state, 'cancel')
        self.assertNotIn(mail.mail_message_id, self.customer.message_ids)

    def test_toggle_is_logged_in_user_chatter(self):
        row = self.env['user.email.subscription'].search(
            [('user_id', '=', self.anna.id), ('template_id', '=', self.template.id)])
        row.with_user(self.anna).is_subscribed = False
        log = self.anna.message_ids[0]
        self.assertIn('Unsubscribed from e-mail template "Report"', log.body)
        self.assertEqual(log.author_id, self.anna.partner_id)

    def test_unflagged_template_reaches_everyone(self):
        self.template.is_user_subscribable = False
        mail = self.template.send_mail_batch(self.customer.ids)
        self.assertEqual(mail.recipient_ids, (self.anna | self.ben).partner_id)
