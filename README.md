# Advanced Truck Load Optimization App

This Streamlit app allows logistics companies to:

- Enter shipment details including start and end cities, size, weight, and hazmat status
- Automatically calculate the driving distance between cities using OpenRouteService
- Estimate fuel and wage costs based on user-defined parameters
- Apply a custom profit margin and view total cost estimates
- Visualize how freight is arranged inside a 50 ft x 8 ft truck

## How to Run Locally

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Run the app:
```bash
streamlit run app.py
```

## OpenRouteService API Key

To use the routing feature, you'll need a free OpenRouteService API key from https://openrouteservice.org/dev/#/signup.

This version includes your pre-configured API key, but you can replace it in `app.py` for security.

## Deploy to Streamlit Cloud

1. Upload the following files to a public GitHub repo:
   - app.py
   - requirements.txt
   - README.md (optional)

2. Go to https://streamlit.io/cloud and deploy from your GitHub repo.