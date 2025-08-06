import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import openrouteservice

# Initialize OpenRouteService client (you must insert your own API key here)
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjNjNTMzNTYwN2I4MjRhYjk4MTFiMmI4MDM3MTEyMjkzIiwiaCI6Im11cm11cjY0In0="
client = openrouteservice.Client(key=ORS_API_KEY)

# Function to get driving distance between two cities
def get_distance(start, end):
    try:
        geocode = client.pelias_search(text=start)["features"][0]["geometry"]["coordinates"]
        start_coords = tuple(geocode[::-1])
        geocode = client.pelias_search(text=end)["features"][0]["geometry"]["coordinates"]
        end_coords = tuple(geocode[::-1])
        route = client.directions(coordinates=[start_coords[::-1], end_coords[::-1]], profile='driving-hgv', format='geojson')
        distance_km = route['features'][0]['properties']['summary']['distance'] / 1000
        return round(distance_km * 0.621371, 2)  # Convert km to miles
    except:
        return None

st.title("Advanced Truck Load Optimizer")

# Sidebar shipment input
st.sidebar.header("Shipment Details")
start_city = st.sidebar.text_input("Start City", "Houston, TX")
end_city = st.sidebar.text_input("End City", "Chicago, IL")
shipment_length = st.sidebar.slider("Length (ft)", 1, 50, 10)
shipment_width = st.sidebar.slider("Width (ft)", 1, 8, 4)
shipment_weight = st.sidebar.slider("Weight (lbs)", 500, 10000, 3000)
hazmat = st.sidebar.checkbox("Hazmat Material")

if st.sidebar.button("Add Shipment"):
    if "shipments" not in st.session_state:
        st.session_state["shipments"] = []
    st.session_state["shipments"].append({
        "Start": start_city,
        "End": end_city,
        "Length": shipment_length,
        "Width": shipment_width,
        "Weight": shipment_weight,
        "Hazmat": hazmat
    })

# Set truck parameters
truck_length = 50
truck_width = 8
truck_max_weight = 45000  # lbs

# Display shipments and costs
if "shipments" in st.session_state and st.session_state["shipments"]:
    st.subheader("Shipment Queue")
    df_shipments = pd.DataFrame(st.session_state["shipments"])
    st.dataframe(df_shipments)

    # Cost Parameters
    st.sidebar.markdown("### Cost Settings")
    diesel_price = st.sidebar.number_input("Diesel Price ($/gallon)", value=4.50)
    mpg = st.sidebar.number_input("Truck MPG", value=6.5)
    wage_per_mile = st.sidebar.number_input("Driver Wage ($/mile)", value=0.60)
    markup_pct = st.sidebar.slider("Profit Margin (%)", 0, 100, 25)

    cost_data = []
    for shipment in st.session_state["shipments"]:
        distance = get_distance(shipment["Start"], shipment["End"])
        if distance is None:
            distance = 1000  # fallback
        fuel_used = distance / mpg
        fuel_cost = fuel_used * diesel_price
        wage_cost = distance * wage_per_mile
        base_cost = fuel_cost + wage_cost
        total_cost = base_cost * (1 + markup_pct / 100)
        cost_data.append({
            "Start": shipment["Start"],
            "End": shipment["End"],
            "Distance (mi)": distance,
            "Fuel Cost": round(fuel_cost, 2),
            "Wage Cost": round(wage_cost, 2),
            "Total Cost ($)": round(total_cost, 2)
        })

    df_cost = pd.DataFrame(cost_data)
    st.subheader("Cost Estimates")
    st.dataframe(df_cost)

    # Visualization: top-down truck view
    st.subheader("Truck Load Visualization")
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.set_xlim([0, truck_length])
    ax.set_ylim([0, truck_width])
    ax.set_xlabel("Truck Length (ft)")
    ax.set_ylabel("Truck Width (ft)")
    ax.set_title("Top-Down Load Plan")

    x_pos, y_pos = 0, 0
    colors = ['red', 'blue', 'green', 'purple', 'orange']
    for i, row in df_shipments.iterrows():
        if x_pos + row["Length"] > truck_length:
            x_pos = 0
            y_pos += row["Width"]
        if y_pos + row["Width"] > truck_width:
            break
        rect = Rectangle((x_pos, y_pos), row["Length"], row["Width"],
                         color=colors[i % len(colors)], alpha=0.5, edgecolor='black')
        ax.add_patch(rect)
        ax.text(x_pos + row["Length"]/2, y_pos + row["Width"]/2,
                f"{row['Weight']} lbs", ha="center", va="center", fontsize=8)
        x_pos += row["Length"]

    st.pyplot(fig)

# Reset
if st.button("Reset All"):
    st.session_state["shipments"] = []
    st.experimental_rerun()