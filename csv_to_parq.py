import duckdb
import os
from pathlib import Path

INPUT_DIR = "data/csv"
OUTPUT_DIR = "data/parq"

def clean_and_convert(csv_path, parquet_path):
    try:
        print(f"Processing: {csv_path}")
        
        with duckdb.connect() as con:
            col_query = f"""
            SELECT * FROM read_csv_auto('{csv_path}',
                sample_size=1,
                all_varchar=true
            )
            """
            col_result = con.execute(col_query)
            column_names = [desc[0] for desc in col_result.description]
            
            select_parts = []
            for col_name in column_names:
                col_lower = col_name.lower()
                
                if col_lower in ['id'] or col_lower.endswith('_id'):
                    select_parts.append(f'try_cast("{col_name}" AS INTEGER) AS "{col_name}"')
                elif col_lower in ['score', 'age', 'price', 'amount', 'value'] or any(word in col_lower for word in ['score', 'age', 'price', 'amount', 'value', 'count', 'num']):
                    select_parts.append(f'CASE WHEN try_cast("{col_name}" AS INTEGER) IS NOT NULL THEN try_cast("{col_name}" AS INTEGER) ELSE try_cast("{col_name}" AS DOUBLE) END AS "{col_name}"')
                elif col_lower in ['active', 'enabled', 'disabled', 'valid'] or any(word in col_lower for word in ['active', 'enabled', 'is_', 'has_']):
                    select_parts.append(f'try_cast("{col_name}" AS BOOLEAN) AS "{col_name}"')
                elif col_lower.endswith('_date') or col_lower.endswith('_time') or col_lower in ['date', 'time', 'created', 'updated']:
                    select_parts.append(f'try_cast("{col_name}" AS TIMESTAMP) AS "{col_name}"')
                else:
                    select_parts.append(f'"{col_name}"')
            
            select_clause = ", ".join(select_parts)
            
            clean_query = f"""
            COPY (
                SELECT {select_clause}
                FROM read_csv_auto('{csv_path}',
                    ignore_errors=true,
                    sample_size=-1,
                    all_varchar=true
                )
            ) TO '{parquet_path}' (FORMAT PARQUET, COMPRESSION GZIP)
            """
            
            con.execute(clean_query)
            print(f"Saved: {parquet_path}")
            
            stats_query = f"""
            SELECT COUNT(*) as total_rows
            FROM read_csv_auto('{csv_path}', ignore_errors=true, sample_size=-1, all_varchar=true)
            """
            stats = con.execute(stats_query).fetchone()
            print(f"  Total rows: {stats[0]}")
            
    except Exception as e:
        print(f"Error processing {csv_path}: {e}")
        return False
    
    return True

def main():
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    input_path = Path(INPUT_DIR)
    if not input_path.exists():
        print(f"Input directory {INPUT_DIR} does not exist!")
        return
    
    csv_files = list(input_path.glob("*.csv"))
    
    if not csv_files:
        print(f"No CSV files found in {INPUT_DIR}")
        return
    
    print(f"Found {len(csv_files)} CSV files to process")
    
    successful = 0
    failed = 0
    
    for csv_file in csv_files:
        parquet_name = csv_file.stem + ".parquet"
        parquet_path = Path(OUTPUT_DIR) / parquet_name
        
        if clean_and_convert(str(csv_file), str(parquet_path)):
            successful += 1
        else:
            failed += 1
    
    print(f"\nProcessing complete!")
    print(f"Successfully converted: {successful} files")
    if failed > 0:
        print(f"Failed to convert: {failed} files")

if __name__ == "__main__":
    main()
