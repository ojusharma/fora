#!/usr/bin/env python3
"""
Script to promote a user to admin role.
Usage: python create_admin.py <user_email>
"""

import sys
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_admin(user_email: str) -> None:
    """
    Promote a user to admin role by their email address.
    
    Args:
        user_email: Email address of the user to promote
    """
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
        sys.exit(1)
    
    # Initialize Supabase client
    supabase: Client = create_client(supabase_url, supabase_key)
    
    try:
        # Find user by email in auth.users
        print(f"Looking up user with email: {user_email}")
        
        # Get user from Supabase Auth
        users_response = supabase.auth.admin.list_users()
        user = None
        
        for u in users_response:
            if u.email == user_email:
                user = u
                break
        
        if not user:
            print(f"Error: No user found with email {user_email}")
            sys.exit(1)
        
        user_uid = user.id
        print(f"Found user: {user.email} (UID: {user_uid})")
        
        # Check if user profile exists
        profile_response = supabase.table("user_profiles").select("*").eq("uid", user_uid).execute()
        
        if not profile_response.data:
            print(f"Error: No user profile found for UID {user_uid}")
            print("The user must have a profile record in user_profiles table")
            sys.exit(1)
        
        current_role = profile_response.data[0].get("role", "user")
        print(f"Current role: {current_role}")
        
        # Update role to admin
        update_response = supabase.table("user_profiles").update({"role": "admin"}).eq("uid", user_uid).execute()
        
        if update_response.data:
            print(f"✅ Successfully promoted {user_email} to admin!")
            print(f"   UID: {user_uid}")
            print(f"   Old role: {current_role}")
            print(f"   New role: admin")
        else:
            print("Error: Failed to update user role")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def list_admins() -> None:
    """List all current admin users."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
        sys.exit(1)
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    try:
        response = supabase.table("user_profiles").select("uid, display_name, role").eq("role", "admin").execute()
        
        if not response.data:
            print("No admin users found.")
            return
        
        print("\n📋 Current Admin Users:")
        print("-" * 70)
        for admin in response.data:
            display_name = admin.get("display_name", "N/A")
            print(f"  UID: {admin['uid']}")
            print(f"  Name: {display_name}")
            print(f"  Role: {admin['role']}")
            print("-" * 70)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python create_admin.py <user_email>     - Promote user to admin")
        print("  python create_admin.py --list           - List all admin users")
        sys.exit(1)
    
    if sys.argv[1] == "--list":
        list_admins()
    else:
        user_email = sys.argv[1]
        create_admin(user_email)
