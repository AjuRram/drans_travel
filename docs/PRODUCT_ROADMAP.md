# Product roadmap

## Phase 1 — Delivered MVP

- Client, agent, and admin authentication
- Organization and client onboarding APIs
- Profile and preference updates
- Multi-service travel requests
- Inventory search adapter
- Agent request management
- Booking, payment-order, invoice, and report APIs
- AI-assisted itinerary endpoint
- Responsive web dashboard

## Phase 2 — Pilot readiness

- Alembic database migrations
- Refresh tokens, password reset, MFA, and session revocation
- Email/SMS notifications and approval policies
- Document upload, OCR, passport/visa expiry reminders
- Real Amadeus test integration and supplier normalization
- Razorpay or Stripe test checkout and signed webhooks
- Invoice PDF rendering and tax configuration
- Agent quotation UI and request comments
- React Native client app

## Phase 3 — Commercial B2B product

- Multi-tenant row isolation and organization branding
- Corporate travel policy engine and approval chains
- Cost centers, departments, projects, and budget limits
- Negotiated hotel/air rates and markups
- Cancellations, refunds, exchanges, and reconciliation
- Supplier settlement and agent commissions
- GST/VAT invoices and accounting exports
- SLA dashboards, audit logs, and support desk

## Phase 4 — Intelligent platform

- Retrieval-based travel policy assistant
- Explainable offer ranking
- Disruption monitoring and proactive rebooking
- Spend forecasting and anomaly detection
- Personalized itineraries constrained by company policy
- Carbon estimates and lower-impact alternatives

## Phase 5 — Enterprise scale

- SSO/SCIM, granular roles, regional data residency
- High availability, disaster recovery, observability, and SLOs
- Security audits, penetration testing, and compliance program
- Multi-region provider routing and cached availability
- Public partner API and integration marketplace

## Production gates

No real payment or ticketing launch should occur until provider contracts,
verified webhooks, reconciliation, refund handling, privacy terms, security
testing, monitoring, backups, incident response, and customer support are ready.
