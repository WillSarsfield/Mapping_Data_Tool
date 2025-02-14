import plotly.graph_objects as go
from plotly.io import to_image

# Test Plotly GO image export locally
fig = go.Figure(data=go.Scatter(x=[1, 2, 3], y=[3, 2, 1], mode='markers'))
try:
    img = to_image(fig, format="png")
    print("Image export successful.")
except Exception as e:
    print(f"Image export failed: {e}")
