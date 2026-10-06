from supabase import create_client, Client

SUPABASE_URL = "https://cauujrnxtqswjzqhphyq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNhdXVqcm54dHFzd2p6cWhwaHlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4ODM0MTA0MywiZXhwIjoyMTAzOTE3MDQzfQ.17AG1uMHj14ZNVuzp56-9_Z2KYeG50Oo3k__kDbhUok"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)