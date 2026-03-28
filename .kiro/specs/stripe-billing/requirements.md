# Requirements Document

## Introduction

CybaOp currently uses a mock billing flow that upgrades users to Pro tier without payment verification. This feature replaces the mock with a real Stripe integration using Stripe Checkout (hosted payment page) and Stripe Customer Portal (subscription management). The backend creates Stripe sessions and processes webhooks; the frontend redirects to Stripe-hosted pages. The Pro tier costs $12/month recurring. Webhook events drive all tier state changes to ensure payment verification before granting access.

## Glossary

- **Billing_Service**: The FastAPI backend billing routes that handle Stripe session creation, webhook processing, and tier management.
- **Checkout_Session_Creator**: The backend component that calls the Stripe API to create a Checkout Session for the $12/mo Pro subscription.
- **Portal_Session_Creator**: The backend component that calls the Stripe API to create a Customer Portal session for subscription management.
- **Webhook_Processor**: The backend component that receives Stripe webhook events, verifies signatures, and dispatches tier changes.
- **Tier_Manager**: The backend component that updates user tier, subscription status, and Stripe metadata in the database.
- **Frontend_Proxy**: The Next.js API routes that proxy billing requests from the browser to the backend.
- **Pro_Page**: The `/dashboard/pro` frontend page displaying pricing, feature comparison, and upgrade/manage buttons.
- **User**: A CybaOp user with a SoundCloud-linked account stored in the users table.
- **Stripe_Customer**: A Stripe Customer object linked to a CybaOp User via `stripe_customer_id`.
- **Subscription_Status**: One of `active`, `past_due`, `canceled`, or `trialing`, stored on the user record.

## Requirements

### Requirement 1: Database Schema for Stripe Billing

**User Story:** As a developer, I want the users table to store Stripe-specific fields, so that the system can track subscription state and link users to Stripe customers.

#### Acceptance Criteria

1. THE Tier_Manager SHALL store `stripe_customer_id` (TEXT, nullable) on the users table to link a User to a Stripe_Customer.
2. THE Tier_Manager SHALL store `stripe_subscription_id` (TEXT, nullable) on the users table to reference the active Stripe subscription.
3. THE Tier_Manager SHALL store `subscription_status` (TEXT, nullable, one of `active`, `past_due`, `canceled`, `trialing`) on the users table.
4. THE Tier_Manager SHALL store `subscription_ends_at` (TIMESTAMPTZ, nullable) on the users table to track the grace period end date after cancellation.
5. THE Tier_Manager SHALL default `stripe_customer_id`, `stripe_subscription_id`, `subscription_status`, and `subscription_ends_at` to NULL for new and existing users.

### Requirement 2: Stripe Configuration

**User Story:** As a developer, I want Stripe credentials loaded from environment variables, so that the backend can authenticate with the Stripe API securely.

#### Acceptance Criteria

1. THE Billing_Service SHALL read `STRIPE_SECRET_KEY` from environment variables for authenticating Stripe API calls.
2. THE Billing_Service SHALL read `STRIPE_WEBHOOK_SECRET` from environment variables for verifying webhook signatures.
3. THE Billing_Service SHALL read `STRIPE_PRO_PRICE_ID` from environment variables to identify the $12/mo Pro price.
4. THE Frontend_Proxy SHALL read `STRIPE_PUBLISHABLE_KEY` from environment variables (prefixed with `NEXT_PUBLIC_`) to expose the publishable key to the browser.
5. IF any required Stripe environment variable is missing at startup, THEN THE Billing_Service SHALL log a warning and allow the application to start without Stripe functionality.

### Requirement 3: Stripe Checkout Session Creation

**User Story:** As a free-tier user, I want to start a Stripe Checkout session when I click "Upgrade to Pro", so that I can securely pay for the Pro subscription through Stripe's hosted page.

#### Acceptance Criteria

1. WHEN a free-tier User sends a POST request to `/billing/checkout`, THE Checkout_Session_Creator SHALL create a Stripe Checkout Session in `subscription` mode with the Pro price ($12/mo recurring).
2. WHEN the User does not have a `stripe_customer_id`, THE Checkout_Session_Creator SHALL create a new Stripe Customer and store the `stripe_customer_id` on the user record before creating the session.
3. WHEN the User already has a `stripe_customer_id`, THE Checkout_Session_Creator SHALL reuse the existing Stripe Customer for the Checkout Session.
4. THE Checkout_Session_Creator SHALL set the Checkout Session `success_url` to redirect back to the CybaOp Pro page with a `session_id` query parameter.
5. THE Checkout_Session_Creator SHALL set the Checkout Session `cancel_url` to redirect back to the CybaOp Pro page.
6. THE Checkout_Session_Creator SHALL include the CybaOp `user_id` in the Checkout Session `metadata` so the webhook can identify the user.
7. THE Checkout_Session_Creator SHALL return the Checkout Session URL to the frontend for redirect.
8. IF the User already has an `active` Subscription_Status, THEN THE Checkout_Session_Creator SHALL return a 400 error indicating the user is already subscribed.
9. IF the Stripe API call fails, THEN THE Checkout_Session_Creator SHALL return a 502 error with a descriptive message.

### Requirement 4: Frontend Checkout Redirect

**User Story:** As a user on the Pro page, I want to be redirected to Stripe's checkout page when I click upgrade, so that I can complete payment securely.

#### Acceptance Criteria

1. WHEN the User clicks "Upgrade to Pro" on the Pro_Page, THE Frontend_Proxy SHALL send a POST request to the backend `/billing/checkout` endpoint.
2. WHEN the backend returns a Checkout Session URL, THE Pro_Page SHALL redirect the browser to the Stripe-hosted checkout page.
3. WHEN the User completes payment and Stripe redirects back, THE Pro_Page SHALL display a success state.
4. WHEN the User cancels checkout and Stripe redirects back, THE Pro_Page SHALL display the original pricing card.
5. WHILE the checkout request is in progress, THE Pro_Page SHALL display a loading state on the upgrade button.

### Requirement 5: Webhook Signature Verification

**User Story:** As a developer, I want all incoming Stripe webhooks verified against the webhook signing secret, so that the system only processes authentic events from Stripe.

#### Acceptance Criteria

1. WHEN a POST request arrives at `/billing/webhook`, THE Webhook_Processor SHALL read the `Stripe-Signature` header and the raw request body.
2. THE Webhook_Processor SHALL verify the signature using the `STRIPE_WEBHOOK_SECRET` and the `stripe` Python library's `Webhook.construct_event` method.
3. IF the signature verification fails, THEN THE Webhook_Processor SHALL return a 400 error and log the verification failure.
4. IF the `Stripe-Signature` header is missing, THEN THE Webhook_Processor SHALL return a 400 error.

### Requirement 6: Webhook Event Processing — Checkout Completed

**User Story:** As a system, I want to upgrade a user to Pro when Stripe confirms a successful checkout, so that the user gains access to Pro features only after verified payment.

#### Acceptance Criteria

1. WHEN the Webhook_Processor receives a `checkout.session.completed` event, THE Tier_Manager SHALL extract the `user_id` from the session metadata.
2. THE Tier_Manager SHALL store the `stripe_subscription_id` from the checkout session on the user record.
3. THE Tier_Manager SHALL set the user `tier` to `pro` and `subscription_status` to `active`.
4. THE Tier_Manager SHALL issue a new JWT with the `pro` tier claim so the next frontend request picks up the updated token.
5. IF the `user_id` in the metadata does not match any existing user, THEN THE Webhook_Processor SHALL log an error and return a 200 response to Stripe (to prevent retries).

### Requirement 7: Webhook Event Processing — Subscription Updated

**User Story:** As a system, I want to handle subscription changes from Stripe, so that the user's tier reflects their current subscription state.

#### Acceptance Criteria

1. WHEN the Webhook_Processor receives a `customer.subscription.updated` event, THE Tier_Manager SHALL update the `subscription_status` on the user record to match the Stripe subscription status.
2. WHEN the Stripe subscription status changes to `past_due`, THE Tier_Manager SHALL keep the user `tier` as `pro` but set `subscription_status` to `past_due`.
3. WHEN the Stripe subscription status changes to `active` (e.g., after a past_due recovery), THE Tier_Manager SHALL set `subscription_status` to `active`.

### Requirement 8: Webhook Event Processing — Subscription Deleted

**User Story:** As a system, I want to downgrade a user when their subscription is canceled, so that Pro access is revoked after the billing period ends.

#### Acceptance Criteria

1. WHEN the Webhook_Processor receives a `customer.subscription.deleted` event, THE Tier_Manager SHALL set the user `tier` to `free` and `subscription_status` to `canceled`.
2. THE Tier_Manager SHALL set `subscription_ends_at` to the Stripe subscription `current_period_end` timestamp to record when access expired.
3. THE Tier_Manager SHALL clear the `stripe_subscription_id` on the user record.

### Requirement 9: Webhook Event Processing — Payment Failed

**User Story:** As a system, I want to flag accounts with failed payments, so that the user is warned and the system can track payment issues.

#### Acceptance Criteria

1. WHEN the Webhook_Processor receives an `invoice.payment_failed` event, THE Tier_Manager SHALL set the `subscription_status` to `past_due` on the user record identified by the Stripe Customer ID.
2. THE Webhook_Processor SHALL log the payment failure with the user ID, invoice ID, and failure reason.

### Requirement 10: Stripe Customer Portal Session

**User Story:** As a Pro user, I want to manage my subscription (cancel, update payment method) through Stripe's Customer Portal, so that I have self-service control over my billing.

#### Acceptance Criteria

1. WHEN a Pro User sends a POST request to `/billing/portal`, THE Portal_Session_Creator SHALL create a Stripe Customer Portal session using the user's `stripe_customer_id`.
2. THE Portal_Session_Creator SHALL set the portal `return_url` to the CybaOp Pro page.
3. THE Portal_Session_Creator SHALL return the portal session URL to the frontend for redirect.
4. IF the User does not have a `stripe_customer_id`, THEN THE Portal_Session_Creator SHALL return a 400 error indicating no subscription exists.
5. IF the User is not on the Pro tier, THEN THE Portal_Session_Creator SHALL return a 403 error.

### Requirement 11: Frontend Portal Redirect

**User Story:** As a Pro user on the Pro page, I want a "Manage Subscription" button that takes me to Stripe's portal, so that I can cancel or update my payment method.

#### Acceptance Criteria

1. WHILE the User has an `active` or `past_due` Subscription_Status, THE Pro_Page SHALL display a "Manage Subscription" button.
2. WHEN the User clicks "Manage Subscription", THE Frontend_Proxy SHALL send a POST request to the backend `/billing/portal` endpoint.
3. WHEN the backend returns a portal session URL, THE Pro_Page SHALL redirect the browser to the Stripe-hosted Customer Portal.
4. WHILE the portal request is in progress, THE Pro_Page SHALL display a loading state on the manage button.

### Requirement 12: Billing Status Endpoint Enhancement

**User Story:** As a frontend developer, I want the billing status endpoint to return subscription details, so that the Pro page can display accurate subscription state.

#### Acceptance Criteria

1. THE Billing_Service SHALL return `subscription_status` (`active`, `past_due`, `canceled`, or null) in the `/billing/status` response.
2. THE Billing_Service SHALL return `subscription_ends_at` (ISO timestamp or null) in the `/billing/status` response.
3. THE Billing_Service SHALL determine `is_pro` based on the user's `tier` column in the database, not solely from the JWT claim.
4. WHEN the User has `subscription_status` of `past_due`, THE Billing_Service SHALL include a `warning` field with the message "Your payment method needs updating".

### Requirement 13: Replace Mock Upgrade Endpoint

**User Story:** As a developer, I want the mock `/billing/upgrade` endpoint removed, so that users cannot bypass Stripe payment to gain Pro access.

#### Acceptance Criteria

1. THE Billing_Service SHALL remove the existing `POST /billing/upgrade` endpoint that upgrades tier without payment verification.
2. THE Billing_Service SHALL return a 410 Gone response if any client calls the old `POST /billing/upgrade` path, with a message directing to the checkout flow.
3. THE Frontend_Proxy SHALL update the upgrade API route to call `/billing/checkout` instead of `/billing/upgrade`.

### Requirement 14: JWT Refresh After Tier Change

**User Story:** As a user whose tier just changed via webhook, I want my next API response to include an updated JWT, so that the frontend reflects my current tier without requiring re-login.

#### Acceptance Criteria

1. WHEN the Billing_Service processes a tier change via webhook, THE Tier_Manager SHALL store the new tier in the database.
2. WHEN a User makes any authenticated request after a tier change, THE Billing_Service SHALL detect that the JWT tier claim differs from the database tier and issue a refreshed JWT in the response header `X-Refreshed-Token`.
3. WHEN the Frontend_Proxy receives an `X-Refreshed-Token` header from the backend, THE Frontend_Proxy SHALL update the `cybaop_token` cookie with the new JWT.

### Requirement 15: Webhook Idempotency

**User Story:** As a developer, I want webhook processing to be idempotent, so that duplicate Stripe events do not cause inconsistent state.

#### Acceptance Criteria

1. WHEN the Webhook_Processor receives a `checkout.session.completed` event for a User who already has `subscription_status` of `active` and a matching `stripe_subscription_id`, THE Webhook_Processor SHALL skip the update and return 200.
2. WHEN the Webhook_Processor receives a `customer.subscription.deleted` event for a User who already has `tier` of `free`, THE Webhook_Processor SHALL skip the update and return 200.
3. THE Webhook_Processor SHALL log skipped duplicate events at the `info` level.

### Requirement 16: Existing Test Compatibility

**User Story:** As a developer, I want all 77 existing backend tests to continue passing after the Stripe integration, so that no existing functionality is broken.

#### Acceptance Criteria

1. THE Billing_Service SHALL maintain backward compatibility with the existing `/billing/status` response shape (fields `tier`, `is_pro`, `features`).
2. THE Billing_Service SHALL ensure that all database schema changes are additive (new nullable columns only) and do not alter existing column definitions.
3. THE Billing_Service SHALL ensure that the `_tier_features` function continues to return the same feature flag structure for both `free` and `pro` tiers.
