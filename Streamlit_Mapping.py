import streamlit as st
import pandas as pd
import geopandas as gpd
import map

def make_map_itl(itl_level):
    itlmapping = pd.read_csv('src/itlmapping.csv')
    itl3_shapes_df = gpd.read_file('src/International_Territorial_Level_3_(January_2021)_UK_BUC_V3.geojson')
    map_df = itl3_shapes_df.rename(columns={'ITL321CD': 'itl3'})
    if itl_level != 'itl3':
        map_df = map_df.merge(itlmapping, how='left', on='itl3')
        map_df = map_df.groupby([itl_level, f'{itl_level}name']).geometry.apply(lambda x: x.union_all()).reset_index()
    map_df = gpd.GeoDataFrame(map_df, geometry='geometry', crs=itl3_shapes_df.crs)
    map_df['geometry'] = map_df['geometry'].simplify(0.0001, preserve_topology=True)
    return map_df

def make_map_authorities(authority_level):
    mcamapping = pd.read_csv('src/mcamapping.csv')
    la_shapes_df = gpd.read_file('src/Local_Authority_Districts_December_2024_Boundaries_UK_BUC_-2087974657986281540.geojson')
    map_df = la_shapes_df.rename(columns={'LAD24CD': 'la'})
    if authority_level != 'la':
        map_df = map_df.merge(mcamapping, how='left', on='la')
        map_df = map_df.groupby(['mca', 'mcaname']).geometry.apply(lambda x: x.union_all()).reset_index()
    map_df = gpd.GeoDataFrame(map_df, geometry='geometry', crs=la_shapes_df.crs)
    map_df['geometry'] = map_df['geometry'].simplify(0.0001, preserve_topology=True)
    return map_df

@st.cache_data
def get_figures(uploaded_file):
    if not uploaded_file:
        return None
    
    df = pd.read_csv(uploaded_file)
    if df.iloc[:, 0][0][:2] == 'TL':
        geo_level = f'itl{str(len(df.iloc[:, 0][0]) - 2)}'
        map_df = make_map_itl(geo_level)
        df = df.rename(columns={df.columns[0]: geo_level})
    elif len(df.iloc[:, 0][0]) == 9:
        geo_level = 'la'
        map_df = make_map_authorities(geo_level)
        df = df.rename(columns={df.columns[0]: geo_level})
    fig = map.make_choropleths(df.set_index(geo_level), map_df, geo_level)
    return fig
    
def main():
    st.set_page_config(layout="wide")

    st.sidebar.html("<a href='https://lab.productivity.ac.uk' alt='The Productivity Lab'></a>")
    st.logo("static/logo.png", link="https://lab.productivity.ac.uk/", icon_image=None)

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
    if st.button("Generate Maps"):
        if uploaded_file:
            st.success(f"Filepath set to: {uploaded_file.name}")
            st.session_state.fig = get_figures(uploaded_file)
        else:
            st.error("No file uploaded yet.")

    if 'fig' in st.session_state:
        if st.session_state.fig:
            # Define button functionality
            with col1:
                if st.button("⬅️ Previous"):
                    st.session_state.index = (st.session_state.index - 1)

            with col3:
                if st.button("Next ➡️"):
                    st.session_state.index = (st.session_state.index + 1)

            # Dots in the centre with proper horizontal alignment
            with col2:
                total_figures = len(st.session_state.fig)
                current_index = st.session_state.index

                # Render clickable dots as styled buttons
                dot_container = '<div style="display: flex; justify-content: center; gap: 10px;">'
                for i in range(total_figures):
                    colour = "blue" if i == current_index % total_figures else "grey"
                    dot_container += f"""<a href="/?index={i}" style="text-decoration: none;">
                    <button style="background-color: {colour}; border: none;
                                border-radius: 50%; width: 20px; height: 20px;
                                cursor: pointer; margin: 0 5px;">
                    </button></a>"""
                dot_container += "</div>"

                st.markdown(dot_container, unsafe_allow_html=True)

            figure.plotly_chart(st.session_state.fig[st.session_state.index % len(st.session_state.fig)], use_container_width=True)


if __name__ == '__main__':
    main()