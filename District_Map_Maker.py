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
    # https://fonts.google.com/selection/embed

#------------------------------------------------------------------------
# Header
#------------------------------------------------------------------------

# st.image('MTSS.ai_Logo.png', width=300)

st.title('MTSS:grey[.ai]')
st.header('Map Maker:grey[ | School Districts]')

contact = st.sidebar.toggle('Handmade by  \n**LeVesseur** :grey[ PhD]  \n| :grey[MTSS.ai]')
if contact:
    st.sidebar.write('Inquiries: [info@mtss.ai](mailto:info@mtss.ai)  \nProfile: [levesseur.com](http://levesseur.com)  \nCheck out: [InkQA | Dynamic PDFs](http://www.inkqa.com)') 
    
#------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------

st.divider()

# Add the descriptive text
st.markdown("""
Your District data spreadsheet must include two columns: 'District' and 'District Code'. The District codes are used to match the location data to create a map.

If your spreadsheet lists districts in the 'District' column but does not include district codes, use the **District Code Matchmaker** to find the 'District Code'.
""")

# Path to the existing Excel file
file_path = "examples/District_Data.xlsx"

# Read the file and load it into a bytes object
with open(file_path, "rb") as file:
    file_data = file.read()

# Display download button with MIME type for Excel
st.download_button(
    label="Download an example District data spreadsheet",
    data=file_data,
    file_name='District_Data.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'  # MIME type for .xlsx files
)

st.divider()

# Excel/CSV file upload
uploaded_file = st.file_uploader("Upload your District data XLSX | CSV", type=['xlsx', 'csv'])
if uploaded_file is not None:
    with st.spinner("Processing data and generating map"):
        # Load data from the uploaded file
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, dtype={'District Code': str})
        elif uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file, dtype={'District Code': str})
        else:
            st.error("Unsupported file format. Please upload a CSV or XLSX file.")
            st.stop()  # Stop execution if file format is not supported

        # Check if required columns are present
        required_columns = ['District', 'District Code']
        if not all(col in df.columns for col in required_columns):
            st.warning("The uploaded file must contain 'District' and 'District Code' columns.")
            st.stop()  # Stop execution if required columns are not present

        # Ensure 'District Code' is treated as a string and remove any decimal points
        df['District Code'] = df['District Code'].apply(lambda x: str(int(float(x))) if '.' in str(x) else str(x))

        # Add column "Count" and set all rows to 1
        df['Count'] = 1

        # If the 'District Code' column contains integers without leading zeros, add them
        df['District Code'] = df['District Code'].apply(lambda x: x.zfill(5))

        # Load GeoJSON file from the root directory
        geojson_filename = "geojson/School_Districts.geojson"  # Name of your GeoJSON file
        geojson_path = Path(geojson_filename)  # Construct the path to the GeoJSON file

        if geojson_path.exists():
            Mi_District_geojson = gpd.read_file(geojson_path)
            Mi_District_geojson.rename(columns={'DCODE': 'District Code', 'NAME': 'District'}, inplace=True)

            # Drop unwanted columns
            columns_to_drop = ['OBJECTID', 'FIPSCODE', 'FIPSNUM', 'LABEL', 'TYPE', 'SQKM', 'SQMILES', 'ACRES', 'VER', 'LAYOUT', 'PENINSULA', 'ShapeSTArea', 'ShapeSTLength', 'ISD']
            Mi_District_geojson.drop(columns=columns_to_drop, axis=1, inplace=True)

            # Ensure 'District Code' is treated as a string to preserve leading zeros
            Mi_District_geojson['District Code'] = Mi_District_geojson['District Code'].apply(lambda x: str(int(float(x))) if '.' in str(x) else str(x))

            # If the 'District Code' column contains integers without leading zeros, add them
            Mi_District_geojson['District Code'] = Mi_District_geojson['District Code'].apply(lambda x: x.zfill(5))

            # Merge GeoJSON file and DataFrame
            District_Combined = pd.merge(Mi_District_geojson, df, on='District Code', how='left', suffixes=('', '_drop')).fillna(0)

            # Identify and drop columns that end with '_drop'
            District_Combined = District_Combined.loc[:, ~District_Combined.columns.str.endswith('_drop')]

            # Generating the Folium map
            def style_function(feature):
                count = feature['properties'].get('Count', 0)
                return {
                    'fillColor': '#48BB88' if count > 0 else 'white',
                    'color': 'black',
                    'weight': 0.15,
                    'fillOpacity': 0.7 if count > 0 else 0.25,
                    'lineOpacity': 0.4,
                }

            # Create the Folium map
            m = folium.Map(location=[44.3148, -85.6024], zoom_start=7)
            folium.GeoJson(
                District_Combined.to_json(),
                style_function=style_function,
                tooltip=folium.GeoJsonTooltip(fields=['District'], aliases=['District: '])
            ).add_to(m)

            # Load the Michigan GeoJSON file
            michigan_geojson_path = "geojson/michigan.geojson"
            michigan_geojson = gpd.read_file(michigan_geojson_path)

            # Define the style function for the Michigan border
            def michigan_style_function(feature):
                return {
                    'color': 'black',        # Border color
                    'weight': 1.5,             # Thicker border for visibility
                    'fillOpacity': 0,        # No fill opacity
                    'lineOpacity': 1,        # Full opacity for the border
                }

            # Add the Michigan GeoJSON to the map with the style function
            folium.GeoJson(
                michigan_geojson,
                style_function=michigan_style_function
            ).add_to(m)

        st.divider()

        # Displaying districts that were matched from df
        Districts_with_one = District_Combined[District_Combined['Count'] == 1]
        if not Districts_with_one.empty:
            st.write("Districts Included:")
            st.dataframe(Districts_with_one[['District', 'District Code']].reset_index(drop=True))

            # Informing the user about the total number of districts with a count of 1
            total_Districts_with_one = len(Districts_with_one)
            st.write("Total number of Districts:", total_Districts_with_one)

            # Convert DataFrame to CSV for the download button
            csv = Districts_with_one[['District', 'District Code']].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Included District List to Verify",
                data=csv,
                file_name="District_List_to_Verify.csv",
                mime="text/csv",
                key='download-csv-1'
            )
        else:
            st.write("No Districts")

        st.divider()

        # Displaying districts that were not matched from df
        unmatched_districts_df = df[~df['District Code'].isin(District_Combined['District Code'])]

        # Display the unmatched districts from df
        if not unmatched_districts_df.empty:
            st.write("Districts unmatched:")
            st.dataframe(unmatched_districts_df[['District', 'District Code']].reset_index(drop=True))

            # Inform the user about the total number of unmatched districts from df
            total_unmatched_districts_df = len(unmatched_districts_df)
            st.write("Total number of unmatched Districts:", total_unmatched_districts_df)

            # Convert DataFrame to CSV for the download button
            csv = unmatched_districts_df[['District', 'District Code']].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Unmatched District List",
                data=csv,
                file_name="Unmatched_District_List.csv",
                mime="text/csv",
                key='download-csv-unmatched-df'
            )
        else:
            st.write("All Districts from your spreadsheet matched with the Michigan District GeoJSON file.")

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
                    file_name="District_Map.html",
                    mime="text/html",
                    type="primary"
                )
