import os
import duckdb

# 1. Grab environment variables from your existing pipeline setup
account_name = os.getenv("STORAGE_ACCOUNT_NAME", "samainafdap123987123")
bronze_container = os.getenv("CONTAINER_NAME", "bronze")
silver_container = os.getenv("SILVER_CONTAINER_NAME", "silver")

# 2. Spin up an in-memory DuckDB session and inject the Azure driver
con = duckdb.connect(database=':memory:')
con.execute("INSTALL azure; LOAD azure;")
con.execute("SET GLOBAL azure_transport_option_type = 'curl';")

# 3. Authenticate using your local Azure CLI / Managed Identity context
con.execute(f"""
    CREATE SECRET azure_identity (
        TYPE AZURE,
        PROVIDER CREDENTIAL_CHAIN,
        ACCOUNT_NAME '{account_name}'
    );
""")

print("\n🔍 --- AUDITING BRONZE LAYER (RAW JSON) ---")
bronze_path = f"az://{bronze_container}/f1/results/season=2014/bronze_results_2014.json"

try:
    bronze_res = con.execute(f"""
        SELECT 
            MRData.limit AS api_limit,
            MRData.total AS total_records,
            len(MRData.RaceTable.Races) AS races_captured
        FROM read_json_auto('{bronze_path}');
    """).fetchone()
    
    print(f"• API Limit Parameter:   {bronze_res[0]}")
    print(f"• Total Records in DB:   {bronze_res[1]}")
    print(f"• Races in JSON File:    {bronze_res[2]}")
except Exception as e:
    print(f"❌ Failed to parse Bronze JSON: {e}")

print("\n💎 --- AUDITING SILVER LAYER (PARQUET) ---")
silver_path = f"az://{silver_container}/race_results/season=2014/*.parquet"

try:
    silver_res = con.execute(f"""
        SELECT 
            count(*) AS total_rows,
            count(DISTINCT raceId) AS total_races,
            list_sort(list(DISTINCT raceId)) AS race_ids_present
        FROM read_parquet('{silver_path}');
    """).fetchone()
    
    print(f"• Total Rows in Parquet:  {silver_res[0]}")
    print(f"• Total Distinct Rounds:  {silver_res[1]}")
    print(f"• List of Rounds Found:   {silver_res[2]}")
except Exception as e:
    print(f"❌ Failed to read Silver Parquet: {e}")