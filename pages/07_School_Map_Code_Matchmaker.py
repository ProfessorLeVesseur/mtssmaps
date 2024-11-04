#------------------------------------------------------------------------
# Import Modules
#------------------------------------------------------------------------

import pandas as pd
import streamlit as st
from PIL import Image

#------------------------------------------------------------------------
# Configurations
#------------------------------------------------------------------------

# Streamlit page setup
Icon = Image.open("images/MTSS.ai_Icon.png")
st.set_page_config(
    page_title="MTSS Map Maker | ISD District School", 
    page_icon=Icon,
    layout="centered", 
    initial_sidebar_state="auto",
    menu_items={
        'About': "### *This application was created by*  \n### LeVesseur Ph.D | MTSS.ai"
    }
)

#------------------------------------------------------------------------
# Header
#------------------------------------------------------------------------

st.title('MTSS:grey[.ai]')
st.header('Code Matchmaker:grey[ | Schools]')

st.divider()

# Add the descriptive text
st.markdown("""
School names must be exact matches and are case-sensitive. If needed, use the 'Enter search string' option to enter partial names to locate a match.
""")

st.divider()

contact = st.sidebar.toggle('Handmade by  \n**LeVesseur** :grey[ PhD]  \n| :grey[MTSS.ai]')
if contact:
    st.sidebar.write('Inquiries: [info@mtss.ai](mailto:info@mtss.ai)  \nProfile: [levesseur.com](http://levesseur.com)  \nCheck out: [InkQA | Dynamic PDFs](http://www.inkqa.com)')  

#------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------

# Load the MI_School_Codes file
@st.cache_data
def load_school_codes_file():
    return pd.read_csv("codes/MI_School_Codes.csv")

# Define the main function
def main():
    # Load the MI_School_Codes file
    df = load_school_codes_file()

    # Remove trailing spaces from the 'School' column
    df['School'] = df['School'].str.strip()

    # Search functionality on the main page
    st.header("Search Schools")
    search_string = st.text_input("Enter search string")
    if search_string:
        matching_rows = df[df['School'].str.startswith(search_string)]
        # Convert 'School Code' values to strings without commas
        matching_rows['School Code'] = matching_rows['School Code'].astype(str)
        matching_rows_display = matching_rows[['School', 'School Code']]
        st.subheader("Matching Rows:")
        st.dataframe(matching_rows_display)

    # Main page header for file upload
    st.header("Upload Your File")
    uploaded_file = st.file_uploader("Upload your file", type=['xlsx', 'csv'])

    if uploaded_file is not None:
        if uploaded_file.name.endswith('.csv'):
            df_nc = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.xlsx'):
            df_nc = pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file format. Please upload a CSV or XLSX file.")
            return  # Stop execution if file format is not supported

        # Remove trailing spaces from the 'School' column
        df_nc['School'] = df_nc['School'].str.strip()

        # Map School codes
        def map_school_codes(row):
            matching_row = df[df['School'] == row['School']]
            if not matching_row.empty:
                return matching_row.iloc[0]['School Code']
            else:
                return None

        # Add 'School Code' column
        df_nc['School Code'] = df_nc.apply(map_school_codes, axis=1)

        # Display matched rows
        matched_rows = df_nc[~df_nc['School Code'].isnull()]
        matched_rows['School Code'] = matched_rows['School Code'].astype(str)
        st.text("Matched Rows:")
        st.dataframe(matched_rows)
        st.write("Total number of matched rows:", len(matched_rows))

        # Display unmatched rows
        unmatched_rows = df_nc[df_nc['School Code'].isnull()]
        unmatched_rows['School Code'] = unmatched_rows['School Code'].astype(str)
        st.text("Unmatched Rows:")
        st.dataframe(unmatched_rows)
        st.write("Total number of unmatched rows:", len(unmatched_rows))

        st.success('Processing complete!')

        st.divider()

        # Download updated file
        st.subheader("Download Updated File")
        df_nc_selected_columns = df_nc[['School', 'School Code']]  # Select only the desired columns
        st.download_button(
            label="Download",
            data=df_nc_selected_columns.to_csv(index=False),
            file_name='School_updated_file.csv',
            mime='text/csv'
        )

if __name__ == "__main__":
    main()
