import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import openrouteservice

# API client setup
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjNjNTMzNTYwN2I4MjRhYjk4MTFiMmI4MDM3MTEyMjkzIiwiaCI6Im11cm11cjY0In0="
client = openrouteservice.Client(key=ORS_API_KEY)

TRUCK_LENGTH = 50
TRUCK_WIDTH = 8
TRUCK_HEIGHT = 10
TRUCK_CAPACITY = 45000

st.set_page_config(layout="wide")
st.title("🚛 Complete Truck Load Optimizer")

# Sidebar Inputs
st.sidebar.header("Add Shipment")
start_city = st.sidebar.text_input("Start City", "Houston, TX")
end_city = st.sidebar.text_input("End City", "Chicago, IL")
length = st.sidebar.slider("Length (ft)", 1, TRUCK_LENGTH, 10)
width = st.sidebar.slider("Width (ft)", 1, TRUCK_WIDTH, 4)
height = st.sidebar.slider("Height (ft)", 1, TRUCK_HEIGHT, 4)
weight = st.sidebar.slider("Weight (lbs)", 100, 10000, 3000)
shape = st.sidebar.selectbox("Shape", ["Rectangular", "Cylinder"])
hazmat = st.sidebar.checkbox("Hazmat")

# Cost configuration
st.sidebar.header("Cost Parameters")
diesel_price = st.sidebar.number_input("Diesel Price ($/gallon)", value=4.50)
mpg = st.sidebar.number_input("Truck MPG", value=6.5)
wage_per_mile = st.sidebar.number_input("Driver Wage ($/mile)", value=0.60)
markup_pct = st.sidebar.slider("Profit Margin (%)", 0, 100, 25)

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

# Routing and cost calculations
def get_route_info(start, end):
    try:
        start_coords = client.pelias_search(text=start)["features"][0]["geometry"]["coordinates"]
        end_coords = client.pelias_search(text=end)["features"][0]["geometry"]["coordinates"]
        route = client.directions(coordinates=[start_coords, end_coords], profile='driving-hgv', format='geojson')
        summary = route['features'][0]['properties']['summary']
        directions = route['features'][0]['properties']['segments'][0]['steps']
        distance_miles = round(summary['distance'] / 1609.34, 2)
        duration_hours = round(summary['duration'] / 3600, 2)
        return distance_miles, duration_hours, directions
    except Exception as e:
        st.warning(f"Routing error: {e}")
        return None, None, None

# 3D Visualization
def plot_3d_truck(shipments):
    fig = go.Figure()
    used = np.zeros((TRUCK_LENGTH, TRUCK_WIDTH, TRUCK_HEIGHT))
    x_cursor, y_cursor, z_cursor = 0, 0, 0

    for i, s in enumerate(shipments):
        l, w, h = s["length"], s["width"], s["height"]
        color = f"rgba({np.random.randint(100,255)}, {np.random.randint(100,255)}, 200, 0.7)"
        if x_cursor + l > TRUCK_LENGTH:
            x_cursor = 0
            y_cursor += w
        if y_cursor + w > TRUCK_WIDTH:
            y_cursor = 0
            z_cursor += h
        if z_cursor + h > TRUCK_HEIGHT:
            continue

        if s["shape"] == "Rectangular":
            fig.add_trace(go.Mesh3d(
                x=[x_cursor, x_cursor+l, x_cursor+l, x_cursor, x_cursor, x_cursor+l, x_cursor+l, x_cursor],
                y=[y_cursor, y_cursor, y_cursor+w, y_cursor+w, y_cursor, y_cursor, y_cursor+w, y_cursor+w],
                z=[z_cursor, z_cursor, z_cursor, z_cursor, z_cursor+h, z_cursor+h, z_cursor+h, z_cursor+h],
                opacity=0.7,
                color=color,
                name=f"{s['weight']} lbs"
            ))
        else:
            theta = np.linspace(0, 2*np.pi, 30)
            x = x_cursor + l/2 + (l/2)*np.cos(theta)
            y = y_cursor + w/2 + (w/2)*np.sin(theta)
            for xb, yb in zip(x, y):
                fig.add_trace(go.Scatter3d(x=[xb, xb], y=[yb, yb], z=[z_cursor, z_cursor+h],
                                           mode='lines', line=dict(color=color, width=4)))

        x_cursor += l

    fig.update_layout(
        scene=dict(
            xaxis=dict(title='Length', range=[0, TRUCK_LENGTH]),
            yaxis=dict(title='Width', range=[0, TRUCK_WIDTH]),
            zaxis=dict(title='Height', range=[0, TRUCK_HEIGHT])
        ),
        margin=dict(l=0, r=0, t=30, b=0),
        height=600
    )
    return fig

# Display if shipments exist
if "shipments" in st.session_state and st.session_state["shipments"]:
    df = pd.DataFrame(st.session_state["shipments"])
    st.subheader("📦 Shipment List")
    st.dataframe(df)

    st.subheader("🌀 3D Truck Load Visualization")
    fig = plot_3d_truck(st.session_state["shipments"])
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🗺 Routing + Cost Estimates")
    for i, s in enumerate(st.session_state["shipments"]):
        dist, hours, steps = get_route_info(s["start"], s["end"])
        if dist:
            fuel = dist / mpg
            fuel_cost = fuel * diesel_price
            wage_cost = dist * wage_per_mile
            base_cost = fuel_cost + wage_cost
            total_cost = base_cost * (1 + markup_pct / 100)
            shifts = int(np.ceil(hours / 12))

            st.markdown(f"### Shipment {i+1}: {s['start']} → {s['end']}")
            st.markdown(f"- Distance: **{dist} miles**")
            st.markdown(f"- Duration: **{hours:.2f} hours** (~{shifts} driver shift{'s' if shifts > 1 else ''})")
            st.markdown(f"- Fuel Cost: **${fuel_cost:.2f}**")
            st.markdown(f"- Wage Cost: **${wage_cost:.2f}**")
            st.markdown(f"- **Total Cost (incl. {markup_pct}% profit): ${total_cost:.2f}**")
            with st.expander("View Driving Directions"):
                for step in steps:
                    st.write(f"→ {step['instruction']}")
            st.markdown("---")

# Reset all
if st.button("🔁 Reset All"):
    st.session_state["shipments"] = []
    st.experimental_rerun()