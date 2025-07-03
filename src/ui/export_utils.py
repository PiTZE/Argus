"""Export utilities for search results."""

import streamlit as st
import pandas as pd
import io
import json
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

class ExportManager:
    """Manages export functionality for search results."""
    
    def __init__(self):
        pass
    
    def render_export_options(self, df: pd.DataFrame, filename_prefix: str):
        """Render export options for a dataframe."""
        if df.empty:
            return
        
        st.subheader("📥 Export Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # CSV Export
            csv_data = self._convert_to_csv(df)
            if csv_data:
                st.download_button(
                    label="📄 Download CSV",
                    data=csv_data,
                    file_name=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    help=f"Export {len(df):,} rows as CSV"
                )
        
        with col2:
            # Excel Export
            excel_data = self._convert_to_excel(df)
            if excel_data:
                st.download_button(
                    label="📊 Download Excel",
                    data=excel_data,
                    file_name=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help=f"Export {len(df):,} rows as Excel"
                )
        
        with col3:
            # JSON Export
            json_data = self._convert_to_json(df)
            if json_data:
                st.download_button(
                    label="🔗 Download JSON",
                    data=json_data,
                    file_name=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    help=f"Export {len(df):,} rows as JSON"
                )
        
        # Export summary
        st.caption(f"💾 Ready to export {len(df):,} rows with {len(df.columns)} columns")
    
    def _convert_to_csv(self, df: pd.DataFrame) -> Optional[str]:
        """Convert dataframe to CSV string."""
        try:
            return df.to_csv(index=False)
        except Exception as e:
            logger.error(f"Error converting to CSV: {e}")
            st.error(f"❌ CSV export failed: {e}")
            return None
    
    def _convert_to_excel(self, df: pd.DataFrame) -> Optional[bytes]:
        """Convert dataframe to Excel bytes."""
        try:
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Search Results')
                
                # Get the workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['Search Results']
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error converting to Excel: {e}")
            st.error(f"❌ Excel export failed: {e}")
            return None
    
    def _convert_to_json(self, df: pd.DataFrame) -> Optional[str]:
        """Convert dataframe to JSON string."""
        try:
            # Convert to JSON with proper formatting
            json_data = df.to_json(orient='records', indent=2, date_format='iso')
            
            # Add metadata
            metadata = {
                'export_timestamp': datetime.now().isoformat(),
                'total_records': len(df),
                'columns': list(df.columns),
                'data': json.loads(json_data)
            }
            
            return json.dumps(metadata, indent=2)
            
        except Exception as e:
            logger.error(f"Error converting to JSON: {e}")
            st.error(f"❌ JSON export failed: {e}")
            return None
    
    def render_bulk_export_options(self, results_dict: dict, search_term: str):
        """Render bulk export options for multiple file results."""
        if not results_dict:
            return
        
        st.subheader("📦 Bulk Export Options")
        
        # Combine all results
        all_dataframes = []
        for file_path, result_data in results_dict.items():
            if result_data.get('data') is not None:
                df = result_data['data'].copy()
                df['source_file'] = result_data['file_name']
                all_dataframes.append(df)
        
        if not all_dataframes:
            st.info("No results to export")
            return
        
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        
        # Export options
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Results", f"{len(combined_df):,}")
            st.metric("Source Files", len(all_dataframes))
        
        with col2:
            # Render export buttons
            self.render_export_options(combined_df, f"bulk_search_{search_term.replace(' ', '_')}")
        
        # Preview of combined data
        with st.expander("👀 Preview Combined Data"):
            st.dataframe(combined_df.head(100), use_container_width=True)
            if len(combined_df) > 100:
                st.caption(f"Showing first 100 rows of {len(combined_df):,} total results")

# Global export manager instance
export_manager = ExportManager()