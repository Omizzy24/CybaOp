# Implementation Plan: Stripe Billing Integration

## Overview

Replace CybaOp's mock billing flow with real Stripe integration. Tasks are ordered for incremental delivery: backend foundation first (schema, config, deps, error types, models), then DB queries, then billing service endpoints (checkout, portal, webhook, mock removal), JWT refresh, and finally frontend proxy routes and Pro page UI. Each group is followed by a checkpoint.

## Tasks

- [ ] 1. Backend foundation — schema, config, dependency, error types, and models
  - [ ] 1.1 Add `stripe` and `hypothesis` dependencies to `backend/pyproject.toml`
    - Add `stripe>=8.0.0` to `[project.dependencies]`
    - Add `hypothesis>=6.100.0` to `[project.optional-dependencies] dev`
    - _Requirements: 2.1, 16.2_

  - [ ] 1.2 Add Stripe settings to `backend/src/shared/config.py`
    - Add `stripe_secret_key: str = ""`, `stripe_webhook_secret: str = ""`, `stripe_pro_price_id: str = ""` to the `Settings` class
    - All default to empty string so the app starts without them
    - _Requirements: 2.1, 2.2, 2.3, 2.5_

  - [ ] 1.3 Add Stripe columns to database schema in `backend/src/db/schema.py`
    - Add `stripe_customer_id TEXT`, `stripe_subscription_id TEXT`, `subscription_status TEXT`, `subscription_ends_at TIMESTAMPTZ` to the `CREATE TABLE IF NOT EXISTS users` statement
    - Add a new `SCHEMA_SQL_BILLING` block with `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` for each column and partial indexes on `stripe_customer_id` and `stripe_subscription_id`
    - Call `await conn.execute(SCHEMA_SQL_BILLING)` in `initialize_schema()`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 16.2_

  - [ ] 1.4 Add `StripeError` to `backend/src/shared/errors.py` and register in error handler
    - Add `StripeError(CybaOpError)` with error_code `STRIPE_ERROR`
    - Add `"STRIPE_ERROR": 502` to `STATUS_MAP` in `backend/src/api/middleware/error_handler.py`
    - _Requirements: 3.9_

  - [ ] 1.5 Add Pydantic response models to `backend/src/shared/models.py`
    - Add `BillingStatusResponse`, `CheckoutResponse`, `PortalResponse` models
    - _Requirements: 12.1, 12.2, 12.3, 12.4_

  - [ ]* 1.6 Write property test for `_tier_features` backward compatibility
    - **Property 15: _tier_features backward compatibility**
    - **Validates: Requirements 16.3**

- [ ] 2. Checkpoint — Verify foundation
  - Ensure all 77 existing tests pass with `PYTHONPATH=backend python3.11 -m pytest backend/tests/unit/ -x -q`
  - Ensure no import errors from new models/errors
  - Ask the user if questions arise.

- [ ] 3. Database query functions for Stripe fields
  - [ ] 3.1 Add `get_user_by_stripe_customer()` to `backend/src/db/queries.py`
    - Query users table by `stripe_customer_id`, return dict or None
    - _Requirements: 9.1_

  - [ ] 3.2 Add `get_user_by_stripe_subscription()` to `backend/src/db/queries.py`
    - Query users table by `stripe_subscription_id`, return dict or None
    - _Requirements: 7.1, 8.1_

  - [ ] 3.3 Add `update_user_stripe_info()` to `backend/src/db/queries.py`
    - Accept optional kwargs: `stripe_customer_id`, `stripe_subscription_id`, `subscription_status`, `subscription_ends_at`, `tier`
    - Build dynamic UPDATE query for only the provided fields plus `updated_at = NOW()`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 6.2, 6.3, 7.1, 8.1, 8.2, 8.3_

  - [ ]* 3.4 Write property test for Stripe field storage round-trip
    - **Property 1: Stripe field storage round-trip**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

- [ ] 4. Billing service — checkout, portal, webhook, mock removal
  - [ ] 4.1 Refactor `backend/src/api/routes/billing.py` — update `/billing/status` to read from DB
    - Change `billing_status` to fetch user from DB via `get_user(user_id)`
    - Determine `is_pro` from DB `tier` column (not JWT claim)
    - Include `subscription_status`, `subscription_ends_at`, and `warning` (if `past_due`) in response
    - Preserve `_tier_features()` function unchanged
    - Use `BillingStatusResponse` model
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 16.1, 16.3_

  - [ ]* 4.2 Write property test for billing status reflects database state
    - **Property 13: Billing status reflects database state**
    - **Validates: Requirements 12.1, 12.2, 12.3, 12.4, 16.1**

  - [ ] 4.3 Implement `POST /billing/checkout` endpoint
    - Validate user is not already `active` subscriber (return 400 if so)
    - Check Stripe config is present (return 503 if missing)
    - Get or create Stripe Customer (store `stripe_customer_id` if new)
    - Create Checkout Session with `mode=subscription`, `price_id`, `metadata={"user_id": ...}`, `success_url`, `cancel_url`
    - Return `CheckoutResponse` with session URL
    - Catch `stripe.error.StripeError` and raise `StripeError`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9_

  - [ ]* 4.4 Write property tests for checkout
    - **Property 3: Checkout session creation correctness**
    - **Property 4: Checkout rejects already-active subscribers**
    - **Property 5: Stripe Customer creation vs reuse**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8**

  - [ ] 4.5 Implement `POST /billing/portal` endpoint
    - Validate user has `stripe_customer_id` (return 400 if missing)
    - Validate user is Pro tier (return 403 if not)
    - Create Stripe Portal Session with `customer` and `return_url`
    - Return `PortalResponse` with portal URL
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [ ]* 4.6 Write property test for portal session creation
    - **Property 14: Portal session creation for Pro users**
    - **Validates: Requirements 10.1, 10.2, 10.3**

  - [ ] 4.7 Implement `POST /billing/webhook` endpoint with signature verification and event dispatch
    - Read raw body and `Stripe-Signature` header
    - Verify with `stripe.Webhook.construct_event()`; return 400 on failure
    - Dispatch `checkout.session.completed`: extract `user_id` from metadata, set tier=pro, status=active, store sub_id (idempotent: skip if already active with same sub_id)
    - Dispatch `customer.subscription.updated`: find user by sub_id, update subscription_status
    - Dispatch `customer.subscription.deleted`: find user by sub_id, set tier=free, status=canceled, clear sub_id, set ends_at (idempotent: skip if already free)
    - Dispatch `invoice.payment_failed`: find user by customer_id, set status=past_due
    - Unknown events: log and return 200
    - Always return 200 after successful signature verification (even on internal errors)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.5, 7.1, 7.2, 7.3, 8.1, 8.2, 8.3, 9.1, 9.2, 15.1, 15.2, 15.3_

  - [ ]* 4.8 Write property tests for webhook processing
    - **Property 2: Webhook signature verification gate**
    - **Property 6: checkout.session.completed upgrades user**
    - **Property 7: customer.subscription.updated syncs status**
    - **Property 8: customer.subscription.deleted downgrades user**
    - **Property 9: invoice.payment_failed sets past_due**
    - **Property 10: Checkout idempotency**
    - **Property 11: Deletion idempotency**
    - **Validates: Requirements 5.2, 5.3, 6.2, 6.3, 7.1, 7.2, 7.3, 8.1, 8.2, 8.3, 9.1, 15.1, 15.2**

  - [ ] 4.9 Replace mock `POST /billing/upgrade` with 410 Gone response
    - Replace the existing `upgrade_to_pro` handler body with a return of 410 Gone and message directing to checkout flow
    - Remove unused imports (e.g., `upgrade_user_tier` if no longer needed elsewhere)
    - _Requirements: 13.1, 13.2_

  - [ ]* 4.10 Write unit tests for billing endpoints in `backend/tests/unit/test_billing.py`
    - Test `_tier_features("free")` and `_tier_features("pro")` return expected shapes
    - Test checkout with missing Stripe config returns 503
    - Test portal with no `stripe_customer_id` returns 400
    - Test portal with free tier returns 403
    - Test webhook with missing `Stripe-Signature` returns 400
    - Test webhook with unknown event type returns 200
    - Test `POST /billing/upgrade` returns 410 Gone
    - Test billing status includes all required fields
    - _Requirements: 3.8, 3.9, 5.4, 10.4, 10.5, 13.2, 16.1, 16.3_

- [ ] 5. Checkpoint — Verify billing service
  - Ensure all existing 77 tests plus new billing tests pass with `PYTHONPATH=backend python3.11 -m pytest backend/tests/unit/ -x -q`
  - Ask the user if questions arise.

- [ ] 6. JWT refresh mechanism
  - [ ] 6.1 Implement `maybe_refresh_jwt()` utility in `backend/src/api/routes/billing.py`
    - Compare JWT `tier` claim with DB user `tier`
    - If different, call `create_jwt()` with DB tier and return the new token
    - If same, return None
    - _Requirements: 14.1, 14.2_

  - [ ] 6.2 Wire JWT refresh into `/billing/status` response
    - Call `maybe_refresh_jwt()` after fetching DB user
    - If a new token is returned, set `X-Refreshed-Token` response header
    - _Requirements: 6.4, 14.2_

  - [ ]* 6.3 Write property test for JWT refresh on tier mismatch
    - **Property 12: JWT refresh on tier mismatch**
    - **Validates: Requirements 6.4, 14.2**

- [ ] 7. Frontend proxy routes and Pro page UI
  - [ ] 7.1 Create `app/api/billing/checkout/route.ts`
    - POST handler: read `cybaop_token` cookie, proxy to backend `/billing/checkout`, return JSON with `url`
    - _Requirements: 4.1_

  - [ ] 7.2 Create `app/api/billing/portal/route.ts`
    - POST handler: read `cybaop_token` cookie, proxy to backend `/billing/portal`, return JSON with `url`
    - _Requirements: 11.2_

  - [ ] 7.3 Create `app/api/billing/webhook/route.ts`
    - POST handler: forward raw body and `Stripe-Signature` header to backend `/billing/webhook`
    - No auth cookie needed — Stripe calls this directly
    - _Requirements: 5.1_

  - [ ] 7.4 Update `app/api/billing/upgrade/route.ts` to call `/billing/checkout`
    - Change backend path from `/billing/upgrade` to `/billing/checkout`
    - On success, return the checkout URL for frontend redirect instead of setting token cookie
    - _Requirements: 13.3_

  - [ ] 7.5 Update `app/api/billing/status/route.ts` to handle `X-Refreshed-Token`
    - After proxying to backend, check for `X-Refreshed-Token` header
    - If present, set `cybaop_token` cookie with the new JWT value
    - _Requirements: 14.3_

  - [ ] 7.6 Update `app/dashboard/pro/page.tsx` for Stripe checkout and subscription management
    - Expand `BillingStatus` interface with `subscription_status`, `subscription_ends_at`, `warning`
    - When `!is_pro`: "Upgrade to Pro" button calls `/api/billing/checkout` then redirects to returned URL
    - When `is_pro && subscription_status === "active"`: show green active badge + "Manage Subscription" button (calls `/api/billing/portal` then redirects)
    - When `is_pro && subscription_status === "past_due"`: show warning banner with `warning` text + "Update Payment" button (links to portal)
    - Handle `session_id` query param on return from Stripe checkout (show success state)
    - Loading states on both upgrade and manage buttons during API calls
    - _Requirements: 4.2, 4.3, 4.4, 4.5, 11.1, 11.2, 11.3, 11.4_

- [ ] 8. Final checkpoint — Verify full integration
  - Ensure all tests pass with `PYTHONPATH=backend python3.11 -m pytest backend/tests/unit/ -x -q`
  - Ensure no TypeScript errors in frontend files
  - Ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design document (15 properties total)
- Unit tests validate specific examples and edge cases
- All Stripe API calls are mocked in tests — no real Stripe calls
- The 77 existing backend tests must continue passing after every checkpoint
