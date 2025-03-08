import streamlit as st
import re
import json
import google.generativeai as palm  # The new library
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ------------------------------------------------------------------------------
# 1) Configure your Google Generative AI API key once at the start
# ------------------------------------------------------------------------------
GOOGLE_API_KEY = st.secrets["google"]["api_key"]
palm.configure(api_key=GOOGLE_API_KEY)

# We'll reference this model for all calls:
GEMINI_MODEL = "models/gemini-2.0-flash"

# ------------------------------------------------------------------------------
# 2) Custom CSS: World-Class UX Aesthetics
# ------------------------------------------------------------------------------
custom_css = """
<style>
/* ...[CSS omitted for brevity—same as before]... */
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 3) Helper Functions for Visual Elements
# ------------------------------------------------------------------------------
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
    values = [factors['D'], factors['O'], factors['G'], factors['L'], factors['B']]
    # Close the shape by repeating the first value
    values.append(values[0])
    categories.append(categories[0])
    
    fig = go.Figure()
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
    
    # Layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[-3, 3],
                tickvals=[-2, -1, 0, 1, 2],
                gridcolor='rgba(200, 200, 200, 0.3)'
            ),
            angularaxis=dict(
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
    # Define gauge color
    if pds >= 5:
        color = "#48bb78"  # Green
    elif pds < 0:
        color = "#f56565"  # Red
    else:
        color = "#ed8936"  # Orange
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pds,
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [-10, 10]},
            'bar': {'color': color},
            'steps': [
                {'range': [-10, 0], 'color': '#fed7d7'},
                {'range': [0, 5], 'color': '#feebc8'},
                {'range': [5, 10], 'color': '#c6f6d5'}
            ],
        }
    ))
    
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': "#2d3748", 'family': "Inter, sans-serif"}
    )
    return fig

# ------------------------------------------------------------------------------
# 4) get_factors_from_gemini: Using the new google-generativeai library
# ------------------------------------------------------------------------------
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
        # No "Client" usage here! Just palm.generate_text
        response = palm.generate_text(
            model=GEMINI_MODEL,
            prompt=prompt_text,
            temperature=0.2,      # optional
            max_output_tokens=512 # optional
        )

        if not response or not response.candidates:
            st.error("No text candidates returned from the Gemini model.")
            return {"D": 0, "O": 0, "G": 0, "L": 0, "B": 0}

        output_text = response.candidates[0]["output"]
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

# ------------------------------------------------------------------------------
# 5) Preset Scenarios for Testing
# ------------------------------------------------------------------------------
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

# ------------------------------------------------------------------------------
# 6) Sidebar Navigation
# ------------------------------------------------------------------------------
with st.sidebar:
    render_logo()
    st.markdown("##### Decision Assistant")
    
    # Provide a non-empty label to avoid the accessibility warning
    pages = ["Decision Tool", "Features", "Sign Up", "Contact"]
    selection = st.radio("Navigate to page:", pages, label_visibility="collapsed")
    
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

# ------------------------------------------------------------------------------
# 7) Main Page Logic
# ------------------------------------------------------------------------------
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
    st.markdown('<div class="card">', unsafe_allow_html=True)
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
                insights.append("⚠️ Be cautious of any potential ongoing costs this purchase may create.")
            elif factors["L"] > 1:
                insights.append("✅ This purchase offers good long-term value.")
            
            # Behavioral/Psychological Factor
            if factors["B"] < 0:
                insights.append("⚠️ Be aware of impulsive or stress-induced spending.")
            elif factors["B"] > 1:
                insights.append("✅ This purchase urgency is justified and reduces stress.")
            
            if not insights:
                st.markdown("No specific red or green flags found. Evaluate carefully!")
            else:
                for insight in insights:
                    st.markdown(f"- {insight}")
            
            st.markdown('</div>', unsafe_allow_html=True)

elif selection == "Features":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    render_section_header("Product Features", "💡")
    st.write(
        """
        **Munger AI** helps you:
        - Quickly evaluate discretionary vs. essential spending
        - Assess alignment with your financial goals
        - Measure long-term ROI or cost burden
        - Account for behavioral and psychological triggers
        - Produce a clear Purchase Decision Score (PDS)
        
        **Additional Highlights**:
        - Secure, real-time AI analysis
        - Easy-to-read charts and gauges
        - Mobile-friendly design
        - Regular updates and new scenarios
        """
    )
    st.markdown('</div>', unsafe_allow_html=True)

elif selection == "Sign Up":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    render_section_header("Sign Up for Early Access", "🚀")
    
    with st.form("signup_form"):
        full_name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        submitted = st.form_submit_button("Sign Up")
    
    if submitted:
        if full_name and email and password:
            st.success(f"Thanks for signing up, {full_name}!")
            st.write("We'll send you updates on the latest Munger AI features and improvements.")
        else:
            st.error("Please fill in all fields to sign up.")
    
    st.markdown('</div>', unsafe_allow_html=True)

elif selection == "Contact":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    render_section_header("Contact Us", "✉️")
    st.write(
        """
        **We'd love to hear from you!**  
        - **Email**: support@mungerai.com  
        - **Phone**: (123) 456-7890  
        - **Address**: 123 Munger Lane, FinTech City, USA  

        Or leave us a message below:
        """
    )
    with st.form("contact_form"):
        user_name = st.text_input("Your Name")
        user_email = st.text_input("Your Email")
        user_message = st.text_area("Your Message")
        
        contact_submitted = st.form_submit_button("Send Message")
    
    if contact_submitted:
        if user_name and user_email and user_message:
            st.success("Thank you! Your message has been sent.")
        else:
            st.error("Please complete all fields before sending.")
    
    st.markdown('</div>', unsafe_allow_html=True)
