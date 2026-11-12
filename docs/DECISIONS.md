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

## 3. Send-path override in two places (planned)

- **Hook A** `mail.template._generate_template_recipients`: drop opted-out users' partners
  and e-mail addresses from the computed recipients (direct `send_mail`, composer, preview).
- **Hook B** `mail.compose.message` puts the template id into the context;
  `mail.thread._notify_get_recipients` drops opted-out users, including followers.
- **Why not one hook in `mail.mail._send`:** a `mail.mail` does not know its template,
  `force_send` sends before a later filter runs, and inbox notifications are not mails.

## 4. Suppress on every channel

An opted-out template reaches the user neither by e-mail nor in the Odoo inbox.

## 5. Removing the flag keeps opt-outs, but ignores them

The flag (`is_user_subscribable`, set by the admin) is the main switch; the opt-out is the
user's personal choice. Without the flag the template is always sent. Setting the flag again
restores the old choices. Safe default: technical mails (e.g. 2FA codes) are never filtered.

## 6. Audit on the user's chatter (planned)

`res.users` has no chatter in standard Odoo. Plan: add `mail.thread` to `res.users` and post
"who / when / which template" there. Fallback: the related partner's chatter.

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
