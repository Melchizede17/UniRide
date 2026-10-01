# UniRide --- Complete Project Architecture

## 1. Project Overview

**Project Name:** UniRide\
**Project Type:** Full-stack intelligent student ride-matching platform\
**Primary Goal:** Help university students find compatible passengers
for a shared ride so they can coordinate one ride and split
transportation expenses.

UniRide is **not a ride-hailing service** and does not provide drivers.
It is a coordination and matching platform. Users submit a pickup
location, destination, departure time, and ride preferences. The system
searches for compatible users based on exact destinations or
overlapping/compatible routes.

------------------------------------------------------------------------

## 2. Problem Statement

Individual ride-hailing trips can be expensive for university students,
particularly for longer trips such as airports, train stations, shopping
areas, or other regional destinations.

Students may be traveling: - From nearby pickup locations, - At
approximately the same time, - To the same destination, or - Along
substantially overlapping routes,

but have no reliable way to discover one another before booking.

### Proposed Solution

UniRide creates a location-aware matching platform that:

1.  Accepts a user's pickup location, destination, and preferred
    departure time.
2.  Finds users traveling to the same destination.
3.  Finds users whose routes substantially overlap even when
    destinations differ.
4.  Applies user-controlled ride-sharing preferences.
5.  Ranks eligible matches using a compatibility score.
6.  Allows both users to accept a match before exposing coordination
    information.
7.  Supports real-time match notifications.

------------------------------------------------------------------------

## 3. Core System Architecture

``` text
┌───────────────────────────────────────────────────────────────┐
│                         USER / BROWSER                        │
└───────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                  React + TypeScript Frontend                  │
│                                                               │
│  • Registration/Login                                         │
│  • Create Ride Request                                        │
│  • Map / Address Search                                       │
│  • Match Results                                              │
│  • Match Acceptance                                           │
│  • Ride History                                               │
│  • User Preferences                                           │
└───────────────────────────────┬───────────────────────────────┘
                                │ HTTPS / REST / WebSocket
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                    Python FastAPI Backend                     │
│                                                               │
│  Authentication / Users                                       │
│  Ride Request Service                                         │
│  Matching Service                                             │
│  Route Service                                                │
│  Notification Service                                         │
│  Privacy / Preference Rules                                   │
└───────────────┬─────────────────────┬─────────────────────────┘
                │                     │
                ▼                     ▼
┌─────────────────────────┐   ┌─────────────────────────────────┐
│ Matching Engine         │   │ Maps / Routing Provider         │
│                         │   │                                 │
│ • Eligibility filters   │   │ • Geocoding                    │
│ • Destination similarity│   │ • Places/autocomplete           │
│ • Pickup proximity      │   │ • Route geometry                │
│ • Time compatibility    │   │ • Distance/duration            │
│ • Route overlap         │   │                                 │
│ • Preference matching   │   └─────────────────────────────────┘
│ • Compatibility ranking │
└─────────────┬───────────┘
              │
              ▼
┌───────────────────────────────────────────────────────────────┐
│                 PostgreSQL + PostGIS Database                 │
│                                                               │
│ Users | Ride Requests | Routes | Matches | Preferences        │
│ Notifications | Ride History | Match Feedback                 │
└───────────────────────────────────────────────────────────────┘
```

------------------------------------------------------------------------

## 4. Recommended Technology Stack

  -----------------------------------------------------------------------
  Layer                   Technology              Purpose
  ----------------------- ----------------------- -----------------------
  Frontend                React                   User interface

  Frontend language       TypeScript              Safer, maintainable
                                                  frontend code

  Build tool              Vite                    React development/build
                                                  tooling

  Backend                 FastAPI                 REST APIs and backend
                                                  services

  Backend language        Python 3.12             Backend + matching/ML
                                                  ecosystem

  ORM                     SQLAlchemy              Database access

  Validation              Pydantic                Request/response
                                                  validation

  Database                PostgreSQL              Relational application
                                                  data

  Geospatial database     PostGIS                 Spatial queries and
                                                  route/location data

  Containers              Docker / Docker Compose Local infrastructure

  Maps                    Google Maps Platform or Places, coordinates and
                          equivalent              routes

  Real-time               WebSockets              Match
                                                  notifications/status
                                                  updates

  ML/Data                 NumPy, pandas,          Future data-driven
                          scikit-learn            matching

  API testing             Postman                 Backend API testing

  Version control         Git + GitHub            Source control

  IDE                     VS Code                 Development environment
  -----------------------------------------------------------------------

### Important Version Choice

Use **Python 3.12** for the UniRide backend virtual environment even if
a newer Python version is installed system-wide. This reduces
compatibility risk with scientific and geospatial dependencies.

------------------------------------------------------------------------

## 5. Major Functional Modules

### 5.1 Authentication and Student Accounts

Responsibilities: - Create account - Login/logout - Email verification -
Optional university-email verification - User profile - Ride-sharing
preferences

Do not infer sensitive attributes from names, photos, or other profile
data.

### 5.2 Ride Request Module

A ride request contains:

``` text
pickup_location
destination_location
preferred_departure_time
time_flexibility
passenger_count
ride_preferences
status
```

Example:

``` text
Pickup: Stony Brook University
Destination: JFK Airport
Departure: 4:00 PM
Time flexibility: ±20 minutes
Passengers: 1
Preference: Prefer same gender
```

### 5.3 Geospatial Module

Responsibilities: - Convert addresses into latitude/longitude. -
Calculate pickup distance. - Retrieve route geometry. - Compare
destination proximity. - Calculate route overlap. - Calculate additional
detour required for a shared trip.

### 5.4 Matching Engine

The matching engine has **two stages**.

#### Stage A --- Eligibility Filtering

Candidates must satisfy mandatory constraints before ranking.

Possible filters:

``` text
ride_request.status == ACTIVE
candidate != current_user
time_difference <= allowed_window
available_capacity >= required_capacity
route_is_feasible == true
mandatory_preferences_are_mutually_compatible == true
```

This prevents a high numerical score from overriding a mandatory
preference.

#### Stage B --- Compatibility Ranking

For eligible candidates:

\[ S = w_1D + w_2T + w_3P + w_4G \]

Where:

-   **D** = destination/route compatibility
-   **T** = departure-time compatibility
-   **P** = pickup proximity
-   **G** = optional gender-preference compatibility
-   **w₁ ... w₄** = configurable weights

Example initial weights:

\[ S = 0.35D + 0.25T + 0.20P + 0.20G \]

These are initial engineering choices, not learned values. They should
later be evaluated using match acceptance data.

------------------------------------------------------------------------

## 6. Matching Features

### 6.1 Exact / Near-Destination Matching

Example:

``` text
Student A:
Stony Brook → JFK

Student B:
Stony Brook → JFK
```

High destination compatibility.

Destination similarity can be based on geographic distance rather than
raw address-string equality.

Example concept:

``` text
destination_distance <= destination_threshold
```

### 6.2 Route-Based Matching

Example:

``` text
Student A:
Stony Brook → JFK

Student B:
Stony Brook → destination lying near/along A's feasible route
```

The system evaluates whether sharing creates an acceptable route.

Possible metrics:

-   Percentage of route overlap
-   Pickup deviation
-   Destination deviation
-   Added travel time
-   Added distance

A route should not be considered compatible merely because two polylines
intersect.

Example route compatibility:

\[ R = `\alpha `{=tex}O + `\beta`{=tex}(1-`\Delta`{=tex}\_t) +
`\gamma`{=tex}(1-`\Delta`{=tex}\_d) \]

Where:

-   \(O\) = normalized route overlap
-   (`\Delta`{=tex}\_t) = normalized additional travel-time penalty
-   (`\Delta`{=tex}\_d) = normalized additional-distance penalty

### 6.3 Time Compatibility

Example:

``` text
A departure = 4:00 PM
B departure = 4:10 PM
Allowed difference = 20 minutes
```

One simple normalized score:

\[ T = `\max`{=tex}(0, 1 - `\frac{|t_A-t_B|}{T_{max}}`{=tex}) \]

### 6.4 Pickup Compatibility

Use geographic distance:

``` text
distance(pickup_A, pickup_B)
```

Example scoring concept:

\[ P = `\max`{=tex}(0,1-`\frac{d}{d_{max}}`{=tex}) \]

PostGIS can efficiently retrieve nearby pickup requests.

### 6.5 User-Controlled Gender Preference

Suggested options:

``` text
NO_PREFERENCE
PREFER_SAME_GENDER
REQUIRE_SAME_GENDER
```

Behavior:

-   **NO_PREFERENCE:** gender does not affect ranking.
-   **PREFER_SAME_GENDER:** compatible same-gender candidates receive a
    ranking benefit.
-   **REQUIRE_SAME_GENDER:** incompatible candidates are removed during
    eligibility filtering.

Preference compatibility should be **mutual**. The application should
never infer gender from a name or photograph.

------------------------------------------------------------------------

## 7. Example Matching Pipeline

``` text
User creates ride request
        │
        ▼
Validate request
        │
        ▼
Geocode pickup + destination
        │
        ▼
Generate route geometry
        │
        ▼
Retrieve nearby/time-compatible active requests
        │
        ▼
Apply mandatory eligibility filters
        │
        ▼
Calculate destination/route score (D)
        │
        ▼
Calculate time score (T)
        │
        ▼
Calculate pickup score (P)
        │
        ▼
Calculate preference score (G)
        │
        ▼
Calculate final compatibility score
        │
        ▼
Sort candidates
        │
        ▼
Return top matches
        │
        ▼
Mutual acceptance
        │
        ▼
Create confirmed match
```

------------------------------------------------------------------------

## 8. Database Architecture

### 8.1 Users

``` text
users
-----
id                  UUID PK
email               VARCHAR UNIQUE
password_hash       VARCHAR
display_name        VARCHAR
university          VARCHAR
email_verified      BOOLEAN
gender              VARCHAR NULLABLE
created_at          TIMESTAMP
updated_at          TIMESTAMP
```

### 8.2 User Preferences

``` text
user_preferences
----------------
id
user_id             FK -> users.id
gender_preference
default_time_window
default_pickup_radius
created_at
updated_at
```

### 8.3 Ride Requests

``` text
ride_requests
-------------
id
user_id
pickup_address
pickup_point         GEOGRAPHY(Point, 4326)
destination_address
destination_point    GEOGRAPHY(Point, 4326)
departure_time
time_flexibility_minutes
passenger_count
status
created_at
expires_at
```

Possible status values:

``` text
ACTIVE
MATCH_PENDING
MATCHED
CANCELLED
EXPIRED
COMPLETED
```

### 8.4 Route Data

``` text
routes
------
id
ride_request_id
route_geometry       GEOGRAPHY(LineString, 4326)
distance_meters
duration_seconds
provider
created_at
```

### 8.5 Matches

``` text
matches
-------
id
request_a_id
request_b_id
destination_score
time_score
pickup_score
preference_score
route_overlap_score
total_score
status
created_at
```

Possible status values:

``` text
SUGGESTED
A_ACCEPTED
B_ACCEPTED
CONFIRMED
REJECTED
EXPIRED
CANCELLED
```

### 8.6 Match Feedback

``` text
match_feedback
--------------
id
match_id
user_id
accepted
reason
created_at
```

This table becomes useful later for ML.

### 8.7 Notifications

``` text
notifications
-------------
id
user_id
type
message
is_read
created_at
```

------------------------------------------------------------------------

## 9. Simplified Entity Relationships

``` text
USERS
  │
  ├────────────── 1:1 / 1:N ───────── USER_PREFERENCES
  │
  └────────────── 1:N ─────────────── RIDE_REQUESTS
                                          │
                                          ├──── 1:1 ─── ROUTES
                                          │
                                          └──── N:M ─── MATCHES
                                                         │
                                                         └── MATCH_FEEDBACK

USERS ─────────────── 1:N ───────────── NOTIFICATIONS
```

------------------------------------------------------------------------

## 10. Backend API Architecture

Base URL:

``` text
/api/v1
```

### Authentication

``` text
POST   /auth/register
POST   /auth/login
POST   /auth/logout
POST   /auth/verify-email
GET    /auth/me
```

### Users

``` text
GET    /users/me
PATCH  /users/me
GET    /users/me/preferences
PATCH  /users/me/preferences
```

### Ride Requests

``` text
POST   /rides
GET    /rides/{ride_id}
GET    /rides/me
PATCH  /rides/{ride_id}
DELETE /rides/{ride_id}
```

### Matching

``` text
GET    /rides/{ride_id}/matches
POST   /matches/{match_id}/accept
POST   /matches/{match_id}/reject
GET    /matches/{match_id}
```

### History

``` text
GET    /rides/history
```

### Notifications

``` text
GET    /notifications
PATCH  /notifications/{id}/read
```

### Real-Time

``` text
WS /ws/matches
```

------------------------------------------------------------------------

## 11. Example Ride Request API

### Request

``` json
{
  "pickup": {
    "latitude": 40.9143,
    "longitude": -73.1234
  },
  "destination": {
    "latitude": 40.6413,
    "longitude": -73.7781
  },
  "departure_time": "2026-10-10T16:00:00",
  "time_flexibility_minutes": 20,
  "passenger_count": 1,
  "gender_preference": "PREFER_SAME_GENDER"
}
```

### Response

``` json
{
  "ride_request_id": "uuid",
  "status": "ACTIVE",
  "message": "Ride request created"
}
```

------------------------------------------------------------------------

## 12. Frontend Architecture

Recommended pages:

``` text
/
├── Landing Page
├── Register
├── Login
├── Dashboard
│   ├── Create Ride
│   ├── Active Ride
│   ├── Match Results
│   └── Notifications
├── Match Details
├── Ride History
├── Profile
└── Preferences
```

### Main Create-Ride Interface

``` text
┌─────────────────────────────────────┐
│             Find a Ride             │
│                                     │
│ Pickup                              │
│ [ Stony Brook University       ]    │
│                                     │
│ Destination                         │
│ [ JFK Airport                  ]    │
│                                     │
│ Departure                           │
│ [ Date ] [ Time ]                   │
│                                     │
│ Flexible by                         │
│ [ ±20 minutes ]                     │
│                                     │
│ Ride preference                     │
│ [ Prefer same gender ▼ ]            │
│                                     │
│          [ Find Matches ]           │
└─────────────────────────────────────┘
```

------------------------------------------------------------------------

## 13. Suggested Repository Structure

``` text
uniride/
│
├── README.md
├── .gitignore
├── .env.example
├── docker-compose.yml
│
├── backend/
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── tests/
│   │
│   └── app/
│       ├── main.py
│       │
│       ├── api/
│       │   └── v1/
│       │       ├── auth.py
│       │       ├── users.py
│       │       ├── rides.py
│       │       ├── matches.py
│       │       └── notifications.py
│       │
│       ├── core/
│       │   ├── config.py
│       │   ├── security.py
│       │   └── database.py
│       │
│       ├── models/
│       │   ├── user.py
│       │   ├── ride.py
│       │   ├── route.py
│       │   ├── match.py
│       │   └── notification.py
│       │
│       ├── schemas/
│       │   ├── user.py
│       │   ├── ride.py
│       │   └── match.py
│       │
│       ├── services/
│       │   ├── matching_service.py
│       │   ├── route_service.py
│       │   ├── notification_service.py
│       │   └── maps_service.py
│       │
│       └── matching/
│           ├── eligibility.py
│           ├── destination.py
│           ├── pickup.py
│           ├── time.py
│           ├── route_overlap.py
│           ├── preferences.py
│           └── scorer.py
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── components/
│       ├── pages/
│       ├── services/
│       ├── hooks/
│       ├── types/
│       └── utils/
│
├── database/
│   ├── migrations/
│   └── seed/
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── database.md
│   └── matching-algorithm.md
│
└── scripts/
    ├── seed_test_data.py
    └── evaluate_matching.py
```

------------------------------------------------------------------------

## 14. Docker Architecture

For local development:

``` text
Docker Compose
│
├── PostgreSQL + PostGIS
│
└── Optional later:
    ├── Backend container
    └── Redis
```

During early development, running React and FastAPI directly on the Mac
while containerizing PostgreSQL/PostGIS keeps debugging simple.

Example conceptual services:

``` yaml
services:
  db:
    image: postgis/postgis
    ports:
      - "5432:5432"

  # Add backend container after the local backend is stable.
```

------------------------------------------------------------------------

## 15. Real-Time Matching Architecture

When a new compatible match is generated:

``` text
Ride request created
       │
       ▼
Matching service
       │
       ▼
Potential match stored
       │
       ├───────────────┐
       ▼               ▼
WebSocket A        WebSocket B
       │               │
       ▼               ▼
Student A          Student B
"Match found"      "Match found"
       │               │
       └──── Accept ────┘
               │
               ▼
       Confirmed match
```

Do not expose private contact/location details until the appropriate
mutual-consent state is reached.

------------------------------------------------------------------------

## 16. Privacy and Safety Architecture

Because UniRide connects strangers, privacy should be part of the
architecture.

### Principles

-   University/email verification where appropriate.
-   Do not display precise home locations to unmatched users.
-   Store only data required by the product.
-   Never infer gender or other sensitive preferences.
-   User controls their ride preferences.
-   Mutual consent before sharing coordination details.
-   Allow users to cancel/reject matches.
-   Add blocking/reporting capability before any real-world public
    deployment.
-   Do not store third-party API secrets in frontend code.
-   Store secrets in environment variables.
-   Hash passwords using an appropriate password-hashing algorithm.
-   Use HTTPS in deployed environments.

------------------------------------------------------------------------

## 17. Rule-Based Matching First, ML Later

UniRide should **not begin with a machine-learning model**.

### Version 1

Use deterministic algorithms:

``` text
Geospatial filtering
+
Time-window filtering
+
Route comparison
+
Preference constraints
+
Weighted scoring
```

Benefits: - Explainable - Easy to test - No training dataset required -
Strong baseline

### Version 2 --- Data Collection

Collect non-sensitive matching outcomes:

``` text
candidate shown
candidate accepted/rejected
route overlap
pickup distance
time difference
detour
final match outcome
```

### Version 3 --- ML Ranking

Once enough data exists, train a ranking/acceptance model.

Potential input features:

``` text
destination_similarity
route_overlap
pickup_distance
time_difference
detour_minutes
detour_distance
preference_compatibility
historical acceptance signals
```

Possible target:

``` text
P(match accepted)
```

The ML model should improve **ranking**, while mandatory
safety/preference constraints remain deterministic filters.

------------------------------------------------------------------------

## 18. Evaluation Metrics

A strong technical project should measure its matching quality.

### Matching Metrics

-   Match acceptance rate
-   Average route overlap
-   Average pickup distance
-   Average time difference
-   Average detour minutes
-   Percentage of requests receiving at least one feasible match

### System Metrics

-   API response time
-   Matching latency
-   Database query latency
-   WebSocket notification latency
-   Error rate

### Product/Impact Metrics

-   Estimated shared-trip savings
-   Number of confirmed shared rides
-   Repeated use
-   Match cancellation rate

Avoid claiming actual cost savings until measured.

------------------------------------------------------------------------

## 19. Testing Strategy

### Unit Tests

Test each score independently:

``` text
test_time_score()
test_pickup_score()
test_destination_score()
test_route_overlap_score()
test_preference_filter()
test_total_score()
```

### Matching Tests

Examples:

``` text
same destination + same time -> high compatibility
same destination + very different time -> filtered/low
near pickup + overlapping route -> eligible
large detour -> rejected
mandatory preference conflict -> filtered
user matched with own request -> rejected
expired request -> rejected
```

### API Tests

Test: - Authentication - Ride creation - Ride updates - Match
retrieval - Accept/reject - Authorization

### Integration Tests

Test:

``` text
Frontend
   ↓
FastAPI
   ↓
Matching Engine
   ↓
PostgreSQL/PostGIS
```

------------------------------------------------------------------------

## 20. Development Phases

### Phase 0 --- Environment

Install/configure:

``` text
Git
VS Code
Docker
Python 3.12
Node.js + npm
Postman
```

### Phase 1 --- Project Foundation

Build:

``` text
Git repository
frontend/
backend/
docker-compose.yml
environment files
basic README
```

### Phase 2 --- Database

Create:

``` text
PostgreSQL/PostGIS
Users
Ride Requests
Preferences
Routes
Matches
```

### Phase 3 --- Backend

Build:

``` text
FastAPI
database connection
models
schemas
ride CRUD APIs
```

### Phase 4 --- Basic Frontend

Build:

``` text
React + TypeScript
registration/login
dashboard
create-ride form
match-results page
```

### Phase 5 --- Matching Engine V1

Implement:

``` text
destination similarity
time compatibility
pickup proximity
preference constraints
weighted score
```

### Phase 6 --- Route Matching

Add:

``` text
route geometry
route overlap
detour calculations
partial-route compatibility
```

### Phase 7 --- Real-Time Experience

Add:

``` text
WebSockets
match notifications
accept/reject
confirmed-match state
```

### Phase 8 --- Evaluation

Create:

``` text
synthetic/test ride dataset
matching test suite
evaluation script
metrics report
```

### Phase 9 --- ML Enhancement

Only after data exists:

``` text
feature engineering
acceptance prediction/ranking
offline evaluation
compare ML against rule-based baseline
```

### Phase 10 --- Deployment

After local MVP works:

``` text
frontend hosting
backend hosting
managed PostgreSQL/PostGIS
HTTPS
logging
monitoring
CI/CD
```

------------------------------------------------------------------------

## 21. MVP Definition

The first working version should allow:

1.  A user to register/login.
2.  A user to create a ride request.
3.  Pickup/destination coordinates to be stored.
4.  Another user to create a compatible request.
5.  The backend to calculate compatibility.
6.  The system to return ranked matches.
7.  Both users to accept/reject.
8.  A confirmed match to be created after mutual acceptance.

Do **not** make chat, payment splitting, ML, sophisticated reputation
systems, or automatic ride booking prerequisites for the MVP.

------------------------------------------------------------------------

## 22. Example End-to-End Scenario

``` text
Student A
Pickup: Stony Brook
Destination: JFK
Departure: 4:00 PM
        │
        ▼
Ride Request A
        │
        ▼
Student B
Pickup: nearby
Destination: JFK / compatible route
Departure: 4:10 PM
        │
        ▼
Ride Request B
        │
        ▼
Eligibility Engine
        │
        ├─ Time compatible? YES
        ├─ Pickup feasible? YES
        ├─ Route feasible? YES
        └─ Mandatory preferences compatible? YES
        │
        ▼
Scoring Engine
        │
        ├─ D
        ├─ T
        ├─ P
        └─ G
        │
        ▼
Compatibility Score
        │
        ▼
Match Suggested
        │
        ├── A accepts
        └── B accepts
        │
        ▼
Confirmed Match
        │
        ▼
Students coordinate shared ride booking
```

------------------------------------------------------------------------

## 23. Architecture Decisions That Strengthen the Project

### Decision 1 --- PostGIS instead of plain latitude/longitude logic

Shows practical geospatial database engineering and enables indexed
spatial queries.

### Decision 2 --- Eligibility + Ranking

Separating mandatory constraints from preferences prevents a weighted
score from violating explicit requirements.

### Decision 3 --- Route overlap, not only destination equality

This is the core technical differentiator. UniRide can identify
compatible journeys rather than functioning as a simple destination
filter.

### Decision 4 --- Rule-based baseline before ML

Makes the system measurable and technically defensible. ML is added only
when data can demonstrate an improvement.

### Decision 5 --- Real-time mutual acceptance

Transforms the matching algorithm into a usable end-to-end system.

------------------------------------------------------------------------

## 24. Final Architecture Summary

``` text
                 ┌─────────────────┐
                 │ React/TypeScript│
                 │    Frontend     │
                 └────────┬────────┘
                          │
                     REST / WS
                          │
                 ┌────────▼────────┐
                 │     FastAPI     │
                 │     Backend     │
                 └───┬─────────┬───┘
                     │         │
        ┌────────────▼──┐   ┌──▼─────────────┐
        │ Matching      │   │ Maps / Routing │
        │ Engine        │   │ Provider       │
        └──────┬────────┘   └────────────────┘
               │
       ┌───────▼───────────────────┐
       │ Eligibility               │
       │ + Geospatial Matching     │
       │ + Route Overlap           │
       │ + Time Matching           │
       │ + Preference Matching     │
       │ + Compatibility Ranking   │
       └───────────┬───────────────┘
                   │
          ┌────────▼─────────┐
          │ PostgreSQL       │
          │ + PostGIS        │
          └──────────────────┘
```

------------------------------------------------------------------------

## 25. Immediate Next Milestone

With the architecture defined, the implementation should begin with:

``` text
Milestone 1
├── Create uniride/ repository
├── Configure Python 3.12 virtual environment
├── Create FastAPI backend
├── Create React + TypeScript frontend
├── Create Docker Compose file
├── Start PostgreSQL + PostGIS
└── Verify frontend → backend → database connectivity
```

After this milestone is stable, implement the first ride-request API and
database model before working on the matching algorithm.
