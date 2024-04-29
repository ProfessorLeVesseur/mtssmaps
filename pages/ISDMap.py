import streamlit as st
import pandas as pd
import geopandas
import folium
from streamlit_folium import st_folium
from pathlib import Path
import tempfile

# Streamlit page setup
st.set_page_config(page_title="ISD Mapping", layout="centered", initial_sidebar_state="auto")
st.image('/Users/cheynelevesseur/Desktop/Python_Code/Mapping_Projects/ISD_Map/MTSS.ai_Logo.png', width=300)  # Adjust path as needed
st.header('MI MTSS Maps™ | ISDs')
st.subheader('Map Generator')

# CSV file upload
# uploaded_file = st.file_uploader("Upload your ISD data CSV", type=["csv"])
# if uploaded_file is not None:
#     df = pd.read_csv(uploaded_file)

# Excel file upload
uploaded_file = st.file_uploader("Upload your ISD data XLSX", type=["xlsx"])
if uploaded_file is not None:
    # Specify dtype as str for 'ISD Code' to ensure it reads in as string
    df = pd.read_excel(uploaded_file, dtype={"ISD Code": str})
    
    # Add column "Count" and add 1 to all rows
    df['Count'] = 1

    # If the 'ISD Code' column contains integers without leading zeros, add them
    df['ISD Code'] = df['ISD Code'].apply(lambda x: str(x).zfill(5))
    
    # Load GeoJSON file from the root directory
    geojson_filename = "Intermediate_School_Districts.geojson"  # Name of your GeoJSON file
    geojson_path = Path(__file__).parent / geojson_filename  # Construct the path to the GeoJSON file
    
    if geojson_path.exists():
        Mi_ISD_geojson = geopandas.read_file(str(geojson_path))
        Mi_ISD_geojson.rename(columns={'ISD': 'ISD Code', 'NAME': 'ISD'}, inplace=True)
        
        # Drop unwanted columns
        columns_to_drop = ['OBJECTID', 'LABEL', 'TYPE', 'SQKM', 'SQMILES', 'ACRES', 'VER','LAYOUT', 'PENINSULA', 'ISDCode', 'ISD1', 'ShapeSTArea', 'ShapeSTLength']
        Mi_ISD_geojson.drop(columns=columns_to_drop, axis=1, inplace=True)
        
        # Ensure 'ISD Code' is treated as a string to preserve leading zeros
        Mi_ISD_geojson['ISD Code'] = Mi_ISD_geojson['ISD Code'].astype(str)
        
        # If the 'ISD Code' column contains integers without leading zeros, add them
        Mi_ISD_geojson['ISD Code'] = Mi_ISD_geojson['ISD Code'].apply(lambda x: str(x).zfill(5))

        # Merge GeoJSON file and DataFrame
        ISD_Combined = pd.merge(Mi_ISD_geojson, df, on='ISD Code', how='left', suffixes=('', '_drop')).fillna(0)
                                     
        # Identify any columns that end with '_drop' and drop them
        ISD_Combined = ISD_Combined.loc[:, ~ISD_Combined.columns.str.endswith('_drop')]

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

        m = folium.Map(location=[44.3148, -85.6024], zoom_start=7)
        folium.GeoJson(
            ISD_Combined.to_json(),
            style_function=style_function,
            tooltip=folium.GeoJsonTooltip(fields=['ISD'], aliases=['ISD:'])
        ).add_to(m)

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
                    file_name="District_Map.html",
                    mime="text/html"
                )
    
   # Displaying ISDs with a count of 1
    ISDs_with_one = ISD_Combined[ISD_Combined['Count'] == 1]
    if not ISDs_with_one.empty:
        st.write("ISDs:")
        # st.dataframe(ISDs_with_one[['ISD', 'ISD Code']])
        st.dataframe(ISDs_with_one[['ISD', 'ISD Code']].reset_index(drop=True))
        
        # Informing the user about the total number of ISD with a count of 1
        total_ISDs_with_one = len(ISDs_with_one)
        st.write(f"Total number of ISD: {total_ISDs_with_one}")
    else:
        st.write("No ISD have a count of 1.")