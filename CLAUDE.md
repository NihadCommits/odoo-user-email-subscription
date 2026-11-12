# Project context for AI coding agents

Odoo 19 add-on `user_email_subscription/`: users opt out of selected mail templates.
Task, decisions and trade-offs: see `docs/DECISIONS.md`. Keep it updated when a decision changes.

## Run and verify
- `docker compose up -d` -> Odoo http://localhost:8069, Mailpit http://localhost:8025
- Update module: `docker compose run --rm odoo -d odoo -u user_email_subscription --stop-after-init`, then `docker compose restart odoo`
- Tests: `MSYS_NO_PATHCONV=1 docker compose run --rm odoo -d odoo -u user_email_subscription --test-tags /user_email_subscription --stop-after-init` (Git Bash would rewrite `/user_email_subscription` into a Windows path)
- Quick checks: `docker compose run --rm -T odoo odoo shell -d odoo --no-http < script.py` (no commit = rolled back; add `--smtp=mailpit --smtp-port=1025` to really send)
- Demo data (`data/*_demo.xml`) loads only on install, not on `-u`: reinstall the module after changing it.

## Conventions
- Odoo 19 syntax: `<list>` (not `<tree>`), `invisible="..."` (not `attrs`), `Command.*` for x2many writes.
- Code in English, readable for a junior: small methods, comments only for the "why".
- Known limits get a `shortcut: <limit>, <when to upgrade>` comment.
- Verify every behaviour against the running Odoo 19 source before claiming it works.
