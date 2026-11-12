# Odoo – User Email Subscription

Odoo 19 add-on [`user_email_subscription/`](user_email_subscription/): users opt out of selected
mail templates directly on their user profile. Admins decide which templates are "user-subscribable";
the sending logic skips users who opted out, also as followers. Every change is logged in the
user's chatter.

- What the module does and how: [`user_email_subscription/README.md`](user_email_subscription/README.md)
- Architecture decisions and alternatives: [`docs/DECISIONS.md`](docs/DECISIONS.md)

## Local setup (Docker)

```bash
docker compose run --rm odoo -d odoo -i contacts,user_email_subscription --with-demo --load-language=de_DE --stop-after-init
docker compose up -d
```

- Odoo: http://localhost:8069 (demo logins `admin` / `admin` and `demo` / `demo`)
- Mailpit, catches every outgoing mail: http://localhost:8025
- German UI: avatar menu > Preferences > Language > Deutsch

The repository root is the addons path, so the same code runs on Odoo.sh unchanged.

## Tests

```bash
docker compose run --rm odoo -d odoo -u user_email_subscription --test-tags /user_email_subscription --stop-after-init
```

## Demo walkthrough

Logged in as `admin`, developer mode on (`?debug=1` in the URL).

1. **Admin flags templates.** Settings > Technical > Email Templates > *Weekly Report*:
   "User Subscription Possible" is set (demo data). The smart button shows the opted-out users.
2. **User opts out.** Settings > Users > *Marc Demo* > tab *Notifications*: switch off
   *Weekly Report* and *Contact Update*, save. The chatter below logs who, when and which template.
   (Self-service: log in as `demo`, avatar menu > Preferences > *Notifications*.)
3. **Direct send.** Settings > Technical > Scheduled Actions > *Demo: Send Weekly Report* >
   *Run Manually*. Mailpit: only `admin@example.com` got the report. Settings > Technical > Emails:
   Marc's mail is *Cancelled*.
4. **Follower.** Contacts > *Azure Interior* (Marc follows it) > *Send message*. Remove the
   suggested recipient (the contact itself), open the full composer, menu ⋮ > template
   *Contact Update*, *Send*. Mailpit: nothing for `mark.brown23@example.com`
   (while subscribed, Marc gets "Update on Azure Interior").
5. **Bulk re-subscribe.** Template *Weekly Report* > smart button *Unsubscribed* > select Marc >
   *Subscribe*. Run step 3 again: Marc gets the report, his chatter shows the change.
6. **Admin removes the flag.** The template disappears from the users' tab and is sent to
   everyone again; the opt-outs are kept and apply again when the flag is set.

## Repository

| Path | Content |
|---|---|
| `user_email_subscription/` | the Odoo add-on |
| `docs/DECISIONS.md` | decision log: data model, override strategy, security, limits |
| `docker-compose.yml` | Odoo 19 + PostgreSQL + Mailpit for local development |
| `CLAUDE.md` | project context for AI coding agents (how to run, verify, conventions) |
