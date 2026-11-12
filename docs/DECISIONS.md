# Architecture decisions

Short log of the main choices, why they were made and what else was possible.
"Planned" = agreed, not built yet.

## 1. Environment: Odoo 19 in Docker, Mailpit as mail catcher

- **Why:** Odoo Online cannot run custom Python modules. Odoo.sh needs a partner sandbox.
  19.0 is the established release (not the newest). The repo root is the addons path,
  so the same code runs on Odoo.sh unchanged.
- **Mailpit** catches every outgoing mail (web inbox on port 8025): proves in the demo
  that an opted-out user gets nothing, and no real mail ever leaves the machine.

## 2. Data model: opt-out pivot table + read-only SQL view

- **Stored:** only opt-outs, in the Many2many pivot table `user_email_subscription_optout_rel`
  (`mail.template.unsubscribed_user_ids` <-> `res.users.unsubscribed_template_ids`,
  same table seen from both sides). No row = subscribed.
- **Shown:** `user.email.subscription` is an SQL view (`_auto = False`, `_table_query`):
  every internal user x every subscribable template, with `is_subscribed = NOT EXISTS (opt-out row)`.
  Toggles, both smart buttons and both bulk actions use this one model, so both sides behave the same.
  Its `write()` turns a toggle into an insert/delete in the pivot table.
- **Alternatives:**
  - Computed Many2many + checkbox widget: least code, but no toggle list and separate
    smart-button logic per side.
  - TransientModel rows built on every open: extra cleanup, easy to get out of sync.
  - Real table with a row for every user x template: violates "store only opt-outs"
    and must be kept in sync on every new user/template.
- **Trade-off:** raw SQL and a cross join; fine for a prototype (performance is out of scope).

## 3. Send-path override in two places

One rule for both: drop every recipient that is the partner of an opted-out user or has
that user's e-mail address (`mail.template._get_unsubscribed_recipients`).

- **Hook A** `mail.template.send_mail_batch` (direct sending, e.g. report crons; `send_mail`
  calls it): build the mails without sending, remove opted-out users from `recipient_ids`,
  `email_to`, `email_cc`, then send. A mail with nobody left is **cancelled** (visible as
  "Cancelled" under Technical > Emails) instead of failing with "no recipient", and taken out
  of the record's chatter, where it would look delivered. Not deleted: `send_mail` returns its id.
  - First plan was `_generate_template_recipients` (also covers composer and preview), but
    it cannot cancel a mail that ends up empty. The composer is covered by Hook B anyway.
- **Hook B** chatter messages (composer, `message_post_with_source`), incl. followers:
  - part 1 `mail.compose.message._action_send_mail_comment` puts the template id into the context,
  - part 2 `mail.thread._notify_get_recipients` removes opted-out users. This runs before Odoo
    splits recipients into e-mail and inbox, so both channels are skipped.
  - Why a context key: `mail.message` and `mail.mail` have no template field in Odoo 19.
- **Why not one hook in `mail.mail._send`:** a `mail.mail` does not know its template,
  `force_send` sends before a later filter runs, and inbox notifications are not mails.
- **Known limits:** composer "mass mail" mode (one mail per selected record, used for
  customers) is not filtered; messages scheduled for later lose the context key.

## 4. Suppress on every channel

An opted-out template reaches the user neither by e-mail nor in the Odoo inbox.

## 5. Removing the flag keeps opt-outs, but ignores them

The flag (`is_user_subscribable`, set by the admin) is the main switch; the opt-out is the
user's personal choice. Without the flag the template is always sent. Setting the flag again
restores the old choices. Safe default: technical mails (e.g. 2FA codes) are never filtered.

## 6. Audit on the user's chatter

- `res.users` has no chatter in standard Odoo, so the module adds `mail.thread` to it and a
  `<chatter/>` to the user form. The partner's chatter would exist already, but it is a
  different record and not what the task asks for.
- Every real change (toggle, bulk action, profile) goes through `user.email.subscription.write()`,
  which logs a note with `_message_log`: author = who, date = when, text = which template.
  Notes notify nobody. Unchanged rows are not logged.
- Risk check: no Odoo app in this image reads user chatter fields; Odoo's own user tests
  (mail: 21, base: 25 of 26) pass. The one base error happens before `mail` is loaded and is
  about the mail column `notification_type`, not about this module.
- Side effect: template mails rendered on a user (e.g. the weekly report) now also show in
  that user's chatter, like on any other record with a chatter.

## 7. Security

- Employees read and toggle only their own rows (record rule `user_id = user.id`);
  user admins (`base.group_erp_manager`) see all rows.
- `write()` checks these rules first, then writes the pivot table with `sudo()`
  (employees may not edit `res.users` fields directly).
- Employees edit the tab on their own profile (avatar menu > Preferences): the field is in
  `SELF_WRITEABLE_FIELDS`, so Odoo saves it with `sudo()`. That would skip record rules,
  so `write()` checks with `sudo(False)`, i.e. as the real user. Tested: an employee cannot
  smuggle another user's row into their own profile save.

## 8. UI: one list, one action, two smart buttons

- Both smart buttons open the same window action on `user.email.subscription`; they only
  differ in the filter they pass (`search_default_user_id` / `search_default_template_id`
  + `search_default_unsubscribed`). No Python needed for the buttons, and both sides
  behave the same by construction.
- Filters are removable facets (standard Odoo), so the user side can also bulk-unsubscribe.
- Bulk actions are `<header>` buttons of the list (shown when rows are selected).
  Alternative: server actions in the "Actions" menu - more XML, same result.
- The tab is added to the admin form and to the Preferences form (the user's own profile).

## 9. Demo data and tests

- `data/user_email_subscription_demo.xml` (loaded only with demo data): "Weekly Report" sent by
  a cron to every internal user (Hook A), "Contact Update" posted on "Azure Interior", which
  Marc Demo follows (Hook B). Both templates have `use_default_to = False`: in Odoo 19 a
  template otherwise ignores `partner_to` and writes to the record itself.
- Tests were out of scope, but the core rule has 5 short tests (`tests/test_opt_out.py`):
  direct send, follower notification, cancelled empty mail, audit note, unflagged template.
