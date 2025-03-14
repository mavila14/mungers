import streamlit as st
import re
import json
import google.generativeai as genai
import plotly.graph_objects as go
import base64
from pathlib import Path

# ------------------------------------------------------------
# Set page config (MUST BE FIRST STREAMLIT COMMAND)
# ------------------------------------------------------------
st.set_page_config(
    page_title="Munger AI - Purchase Decisions",
    page_icon="💰",
    layout="wide"
)

# ------------------------------------------------------------
# Configure your Google Generative AI API key
# ------------------------------------------------------------
GOOGLE_API_KEY = st.secrets["google"]["api_key"]
genai.configure(api_key=GOOGLE_API_KEY)

GEMINI_MODEL = "gemini-2.0-flash"

# ------------------------------------------------------------
# Modern Dark Palette CSS
# ------------------------------------------------------------
# We're using a deep navy/charcoal background (#1E1E2F),
# near-white text (#ECECEC), and a teal accent (#19A7CE).
# Cards/inputs are slightly lighter (#2A2E3D),
# and we keep corners rounded. Headings are teal for emphasis.
custom_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* Global styling: set entire app background and base text color */
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #ECECEC; /* near-white text */
    background-color: #1E1E2F !important; /* dark background */
    -webkit-font-smoothing: antialiased;
}

/* Remove or override any .main background so main area isn't white */
.main {
    background-color: #1E1E2F !important;
}

/* Headings in teal accent */
h1, h2, h3, h4, h5, h6 {
    color: #19A7CE !important;
    font-weight: 800;
    margin-bottom: 1rem;
}

/* Paragraph text in near-white */
p {
    font-size: 1rem;
    line-height: 1.6;
    color: #ECECEC !important;
    margin-bottom: 1rem;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: #2A2E3D;
    border-right: 1px solid #35354F;
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    padding-top: 2rem;
    padding-left: 1.5rem;
    padding-right: 1.5rem;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label {
    color: #ECECEC !important;
}

/* Sidebar radio buttons in near-white */
.stRadio > div[role="radiogroup"] > label {
    color: #ECECEC !important;
}
.stRadio > div[role="radiogroup"] > label > div[data-testid="stMarkdownContainer"] > p {
    color: #ECECEC !important;
}

/* Inputs: slightly lighter background (#2A2E3D), near-white text */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] {
    border-radius: 8px;
    border: 1px solid #35354F;
    padding: 0.75rem;
    background-color: #2A2E3D;
    color: #ECECEC !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
    width: 100%;
    margin-bottom: 1rem;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #19A7CE;
    box-shadow: 0 0 0 3px rgba(25,167,206, 0.2);
}

/* Labels in near-white */
[data-testid="stTextInput"] label,
[data-testid="stNumberInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stSelectbox"] label,
.stRadio label,
.stCheckbox label {
    color: #ECECEC !important;
}

/* Buttons: teal accent background, white text */
[data-testid="baseButton-secondary"], 
.stButton button {
    background: #19A7CE !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 20px !important;
    padding: 0.75rem 1.5rem !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.025em !important;
    text-transform: uppercase !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 6px rgba(25,167,206, 0.3), 0 1px 3px rgba(25,167,206, 0.2) !important;
}
[data-testid="baseButton-secondary"]:hover, 
.stButton button:hover {
    background: #16A0C0 !important; /* slightly darker teal on hover */
    transform: translateY(-2px) !important;
    box-shadow: 0 7px 14px rgba(25,167,206, 0.4), 0 3px 6px rgba(25,167,206, 0.3) !important;
}
[data-testid="baseButton-secondary"]:active, 
.stButton button:active {
    transform: translateY(0) !important;
    box-shadow: 0 3px 6px rgba(25,167,206, 0.2), 0 1px 3px rgba(25,167,206, 0.1) !important;
}

/* Card styling */
.card {
    background-color: #2A2E3D;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2), 0 10px 15px rgba(0, 0, 0, 0.1);
    border: 1px solid #35354F;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 15px rgba(0, 0, 0, 0.4), 0 20px 30px rgba(0, 0, 0, 0.3);
}

/* Landing page title styling */
.landing-title {
    font-size: 3.5rem;
    font-weight: 900;
    color: #19A7CE;
    margin-bottom: 0.5rem;
    letter-spacing: -0.05em;
    line-height: 1;
    text-align: center;
}
.landing-subtitle {
    font-size: 1.25rem;
    font-weight: 500;
    color: #ECECEC !important;
    margin-bottom: 2rem;
    text-align: center;
}

/* Smaller sidebar logo styling: round corners */
.logo {
    display: flex;
    align-items: center;
    margin-bottom: 2rem;
}
.logo-img {
    width: 50px;
    height: 50px;
    border-radius: 12px;
    margin-right: 0.75rem;
}
.logo-text {
    font-size: 1.5rem;
    font-weight: 800;
    color: #19A7CE;
}

/* Section header */
.section-header {
    display: flex;
    align-items: center;
    margin-bottom: 1.5rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid #35354F;
}
.section-icon {
    width: 32px;
    height: 32px;
    background: #2A2E3D;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 0.75rem;
    color: #19A7CE;
    font-weight: 700;
    font-size: 1rem;
}

/* Decision box */
.decision-box {
    background: #2A2E3D;
    border-radius: 12px;
    padding: 2rem 1.5rem;
    margin-top: 2rem;
    border: 1px solid #35354F;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4), 0 4px 10px rgba(0, 0, 0, 0.3);
    text-align: center;
    animation: fadeInUp 0.5s ease-out forwards;
    transform: translateY(20px);
    opacity: 0;
}
.decision-box h2 {
    font-size: 1.75rem;
    font-weight: 700;
    margin-bottom: 1.5rem;
    color: #19A7CE !important;
}
.decision-box .score {
    font-size: 3rem;
    font-weight: 800;
    margin: 1rem 0;
    color: #ECECEC;
    text-shadow: 0 2px 4px rgba(25,167,206, 0.2);
}
.recommendation {
    margin-top: 1rem;
    font-size: 1.25rem;
    font-weight: 600;
    color: #ECECEC !important;
}

/* Factor cards */
.factor-card {
    display: flex;
    align-items: center;
    background-color: #2A2E3D;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.75rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    border-left: 4px solid #19A7CE;
    transition: all 0.2s ease;
}
.factor-card:hover {
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
    transform: translateX(3px);
}
.factor-card .factor-letter {
    font-size: 1.25rem;
    font-weight: 700;
    margin-right: 1rem;
    width: 2rem;
    height: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #2A2E3D;
    border-radius: 50%;
    border: 2px solid #19A7CE;
    color: #19A7CE;
}
.factor-card .factor-description {
    flex: 1;
    color: #ECECEC !important;
}
.factor-card .factor-value {
    font-size: 1.25rem;
    font-weight: 700;
    margin-left: auto;
    color: #ECECEC !important;
}

/* Item card styles */
.item-card {
    background: #2A2E3D;
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    border: 1px solid #35354F;
    display: flex;
    align-items: center;
}
.item-icon {
    width: 40px;
    height: 40px;
    background: #2A2E3D;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 1rem;
    color: #19A7CE;
    font-weight: 700;
    font-size: 1.25rem;
    border: 2px solid #19A7CE;
}
.item-details {
    flex: 1;
    color: #ECECEC !important;
}
.item-name {
    font-weight: 600;
    font-size: 1.1rem;
    color: #ECECEC !important;
}
.item-cost {
    font-weight: 700;
    font-size: 1.2rem;
    color: #19A7CE !important;
}

/* Plotly axis & caption text in near-white / teal accent */
.css-1b0udgb,
g[class*='tick'],
text {
    fill: #ECECEC !important;
    color: #ECECEC !important;
}

/* Animations */
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
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)


# ------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------
def render_logo():
    """
    Renders the small logo in the sidebar with rounded corners.
    """
    current_dir = Path(__file__).parent
    logo_path = current_dir / "munger.png"
    
    try:
        with open(logo_path, "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
        
        st.markdown(f"""
        <div class="logo">
            <img src="data:image/png;base64,{logo_data}" class="logo-img" alt="Munger AI Logo"/>
            <div class="logo-text">MUNGER AI</div>
        </div>
        """, unsafe_allow_html=True)
    except:
        # Fallback if file not found
        st.markdown("""
        <div class="logo">
            <div style="width: 50px; height: 50px; background: #2A2E3D; 
                        border-radius: 12px; display: flex; 
                        align-items: center; justify-content: center; 
                        margin-right: 0.75rem; color: #19A7CE; 
                        font-weight: 700; font-size: 1.5rem; 
                        border: 2px solid #19A7CE;">
                M
            </div>
            <div class="logo-text">MUNGER AI</div>
        </div>
        """, unsafe_allow_html=True)


def render_big_logo_and_title():
    """
    Renders the large, center logo (rounded) and subtitle.
    """
    current_dir = Path(__file__).parent
    logo_path = current_dir / "munger.png"
    
    try:
        with open(logo_path, "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
        
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 2rem;">
            <img src="data:image/png;base64,{logo_data}"
                 style="width:120px; margin-bottom:1rem; border-radius:12px;"
                 alt="Munger AI"/>
            <p class="landing-subtitle">Should you buy it? Our AI decides in seconds.</p>
        </div>
        """, unsafe_allow_html=True)
    except:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1 class="landing-title">MUNGER AI</h1>
            <p class="landing-subtitle">Should you buy it? Our AI decides in seconds.</p>
        </div>
        """, unsafe_allow_html=True)


def render_section_header(title, icon):
    st.markdown(f"""
    <div class="section-header">
        <div class="section-icon">{icon}</div>
        <h2>{title}</h2>
    </div>
    """, unsafe_allow_html=True)

def render_item_card(item_name, cost):
    icon = "💼" if cost >= 1000 else "🛍️"
    st.markdown(f"""
    <div class="item-card">
        <div class="item-icon">{icon}</div>
        <div class="item-details">
            <div class="item-name">{item_name}</div>
        </div>
        <div class="item-cost">${cost:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

def render_factor_card(factor, value, description):
    st.markdown(f"""
    <div class="factor-card">
        <div class="factor-letter">{factor}</div>
        <div class="factor-description">{description}</div>
        <div class="factor-value">{value:+d}</div>
    </div>
    """, unsafe_allow_html=True)


# ------------------------------------------------------------
# Plotly Charts
# ------------------------------------------------------------
def create_radar_chart(factors):
    categories = [
        "Discretionary Income",
        "Opportunity Cost",
        "Goal Alignment",
        "Long-Term Impact",
        "Behavioral"
    ]
    vals = [
        factors["D"], 
        factors["O"], 
        factors["G"], 
        factors["L"], 
        factors["B"]
    ]
    # close shape
    vals.append(vals[0])
    categories.append(categories[0])
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals,
        theta=categories,
        fill='toself',
        fillcolor='rgba(25,167,206, 0.2)',  # teal accent
        line=dict(color='#19A7CE', width=2),
        name='Factors'
    ))
    # reference lines
    for i in [-2, -1, 0, 1, 2]:
        fig.add_trace(go.Scatterpolar(
            r=[i]*len(categories),
            theta=categories,
            line=dict(color='rgba(236,236,236,0.2)', width=1, dash='dash'),
            showlegend=False
        ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[-3,3],
                tickvals=[-2,-1,0,1,2],
                gridcolor='rgba(236,236,236,0.1)',
                tickfont=dict(color='#ECECEC')
            ),
            angularaxis=dict(
                gridcolor='rgba(236,236,236,0.1)',
                tickfont=dict(color='#ECECEC')
            ),
            bgcolor='rgba(0,0,0,0)'
        ),
        showlegend=False,
        margin=dict(l=60, r=60, t=20, b=20),
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def create_pds_gauge(pds):
    """
    Creates a gauge from -10..10 with steps tinted red/orange/green,
    and teal bar for the needle.
    """
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pds,
        domain={'x':[0,1],'y':[0,1]},
        gauge={
            'axis': {
                'range':[-10,10],
                'tickfont': {'color': '#ECECEC'}
            },
            'bar': {'color': '#19A7CE'},  # teal bar
            'bgcolor':"#2A2E3D",
            'borderwidth':2,
            'bordercolor':"#35354F",
            'steps': [
                {'range':[-10,0], 'color':'rgba(245,101,101,0.3)'}, 
                {'range':[0,5], 'color':'rgba(237,137,54,0.3)'},
                {'range':[5,10], 'color':'rgba(72,187,120,0.3)'}
            ],
        },
        number={'font': {'color': '#ECECEC'}}
    ))
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color':"#ECECEC", 'family':"Inter, sans-serif"}
    )
    return fig


# ------------------------------------------------------------
# AI Logic
# ------------------------------------------------------------
def get_factors_from_gemini(leftover_income, has_high_interest_debt,
                            main_financial_goal, purchase_urgency,
                            item_name, item_cost, extra_context=None):
    """
    Returns factor assignments (D,O,G,L,B) from -2..+2 plus brief explanations.
    Attempts to parse valid JSON from the model's output.
    """
    extra_text = f"\nAdditional user context: {extra_context}" if extra_context else ""
    
    prompt = f"""
We have a Purchase Decision Score (PDS) formula:
PDS = D + O + G + L + B, each factor is -2 to 2.

Guidelines:
1. D: Higher if leftover_income >> item_cost
2. O: Positive if no high-interest debt, negative if debt
3. G: Positive if aligns with main_financial_goal, negative if conflicts
4. L: Positive if it has a long-term benefit, negative if not
5. B: Positive if it's an urgent need, negative if it's an impulsive or non-essential

Evaluate:
- Item: {item_name}
- Cost: {item_cost}
- leftover_income: {leftover_income}
- high_interest_debt: {has_high_interest_debt}
- main_financial_goal: {main_financial_goal}
- purchase_urgency: {purchase_urgency}
{extra_text}

Return valid JSON:
{{
  "D": 2,
  "O": 1,
  "G": 0,
  "L": -1,
  "B": 2,
  "D_explanation": "...",
  "O_explanation": "...",
  "G_explanation": "...",
  "L_explanation": "...",
  "B_explanation": "..."
}}
""".strip()
    
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        resp = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=512
            )
        )
        if not resp:
            st.error("No response from Gemini.")
            return {"D":0,"O":0,"G":0,"L":0,"B":0}
        
        text = resp.text
        # Attempt to extract valid JSON from the response
        candidates = re.findall(r"(\{[\s\S]*?\})", text)
        for c in candidates:
            try:
                data = json.loads(c)
                if all(k in data for k in ["D","O","G","L","B"]):
                    return data
            except json.JSONDecodeError:
                pass
        
        st.error("Unable to parse valid JSON from AI output.")
        return {"D":0,"O":0,"G":0,"L":0,"B":0}
    except Exception as e:
        st.error(f"Error calling Gemini: {e}")
        return {"D":0,"O":0,"G":0,"L":0,"B":0}

def compute_pds(factors):
    return sum(factors.get(f, 0) for f in ["D","O","G","L","B"])

def get_recommendation(pds):
    if pds >= 5:
        return "Buy it.", "positive"
    elif pds < 0:
        return "Don't buy it.", "negative"
    else:
        return "Consider carefully.", "neutral"


# ------------------------------------------------------------
# Main App
# ------------------------------------------------------------
def main():
    with st.sidebar:
        render_logo()
        st.markdown("##### Decision Assistant")
        
        pages = ["Decision Tool", "Advanced Tool"]
        selection = st.radio("", pages, label_visibility="collapsed")
        
        st.markdown("---")
        st.markdown("### Quick Tips")
        st.markdown("""
        - Enter the item and cost
        - Or use Advanced Tool for full control
        - Score ≥ 5 suggests buying
        """)
        
        st.markdown("---")
        st.markdown("© 2025 Munger AI")
    
    # Show the big center logo & subtitle
    render_big_logo_and_title()
    
    # 1. Basic Decision Tool
    if selection == "Decision Tool":
        render_section_header("What are you buying?", "🛍️")
        
        with st.form("basic_form"):
            col1, col2 = st.columns([3,1])
            with col1:
                item_name = st.text_input("What are you buying?", value="New Laptop")
            with col2:
                cost = st.number_input("Cost ($)", min_value=1.0, value=500.0, step=50.0)
            
            submit_btn = st.form_submit_button("Should I Buy It?")
        
        if submit_btn:
            with st.spinner("Analyzing with AI..."):
                leftover_income = max(1000, cost * 2)
                has_high_interest_debt = "No"
                main_financial_goal = "Save for emergencies"
                purchase_urgency = "Mixed"
                
                factors = get_factors_from_gemini(
                    leftover_income,
                    has_high_interest_debt,
                    main_financial_goal,
                    purchase_urgency,
                    item_name,
                    cost
                )
                pds = compute_pds(factors)
                rec_text, rec_class = get_recommendation(pds)
                
                render_item_card(item_name, cost)
                st.markdown(f"""
                <div class="decision-box">
                    <h2>Purchase Decision Score</h2>
                    <div class="score">{pds}</div>
                    <div class="recommendation {rec_class}">{rec_text}</div>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("### Decision Factors")
                    factor_labels = {
                        "D": "Discretionary Income",
                        "O": "Opportunity Cost",
                        "G": "Goal Alignment",
                        "L": "Long-Term Impact",
                        "B": "Behavioral"
                    }
                    for f in ["D","O","G","L","B"]:
                        val = factors.get(f, 0)
                        render_factor_card(f, val, factor_labels[f])
                        exp_key = f"{f}_explanation"
                        if exp_key in factors:
                            st.caption(factors[exp_key])
                            
                with c2:
                    st.markdown("### Factor Analysis")
                    radar_fig = create_radar_chart(factors)
                    st.plotly_chart(radar_fig, use_container_width=True)
                    
                    gauge_fig = create_pds_gauge(pds)
                    st.plotly_chart(gauge_fig, use_container_width=True)
    
    # 2. Advanced Tool
    else:
        render_section_header("Advanced Purchase Query", "⚙️")
        st.markdown("Customize **all** parameters for a more precise analysis.")
        
        with st.form("advanced_form"):
            st.subheader("Purchase Details")
            item_name = st.text_input("Item Name", "High-End Laptop")
            item_cost = st.number_input("Item Cost ($)", min_value=1.0, value=2000.0, step=100.0)
            
            st.subheader("User-Financial Data")
            leftover_income = st.number_input("Monthly Leftover Income ($)", min_value=0.0, value=1500.0, step=100.0)
            has_debt = st.selectbox("High-Interest Debt?", ["No", "Yes"])
            main_goal = st.text_input("Main Financial Goal", "Build an emergency fund")
            urgency = st.selectbox("Purchase Urgency", ["Urgent Needs","Mixed","Mostly Wants"])
            
            st.subheader("Optional Extra Context")
            extra_notes = st.text_area("Any additional context or notes?")
            
            advanced_submit = st.form_submit_button("Analyze My Purchase")
        
        if advanced_submit:
            with st.spinner("Contacting AI for advanced analysis..."):
                factors = get_factors_from_gemini(
                    leftover_income,
                    has_debt,
                    main_goal,
                    urgency,
                    item_name,
                    item_cost,
                    extra_context=extra_notes
                )
                pds = compute_pds(factors)
                rec_text, rec_class = get_recommendation(pds)
                
                render_item_card(item_name, item_cost)
                st.markdown(f"""
                <div class="decision-box">
                    <h2>Purchase Decision Score</h2>
                    <div class="score">{pds}</div>
                    <div class="recommendation {rec_class}">{rec_text}</div>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("### Decision Factors")
                    factor_labels = {
                        "D": "Discretionary Income",
                        "O": "Opportunity Cost",
                        "G": "Goal Alignment",
                        "L": "Long-Term Impact",
                        "B": "Behavioral"
                    }
                    for f in ["D","O","G","L","B"]:
                        val = factors.get(f, 0)
                        render_factor_card(f, val, factor_labels[f])
                        exp_key = f"{f}_explanation"
                        if exp_key in factors:
                            st.caption(factors[exp_key])
                with c2:
                    st.markdown("### Factor Analysis")
                    radar_fig = create_radar_chart(factors)
                    st.plotly_chart(radar_fig, use_container_width=True)
                    
                    gauge_fig = create_pds_gauge(pds)
                    st.plotly_chart(gauge_fig, use_container_width=True)

# ------------------------------------------------------------
# Run the App
# ------------------------------------------------------------
if __name__ == "__main__":
    main()
