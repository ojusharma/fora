-- User Interaction Tracking Schema for ML-based Feed Recommendations
-- This schema tracks user behavior to power personalized feed recommendations

-- ==================== INTERACTION TYPES ====================

CREATE TYPE interaction_type AS ENUM (
  'view',           -- User viewed a listing
  'click',          -- User clicked on a listing
  'apply',          -- User applied to a listing
  'save',           -- User saved/bookmarked a listing
  'share',          -- User shared a listing
  'dismiss'         -- User dismissed/hid a listing
);

-- ==================== USER INTERACTIONS TABLE ====================

CREATE TABLE user_interactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_uid UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  listing_id UUID NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
  interaction_type interaction_type NOT NULL,
  interaction_time TIMESTAMPTZ NOT NULL DEFAULT now(),
  session_id TEXT,                                    -- Optional: track session
  referrer TEXT,                                      -- How user found this listing
  time_spent_seconds INTEGER,                         -- Time spent viewing (for 'view' type)
  user_latitude DOUBLE PRECISION,                     -- User's location at interaction time
  user_longitude DOUBLE PRECISION,
  device_type TEXT,                                   -- mobile, desktop, tablet
  metadata JSONB                                      -- Additional context
);

-- Indexes for fast queries
CREATE INDEX idx_user_interactions_user ON user_interactions(user_uid, interaction_time DESC);
CREATE INDEX idx_user_interactions_listing ON user_interactions(listing_id, interaction_time DESC);
CREATE INDEX idx_user_interactions_type ON user_interactions(interaction_type);
CREATE INDEX idx_user_interactions_time ON user_interactions(interaction_time DESC);

-- ==================== USER FEED PREFERENCES ====================

CREATE TABLE user_feed_preferences (
  user_uid UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  max_distance_km DOUBLE PRECISION DEFAULT 50.0,      -- Max distance for listings
  preferred_compensation_min NUMERIC(12,2),
  preferred_compensation_max NUMERIC(12,2),
  preferred_tags INTEGER[],                            -- Array of preferred tag IDs
  blocked_tags INTEGER[],                              -- Tags to exclude
  blocked_users UUID[],                                -- Users to exclude
  show_applied_listings BOOLEAN DEFAULT FALSE,         -- Show listings already applied to
  show_completed_listings BOOLEAN DEFAULT FALSE,       -- Show completed listings
  personalization_enabled BOOLEAN DEFAULT TRUE,        -- Enable ML recommendations
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ==================== LISTING ENGAGEMENT METRICS ====================

CREATE TABLE listing_engagement_metrics (
  listing_id UUID PRIMARY KEY REFERENCES listings(id) ON DELETE CASCADE,
  view_count INTEGER NOT NULL DEFAULT 0,
  click_count INTEGER NOT NULL DEFAULT 0,
  apply_count INTEGER NOT NULL DEFAULT 0,
  save_count INTEGER NOT NULL DEFAULT 0,
  share_count INTEGER NOT NULL DEFAULT 0,
  dismiss_count INTEGER NOT NULL DEFAULT 0,
  avg_time_spent_seconds DOUBLE PRECISION DEFAULT 0,
  engagement_score DOUBLE PRECISION DEFAULT 0,         -- Computed score
  trending_score DOUBLE PRECISION DEFAULT 0,           -- Recent engagement weight
  last_updated TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_listing_engagement_score ON listing_engagement_metrics(engagement_score DESC);
CREATE INDEX idx_listing_trending_score ON listing_engagement_metrics(trending_score DESC);

-- ==================== USER SIMILARITY MATRIX ====================
-- For collaborative filtering: tracks users with similar behavior

CREATE TABLE user_similarity_matrix (
  user_a_uid UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  user_b_uid UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  similarity_score DOUBLE PRECISION NOT NULL,          -- 0.0 to 1.0
  interaction_count INTEGER NOT NULL DEFAULT 0,        -- Number of common interactions
  last_computed TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_a_uid, user_b_uid),
  CHECK (user_a_uid < user_b_uid)                      -- Ensure only one direction stored
);

CREATE INDEX idx_user_similarity_user_a ON user_similarity_matrix(user_a_uid, similarity_score DESC);
CREATE INDEX idx_user_similarity_user_b ON user_similarity_matrix(user_b_uid, similarity_score DESC);

-- ==================== LISTING FEATURE VECTORS ====================
-- For content-based filtering: pre-computed feature vectors

CREATE TABLE listing_feature_vectors (
  listing_id UUID PRIMARY KEY REFERENCES listings(id) ON DELETE CASCADE,
  tag_vector DOUBLE PRECISION[],                       -- Tag embeddings
  location_cluster INTEGER,                            -- Geographic cluster ID
  compensation_normalized DOUBLE PRECISION,            -- Normalized compensation
  poster_quality_score DOUBLE PRECISION,               -- Poster reputation
  feature_vector DOUBLE PRECISION[],                   -- Combined feature vector
  last_computed TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_listing_features_cluster ON listing_feature_vectors(location_cluster);

-- ==================== USER FEATURE VECTORS ====================
-- User preference vectors for content-based matching

CREATE TABLE user_feature_vectors (
  user_uid UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  tag_preference_vector DOUBLE PRECISION[],            -- Learned tag preferences
  location_preference_vector DOUBLE PRECISION[],       -- Preferred locations
  compensation_preference_mean DOUBLE PRECISION,
  compensation_preference_std DOUBLE PRECISION,
  activity_level DOUBLE PRECISION DEFAULT 0,           -- How active the user is
  feature_vector DOUBLE PRECISION[],                   -- Combined preference vector
  last_computed TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ==================== FEED IMPRESSIONS ====================
-- Track what was shown to users to avoid repetition

CREATE TABLE feed_impressions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_uid UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  listing_id UUID NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
  shown_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  position INTEGER NOT NULL,                           -- Position in feed
  score DOUBLE PRECISION,                              -- Recommendation score
  algorithm_version TEXT,                              -- Which algorithm version used
  interacted BOOLEAN DEFAULT FALSE,                    -- Did user interact?
  interaction_type interaction_type
);

CREATE INDEX idx_feed_impressions_user ON feed_impressions(user_uid, shown_at DESC);
CREATE INDEX idx_feed_impressions_listing ON feed_impressions(listing_id);

-- ==================== TRIGGERS ====================

-- Update listing engagement metrics on interaction
CREATE OR REPLACE FUNCTION update_listing_engagement() 
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO listing_engagement_metrics (listing_id)
  VALUES (NEW.listing_id)
  ON CONFLICT (listing_id) DO NOTHING;
  
  UPDATE listing_engagement_metrics
  SET 
    view_count = CASE WHEN NEW.interaction_type = 'view' THEN view_count + 1 ELSE view_count END,
    click_count = CASE WHEN NEW.interaction_type = 'click' THEN click_count + 1 ELSE click_count END,
    apply_count = CASE WHEN NEW.interaction_type = 'apply' THEN apply_count + 1 ELSE apply_count END,
    save_count = CASE WHEN NEW.interaction_type = 'save' THEN save_count + 1 ELSE save_count END,
    share_count = CASE WHEN NEW.interaction_type = 'share' THEN share_count + 1 ELSE share_count END,
    dismiss_count = CASE WHEN NEW.interaction_type = 'dismiss' THEN dismiss_count + 1 ELSE dismiss_count END,
    last_updated = now()
  WHERE listing_id = NEW.listing_id;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_listing_engagement
AFTER INSERT ON user_interactions
FOR EACH ROW EXECUTE FUNCTION update_listing_engagement();

-- ==================== HELPER FUNCTIONS ====================

-- Calculate engagement score for a listing
CREATE OR REPLACE FUNCTION calculate_engagement_score(listing_uuid UUID)
RETURNS DOUBLE PRECISION AS $$
DECLARE
  score DOUBLE PRECISION := 0.0;
  metrics RECORD;
BEGIN
  SELECT * INTO metrics 
  FROM listing_engagement_metrics 
  WHERE listing_id = listing_uuid;
  
  IF metrics IS NULL THEN
    RETURN 0.0;
  END IF;
  
  -- Weighted scoring: applies > saves > shares > clicks > views
  score := (metrics.apply_count * 10.0) +
           (metrics.save_count * 5.0) +
           (metrics.share_count * 3.0) +
           (metrics.click_count * 2.0) +
           (metrics.view_count * 1.0) -
           (metrics.dismiss_count * 5.0);
  
  RETURN GREATEST(score, 0.0);
END;
$$ LANGUAGE plpgsql;

-- Get user's preferred tags based on interaction history
CREATE OR REPLACE FUNCTION get_user_preferred_tags(user_uuid UUID, limit_count INTEGER DEFAULT 10)
RETURNS INTEGER[] AS $$
DECLARE
  tag_ids INTEGER[];
BEGIN
  SELECT ARRAY_AGG(DISTINCT unnest_tags.tag_id ORDER BY interaction_count DESC)
  INTO tag_ids
  FROM (
    SELECT unnest(l.tags) as tag_id, COUNT(*) as interaction_count
    FROM user_interactions ui
    JOIN listings l ON l.id = ui.listing_id
    WHERE ui.user_uid = user_uuid
      AND ui.interaction_type IN ('view', 'click', 'apply', 'save')
      AND ui.interaction_time >= now() - INTERVAL '90 days'
    GROUP BY unnest(l.tags)
    ORDER BY interaction_count DESC
    LIMIT limit_count
  ) unnest_tags;
  
  RETURN COALESCE(tag_ids, ARRAY[]::INTEGER[]);
END;
$$ LANGUAGE plpgsql;

-- Get similar users for collaborative filtering
CREATE OR REPLACE FUNCTION get_similar_users(user_uuid UUID, limit_count INTEGER DEFAULT 20)
RETURNS TABLE(similar_user_uid UUID, similarity DOUBLE PRECISION) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    CASE 
      WHEN user_a_uid = user_uuid THEN user_b_uid 
      ELSE user_a_uid 
    END as similar_user_uid,
    similarity_score as similarity
  FROM user_similarity_matrix
  WHERE user_a_uid = user_uuid OR user_b_uid = user_uuid
  ORDER BY similarity_score DESC
  LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- ==================== MATERIALIZED VIEWS ====================

-- Recently trending listings
CREATE MATERIALIZED VIEW trending_listings AS
SELECT 
  l.id,
  l.name,
  l.tags,
  l.latitude,
  l.longitude,
  lem.engagement_score,
  lem.trending_score,
  COUNT(DISTINCT ui.user_uid) FILTER (WHERE ui.interaction_time >= now() - INTERVAL '24 hours') as recent_users,
  COUNT(*) FILTER (WHERE ui.interaction_type = 'view' AND ui.interaction_time >= now() - INTERVAL '24 hours') as recent_views,
  COUNT(*) FILTER (WHERE ui.interaction_type = 'apply' AND ui.interaction_time >= now() - INTERVAL '24 hours') as recent_applies
FROM listings l
LEFT JOIN listing_engagement_metrics lem ON lem.listing_id = l.id
LEFT JOIN user_interactions ui ON ui.listing_id = l.id
WHERE l.status = 'open'
  AND l.created_at >= now() - INTERVAL '30 days'
GROUP BY l.id, l.name, l.tags, l.latitude, l.longitude, lem.engagement_score, lem.trending_score
ORDER BY recent_applies DESC, recent_views DESC;

CREATE INDEX idx_trending_listings_score ON trending_listings(trending_score DESC);

-- Refresh trending listings view periodically (call from cron job)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY trending_listings;
