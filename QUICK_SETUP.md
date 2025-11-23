# Quick Setup Guide - Create Rewards Tables

## Step 1: Open Supabase SQL Editor

1. Go to: **https://app.supabase.com**
2. Sign in if needed
3. Select your project: **hoaxrkhwzmtohhwibsih**
4. Click on **"SQL Editor"** in the left sidebar
5. Click **"New Query"** button

## Step 2: Copy the SQL

The SQL code you need is in: `docs/rewards_schema.sql`

Or copy this entire block:

```sql
-- Rewards System Schema
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

CREATE TABLE reward_claims (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  reward_id UUID NOT NULL REFERENCES rewards(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  credits_spent INTEGER NOT NULL,
  reward_title TEXT NOT NULL,
  claimed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  email_sent BOOLEAN NOT NULL DEFAULT false,
  email_sent_at TIMESTAMPTZ,
  UNIQUE(id)
);

CREATE INDEX idx_reward_claims_user ON reward_claims (user_id);
CREATE INDEX idx_reward_claims_reward ON reward_claims (reward_id);
CREATE INDEX idx_reward_claims_claimed_at ON reward_claims (claimed_at);

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

CREATE OR REPLACE FUNCTION validate_reward_claim()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
  user_credits INTEGER;
  reward_credits INTEGER;
  reward_active BOOLEAN;
BEGIN
  SELECT credits INTO user_credits
  FROM user_profiles
  WHERE uid = NEW.user_id;
  
  SELECT credits_required, is_active INTO reward_credits, reward_active
  FROM rewards
  WHERE id = NEW.reward_id;
  
  IF NOT reward_active THEN
    RAISE EXCEPTION 'This reward is no longer available';
  END IF;
  
  IF user_credits < reward_credits THEN
    RAISE EXCEPTION 'Insufficient credits. Required: %, Available: %', reward_credits, user_credits;
  END IF;
  
  UPDATE user_profiles
  SET credits = credits - reward_credits
  WHERE uid = NEW.user_id;
  
  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_reward_claim
BEFORE INSERT ON reward_claims
FOR EACH ROW EXECUTE FUNCTION validate_reward_claim();
```

## Step 3: Run the SQL

1. Paste the SQL into the editor
2. Click the green **"Run"** button (or press Cmd/Ctrl + Enter)
3. Wait for success message

## Step 4: Verify Tables Created

In Supabase:
1. Go to **"Table Editor"** in left sidebar
2. You should see two new tables:
   - **rewards**
   - **reward_claims**

## Step 5: Start Your Application

```bash
# Terminal 1 - Backend
cd server
python3 run.py

# Terminal 2 - Frontend
cd client
npm run dev
```

## Step 6: Test It!

1. **As Admin:**
   - Go to: http://localhost:3000/admin/rewards
   - Create a test reward (e.g., "Test Reward" for 10 credits)

2. **As User:**
   - Look for the gold coin icon in top-right navigation
   - Click it to open rewards modal
   - Try claiming a reward!

## Troubleshooting

### "User does not have enough credits"
Make sure your test user has credits:
```sql
UPDATE user_profiles SET credits = 1000 WHERE uid = 'your-user-id';
```

### "Access denied" on admin page
Make sure your user has admin role:
```sql
UPDATE user_profiles SET role = 'admin' WHERE uid = 'your-user-id';
```

### Can't see credits in navigation
- Make sure you're logged in
- Refresh the page
- Check browser console for errors

## Done! 🎉

Your rewards system is now ready to use!
