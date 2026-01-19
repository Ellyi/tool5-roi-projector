import psycopg2

# Railway PostgreSQL public connection
DATABASE_URL = "postgresql://postgres:dlkbpbLyksIHtZfLEicctAxjUncNTotr@metro.proxy.rlwy.net:14980/railway"

print("Connecting to database...")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("Reading schema.sql...")
with open('schema.sql', 'r') as f:
    schema = f.read()

print("Creating tables...")
cur.execute(schema)
conn.commit()

print("✅ Tables created successfully!")
print("✅ roi_projections")
print("✅ roi_patterns")
print("✅ roi_insights")
print("✅ sessions")

cur.close()
conn.close()