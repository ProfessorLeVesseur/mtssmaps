import pandas as pd
import streamlit as st

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

#Add the image with a specified width
# image_width = 300  # Set the desired width in pixels
# st.image('MTSS.ai_Logo.png', width=image_width)

st.title('MTSS:grey[.ai]')
st.header(District Code Matchmaker:grey[ School Districts]')

contact = st.sidebar.toggle('Handmade by  \n**LeVesseur** :grey[ PhD]  \n| :grey[MTSS.ai]')
if contact:
    st.sidebar.write('Email: [info@mtss.ai](mailto:info@mtss.ai)  \nWebsite: [levesseur.com](http://levesseur.com)') 
    st.sidebar.write('Inquiries: [info@mtss.ai](mailto:info@mtss.ai)  \nCheck out: [InkQA | Dynamic PDFs](http://www.inkqa.com)') 


# Load the MI_District_Codes file
@st.cache_data
def load_district_codes_file():
    return pd.read_csv("codes/MI_District_Codes.csv")

# Define the main function
def main():    
    # Upload user's file
    st.sidebar.header("Upload File")
    uploaded_file = st.sidebar.file_uploader("Upload your file", type=['xlsx', 'csv'])
    
    # Load the MI_District_Codes file
    df = load_district_codes_file()
    
    # Remove trailing spaces from the 'District' column
    df['District'] = df['District'].str.strip()
    
    # Search functionality
    st.sidebar.header("Search Districts")
    search_string = st.sidebar.text_input("Enter search string")
    if search_string:
        matching_rows = df[df['District'].str.startswith(search_string)]
        # Convert 'District Code' values to strings without commas
        matching_rows['District Code'] = matching_rows['District Code'].astype(str)
        matching_rows_display = matching_rows[['District', 'District Code']]
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
            
        # Remove trailing spaces from the 'District' column
        df_nc['District'] = df_nc['District'].str.strip()
        
        # Map district codes
        def map_district_codes(row):
            matching_row = df[df['District'] == row['District']]
            if not matching_row.empty:
                return matching_row.iloc[0]['District Code']
            else:
                return None

        # Add 'District Code' column
        df_nc['District Code'] = df_nc.apply(map_district_codes, axis=1)

        # Display matched rows
        matched_rows = df_nc[~df_nc['District Code'].isnull()] 
        matched_rows['District Code'] = matched_rows['District Code'].astype(str)
        st.text("Matched Rows:")
        st.dataframe(matched_rows)
        st.write("Total number of matched rows:", len(matched_rows))

        # Display unmatched rows
        unmatched_rows = df_nc[df_nc['District Code'].isnull()]
        unmatched_rows['District Code'] = unmatched_rows['District Code'].astype(str)
        st.text("Unmatched Rows:")
        st.dataframe(unmatched_rows)
        st.write("Total number of unmatched rows:", len(unmatched_rows))
        
        st.success('Processing complete!')
        
        st.divider()
        
        # Download updated file
        st.subheader("Download Updated File")
        st.download_button("Download", data=df_nc.to_csv(), file_name='updated_file.csv', type="primary")

if __name__ == "__main__":
    main()