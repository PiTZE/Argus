import duckdb
import os
import sys
import time
import logging
import psutil
from pathlib import Path
from datetime import datetime
from config import load_config, configure_duckdb, get_directories, get_csv_options

# ============================================================================
# CONFIGURATION AND CONSTANTS
# ============================================================================

RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

# ============================================================================
# LOGGING FUNCTIONS
# ============================================================================

def log_info(message):
    print(f"{BLUE}[INFO]{NC} {message}")

def log_success(message):
    print(f"{GREEN}[SUCCESS]{NC} {message}")

def log_warning(message):
    print(f"{YELLOW}[WARNING]{NC} {message}")

def log_error(message):
    print(f"{RED}[ERROR]{NC} {message}")

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def setup_logging(config):
    dirs = get_directories(config)
    log_dir = Path(dirs['log_dir'])
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"csv_to_parq_{timestamp}.log"
    
    logging_config = config.get('logging', {})
    date_format = logging_config.get('date_format', '%Y-%m-%d %H:%M:%S')
    
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt=date_format
    )
    
    file_handler = logging.FileHandler(log_file)
    file_level = logging_config.get('file_level', 'DEBUG')
    file_handler.setLevel(getattr(logging, file_level))
    file_handler.setFormatter(formatter)
    
    logger = logging.getLogger('csv_to_parq')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    
    return logger, log_file

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
        info_msg = f"System Memory - Total: {memory.total / (1024**3):.1f}GB, Available: {memory.available / (1024**3):.1f}GB, Used: {memory.percent}%"
        log_info(info_msg)
        logger.info(info_msg)
        
        cpu_msg = f"CPU Count: {psutil.cpu_count()}"
        log_info(cpu_msg)
        logger.info(cpu_msg)
    except Exception as e:
        warning_msg = f"Could not get system info: {e}"
        log_warning(warning_msg)
        logger.warning(warning_msg)

# ============================================================================
# DATA PROCESSING
# ============================================================================

def clean_and_convert(csv_path, parquet_path, logger, file_index, total_files, config):
    start_time = time.time()
    
    try:
        file_size_mb = get_file_size_mb(csv_path)
        
        process_msg = f"[{file_index}/{total_files}] Processing: {csv_path}"
        log_info(process_msg)
        logger.info(process_msg)
        
        size_msg = f"File size: {file_size_mb:.1f} MB"
        log_info(size_msg)
        logger.info(size_msg)
        
        with duckdb.connect() as con:
            configure_duckdb(con, config)
            
            step1_msg = "Step 1/3: Analyzing column structure..."
            log_info(step1_msg)
            logger.info(step1_msg)
            
            csv_options = get_csv_options(config)
            col_query = f"""
            SELECT * FROM read_csv_auto('{csv_path}',
                sample_size=1,
                all_varchar=true,
                {csv_options}
            )
            """
            col_result = con.execute(col_query)
            column_names = [desc[0] for desc in col_result.description]
            
            cols_msg = f"Found {len(column_names)} columns"
            log_info(cols_msg)
            logger.info(cols_msg)
            
            step2_msg = "Step 2/3: Building type conversion logic..."
            log_info(step2_msg)
            logger.info(step2_msg)
            
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
            
            type_msg = f"Type mapping: INT={type_counts['integer']}, NUM={type_counts['numeric']}, BOOL={type_counts['boolean']}, TS={type_counts['timestamp']}, STR={type_counts['varchar']}"
            log_info(type_msg)
            logger.info(type_msg)
            
            select_clause = ", ".join(select_parts)
            
            step3_msg = "Step 3/3: Converting and writing to Parquet..."
            log_info(step3_msg)
            logger.info(step3_msg)
            
            wait_msg = "This may take several minutes for large files..."
            log_info(wait_msg)
            logger.info(wait_msg)
            
            conversion_start = time.time()
            clean_query = f"""
            COPY (
                SELECT {select_clause}
                FROM read_csv_auto('{csv_path}',
                    {csv_options}
                )
            ) TO '{parquet_path}' (FORMAT PARQUET, COMPRESSION GZIP)
            """
            
            con.execute(clean_query)
            conversion_time = time.time() - conversion_start
            
            output_size_mb = get_file_size_mb(parquet_path)
            compression_ratio = (file_size_mb / output_size_mb) if output_size_mb > 0 else 0
            
            complete_msg = f"✓ Conversion completed in {conversion_time:.1f}s"
            log_success(complete_msg)
            logger.info(complete_msg)
            
            output_msg = f"✓ Output: {parquet_path}"
            log_success(output_msg)
            logger.info(output_msg)
            
            size_result_msg = f"✓ Size: {file_size_mb:.1f}MB → {output_size_mb:.1f}MB (compression: {compression_ratio:.1f}x)"
            log_success(size_result_msg)
            logger.info(size_result_msg)
            
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"✗ Error processing {csv_path} after {elapsed:.1f}s: {e}"
        log_error(error_msg)
        logger.error(error_msg)
        
        error_type_msg = f"Error type: {type(e).__name__}"
        log_error(error_type_msg)
        logger.error(error_type_msg)
        return False
    
    total_time = time.time() - start_time
    complete_file_msg = f"✓ File completed in {total_time:.1f}s"
    log_success(complete_file_msg)
    logger.info(complete_file_msg)
    
    import gc
    gc.collect()
    
    return True

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    config = load_config()
    logger, log_file = setup_logging(config)
    
    try:
        print("=" * 60)
        log_info("CSV to Parquet Converter Started")
        print("=" * 60)
        
        logger.info("=" * 60)
        logger.info("CSV to Parquet Converter Started")
        logger.info("=" * 60)
        
        log_system_info(logger)
        
        dirs = get_directories(config)
        input_dir = dirs['input_dir']
        output_dir = dirs['output_dir']
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        output_msg = f"Output directory: {output_dir}"
        log_info(output_msg)
        logger.info(output_msg)
        
        input_path = Path(input_dir)
        if not input_path.exists():
            error_msg = f"Input directory {input_dir} does not exist!"
            log_error(error_msg)
            logger.error(error_msg)
            return 1
        
        input_msg = f"Input directory: {input_dir}"
        log_info(input_msg)
        logger.info(input_msg)
        
        scan_msg = "Scanning for CSV files..."
        log_info(scan_msg)
        logger.info(scan_msg)
        
        csv_files = list(input_path.glob("*.csv"))
        
        if not csv_files:
            no_files_msg = f"No CSV files found in {input_dir}"
            log_error(no_files_msg)
            logger.error(no_files_msg)
            return 1
        
        processing_config = config.get('processing', {})
        csv_files_with_size = [(f, get_file_size_mb(f)) for f in csv_files]
        
        if processing_config.get('sort_files_by_size', True):
            csv_files_with_size.sort(key=lambda x: x[1])
        
        total_size_mb = sum(size for _, size in csv_files_with_size)
        
        found_msg = f"Found {len(csv_files)} CSV files to process"
        log_info(found_msg)
        logger.info(found_msg)
        
        total_size_msg = f"Total size: {total_size_mb:.1f} MB"
        log_info(total_size_msg)
        logger.info(total_size_msg)
        
        for i, (csv_file, size_mb) in enumerate(csv_files_with_size, 1):
            file_list_msg = f"  {i:2d}. {csv_file.name} ({size_mb:.1f} MB)"
            log_info(file_list_msg)
            logger.info(file_list_msg)
        
        print("-" * 60)
        logger.info("-" * 60)
        
        successful = 0
        failed = 0
        total_start_time = time.time()
        
        for i, (csv_file, size_mb) in enumerate(csv_files_with_size, 1):
            parquet_name = csv_file.stem + ".parquet"
            parquet_path = Path(output_dir) / parquet_name
            
            if parquet_path.exists():
                exists_msg = f"[{i}/{len(csv_files)}] Output file already exists: {parquet_path}"
                log_warning(exists_msg)
                logger.warning(exists_msg)
                
                skip_msg = "Skipping (delete the output file to reprocess)"
                log_info(skip_msg)
                logger.info(skip_msg)
                continue
            
            start_msg = f"[{i}/{len(csv_files)}] Starting file {i} of {len(csv_files)}"
            log_info(start_msg)
            logger.info(start_msg)
            
            if clean_and_convert(str(csv_file), str(parquet_path), logger, i, len(csv_files), config):
                successful += 1
                success_msg = f"[{i}/{len(csv_files)}] ✓ SUCCESS"
                log_success(success_msg)
                logger.info(success_msg)
            else:
                failed += 1
                fail_msg = f"[{i}/{len(csv_files)}] ✗ FAILED"
                log_error(fail_msg)
                logger.error(fail_msg)
            
            progress = (i / len(csv_files)) * 100
            elapsed = time.time() - total_start_time
            progress_msg = f"Progress: {progress:.1f}% ({i}/{len(csv_files)}) - Elapsed: {elapsed:.1f}s"
            log_info(progress_msg)
            logger.info(progress_msg)
            
            print("-" * 40)
            logger.info("-" * 40)
        
        total_time = time.time() - total_start_time
        
        print("=" * 60)
        log_success("PROCESSING COMPLETE")
        print("=" * 60)
        
        logger.info("=" * 60)
        logger.info("PROCESSING COMPLETE")
        logger.info("=" * 60)
        
        time_msg = f"Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)"
        log_info(time_msg)
        logger.info(time_msg)
        
        success_count_msg = f"Successfully converted: {successful} files"
        log_success(success_count_msg)
        logger.info(success_count_msg)
        
        if failed > 0:
            fail_count_msg = f"Failed to convert: {failed} files"
            log_error(fail_count_msg)
            logger.error(fail_count_msg)
        else:
            all_success_msg = "All files processed successfully!"
            log_success(all_success_msg)
            logger.info(all_success_msg)
        
        log_file_msg = f"Detailed log saved to: {log_file}"
        log_info(log_file_msg)
        logger.info(log_file_msg)
        
        return 0 if failed == 0 else 1
        
    except KeyboardInterrupt:
        interrupt_msg = "Process interrupted by user (Ctrl+C)"
        log_warning(interrupt_msg)
        logger.warning(interrupt_msg)
        return 130
    except Exception as e:
        error_msg = f"Unexpected error in main: {e}"
        log_error(error_msg)
        logger.error(error_msg)
        
        error_type_msg = f"Error type: {type(e).__name__}"
        log_error(error_type_msg)
        logger.error(error_type_msg)
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
