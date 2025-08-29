import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Excel Data Cleaner", page_icon="📊", layout="wide")

st.title("📊 Excel Data Cleaner")
st.write("Upload your Excel/CSV file to remove duplicates and filter data")

# File upload
uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=['csv', 'xlsx'])

if uploaded_file is not None:
    try:
        # Read file
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success(f"✅ File uploaded successfully! ({df.shape[0]} rows, {df.shape[1]} columns)")
        
        # Show original data preview
        with st.expander("📋 View Original Data (First 10 rows)"):
            st.dataframe(df.head(10))
        
        # Processing section
        st.subheader("⚙️ Processing Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**Duplicate Removal**")
            duplicate_column = st.selectbox(
                "Column for duplicate removal", 
                options=df.columns, 
                index=0
            )
            weight_column = st.selectbox(
                "Weight column", 
                options=df.columns, 
                index=0
            )
        
        with col2:
            st.write("**Text Filtering**")
            filter_column = st.selectbox(
                "Column to filter", 
                options=df.columns, 
                index=0
            )
            filter_value = st.text_input("Value to exclude", value="ac one")
        
        with col3:
            st.write("**📅 Date Filter**")
            # Find date columns automatically
            date_columns = []
            for col in df.columns:
                try:
                    # Try to convert sample data to datetime to identify date columns
                    sample_data = df[col].dropna().head(5)
                    if not sample_data.empty:
                        pd.to_datetime(sample_data, errors='coerce')
                        date_columns.append(col)
                except:
                    continue
            
            date_column = st.selectbox(
                "Date column to filter",
                options=date_columns if date_columns else df.columns,
                index=0,
                help="Select a column containing dates"
            )
            
            # Date filter type selection
            date_filter_type = st.radio(
                "Date filter type:",
                ["Range Filter", "Single Date Filter"],
                horizontal=True
            )
            
            try:
                # Convert to datetime for min/max calculation
                date_series = pd.to_datetime(df[date_column], errors='coerce')
                min_date = date_series.min()
                max_date = date_series.max()
                
                if pd.notna(min_date) and pd.notna(max_date):
                    if date_filter_type == "Range Filter":
                        st.write("**Select date range:**")
                        start_date = st.date_input(
                            "Start date",
                            value=min_date,
                            min_value=min_date,
                            max_value=max_date,
                            key="start_date"
                        )
                        end_date = st.date_input(
                            "End date",
                            value=max_date,
                            min_value=min_date,
                            max_value=max_date,
                            key="end_date"
                        )
                        single_date = None
                    else:  # Single Date Filter
                        st.write("**Select specific date:**")
                        single_date = st.date_input(
                            "Select date",
                            value=min_date,
                            min_value=min_date,
                            max_value=max_date,
                            key="single_date"
                        )
                        start_date = end_date = None
                else:
                    st.warning("No valid dates found in selected column")
                    start_date = end_date = single_date = None
            except:
                st.warning("Could not parse dates from selected column")
                start_date = end_date = single_date = None
        
        # Select columns to keep
        st.write("**📁 Select columns to keep in output**")
        columns_to_keep = st.multiselect(
            "Choose columns", 
            options=df.columns, 
            default=df.columns.tolist()[:4]
        )
        
        if st.button("🚀 Process Data", type="primary"):
            with st.spinner("Processing your data..."):
                # Process data
                df['has_weight'] = df[weight_column].notna()
                df_sorted = df.sort_values(by=[duplicate_column, 'has_weight'], ascending=[True, False])
                df_clean = df_sorted.drop_duplicates(subset=[duplicate_column], keep='first')
                
                # Filter out unwanted text values
                if filter_value:
                    df_clean = df_clean[~df_clean[filter_column].astype(str).str.lower().str.contains(filter_value.lower(), na=False)]
                
                # Apply date filter
                date_filter_applied = False
                if date_column:
                    try:
                        # Convert date column to datetime
                        df_clean['temp_date'] = pd.to_datetime(df_clean[date_column], errors='coerce')
                        
                        if date_filter_type == "Range Filter" and start_date and end_date:
                            # Convert user input dates to datetime
                            start_dt = pd.to_datetime(start_date)
                            end_dt = pd.to_datetime(end_date)
                            
                            # Filter by date range
                            df_clean = df_clean[
                                (df_clean['temp_date'] >= start_dt) & 
                                (df_clean['temp_date'] <= end_dt)
                            ]
                            date_filter_applied = True
                            st.info(f"📅 Filtered by date range: {start_date} to {end_date}")
                            
                        elif date_filter_type == "Single Date Filter" and single_date:
                            # Convert user input date to datetime
                            single_dt = pd.to_datetime(single_date)
                            
                            # Filter by single date
                            df_clean = df_clean[
                                df_clean['temp_date'].dt.date == single_dt.date()
                            ]
                            date_filter_applied = True
                            st.info(f"📅 Filtered by specific date: {single_date}")
                        
                        # Remove temporary column
                        df_clean = df_clean.drop(columns=['temp_date'])
                        
                    except Exception as e:
                        st.warning(f"Could not apply date filter: {str(e)}")
                
                # Select only desired columns
                final_df = df_clean[columns_to_keep]
                
                st.success("✅ Processing complete!")
                
                # Show metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Original rows", df.shape[0])
                with col2:
                    st.metric("Processed rows", final_df.shape[0])
                with col3:
                    st.metric("Rows removed", df.shape[0] - final_df.shape[0])
                
                if date_filter_applied:
                    st.info(f"📊 Showing {final_df.shape[0]} rows after date filtering")
                
                st.dataframe(final_df)
                
                # Download button
                csv = final_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Processed CSV",
                    data=csv,
                    file_name="cleaned_data.csv",
                    mime="text/csv"
                )
                
    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}")
        st.info("Please check your file format and try again.")

else:
    st.info("👆 Please upload a CSV or Excel file to get started")

# Add instructions in sidebar
st.sidebar.markdown("---")
st.sidebar.info("""
**How to use:**
1. 📁 Upload your CSV/Excel file
2. ⚙️ Select processing options
3. 📅 Choose date filter type:
   - **Range Filter**: Select start and end dates
   - **Single Date Filter**: Select one specific date
4. 📁 Select columns to keep
5. 🚀 Click 'Process Data'
6. 📥 Download your cleaned file
""")

st.sidebar.markdown("---")
st.sidebar.success("**Date Filter Options:**\n- 📅 Range: Filter between two dates\n- 📆 Single: Filter for one specific date")
