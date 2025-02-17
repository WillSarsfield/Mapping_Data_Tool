import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
import asyncio

async def write_image(pio, fig, filename):
    pio.write_image(fig, filename, format="png", engine="kaleido")

async def main():
    fig = go.Figure(data=go.Scatter(x=[1, 2, 3], y=[3, 2, 1], mode='markers'))

    filename = 'image.png'

    with st.spinner('exporting image'):
        try:
            await asyncio.wait_for(write_image(pio, fig, filename), timeout=15)
            st.success("Image export successful.")
        except asyncio.TimeoutError:
            st.error(f"Timed out")
        except Exception as e:
            st.error(f"Image export failed: {e}")

    with open(filename, "rb") as file:
        st.image(filename)
        st.download_button(
            label="Download Plot as PNG",
            data=file,
            file_name=filename,
            mime="image/png"
        )

if __name__ == '__main__':
    asyncio.run(main())