# Deployment

## Current public demo

- URL: <https://voyageai-b2b-travel.atsdev7.chatgpt.site>
- Hosting: OpenAI Sites on an edge runtime
- Application mode: static Next.js export with `NEXT_PUBLIC_DEMO_MODE=true`
- Data mode: fictional seed data persisted in the visitor's browser
- Production release: Sites version 2

This public deployment is intended for portfolio review and workflow
demonstration. It includes client, agent, and administrator experiences without
requiring a public database. It does not submit real bookings, charge cards, or
send data to external travel suppliers.

## Demo access

| Role | Email | Password |
|---|---|---|
| Administrator | `admin@voyageai.demo` | `Admin123!` |
| Agent | `agent@voyageai.demo` | `Agent123!` |
| Client | `client@acme.demo` | `Client123!` |

## Public-demo build

From `frontend`:

```powershell
$env:NEXT_PUBLIC_DEMO_MODE = "true"
$env:DEPLOY_STATIC_EXPORT = "true"
npm run build
```

The static output is generated in `frontend/out`. `frontend/deploy-worker.js`
is the edge-safe asset entrypoint used by the hosted version. The hosting
project identifier is kept in `.openai/hosting.json`; credentials and secrets
must never be committed there.

## Full production topology

```text
Browser / mobile app
        |
        v
Next.js web application
        |
        v
FastAPI REST API
   |          |
   v          v
PostgreSQL   Travel/payment provider APIs
```

Deploy the components separately for a real multi-user environment:

1. Provision managed PostgreSQL with backups, encryption, and restricted
   network access.
2. Deploy `backend` behind HTTPS and run database migrations.
3. Configure an approved travel inventory provider and payment gateway using
   their sandbox credentials first.
4. Deploy `frontend` with `NEXT_PUBLIC_DEMO_MODE=false` and
   `NEXT_PUBLIC_API_URL` set to the public FastAPI URL.
5. Restrict CORS with `FRONTEND_ORIGIN`, rotate `JWT_SECRET`, and keep every
   provider key in the hosting platform's secret store.
6. Add monitoring, audit-log retention, rate limiting, and restore testing
   before onboarding real organizations.

Important backend settings are documented in the root
[README](../README.md#environment-configuration). Use `.env.example` files as
templates; never commit populated `.env` files.

## Release verification

Before publishing a release:

```powershell
cd backend
python -m pytest

cd ..\frontend
npm test
npm run build
```

After deployment, verify:

- the public URL returns HTTP 200;
- each demo role can sign in;
- a client can create and modify a travel request;
- an administrator can view requests and organization/reporting screens;
- browser developer tools show no failed application requests;
- no secrets or real customer data are present in the static assets.

## Rollback

Hosting releases are immutable saved versions. If a release fails smoke
testing, redeploy the most recent verified Sites version. Database-backed
production releases should pair each application release with a reversible
migration plan and a tested database backup.
