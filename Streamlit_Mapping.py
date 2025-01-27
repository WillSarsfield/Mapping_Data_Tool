import streamlit as st
import pandas as pd
import geopandas as gpd
import map

@st.cache_data
def load_data():
    itlmapping = pd.read_csv('itlmapping.csv')
    itl3_shapes_df = gpd.read_file('International_Territorial_Level_3_(January_2021)_UK_BUC_V3.geojson')
    return itlmapping, itl3_shapes_df

@st.cache_data
def process_data(map_df):
    
    return map_df

def main():
    st.set_page_config(layout="wide")

    uploaded_file = st.file_uploader("Upload a file", type=["csv"])

    # Button to confirm the selection
    if st.button("Set Filepath"):
        if uploaded_file:
            st.success(f"Filepath set to: {uploaded_file.name}")
            df = pd.read_csv(uploaded_file)
            st.dataframe(df)
            itlmapping, itl3_shapes_df = load_data()
            map_df = itl3_shapes_df.rename(columns={'ITL321CD': 'itl3'})
            map_df = map_df.merge(itlmapping, how='left', on='itl3')
            map_df = map_df.groupby(['itl2', 'itl2name']).geometry.apply(lambda x: x.union_all()).reset_index()
            map_df = gpd.GeoDataFrame(map_df, geometry='geometry', crs=itl3_shapes_df.crs)
            map_df['geometry'] = map_df['geometry'].simplify(0.0001, preserve_topology=True)
            figure = st.empty()

            fig = map.make_choropleths(df.set_index('itl2'), map_df)


            figure.plotly_chart(fig[0], use_container_width=True, key=f"plot_1")
        else:
            st.error("No file uploaded yet.")
    
    


if __name__ == '__main__':
    main()