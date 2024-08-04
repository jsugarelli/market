import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as pt

# Set initial slope and intercept for demand and supply curves
demand_slope = -1
demand_intercept = 10
supply_slope = 1
supply_intercept = 2

# Set initial colors for demand and supply curves
supply_color = (218/255,0/255,42/255)
demand_color = (31/255,73/255,125/255)
equilibrium_color = (0/255,0/255,0/255)
alpha = 0.4
alpha_shift = 0.2

if "loaded" not in st.session_state:        
    st.session_state["demand_shift"] = 0
    st.session_state["supply_shift"] = 0
    st.session_state["shift"] = False
    st.session_state["equilibrium_quantity_original"] = 0
    st.session_state["equilibrium_quantity_shifted"] = 0
    st.session_state["equilibrium_price_original"] = 0
    st.session_state["equilibrium_price_shifted"] = 0    
    st.session_state["loaded"] = True

# Create Streamlit application
st.title("Vollkommener Wettbewerbsmarkt")

# Callbacks for sliders
def callback_shifts():    
    st.session_state["demand_shift"] = st.session_state.slider1
    st.session_state["supply_shift"] = st.session_state.slider2
    st.session_state["shift"] = st.session_state["demand_shift"] != 0 or st.session_state["supply_shift"] != 0

# Create sliders for shifting demand and supply curves
st.slider("Nachfrage verschieben", key="slider1", min_value=-10, max_value=10, value=st.session_state["demand_shift"], on_change=callback_shifts)
st.slider("Angebot verschieben", key="slider2", min_value=-10, max_value=10, value=st.session_state["supply_shift"], on_change=callback_shifts)

# Create text inputs for slope, intercept and colors
with st.sidebar.expander("Parameter"):
    demand_slope = float(st.text_input("Nachfrage Steigung", value=str(demand_slope)))
    demand_intercept = float(st.text_input("Nachfrage y-Achsenabschnitt", value=str(demand_intercept)))
    supply_slope = float(st.text_input("Angebot Steigung", value=str(supply_slope)))
    supply_intercept = float(st.text_input("Angebot y-Achsenabschnitt", value=str(supply_intercept)))

# Create option to show surpluses
surplus_option = st.sidebar.radio("Renten anzeigen", ("Keine", "Ausgangssituation", "Nach Veränderung", "Beide"))

# Calculate equilibrium price and quantity
st.session_state["equilibrium_quantity_original"] = (demand_intercept - supply_intercept) / (supply_slope - demand_slope)
st.session_state["equilibrium_price_original"] = demand_intercept + demand_slope * st.session_state["equilibrium_quantity_original"]

st.session_state["equilibrium_quantity_shifted"] = (demand_intercept + st.session_state["demand_shift"] - (supply_intercept + st.session_state["supply_shift"])) / (supply_slope - demand_slope)
st.session_state["equilibrium_price_shifted"] = demand_intercept + st.session_state["demand_shift"]  + demand_slope * st.session_state["equilibrium_quantity_shifted"]


# Calculate surplus areas
def calculate_surplus(demand_intercept, supply_intercept, equilibrium_price, equilibrium_quantity):
    consumer_surplus = 0.5 * (demand_intercept - equilibrium_price) * equilibrium_quantity
    producer_surplus = 0.5 * (equilibrium_price - supply_intercept) * equilibrium_quantity
    return consumer_surplus, producer_surplus

consumer_surplus_original, producer_surplus_original = calculate_surplus(
    demand_intercept, supply_intercept, st.session_state["equilibrium_price_original"], st.session_state["equilibrium_quantity_original"])
consumer_surplus_shifted, producer_surplus_shifted = calculate_surplus(
    demand_intercept + st.session_state["demand_shift"], supply_intercept + st.session_state["supply_shift"], st.session_state["equilibrium_price_shifted"], st.session_state["equilibrium_quantity_shifted"])

# Create plot
x = np.linspace(0, 20, 400)
fig, ax = plt.subplots()

# Plot original and shifted demand and supply curves
ax.plot(x, demand_slope * x + demand_intercept, label="Nachfrage", color=demand_color)
ax.plot(x, supply_slope * x + supply_intercept, label="Angebot", color=supply_color)
if st.session_state["shift"]:    
    ax.plot(x, demand_slope * x + demand_intercept + st.session_state["demand_shift"], label="Nachfrage (verschoben)", linestyle="dotted", color=demand_color)
    ax.plot(x, supply_slope * x + supply_intercept + st.session_state["supply_shift"], label="Angebot (verschoben)", linestyle="dotted", color=supply_color)

# Plot equilibrium points
ax.plot(st.session_state["equilibrium_quantity_original"], st.session_state["equilibrium_price_original"], marker="o", markersize=5, color=equilibrium_color)

if st.session_state["shift"]:
    print("shifty")
    ax.plot(st.session_state["equilibrium_quantity_shifted"], st.session_state["equilibrium_price_shifted"], marker="o", markersize=5, color=equilibrium_color)

# Plot surpluses if option is selected
if surplus_option == "Ausgangssituation" or surplus_option == "Beide":
    # Original Consumer Surplus
    consumer_surplus_edges = [(0, demand_intercept), (st.session_state["equilibrium_quantity_original"], st.session_state["equilibrium_price_original"]), (0, st.session_state["equilibrium_price_original"])]
    patch_consumer_surplus = pt.Polygon(consumer_surplus_edges, closed=True, fill=True, edgecolor='none',facecolor=demand_color, alpha=alpha, label="Konsumentenrente")
    ax.add_patch(patch_consumer_surplus)
    # Original Producer Surplus
    producer_surplus_edges = [(0, supply_intercept), (st.session_state["equilibrium_quantity_original"], st.session_state["equilibrium_price_original"]), (0, st.session_state["equilibrium_price_original"])]
    patch_producer_surplus = pt.Polygon(producer_surplus_edges, closed=True, fill=True, edgecolor='none',facecolor=supply_color, alpha=alpha, label="Produzentenrente")
    ax.add_patch(patch_producer_surplus)
if (surplus_option == "Nach Veränderung" or surplus_option == "Beide") and st.session_state["shift"]:
    # Shifted Consumer Surplus
    consumer_surplus_edges_shifted = [(0, demand_intercept+st.session_state["demand_shift"]), (st.session_state["equilibrium_quantity_shifted"], st.session_state["equilibrium_price_shifted"]), (0, st.session_state["equilibrium_price_shifted"])]
    patch_consumer_surplus_shifted = pt.Polygon(consumer_surplus_edges_shifted, closed=True, fill=True, edgecolor='none',facecolor=demand_color, alpha=alpha_shift, label="Konsumentenrente (nach Veränderung)")
    ax.add_patch(patch_consumer_surplus_shifted)
    # Shifted Producer Surplus
    producer_surplus_edges_shifted = [(0, supply_intercept+st.session_state["supply_shift"]), (st.session_state["equilibrium_quantity_shifted"], st.session_state["equilibrium_price_shifted"]), (0, st.session_state["equilibrium_price_shifted"])]
    patch_producer_surplus_shifted = pt.Polygon(producer_surplus_edges_shifted, closed=True, fill=True, edgecolor='none',facecolor=supply_color, alpha=alpha_shift, label="Produzentenrente (nach Veränderung)")
    ax.add_patch(patch_producer_surplus_shifted)

ax.set_xlabel("Menge")
ax.set_ylabel("Preis")
ax.legend()
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines['bottom'].set_position("zero")
ax.spines['left'].set_position("zero")
ax.xaxis.set_ticks_position("bottom")
ax.yaxis.set_ticks_position("left")
ax.set_ylim(bottom=0)
st.pyplot(fig)

# Display equilibrium price and quantity
st.sidebar.write("Gleichgewichtspreis (ursprünglich):", round(st.session_state["equilibrium_price_original"], 2))
st.sidebar.write("Gleichgewichtsmenge (ursprünglich):", round(st.session_state["equilibrium_quantity_original"], 2))
if st.session_state["shift"]:
    st.sidebar.write("Gleichgewichtspreis (verschoben):", round(st.session_state["equilibrium_price_shifted"], 2))
    st.sidebar.write("Gleichgewichtsmenge (verschoben):", round(st.session_state["equilibrium_quantity_shifted"], 2))

# Display surplus values if option is selected
if surplus_option == "Ausgangssituation" or surplus_option == "Beide":
    st.sidebar.write("Konsumentenrente (ursprünglich):", round(consumer_surplus_original, 2))
    st.sidebar.write("Produzentenrente (ursprünglich):", round(producer_surplus_original, 2))
    st.sidebar.write("Gesamtwohlfahrt (ursprünglich):", round(consumer_surplus_original + producer_surplus_original, 2))
elif (surplus_option == "Nach Veränderung" or surplus_option == "Beide") and st.session_state["shift"]:
    st.sidebar.write("Konsumentenrente (verschoben):", round(consumer_surplus_shifted, 2))
    st.sidebar.write("Produzentenrente (verschoben):", round(producer_surplus_shifted, 2))
    st.sidebar.write("Gesamtwohlfahrt (verschoben):", round(consumer_surplus_shifted + producer_surplus_shifted, 2))