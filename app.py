import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set page configuration
st.set_page_config(
    page_title="Betting Insights",
    page_icon="🎲",
    layout="wide"
)

# Add custom CSS
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .high-probability { color: green; }
    .medium-probability { color: orange; }
    .low-probability { color: red; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load and cache all necessary data"""
    league_probs = pd.read_csv('league_probabilities.csv', index_col=0)
    home_probs = pd.read_csv('home_team_probabilities.csv', index_col=0)
    guest_probs = pd.read_csv('guest_team_probabilities.csv', index_col=0)
    historical_data = pd.read_csv('clean_data_bet.csv')
    return league_probs, home_probs, guest_probs, historical_data

def get_probability_color(prob):
    """Return color based on probability value"""
    if prob >= 0.6:
        return "high-probability"
    elif prob >= 0.45:
        return "medium-probability"
    return "low-probability"

def main():
    st.title("🎲 Betting Probability Calculator")
    
    try:
        # Load data
        league_probs, home_probs, guest_probs, historical_data = load_data()
    except FileNotFoundError:
        st.error("Please run the data processing notebook first to generate the required files.")
        st.stop()
    
    # Create three columns for selection
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("League Selection")
        selected_league = st.selectbox(
            "Choose League",
            options=sorted(league_probs.index),
            format_func=lambda x: f"{x} (Prob: {league_probs.loc[x, 'probability']:.2f})"
        )
        
    # Filter teams based on selected league and available probability data
    league_teams = historical_data[historical_data['league'] == selected_league]
    available_home_teams = sorted(set(league_teams['home_team']) & set(home_probs.index))
    available_away_teams = sorted(set(league_teams['guest_team']) & set(guest_probs.index))
    
    with col2:
        st.subheader("Home Team")
        if available_home_teams:
            selected_home = st.selectbox(
                "Choose Home Team",
                options=available_home_teams,
                format_func=lambda x: f"{x} (Prob: {home_probs.loc[x, 'probability']:.2f})"
            )
        else:
            st.warning("No home teams available for this league")
            st.stop()
        
    with col3:
        st.subheader("Away Team")
        if available_away_teams:
            selected_away = st.selectbox(
                "Choose Away Team",
                options=available_away_teams,
                format_func=lambda x: f"{x} (Prob: {guest_probs.loc[x, 'probability']:.2f})"
            )
        else:
            st.warning("No away teams available for this league")
            st.stop()

    # Calculate probabilities
    league_p = league_probs.loc[selected_league, 'probability']
    home_p = home_probs.loc[selected_home, 'probability']
    away_p = guest_probs.loc[selected_away, 'probability']
    
    # Allow users to adjust weights
    st.sidebar.subheader("Probability Weights")
    league_weight = st.sidebar.slider("League Weight", 0.0, 1.0, 0.4)
    home_weight = st.sidebar.slider("Home Team Weight", 0.0, 1.0, 0.3)
    away_weight = st.sidebar.slider("Away Team Weight", 0.0, 1.0, 0.3)
    
    # Normalize weights
    total_weight = league_weight + home_weight + away_weight
    weights = (league_weight/total_weight, home_weight/total_weight, away_weight/total_weight)
    
    # Calculate combined probability
    combined_prob = (league_p * weights[0] + home_p * weights[1] + away_p * weights[2])
    
    # Display main probability
    st.markdown("---")
    st.markdown(f"""
        <h2 style='text-align: center;' class='{get_probability_color(combined_prob)}'>
        Combined Probability: {combined_prob:.2%}
        </h2>
    """, unsafe_allow_html=True)
    
    # Display detailed analysis
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
            <div class='metric-card'>
            <h4>League Analysis</h4>
            <p>Probability: {league_p:.2%}</p>
            <p>Reliability: {league_probs.loc[selected_league, 'reliability']}</p>
            <p>Games Analyzed: {league_probs.loc[selected_league, 'total_games']}</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
            <div class='metric-card'>
            <h4>Home Team Analysis</h4>
            <p>Probability: {home_p:.2%}</p>
            <p>Reliability: {home_probs.loc[selected_home, 'reliability']}</p>
            <p>Games Analyzed: {home_probs.loc[selected_home, 'total_games']}</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
            <div class='metric-card'>
            <h4>Away Team Analysis</h4>
            <p>Probability: {away_p:.2%}</p>
            <p>Reliability: {guest_probs.loc[selected_away, 'reliability']}</p>
            <p>Games Analyzed: {guest_probs.loc[selected_away, 'total_games']}</p>
            </div>
        """, unsafe_allow_html=True)

    # Display recommendations
    st.markdown("### Betting Recommendation")
    if combined_prob >= 0.6 and all(x in ['High', 'Very High'] for x in 
        [league_probs.loc[selected_league, 'reliability'],
         home_probs.loc[selected_home, 'reliability'],
         guest_probs.loc[selected_away, 'reliability']]):
        st.success("Strong Betting Opportunity ✅")
    elif combined_prob <= 0.4:
        st.error("High Risk - Consider Avoiding ⚠️")
    else:
        st.warning("Moderate Probability - Proceed with Caution ⚠️")

    # Add historical performance
    st.markdown("### Historical Performance")
    head_to_head = historical_data[
        (historical_data['home_team'] == selected_home) & 
        (historical_data['guest_team'] == selected_away)
    ]
    if not head_to_head.empty:
        st.dataframe(head_to_head)
    else:
        st.info("No historical matches found between these teams")

if __name__ == "__main__":
    main()