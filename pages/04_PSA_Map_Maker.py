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
st.header('Map Maker:grey[ | Public School Academies]')

contact = st.sidebar.toggle('Handmade by  \n**LeVesseur** :grey[ PhD]  \n| :grey[MTSS.ai]')
if contact:
    st.sidebar.write('Inquiries: [info@mtss.ai](mailto:info@mtss.ai)  \nProfile: [levesseur.com](http://levesseur.com)  \nCheck out: [InkQA | Dynamic PDFs](http://www.inkqa.com)') 
    
#------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------

st.divider()

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
        required_columns = ['PSA', 'PSA Code']
        if not all(col in df.columns for col in required_columns):
            st.warning("The uploaded file must contain 'PSA' and 'PSA Code' columns.")
            st.stop()  # Stop execution if required columns are not present

        # Specify dtype as str for 'PSA Code' to ensure it reads in as string
        df['PSA Code'] = df['PSA Code'].astype(str)

        # Add column "Count" and set all rows to 1
        df['Count'] = 1

        # If the 'PSA Code' column contains integers without leading zeros, add them
        df['PSA Code'] = df['PSA Code'].apply(lambda x: str(x).zfill(5))

        # Load GeoJSON file from the root directory
        geojson_filename = "geojson/PSA_geojson.csv"  # Name of file
        geojson_path = Path(geojson_filename)  # Construct the path to the GeoJSON file

        if geojson_path.exists():
            Mi_PSA_geojson = gpd.read_file(geojson_path)

            # Drop unwanted columns
            columns_to_drop = ['Street', 'City', 'State', 'Zip', 'Address_Unformatted', 'confidence', 'confidence_city_level', 'confidence_street_level']
            Mi_PSA_geojson.drop(columns=columns_to_drop, axis=1, inplace=True)

            # Ensure 'PSA Code' is treated as a string to preserve leading zeros
            Mi_PSA_geojson['PSA Code'] = Mi_PSA_geojson['PSA Code'].astype(str)

            # If the 'PSA Code' column contains integers without leading zeros, add them
            Mi_PSA_geojson['PSA Code'] = Mi_PSA_geojson['PSA Code'].apply(lambda x: str(x).zfill(5))

            # Merge GeoJSON file and DataFrame
            # PSA_Combined = pd.merge(Mi_PSA_geojson, df, on='PSA Code', how='left', suffixes=('', '_drop')).fillna(0)
            PSA_Combined = pd.merge(Mi_PSA_geojson, df, on='PSA Code', how='left', suffixes=('', '_drop'))

            # Identify and drop columns that end with '_drop'
            PSA_Combined = PSA_Combined.loc[:, ~PSA_Combined.columns.str.endswith('_drop')]
            
            # Convert Latitude and Longitude to numeric, coercing errors to NaN
            PSA_Combined['Latitude'] = pd.to_numeric(PSA_Combined['Latitude'], errors='coerce')
            PSA_Combined['Longitude'] = pd.to_numeric(PSA_Combined['Longitude'], errors='coerce')

            # Drop rows where Latitude or Longitude are NaN
            PSA_Combined.dropna(subset=['Latitude', 'Longitude'], inplace=True)

            #NEW 
            # Load the Michigan GeoJSON file
            michigan_geojson_path = "geojson/michigan.geojson"  # file path
            michigan_geojson = gpd.read_file(michigan_geojson_path)

            def style_function(feature):
                return {
                    'color': 'black',        # Border color
                    'weight': 1,           # Slightly thicker border for clarity
                    'fillOpacity': 0.0,      # No fill opacity
                    'lineOpacity': 2,      # Make the border more visible
                }
            #END 

            # Generating the Folium map
            # def style_function(feature):
            #     count = feature['properties'].get('Count', 0)
            #     return {
            #         'fillColor': '#48BB88' if count > 0 else 'white',
            #         'color': 'black',
            #         'weight': 0.5,
            #         'fillOpacity': 0.7 if count > 0 else 0.25,
            #         'lineOpacity': 0.4,
            #     }

            # with st.spinner("Generating Folium map..."):
            m = folium.Map(location=[44.3148, -85.6024], zoom_start=7, attr='MiMTSS TA Center')

            #NEW
            # Add the Michigan GeoJSON to the map with the style function
            folium.GeoJson(
                michigan_geojson,
                style_function=style_function
            ).add_to(m)
            #END
            
            # # Iterate through the Mi_PSA_geocoded DataFrame to add markers
            # for idx, row in PSA_Combined.iterrows():
            #     if row['Count'] == 1:  # Check if the 'Count' column is 1
            #         folium.Marker(
            #             location=[row['Latitude'], row['Longitude']],
            #             popup=row['PSA'],  
            #             icon=folium.Icon(color='#006DB6', icon="circle", prefix='fa')
            #         ).add_to(m)

            # Iterate through the PSA_Combined DataFrame to add circle markers
            for idx, row in PSA_Combined.iterrows():
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
                        popup=row['PSA']
                    ).add_to(m)

        st.divider()

        # Displaying PSAs that were matched from df
        PSAs_with_one = PSA_Combined[PSA_Combined['Count'] == 1]
        if not PSAs_with_one.empty:
            st.write("PSAs Included:")
            st.dataframe(PSAs_with_one[['PSA', 'PSA Code']].reset_index(drop=True))

            # Informing the user about the total number of PSAs with a count of 1
            total_PSAs_with_one = len(PSAs_with_one)
            # st.write(f"Total number of PSAs: {total_PSAs_with_one}")
            st.write("Total number of PSAs:", total_PSAs_with_one)

            # Convert DataFrame to CSV for the download button
            csv = PSAs_with_one[['PSA', 'PSA Code']].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Included PSA List to Verify",
                data=csv,
                file_name="PSA_List_to_Verify.csv",
                mime="text/csv",
                key='download-csv-1'
            )
        else:
            st.write("No PSAs")

        st.divider() 
        
        # Displaying PSAs that were not matched from df
        unmatched_PSAs_df = df[~df['PSA Code'].isin(PSA_Combined['PSA Code'])]
        
        # Display the unmatched PSAs from df
        if not unmatched_PSAs_df.empty:
            st.write("PSAs unmatched::")
            st.dataframe(unmatched_PSAs_df[['PSA', 'PSA Code']].reset_index(drop=True))
        
            # Inform the user about the total number of unmatched PSAs from df
            total_unmatched_PSAs_df = len(unmatched_PSAs_df)
            st.write("Total number of unmatched PSAs:", total_unmatched_PSAs_df)
        
            # Convert DataFrame to CSV for the download button
            csv = unmatched_PSAs_df[['PSA', 'PSA Code']].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Unmatched PSA List",
                data=csv,
                file_name="Unmatched_PSA_List.csv",
                mime="text/csv",
                key='download-csv-unmatched-df'
            )
        else:
            st.write("All PSAs from your spreadsheet matched with the Michigan PSA Location file.")


        st.divider()

        # call to render Folium map in Streamlit
        st_data = st_folium(m, width=725)

        # Save the map to a temporary HTML file and offer it for download
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmpfile:
            m.save(tmpfile.name)
            tmpfile.seek(0)
            with open(tmpfile.name, "rb") as file:
                btn = st.download_button(
                    label="Download Map as HTML",
                    data=file,
                    file_name="PSA_Map.html",
                    mime="text/html",
                    type="primary"
                )
