import streamlit as st
import re
import json
import google.generativeai as genai  # <-- Updated import
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --------------------------------------------------------------------
# Configure your Google Generative AI API key once at the start:
# --------------------------------------------------------------------
GOOGLE_API_KEY = st.secrets["google"]["api_key"]
genai.configure(api_key=GOOGLE_API_KEY)

# We'll reference this model for all calls:
GEMINI_MODEL = "gemini-2.0-flash"  # <-- Removed "models/" prefix

# --------------------------------------------------------------------
# Custom CSS: World-Class UX Aesthetics
# --------------------------------------------------------------------
custom_css = """
<style>
/* Typography */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* Base styles */
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #1a202c;
    -webkit-font-smoothing: antialiased;
}

/* Overall page styling with subtle gradient */
.main {
    background: linear-gradient(145deg, #f8fafc 0%, #edf2f7 100%);
}

/* Header and text styling */
h1 {
    font-weight: 800;
    font-size: 2.5rem;
    letter-spacing: -0.025em;
    color: #1a202c;
    line-height: 1.2;
    margin-bottom: 1rem;
}

h2 {
    font-weight: 700;
    font-size: 1.8rem;
    letter-spacing: -0.025em;
    color: #2d3748;
    margin-top: 1.5rem;
    margin-bottom: 0.75rem;
}

h3 {
    font-weight: 600;
    font-size: 1.3rem;
    color: #4a5568;
    margin-top: 1.25rem;
    margin-bottom: 0.5rem;
}

p {
    font-size: 1rem;
    line-height: 1.6;
    color: #4a5568;
    margin-bottom: 1rem;
}

/* Layout Containers */
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: #fff;
    border-right: 1px solid #e2e8f0;
}

[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    padding-top: 2rem;
    padding-left: 1.5rem;
    padding-right: 1.5rem;
}

[data-testid="stSidebar"] h1 {
    font-size: 1.5rem;
    color: #5a67d8;
    margin-bottom: 2rem;
}

/* Custom form inputs */
[data-testid="stTextInput"] input, 
[data-testid="stNumberInput"] input, 
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] {
    border-radius: 8px;
    border: 1px solid #e2e8f0;
    padding: 0.75rem;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    width: 100%;
    margin-bottom: 1rem;
}

[data-testid="stTextInput"] input:focus, 
[data-testid="stNumberInput"] input:focus, 
[data-testid="stTextArea"] textarea:focus {
    border-color: #5a67d8;
    box-shadow: 0 0 0 3px rgba(90, 103, 216, 0.15);
}

/* Buttons */
[data-testid="baseButton-secondary"], 
.stButton button {
    background: linear-gradient(135deg, #5a67d8 0%, #4c51bf 100%);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
    font-weight: 600;
    letter-spacing: 0.025em;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.2s ease;
    box-shadow: 0 4px 6px rgba(90, 103, 216, 0.2), 0 1px 3px rgba(90, 103, 216, 0.1);
}

[data-testid="baseButton-secondary"]:hover, 
.stButton button:hover {
    background: linear-gradient(135deg, #4c51bf 0%, #434190 100%);
    transform: translateY(-2px);
    box-shadow: 0 7px 14px rgba(90, 103, 216, 0.25), 0 3px 6px rgba(90, 103, 216, 0.15);
}

[data-testid="baseButton-secondary"]:active, 
.stButton button:active {
    transform: translateY(0);
    box-shadow: 0 3px 6px rgba(90, 103, 216, 0.15), 0 1px 3px rgba(90, 103, 216, 0.1);
}

/* Card styling */
.card {
    background-color: white;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05), 0 10px 15px rgba(0, 0, 0, 0.025);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    border: 1px solid #f0f4f8;
}

.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 15px rgba(0, 0, 0, 0.07), 0 20px 30px rgba(0, 0, 0, 0.035);
}

/* Decision result box */
.decision-box {
    background: linear-gradient(135deg, #ffffff 0%, #f7fafc 100%);
    border-radius: 12px;
    padding: 2rem 1.5rem;
    margin-top: 2rem;
    border: 1px solid #f0f4f8;
    box-shadow: 0 10px 25px rgba(90, 103, 216, 0.12), 0 4px 10px rgba(90, 103, 216, 0.08);
    text-align: center;
    animation: fadeInUp 0.5s ease-out forwards;
    transform: translateY(20px);
    opacity: 0;
}

.decision-box h2 {
    font-size: 1.75rem;
    font-weight: 700;
    color: #5a67d8;
    margin-bottom: 1.5rem;
}

.decision-box strong {
    color: #1a202c;
    font-weight: 700;
}

.decision-box .score {
    font-size: 3rem;
    font-weight: 800;
    color: #5a67d8;
    margin: 1rem 0;
    text-shadow: 0 2px 4px rgba(90, 103, 216, 0.2);
}

/* Factor cards */
.factor-card {
    display: flex;
    align-items: center;
    background-color: white;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.75rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    transition: all 0.2s ease;
    border-left: 4px solid #5a67d8;
}

.factor-card:hover {
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.08);
    transform: translateX(3px);
}

.factor-card .factor-letter {
    font-size: 1.25rem;
    font-weight: 700;
    color: #5a67d8;
    margin-right: 1rem;
    width: 2rem;
    height: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #ebf4ff;
    border-radius: 50%;
}

.factor-card .factor-value {
    font-size: 1.25rem;
    font-weight: 700;
    margin-left: auto;
}

.factor-card .factor-value.positive {
    color: #48bb78;
}

.factor-card .factor-value.negative {
    color: #f56565;
}

.factor-card .factor-value.neutral {
    color: #a0aec0;
}

/* Landing page title styling */
.landing-title {
    font-size: 3.5rem;
    font-weight: 900;
    background: linear-gradient(135deg, #5a67d8 0%, #4c51bf 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
    letter-spacing: -0.05em;
    line-height: 1;
    text-align: center;
}

.landing-subtitle {
    font-size: 1.25rem;
    font-weight: 500;
    color: #4a5568;
    margin-bottom: 2rem;
    text-align: center;
}

/* Logo styling */
.logo {
    display: flex;
    align-items: center;
    margin-bottom: 2rem;
}

.logo-icon {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, #5a67d8 0%, #4c51bf 100%);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 0.75rem;
    color: white;
    font-weight: 700;
    font-size: 1.25rem;
}

.logo-text {
    font-size: 1.5rem;
    font-weight: 800;
    color: #5a67d8;
}

/* Animation keyframes */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes pulse {
    0% {
        box-shadow: 0 0 0 0 rgba(90, 103, 216, 0.4);
    }
    70% {
        box-shadow: 0 0 0 10px rgba(90, 103, 216, 0);
    }
    100% {
        box-shadow: 0 0 0 0 rgba(90, 103, 216, 0);
    }
}

/* Decision recommendation styling */
.recommendation {
    margin-top: 1rem;
    font-size: 1.25rem;
    font-weight: 600;
}

.recommendation.positive {
    color: #48bb78;
}

.recommendation.negative {
    color: #f56565;
}

.recommendation.neutral {
    color: #ed8936;
}

/* Section headers */
.section-header {
    display: flex;
    align-items: center;
    margin-bottom: 1.5rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid #e2e8f0;
}

.section-header h2 {
    margin: 0;
}

.section-icon {
    width: 32px;
    height: 32px;
    background: #ebf4ff;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 0.75rem;
    color: #5a67d8;
    font-weight: 700;
    font-size: 1rem;
}

/* Custom radio buttons for Navigation */
.custom-radio {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 2rem;
}

.custom-radio-option {
    background-color: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    cursor: pointer;
    transition: all 0.2s ease;
    font-weight: 500;
}

.custom-radio-option:hover {
    background-color: #f7fafc;
    transform: translateX(3px);
}

.custom-radio-option.active {
    background-color: #ebf4ff;
    border-color: #5a67d8;
    color: #5a67d8;
    font-weight: 600;
}

/* Form layout */
.form-2-columns {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
}

/* Success & Error messages */
.success-message, .error-message {
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
    animation: fadeInUp 0.3s ease-out forwards;
}

.success-message {
    background-color: #f0fff4;
    border: 1px solid #c6f6d5;
    color: #2f855a;
}

.error-message {
    background-color: #fff5f5;
    border: 1px solid #fed7d7;
    color: #c53030;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --------------------------------------------------------------------
# Helper functions for visual elements
# --------------------------------------------------------------------
def render_logo():
    st.markdown("""
    <div class="logo">
        <div class="logo-icon">M</div>
        <div class="logo-text">Munger AI</div>
    </div>
    """, unsafe_allow_html=True)

def render_section_header(title, icon):
    st.markdown(f"""
    <div class="section-header">
        <div class="section-icon">{icon}</div>
        <h2>{title}</h2>
    </div>
    """, unsafe_allow_html=True)

def render_factor_card(factor, value, description):
    # Determine class based on value
    if value > 0:
        value_class = "positive"
    elif value < 0:
        value_class = "negative"
    else:
        value_class = "neutral"
        
    st.markdown(f"""
    <div class="factor-card">
        <div class="factor-letter">{factor}</div>
        <div class="factor-description">{description}</div>
        <div class="factor-value {value_class}">{value:+d}</div>
    </div>
    """, unsafe_allow_html=True)

def create_radar_chart(factors):
    categories = [
        'Discretionary Income', 
        'Opportunity Cost', 
        'Goal Alignment', 
        'Long-Term Impact', 
        'Behavioral'
    ]
    
    values = [
        factors['D'], 
        factors['O'], 
        factors['G'], 
        factors['L'], 
        factors['B']
    ]
    # Add the first value at the end to close the shape
    values.append(values[0])
    categories.append(categories[0])
    
    fig = go.Figure()
    
    # Add radar chart trace
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(90, 103, 216, 0.2)',
        line=dict(color='#5a67d8', width=2),
        name='Factors'
    ))
    
    # Add horizontal lines for reference
    for i in [-2, -1, 0, 1, 2]:
        fig.add_trace(go.Scatterpolar(
            r=[i] * len(categories),
            theta=categories,
            line=dict(color='rgba(200, 200, 200, 0.5)', width=1, dash='dash'),
            name=f'Level {i}',
            showlegend=False
        ))
    
    # Update layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[-3, 3],
                tickvals=[-2, -1, 0, 1, 2],
                showticklabels=True,
                ticks='',
                linewidth=0,
                gridwidth=0.5,
                gridcolor='rgba(200, 200, 200, 0.3)'
            ),
            angularaxis=dict(
                tickwidth=1,
                linewidth=1,
                gridwidth=1,
                gridcolor='rgba(200, 200, 200, 0.3)'
            ),
            bgcolor='rgba(255, 255, 255, 0.9)'
        ),
        showlegend=False,
        margin=dict(l=70, r=70, t=20, b=20),
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def create_pds_gauge(pds):
    # Define gauge colors based on value
    if pds >= 5:
        color = "#48bb78"  # Green for positive
    elif pds < 0:
        color = "#f56565"  # Red for negative
    else:
        color = "#ed8936"  # Orange for neutral
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pds,
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [-10, 10], 'tickwidth': 1, 'tickcolor': "#2d3748"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#e2e8f0",
            'steps': [
                {'range': [-10, 0], 'color': '#fed7d7'},
                {'range': [0, 5], 'color': '#feebc8'},
                {'range': [5, 10], 'color': '#c6f6d5'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 0
            }
        }
    ))
    
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': "#2d3748", 'family': "Inter, sans-serif"}
    )
    
    return fig

# --------------------------------------------------------------------
# get_factors_from_gemini: Using the updated google-generativeai library
# --------------------------------------------------------------------
def get_factors_from_gemini(
    leftover_income: float,
    has_high_interest_debt: str,
    main_financial_goal: str,
    purchase_urgency: str,
    item_name: str,
    item_cost: float
) -> dict:
    """
    Calls the Gemini 2.0 Flash model with a prompt that explains how to assign each factor.
    Returns factor values (D, O, G, L, B) as integers in the range -2 to +2.
    """
    prompt_text = f"""
We have a Purchase Decision Score (PDS) formula:
PDS = D + O + G + L + B,
where each factor is an integer from -2 to +2.

Guidelines:
1. D (Discretionary Income Factor): Rate higher if leftover_income is much larger than item_cost.
2. O (Opportunity Cost Factor): Rate positive if no high-interest debt and cost is negligible compared to goals; negative if high-interest debt exists.
3. G (Goal Alignment Factor): Rate positive if the purchase strongly supports the main financial goal; negative if it conflicts.
4. L (Long-Term Impact Factor): Rate positive if the purchase has lasting benefits; negative if it creates ongoing costs.
5. B (Behavioral/Psychological Factor): Rate positive if the purchase is urgently needed and reduces stress; negative if it is impulsive.

Evaluate the following scenario:
- Item: "{item_name}"
- Cost: {item_cost} USD
- Monthly Leftover Income: {leftover_income} USD
- High-interest debt: {has_high_interest_debt}
- Main Financial Goal: {main_financial_goal}
- Purchase Urgency: {purchase_urgency}

Assign integer values from -2 to +2 for each factor (D, O, G, L, B) according to the guidelines.
Return the result in valid JSON format (only the JSON as the final line), for example:
{{
  "D": 2,
  "O": 2,
  "G": 2,
  "L": 2,
  "B": 2
}}
    """.strip()

    try:
        # Create the model and generate content
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(
            prompt_text,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=512
            )
        )

        if not response:
            st.error("No response returned from the Gemini model.")
            return {"D": 0, "O": 0, "G": 0, "L": 0, "B": 0}

        output_text = response.text
        # Attempt to extract JSON from the output
        candidates = re.findall(r"(\{[\s\S]*?\})", output_text)
        for candidate in candidates:
            try:
                data = json.loads(candidate)
                if all(k in data for k in ["D", "O", "G", "L", "B"]):
                    return data
            except json.JSONDecodeError:
                continue

        st.error("Unable to parse valid JSON from model output.")
        return {"D": 0, "O": 0, "G": 0, "L": 0, "B": 0}

    except Exception as e:
        st.error(f"Error calling Gemini model: {e}")
        return {"D": 0, "O": 0, "G": 0, "L": 0, "B": 0}

def compute_pds(factors: dict) -> int:
    """Compute the Purchase Decision Score as a sum of factors."""
    return sum(factors.get(k, 0) for k in ["D", "O", "G", "L", "B"])

def get_recommendation(pds: int) -> tuple:
    """Return a recommendation based on the PDS."""
    if pds >= 5:
        return "Likely a strong purchase choice.", "positive"
    elif pds < 0:
        return "Likely not advisable at this time.", "negative"
    else:
        return "Borderline—evaluate carefully before buying.", "neutral"

# --------------------------------------------------------------------
# Preset Scenarios for Testing
# --------------------------------------------------------------------
preset_scenarios = {
    "Scenario A: Essential Upgrade": {
        "item_name": "High-Performance Laptop",
        "item_cost": 800.0,
        "leftover_income": 5000.0,
        "has_high_interest_debt": "No",
        "main_financial_goal": "Grow my freelance business",
        "purchase_urgency": "Urgent Needs"
    },
    "Scenario B: Non-Essential Luxury": {
        "item_name": "Luxury Watch",
        "item_cost": 3000.0,
        "leftover_income": 4000.0,
        "has_high_interest_debt": "No",
        "main_financial_goal": "Save for a house",
        "purchase_urgency": "Mostly Wants"
    },
    "Scenario C: Risky Investment": {
        "item_name": "New Car",
        "item_cost": 25000.0,
        "leftover_income": 1500.0,
        "has_high_interest_debt": "Yes",
        "main_financial_goal": "Pay off debt",
        "purchase_urgency": "Mixed"
    }
}

# --------------------------------------------------------------------
# Sidebar Navigation
# --------------------------------------------------------------------
with st.sidebar:
    render_logo()
    st.markdown("##### Decision Assistant")
    
    pages = ["Decision Tool", "Features", "Sign Up", "Contact"]
    selection = st.radio("", pages, label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("### Quick Tips")
    st.markdown("""
    - Enter accurate income details
    - Be honest about your debt
    - Define clear financial goals
    - Consider long-term impact
    """)
    
    st.markdown("---")
    st.markdown("© 2025 Munger AI")

# --------------------------------------------------------------------
# Main Page Logic
# --------------------------------------------------------------------
if selection == "Decision Tool":
    # Landing Page
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 class="landing-title">Munger AI</h1>
        <p class="landing-subtitle">Make smarter financial decisions with AI-powered insights</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Preset scenario selection
    preset_choice = st.selectbox(
        "Choose a Preset Scenario (or select 'Custom' to enter your own):", 
        list(preset_scenarios.keys()) + ["Custom"]
    )
    if preset_choice != "Custom":
        scenario = preset_scenarios[preset_choice]
    else:
        scenario = {}
    
    # Main form in a card
    
    render_section_header("Purchase Details", "📊")
    
    with st.form("purchase_decision_form"):
        col1, col2 = st.columns(2)
        with col1:
            item_name = st.text_input(
                "Item Name", 
                value=scenario.get("item_name", "New Laptop")
            )
            item_cost = st.number_input(
                "Item Cost ($)", 
                min_value=0.0, 
                value=scenario.get("item_cost", 500.0), 
                step=50.0
            )
            main_goal = st.text_input(
                "Main Financial Goal", 
                value=scenario.get("main_financial_goal", "Save for a house")
            )
        with col2:
            leftover_income = st.number_input(
                "Monthly Leftover Income ($)", 
                min_value=0.0, 
                value=scenario.get("leftover_income", 1000.0), 
                step=50.0
            )
            has_debt = st.selectbox(
                "High-Interest Debt?", 
                ["Yes", "No", "Unsure"], 
                index=["Yes", "No", "Unsure"].index(
                    scenario.get("has_high_interest_debt", "Yes")
                )
            )
            purchase_urgency = st.selectbox(
                "Purchase Urgency", 
                ["Urgent Needs", "Mostly Wants", "Mixed"], 
                index=["Urgent Needs", "Mostly Wants", "Mixed"].index(
                    scenario.get("purchase_urgency", "Urgent Needs")
                )
            )
        
        submit_pdt = st.form_submit_button(
            "Generate AI Decision",
            help="Click to get an AI-powered purchase decision",
            use_container_width=True
        )
    st.markdown('</div>', unsafe_allow_html=True)
    
    if submit_pdt:
        with st.spinner("Analyzing your purchase decision..."):
            factors = get_factors_from_gemini(
                leftover_income=leftover_income,
                has_high_interest_debt=has_debt,
                main_financial_goal=main_goal,
                purchase_urgency=purchase_urgency,
                item_name=item_name,
                item_cost=item_cost
            )
            pds = compute_pds(factors)
            recommendation, rec_class = get_recommendation(pds)
            
            # Display results
            st.markdown(f"""
            <div class="decision-box">
                <h2>Purchase Decision Analysis</h2>
                <div class="score">{pds}</div>
                <div class="recommendation {rec_class}">{recommendation}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Two columns for radar chart and gauge
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Decision Factors")
                factor_descriptions = {
                    'D': 'Discretionary Income',
                    'O': 'Opportunity Cost', 
                    'G': 'Goal Alignment',
                    'L': 'Long-Term Impact',
                    'B': 'Behavioral/Psychological'
                }
                for factor, description in factor_descriptions.items():
                    render_factor_card(factor, factors[factor], description)
            
            with col2:
                st.markdown("### Factor Analysis")
                radar_fig = create_radar_chart(factors)
                st.plotly_chart(radar_fig, use_container_width=True)
                
                gauge_fig = create_pds_gauge(pds)
                st.plotly_chart(gauge_fig, use_container_width=True)
            
            # Detailed recommendation based on the factors
            st.markdown("### Decision Insights")
            st.markdown('<div class="card">', unsafe_allow_html=True)
            
            insights = []
            
            # Discretionary Income Factor
            if factors["D"] <= 0:
                insights.append("⚠️ This purchase may strain your discretionary income.")
            elif factors["D"] >= 2:
                insights.append("✅ This purchase is well within your financial means.")
            
            # Opportunity Cost Factor
            if factors["O"] < 0:
                insights.append("⚠️ Consider addressing high-interest debt first.")
            elif factors["O"] > 1:
                insights.append("✅ This purchase represents a good use of your funds.")
            
            # Goal Alignment Factor
            if factors["G"] < 0:
                insights.append("⚠️ This purchase doesn't align with your stated financial goal.")
            elif factors["G"] > 1:
                insights.append("✅ This purchase strongly supports your main financial goal.")
            
            # Long-Term Impact Factor
            if factors["L"] < 0:
                insights.append("⚠️ The long-term impact of this purchase might be negative.")
            elif factors["L"] > 1:
                insights.append("✅ The long-term benefits of this purchase are promising.")
            
            # Behavioral/Psychological Factor
            if factors["B"] < 0:
                insights.append("⚠️ This purchase might be driven by impulse rather than necessity.")
            elif factors["B"] > 1:
                insights.append("✅ This purchase is likely to bring positive psychological benefits.")
            
            for insight in insights:
                st.markdown(f"- {insight}")
            
            st.markdown('</div>', unsafe_allow_html=True)

elif selection == "Features":
    st.markdown("## Features")
    st.write("Coming soon: Detailed features of Munger AI will be listed here.")

elif selection == "Sign Up":
    st.markdown("## Sign Up")
    st.write("Sign up for early access and stay updated with our latest features!")

elif selection == "Contact":
    st.markdown("## Contact")
    st.write("Get in touch with us at contact@mungerai.com for any inquiries or support.")
