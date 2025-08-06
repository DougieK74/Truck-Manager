import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import openrouteservice

# Initialize OpenRouteService client with provided API key
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjNjNTMzNTYwN2I4MjRhYjk4MTFiMmI4MDM3MTEyMjkzIiwiaCI6Im11cm11cjY0In0="
client = openrouteservice.Client(key=ORS_API_KEY)

# Truck configuration
TRUCK_LENGTH = 50
TRUCK_WIDTH = 8
TRUCK_HEIGHT = 10
TRUCK_CAPACITY = 45000

st.set_page_config(layout="wide")
st.title("🚛 AI Truck Load Optimizer with 3D Visualization and Routing")

# Sidebar inputs
st.sidebar.header("Add Shipment")
start_city = st.sidebar.text_input("Start City", "Houston, TX")
end_city = st.sidebar.text_input("End City", "Chicago, IL")
length = st.sidebar.slider("Length (ft)", 1, TRUCK_LENGTH, 10)
width = st.sidebar.slider("Width (ft)", 1, TRUCK_WIDTH, 4)
height = st.sidebar.slider("Height (ft)", 1, TRUCK_HEIGHT, 4)
weight = st.sidebar.slider("Weight (lbs)", 100, 10000, 3000)
shape = st.sidebar.selectbox("Shape", ["Rectangular", "Cylinder"])
hazmat = st.sidebar.checkbox("Hazmat")

if st.sidebar.button("Add to Load"):
    if "shipments" not in st.session_state:
        st.session_state["shipments"] = []
    st.session_state["shipments"].append({
        "start": start_city,
        "end": end_city,
        "length": length,
        "width": width,
        "height": height,
        "weight": weight,
        "shape": shape,
        "hazmat": hazmat
    })

# Get truck route and driving time
def get_route_distance_and_duration(start, end):
    try:
        start_coords = client.pelias_search(text=start)["features"][0]["geometry"]["coordinates"]
        end_coords = client.pelias_search(text=end)["features"][0]["geometry"]["coordinates"]
        route = client.directions(coordinates=[start_coords, end_coords], profile='driving-hgv', format='geojson')
        summary = route['features'][0]['properties']['summary']
        return round(summary['distance'] / 1609.34, 2), round(summary['duration'] / 3600, 2)  # miles, hours
    except Exception as e:
        st.warning(f"Routing error: {e}")
        return None, None

# Visualize 3D load in truck
def plot_3d_truck(shipments):
    fig = go.Figure()
    used_space = np.zeros((TRUCK_LENGTH, TRUCK_WIDTH, TRUCK_HEIGHT))
    x_cursor, y_cursor, z_cursor = 0, 0, 0

    for i, s in enumerate(shipments):
        l, w, h = s["length"], s["width"], s["height"]
        while x_cursor + l > TRUCK_LENGTH or y_cursor + w > TRUCK_WIDTH:
            x_cursor = 0
            y_cursor += w
            if y_cursor + w > TRUCK_WIDTH:
                y_cursor = 0
                z_cursor += h
            if z_cursor + h > TRUCK_HEIGHT:
                break
        if z_cursor + h > TRUCK_HEIGHT:
            continue

        color = f"rgba({np.random.randint(100,255)},{np.random.randint(100,255)},200,0.7)"
        if s["shape"] == "Rectangular":
            fig.add_trace(go.Mesh3d(
                x=[x_cursor, x_cursor+l, x_cursor+l, x_cursor, x_cursor, x_cursor+l, x_cursor+l, x_cursor],
                y=[y_cursor, y_cursor, y_cursor+w, y_cursor+w, y_cursor, y_cursor, y_cursor+w, y_cursor+w],
                z=[z_cursor, z_cursor, z_cursor, z_cursor, z_cursor+h, z_cursor+h, z_cursor+h, z_cursor+h],
                opacity=0.7,
                color=color,
                name=f"{s['weight']} lbs"
            ))
        elif s["shape"] == "Cylinder":
            theta = np.linspace(0, 2*np.pi, 30)
            x = x_cursor + l/2 + (l/2)*np.cos(theta)
            y = y_cursor + w/2 + (w/2)*np.sin(theta)
            z_base = np.full_like(theta, z_cursor)
            z_top = np.full_like(theta, z_cursor + h)
            for xb, yb, zb, zt in zip(x, y, z_base, z_top):
                fig.add_trace(go.Scatter3d(x=[xb, xb], y=[yb, yb], z=[zb, zt],
                                           mode='lines', line=dict(color=color, width=4)))

        x_cursor += l

    fig.update_layout(
        scene=dict(
            xaxis_title='Length (ft)',
            yaxis_title='Width (ft)',
            zaxis_title='Height (ft)',
            xaxis=dict(range=[0, TRUCK_LENGTH]),
            yaxis=dict(range=[0, TRUCK_WIDTH]),
            zaxis=dict(range=[0, TRUCK_HEIGHT])
        ),
        margin=dict(l=0, r=0, b=0, t=30),
        height=600
    )
    return fig

# Display all shipments
if "shipments" in st.session_state and st.session_state["shipments"]:
    st.subheader("Shipment List")
    df = pd.DataFrame(st.session_state["shipments"])
    st.dataframe(df)

    st.subheader("3D Truck Load Plan")
    fig = plot_3d_truck(st.session_state["shipments"])
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Logistics Routes & Timelines")
    for i, s in enumerate(st.session_state["shipments"]):
        dist, hours = get_route_distance_and_duration(s["start"], s["end"])
        if dist is not None:
            shifts = np.ceil(hours / 12)
            st.markdown(f"**Shipment {i+1}:** {s['start']} → {s['end']}")
            st.markdown(f"- Distance: {dist} miles")
            st.markdown(f"- Drive Time: {hours:.2f} hours")
            st.markdown(f"- Estimated Shifts (12h max): {int(shifts)}")
            st.markdown("---")

# Reset button
if st.button("Reset All Shipments"):
    st.session_state["shipments"] = []
    st.experimental_rerun()