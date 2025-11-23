# ML Feed System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER INTERACTIONS                           │
│  (Views, Clicks, Applications, Saves, Shares, Dismissals)           │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    INTERACTION TRACKING LAYER                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  POST /api/v1/feed/interactions/{listing_id}                  │  │
│  │  • Tracks user behavior in real-time                          │  │
│  │  • Stores: user_uid, listing_id, type, metadata, timestamp    │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DATABASE LAYER                               │
│  ┌───────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │ user_interactions │  │ engagement_      │  │ user_similarity │ │
│  │ • user_uid        │  │ metrics          │  │ _matrix         │ │
│  │ • listing_id      │  │ • view_count     │  │ • user_a_uid    │ │
│  │ • type            │  │ • click_count    │  │ • user_b_uid    │ │
│  │ • timestamp       │  │ • apply_count    │  │ • similarity    │ │
│  │ • metadata        │  │ • engagement_    │  │ • last_computed │ │
│  │                   │  │   score          │  │                 │ │
│  └───────────────────┘  └──────────────────┘  └─────────────────┘ │
│                                                                      │
│  ┌───────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │ user_feed_        │  │ listing_feature_ │  │ user_feature_   │ │
│  │ preferences       │  │ vectors          │  │ vectors         │ │
│  │ • max_distance    │  │ • tag_vector     │  │ • tag_           │ │
│  │ • preferred_tags  │  │ • location       │  │   preference    │ │
│  │ • blocked_tags    │  │ • compensation   │  │ • compensation_ │ │
│  │ • personalization │  │ • poster_score   │  │   preference    │ │
│  │   _enabled        │  │ • feature_vector │  │ • activity_level│ │
│  └───────────────────┘  └──────────────────┘  └─────────────────┘ │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ML RECOMMENDATION ENGINE                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                  COLLABORATIVE FILTERING                      │  │
│  │  • Builds user-item interaction matrix                        │  │
│  │  • Calculates user-user similarity (cosine)                   │  │
│  │  • "Users like you also viewed..."                            │  │
│  │  • Weight: 10%                                                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                  CONTENT-BASED FILTERING                      │  │
│  │  • Extracts listing features (tags, location, compensation)   │  │
│  │  • Builds user preference vectors                             │  │
│  │  • Matches listings to preferences                            │  │
│  │  • Weight: 10%                                                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                  LOCATION-BASED SCORING                       │  │
│  │  • Haversine distance calculation                             │  │
│  │  • Exponential decay with distance                            │  │
│  │  • Closer listings rank higher                                │  │
│  │  • Weight: 25%                                                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    TAG SIMILARITY                             │  │
│  │  • Jaccard coefficient (intersection / union)                 │  │
│  │  • Matches user interests to listing tags                     │  │
│  │  • Weight: 20%                                                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                  ENGAGEMENT SCORING                           │  │
│  │  • Weighted: apply(10) + save(5) + share(3) + click(2) +     │  │
│  │    view(1) - dismiss(5)                                       │  │
│  │  • Log-scaled to prevent viral bias                           │  │
│  │  • Weight: 15%                                                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    RECENCY SCORING                            │  │
│  │  • Exponential time decay                                     │  │
│  │  • Newer listings get priority                                │  │
│  │  • Weight: 10%                                                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                  POSTER QUALITY                               │  │
│  │  • Average rating                                             │  │
│  │  • Completion rate                                            │  │
│  │  • Experience factor                                          │  │
│  │  • Weight: 10%                                                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    HYBRID COMBINER                            │  │
│  │  final_score = Σ(weight_i × component_score_i)               │  │
│  │  • Weighted sum of all components                             │  │
│  │  • Adjustable weights                                         │  │
│  │  • Returns ranked list                                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      API RESPONSE LAYER                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  GET /api/v1/feed?user_uid={uuid}&limit=50                    │  │
│  │  • Returns ranked listings                                    │  │
│  │  • Includes recommendation scores                             │  │
│  │  • Excludes seen/applied listings                             │  │
│  │  • Respects user preferences                                  │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       CLIENT APPLICATION                             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  • Displays personalized feed                                 │  │
│  │  • Tracks user interactions                                   │  │
│  │  │  - Views (time spent)                                      │  │
│  │  │  - Clicks                                                  │  │
│  │  │  - Applications                                            │  │
│  │  │  - Saves/Dismisses                                         │  │
│  │  • Sends feedback to system                                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             │  (feedback loop)
                             └────────────────┐
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    BACKGROUND TRAINING JOBS                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  DAILY (2 AM):                                                │  │
│  │  • Compute user similarity matrix                             │  │
│  │  • Update user feature vectors                                │  │
│  │  • Train collaborative filtering models                       │  │
│  │  • Duration: ~10-30 minutes                                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  HOURLY:                                                      │  │
│  │  • Update engagement scores                                   │  │
│  │  • Recalculate trending scores                                │  │
│  │  • Duration: ~1-5 minutes                                     │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  EVERY 15 MINUTES:                                            │  │
│  │  • Refresh trending listings view                             │  │
│  │  • Duration: ~10-30 seconds                                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘


DATA FLOW:
==========

1. User views listing → POST /interactions → Database
2. Background jobs process data → Compute similarities → Update vectors
3. User requests feed → GET /feed → ML engine ranks listings → Returns results
4. User interacts with results → Tracks feedback → Loop continues

ALGORITHM FLOW:
===============

Input: user_uid, candidate_listings
  │
  ├─→ Get user profile (location, preferences)
  │
  ├─→ For each candidate listing:
  │     ├─→ Calculate location_score (Haversine)
  │     ├─→ Calculate tag_similarity (Jaccard)
  │     ├─→ Calculate engagement_score (weighted sum)
  │     ├─→ Calculate recency_score (time decay)
  │     ├─→ Calculate poster_quality_score
  │     ├─→ Get collaborative_score (similar users)
  │     └─→ Get content_score (feature matching)
  │
  ├─→ Combine scores: final = Σ(weight_i × score_i)
  │
  ├─→ Sort by final_score (descending)
  │
  └─→ Return top N listings

SCALABILITY:
============

Current: ✅ Handles 10K users, 100K listings, 1M interactions
Optimized: ✅ Can scale to 100K users, 1M listings, 10M interactions

With additional optimizations:
- Redis caching → 1M users
- Horizontal scaling → 10M users
- Spark for training → 100M users


KEY METRICS TO MONITOR:
========================

1. Recommendation Quality:
   - CTR: clicks / impressions (Target: >5%)
   - Apply Rate: applies / clicks (Target: >10%)
   - Time Spent: avg seconds per listing (Target: >30s)

2. System Performance:
   - Feed Generation: <500ms (Target: <200ms)
   - Training Duration: <30min daily (Target: <15min)
   - Database Queries: <100ms (Target: <50ms)

3. Model Coverage:
   - Users with personalization: >80%
   - Listings in feed: >90%
   - Similar users found: >70%
```

## Component Dependencies

```
scikit-learn (BSD License)
├── cosine_similarity → Collaborative filtering
├── StandardScaler → Feature normalization
└── KMeans → Location clustering (optional)

numpy (BSD License)
├── Array operations
├── Matrix calculations
└── Mathematical functions

scipy (BSD License)
├── Sparse matrices → Memory-efficient storage
└── Distance calculations

PostgreSQL/Supabase
├── PostGIS → Geographic queries
├── Triggers → Auto-updates
└── Materialized Views → Fast trending
```

## Algorithm Complexity

```
Feed Generation:
  Time: O(n log n) where n = candidate listings
  Space: O(n)
  Per request: ~100-500ms

Training (Daily):
  Similarity Matrix: O(u²·i) where u = users, i = items
  Feature Vectors: O(u·i)
  Total: ~10-30 minutes for 10K users

Database Queries:
  Interactions: O(log n) with indexes
  Feed: O(n) for filtering + O(n log n) for sorting
  Trending: O(1) with materialized view
```
