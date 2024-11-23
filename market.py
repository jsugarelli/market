# -------- IMPORTS --------

import streamlit as st
import numpy as np
import math
import matplotlib.pyplot as plt
import matplotlib.patches as pt
import json
import os
from config import *
from translations import translations, language_flags
from openai import OpenAI
from streamlit import secrets
from PIL import Image
import requests
import time

# ----------- OPENROUTER -----------

def query_openrouter(system_message, user_prompt, model_name, temperature=0.2, preferred_providers=None):
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    if "user_api_key" in st.session_state:
        user_api_key = st.session_state["user_api_key"]
    else:
        user_api_key = secrets["API_KEY"]

    headers = {
        "Authorization": f"Bearer {user_api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature
    }
    
    if preferred_providers:
        data["providers"] = preferred_providers
    
    try:
        start_time = time.time()
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        end_time = time.time()
        
        result = response.json()
        response_text = result['choices'][0]['message']['content']
        generation_time = end_time - start_time
        
        return response_text, generation_time
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return "", 0



# -------- TITLE --------

# Initialize language
if "language" not in st.session_state:
    st.session_state["language"] = default_language

# Add this function to get translations
def get_translation(key):
    return translations[st.session_state["language"]].get(key, key)

# Set the page config after initializing language and defining get_translation
st.set_page_config(page_title=get_translation("TITLE"))

if 'disclaimer_confirmed' not in st.session_state:
    st.session_state.disclaimer_confirmed = False

# Display disclaimer if not yet confirmed and disclaimer_text is not empty
if not st.session_state.disclaimer_confirmed and disclaimer_text != "":
    disclaimer_container = st.container()
    with disclaimer_container:
        st.markdown(
            f"""
            <div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 20px">
                {disclaimer_text}
            </div>
            """,
            unsafe_allow_html=True
        )
        
        if ask_confirmation:
            if st.checkbox(get_translation("CONFIRM_CHECKBOX")):
                st.session_state.disclaimer_confirmed = True
                st.rerun()

# Display logo if file exists
try:
    if os.path.exists(logo):
        desired_height = 60
        if "max_logo_height" in globals():
            try:
                if isinstance(max_logo_height, (int, float)) and max_logo_height > 0:
                    desired_height = max_logo_height
            except:
                pass
        
        # Load image and calculate dimensions
        img = Image.open(logo)
        aspect_ratio = img.size[0] / img.size[1]  # width / height
        desired_width = int(desired_height * aspect_ratio)
        
        # Create three columns with wider side columns for better centering
        left_col, center_col, right_col = st.columns([2, 1, 2])
        with center_col:
            st.image(logo, width=desired_width)
except:
    pass

# Create Streamlit application
st.title(get_translation("TITLE"))
st.markdown("<br>", unsafe_allow_html=True)



# -------- CONFIGURATION AND SETUP --------

# Check if OPENAI_API_KEY is in secrets
if "API_KEY" in st.secrets:
    client = OpenAI(api_key=st.secrets["API_KEY"])    



# -------- SESSION STATE INITIALIZATION --------

if "loaded" not in st.session_state:        
    st.session_state["demand_slope"] = demand_slope
    st.session_state["demand_intercept"] = demand_intercept
    st.session_state["supply_slope"] = supply_slope
    st.session_state["supply_intercept"] = supply_intercept
    st.session_state["demand_shift"] = 0
    st.session_state["supply_shift"] = 0
    st.session_state["shift"] = False
    st.session_state["equilibrium_quantity_original"] = (st.session_state["demand_intercept"] - st.session_state["supply_intercept"]) / (st.session_state["supply_slope"] - st.session_state["demand_slope"])
    st.session_state["equilibrium_quantity_modified"] = 0
    st.session_state["equilibrium_price_original"] = st.session_state["demand_intercept"] + st.session_state["demand_slope"] * st.session_state["equilibrium_quantity_original"]
    st.session_state["equilibrium_price_modified"] = 0
    st.session_state["equilibrium_mc_prosppay_newquantity"] = 0
    st.session_state["elasticity_demand"] = -(st.session_state["demand_slope"] * 
                                           st.session_state["equilibrium_price_original"] / 
                                           st.session_state["equilibrium_quantity_original"])
    st.session_state["elasticity_supply"] = (st.session_state["supply_slope"] * 
                                           st.session_state["equilibrium_price_original"] / 
                                           st.session_state["equilibrium_quantity_original"])
    st.session_state["gov_intervention"] = False
    st.session_state["gallery_selected"] = "(bitte wählen)"
    st.session_state["max_price"] = 0
    st.session_state["min_price"] = 0
    st.session_state["limit_price"] = 0
    st.session_state["limit_quantity"] = 0    
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
    st.session_state["mode"]= "shift"
    st.session_state["line_thickness"] = 2.0
    st.session_state["loaded"] = True



# -------- HELPER FUNCTIONS --------

# Mode changes
def mode_shifts():    
    st.session_state["mode"] = "shift"
    st.session_state["max_price"] = 0
    st.session_state["min_price"] = 0
    st.session_state["limit_price"] = 0
    st.session_state["limit_quantity"] = 0

def mode_pricelimits():
    st.session_state["mode"] = "pricelimits"    
    st.session_state["demand_shift"] = 0
    st.session_state["supply_shift"] = 0
    st.session_state["shift"] = False
    st.session_state["gov_intervention"] = False
    st.session_state["equilibrium_quantity_modified"] = 0        
    st.session_state["equilibrium_price_modified"] = 0
    st.session_state["equilibrium_mc_prosppay_newquantity"] = 0

# Call the API
def call_openrouter_api(user_input):
    try:                
        response_text, generation_time = query_openrouter(
            system_message=ai_system_message.replace("<LANGUAGE>", st.session_state["language"]),
            user_prompt=user_input,
            model_name=ai_model,
            temperature=ai_temperature
        )
        
        print("Raw API response:", response_text)  # Debug print
        return response_text
    except Exception as e:
        print(f"Error in API call: {str(e)}")  # Debug print
        error_message = get_translation("API_ERROR_WARNING")
        st.warning(f"{error_message}: {str(e)}")
        return f"Error: {str(e)}"

# Parse the API response
def parse_api_response(response):
    try:
        result = json.loads(response)
    except json.JSONDecodeError:
        lines = response.strip().split('\n')
        result = {}
        for line in lines:
            parts = line.split(':', 1)
            if len(parts) == 2:
                key, value = parts
                result[key.strip()] = value.strip()    
    
    try:
        return {
            "status": result.get("status", "okay"),
            "shift_demand": float(result.get("shift_demand", 0) or 0),
            "shift_supply": float(result.get("shift_supply", 0) or 0),
            "gov_intervention": bool(result.get("gov_intervention", "False"))   ,
            "comment": result.get("comment", "")
        }
    except Exception as e:
        print(f"Error extracting values from parsed result: {str(e)}")
        comment = ""
        return {"status": "error", "message": str(e), "comment": comment}



# -------- CALLBACK FUNCTIONS --------

def callback_shifts():    
    mode_shifts()
    st.session_state["demand_shift"] = float(st.session_state.slider1)
    st.session_state["supply_shift"] = float(st.session_state.slider2)
    st.session_state["shift"] = st.session_state["demand_shift"] != 0 or st.session_state["supply_shift"] != 0
    st.session_state["gallery_selected"] = "(bitte wählen)"    

def callback_params():
    st.session_state["demand_slope"] = float(st.session_state.demand_slope_slider)
    st.session_state["demand_intercept"] = float(st.session_state.demand_intercept_slider)
    st.session_state["supply_slope"] = float(st.session_state.supply_slope_slider)
    st.session_state["supply_intercept"] = float(st.session_state.supply_intercept_slider)
    st.session_state["elasticity_demand"] = (st.session_state["demand_slope"] * 
                                           st.session_state["equilibrium_price_original"] / 
                                           st.session_state["equilibrium_quantity_original"])
    st.session_state["elasticity_supply"] = (st.session_state["supply_slope"] * 
                                           st.session_state["equilibrium_price_original"] / 
                                           st.session_state["equilibrium_quantity_original"])
    st.session_state["fix_axes"] = st.session_state.fix_axes_checkbox
    st.session_state["show_grid"] = st.session_state.show_grid_checkbox
    st.session_state["tickmark_width"] = st.session_state.tickmark_input
    st.session_state["line_thickness"] = float(st.session_state.line_thickness_input)

def callback_reset():
    st.session_state["demand_slope"] = demand_slope
    st.session_state["demand_intercept"] = demand_intercept
    st.session_state["supply_slope"] = supply_slope
    st.session_state["supply_intercept"] = supply_intercept
    st.session_state["line_thickness"] = 2.0    
    st.session_state["equilibrium_quantity_original"] = (st.session_state["demand_intercept"] - st.session_state["supply_intercept"]) / (st.session_state["supply_slope"] - st.session_state["demand_slope"])
    st.session_state["equilibrium_price_original"] = st.session_state["demand_intercept"] + st.session_state["demand_slope"] * st.session_state["equilibrium_quantity_original"]
    st.session_state["elasticity_demand"] = (st.session_state["demand_slope"] * 
                                           st.session_state["equilibrium_price_original"] / 
                                           st.session_state["equilibrium_quantity_original"])
    st.session_state["elasticity_supply"] = (st.session_state["supply_slope"] * 
                                           st.session_state["equilibrium_price_original"] / 
                                           st.session_state["equilibrium_quantity_original"])

def callback_gov():
    st.session_state["gov_intervention"] = not st.session_state["gov_intervention"]
    st.session_state["gallery_selected"] = "(bitte wählen)"
    
def callback_scenarios():    
    mode_shifts()
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
        st.session_state["equilibrium_quantity_modified"] = 0        
        st.session_state["equilibrium_price_modified"] = 0
        st.session_state["equilibrium_mc_prosppay_newquantity"] = 0
    
def callback_language_change():
    st.session_state["language"] = st.session_state["language_selector"]

def callback_pricelimits():
    if (st.session_state.hoechstpreis > 0 and st.session_state.mindestpreis == 0) or (st.session_state.hoechstpreis == 0 and st.session_state.mindestpreis > 0):
        mode_pricelimits()
        st.session_state["max_price"] = st.session_state.hoechstpreis
        st.session_state["min_price"] = st.session_state.mindestpreis
        if st.session_state["max_price"] > 0:
            st.session_state["limit_price"] = st.session_state["max_price"]
        if st.session_state["min_price"] > 0:
            st.session_state["limit_price"] = st.session_state["min_price"]

def callback_elasticity_demand():
    new_elasticity = float(st.session_state.elasticity_demand_slider)
    st.session_state["demand_slope"] = -new_elasticity * st.session_state["equilibrium_quantity_original"] / st.session_state["equilibrium_price_original"]
    st.session_state["demand_intercept"] = (st.session_state["supply_intercept"] + 
                                          st.session_state["supply_slope"] * st.session_state["equilibrium_quantity_original"] - 
                                          st.session_state["demand_slope"] * st.session_state["equilibrium_quantity_original"])
    st.session_state["elasticity_demand"] = new_elasticity

def callback_elasticity_supply():
    new_elasticity = float(st.session_state.elasticity_supply_slider)
    st.session_state["supply_slope"] = new_elasticity * st.session_state["equilibrium_quantity_original"] / st.session_state["equilibrium_price_original"]
    st.session_state["supply_intercept"] = (st.session_state["demand_intercept"] + 
                                          st.session_state["demand_slope"] * st.session_state["equilibrium_quantity_original"] - 
                                          st.session_state["supply_slope"] * st.session_state["equilibrium_quantity_original"])
    st.session_state["elasticity_supply"] = new_elasticity



# -------- UI COMPONENTS I OF II --------

# Create tabs for controls
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
        hoechstpreis = st.number_input(get_translation("MAX_PRICE"), value=0.0, step=0.1, format="%.2f", key="hoechstpreis", on_change=callback_pricelimits)
    with col2:
        mindestpreis = st.number_input(get_translation("MIN_PRICE"), value=0.0, step=0.1, format="%.2f", key="mindestpreis", on_change=callback_pricelimits)

    if hoechstpreis != 0 and mindestpreis != 0:
        st.warning(get_translation("PRICE_LIMITS_WARNING"))

    if mindestpreis != 0  and mindestpreis < st.session_state["equilibrium_price_original"]:
        st.warning(get_translation("MIN_PRICE_WARNING").format(st.session_state["equilibrium_price_original"]))

    if hoechstpreis != 0 and hoechstpreis > st.session_state["equilibrium_price_original"]:
        st.warning(get_translation("MAX_PRICE_WARNING").format(st.session_state["equilibrium_price_original"]))

if st.session_state["use_gallery"]:
    if st.session_state["has_gallery"]:    
        with tabs[2]:
            gallery_entry_names = ["(bitte wählen)"] + [s for s in st.session_state["gallery_entries"].keys()]
            st.write(get_translation("SCENARIOS_INSTRUCTIONS"))
            gallery_option = st.selectbox(label=get_translation("SCENARIOS_LABEL"), label_visibility="hidden", options = gallery_entry_names, on_change=callback_scenarios, key="gallery_choice", index = gallery_entry_names.index(st.session_state["gallery_selected"]))


# Modify the AI tab content
if st.session_state["use_ai"]:
    with tabs[-1]:
        st.write(get_translation("AI_INSTRUCTIONS"))
        
        # Add example scenario description in a box
        st.markdown(
            f"""
            <div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
                <strong>{get_translation("EXAMPLE_SCENARIO_LABEL")}</strong><br>
                {get_translation("EXAMPLE_SCENARIO_TEXT")}
            </div>
            """,
            unsafe_allow_html=True
        )
        
        user_input = st.text_area(get_translation("AI_INPUT_LABEL"), height=150)
        if st.button(get_translation("ANALYZE_BUTTON")):
            with st.spinner(get_translation("ANALYZING_MESSAGE")):
                api_response = call_openrouter_api(user_input)
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


# Sidebar components
st.sidebar.header(get_translation("DISPLAY_HEADER"))

# Create option to show surpluses
st.sidebar.subheader(get_translation("SURPLUS_SUBHEADER"))
surplus_option = st.sidebar.radio(label="", options=(get_translation("SURPLUS_NONE"), get_translation("SURPLUS_ORIGINAL"), get_translation("SURPLUS_SHIFTED"), get_translation("SURPLUS_BOTH")), label_visibility="collapsed")

st.sidebar.subheader(get_translation("GOV_SURPLUS_SUBHEADER"))
show_gov = st.sidebar.checkbox(get_translation("SHOW_GOV_CHECKBOX"))
if show_gov and not st.session_state["gov_intervention"]:
    st.sidebar.warning(get_translation("GOV_INTERVENTION_WARNING"))

st.sidebar.subheader(get_translation("DEADWEIGHT_LOSS_SUBHEADER"))
show_deadweight_loss = st.sidebar.checkbox(get_translation("SHOW_DEADWEIGHT_LOSS_CHECKBOX"))
if show_deadweight_loss and not st.session_state["gov_intervention"]:
    st.sidebar.warning(get_translation("GOV_INTERVENTION_WARNING"))

st.sidebar.subheader(get_translation("QUANTITATIVE_RESULTS_SUBHEADER"))
show_quant_results = st.sidebar.checkbox(get_translation("SHOW_QUANT_RESULTS_CHECKBOX"))



# -------- CALCULATIONS

# Equilibrium price and quantity before changes
st.session_state["equilibrium_quantity_original"] = (st.session_state["demand_intercept"] - st.session_state["supply_intercept"]) / (st.session_state["supply_slope"] - st.session_state["demand_slope"])
st.session_state["equilibrium_price_original"] = st.session_state["demand_intercept"] + st.session_state["demand_slope"] * st.session_state["equilibrium_quantity_original"]

# Equilibrium price and quantity after shifts
if st.session_state["shift"]:
    st.session_state["equilibrium_quantity_modified"] = (st.session_state["demand_intercept"] + st.session_state["demand_shift"] - (st.session_state["supply_intercept"] + st.session_state["supply_shift"])) / (st.session_state["supply_slope"] - st.session_state["demand_slope"])
    st.session_state["equilibrium_price_modified"] = st.session_state["demand_intercept"] + st.session_state["demand_shift"]  + st.session_state["demand_slope"] * st.session_state["equilibrium_quantity_modified"]
    if st.session_state["demand_shift"] != 0 and st.session_state["supply_shift"] == 0:
        st.session_state["equilibrium_mc_prosppay_newquantity"] = st.session_state["demand_intercept"] + st.session_state["demand_slope"] * st.session_state["equilibrium_quantity_modified"]
    elif st.session_state["demand_shift"] == 0 and st.session_state["supply_shift"] != 0:
        st.session_state["equilibrium_mc_prosppay_newquantity"] = st.session_state["supply_intercept"] + st.session_state["supply_slope"] * st.session_state["equilibrium_quantity_modified"]
    else:
        st.session_state["equilibrium_mc_prosppay_newquantity"] = 0

# Equilibrium price and quantity after min/max price
if st.session_state["mode"] == "pricelimits":    
    if(st.session_state["min_price"]) > 0:
        st.session_state["limit_quantity"] = (st.session_state["limit_price"] - st.session_state["demand_intercept"]) / st.session_state["demand_slope"]
    if(st.session_state["max_price"]) > 0:
        st.session_state["limit_quantity"] = (st.session_state["limit_price"] - st.session_state["supply_intercept"]) / st.session_state["supply_slope"]
    st.session_state["equilibrium_quantity_modified"] = st.session_state["limit_quantity"]
    st.session_state["equilibrium_price_modified"] = st.session_state["limit_price"]

# Surplus areas before/after shifts
def calculate_surplus_shifts(demand_intercept, supply_intercept, equilibrium_price, equilibrium_quantity):
    consumer_surplus = 0.5 * (demand_intercept - equilibrium_price) * equilibrium_quantity
    producer_surplus = 0.5 * (equilibrium_price - supply_intercept) * equilibrium_quantity
    return consumer_surplus, producer_surplus

# Surplus areas after min/max prices
def calculate_surplus_limits(demand_intercept, supply_intercept, demand_slope, supply_slope, limit_price, limit_quantity, equilibrium_price):
    if limit_price < equilibrium_price:
        demand_price = (demand_intercept - demand_slope * limit_quantity)
        supply_price = limit_price
    else:
        demand_price = limit_price
        supply_price = supply_intercept + supply_slope * limit_quantity

    base_consumer_surplus = 0.5*(demand_intercept - demand_price)
    base_producer_surplus = 0.5*(supply_price - supply_intercept)        
    distrib_surplus = (demand_price - supply_price) * limit_quantity
	
    if limit_price < equilibrium_price:
        consumer_surplus = base_consumer_surplus
        producer_surplus = base_producer_surplus + distrib_surplus
    else:
        consumer_surplus = base_consumer_surplus + distrib_surplus
        producer_surplus = base_producer_surplus

    return consumer_surplus, producer_surplus

# Call calculation of surpluses
consumer_surplus_original, producer_surplus_original = calculate_surplus_shifts(
    st.session_state["demand_intercept"], st.session_state["supply_intercept"], st.session_state["equilibrium_price_original"], st.session_state["equilibrium_quantity_original"])
if st.session_state["shift"]:
    consumer_surplus_modified, producer_surplus_modified = calculate_surplus_shifts(
        st.session_state["demand_intercept"] + st.session_state["demand_shift"], st.session_state["supply_intercept"] + st.session_state["supply_shift"], st.session_state["equilibrium_price_modified"], st.session_state["equilibrium_quantity_modified"])
if st.session_state["mode"] == "pricelimits":    
    consumer_surplus_modified, producer_surplus_modified = calculate_surplus_limits(
        st.session_state["demand_intercept"], st.session_state["supply_intercept"], st.session_state["demand_slope"], st.session_state["supply_slope"], st.session_state["limit_price"], st.session_state["limit_quantity"], st.session_state["equilibrium_price_original"])



# -------- PLOTTING: SETUP --------

# Create plot
st.markdown("<br>", unsafe_allow_html=True)
st.subheader(get_translation("GRAPHICAL_ANALYSIS_SUBHEADER"), divider="gray")

x = np.linspace(0, 20, 400)
fig, ax = plt.subplots()

# Increase font size for axis labels and tick labels
plt.rcParams.update({'font.size': 14})

# Graph style
ax.set_xlabel(get_translation("QUANTITY_LABEL"), fontsize=16)
ax.set_ylabel(get_translation("PRICE_LABEL"), fontsize=16)
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

# Add legend to the right center of the graph
ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=16)



# -------- PLOTTING: CONTENT --------

# Plot original and shifted demand and supply curves
demand_line, = ax.plot(x, st.session_state["demand_slope"] * x + st.session_state["demand_intercept"], label=get_translation("DEMAND_LABEL"), color=demand_color, linewidth=st.session_state["line_thickness"])
supply_line, = ax.plot(x, st.session_state["supply_slope"] * x + st.session_state["supply_intercept"], label=get_translation("SUPPLY_LABEL"), color=supply_color, linewidth=st.session_state["line_thickness"])

legend_elements = [demand_line, supply_line]

if st.session_state["shift"]:    
    demand_shifted, = ax.plot(x, st.session_state["demand_slope"] * x + st.session_state["demand_intercept"] + st.session_state["demand_shift"], label=get_translation("DEMAND_SHIFTED_LABEL"), linestyle="dotted", color=demand_color, linewidth=st.session_state["line_thickness"])
    supply_shifted, = ax.plot(x, st.session_state["supply_slope"] * x + st.session_state["supply_intercept"] + st.session_state["supply_shift"], label=get_translation("SUPPLY_SHIFTED_LABEL"), linestyle="dotted", color=supply_color, linewidth=st.session_state["line_thickness"])
    legend_elements.extend([demand_shifted, supply_shifted])

# Plot equilibrium points before changes
ax.plot(st.session_state["equilibrium_quantity_original"], st.session_state["equilibrium_price_original"], marker="o", markersize=5, color=equilibrium_color)

# Plot equilibrium points after shifts
if st.session_state["shift"]:
    ax.plot(st.session_state["equilibrium_quantity_modified"], st.session_state["equilibrium_price_modified"], marker="o", markersize=5, color=equilibrium_color)

# Plot equilibrium points after min/max prices
if st.session_state["mode"] == "pricelimits":
    ax.plot([0, st.session_state["limit_quantity"]], 
            [st.session_state["limit_price"], st.session_state["limit_price"]], 
            color='gray', linestyle=':', linewidth=2)
    ax.plot([st.session_state["limit_quantity"], st.session_state["limit_quantity"]], 
            [st.session_state["limit_price"], 0], 
            color='gray', linestyle=':', linewidth=2)

# Plot original surpluses depending on view options
if surplus_option == get_translation("SURPLUS_ORIGINAL") or surplus_option == get_translation("SURPLUS_BOTH"):
    
    # Original consumer surplus
    consumer_surplus_edges = [(0, st.session_state["demand_intercept"]), (st.session_state["equilibrium_quantity_original"], st.session_state["equilibrium_price_original"]), (0, st.session_state["equilibrium_price_original"])]
    patch_consumer_surplus = pt.Polygon(consumer_surplus_edges, closed=True, fill=True, edgecolor='none',facecolor=demand_color, alpha=alpha, label=get_translation("CONSUMER_SURPLUS_LABEL"))
    ax.add_patch(patch_consumer_surplus)
    legend_elements.append(patch_consumer_surplus)
    
    # Original producer surplus
    producer_surplus_edges = [(0, st.session_state["supply_intercept"]), (st.session_state["equilibrium_quantity_original"], st.session_state["equilibrium_price_original"]), (0, st.session_state["equilibrium_price_original"])]
    patch_producer_surplus = pt.Polygon(producer_surplus_edges, closed=True, fill=True, edgecolor='none',facecolor=supply_color, alpha=alpha, label=get_translation("PRODUCER_SURPLUS_LABEL"))
    ax.add_patch(patch_producer_surplus)
    legend_elements.append(patch_producer_surplus)

# Plot welfare after shifts depending on view options
if st.session_state["mode"] == "shift" :
    if (surplus_option == get_translation("SURPLUS_SHIFTED") or surplus_option == get_translation("SURPLUS_BOTH")) and st.session_state["shift"]:
        
        # Consumer surplus after shifts
        consumer_surplus_edges_shifted = [(0, st.session_state["demand_intercept"]+st.session_state["demand_shift"]), (st.session_state["equilibrium_quantity_modified"], st.session_state["equilibrium_price_modified"]), (0, st.session_state["equilibrium_price_modified"])]
        patch_consumer_surplus_shifted = pt.Polygon(consumer_surplus_edges_shifted, closed=True, fill=True, edgecolor='none',facecolor=demand_color, alpha=alpha_shift, label=get_translation("CONSUMER_SURPLUS_SHIFTED_LABEL"))
        ax.add_patch(patch_consumer_surplus_shifted)
        legend_elements.append(patch_consumer_surplus_shifted)
        
        # Producer surplus
        producer_surplus_edges_shifted = [(0, st.session_state["supply_intercept"]+st.session_state["supply_shift"]), (st.session_state["equilibrium_quantity_modified"], st.session_state["equilibrium_price_modified"]), (0, st.session_state["equilibrium_price_modified"])]
        patch_producer_surplus_shifted = pt.Polygon(producer_surplus_edges_shifted, closed=True, fill=True, edgecolor='none',facecolor=supply_color, alpha=alpha_shift, label=get_translation("PRODUCER_SURPLUS_SHIFTED_LABEL"))
        ax.add_patch(patch_producer_surplus_shifted)
        legend_elements.append(patch_producer_surplus_shifted)

    # Deadweight loss
    if show_deadweight_loss:
        if st.session_state["equilibrium_mc_prosppay_newquantity"] != 0 and st.session_state["gov_intervention"]:
            deadweight_loss_shifted = [(st.session_state["equilibrium_quantity_modified"], st.session_state["equilibrium_price_modified"]), (st.session_state["equilibrium_quantity_original"], st.session_state["equilibrium_price_original"]), (st.session_state["equilibrium_quantity_modified"], st.session_state["equilibrium_mc_prosppay_newquantity"])]
            patch_deadweight_loss = pt.Polygon(deadweight_loss_shifted, closed=True, fill=True, edgecolor='none',facecolor=deadweightloss_color, alpha=alpha_deadweight_loss, label=get_translation("DEADWEIGHT_LOSS_LABEL"))
            ax.add_patch(patch_deadweight_loss)
            legend_elements.append(patch_deadweight_loss)

    # Plot government surplus after shifts depending on view options
    if show_gov:
        if st.session_state["equilibrium_mc_prosppay_newquantity"] != 0 and st.session_state["gov_intervention"]:
            if st.session_state["demand_shift"] != 0:
                gov_incexp = [(0, st.session_state["demand_intercept"]), (0, st.session_state["demand_intercept"] + st.session_state["demand_shift"]), (st.session_state["equilibrium_quantity_modified"], st.session_state["equilibrium_price_modified"]), (st.session_state["equilibrium_quantity_modified"], st.session_state["equilibrium_mc_prosppay_newquantity"])]            
            if st.session_state["supply_shift"] != 0:
                gov_incexp = [(0, st.session_state["supply_intercept"]), (0, st.session_state["supply_intercept"] + st.session_state["supply_shift"]), (st.session_state["equilibrium_quantity_modified"], st.session_state["equilibrium_price_modified"]), (st.session_state["equilibrium_quantity_modified"], st.session_state["equilibrium_mc_prosppay_newquantity"])]
            if st.session_state["demand_shift"] < 0 or st.session_state["supply_shift"] > 0:
                gov_color = gov_income_color
                gov_text = get_translation("GOV_INCOME_LABEL")
            else:
                gov_color = gov_expenses_color
                gov_text = get_translation("GOV_EXPENSES_LABEL")
            patch_gov = pt.Polygon(gov_incexp, closed=True, fill=True, edgecolor='none',facecolor=gov_color, alpha=alpha_gov, label=gov_text)
            ax.add_patch(patch_gov)
            legend_elements.append(patch_gov)

# Plot welfare after min/max prices depending on view options
if st.session_state["mode"] == "pricelimits":
    
    # Plot shifted surpluses after min/max prices
    if surplus_option == get_translation("SURPLUS_SHIFTED") or surplus_option == get_translation("SURPLUS_BOTH"):
        if st.session_state["limit_price"] < st.session_state["equilibrium_price_original"]:
            consumer_surplus_edges_limits = [(0, st.session_state["demand_intercept"]), (0, st.session_state["limit_price"]), (st.session_state["limit_quantity"], st.session_state["limit_price"]), (st.session_state["limit_quantity"], st.session_state["demand_intercept"] + st.session_state["demand_slope"] * st.session_state["limit_quantity"])]
            producer_surplus_edges_limits = [(0, st.session_state["supply_intercept"]), (0, st.session_state["limit_price"]), (st.session_state["limit_quantity"], st.session_state["limit_price"])]
        else:
            consumer_surplus_edges_limits = [(0, st.session_state["demand_intercept"]), (0, st.session_state["limit_price"]), (st.session_state["limit_quantity"], st.session_state["limit_price"])]
            producer_surplus_edges_limits = [(0, st.session_state["limit_price"]), (st.session_state["limit_quantity"], st.session_state["limit_price"]), (st.session_state["limit_quantity"], st.session_state["supply_intercept"] + st.session_state["supply_slope"] * st.session_state["limit_quantity"]), (0, st.session_state["supply_intercept"])]
        patch_consumer_surplus_limits = pt.Polygon(consumer_surplus_edges_limits, closed=True, fill=True, edgecolor='none',facecolor=demand_color, alpha=alpha_shift, label=get_translation("CONSUMER_SURPLUS_SHIFTED_LABEL"))
        ax.add_patch(patch_consumer_surplus_limits)
        legend_elements.append(patch_consumer_surplus_limits)
        patch_producer_surplus_limits = pt.Polygon(producer_surplus_edges_limits, closed=True, fill=True, edgecolor='none',facecolor=supply_color, alpha=alpha_shift, label=get_translation("PRODUCER_SURPLUS_SHIFTED_LABEL"))
        ax.add_patch(patch_producer_surplus_limits)
        legend_elements.append(patch_producer_surplus_limits)
    
    # Plot deadweight loss after min/max prices
    if show_deadweight_loss:
        if st.session_state["limit_price"] < st.session_state["equilibrium_price_original"]:
            deadweight_loss_imits = [(st.session_state["equilibrium_quantity_original"], st.session_state["equilibrium_price_original"]), (st.session_state["limit_quantity"], st.session_state["limit_price"]), (st.session_state["limit_quantity"], st.session_state["demand_intercept"] + st.session_state["demand_slope"] * st.session_state["limit_quantity"])]
        else:
            deadweight_loss_imits = [(st.session_state["equilibrium_quantity_original"], st.session_state["equilibrium_price_original"]), (st.session_state["limit_quantity"], st.session_state["limit_price"]), (st.session_state["limit_quantity"], st.session_state["supply_intercept"] + st.session_state["supply_slope"] * st.session_state["limit_quantity"])]
        patch_deadweight_loss = pt.Polygon(deadweight_loss_imits, closed=True, fill=True, edgecolor='none',facecolor=deadweightloss_color, alpha=alpha_deadweight_loss, label=get_translation("DEADWEIGHT_LOSS_LABEL"))
        ax.add_patch(patch_deadweight_loss)
        legend_elements.append(patch_deadweight_loss)

# Add the legend to the right center of the graph
ax.legend(handles=legend_elements, loc='center left', bbox_to_anchor=(1, 0.5), fontsize=16)

st.pyplot(fig)


# -------- TEXTUAL COMMENTS --------

# Display the AI comment in a yellow box
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

# Display the pre-defined model comment for scenarios from the gallery
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



# -------- QUANTITATIVE RESULTS --------

if show_quant_results:
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader(get_translation("QUANT_RESULTS_SUBHEADER"), divider="gray")

    # Display equilibrium price and quantity
    st.markdown("#### " + get_translation("PRICES_LABEL"))
    outp = get_translation("EQUILIBRIUM_PRICE_ORIGINAL_LABEL") + " **" + str(round(st.session_state["equilibrium_price_original"], 2)) + "**"
    st.write(outp)
    if (st.session_state["mode"] == "shift" and st.session_state["shift"]) or st.session_state["mode"]=="pricelimits":
        outp = get_translation("EQUILIBRIUM_PRICE_SHIFTED_LABEL") + " **" + str(round(st.session_state["equilibrium_price_modified"], 2)) + "**"
        st.write(outp)

    st.markdown("#### " + get_translation("QUANTITIES_LABEL"))
    outp = get_translation("EQUILIBRIUM_QUANTITY_ORIGINAL_LABEL") + " **" + str(round(st.session_state["equilibrium_quantity_original"], 2)) + "**"
    st.write(outp)
    if (st.session_state["mode"] == "shift" and st.session_state["shift"]) or st.session_state["mode"]=="pricelimits":
        outp = get_translation("EQUILIBRIUM_QUANTITY_SHIFTED_LABEL") + " **" + str(round(st.session_state["equilibrium_quantity_modified"], 2)) + "**"
        st.write(outp)

    if surplus_option != get_translation("SURPLUS_NONE"):
        st.markdown("#### " + get_translation("CONSUMER_SURPLUS_LABEL"))
    if surplus_option == get_translation("SURPLUS_ORIGINAL") or surplus_option == get_translation("SURPLUS_BOTH"):
        outp = get_translation("CONSUMER_SURPLUS_ORIGINAL_LABEL") + " **" + str(round(consumer_surplus_original, 2)) + "**"
        st.write(outp)
    if (surplus_option == get_translation("SURPLUS_SHIFTED") or surplus_option == get_translation("SURPLUS_BOTH")) and ((st.session_state["mode"] == "shift" and st.session_state["shift"]) or st.session_state["mode"]=="pricelimits"):
        outp = get_translation("CONSUMER_SURPLUS_SHIFTED_LABEL") + " **" + str(round(consumer_surplus_modified, 2)) + "**"
        st.write(outp)

    if surplus_option != get_translation("SURPLUS_NONE"):
        st.markdown("#### " + get_translation("PRODUCER_SURPLUS_LABEL"))
    if surplus_option == get_translation("SURPLUS_ORIGINAL") or surplus_option == get_translation("SURPLUS_BOTH"):
        outp = get_translation("PRODUCER_SURPLUS_ORIGINAL_LABEL") + " **" +  str(round(producer_surplus_original, 2)) + "**"
        st.write(outp)
    if (surplus_option == get_translation("SURPLUS_SHIFTED") or surplus_option == get_translation("SURPLUS_BOTH")) and ((st.session_state["mode"] == "shift" and st.session_state["shift"]) or st.session_state["mode"]=="pricelimits"):
        outp = get_translation("PRODUCER_SURPLUS_SHIFTED_LABEL") + " **" + str(round(producer_surplus_modified, 2)) + "**"
        st.write(outp)

    if surplus_option != get_translation("SURPLUS_NONE"):
        st.markdown("#### " + get_translation("TOTAL_WELFARE_LABEL"))
    if surplus_option == get_translation("SURPLUS_ORIGINAL") or surplus_option == get_translation("SURPLUS_BOTH"):
        outp = get_translation("TOTAL_WELFARE_ORIGINAL_LABEL") + " **" + str(round(consumer_surplus_original + producer_surplus_original, 2)) + "**"
        st.write(outp)
    if (surplus_option == get_translation("SURPLUS_SHIFTED") or surplus_option == get_translation("SURPLUS_BOTH")) and ((st.session_state["mode"]=="shift" and st.session_state["shift"]) or st.session_state["mode"]=="pricelimits"):
        outp = get_translation("TOTAL_WELFARE_SHIFTED_LABEL") + " **" + str(round(consumer_surplus_modified + producer_surplus_modified, 2)) + "**"
        st.write(outp)




# -------- SETTINGS IN SIDEBAR--------

st.sidebar.divider()
st.sidebar.header(get_translation("SETTINGS_HEADER"))

# Settings for language

selected_flag = st.sidebar.selectbox(
    "Language / Sprache",
    options=list(language_flags.keys()),
    format_func=lambda x: language_flags[x],
    index=list(language_flags.keys()).index(st.session_state["language"]),
    key="language_selector",
    on_change=callback_language_change
)

# Force a rerun when the language changes
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

# Settings for demand and supply curves
with st.sidebar.expander(get_translation("CURVE_PARAMS_EXPANDER")):
    st.text_input(get_translation("DEMAND_SLOPE_LABEL"), value=str(st.session_state["demand_slope"]), key="demand_slope_slider", on_change=callback_params)
    st.text_input(get_translation("DEMAND_INTERCEPT_LABEL"), value=str(st.session_state["demand_intercept"]), key="demand_intercept_slider", on_change=callback_params)
    st.number_input(get_translation("ELASTICITY_LABEL_DEMAND"), 
                   value=float(st.session_state["elasticity_demand"]), 
                   min_value=-100.0, 
                   max_value=100.0, 
                   step=0.1, 
                   key="elasticity_demand_slider", 
                   on_change=callback_elasticity_demand)
    st.text_input(get_translation("SUPPLY_SLOPE_LABEL"), value=str(st.session_state["supply_slope"]), key="supply_slope_slider", on_change=callback_params)
    st.text_input(get_translation("SUPPLY_INTERCEPT_LABEL"), value=str(st.session_state["supply_intercept"]), key="supply_intercept_slider", on_change=callback_params)
    st.number_input(get_translation("ELASTICITY_LABEL_SUPPLY"), 
                   value=float(st.session_state["elasticity_supply"]), 
                   min_value=-100.0, 
                   max_value=100.0, 
                   step=0.1, 
                   key="elasticity_supply_slider", 
                   on_change=callback_elasticity_supply)
    st.button(get_translation("RESET_BUTTON"), on_click=callback_reset)

# Settings for graphs
with st.sidebar.expander(get_translation("GRAPH_PARAMS_EXPANDER")):    
    st.checkbox(get_translation("FIX_AXES_CHECKBOX"), value=st.session_state["fix_axes"], key="fix_axes_checkbox", on_change=callback_params)
    st.checkbox(get_translation("SHOW_GRID_CHECKBOX"), value=st.session_state["show_grid"], key="show_grid_checkbox", on_change=callback_params)
    st.number_input(get_translation("TICKMARK_WIDTH_LABEL"), value=st.session_state["tickmark_width"], step=0.5, min_value=0.5, max_value=5.0, format="%.1f", key="tickmark_input", on_change=callback_params)
    st.number_input(get_translation("LINE_THICKNESS_LABEL"), value=st.session_state["line_thickness"], step=0.1, min_value=0.1, max_value=5.0, format="%.1f", key="line_thickness_input", on_change=callback_params)

# Settings for OpenAI API
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

# About page
with st.sidebar.expander(get_translation("ABOUT_EXPANDER")):
    st.write(get_translation("VERSION_LABEL"))
    st.write("Joachim Zuckarelli")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image("social-github-col.png", width=30)
    with col2:
        st.markdown("[GitHub](https://github.com/jsugarelli/market)")