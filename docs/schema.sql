-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.listing_applicants (
  listing_id uuid NOT NULL,
  applicant_uid uuid NOT NULL,
  applied_at timestamp with time zone NOT NULL DEFAULT now(),
  status USER-DEFINED NOT NULL DEFAULT 'applied'::applicant_status,
  message text,
  CONSTRAINT listing_applicants_listing_id_fkey FOREIGN KEY (listing_id) REFERENCES public.listings(id),
  CONSTRAINT listing_applicants_applicant_uid_fkey FOREIGN KEY (applicant_uid) REFERENCES auth.users(id)
);
CREATE TABLE public.listing_tags (
  listing_id uuid NOT NULL,
  tag_id integer NOT NULL,
  CONSTRAINT listing_tags_pkey PRIMARY KEY (listing_id, tag_id),
  CONSTRAINT listing_tags_listing_id_fkey FOREIGN KEY (listing_id) REFERENCES public.listings(id),
  CONSTRAINT listing_tags_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tags(id)
);
CREATE TABLE public.listings (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL,
  description text,
  images jsonb,
  poster_uid uuid NOT NULL,
  assignee_uid uuid,
  applicants ARRAY DEFAULT '{}'::uuid[],
  tags ARRAY DEFAULT '{}'::integer[],
  status USER-DEFINED NOT NULL DEFAULT 'open'::listing_status,
  location_geog USER-DEFINED,
  latitude double precision,
  longitude double precision,
  deadline timestamp with time zone,
  compensation numeric,
  last_posted timestamp with time zone NOT NULL DEFAULT now(),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  poster_rating numeric DEFAULT NULL::numeric,
  assignee_rating numeric DEFAULT NULL::numeric,
  CONSTRAINT listings_pkey PRIMARY KEY (id),
  CONSTRAINT listings_poster_uid_fkey FOREIGN KEY (poster_uid) REFERENCES auth.users(id),
  CONSTRAINT listings_assignee_uid_fkey FOREIGN KEY (assignee_uid) REFERENCES auth.users(id)
);
CREATE TABLE public.tags (
  id integer NOT NULL DEFAULT nextval('tags_id_seq'::regclass),
  name text NOT NULL UNIQUE,
  CONSTRAINT tags_pkey PRIMARY KEY (id)
);
CREATE TABLE public.user_preferences (
  uid uuid NOT NULL,
  tag_id integer NOT NULL,
  CONSTRAINT user_preferences_pkey PRIMARY KEY (uid, tag_id),
  CONSTRAINT user_preferences_uid_fkey FOREIGN KEY (uid) REFERENCES auth.users(id),
  CONSTRAINT user_preferences_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tags(id)
);
CREATE TABLE public.user_profiles (
  uid uuid NOT NULL,
  dob date,
  phone text,
  role USER-DEFINED NOT NULL DEFAULT 'user'::user_role,
  credits integer NOT NULL DEFAULT 0,
  last_updated timestamp with time zone NOT NULL DEFAULT now(),
  location_geog USER-DEFINED,
  latitude double precision,
  longitude double precision,
  CONSTRAINT user_profiles_pkey PRIMARY KEY (uid),
  CONSTRAINT user_profiles_uid_fkey FOREIGN KEY (uid) REFERENCES auth.users(id)
);
CREATE TABLE public.user_stats (
  uid uuid NOT NULL,
  num_listings_posted integer NOT NULL DEFAULT 0,
  num_listings_applied integer NOT NULL DEFAULT 0,
  num_listings_assigned integer NOT NULL DEFAULT 0,
  num_listings_completed integer NOT NULL DEFAULT 0,
  avg_rating numeric DEFAULT NULL::numeric,
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT user_stats_pkey PRIMARY KEY (uid),
  CONSTRAINT user_stats_uid_fkey FOREIGN KEY (uid) REFERENCES auth.users(id)
);