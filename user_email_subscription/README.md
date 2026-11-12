# User Email Subscription

Odoo 19 add-on: users decide on their profile which mail templates they receive.
Opt-out principle: a template the admin has flagged reaches everyone, unless a user switches it off.

## Features

| Area | What it does | Where |
|---|---|---|
| Admin | Flag **User Subscription Possible** on a mail template; only flagged templates are offered to users | `models/mail_template.py`, `views/mail_template_views.xml` |
| Admin | Smart button on the template: users who opted out, bulk **Subscribe** / **Unsubscribe** | `views/user_email_subscription_views.xml` |
| User | Tab **Notifications** with one toggle per flagged template, on by default (admin user form and own Preferences) | `views/res_users_views.xml` |
| User | Smart button on the user: templates the user opted out of, same bulk actions | `views/res_users_views.xml` |
| Sending | Opted-out users are removed when a template is sent directly or posted in a chatter, also as followers, on e-mail and inbox | `models/mail_template.py`, `models/mail_thread.py`, `wizard/mail_compose_message.py` |
| Audit | Every change is logged in the user's chatter: who, when, which template | `models/user_email_subscription.py` |

## How it works

```
 mail.template  <──── user_email_subscription_optout_rel ────>  res.users
 (flag)               one row = one opt-out (nothing else is stored)

 user.email.subscription  (SQL view, read model)
   every internal user x every flagged template, is_subscribed = no opt-out row
   -> toggles, both smart buttons, bulk actions; write() turns a toggle into
      an insert/delete in the pivot table and logs it in the user's chatter

 Sending
   A  send_mail_batch          direct sending (e.g. report cron): remove opted-out
                               recipients, cancel a mail with nobody left
   B  composer -> context      chatter messages: _notify_get_recipients removes
      _notify_get_recipients   opted-out recipients and followers
```

Why it is built this way, with alternatives: [`docs/DECISIONS.md`](../docs/DECISIONS.md).

## Module structure

```
user_email_subscription/
├── __manifest__.py
├── models/
│   ├── mail_template.py             flag, pivot field, hook A, shared opt-out rule
│   ├── mail_thread.py               hook B part 2 (recipients and followers)
│   ├── res_users.py                 pivot field, tab rows, chatter, self-edit rights
│   └── user_email_subscription.py   SQL view: toggles, bulk actions, audit note
├── wizard/mail_compose_message.py   hook B part 1 (template id into context)
├── views/                           template form, user forms, subscription list
├── security/                        access rights + record rules (own rows only)
├── data/                            demo data: weekly report cron, contact update, follower
├── i18n/de.po                       German translation
└── tests/test_opt_out.py            5 tests for the core rule
```

## Known limits

- Composer "mass mail" mode (one mail per selected record, meant for customers) is not filtered.
- Messages scheduled for later lose the template id in the context and are not filtered.
- View row id = `user_id * 100000 + template_id`: unique while template ids stay below 100000.
- Performance with very many users x templates was out of scope.
