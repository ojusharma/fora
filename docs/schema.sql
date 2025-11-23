CREATE TYPE listing_status AS ENUM (
  'open',
  'in_progress',
  'pending_confirmation',
  'completed',
  'cancelled'
);

CREATE TYPE applicant_status AS ENUM (
  'applied',
  'shortlisted',
  'rejected',
  'withdrawn',
  'pending_confirmation',
  'completed'
);

CREATE TYPE user_role AS ENUM (
  'user',
  'moderator',
  'admin'
);

CREATE TYPE rating_type AS ENUM (
  'poster',
  'assignee'
);



CREATE TABLE tags (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE user_profiles (
  uid UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  dob DATE,
  phone TEXT,
  role user_role NOT NULL DEFAULT 'user',
  credits INTEGER NOT NULL DEFAULT 0,
  last_updated TIMESTAMPTZ NOT NULL DEFAULT now(),

  -- no PostGIS
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  user_rating NUMERIC(3, 2),
  no_ratings INTEGER NOT NULL DEFAULT 0
);


CREATE INDEX idx_user_profiles_location_latlng
  ON user_profiles (latitude, longitude);

CREATE TABLE listings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  description TEXT,
  images JSONB,

  poster_uid UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  assignee_uid UUID REFERENCES auth.users(id) ON DELETE SET NULL,

  status listing_status NOT NULL DEFAULT 'open',

  -- location fields
  location_address TEXT,
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,

  deadline TIMESTAMPTZ,
  compensation NUMERIC(12, 2),

  last_posted TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  poster_rating NUMERIC(3, 2),
  assignee_rating NUMERIC(3, 2)
);

CREATE INDEX idx_listings_status ON listings (status);
CREATE INDEX idx_listings_deadline ON listings (deadline);
CREATE INDEX idx_listings_poster ON listings (poster_uid);
CREATE INDEX idx_listings_assignee ON listings (assignee_uid);




CREATE TABLE listing_tags (
  listing_id UUID NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
  tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY (listing_id, tag_id)
);



CREATE TABLE listing_applicants (
  listing_id UUID NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
  applicant_uid UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  applied_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  status applicant_status NOT NULL DEFAULT 'applied',
  message TEXT,

  PRIMARY KEY (listing_id, applicant_uid)
);

CREATE INDEX idx_listing_applicants_listing ON listing_applicants (listing_id);
CREATE INDEX idx_listing_applicants_applicant ON listing_applicants (applicant_uid);

CREATE TABLE user_preferences (
  uid UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY (uid, tag_id)
);

CREATE INDEX idx_user_preferences_uid
  ON user_preferences (uid);



CREATE TABLE user_stats (
  uid UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  num_listings_posted INTEGER NOT NULL DEFAULT 0,
  num_listings_applied INTEGER NOT NULL DEFAULT 0,
  num_listings_assigned INTEGER NOT NULL DEFAULT 0,
  num_listings_completed INTEGER NOT NULL DEFAULT 0,
  avg_rating NUMERIC(3, 2),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);



CREATE OR REPLACE FUNCTION refresh_listing_rating_avgs(listing_uuid UUID)
RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
  UPDATE listings
  SET
    poster_rating = sub.poster_avg,
    assignee_rating = sub.assignee_avg
  FROM (
    SELECT
      AVG(rating) FILTER (WHERE rating_type = 'poster') AS poster_avg,
      AVG(rating) FILTER (WHERE rating_type = 'assignee') AS assignee_avg
    FROM listing_ratings
    WHERE listing_id = listing_uuid
  ) AS sub
  WHERE id = listing_uuid;
END;
$$;

CREATE OR REPLACE FUNCTION trg_listing_ratings_after_change()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  PERFORM refresh_listing_rating_avgs(NEW.listing_id);
  RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION trg_listing_ratings_after_delete()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  PERFORM refresh_listing_rating_avgs(OLD.listing_id);
  RETURN OLD;
END;
$$;

CREATE TRIGGER trg_listing_ratings_after_insert
AFTER INSERT ON listing_ratings
FOR EACH ROW EXECUTE FUNCTION trg_listing_ratings_after_change();

CREATE TRIGGER trg_listing_ratings_after_update
AFTER UPDATE ON listing_ratings
FOR EACH ROW EXECUTE FUNCTION trg_listing_ratings_after_change();

CREATE TRIGGER trg_listing_ratings_after_delete
AFTER DELETE ON listing_ratings
FOR EACH ROW EXECUTE FUNCTION trg_listing_ratings_after_delete();



CREATE OR REPLACE FUNCTION prevent_self_apply()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM listings
    WHERE id = NEW.listing_id
      AND poster_uid = NEW.applicant_uid
  ) THEN
    RAISE EXCEPTION 'Poster cannot apply to their own listing';
  END IF;

  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_prevent_self_apply
BEFORE INSERT ON listing_applicants
FOR EACH ROW EXECUTE FUNCTION prevent_self_apply();
