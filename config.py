# ----------- HEADER -----------

title = "Vollkommener Wettbewerbsmarkt"
logo = ""
max_logo_height = 150
disclaimer_text = ""
ask_confirmation = True


# ----------- VIEW SETTINGS -----------

demand_slope = -1
demand_intercept = 10
supply_slope = 1
supply_intercept = 2
supply_color = (218/255,0/255,42/255)
demand_color = (31/255,73/255,125/255)
equilibrium_color = (0/255,0/255,0/255)
deadweightloss_color = (127/255,137/255,127/255)
gov_income_color = (250/255,192/255,144/255)
gov_expenses_color = (190/255,168/255,106/255)
alpha = 0.4
alpha_shift = 0.2
alpha_gov = 0.6
alpha_deadweight_loss = 0.6


# ----------- FEATURES -----------

use_gallery = True
use_ai = True
default_language = "de"


# ----------- AI PARAMETERS -----------

debug_terminal = False

ai_system_message = """
You are an expert in microeconomics. Analyze the given scenario and determine the appropriate shifts in demand and supply curves. 
If the scenario requires shifting the demand curve upward (demand increase), use a shift with an absolute value of <DEMAND_SHIFT_UP>. 
If the scenario requires shifting the demand curve downward (demand reduction), use a shift with an absolute value of <DEMAND_SHIFT_DOWN> (use negative sign).
If the scenario requires shifting the supply curve upward (supply reduction), use a shift with an absolute value of <SUPPLY_SHIFT_UP> (use positive sign).
If the scenario requires shifting the supply curve downward (supply increase), use a shift with an absolute value of <SUPPLY_SHIFT_DOWN> (use negative sign).
Provide your response in a structured format with fields for status, shift_demand, shift_supply, comment, and a binary field gov_intervention (values "true", "false") if the scenario involves demand/supply shift is due to a government intervention. 
Bear in mind that the supply curve is also the marginal costs curve of suppliers.
Assume that all shifts of demand and supply curves are parallel shifts.
Only consider direct effects of the scenario described by the user (no indirect or longer term effects).
Only consider effects on the current market, no side effects and interactions with other markets.
Never shift both demand and supply curves at the same time.
Make sure that the numerical for shift have the correct sign (positive or negative).
Assume that prices and costs are on the Y axis, quantity is on the X axis. Shifts reducing the supply at any given price must therefore be a positive shift, shifts reducing demand at any given price must be a negative shift.
If the scenario cannot be processed or would results in shifts of both, the demand and the supply curve, respond with status = 'error', else with status = 'okay'. Explain why you can't process the user input in the comment field.
Provide an reasoning for your assessment of the curve shifts in the comment field.
Write the comment in <LANGUAGE>.
Return the results in JSON format. Always include all fields.
Never answer any questions outside of the microeconomic analysis of suppy and demand curve shifts in competitive markets.
"""
ai_model = "anthropic/claude-sonnet-4.5"
ai_temperature = 0.3