import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import openrouteservice

# API Key
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjNjNTMzNTYwN2I4MjRhYjk4MTFiMmI4MDM3MTEyMjkzIiwiaCI6Im11cm11cjY0In0="
client = openrouteservice.Client(key=ORS_API_KEY)

# Truck parameters
TRUCK_LENGTH = 50
TRUCK_WIDTH = 8
TRUCK_HEIGHT = 10

st.set_page_config(layout="wide")
st.title("🚛 Smart Truck Load & Routing App")

# Sidebar shipment entry
st.sidebar.header("Add Shipment")
start_city = st.sidebar.text_input("Start City", "Houston, TX")
end_city = st.sidebar.text_input("End City", "Chicago, IL")
length = st.sidebar.slider("Length (ft)", 1, TRUCK_LENGTH, 10)
width = st.sidebar.slider("Width (ft)", 1, TRUCK_WIDTH, 4)
height = st.sidebar.slider("Height (ft)", 1, TRUCK_HEIGHT, 4)
weight = st.sidebar.slider("Weight (lbs)", 100, 10000, 3000)
shape = st.sidebar.selectbox("Shape", ["Rectangular", "Cylinder"])
name = st.sidebar.text_input("Item Name", "Steel Pipes")
hazmat = st.sidebar.checkbox("Hazmat")

# Sidebar cost settings
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
        "hazmat": hazmat,
        "name": name
    })

# Get routing info
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

# Plot truck with walls, color coding, tooltips
def plot_3d_truck(shipments):
    fig = go.Figure()

    # Trailer flatbed
    fig.add_trace(go.Mesh3d(
        x=[0, 0, TRUCK_LENGTH, TRUCK_LENGTH, 0, 0, TRUCK_LENGTH, TRUCK_LENGTH],
        y=[0, TRUCK_WIDTH, TRUCK_WIDTH, 0, 0, TRUCK_WIDTH, TRUCK_WIDTH, 0],
        z=[0]*4 + [1]*4,
        color='lightgray',
        opacity=0.2,
        name='Flatbed'
    ))

    # Truck cab
    fig.add_trace(go.Mesh3d(
        x=[-6, -6, 0, 0, -6, -6, 0, 0],
        y=[0, TRUCK_WIDTH, TRUCK_WIDTH, 0, 0, TRUCK_WIDTH, TRUCK_WIDTH, 0],
        z=[0, 0, 0, 0, 8, 8, 8, 8],
        color='blue',
        opacity=0.5,
        name='Truck Cab'
    ))

    # Trailer walls
    fig.add_trace(go.Scatter3d(x=[0, 0, 0, 0], y=[0, TRUCK_WIDTH, 0, TRUCK_WIDTH], z=[0, 0, TRUCK_HEIGHT, TRUCK_HEIGHT],
                               mode='lines', line=dict(color='black', width=2), name='Walls'))
    fig.add_trace(go.Scatter3d(x=[TRUCK_LENGTH, TRUCK_LENGTH, TRUCK_LENGTH, TRUCK_LENGTH],
                               y=[0, TRUCK_WIDTH, 0, TRUCK_WIDTH], z=[0, 0, TRUCK_HEIGHT, TRUCK_HEIGHT],
                               mode='lines', line=dict(color='black', width=2), name='Walls'))

    x_cursor, y_cursor, z_cursor = 0, 0, 1
    for s in shipments:
        l, w, h = s["length"], s["width"], s["height"]
        color = 'red' if s["hazmat"] else 'green'
        tooltip = f"{s['name']}<br>{s['weight']} lbs<br>{l}x{w}x{h} ft"

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
                z=[z_cursor]*4 + [z_cursor+h]*4,
                color=color,
                opacity=0.8,
                name=s["name"],
                hovertext=tooltip,
                hoverinfo='text'
            ))

        x_cursor += l

    fig.update_layout(
        scene=dict(
            xaxis=dict(title='Length (ft)', range=[-6, TRUCK_LENGTH]),
            yaxis=dict(title='Width (ft)', range=[0, TRUCK_WIDTH]),
            zaxis=dict(title='Height (ft)', range=[0, TRUCK_HEIGHT + 5])
        ),
        margin=dict(l=0, r=0, t=30, b=0),
        height=700,
        showlegend=False
    )
    return fig

# Display shipments
if "shipments" in st.session_state and st.session_state["shipments"]:
    df = pd.DataFrame(st.session_state["shipments"])
    st.subheader("📦 Shipment List")
    st.dataframe(df)

    st.subheader("🚛 3D Load View")
    fig = plot_3d_truck(st.session_state["shipments"])
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🗺 Routing & Cost Details")
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
            with st.expander("View Directions"):
                for step in steps:
                    st.write(f"→ {step['instruction']}")
            st.markdown("---")

# Reset
if st.button("🔁 Reset All"):
    st.session_state["shipments"] = []
    st.experimental_rerun()