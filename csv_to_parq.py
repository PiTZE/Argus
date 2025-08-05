import duckdb
import os

INPUT_DIR = "data/csv"
OUTPUT_DIR = "data/parq"

os.makedirs(OUTPUT_DIR, exist_ok=True)

con = duckdb.connect()

def clean_and_convert(csv_path, parquet_path):
    print(f"Processing: {csv_path}")
    sample_query = f"SELECT * FROM read_csv_auto('{csv_path}', sample_size=-1)"
    con.execute(sample_query)
    col_types = con.get_columns()

    select_parts = []
    for col in col_types:
        col_name = col.name
        duck_type = col.logical_type
        if duck_type.upper() == "VARCHAR":
            select_parts.append(f'"{col_name}"')
        else:
            select_parts.append(f'try_cast("{col_name}" AS {duck_type}) AS "{col_name}"')

    select_clause = ", ".join(select_parts)
    clean_query = f"""
    COPY (
        SELECT {select_clause}
        FROM read_csv_auto('{csv_path}', sample_size=-1)
    ) TO '{parquet_path}' (FORMAT PARQUET, COMPRESSION GZIP)
    """
    con.execute(clean_query)
    print(f"Saved: {parquet_path}")

for filename in os.listdir(INPUT_DIR):
    if filename.endswith(".csv"):
        csv_path = os.path.join(INPUT_DIR, filename)
        parquet_name = os.path.splitext(filename)[0] + ".parquet"
        parquet_path = os.path.join(OUTPUT_DIR, parquet_name)
        clean_and_convert(csv_path, parquet_path)

print("Done.")
