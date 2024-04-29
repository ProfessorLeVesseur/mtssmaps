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
st.header('Code Matchmaker:grey[ | Intermediate School Districts]')

contact = st.sidebar.toggle('Handmade by  \n**LeVesseur** :grey[ PhD]  \n| :grey[MTSS.ai]')
if contact:
    st.sidebar.write('Inquiries: [info@mtss.ai](mailto:info@mtss.ai)  \nProfile: [levesseur.com](http://levesseur.com)  \nCheck out: [InkQA | Dynamic PDFs](http://www.inkqa.com)')  

#------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------

# Load the MI_ISD_Codes file
@st.cache_data
def load_ISD_codes_file():
    # return pd.read_csv("codes/MI_ISD_Codes.csv")
    return pd.read_csv("/Users/cheynelevesseur/Desktop/Python_Code/Mapping_Projects/ISD_Map/MI_ISD_Codes.csv")

# Define the main function
def main():    
    # Upload user's file
    st.sidebar.header("Upload File")
    uploaded_file = st.sidebar.file_uploader("Upload your file", type=['xlsx', 'csv'])
    
    # Load the MI_ISD_Codes file
    df = load_ISD_codes_file()
    
    # Remove trailing spaces from the 'ISD' column
    df['ISD'] = df['ISD'].str.strip()
    
    # Search functionality
    st.sidebar.header("Search ISDs")
    search_string = st.sidebar.text_input("Enter search string")
    if search_string:
        matching_rows = df[df['ISD'].str.startswith(search_string)]
        # Convert 'ISD Code' values to strings without commas
        matching_rows['ISD Code'] = matching_rows['ISD Code'].astype(str)
        matching_rows_display = matching_rows[['ISD', 'ISD Code']]
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
            
        # Remove trailing spaces from the 'ISD' column
        df_nc['ISD'] = df_nc['ISD'].str.strip()
        
        # Map ISD codes
        def map_ISD_codes(row):
            matching_row = df[df['ISD'] == row['ISD']]
            if not matching_row.empty:
                return matching_row.iloc[0]['ISD Code']
            else:
                return None

        # Add 'ISD Code' column
        df_nc['ISD Code'] = df_nc.apply(map_ISD_codes, axis=1)

        # Display matched rows
        matched_rows = df_nc[~df_nc['ISD Code'].isnull()] 
        matched_rows['ISD Code'] = matched_rows['ISD Code'].astype(str)
        st.text("Matched Rows:")
        st.dataframe(matched_rows)
        st.write("Total number of matched rows:", len(matched_rows))

        # Display unmatched rows
        unmatched_rows = df_nc[df_nc['ISD Code'].isnull()]
        unmatched_rows['ISD Code'] = unmatched_rows['ISD Code'].astype(str)
        st.text("Unmatched Rows:")
        st.dataframe(unmatched_rows)
        st.write("Total number of unmatched rows:", len(unmatched_rows))
        
        st.success('Processing complete!')
        
        st.divider()
        
        # Download updated file
        st.subheader("Download Updated File")
        st.download_button("Download", data=df_nc.to_csv(), file_name='ISD_updated_file.csv', type="primary")

if __name__ == "__main__":
    main()
