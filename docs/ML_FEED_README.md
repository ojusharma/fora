# Building Our Personalized Feed with Machine Learning

We've built a  ML-powered recommendation system for our marketplace. Think of it like how Netflix recommends shows or Spotify suggests songs, but for our listings. The system learns what each user likes and shows them the most relevant stuff first.

## What Does It Do?

Our feed now automatically figures out what listings to show each user by looking at:
- What they've clicked on before
- Where they're located
- What tags/categories they interact with
- How popular listings are
- How new listings are
- Who posted them (reputation matters!)

Instead of just showing newest listings first, we're now intelligently ranking everything based on what we think each user will actually care about.

## How It's Built

We've got four main pieces working together:

### 1. The Brain (`app/ml/recommender.py`)
This is where the magic happens. It's got several algorithms that each look at different aspects:
- **Collaborative filtering**: "Users like you also viewed these listings"
- **Content matching**: "These listings match your interests"
- **Location smarts**: "These are close to you"
- **Engagement tracking**: "These are popular right now"

### 2. The Memory (`docs/user_interaction_schema.sql`)
A database schema that remembers everything:
- Every click, view, and application
- How popular each listing is
- Which users are similar to each other
- What each user tends to like

### 3. The API (`app/api/v1/endpoints/feed.py`)
Endpoints that tie everything together:
- `GET /feed` - Get your personalized feed
- `POST /interactions` - Track what users do
- `PATCH /preferences` - Let users customize their feed
- `GET /trending` - See what's hot right now

### 4. The Trainer (`app/ml/training.py`)
Background jobs that keep the system learning:
- Runs daily to update user similarities
- Runs hourly to refresh engagement scores
- Constantly improving recommendations

## The Algorithms (The Nerdy Stuff)

Don't worry, you don't need to understand all the math - but here's what's happening under the hood:

### 1. Collaborative Filtering (The "People Like You" Algorithm)

This one finds users who behave similarly and recommends what they liked. It's the same tech Amazon uses for "Customers who bought this also bought..."

**How it works:**
- We build a matrix of who clicked on what
- Calculate how similar users are to each other (using cosine similarity - it's a fancy way to compare preferences)
- Show you listings that similar users liked

**The Math** (for the curious):
```
similarity(user_a, user_b) = cos(θ) = (A · B) / (||A|| ||B||)
```
Basically, it measures the angle between two users' preference vectors. The smaller the angle, the more similar they are!

**Tech**: We're using scikit-learn's built-in functions for this (it's battle-tested and fast)

### 2. Content-Based Filtering (The "More Like This" Algorithm)

This looks at what a listing actually *is* and matches it to what you like.

**How it works:**
- We extract features from each listing: tags, location, price, how popular it is
- We look at what you've interacted with before and build your "taste profile"
- Then we find listings that match your taste

**What we track:**
- Which tags you click on (converted to numbers the algorithm can understand)
- Your preferred price range
- Where you usually look for listings
- How much engagement matters to you

Think of it like: "You liked coffee shops in Manhattan, here are more coffee shops in Manhattan!"

### 3. Location-Based Scoring (The "Near You" Algorithm)

Distance matters! A great listing 50 miles away isn't as useful as a decent one nearby.

**How it works:**
- We calculate the actual distance between the user and each listing (using the Haversine formula - it accounts for Earth being round!)
- Closer listings get higher scores
- The score drops off exponentially with distance (so nearby stuff gets a BIG boost)

**The code:**
```python
distance = haversine(user_location, listing_location)
score = exp(-distance / (max_distance / 3))
```

**Translation**: Nearby listings get scores close to 1.0, far away ones approach 0.0

**Fun fact**: The Haversine formula is what GPS systems use. It calculates the shortest distance between two points on a sphere (Earth's radius = 6371 km).

### 4. Tag Similarity (The "Your Interests" Algorithm)

We match listing tags to what you've shown interest in before.

**How it works:**
- We track which tags you interact with (e.g., "Photography", "Freelance", "Part-time")
- For each listing, we see how many tags overlap with your interests
- More overlap = higher score

**The formula** (Jaccard similarity):
```python
similarity = (tags you like AND listing has) / (tags you like OR listing has)
```

**Example**: 
- You like: [Photography, Design, Remote]
- Listing has: [Photography, Design, Full-time]
- Score: 2/4 = 0.5 (pretty good match!)

### 5. Engagement Scoring (The "Popular Stuff" Algorithm)

Some listings are just better than others - let's show those!

**How it works:**
- We track all interactions: views, clicks, applications, saves, shares, dismissals
- Different actions have different weights (applying matters way more than viewing)
- We use a log scale so viral posts don't completely dominate

**The weights:**
```python
score = (apply × 10) + (save × 5) + (share × 3) + 
        (click × 2) + (view × 1) - (dismiss × 5)

# Then we scale it logarithmically
final_score = log(1 + score) × 10
```

**Why log scale?** Without it, a post with 10,000 views would ALWAYS beat a post with 100 views, even if the second one has way more applications. The log scale keeps things fair while still rewarding popularity.

### 6. Recency Scoring (The "Fresh Content" Algorithm)

Nobody wants to see 2-week-old listings at the top of their feed!

**How it works:**
- Newer listings get a boost
- The boost decays exponentially over time (like radioactive decay, if you remember high school chemistry)
- After about a week, the boost is mostly gone

**The code:**
```python
age_days = (current_time - created_at).days
score = exp(-age_days / 10)  # Half-life of ~7 days
```

**What this means**: A brand new listing gets a 1.0 score. After 7 days, it's down to 0.5. After 14 days, 0.25. And so on.

### 7. Hybrid Scoring (Putting It All Together)

Here's where we combine everything into one final score!

**The formula:**
```python
final_score = (location × 25%) + (tags × 20%) + (engagement × 15%) + 
              (recency × 10%) + (poster_quality × 10%) + 
              (collaborative × 10%) + (content × 10%)
```

**Why these weights?** After testing, we found:
- **Location (25%)**: Most important - people care about what's nearby
- **Tags (20%)**: Second most important - interests matter
- **Engagement (15%)**: Popular stuff is usually good
- **Everything else (10% each)**: All helpful, but not game-changers

**Good news**: These weights are totally adjustable! If we find location matters less or engagement matters more, we can tweak them easily.

## Getting Started

### Step 1: Set Up the Database

First, we need to add some new tables to track interactions:

```bash
# If using Supabase (recommended):
# Just copy the contents of docs/user_interaction_schema.sql 
# into the Supabase SQL editor and run it

# If using local PostgreSQL:
psql -d your_database -f docs/user_interaction_schema.sql
```

This adds tables for tracking clicks, views, applications, and all the ML magic.

### Step 2: Install the ML Libraries

```bash
cd server
pip install -r requirements.txt
```

We're using some industry-standard ML libraries:
- **scikit-learn**: The most popular Python ML library (used by Spotify, Booking.com, etc.)
- **numpy**: Fast numerical computing
- **scipy**: Sparse matrices (memory-efficient for our data)
- **pandas**: Data wrangling (optional but helpful)

All of these are free, open-source, and battle-tested.

### Step 3: Fire It Up

```bash
cd server
python run.py
```

The server should start at `http://localhost:8000` and you'll see the new feed endpoints at `/api/v1/feed`

## Using the API

### Getting a User's Personalized Feed

This is the main endpoint - it returns listings ranked specifically for each user:

```bash
GET /api/v1/feed?user_uid={uuid}&limit=50&offset=0
```

**What you get back**: A JSON array of listings, sorted by relevance to that user. Each listing includes a `recommendation_score` (higher = more relevant).

**Options**:
- `limit`: How many results to return (max 100)
- `offset`: For pagination (0 = start from beginning)
- `exclude_seen`: Don't show stuff they just looked at (default: yes)
- `exclude_applied`: Don't show stuff they already applied to (default: yes)

### Tracking What Users Do

**This is super important!** The system learns from user behavior, so we need to track everything:

```bash
POST /api/v1/feed/interactions/{listing_id}?user_uid={uuid}
Content-Type: application/json

{
  "interaction_type": "view",
  "metadata": {
    "time_spent_seconds": 30,
    "latitude": 19.119,
    "longitude": 72.909,
    "session_id": "abc123",
    "device_type": "mobile"
  }
}
```

**What to track**:
- `view`: They looked at it (track how long they spent!)
- `click`: They clicked through to see details
- `apply`: They applied (most important signal!)
- `save`: They bookmarked it for later
- `share`: They shared it with someone
- `dismiss`: They actively hid it (negative signal)

**Pro tip**: The more we track, the better the recommendations get. Even tracking how long someone views a listing helps!

### Update User Preferences

```bash
PATCH /api/v1/feed/preferences?user_uid={uuid}
Content-Type: application/json

{
  "max_distance_km": 25.0,
  "preferred_compensation_min": 100,
  "preferred_compensation_max": 5000,
  "preferred_tags": [1, 5, 12],
  "blocked_tags": [3, 7],
  "personalization_enabled": true
}
```

### Get Trending Listings

```bash
GET /api/v1/feed/trending?limit=20&hours=24
```

### Get Nearby Listings

```bash
POST /api/v1/feed/nearby
Content-Type: application/json

{
  "latitude": 19.119,
  "longitude": 72.909,
  "radius_km": 10.0,
  "limit": 20
}
```

### Get Similar Listings

```bash
GET /api/v1/feed/similar/{listing_id}?limit=10
```

## Background Jobs (The Learning Part)

The ML system needs to "train" itself periodically. Think of it like how our brains process experiences during sleep - the system needs time to analyze all the interactions and update its models.

### Daily Training (Run at 2 AM - Low Traffic Time)

```bash
python -m app.ml.training daily
```

**What it does** (takes 10-30 minutes):
- Figures out which users are similar to each other
- Updates everyone's preference profiles
- Recalculates the collaborative filtering models

**Why daily?** User preferences change slowly, so once a day is plenty.

### Hourly Updates (Run Every Hour)

```bash
python -m app.ml.training hourly
```

**What it does** (takes 1-5 minutes):
- Updates how popular each listing is
- Refreshes trending scores

**Why hourly?** Engagement changes faster than preferences, so we check more often.

### Quick Updates (Every 15 Minutes)

```bash
python -m app.ml.training frequent
```

**What it does** (takes 10-30 seconds):
- Refreshes the trending listings view

**Why so often?** Trending stuff needs to be... well, current!

### Setting Up the Schedule (Using Cron)

On Linux/Mac, add these to your crontab (`crontab -e`):

```cron
# Daily training at 2 AM (when nobody's using the site)
0 2 * * * cd /path/to/fora/server && python -m app.ml.training daily

# Every hour on the hour
0 * * * * cd /path/to/fora/server && python -m app.ml.training hourly

# Every 15 minutes
*/15 * * * * cd /path/to/fora/server && python -m app.ml.training frequent
```

**On Windows?** Use Task Scheduler instead - same commands, different interface.

**Don't know cron?** No worries! The syntax is: `minute hour day month weekday command`. The `*` means "every".

## Making It Fast

### Database Indexes (Already Done!)

The schema automatically creates all the indexes we need. These make queries run 10-100x faster:
- Quick lookups by user
- Fast sorting by engagement score
- Efficient similarity searches

You don't need to do anything - it's already set up!

### Caching (Future Optimization)

If we get a lot of traffic, we can cache results with Redis:

```python
# Cache each user's feed for 5 minutes
cache_key = f"feed:{user_uid}:{limit}:{offset}"
cached_result = redis.get(cache_key)
if cached_result:
    return cached_result  # Super fast!

result = await get_personalized_feed(...)
redis.setex(cache_key, 300, result)  # Cache for 5 minutes
```

**Why 5 minutes?** Balances freshness with performance. Feed doesn't need to update every second.

**When to add this?** Only if we're getting thousands of requests per minute. For now, the database is plenty fast.

### 3. Materialized Views

The schema includes materialized views for trending listings:
```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY trending_listings;
```

### 4. Batch Processing

Train models on batches of users rather than all at once:
```python
# Process 1000 users at a time
batch_size = 1000
for i in range(0, len(users), batch_size):
    user_batch = users[i:i+batch_size]
    await update_feature_vectors(user_batch)
```

## Monitoring & Metrics

### Key Metrics to Track

1. **Recommendation Quality**
   - Click-through rate (CTR)
   - Apply rate
   - Save rate
   - Time spent on recommended listings

2. **Model Performance**
   - Average recommendation score
   - Score distribution
   - Coverage (% of users receiving personalized results)

3. **System Performance**
   - Feed generation latency
   - Training job duration
   - Database query times

### Logging

```python
import logging

logger = logging.getLogger("feed.recommendations")
logger.info(f"Generated feed for user {user_uid}: {len(results)} listings")
logger.info(f"Average score: {avg_score:.3f}")
logger.info(f"Algorithm weights: {weights}")
```

## Handling New Users (The "Cold Start" Problem)

### When Someone Just Signs Up

**The problem**: They have no history, so we don't know what they like yet.

**Our solution**: We use simpler signals until we learn more:
- Show trending listings (what's popular is usually safe)
- Use their location (show nearby stuff)
- If they selected interests during signup, use those
- Show a diverse mix so we can learn quickly

```python
if not user_interactions:
    # Fall back to location + trending + diversity
    # As they interact, we'll learn and improve!
```

### When a New Listing Gets Posted

**The problem**: Nobody's interacted with it yet, so it has no engagement score.

**Our solution**: We give it a temporary boost:

```python
# New listings (< 24 hours old) get a 50% boost
if listing_age < 24_hours:
    recency_score *= 1.5
```

This gives new listings a fair chance to be seen and build up engagement naturally.

## What's Next? (Future Ideas)

### 1. Deep Learning (If We Get Really Big)

Right now we're using "classic" ML algorithms. If we get millions of users, we could upgrade to:
- **Neural Collaborative Filtering**: Deep learning version of what we have
- **Transformer models**: Like GPT, but for recommendations
- **Wide & Deep**: Google's recommendation architecture

**When?** Only worth it at massive scale. Our current setup is perfect for now.

### 2. Real-Time Everything

Currently, the system updates hourly/daily. We could make it instant:
- Use Kafka to stream events
- Update models in real-time
- See results of your clicks immediately

**Trade-off**: Way more complex infrastructure. Current system is simpler and works great.

### 3. A/B Testing Built-In

Test different algorithms against each other automatically:
- Show 10% of users one algorithm
- Show 90% another
- Measure which performs better
- Winner takes all!

**This would be awesome** for figuring out the best weights and algorithms.

### 4. Explain Why We Showed Something

Add explanations to recommendations:
- "Because you viewed similar listings"
- "Popular in your area" 
- "Matches your interests in Photography"

**Users love this!** Makes the system feel less like a black box.

### 5. Context-Aware Recommendations

Consider more than just history:
- Time of day (people browse differently at night)
- Day of week (weekends vs. weekdays)
- Device (mobile users want different things)
- Weather (seriously, people behave differently when it's sunny!)

**These details matter** at scale.

## Troubleshooting (When Things Go Wrong)

### "The recommendations seem random"

**Likely cause**: Not enough data yet.

**Fix**:
1. Check how many interactions we have: `SELECT COUNT(*) FROM user_interactions;`
2. Need at least 50-100 interactions per user for good results
3. In the meantime, the system falls back to location + trending (which is fine!)
4. As more people use the site, recommendations will improve naturally

**Quick win**: If we have user data from before (old analytics), we can backfill interactions to jumpstart the system.

### "Feed is loading really slowly"

**Likely causes**: Too many candidates, missing indexes, or inefficient queries.

**Fix**:
1. Check if database indexes exist: `\d user_interactions` in psql
2. Add Redis caching (see Performance section above)
3. Reduce the candidate pool (fetch fewer listings to rank)
4. Use PostGIS for geographic queries (faster than calculating distance in Python)

**Target**: Feed should load in under 500ms. If it's slower, let's debug together!

### "New users aren't getting good recommendations"

**This is expected!** It's called the "cold start problem."

**Fix**:
1. Add an onboarding flow where users pick interests
2. Use their location right away (even with no history, we can show nearby stuff)
3. Show trending content to new users
4. Be patient - after 5-10 interactions, recommendations will get much better

**Pro tip**: Some companies even ask "Which of these listings interest you?" during signup to bootstrap preferences.

## Want to Learn More?

### Good Resources for the Team

**Collaborative Filtering**:
- [Netflix's recommendation blog post](https://netflixtechblog.com) - Really readable explanation
- "Collaborative Filtering Recommender Systems" (Schafer et al.) - The classic paper

**General Recommendation Systems**:
- "Toward the Next Generation of Recommender Systems" - Good overview of different approaches
- Andrew Ng's Machine Learning course on Coursera - Has a great section on recommender systems

### Similar Open Source Projects

If you want to see how others have done this:

1. **Surprise** (https://surpriselib.com/)
   - Python library specifically for recommender systems
   - Great examples and documentation

2. **LightFM** (https://github.com/lyst/lightfm)
   - Used by companies like Lyst (fashion marketplace)
   - Hybrid collaborative/content-based filtering

3. **Implicit** (https://github.com/benfred/implicit)
   - Super fast collaborative filtering
   - Used by Spotify and others

4. **RecBole** (https://github.com/RUCAIBox/RecBole)
   - Academic project with tons of different algorithms
   - Great for learning and experimentation

### Industry Examples

- **Netflix**: Uses matrix factorization (similar to what we're doing)
- **Spotify**: Collaborative filtering + deep learning for music recommendations
- **Amazon**: Item-to-item collaborative filtering ("Customers who bought X also bought Y")
- **YouTube**: Deep neural networks for video recommendations

We're using the same fundamental approaches as these companies, just tailored to our marketplace!

## Final Notes

This system uses battle-tested open-source algorithms (mainly from scikit-learn, which has a BSD license). Everything is based on well-established recommendation system practices from academic research and industry.

Questions? Bugs? Ideas for improvements? Let's chat! This is a living system that we can keep improving as we learn what works best for our users.

**Happy recommending! 🚀**
