# Odoo – User Email Subscription

Odoo add-on `user_email_subscription/`: users can opt out of selected mail templates
directly on their user profile. Admins decide which templates are "user-subscribable";
the sending logic then skips users who opted out (also as followers).

> Work in progress – assessment case for Cloudunify.

## Local setup (Odoo 19)

```bash
docker compose up -d
docker compose run --rm odoo -d odoo -i mail,contacts --with-demo --stop-after-init
```

- Odoo: http://localhost:8069 (demo login `admin` / `admin`)
- Mailpit (catches every outgoing mail): http://localhost:8025
