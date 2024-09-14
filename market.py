import streamlit as st
import numpy as np
import math
import matplotlib.pyplot as plt
import matplotlib.patches as pt
import json
import os
from config import *
from translations import translations, language_flags  # Import the translations and flags
from openai import OpenAI
from streamlit import secrets

# Set up OpenAI API key
client = OpenAI(api_key=secrets["OPENAI_API_KEY"])

# Set the page title (browser tab title)
st.set_page_config(page_title=title)

if "loaded" not in st.session_state:        
    st.session_state["demand_slope"] = demand_slope
    st.session_state["demand_intercept"] = demand_intercept
    st.session_state["supply_slope"] = supply_slope
    st.session_state["supply_intercept"] = supply_intercept
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
    st.session_state["fix_axes"] = True
    st.session_state["show_grid"] = False
    st.session_state["tickmark_width"] = 1.0
    st.session_state["use_gallery"] = use_gallery
    st.session_state["use_ai"] = use_ai
    st.session_state["loaded"] = True
    st.session_state["language"] = default_language

# Add this function to get translations
def get_translation(key):
    return translations[st.session_state["language"]].get(key, key)

# Create Streamlit application
st.title(get_translation("TITLE"))
st.markdown("<br>", unsafe_allow_html=True)

# Callbacks
def callback_shifts():    
    st.session_state["demand_shift"] = float(st.session_state.slider1)
    st.session_state["supply_shift"] = float(st.session_state.slider2)
    st.session_state["shift"] = st.session_state["demand_shift"] != 0 or st.session_state["supply_shift"] != 0
    st.session_state["gallery_selected"] = "(bitte wählen)"

def callback_params():
    st.session_state["demand_slope"] = float(st.session_state.demand_slope_slider)
    st.session_state["demand_intercept"] = float(st.session_state.demand_intercept_slider)
    st.session_state["supply_slope"] = float(st.session_state.supply_slope_slider)
    st.session_state["supply_intercept"] = float(st.session_state.supply_intercept_slider)
    st.session_state["fix_axes"] = st.session_state.fix_axes_checkbox
    st.session_state["show_grid"] = st.session_state.show_grid_checkbox
    st.session_state["tickmark_width"] = st.session_state.tickmark_input

def callback_reset():
    st.session_state["demand_slope"] = demand_slope
    st.session_state["demand_intercept"] = demand_intercept
    st.session_state["supply_slope"] = supply_slope
    st.session_state["supply_intercept"] = supply_intercept

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
    

# Add this callback function for language change
def callback_language_change():
    st.session_state["language"] = st.session_state["language_selector"]

# Create tabs for controls and empty tab
st.subheader(get_translation("INPUTS_SUBHEADER"), divider="gray")
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 18px;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 20px;
        padding-bottom: 40px;
    }
    </style>
""", unsafe_allow_html=True)

tablist = [get_translation("EXOGENOUS_VARIABLES_TAB"), get_translation("PRICE_LIMITS_TAB")]
if st.session_state["use_gallery"]:
    tablist.append(get_translation("SCENARIOS_TAB"))
if st.session_state["use_ai"]:
    tablist.append(get_translation("AI_TAB"))

tabs = st.tabs(tablist)

with tabs[0]:    
    st.markdown("<br>", unsafe_allow_html=True)
    slider_value_demand = st.slider(get_translation("SHIFT_DEMAND"), key="slider1", min_value=-10.0, max_value=10.0, value=float(st.session_state["demand_shift"]), step=1.0, on_change=callback_shifts)
    slider_value_supply = st.slider(get_translation("SHIFT_SUPPLY"), key="slider2", min_value=-10.0, max_value=10.0, value=float(st.session_state["supply_shift"]), step=1.0, on_change=callback_shifts)
    st.checkbox(get_translation("GOV_INTERVENTION_CHECKBOX"), st.session_state["gov_intervention"], on_change=callback_gov)

with tabs[1]:
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        hoechstpreis = st.number_input(get_translation("MAX_PRICE"), value=None, step=0.1, format="%.2f")
    with col2:
        mindestpreis = st.number_input(get_translation("MIN_PRICE"), value=None, step=0.1, format="%.2f")

    if hoechstpreis is not None and mindestpreis is not None:
        st.warning(get_translation("PRICE_LIMITS_WARNING"))

    if mindestpreis is not None and mindestpreis < st.session_state["equilibrium_price_original"]:
        st.warning(get_translation("MIN_PRICE_WARNING").format(st.session_state["equilibrium_price_original"]))

    if hoechstpreis is not None and hoechstpreis > st.session_state["equilibrium_price_original"]:
        st.warning(get_translation("MAX_PRICE_WARNING").format(st.session_state["equilibrium_price_original"]))

if st.session_state["use_gallery"]:
    if st.session_state["has_gallery"]:    
        with tabs[2]:
            gallery_entry_names = ["(bitte wählen)"] + [s for s in st.session_state["gallery_entries"].keys()]
            st.write(get_translation("SCENARIOS_INSTRUCTIONS"))
            gallery_option = st.selectbox(label=get_translation("SCENARIOS_LABEL"), label_visibility="hidden", options = gallery_entry_names, on_change=callback_scenarios, key="gallery_choice", index = gallery_entry_names.index(st.session_state["gallery_selected"]))


# Add this function to call the OpenAI API
def call_openai_api(user_input):
    try:        
        print("Attempting to call OpenAI API...")
        # Use the user's API key if provided, otherwise use the default
        api_key = st.session_state.get("user_api_key", secrets["OPENAI_API_KEY"])
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model=ai_model,
            messages=[
                {"role": "system", "content": ai_system_message.replace("<LANGUAGE>", st.session_state["language"])},
                {"role": "user", "content": user_input}
            ],
            temperature=ai_temperature
        )        
        content = response.choices[0].message.content
        print("Raw API response:", content)  # Debug print
        return content
    except Exception as e:
        print(f"Error in API call: {str(e)}")  # Debug print
        error_message = get_translation("API_ERROR_WARNING")
        st.warning(f"{error_message}: {str(e)}")
        return f"Error: {str(e)}"

# Add this function to parse the API response
def parse_api_response(response):
    print("Raw API response:", response)  # Debug print
    try:
        # First, try to parse the response as JSON
        result = json.loads(response)
    except json.JSONDecodeError:
        print("Failed to parse response as JSON, attempting to parse as key-value pairs")
        # If JSON parsing fails, parse as a simple key-value format
        lines = response.strip().split('\n')
        result = {}
        for line in lines:
            parts = line.split(':', 1)
            if len(parts) == 2:
                key, value = parts
                result[key.strip()] = value.strip()
    
    print("Parsed result:", result)  # Debug print
    
    # Extract values with error handling
    try:
        return {
            "status": result.get("status", "okay"),
            "shift_demand": float(result.get("shift_demand", 0) or 0),
            "shift_supply": float(result.get("shift_supply", 0) or 0),
            "gov_intervention": result.get("gov_intervention", "False").lower() == "true",
            "comment": result.get("comment", "")
        }
    except Exception as e:
        print(f"Error extracting values from parsed result: {str(e)}")
        comment = ""
        return {"status": "error", "message": str(e), "comment": comment}

# Modify the AI tab content
if st.session_state["use_ai"]:
    with tabs[-1]:
        st.write(get_translation("AI_INSTRUCTIONS"))
        user_input = st.text_area(get_translation("AI_INPUT_LABEL"), height=150)
        if st.button(get_translation("ANALYZE_BUTTON")):
            with st.spinner(get_translation("ANALYZING_MESSAGE")):
                api_response = call_openai_api(user_input)
                result = parse_api_response(api_response)
                st.session_state["ai_result"] = result
                
                if result["status"] == "error" and result.get("comment")=="":
                    st.error(get_translation("AI_ERROR_MESSAGE") + result.get("message", ""))
                elif result["status"] == "error" and result.get("comment")!="":
                    st.error(get_translation("AI_ERROR_MESSAGE") + result.get("comment", ""))
                else:
                    st.success(get_translation("AI_SUCCESS_MESSAGE"))
                    st.session_state["demand_shift"] = result["shift_demand"]
                    st.session_state["supply_shift"] = result["shift_supply"]
                    st.session_state["gov_intervention"] = result["gov_intervention"]
                    st.session_state["shift"] = result["shift_demand"] != 0 or result["shift_supply"] != 0                    
                    st.rerun()


st.sidebar.header(get_translation("DISPLAY_HEADER"))


# Create option to show surpluses
st.sidebar.subheader(get_translation("SURPLUS_SUBHEADER"))
surplus_option = st.sidebar.radio(label=get_translation("SURPLUS_RADIO_LABEL"), options=(get_translation("SURPLUS_NONE"), get_translation("SURPLUS_ORIGINAL"), get_translation("SURPLUS_SHIFTED"), get_translation("SURPLUS_BOTH")))
st.sidebar.subheader(get_translation("GOV_SURPLUS_SUBHEADER"))
show_gov = st.sidebar.checkbox(get_translation("SHOW_GOV_CHECKBOX"))
if show_gov and not st.session_state["gov_intervention"]:
    st.sidebar.write(get_translation("GOV_INTERVENTION_WARNING"))
st.sidebar.subheader(get_translation("DEADWEIGHT_LOSS_SUBHEADER"))
show_deadweight_loss = st.sidebar.checkbox(get_translation("SHOW_DEADWEIGHT_LOSS_CHECKBOX"))
if show_deadweight_loss and not st.session_state["gov_intervention"]:
    st.sidebar.write(get_translation("GOV_INTERVENTION_WARNING"))
st.sidebar.subheader(get_translation("QUANT_RESULTS_SUBHEADER"))
show_quant_results = st.sidebar.checkbox(get_translation("SHOW_QUANT_RESULTS_CHECKBOX"))




# -------- CALCULATE EQUILIBRIUM PRICE AND QUANTITY AS WELL AS SUPPORT POINT ON ORIGINAL CURVE (MARGINAL COSTS/MARGINAL PROSPENSITY TO PAY AT NEW QUANTITY)

# Original
st.session_state["equilibrium_quantity_original"] = (st.session_state["demand_intercept"] - st.session_state["supply_intercept"]) / (st.session_state["supply_slope"] - st.session_state["demand_slope"])
st.session_state["equilibrium_price_original"] = st.session_state["demand_intercept"] + st.session_state["demand_slope"] * st.session_state["equilibrium_quantity_original"]
# After shift
st.session_state["equilibrium_quantity_shifted"] = (st.session_state["demand_intercept"] + st.session_state["demand_shift"] - (st.session_state["supply_intercept"] + st.session_state["supply_shift"])) / (st.session_state["supply_slope"] - st.session_state["demand_slope"])
st.session_state["equilibrium_price_shifted"] = st.session_state["demand_intercept"] + st.session_state["demand_shift"]  + st.session_state["demand_slope"] * st.session_state["equilibrium_quantity_shifted"]
if st.session_state["demand_shift"] != 0 and st.session_state["supply_shift"] == 0:
    st.session_state["equilibrium_mc_prosppay_newquantity"] = st.session_state["demand_intercept"] + st.session_state["demand_slope"] * st.session_state["equilibrium_quantity_shifted"]
elif st.session_state["demand_shift"] == 0 and st.session_state["supply_shift"] != 0:
    st.session_state["equilibrium_mc_prosppay_newquantity"] = st.session_state["supply_intercept"] + st.session_state["supply_slope"] * st.session_state["equilibrium_quantity_shifted"]
else:
    st.session_state["equilibrium_mc_prosppay_newquantity"] = 0



# --------  CALCULATE SURPLUS AREAS

def calculate_surplus(demand_intercept, supply_intercept, equilibrium_price, equilibrium_quantity):
    consumer_surplus = 0.5 * (demand_intercept - equilibrium_price) * equilibrium_quantity
    producer_surplus = 0.5 * (equilibrium_price - supply_intercept) * equilibrium_quantity
    return consumer_surplus, producer_surplus

consumer_surplus_original, producer_surplus_original = calculate_surplus(
    st.session_state["demand_intercept"], st.session_state["supply_intercept"], st.session_state["equilibrium_price_original"], st.session_state["equilibrium_quantity_original"])
consumer_surplus_shifted, producer_surplus_shifted = calculate_surplus(
    st.session_state["demand_intercept"] + st.session_state["demand_shift"], st.session_state["supply_intercept"] + st.session_state["supply_shift"], st.session_state["equilibrium_price_shifted"], st.session_state["equilibrium_quantity_shifted"])



# --------  CREATE PLOT

st.markdown("<br>", unsafe_allow_html=True)
st.subheader(get_translation("GRAPHICAL_ANALYSIS_SUBHEADER"), divider="gray")

x = np.linspace(0, 20, 400)
fig, ax = plt.subplots()

# Plot original and shifted demand and supply curves
ax.plot(x, st.session_state["demand_slope"] * x + st.session_state["demand_intercept"], label=get_translation("DEMAND_LABEL"), color=demand_color)
ax.plot(x, st.session_state["supply_slope"] * x + st.session_state["supply_intercept"], label=get_translation("SUPPLY_LABEL"), color=supply_color)
if st.session_state["shift"]:    
    ax.plot(x, st.session_state["demand_slope"] * x + st.session_state["demand_intercept"] + st.session_state["demand_shift"], label=get_translation("DEMAND_SHIFTED_LABEL"), linestyle="dotted", color=demand_color)
    ax.plot(x, st.session_state["supply_slope"] * x + st.session_state["supply_intercept"] + st.session_state["supply_shift"], label=get_translation("SUPPLY_SHIFTED_LABEL"), linestyle="dotted", color=supply_color)

# Plot equilibrium points
ax.plot(st.session_state["equilibrium_quantity_original"], st.session_state["equilibrium_price_original"], marker="o", markersize=5, color=equilibrium_color)

if st.session_state["shift"]:
    ax.plot(st.session_state["equilibrium_quantity_shifted"], st.session_state["equilibrium_price_shifted"], marker="o", markersize=5, color=equilibrium_color)

# Plot surpluses if option is selected
if surplus_option == get_translation("SURPLUS_ORIGINAL") or surplus_option == get_translation("SURPLUS_BOTH"):
    # Original Consumer Surplus
    consumer_surplus_edges = [(0, st.session_state["demand_intercept"]), (st.session_state["equilibrium_quantity_original"], st.session_state["equilibrium_price_original"]), (0, st.session_state["equilibrium_price_original"])]
    patch_consumer_surplus = pt.Polygon(consumer_surplus_edges, closed=True, fill=True, edgecolor='none',facecolor=demand_color, alpha=alpha, label=get_translation("CONSUMER_SURPLUS_LABEL"))
    ax.add_patch(patch_consumer_surplus)
    # Original Producer Surplus
    producer_surplus_edges = [(0, st.session_state["supply_intercept"]), (st.session_state["equilibrium_quantity_original"], st.session_state["equilibrium_price_original"]), (0, st.session_state["equilibrium_price_original"])]
    patch_producer_surplus = pt.Polygon(producer_surplus_edges, closed=True, fill=True, edgecolor='none',facecolor=supply_color, alpha=alpha, label=get_translation("PRODUCER_SURPLUS_LABEL"))
    ax.add_patch(patch_producer_surplus)
if (surplus_option == get_translation("SURPLUS_SHIFTED") or surplus_option == get_translation("SURPLUS_BOTH")) and st.session_state["shift"]:
    # Shifted Consumer Surplus
    consumer_surplus_edges_shifted = [(0, st.session_state["demand_intercept"]+st.session_state["demand_shift"]), (st.session_state["equilibrium_quantity_shifted"], st.session_state["equilibrium_price_shifted"]), (0, st.session_state["equilibrium_price_shifted"])]
    patch_consumer_surplus_shifted = pt.Polygon(consumer_surplus_edges_shifted, closed=True, fill=True, edgecolor='none',facecolor=demand_color, alpha=alpha_shift, label=get_translation("CONSUMER_SURPLUS_SHIFTED_LABEL"))
    ax.add_patch(patch_consumer_surplus_shifted)
    # Shifted Producer Surplus
    producer_surplus_edges_shifted = [(0, st.session_state["supply_intercept"]+st.session_state["supply_shift"]), (st.session_state["equilibrium_quantity_shifted"], st.session_state["equilibrium_price_shifted"]), (0, st.session_state["equilibrium_price_shifted"])]
    patch_producer_surplus_shifted = pt.Polygon(producer_surplus_edges_shifted, closed=True, fill=True, edgecolor='none',facecolor=supply_color, alpha=alpha_shift, label=get_translation("PRODUCER_SURPLUS_SHIFTED_LABEL"))
    ax.add_patch(patch_producer_surplus_shifted)
if show_deadweight_loss:
    if st.session_state["equilibrium_mc_prosppay_newquantity"] != 0 and st.session_state["gov_intervention"]:
        deadweight_loss_shifted = [(st.session_state["equilibrium_quantity_shifted"], st.session_state["equilibrium_price_shifted"]), (st.session_state["equilibrium_quantity_original"], st.session_state["equilibrium_price_original"]), (st.session_state["equilibrium_quantity_shifted"], st.session_state["equilibrium_mc_prosppay_newquantity"])]
        patch_deadweight_loss = pt.Polygon(deadweight_loss_shifted, closed=True, fill=True, edgecolor='none',facecolor=deadweightloss_color, alpha=alpha_deadweight_loss, label=get_translation("DEADWEIGHT_LOSS_LABEL"))
        ax.add_patch(patch_deadweight_loss)
if show_gov:
    if st.session_state["equilibrium_mc_prosppay_newquantity"] != 0 and st.session_state["gov_intervention"]:
        if st.session_state["demand_shift"] != 0:
            gov_incexp = [(0, st.session_state["demand_intercept"]), (0, st.session_state["demand_intercept"] + st.session_state["demand_shift"]), (st.session_state["equilibrium_quantity_shifted"], st.session_state["equilibrium_price_shifted"]), (st.session_state["equilibrium_quantity_shifted"], st.session_state["equilibrium_mc_prosppay_newquantity"])]            
        if st.session_state["supply_shift"] != 0:
            gov_incexp = [(0, st.session_state["supply_intercept"]), (0, st.session_state["supply_intercept"] + st.session_state["supply_shift"]), (st.session_state["equilibrium_quantity_shifted"], st.session_state["equilibrium_price_shifted"]), (st.session_state["equilibrium_quantity_shifted"], st.session_state["equilibrium_mc_prosppay_newquantity"])]
        if st.session_state["demand_shift"] < 0 or st.session_state["supply_shift"] > 0:
            gov_color = gov_income_color
            gov_text = get_translation("GOV_INCOME_LABEL")
        else:
            gov_color = gov_expenses_color
            gov_text = get_translation("GOV_EXPENSES_LABEL")
        patch_gov = pt.Polygon(gov_incexp, closed=True, fill=True, edgecolor='none',facecolor=gov_color, alpha=alpha_gov, label=gov_text)
        ax.add_patch(patch_gov)

# Increase font size for axis labels and tick labels
plt.rcParams.update({'font.size': 14})

# Graph style
ax.set_xlabel(get_translation("QUANTITY_LABEL"), fontsize=16)
ax.set_ylabel(get_translation("PRICE_LABEL"), fontsize=16)
ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=14)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines['bottom'].set_position("zero")
ax.spines['left'].set_position("zero")
ax.xaxis.set_ticks_position("bottom")
ax.yaxis.set_ticks_position("left")
ax.set_ylim(bottom=0)

# Increase tick label font size
ax.tick_params(axis='both', which='major', labelsize=14)

# Set tick marks based on tickmark_width
ax.xaxis.set_major_locator(plt.MultipleLocator(st.session_state["tickmark_width"]))
ax.yaxis.set_major_locator(plt.MultipleLocator(st.session_state["tickmark_width"]))

# Set fixed axes if checkbox is checked
if st.session_state["fix_axes"]:
    ax.set_xlim(0, math.ceil(demand_intercept / ((-1)*demand_slope))+5)
    ax.set_ylim(0, math.ceil(demand_intercept)+5)
else:
    ax.set_xlim(0, math.ceil(max(st.session_state["demand_intercept"], st.session_state["demand_intercept"] + st.session_state["demand_shift"]) / ((-1)*st.session_state["demand_slope"]))+5)
    ax.set_ylim(0, math.ceil(max(st.session_state["demand_intercept"], st.session_state["demand_intercept"] + st.session_state["demand_shift"]))+5)

# Add gridlines if show_grid is True
if st.session_state["show_grid"]:
    ax.grid(True, linestyle=':', color='gray', alpha=0.8)

# Adjust the figure size to accommodate the legend
fig.set_size_inches(12, 8)
plt.tight_layout()

st.pyplot(fig)

# Add this section to display the AI comment in a yellow box
if st.session_state["use_ai"] and "ai_result" in st.session_state and st.session_state["ai_result"]["status"] == "okay":
    ai_comment = st.session_state["ai_result"].get("comment", "")
    if ai_comment:
        st.markdown(
            f"""
            <div style="background-color: #ffffd0; padding: 10px; border-radius: 5px; margin-top: 10px;">
                <strong>{get_translation("AI_COMMENT_LABEL")}</strong><br>
                {ai_comment}
            </div>
            """,
            unsafe_allow_html=True
        )

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
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader(get_translation("QUANT_RESULTS_SUBHEADER"), divider="gray")

    # Display equilibrium price and quantity
    st.markdown("#### " + get_translation("PRICES_LABEL"))
    outp = get_translation("EQUILIBRIUM_PRICE_ORIGINAL_LABEL") + " **" + str(round(st.session_state["equilibrium_price_original"], 2)) + "**"
    st.write(outp)
    if st.session_state["shift"]:
        outp = get_translation("EQUILIBRIUM_PRICE_SHIFTED_LABEL") + " **" + str(round(st.session_state["equilibrium_price_shifted"], 2)) + "**"
        st.write(outp)

    st.markdown("#### " + get_translation("QUANTITIES_LABEL"))
    outp = get_translation("EQUILIBRIUM_QUANTITY_ORIGINAL_LABEL") + " **" + str(round(st.session_state["equilibrium_quantity_original"], 2)) + "**"
    st.write(outp)
    if st.session_state["shift"]:
        outp = get_translation("EQUILIBRIUM_QUANTITY_SHIFTED_LABEL") + " **" + str(round(st.session_state["equilibrium_quantity_shifted"], 2)) + "**"
        st.write(outp)

    if surplus_option != get_translation("SURPLUS_NONE"):
        st.markdown("#### " + get_translation("CONSUMER_SURPLUS_LABEL"))
    if surplus_option == get_translation("SURPLUS_ORIGINAL") or surplus_option == get_translation("SURPLUS_BOTH"):
        outp = get_translation("CONSUMER_SURPLUS_ORIGINAL_LABEL") + " **" + str(round(consumer_surplus_original, 2)) + "**"
        st.write(outp)
    if (surplus_option == get_translation("SURPLUS_SHIFTED") or surplus_option == get_translation("SURPLUS_BOTH")) and st.session_state["shift"]:
        outp = get_translation("CONSUMER_SURPLUS_SHIFTED_LABEL") + " **" + str(round(consumer_surplus_shifted, 2)) + "**"
        st.write(outp)

    if surplus_option != get_translation("SURPLUS_NONE"):
        st.markdown("#### " + get_translation("PRODUCER_SURPLUS_LABEL"))
    if surplus_option == get_translation("SURPLUS_ORIGINAL") or surplus_option == get_translation("SURPLUS_BOTH"):
        outp = get_translation("PRODUCER_SURPLUS_ORIGINAL_LABEL") + " **" +  str(round(producer_surplus_original, 2)) + "**"
        st.write(outp)
    if (surplus_option == get_translation("SURPLUS_SHIFTED") or surplus_option == get_translation("SURPLUS_BOTH")) and st.session_state["shift"]:
        outp = get_translation("PRODUCER_SURPLUS_SHIFTED_LABEL") + " **" + str(round(producer_surplus_shifted, 2)) + "**"
        st.write(outp)

    if surplus_option != get_translation("SURPLUS_NONE"):
        st.markdown("#### " + get_translation("TOTAL_WELFARE_LABEL"))
    if surplus_option == get_translation("SURPLUS_ORIGINAL") or surplus_option == get_translation("SURPLUS_BOTH"):
        outp = get_translation("TOTAL_WELFARE_ORIGINAL_LABEL") + " **" + str(round(consumer_surplus_original + producer_surplus_original, 2)) + "**"
        st.write(outp)
    if (surplus_option == get_translation("SURPLUS_SHIFTED") or surplus_option == get_translation("SURPLUS_BOTH")) and st.session_state["shift"]:
        outp = get_translation("TOTAL_WELFARE_SHIFTED_LABEL") + " **" + str(round(consumer_surplus_shifted + producer_surplus_shifted, 2)) + "**"
        st.write(outp)


# Create inputs for demand and supply curves

st.sidebar.divider()

st.sidebar.header(get_translation("SETTINGS_HEADER"))


selected_flag = st.sidebar.selectbox(
    "Language / Sprache",
    options=list(language_flags.keys()),
    format_func=lambda x: language_flags[x],
    index=list(language_flags.keys()).index(st.session_state["language"]),
    key="language_selector",
    on_change=callback_language_change
)

# Add this check to force a rerun when the language changes
if "previous_language" not in st.session_state:
    st.session_state["previous_language"] = st.session_state["language"]
elif st.session_state["previous_language"] != st.session_state["language"]:
    st.session_state["previous_language"] = st.session_state["language"]
    st.rerun()

st.markdown("""
    <style>
    .streamlit-expanderHeader {
        font-size: 18px !important;
        font-weight: bold;
    }
    div[data-testid="stExpander"] div[role="button"] p {
        font-size: 18px !important;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

with st.sidebar.expander(get_translation("CURVE_PARAMS_EXPANDER")):
    st.text_input(get_translation("DEMAND_SLOPE_LABEL"), value=str(st.session_state["demand_slope"]), key="demand_slope_slider", on_change=callback_params)
    st.text_input(get_translation("DEMAND_INTERCEPT_LABEL"), value=str(st.session_state["demand_intercept"]), key="demand_intercept_slider", on_change=callback_params)
    st.text_input(get_translation("SUPPLY_SLOPE_LABEL"), value=str(st.session_state["supply_slope"]), key="supply_slope_slider", on_change=callback_params)
    st.text_input(get_translation("SUPPLY_INTERCEPT_LABEL"), value=str(st.session_state["supply_intercept"]), key="supply_intercept_slider", on_change=callback_params)
    st.button(get_translation("RESET_BUTTON"), on_click=callback_reset)

with st.sidebar.expander(get_translation("GRAPH_PARAMS_EXPANDER")):    
    st.checkbox(get_translation("FIX_AXES_CHECKBOX"), value=st.session_state["fix_axes"], key="fix_axes_checkbox", on_change=callback_params)
    st.checkbox(get_translation("SHOW_GRID_CHECKBOX"), value=st.session_state["show_grid"], key="show_grid_checkbox", on_change=callback_params)
    st.number_input(get_translation("TICKMARK_WIDTH_LABEL"), value=st.session_state["tickmark_width"], step=0.5, min_value=0.5, max_value=5.0, format="%.1f", key="tickmark_input", on_change=callback_params)

with st.sidebar.expander(get_translation("API_SETTINGS_EXPANDER")):
    user_api_key = st.text_input(
        get_translation("API_KEY_INPUT"),
        type="password",
        help=get_translation("API_KEY_HELP")
    )
    if user_api_key:
        st.session_state["user_api_key"] = user_api_key
    elif "user_api_key" in st.session_state:
        del st.session_state["user_api_key"]

with st.sidebar.expander(get_translation("ABOUT_EXPANDER")):
    st.write(get_translation("VERSION_LABEL"))