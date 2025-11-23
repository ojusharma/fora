-- Rewards System Schema
-- This schema adds a reward system where admins can create rewards
-- that users can claim using their credits

-- Table to store rewards configured by admins
CREATE TABLE rewards (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  description TEXT,
  credits_required INTEGER NOT NULL CHECK (credits_required > 0),
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_rewards_is_active ON rewards (is_active);
CREATE INDEX idx_rewards_created_by ON rewards (created_by);

-- Table to track reward claims by users
CREATE TABLE reward_claims (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  reward_id UUID NOT NULL REFERENCES rewards(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  credits_spent INTEGER NOT NULL,
  reward_title TEXT NOT NULL, -- Store title at time of claim
  claimed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  email_sent BOOLEAN NOT NULL DEFAULT false,
  email_sent_at TIMESTAMPTZ,
  
  -- Ensure a user can claim the same reward multiple times if needed
  -- but track each claim separately
  UNIQUE(id)
);

CREATE INDEX idx_reward_claims_user ON reward_claims (user_id);
CREATE INDEX idx_reward_claims_reward ON reward_claims (reward_id);
CREATE INDEX idx_reward_claims_claimed_at ON reward_claims (claimed_at);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_rewards_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_rewards_update_timestamp
BEFORE UPDATE ON rewards
FOR EACH ROW EXECUTE FUNCTION update_rewards_updated_at();

-- Function to validate user has enough credits before claiming
CREATE OR REPLACE FUNCTION validate_reward_claim()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
  user_credits INTEGER;
  reward_credits INTEGER;
  reward_active BOOLEAN;
BEGIN
  -- Get user's current credits
  SELECT credits INTO user_credits
  FROM user_profiles
  WHERE uid = NEW.user_id;
  
  -- Get reward details
  SELECT credits_required, is_active INTO reward_credits, reward_active
  FROM rewards
  WHERE id = NEW.reward_id;
  
  -- Check if reward is active
  IF NOT reward_active THEN
    RAISE EXCEPTION 'This reward is no longer available';
  END IF;
  
  -- Check if user has enough credits
  IF user_credits < reward_credits THEN
    RAISE EXCEPTION 'Insufficient credits. Required: %, Available: %', reward_credits, user_credits;
  END IF;
  
  -- Deduct credits from user
  UPDATE user_profiles
  SET credits = credits - reward_credits
  WHERE uid = NEW.user_id;
  
  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_reward_claim
BEFORE INSERT ON reward_claims
FOR EACH ROW EXECUTE FUNCTION validate_reward_claim();
