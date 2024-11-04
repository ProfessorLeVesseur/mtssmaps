#------------------------------------------------------------------------
# Import Modules
#------------------------------------------------------------------------

import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from pathlib import Path
import tempfile
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
st.header('Map Maker:grey[ | Schools]')

contact = st.sidebar.toggle('Handmade by  \n**LeVesseur** :grey[ PhD]  \n| :grey[MTSS.ai]')
if contact:
    st.sidebar.write('Inquiries: [info@mtss.ai](mailto:info@mtss.ai)  \nProfile: [levesseur.com](http://levesseur.com)  \nCheck out: [InkQA | Dynamic PDFs](http://www.inkqa.com)') 
    
#------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------

st.divider()

# Add the descriptive text
st.markdown("""
Your School data spreadsheet must include two columns: 'School' and 'School Code'. The School codes are used to match the location data to create a map.

If your spreadsheet lists Schools in the 'School' column but does not include School codes, use the **School Code Matchmaker** to find the 'School Code'.
""")

# Path to the existing Excel file
file_path = "examples/School_Data.xlsx"

# Read the file and load it into a bytes object
with open(file_path, "rb") as file:
    file_data = file.read()

# Display download button with MIME type for Excel
st.download_button(
    label="Download an example School data spreadsheet",
    data=file_data,
    file_name='School_Data.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'  # MIME type for .xlsx files
)

st.divider()

# Excel/CSV file upload
uploaded_file = st.file_uploader("Upload your District data XLSX | CSV", type=['xlsx', 'csv'])
if uploaded_file is not None:
    with st.spinner("Processing data and generating map"):
        # Load data from the uploaded file
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file format. Please upload a CSV or XLSX file.")
            st.stop()  # Stop execution if file format is not supported

        # Check if required columns are present
        required_columns = ['School', 'School Code']
        if not all(col in df.columns for col in required_columns):
            st.warning("The uploaded file must contain 'School' and 'School Code' columns.")
            st.stop()  # Stop execution if required columns are not present

        # Specify dtype as str for 'School Code' to ensure it reads in as string
        df['School Code'] = df['School Code'].astype(str)

        # Add column "Count" and set all rows to 1
        df['Count'] = 1

        # If the 'School Code' column contains integers without leading zeros, add them
        df['School Code'] = df['School Code'].apply(lambda x: str(x).zfill(5))

        # Load GeoJSON file from the root directory
        geojson_filename = "geojson/School_geojson.csv"  # Name of file
        geojson_path = Path(geojson_filename)  # Construct the path to the GeoJSON file

        if geojson_path.exists():
            Mi_School_geojson = gpd.read_file(geojson_path)

            # Drop unwanted columns
            columns_to_drop = ['Address', 'City', 'ZIP Code', 'Grade Levels', 'Locale', 'District Code', 'District', 'ISD Code', 'ISD Name']
            Mi_School_geojson.drop(columns=columns_to_drop, axis=1, inplace=True)

            # Ensure 'School Code' is treated as a string to preserve leading zeros
            Mi_School_geojson['School Code'] = Mi_School_geojson['School Code'].astype(str)

            # If the 'School Code' column contains integers without leading zeros, add them
            Mi_School_geojson['School Code'] = Mi_School_geojson['School Code'].apply(lambda x: str(x).zfill(5))

            # Merge GeoJSON file and DataFrame
            School_Combined = pd.merge(Mi_School_geojson, df, on='School Code', how='left', suffixes=('', '_drop'))

            # Identify and drop columns that end with '_drop'
            School_Combined = School_Combined.loc[:, ~School_Combined.columns.str.endswith('_drop')]
            
            # Convert Latitude and Longitude to numeric, coercing errors to NaN
            School_Combined['Latitude'] = pd.to_numeric(School_Combined['Latitude'], errors='coerce')
            School_Combined['Longitude'] = pd.to_numeric(School_Combined['Longitude'], errors='coerce')

            # Drop rows where Latitude or Longitude are NaN
            School_Combined.dropna(subset=['Latitude', 'Longitude'], inplace=True)

            # Load the Michigan GeoJSON file
            michigan_geojson_path = "geojson/michigan.geojson"  # file path
            michigan_geojson = gpd.read_file(michigan_geojson_path)

            def style_function(feature):
                return {
                    'color': 'black',        # Border color
                    'weight': 1.5,           # Slightly thicker border for clarity
                    'fillOpacity': 0.0,      # No fill opacity
                    'lineOpacity': 1,        # Make the border more visible
                }

            m = folium.Map(location=[44.3148, -85.6024], zoom_start=7, attr='MiMTSS TA Center')

            # Add the Michigan GeoJSON to the map with the style function
            folium.GeoJson(
                michigan_geojson,
                style_function=style_function
            ).add_to(m)

            # Iterate through the School_Combined DataFrame to add circle markers
            for idx, row in School_Combined.iterrows():
                if row['Count'] == 1:  # Check if the 'Count' column is 1
                    folium.CircleMarker(
                        location=[row['Latitude'], row['Longitude']],
                        radius=8,  # Small radius for the dot
                        color='#006DB6',  # Border color of the circle
                        stroke=False,  # No border
                        fill=True,  # Fill the circle
                        fill_color='#006DB6',  # Fill color of the circle
                        fill_opacity=0.6,  # Opacity of the fill
                        opacity=1,  # Opacity of the stroke (not used since stroke=False)
                        popup=row['School']
                    ).add_to(m)

        st.divider()

        # Displaying Schools that were matched from df
        Schools_with_one = School_Combined[School_Combined['Count'] == 1]
        if not Schools_with_one.empty:
            st.write("Schools Included:")
            st.dataframe(Schools_with_one[['School', 'School Code']].reset_index(drop=True))

            # Informing the user about the total number of Schools with a count of 1
            total_Schools_with_one = len(Schools_with_one)
            st.write("Total number of Schools:", total_Schools_with_one)

            # Convert DataFrame to CSV for the download button
            csv = Schools_with_one[['School', 'School Code']].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Included School List to Verify",
                data=csv,
                file_name="School_List_to_Verify.csv",
                mime="text/csv",
                key='download-csv-1'
            )
        else:
            st.write("No Schools")

        st.divider() 
        
        # Displaying Schools that were not matched from df
        unmatched_Schools_df = df[~df['School Code'].isin(School_Combined['School Code'])]
        
        # Display the unmatched Schools from df
        if not unmatched_Schools_df.empty:
            st.write("Schools unmatched:")
            st.dataframe(unmatched_Schools_df[['School', 'School Code']].reset_index(drop=True))
        
            # Inform the user about the total number of unmatched Schools from df
            total_unmatched_Schools_df = len(unmatched_Schools_df)
            st.write("Total number of unmatched Schools:", total_unmatched_Schools_df)
        
            # Convert DataFrame to CSV for the download button
            csv = unmatched_Schools_df[['School', 'School Code']].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Unmatched School List",
                data=csv,
                file_name="Unmatched_School_List.csv",
                mime="text/csv",
                key='download-csv-unmatched-df'
            )
        else:
            st.write("All Schools from your spreadsheet matched with the Michigan School Location file.")

        st.divider()

        # Call to render Folium map in Streamlit
        st_data = st_folium(m, width=725)

        # Save the map to a temporary HTML file and offer it for download
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmpfile:
            m.save(tmpfile.name)
            tmpfile.seek(0)
            with open(tmpfile.name, "rb") as file:
                btn = st.download_button(
                    label="Download Map as HTML",
                    data=file,
                    file_name="School_Map.html",
                    mime="text/html",
                    type="primary"
                )
