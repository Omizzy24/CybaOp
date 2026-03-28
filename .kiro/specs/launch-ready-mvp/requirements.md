# Requirements Document

## Introduction

CybaOp is preparing for public launch. Two areas need attention before real users hit the product: the landing page must clearly communicate value and convert SoundCloud creators into authenticated users, and the OAuth authentication flow must work reliably end-to-end in production with proper error handling, no dev workarounds, and clear user feedback at every step.

This spec covers the landing page polish pass (copy, structure, trust signals, SEO, mobile) and the production hardening of the OAuth flow (cleanup, health checks, error states, loading UX).

## Glossary

- **Landing_Page**: The public-facing page at `app/page.tsx` that serves as the entry point for unauthenticated visitors
- **OAuth_Flow**: The complete authentication sequence: frontend redirect → SoundCloud authorization → callback code exchange → backend JWT issuance → cookie storage → dashboard redirect
- **Callback_Route**: The Next.js API route at `/api/auth/callback` that handles the SoundCloud OAuth redirect, exchanges the code for a token, and registers the user with the backend
- **Me_Route**: The Next.js API route at `/api/auth/me` that returns the authenticated user's profile by proxying to the backend
- **Health_Check_Endpoint**: A new API route that verifies the backend (Railway) is reachable from the frontend (Vercel)
- **SC_Token_Fallback**: The existing dev workaround in the Me_Route that tries using the JWT cookie as a raw SoundCloud token when the backend rejects it
- **CTA**: Call-to-action UI element that prompts the visitor to connect their SoundCloud account
- **OG_Tags**: Open Graph meta tags used by social platforms to render link previews
- **Backend**: The FastAPI service running on Railway at `delightful-beauty-production-7537.up.railway.app`
- **Frontend**: The Next.js 15 application running on Vercel at `cyba-op.vercel.app`

## Requirements

### Requirement 1: Value Proposition Hierarchy

**User Story:** As a SoundCloud creator visiting the landing page, I want to immediately understand what CybaOp does and why it matters to me, so that I can decide whether to connect my account.

#### Acceptance Criteria

1. THE Landing_Page SHALL display a primary headline that communicates the core value proposition for SoundCloud creators
2. THE Landing_Page SHALL display a supporting subheadline that explains what CybaOp does in concrete terms (analytics, trends, insights)
3. THE Landing_Page SHALL display a "How it works" section with three steps: Connect, Analyze, Act
4. THE Landing_Page SHALL replace the "Join 500+ SoundCloud creators" text with honest copy that does not claim an unverified user count

### Requirement 2: Social Proof and Trust Signals

**User Story:** As a SoundCloud creator, I want to see trust signals before connecting my account, so that I feel confident CybaOp is safe and legitimate.

#### Acceptance Criteria

1. THE Landing_Page SHALL display a trust signals section containing the statements "Read-only access", "No data stored on third parties", and "Open analytics"
2. THE Landing_Page SHALL display a social proof section that communicates the target audience (independent SoundCloud artists) without fabricating user counts
3. THE Landing_Page SHALL display the text "Read-only access. We never modify your account." adjacent to the primary CTA

### Requirement 3: Feature Showcase Depth

**User Story:** As a SoundCloud creator, I want to see the specific capabilities CybaOp offers beyond basic stats, so that I understand the depth of the analytics platform.

#### Acceptance Criteria

1. THE Landing_Page SHALL display feature cards that describe the dashboard capabilities: track analytics with engagement rates and outlier detection, trend detection with release timing and growth velocity, and AI-powered insights with personalized recommendations
2. THE Landing_Page SHALL display the comparison section showing what SoundCloud provides versus what CybaOp provides, including engagement rate, best release day, top track performance, and catalog health score
3. THE Landing_Page SHALL include references to triage and workflow capabilities in the feature showcase

### Requirement 4: Secondary CTA and Footer

**User Story:** As a visitor who has scrolled through the landing page, I want a second opportunity to connect my account and access to legal links, so that I can act on my interest without scrolling back up.

#### Acceptance Criteria

1. THE Landing_Page SHALL display a secondary CTA at the bottom of the page content, above the footer, that links to `/api/auth/soundcloud`
2. THE Landing_Page SHALL display a footer containing links for Privacy Policy and Terms of Service (placeholder hrefs are acceptable for launch)
3. THE Landing_Page SHALL display the CybaOp copyright and a "Built for SoundCloud creators" tagline in the footer

### Requirement 5: SEO and Social Sharing Meta Tags

**User Story:** As a creator sharing CybaOp on social media, I want the link preview to display a compelling title, description, and image, so that my followers understand what CybaOp is.

#### Acceptance Criteria

1. THE Landing_Page layout SHALL include a meta description that describes CybaOp as an analytics intelligence platform for SoundCloud creators
2. THE Landing_Page layout SHALL include Open Graph tags: `og:title`, `og:description`, `og:image`, `og:url`, and `og:type`
3. THE Landing_Page layout SHALL include Twitter Card meta tags: `twitter:card`, `twitter:title`, `twitter:description`, and `twitter:image`
4. THE Landing_Page layout SHALL include a canonical URL pointing to `https://cyba-op.vercel.app`

### Requirement 6: Mobile-First Responsive Polish

**User Story:** As a SoundCloud creator browsing on my phone, I want the landing page to be well-structured and readable on mobile screens, so that I can learn about CybaOp and connect my account from any device.

#### Acceptance Criteria

1. THE Landing_Page SHALL render the hero section, feature cards, comparison section, and CTAs in a single-column layout on viewports narrower than 640px
2. THE Landing_Page SHALL use font sizes, padding, and spacing that maintain readability on mobile viewports without horizontal scrolling
3. THE Landing_Page CTA buttons SHALL have a minimum touch target size of 44x44 CSS pixels on mobile viewports

### Requirement 7: Remove SC Token Fallback from Me Route

**User Story:** As a developer preparing for production, I want the `/api/auth/me` route to only accept the JWT authentication path, so that there are no dev workarounds in the production code.

#### Acceptance Criteria

1. THE Me_Route SHALL authenticate requests using only the `cybaop_token` JWT cookie validated by the Backend
2. THE Me_Route SHALL NOT attempt to use the cookie value as a raw SoundCloud OAuth token
3. WHEN the Backend returns a 401 status for the JWT, THEN THE Me_Route SHALL return a 401 response to the client and delete the `cybaop_token` cookie
4. WHEN the Backend is unreachable, THEN THE Me_Route SHALL return a 503 response with the message "Profile service unavailable"

### Requirement 8: Backend Health Check Endpoint

**User Story:** As a developer deploying to production, I want a health check endpoint that verifies the backend is reachable from the frontend, so that I can diagnose connectivity issues between Vercel and Railway.

#### Acceptance Criteria

1. WHEN a GET request is made to `/api/health`, THE Health_Check_Endpoint SHALL make a request to the Backend health endpoint and return the Backend's status
2. WHEN the Backend is reachable, THE Health_Check_Endpoint SHALL return a 200 response containing `{ "status": "ok", "backend": "reachable" }`
3. WHEN the Backend is unreachable or returns an error, THE Health_Check_Endpoint SHALL return a 503 response containing `{ "status": "degraded", "backend": "unreachable" }`
4. THE Health_Check_Endpoint SHALL complete within 5000 milliseconds, returning the unreachable status if the Backend does not respond in time

### Requirement 9: OAuth Error Handling and User Feedback

**User Story:** As a SoundCloud creator attempting to sign in, I want clear error messages when something goes wrong during authentication, so that I know what happened and what to do next.

#### Acceptance Criteria

1. WHEN SoundCloud is unreachable during token exchange, THEN THE Callback_Route SHALL redirect to the Landing_Page with the query parameter `error=timeout`
2. WHEN the Backend is unreachable during user registration, THEN THE Callback_Route SHALL redirect to the Landing_Page with the query parameter `error=service_unavailable`
3. WHEN the authorization code is missing from the callback, THEN THE Callback_Route SHALL redirect to the Landing_Page with the query parameter `error=exchange_failed`
4. WHEN the SoundCloud token exchange returns an error, THEN THE Callback_Route SHALL redirect to the Landing_Page with the query parameter `error=auth_failed`
5. THE Landing_Page SHALL display a human-readable error message for each error code: `auth_failed`, `timeout`, `service_unavailable`, `exchange_failed`, and `unexpected`
6. THE Landing_Page error messages SHALL include a "Try again" link that points to `/api/auth/soundcloud`


### Requirement 10: OAuth Loading State

**User Story:** As a SoundCloud creator clicking "Connect SoundCloud", I want to see a loading indicator while the OAuth redirect is in progress, so that I know the app is working and not frozen.

#### Acceptance Criteria

1. WHEN a user clicks the "Connect SoundCloud" CTA, THE Landing_Page SHALL display a "Connecting..." loading state on the CTA button
2. THE Landing_Page SHALL disable the CTA button while the loading state is active to prevent duplicate OAuth initiations

### Requirement 11: Authenticated User Redirect

**User Story:** As a SoundCloud creator who is already signed in, I want to be redirected to the dashboard when I visit the landing page, so that I do not have to sign in again.

#### Acceptance Criteria

1. WHEN an authenticated user (with a valid `cybaop_token` cookie) visits the Landing_Page, THE Landing_Page SHALL redirect the user to `/dashboard`
2. THE Landing_Page SHALL verify authentication by calling the Me_Route before redirecting

### Requirement 12: Logout Flow

**User Story:** As an authenticated user, I want the logout action to fully clear my session and return me to the landing page, so that my account is properly signed out.

#### Acceptance Criteria

1. WHEN a user triggers logout, THE Frontend SHALL send a POST request to `/api/auth/logout`
2. THE logout route SHALL delete the `cybaop_token` cookie from the response
3. WHEN the cookie is deleted, THE Frontend SHALL redirect the user to the Landing_Page at `/`

### Requirement 13: Environment Variable Documentation

**User Story:** As a developer deploying CybaOp, I want all required environment variables documented, so that I can configure Vercel and Railway correctly for production.

#### Acceptance Criteria

1. THE project SHALL include documentation listing all required environment variables for the Frontend deployment: `SOUNDCLOUD_CLIENT_ID`, `SOUNDCLOUD_CLIENT_SECRET`, `SOUNDCLOUD_REDIRECT_URI`, `BACKEND_URL`
2. THE project SHALL include documentation listing all required environment variables for the Backend deployment: `SOUNDCLOUD_CLIENT_ID`, `SOUNDCLOUD_CLIENT_SECRET`, `JWT_SECRET`, `DATABASE_URL`
3. THE documentation SHALL specify which variables are required versus optional and provide example values for each
