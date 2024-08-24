import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as pt
import json
import os
from config import *


if "loaded" not in st.session_state:        
    st.session_state["demand_shift"] = 0
    st.session_state["supply_shift"] = 0
    st.session_state["shift"] = False
    st.session_state["equilibrium_quantity_original"] = 0
    st.session_state["equilibrium_quantity_shifted"] = 0
    st.session_state["equilibrium_price_original"] = 0
    st.session_state["equilibrium_price_shifted"] = 0    
    st.session_state["equilibrium_mc_prosppay_newquantity"] = 0
    st.session_state["gov_intervention"] = False
    st.session_state["gallery_selected"] = "(bitte wählen)"
    if os.path.exists("gallery.json"):
        st.session_state["has_gallery"] = True
        with open("gallery.json", "r", encoding="utf-8") as galleryfile:
            st.session_state["gallery_entries"] = json.load(galleryfile)
    else:
        st.session_state["has_gallery"] = False
    st.session_state["loaded"] = True


# Create Streamlit application
st.title(title)

# Callbacks
def callback_shifts():    
    st.session_state["demand_shift"] = st.session_state.slider1
    st.session_state["supply_shift"] = st.session_state.slider2
    st.session_state["shift"] = st.session_state["demand_shift"] != 0 or st.session_state["supply_shift"] != 0
    st.session_state["gallery_selected"] = "(bitte wählen)"

def callback_gov():
    st.session_state["gov_intervention"] = not st.session_state["gov_intervention"]
    st.session_state["gallery_selected"] = "(bitte wählen)"
    

def callback_scenarios():    
    scenario = st.session_state["gallery_choice"]
    st.session_state["gallery_selected"] = scenario
    if st.session_state["gallery_choice"] != "(bitte wählen)":
        st.session_state["demand_shift"] = st.session_state["gallery_entries"][scenario]["shift_demand"]
        st.session_state["supply_shift"] = st.session_state["gallery_entries"][scenario]["shift_supply"]
        st.session_state["shift"] = st.session_state["demand_shift"] != 0 or st.session_state["supply_shift"] != 0
        st.session_state["gov_intervention"] = st.session_state["gallery_entries"][scenario]["gov_intervention"]
    else:
        st.session_state["demand_shift"] = 0
        st.session_state["supply_shift"] = 0
        st.session_state["shift"] = False
        st.session_state["gov_intervention"] = False
    


# Create sliders for shifting demand and supply curves
st.subheader("I. Vorgaben", divider="gray")
slider_value_demand = st.slider("Nachfrage verschieben", key="slider1", min_value=-10, max_value=10, value=st.session_state["demand_shift"], on_change=callback_shifts)
st.slider("Angebot verschieben", key="slider2", min_value=-10, max_value=10, value=st.session_state["supply_shift"], on_change=callback_shifts)
st.checkbox("Verschiebung durch Steuer oder Subvention des Staates", st.session_state["gov_intervention"], on_change=callback_gov)


st.sidebar.header("Anzeige")

# Create option to show surpluses
st.sidebar.subheader("Renten von Haushalten und Firmen")
surplus_option = st.sidebar.radio(label="In Grafik darstellen", options=("Keine", "Ausgangssituation", "Nach Veränderung", "Beide"))
st.sidebar.subheader("Renten des Staates")
show_gov = st.sidebar.checkbox("Staatseinnahmen/-ausgaben anzeigen")
if show_gov and not st.session_state["gov_intervention"]:
    st.sidebar.write('<span style="color:red;">Die aktuelle Veränderung von Angebot/Nachfrage ist nicht markiert als durch Steuern oder Subventionen hervorgerufen. Solange werden keine Einnahmen/Ausgaben des Staates angezeigt.</span>', unsafe_allow_html=True)
st.sidebar.subheader("Wohlfahrtsverlust")
show_deadweight_loss = st.sidebar.checkbox("Wohlfahrtsverlust anzeigen (bei Staatseingriff)")
if show_deadweight_loss and not st.session_state["gov_intervention"]:
    st.sidebar.write('<span style="color:red;">Die aktuelle Veränderung von Angebot/Nachfrage ist nicht markiert als durch Steuern oder Subventionen hervorgerufen. Solange wird kein Wohlfahrtsverslust angezeigt.</span>', unsafe_allow_html=True)
st.sidebar.subheader("Quantitative Ergebnisse")
show_quant_results = st.sidebar.checkbox("Quantitative Ergebnisse anzeigen")

# Gallery
if st.session_state["has_gallery"]:    
    st.sidebar.divider()
    st.sidebar.header("Fertige Szenarien")
    gallery_entry_names = ["(bitte wählen)"] + [s for s in st.session_state["gallery_entries"].keys()]    
    gallery_option = st.sidebar.selectbox(label = "Fertige Szenarien:", options = gallery_entry_names, on_change=callback_scenarios, key="gallery_choice", index = gallery_entry_names.index(st.session_state["gallery_selected"]))



# -------- CALCULATE EQUILIBRIUM PRICE AND QUANTITY AS WELL AS SUPPORT POINT ON ORIGINAL CURVE (MARGINAL COSTS/MARGINAL PROSPENSITY TO PAY AT NEW QUANTITY)

# Original
st.session_state["equilibrium_quantity_original"] = (demand_intercept - supply_intercept) / (supply_slope - demand_slope)
st.session_state["equilibrium_price_original"] = demand_intercept + demand_slope * st.session_state["equilibrium_quantity_original"]
# After shift
st.session_state["equilibrium_quantity_shifted"] = (demand_intercept + st.session_state["demand_shift"] - (supply_intercept + st.session_state["supply_shift"])) / (supply_slope - demand_slope)
st.session_state["equilibrium_price_shifted"] = demand_intercept + st.session_state["demand_shift"]  + demand_slope * st.session_state["equilibrium_quantity_shifted"]
if st.session_state["demand_shift"] != 0 and st.session_state["supply_shift"] == 0:
    st.session_state["equilibrium_mc_prosppay_newquantity"] = demand_intercept + demand_slope * st.session_state["equilibrium_quantity_shifted"]
elif st.session_state["demand_shift"] == 0 and st.session_state["supply_shift"] != 0:
    st.session_state["equilibrium_mc_prosppay_newquantity"] = supply_intercept + supply_slope * st.session_state["equilibrium_quantity_shifted"]
else:
    st.session_state["equilibrium_mc_prosppay_newquantity"] = 0



# --------  CALCULATE SURPLUS AREAS

def calculate_surplus(demand_intercept, supply_intercept, equilibrium_price, equilibrium_quantity):
    consumer_surplus = 0.5 * (demand_intercept - equilibrium_price) * equilibrium_quantity
    producer_surplus = 0.5 * (equilibrium_price - supply_intercept) * equilibrium_quantity
    return consumer_surplus, producer_surplus

consumer_surplus_original, producer_surplus_original = calculate_surplus(
    demand_intercept, supply_intercept, st.session_state["equilibrium_price_original"], st.session_state["equilibrium_quantity_original"])
consumer_surplus_shifted, producer_surplus_shifted = calculate_surplus(
    demand_intercept + st.session_state["demand_shift"], supply_intercept + st.session_state["supply_shift"], st.session_state["equilibrium_price_shifted"], st.session_state["equilibrium_quantity_shifted"])



# --------  CREATE PLOT

st.subheader("II. Grafische Analyse", divider="gray")

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
if show_deadweight_loss:
    if st.session_state["equilibrium_mc_prosppay_newquantity"] != 0 and st.session_state["gov_intervention"]:
        deadweight_loss_shifted = [(st.session_state["equilibrium_quantity_shifted"], st.session_state["equilibrium_price_shifted"]), (st.session_state["equilibrium_quantity_original"], st.session_state["equilibrium_price_original"]), (st.session_state["equilibrium_quantity_shifted"], st.session_state["equilibrium_mc_prosppay_newquantity"])]
        patch_deadweight_loss = pt.Polygon(deadweight_loss_shifted, closed=True, fill=True, edgecolor='none',facecolor=deadweightloss_color, alpha=alpha_deadweight_loss, label="Wohlfahrtsverlust")
        ax.add_patch(patch_deadweight_loss)
if show_gov:
    if st.session_state["equilibrium_mc_prosppay_newquantity"] != 0 and st.session_state["gov_intervention"]:
        if st.session_state["demand_shift"] != 0:
            gov_incexp = [(0, demand_intercept), (0, demand_intercept + st.session_state["demand_shift"]), (st.session_state["equilibrium_quantity_shifted"], st.session_state["equilibrium_price_shifted"]), (st.session_state["equilibrium_quantity_shifted"], st.session_state["equilibrium_mc_prosppay_newquantity"])]            
        if st.session_state["supply_shift"] != 0:
            gov_incexp = [(0, supply_intercept), (0, supply_intercept + st.session_state["supply_shift"]), (st.session_state["equilibrium_quantity_shifted"], st.session_state["equilibrium_price_shifted"]), (st.session_state["equilibrium_quantity_shifted"], st.session_state["equilibrium_mc_prosppay_newquantity"])]
        if st.session_state["demand_shift"] < 0 or st.session_state["supply_shift"] > 0:
            gov_color = gov_income_color
            gov_text = "Einnahmen Staat"
        else:
            gov_color = gov_expenses_color
            gov_text = "Ausgaben Staat"
        patch_gov = pt.Polygon(gov_incexp, closed=True, fill=True, edgecolor='none',facecolor=gov_color, alpha=alpha_gov, label=gov_text)
        ax.add_patch(patch_gov)

# Graph style
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


# Model comment
if st.session_state["gallery_selected"] != "(bitte wählen)":
    scenario = st.session_state["gallery_selected"]    
    st.markdown(
        """
        <div style="background-color: #ffffcc; padding: 10px; border-radius: 5px; margin-bottom:20px">
            <p style="color: black;">
                <b> """ + scenario + """ </b><br> """ + st.session_state["gallery_entries"][scenario]["explain_text"] + """
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

if show_quant_results:    
    st.subheader("III. Quantitative Ergebnisse", divider="gray")

    # Display equilibrium price and quantity
    st.markdown("#### Preise")
    outp = "Gleichgewichtspreis (ursprünglich): **" + str(round(st.session_state["equilibrium_price_original"], 2)) + "**"
    st.write(outp)
    if st.session_state["shift"]:
        outp = "Gleichgewichtspreis (verschoben): **" + str(round(st.session_state["equilibrium_price_shifted"], 2)) + "**"
        st.write(outp)

    st.markdown("#### Mengen")
    outp = "Gleichgewichtsmenge (ursprünglich): **" + str(round(st.session_state["equilibrium_quantity_original"], 2)) + "**"
    st.write(outp)
    if st.session_state["shift"]:
        outp = "Gleichgewichtsmenge (verschoben): **" + str(round(st.session_state["equilibrium_quantity_shifted"], 2)) + "**"
        st.write(outp)

    if surplus_option != "Keine":
        st.markdown("#### Konsumentenrente")
    if surplus_option == "Ausgangssituation" or surplus_option == "Beide":
        outp = "Konsumentenrente (ursprünglich): **" + str(round(consumer_surplus_original, 2)) + "**"
        st.write(outp)
    if (surplus_option == "Nach Veränderung" or surplus_option == "Beide") and st.session_state["shift"]:
        outp = "Konsumentenrente (verschoben): **" + str(round(consumer_surplus_shifted, 2)) + "**"
        st.write(outp)

    if surplus_option != "Keine":
        st.markdown("#### Produzentenrente")
    if surplus_option == "Ausgangssituation" or surplus_option == "Beide":
        outp = "Produzentenrente (ursprünglich): **" +  str(round(producer_surplus_original, 2)) + "**"
        st.write(outp)
    if (surplus_option == "Nach Veränderung" or surplus_option == "Beide") and st.session_state["shift"]:
        outp = "Produzentenrente (verschoben): **" + str(round(producer_surplus_shifted, 2)) + "**"
        st.write(outp)

    if surplus_option != "Keine":
        st.markdown("#### Gesamtwohlfahrt")
    if surplus_option == "Ausgangssituation" or surplus_option == "Beide":
        outp = "Gesamtwohlfahrt (ursprünglich): **" + str(round(consumer_surplus_original + producer_surplus_original, 2)) + "**"
        st.write(outp)
    if (surplus_option == "Nach Veränderung" or surplus_option == "Beide") and st.session_state["shift"]:
        outp = "Gesamtwohlfahrt (verschoben): **" + str(round(consumer_surplus_shifted + producer_surplus_shifted, 2)) + "**"
        st.write(outp)


# Create inputs for demand and supply curves

st.sidebar.divider()

st.sidebar.header("Einstellungen")

with st.sidebar.expander("Parameter Angebots- und Nachfragekurven"):
    demand_slope = float(st.text_input("Nachfrage Steigung", value=str(demand_slope)))
    demand_intercept = float(st.text_input("Nachfrage y-Achsenabschnitt", value=str(demand_intercept)))
    supply_slope = float(st.text_input("Angebot Steigung", value=str(supply_slope)))
    supply_intercept = float(st.text_input("Angebot y-Achsenabschnitt", value=str(supply_intercept)))

with st.sidebar.expander("About MarketSimulator"):
    st.write("Version 0.2")