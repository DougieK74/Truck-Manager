import streamlit as st
import pandas as pd
import numpy as np
import random
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# Set up Streamlit app title
st.title("Truck Load Optimization Prototype")

# Define truck parameters
truck_length = 50
truck_width = 8
truck_max_weight = 45000  # in lbs

# Create an input form for shipments
st.sidebar.header("Add a Shipment")
shipment_length = st.sidebar.slider("Length (ft)", 1, 50, 10)
shipment_width = st.sidebar.slider("Width (ft)", 1, 8, 4)
shipment_weight = st.sidebar.slider("Weight (lbs)", 500, 10000, 3000)
destination = st.sidebar.text_input("Destination", "New York, NY")
if st.sidebar.button("Add Shipment"):
    if "shipments" not in st.session_state:
        st.session_state["shipments"] = []
    st.session_state["shipments"].append({
        "Length": shipment_length,
        "Width": shipment_width,
        "Weight": shipment_weight,
        "Destination": destination
    })

# Display current shipments
if "shipments" in st.session_state and st.session_state["shipments"]:
    st.subheader("Current Shipments")
    df_shipments = pd.DataFrame(st.session_state["shipments"])
    st.dataframe(df_shipments)

    # Optimize truck load
    total_weight = df_shipments["Weight"].sum()
    if total_weight > truck_max_weight:
        st.warning("Warning: Truck is overloaded! Consider redistributing loads.")

    # Visualize truck load arrangement
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.set_xlim([0, truck_length])
    ax.set_ylim([0, truck_width])
    ax.set_xlabel("Truck Length (ft)")
    ax.set_ylabel("Truck Width (ft)")
    ax.set_title("Truck Load Arrangement")

    x_pos = 0
    y_pos = 0
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'yellow']
    for i, row in df_shipments.iterrows():
        if x_pos + row["Length"] > truck_length:  # Move to next row if length exceeds
            x_pos = 0
            y_pos += row["Width"]
        if y_pos + row["Width"] > truck_width:  # Stop if width exceeds
            break
        rect = Rectangle((x_pos, y_pos), row["Length"], row["Width"],
                         color=colors[i % len(colors)], alpha=0.5, edgecolor='black', linewidth=1)
        ax.add_patch(rect)
        ax.text(x_pos + row["Length"]/2, y_pos + row["Width"]/2,
                f"{row['Weight']} lbs", ha="center", va="center", fontsize=10, color="black")
        x_pos += row["Length"]

    st.pyplot(fig)

    # Show total weight and available capacity
    remaining_weight = truck_max_weight - total_weight
    st.subheader(f"Total Weight: {total_weight} lbs (Remaining: {remaining_weight} lbs)")
else:
    st.info("No shipments added yet. Use the sidebar to add shipments.")

# Reset button
if st.button("Reset Shipments"):
    st.session_state["shipments"] = []
    st.experimental_rerun()