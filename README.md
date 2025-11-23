# Fora - UBC Task Board

<div align="center">

**A UBC Okanagan exclusive task marketplace for students, faculty, and staff with ML-powered recommendations and campus rewards**

[![Next.js](https://img.shields.io/badge/Next.js-16.0-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688)](https://fastapi.tiangolo.com/)
[![Supabase](https://img.shields.io/badge/Supabase-Powered-3ECF8E)](https://supabase.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB)](https://www.python.org/)


</div>

---

## Overview

Fora is a **UBC Okanagan exclusive** task marketplace platform designed for students, faculty, and staff. Users must have a valid **UBC email** (@ubc.ca or @student.ubc.ca) to join. Complete tasks to earn credits, then redeem them at participating **UBC Okanagan locations** - grab a free coffee from Tim Hortons, get discounts at the bookstore, or enjoy perks at local partner businesses.

Inspired by **Fiverr's freelance marketplace** and **Tinder's swipe interface**, Fora combines professional task matching with a quick, intuitive application experience that makes finding voluntary work and helping the campus community feel effortless.

### What Makes Fora Special?

- **🎓 UBC Okanagan Exclusive**: Requires valid UBC student/faculty/staff email - built for the campus community
- **👆 Tinder-Style Interface**: Swipe through tasks quickly - apply with a tap, dismiss with a swipe
- **☕ Campus Rewards**: Redeem earned credits at UBC Okanagan locations (Tim Hortons, bookstore, and more)
- **🎯 Smart Recommendations**: ML-powered feed that learns user preferences and shows relevant tasks
- **💼 Fiverr-Inspired Marketplace**: Professional freelance task posting with categories, ratings, and portfolios
- **📍 Location-Aware**: Geographic search and filtering with interactive maps around campus
- **💰 Credits System**: Complete tasks to earn credits, spend them on real campus perks
- **💬 Real-time Chat**: Built-in messaging between posters and assignees
- **🔔 Smart Notifications**: Context-aware alerts for task updates, messages, and completions
- **⭐ Ratings System**: Reputation tracking for both posters and assignees
- **🎨 Modern UI**: Clean, responsive interface with dark mode support

---

## Features

### Core Functionality

#### For Task Posters
- **Create Listings** with rich details (title, description, images, location, deadline, credits which can be earnt)
- **Manage Applications** - shortlist, reject, or select applicants
- **Track Progress** - monitor task status through completion workflow
- **Edit & Delete** - full control over your posted tasks
- **Chat with Assignees** - communicate directly with selected workers
- **Confirm Completion** - approve work and award credits

#### For Task Finders
- **Browse Marketplace** - discover tasks with advanced filtering (location, tags, compensation)
- **Personalized Feed** - ML-powered recommendations based on your interests and history
- **Apply to Tasks** - submit applications with optional messages
- **Track Applications** - monitor your applied, shortlisted, and assigned tasks
- **Mark Complete** - submit task for poster approval
- **Earn Credits** - get rewarded for completed tasks

#### Platform Features

- **UBC Email Verification** - exclusive access for UBC Okanagan students, faculty, and staff
- **Campus Credits Economy** - earn credits by completing tasks, spend on real campus rewards
- **Rewards Marketplace** - redeem credits at UBC Okanagan locations, such as:
  - Free coffee from Comma
  - Discounts at the bookstore
  - Special perks at local partner businesses
- **User Profiles** - track your stats, ratings, and activity
- **Interactive Maps** - Google Maps integration for campus location-based discovery
- **Real-time Notifications** - instant updates for all important events
- **Chat System** - in-app messaging for each listing
- **Ratings & Reviews** - build reputation  within the UBC community
- **Tag System** - categorize and filter tasks by interests
- **Admin Dashboard** - manage users, listings, and campus rewards partnerships

### Advanced Features

#### ML Recommendation Engine
Our sophisticated machine learning system provides personalized task recommendations using:
- **Collaborative Filtering** - "Users like you also viewed..."
- **Content-Based Filtering** - Match tasks to your interests
- **Location Scoring** - Prioritize nearby opportunities
- **Engagement Analysis** - Surface popular and trending tasks
- **Recency Boost** - Keep fresh content visible
- **Hybrid Scoring** - Combine multiple signals for optimal results

See [ML Documentation](docs/ML_FEED_README.md) for technical details.

#### Interactive Map View
Discover tasks geographically with our powerful map interface powered by **Google Maps API**:

**Features:**
- **Visual Task Discovery** - See all available tasks on an interactive map centered on UBC Okanagan campus
- **Smart Filtering** - Filter tasks by:
  - Name search
  - Location-based radius (search within X km of any address)
  - Tags and categories
  - Credits
- **Real-time Markers** - Each task appears as a marker on the map with:
  - Color-coded status indicators
  - Hover effects for quick preview
  - Click to view full details in InfoWindow
- **Synchronized Views** - Listings panel syncs with map selection
  - Click any listing card to center the map
  - Hover over cards to highlight map markers
  - Filter results update both panel and map instantly
- **Location Intelligence** - Uses the Haversine formula to calculate precise distances
- **Geocoding Support** - Search by address and automatically center the map with radius filtering
- **Responsive Design** - Split-screen layout with listings sidebar and full map view

**How to Use:**
1. Navigate to `/map` from the main navigation
2. Browse tasks in the left panel or directly on the map
3. Use filters to narrow down opportunities by location, name, or tags
4. Click markers or listing cards to view task details
5. Apply to tasks directly from the InfoWindow popup

**Technical Implementation:**
- `@react-google-maps/api` for React integration
- Real-time listing data from FastAPI backend
- Client-side filtering for instant results
- localStorage caching for improved performance
- Authenticated access only (UBC email required)

Access the map view at: `/map`

#### Smart Notifications
- Task status changes (shortlisted, assigned, completed)
- New applicants for your listings
- Credits earned notifications
- New messages in chat
- Task deadlines approaching
- Reward claims confirmation

#### Security & Privacy
- Supabase Authentication (email, OAuth)
- Row-Level Security (RLS) policies
- Role-based access control (user, moderator, admin)
- Secure credit transactions with database triggers
- Input validation and sanitization

---

## Quick Start

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.10+
- **Supabase** account ([free tier available](https://supabase.com))
- **Google Maps API** key ([get one here](https://developers.google.com/maps))

### 1. Clone the Repository

```bash
git clone https://github.com/ojusharma/fora.git
cd fora
```

### 2. Set Up Supabase

1. Create a new project at [supabase.com](https://supabase.com)
2. Run the database migrations:
   - Open SQL Editor in Supabase Dashboard
   - Execute `docs/schema.sql`
   - Execute `docs/user_interaction_schema.sql` (for ML features)
   - Execute `docs/rewards_schema.sql` (for rewards system)

### 3. Configure Environment Variables

#### Backend (`server/.env`)

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Email Configuration (optional, for notifications)
RESEND_API_KEY=your_resend_api_key
FROM_EMAIL=noreply@yourdomain.com

# Server Configuration
ENVIRONMENT=development
DEBUG=true
```

#### Frontend (`client/.env.local`)

```env
# Supabase
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=your_supabase_anon_key

# API
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Google Maps
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

### 4. Install Dependencies

```bash
# Backend
cd server
pip install -r requirements.txt

# Frontend (in new terminal)
cd client
npm install
```

### 5. Run the Application

```bash
# Start Backend (Terminal 1)
cd server
python run.py
# Server runs at http://localhost:8000

# Start Frontend (Terminal 2)
cd client
npm run dev
# App runs at http://localhost:3000
```

### 6. Create Your First Admin User

```sql
-- In Supabase SQL Editor
UPDATE user_profiles 
SET role = 'admin', credits = 1000 
WHERE uid = 'your-user-id-from-auth-users-table';
```

### 7. Access the Application

- **Main App**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Admin Panel**: http://localhost:3000/admin

---

## Architecture

### Tech Stack

#### Frontend
- **Framework**: Next.js 16 (App Router, Server Components)
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS 3.4
- **UI Components**: Radix UI primitives
- **State Management**: React hooks, Server Components
- **Maps**: Google Maps API (@react-google-maps/api)
- **Authentication**: Supabase Auth
- **HTTP Client**: Native fetch

#### Backend
- **Framework**: FastAPI (async/await)
- **Language**: Python 3.10+
- **Database**: PostgreSQL (via Supabase)
- **ORM**: Supabase Client (direct SQL queries)
- **ML Libraries**: scikit-learn, NumPy, SciPy
- **Background Jobs**: APScheduler
- **Validation**: Pydantic v2
- **Email**: Resend

#### Infrastructure
- **Database**: Supabase (PostgreSQL 15)
- **Authentication**: Supabase Auth
- **Storage**: Supabase Storage (for images)
- **Hosting**: Vercel (frontend), Azure App Service (backend)
- **CI/CD**: GitHub Actions



### Database Schema

#### Core Tables
- **listings** - Task postings with details, location, compensation
- **listing_applicants** - Applications to tasks
- **user_profiles** - Extended user data (credits, location, ratings)
- **tags** - Categories for listings
- **listing_tags** - Many-to-many relationship
- **notifications** - User notifications
- **user_stats** - Aggregated user statistics

#### Chat System
- **chat_rooms** - Conversation threads per listing
- **chat_messages** - Individual messages

#### Rewards System
- **rewards** - Available rewards in marketplace
- **reward_claims** - User reward redemptions

#### ML System (see [ML docs](docs/ML_FEED_README.md))
- **user_interactions** - Tracking user behavior
- **user_feature_vectors** - ML-computed preferences
- **listing_engagement_scores** - Popularity metrics
- **user_similarity_matrix** - Collaborative filtering data

---

## API Documentation

### Base URL
- **Development**: `http://localhost:8000`
- **Production**: Your deployed backend URL

### Interactive Docs
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`

### Key Endpoints

#### Listings
```
GET    /api/v1/listings                 # List all listings (with filters)
POST   /api/v1/listings                 # Create new listing
GET    /api/v1/listings/{id}            # Get listing details
PATCH  /api/v1/listings/{id}            # Update listing
DELETE /api/v1/listings/{id}            # Delete listing
POST   /api/v1/listings/{id}/confirm-completion  # Mark as complete
```

#### Applications
```
POST   /api/v1/listings/{id}/applicants/{uid}/apply      # Apply to listing
GET    /api/v1/listings/{id}/applicants                   # Get applicants
PATCH  /api/v1/listings/{id}/applicants/{uid}            # Update application
POST   /api/v1/listings/{id}/applicants/{uid}/shortlist  # Shortlist applicant
POST   /api/v1/listings/{id}/applicants/{uid}/reject     # Reject applicant
```

#### Personalized Feed
```
GET    /api/v1/feed?user_uid={uuid}          # Get personalized recommendations
POST   /api/v1/feed/interactions/{id}        # Track user interaction
GET    /api/v1/feed/trending                 # Get trending listings
POST   /api/v1/feed/nearby                   # Get nearby listings
```

#### Chat
```
GET    /api/v1/chats/{listing_id}/messages   # Get chat messages
POST   /api/v1/chats/{listing_id}/messages   # Send message
```

#### Notifications
```
GET    /api/v1/notifications?user_uid={uuid}     # Get user notifications
PATCH  /api/v1/notifications/{id}/read           # Mark as read
DELETE /api/v1/notifications/{id}                # Delete notification
```

#### Users
```
GET    /api/v1/users/{uid}                  # Get user profile
PATCH  /api/v1/users/{uid}                  # Update profile
PATCH  /api/v1/users/{uid}/location         # Update location
```

#### Rewards (Admin)
```
GET    /api/v1/admin/rewards                # List rewards
POST   /api/v1/admin/rewards                # Create reward
PATCH  /api/v1/admin/rewards/{id}           # Update reward
DELETE /api/v1/admin/rewards/{id}           # Delete reward
POST   /api/v1/rewards/{id}/claim           # Claim reward
```

See full API documentation at `/docs` when running the server.

---


## UI/UX Features

- **Responsive Design** - Mobile-first, works on all devices
- **Dark Mode** - System-aware theme switching
- **Interactive Maps** - Browse tasks geographically
- **Real-time Updates** - Live notifications and chat
- **Smooth Animations** - Polished transitions and interactions
- **Accessibility** - ARIA labels, keyboard navigation
- **Loading States** - Skeleton screens and suspense fallbacks

---

## Security

### Authentication
- Supabase Auth with JWT tokens
- Email verification
- Password reset flows
- OAuth providers (Google, GitHub, etc.)

### Authorization
- Row-Level Security (RLS) policies
- Role-based access control (user, moderator, admin)
- Protected API routes
- Server-side validation

### Data Protection
- Input sanitization
- SQL injection prevention
- CORS configuration
- Secure credit transactions
- Database triggers for business logic

---

## Deployment

### Production Deployment

**Live Application**: [https://fora-web.azurewebsites.net/](https://fora-web.azurewebsites.net/)

Fora is deployed on **Azure App Service** in the Canada Central region, using Infrastructure as Code (IaC) with ARM templates.

#### Azure Resources

- **App Service**: `fora-web` (Linux, Next.js)
- **Resource Group**: `fora-rg`
- **Region**: Canada Central
- **Managed Identity**: User-assigned identity for secure resource access

#### Deployment via ARM Templates

ARM templates are located in the `devops/` directory:

```bash
# Deploy web app
az deployment group create \
  --resource-group fora-rg \
  --template-file devops/fora-web-arm.json

# Deploy supporting infrastructure
az deployment group create \
  --resource-group fora-rg \
  --template-file devops/fora-prod-arm.json
```

#### Environment Variables (Azure App Service)

Configure the following in Azure Portal → App Service → Configuration:

```
NEXT_PUBLIC_SUPABASE_URL=<your-supabase-url>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-supabase-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>
GOOGLE_MAPS_API_KEY=<your-google-maps-key>
```

### Local Deployment Options

#### Frontend (Vercel)

```bash
cd client
npm run build
# Deploy to Vercel via GitHub integration
```

#### Backend (Docker)

```bash
cd server
docker build -t fora-backend .
docker run -p 8000:8000 --env-file .env fora-backend
```

### Database Migrations

Run migrations in Supabase SQL Editor:
1. `docs/schema.sql` - Core schema
2. `docs/user_interaction_schema.sql` - ML tables
3. `docs/rewards_schema.sql` - Rewards system

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Built with ❤️ by

- Ojus Sharma
- Mithish Ravisankar
- Ribhav Sharma
- Sparsh Khanna
---

