#------------------------------------------------------------------------
# Import Modules NEED WORK
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
    page_title="MTSS Map Maker | ISD District PSA", 
    page_icon=Icon,
    layout="centered", 
    initial_sidebar_state="auto",
    menu_items={
        'About': "### *This application was created by*  \n### LeVesseur Ph.D | MTSS.ai"
    }
)

# with open( "style.css" ) as css:
#     st.markdown( f'<style>{css.read()}</style>' , unsafe_allow_html= True)
#     # https://fonts.google.com/selection/embed

#------------------------------------------------------------------------
# Header
#------------------------------------------------------------------------

#Add the image with a specified width
# image_width = 300  # Set the desired width in pixels
# st.image('MTSS.ai_Logo.png', width=image_width)

st.title('MTSS:grey[.ai]')
st.header('Code Matchmaker:grey[ | Public School Academies]')

# Add the descriptive text
st.markdown("""
PSA names must be exact matches and are case-sensitive. If needed, use the 'Enter search string' option to enter partial names to locate a match.
""")

contact = st.sidebar.toggle('Handmade by  \n**LeVesseur** :grey[ PhD]  \n| :grey[MTSS.ai]')
if contact:
    st.sidebar.write('Inquiries: [info@mtss.ai](mailto:info@mtss.ai)  \nProfile: [levesseur.com](http://levesseur.com)  \nCheck out: [InkQA | Dynamic PDFs](http://www.inkqa.com)')  

#------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------

# Add the descriptive text
st.markdown("""
Your PSA data spreadsheet must include two columns: 'PSA' and 'PSA Code'. The PSA codes are used to match the location data to create a map.

If your spreadsheet lists PSAs in the 'PSA' column but does not include PSA codes, use the **PSA Code Matchmaker** to find the 'PSA Code'.
""")

# Path to the existing Excel file
file_path = "examples/PSA_Data.xlsx"

# Read the file and load it into a bytes object
with open(file_path, "rb") as file:
    file_data = file.read()

# Display download button with MIME type for Excel
st.download_button(
    label="Download an example PSA data spreadsheet",
    data=file_data,
    file_name='PSA_Data.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'  # MIME type for .xlsx files
)

# Load the MI_PSA_Codes file
@st.cache_data
def load_PSA_codes_file():
    return pd.read_csv("codes/MI_PSA_Codes.csv")

# Define the main function
def main():    
    # Upload user's file
    st.sidebar.header("Upload File")
    uploaded_file = st.sidebar.file_uploader("Upload your file", type=['xlsx', 'csv'])
    
    # Load the MI_PSA_Codes file
    df = load_PSA_codes_file()
    
    # Remove trailing spaces from the 'PSA' column
    df['PSA'] = df['PSA'].str.strip()
    
    # Search functionality
    st.sidebar.header("Search PSAs")
    search_string = st.sidebar.text_input("Enter search string")
    if search_string:
        matching_rows = df[df['PSA'].str.startswith(search_string)]
        # Convert 'PSA Code' values to strings without commas
        matching_rows['PSA Code'] = matching_rows['PSA Code'].astype(str)
        matching_rows_display = matching_rows[['PSA', 'PSA Code']]
        st.sidebar.subheader("Matching Rows:")
        st.sidebar.dataframe(matching_rows_display)

    if uploaded_file is not None:
        if uploaded_file.name.endswith('.csv'):
            df_nc = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.xlsx'):
            df_nc = pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file format. Please upload a CSV or XLSX file.")
            return  # Stop execution if file format is not supported
            
        # Remove trailing spaces from the 'PSA' column
        df_nc['PSA'] = df_nc['PSA'].str.strip()
        
        # Map PSA codes
        def map_PSA_codes(row):
            matching_row = df[df['PSA'] == row['PSA']]
            if not matching_row.empty:
                return matching_row.iloc[0]['PSA Code']
            else:
                return None

        # Add 'PSA Code' column
        df_nc['PSA Code'] = df_nc.apply(map_PSA_codes, axis=1)

        # Display matched rows
        matched_rows = df_nc[~df_nc['PSA Code'].isnull()] 
        matched_rows['PSA Code'] = matched_rows['PSA Code'].astype(str)
        st.text("Matched Rows:")
        st.dataframe(matched_rows)
        st.write("Total number of matched rows:", len(matched_rows))

        # Display unmatched rows
        unmatched_rows = df_nc[df_nc['PSA Code'].isnull()]
        unmatched_rows['PSA Code'] = unmatched_rows['PSA Code'].astype(str)
        st.text("Unmatched Rows:")
        st.dataframe(unmatched_rows)
        st.write("Total number of unmatched rows:", len(unmatched_rows))
        
        st.success('Processing complete!')
        
        st.divider()
        
        # Download updated file
        # st.subheader("Download Updated File")
        # st.download_button("Download", data=df_nc.to_csv(), file_name='PSA_updated_file.csv', type="primary")

        # Download updated file
        st.subheader("Download Updated File")
        df_nc_selected_columns = df_nc[['PSA', 'PSA Code']]  # Select only the desired columns
        st.download_button("Download", data=df_nc_selected_columns.to_csv(index=False), file_name='PSA_updated_file.csv', type="primary")


if __name__ == "__main__":
    main()
