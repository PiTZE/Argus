import duckdb
import os
import sys
import time
import logging
import psutil
from pathlib import Path
from datetime import datetime

INPUT_DIR = "data/csv"
OUTPUT_DIR = "data/parq"

def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"csv_to_parq_{timestamp}.log"
    
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    logger = logging.getLogger('csv_to_parq')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_file_size_mb(file_path):
    return os.path.getsize(file_path) / (1024 * 1024)

def get_memory_usage():
    process = psutil.Process()
    memory_info = process.memory_info()
    return {
        'rss_mb': memory_info.rss / (1024 * 1024),
        'vms_mb': memory_info.vms / (1024 * 1024),
        'percent': process.memory_percent()
    }

def log_system_info(logger):
    try:
        memory = psutil.virtual_memory()
        logger.info(f"System Memory - Total: {memory.total / (1024**3):.1f}GB, Available: {memory.available / (1024**3):.1f}GB, Used: {memory.percent}%")
        logger.info(f"CPU Count: {psutil.cpu_count()}")
    except Exception as e:
        logger.warning(f"Could not get system info: {e}")

def clean_and_convert(csv_path, parquet_path, logger, file_index, total_files):
    start_time = time.time()
    
    try:
        file_size_mb = get_file_size_mb(csv_path)
        logger.info(f"[{file_index}/{total_files}] Processing: {csv_path}")
        logger.info(f"File size: {file_size_mb:.1f} MB")
        
        initial_memory = get_memory_usage()
        logger.debug(f"Initial memory usage: RSS={initial_memory['rss_mb']:.1f}MB, VMS={initial_memory['vms_mb']:.1f}MB, %={initial_memory['percent']:.1f}%")
        
        with duckdb.connect() as con:
            con.execute("SET memory_limit='1GB'")
            con.execute("SET threads=2")
            
            logger.info("Step 1/3: Analyzing column structure...")
            col_query = f"""
            SELECT * FROM read_csv_auto('{csv_path}',
                sample_size=1,
                all_varchar=true
            )
            """
            col_result = con.execute(col_query)
            column_names = [desc[0] for desc in col_result.description]
            logger.info(f"Found {len(column_names)} columns")
            logger.debug(f"Columns: {', '.join(column_names[:10])}{'...' if len(column_names) > 10 else ''}")
            
            memory_after_cols = get_memory_usage()
            logger.debug(f"Memory after column detection: RSS={memory_after_cols['rss_mb']:.1f}MB (+{memory_after_cols['rss_mb'] - initial_memory['rss_mb']:.1f}MB)")
            
            logger.info("Step 2/3: Building type conversion logic...")
            select_parts = []
            type_counts = {'integer': 0, 'numeric': 0, 'boolean': 0, 'timestamp': 0, 'varchar': 0}
            
            for col_name in column_names:
                col_lower = col_name.lower()
                
                if col_lower in ['id'] or col_lower.endswith('_id'):
                    select_parts.append(f'try_cast("{col_name}" AS INTEGER) AS "{col_name}"')
                    type_counts['integer'] += 1
                elif col_lower in ['score', 'age', 'price', 'amount', 'value'] or any(word in col_lower for word in ['score', 'age', 'price', 'amount', 'value', 'count', 'num']):
                    select_parts.append(f'CASE WHEN try_cast("{col_name}" AS INTEGER) IS NOT NULL THEN try_cast("{col_name}" AS INTEGER) ELSE try_cast("{col_name}" AS DOUBLE) END AS "{col_name}"')
                    type_counts['numeric'] += 1
                elif col_lower in ['active', 'enabled', 'disabled', 'valid'] or any(word in col_lower for word in ['active', 'enabled', 'is_', 'has_']):
                    select_parts.append(f'try_cast("{col_name}" AS BOOLEAN) AS "{col_name}"')
                    type_counts['boolean'] += 1
                elif col_lower.endswith('_date') or col_lower.endswith('_time') or col_lower in ['date', 'time', 'created', 'updated']:
                    select_parts.append(f'try_cast("{col_name}" AS TIMESTAMP) AS "{col_name}"')
                    type_counts['timestamp'] += 1
                else:
                    select_parts.append(f'"{col_name}"')
                    type_counts['varchar'] += 1
            
            logger.info(f"Type mapping: INT={type_counts['integer']}, NUM={type_counts['numeric']}, BOOL={type_counts['boolean']}, TS={type_counts['timestamp']}, STR={type_counts['varchar']}")
            
            select_clause = ", ".join(select_parts)
            
            logger.info("Step 3/3: Converting and writing to Parquet...")
            logger.info("This may take several minutes for large files...")
            
            conversion_start = time.time()
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
            conversion_time = time.time() - conversion_start
            
            memory_after_conversion = get_memory_usage()
            logger.debug(f"Memory after conversion: RSS={memory_after_conversion['rss_mb']:.1f}MB (+{memory_after_conversion['rss_mb'] - initial_memory['rss_mb']:.1f}MB)")
            
            output_size_mb = get_file_size_mb(parquet_path)
            compression_ratio = (file_size_mb / output_size_mb) if output_size_mb > 0 else 0
            
            logger.info(f"✓ Conversion completed in {conversion_time:.1f}s")
            logger.info(f"✓ Output: {parquet_path}")
            logger.info(f"✓ Size: {file_size_mb:.1f}MB → {output_size_mb:.1f}MB (compression: {compression_ratio:.1f}x)")
            
            try:
                logger.debug("Getting row count...")
                stats_query = f"""
                SELECT COUNT(*) as total_rows
                FROM read_csv_auto('{csv_path}', ignore_errors=true, sample_size=-1, all_varchar=true)
                """
                stats = con.execute(stats_query).fetchone()
                logger.info(f"✓ Total rows: {stats[0]:,}")
            except Exception as e:
                logger.warning(f"Could not get row count: {e}")
            
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"✗ Error processing {csv_path} after {elapsed:.1f}s: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        
        try:
            error_memory = get_memory_usage()
            logger.error(f"Memory at error: RSS={error_memory['rss_mb']:.1f}MB, %={error_memory['percent']:.1f}%")
        except:
            pass
            
        return False
    
    total_time = time.time() - start_time
    final_memory = get_memory_usage()
    logger.info(f"✓ File completed in {total_time:.1f}s")
    logger.debug(f"Final memory usage: RSS={final_memory['rss_mb']:.1f}MB, %={final_memory['percent']:.1f}%")
    
    return True

def main():
    logger = setup_logging()
    
    try:
        logger.info("=" * 60)
        logger.info("CSV to Parquet Converter Started")
        logger.info("=" * 60)
        
        log_system_info(logger)
        
        Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory: {OUTPUT_DIR}")
        
        input_path = Path(INPUT_DIR)
        if not input_path.exists():
            logger.error(f"Input directory {INPUT_DIR} does not exist!")
            return 1
        
        logger.info(f"Input directory: {INPUT_DIR}")
        
        logger.info("Scanning for CSV files...")
        csv_files = list(input_path.glob("*.csv"))
        
        if not csv_files:
            logger.error(f"No CSV files found in {INPUT_DIR}")
            return 1
        
        csv_files_with_size = [(f, get_file_size_mb(f)) for f in csv_files]
        csv_files_with_size.sort(key=lambda x: x[1])
        
        total_size_mb = sum(size for _, size in csv_files_with_size)
        logger.info(f"Found {len(csv_files)} CSV files to process")
        logger.info(f"Total size: {total_size_mb:.1f} MB")
        
        for i, (csv_file, size_mb) in enumerate(csv_files_with_size, 1):
            logger.info(f"  {i:2d}. {csv_file.name} ({size_mb:.1f} MB)")
        
        logger.info("-" * 60)
        
        successful = 0
        failed = 0
        total_start_time = time.time()
        
        for i, (csv_file, size_mb) in enumerate(csv_files_with_size, 1):
            parquet_name = csv_file.stem + ".parquet"
            parquet_path = Path(OUTPUT_DIR) / parquet_name
            
            if parquet_path.exists():
                logger.warning(f"[{i}/{len(csv_files)}] Output file already exists: {parquet_path}")
                logger.info("Skipping (delete the output file to reprocess)")
                continue
            
            logger.info(f"[{i}/{len(csv_files)}] Starting file {i} of {len(csv_files)}")
            
            if clean_and_convert(str(csv_file), str(parquet_path), logger, i, len(csv_files)):
                successful += 1
                logger.info(f"[{i}/{len(csv_files)}] ✓ SUCCESS")
            else:
                failed += 1
                logger.error(f"[{i}/{len(csv_files)}] ✗ FAILED")
            
            progress = (i / len(csv_files)) * 100
            elapsed = time.time() - total_start_time
            logger.info(f"Progress: {progress:.1f}% ({i}/{len(csv_files)}) - Elapsed: {elapsed:.1f}s")
            logger.info("-" * 40)
        
        total_time = time.time() - total_start_time
        logger.info("=" * 60)
        logger.info("PROCESSING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
        logger.info(f"Successfully converted: {successful} files")
        if failed > 0:
            logger.error(f"Failed to convert: {failed} files")
        else:
            logger.info("All files processed successfully!")
        
        final_memory = get_memory_usage()
        logger.info(f"Final memory usage: {final_memory['rss_mb']:.1f}MB ({final_memory['percent']:.1f}%)")
        
        return 0 if failed == 0 else 1
        
    except KeyboardInterrupt:
        logger.warning("Process interrupted by user (Ctrl+C)")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
