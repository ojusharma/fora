-- Migration to add 'completed' status to listing_status enum
-- Run this in your Supabase SQL Editor

ALTER TYPE listing_status ADD VALUE IF NOT EXISTS 'completed';
