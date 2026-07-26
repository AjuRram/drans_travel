# Architecture

## System context

```text
Next.js web / React Native app
                 │
                 ▼
          FastAPI REST API
        ┌────────┼─────────┐
        ▼        ▼         ▼
   PostgreSQL  Provider   Payment
               adapters   adapters
                 │          │
       Amadeus / weather   Stripe /
       inventory / mock    Razorpay / mock
```

## Roles

- **Client:** update profile, create and edit requests, search inventory, view
  bookings and invoices, initiate payment.
- **Agent:** view all client requests, quote, approve, assign, book, and report.
- **Admin:** all agent functions plus organization and user onboarding.

## Request lifecycle

```text
submitted → reviewing → quoted → approved → booked
     └──────────────────────────────→ cancelled
```

Clients can modify submitted or reviewing requests. Agents and administrators
control status, quote, assignment, and booking.

## Data model

Organizations own users. Client users own travel requests. Each request can
produce bookings, and each booking can have payments and one invoice. JSON fields
store provider-specific preferences and inventory details without coupling the
core domain to one supplier.

## Provider integration strategy

Every external supplier should implement a stable internal interface:

1. Normalize a search request.
2. Authenticate to the supplier.
3. Convert supplier offers into the VoyageAI inventory schema.
4. Reprice before booking.
5. Create a booking and store supplier reference.
6. Process signed webhooks for changes/cancellations.

The default mock provider makes development deterministic. Amadeus test APIs can
be enabled for flight and hotel shopping with credentials. Bus, cab, hotel, and
event production suppliers vary by country and normally require commercial
onboarding.

## Mobile plan

The REST API is frontend-independent. The React Native application can share:

- OpenAPI-generated API types
- authentication/session rules
- design tokens
- validation schemas
- analytics event names

It should use secure device storage for access tokens and deep links for payment
returns.
