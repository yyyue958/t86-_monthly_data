import streamlit as st
import pandas as pd
import io

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

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Duplicate Removal**")
            duplicate_column = st.selectbox(
                "Column for duplicate removal",
                options=df.columns,
                index=0,
                help="Select the column to remove duplicates from (e.g., MAWB)"
            )
            weight_column = st.selectbox(
                "Weight column",
                options=df.columns,
                index=next((i for i, col in enumerate(df.columns) if 'weight' in col.lower() or 'wt' in col.lower()),
                           0),
                help="Column containing weight data. Non-blank values will be prioritized."
            )

        with col2:
            st.write("**Filtering**")
            filter_column = st.selectbox(
                "Column to filter",
                options=df.columns,
                index=0,
                help="Select column to filter values from"
            )
            filter_value = st.text_input(
                "Value to exclude",
                value="ac one",
                help="Case-insensitive filter. Rows containing this text will be removed."
            )

        # Select columns to keep
        st.write("**📁 Select columns to keep in output**")
        default_cols = [col for col in df.columns if col in [duplicate_column, weight_column, filter_column]]
        columns_to_keep = st.multiselect(
            "Choose columns",
            options=df.columns,
            default=default_cols if default_cols else df.columns.tolist()[:4]
        )

        if st.button("🚀 Process Data", type="primary"):
            with st.spinner("Processing your data..."):
                # Process data - prioritize rows with weight data
                df['has_weight'] = df[weight_column].notna()
                df_sorted = df.sort_values(by=[duplicate_column, 'has_weight'], ascending=[True, False])
                df_clean = df_sorted.drop_duplicates(subset=[duplicate_column], keep='first')

                # Filter out unwanted values
                if filter_value:
                    df_clean = df_clean[
                        ~df_clean[filter_column].astype(str).str.lower().str.contains(filter_value.lower(), na=False)]

                # Select only desired columns
                final_df = df_clean[columns_to_keep]

                st.success("✅ Processing complete!")

                # Show results
                st.subheader("📈 Processed Results")
                st.dataframe(final_df)

                st.metric("Original rows", df.shape[0])
                st.metric("Processed rows", final_df.shape[0])
                st.metric("Rows removed", df.shape[0] - final_df.shape[0])

                # Download button
                csv = final_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Processed CSV",
                    data=csv,
                    file_name="cleaned_data.csv",
                    mime="text/csv",
                    help="Click to download the processed data as CSV"
                )

    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}")
        st.info("Please make sure you uploaded a valid Excel or CSV file.")

else:
    st.info("👆 Please upload a CSV or Excel file to get started")

st.sidebar.markdown("---")
st.sidebar.info("""
**How to use:**
1. Upload your CSV/Excel file
2. Select processing options
3. Choose columns to keep
4. Click 'Process Data'
5. Download your cleaned file
""")