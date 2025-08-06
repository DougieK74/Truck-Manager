import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import openrouteservice

# API setup
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjNjNTMzNTYwN2I4MjRhYjk4MTFiMmI4MDM3MTEyMjkzIiwiaCI6Im11cm11cjY0In0="
client = openrouteservice.Client(key=ORS_API_KEY)

TRUCK_LENGTH = 50
TRUCK_WIDTH = 8
TRUCK_HEIGHT = 10

st.set_page_config(layout="wide")
st.title("🚛 Smart Truck Load Visualizer")

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

def plot_3d_truck(shipments):
    fig = go.Figure()

    # Trailer base
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

    # Trailer walls (faint)
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

if "shipments" in st.session_state and st.session_state["shipments"]:
    st.subheader("🌀 3D Truck Load View (Flatbed + Cab + Color Tags)")
    fig = plot_3d_truck(st.session_state["shipments"])
    st.plotly_chart(fig, use_container_width=True)