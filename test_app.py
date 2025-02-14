import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

def main():
    fig = go.Figure(data=go.Scatter(x=[1, 2, 3], y=[3, 2, 1], mode='markers'))

    filename = 'image.png'

    with st.spinner('exporting image'):
        try:
            pio.write_image(fig, filename, format="png", engine="kaleido")
            print("Image export successful.")
        except Exception as e:
            print(f"Image export failed: {e}")

    with open(filename, "rb") as file:
        st.download_button(
            label="Download Plot as PNG",
            data=file,
            file_name=filename,
            mime="image/png"
        )

if __name__ == '__main__':
    main()