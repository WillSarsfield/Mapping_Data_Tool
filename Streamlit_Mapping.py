import streamlit as st
import pandas as pd
import geopandas as gpd
import map

@st.cache_data
def get_figures(uploaded_file):
    if not uploaded_file:
        return None
    itlmapping = pd.read_csv('itlmapping.csv')
    itl3_shapes_df = gpd.read_file('International_Territorial_Level_3_(January_2021)_UK_BUC_V3.geojson')
    map_df = itl3_shapes_df.rename(columns={'ITL321CD': 'itl3'})
    map_df = map_df.merge(itlmapping, how='left', on='itl3')
    map_df = map_df.groupby(['itl2', 'itl2name']).geometry.apply(lambda x: x.union_all()).reset_index()
    map_df = gpd.GeoDataFrame(map_df, geometry='geometry', crs=itl3_shapes_df.crs)
    map_df['geometry'] = map_df['geometry'].simplify(0.0001, preserve_topology=True)
    df = pd.read_csv(uploaded_file)
    fig = map.make_choropleths(df.set_index('itl2'), map_df)
    return fig
    
def main():
    st.set_page_config(layout="wide")

    figure = st.empty()
    col1, col2, col3 = st.columns([1, 6, 1])

    uploaded_file = st.file_uploader("Upload a file", type=["csv"])

    # Initialise session state for the current figure index
    if "index" not in st.session_state:
        st.session_state.index = 0
    
    # Ensure session state is initialised for `fig`
    if "fig" not in st.session_state:
        st.session_state.fig = get_figures(uploaded_file)

    # Button to confirm the selection
    if st.button("Set Filepath"):
        if uploaded_file:
            st.success(f"Filepath set to: {uploaded_file.name}")
            st.session_state.fig = get_figures(uploaded_file)
        else:
            st.error("No file uploaded yet.")


    if st.session_state.fig:
        # Define button functionality
        with col1:
            if st.button("⬅️ Previous"):
                st.session_state.index = (st.session_state.index - 1)

        with col3:
            if st.button("Next ➡️"):
                st.session_state.index = (st.session_state.index + 1)
        
        figure.plotly_chart(st.session_state.fig[st.session_state.index % len(st.session_state.fig)], use_container_width=True)

    # st.dataframe(df)


if __name__ == '__main__':
    main()