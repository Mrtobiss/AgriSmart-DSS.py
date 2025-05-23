import streamlit as st
import pandas as pd

# ======================
# DSS KNOWLEDGE BASE  
# ======================
st.set_page_config(
    page_title="AgriSmart DSS",
    page_icon="🌱",
    layout="wide"
)

# Load dataset
@st.cache_data
def load_data():
    return pd.read_csv("TEAM_DSS_Dataset.csv") 

df = load_data()

# validate data
def validate_data(df):
    """Check for required columns and data"""
    required_cols = [
        'Farm Location', 'Crop', 'cold storage location',
        'optimal storage temp(degree c)', 
        'spoilage rate at optimal temp(%)per week'
    ]
    
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        st.error(f"Missing columns: {missing}")
        return False
        
    null_report = df[required_cols].isnull().sum()
    if null_report.sum() > 0:
        st.warning("Null values found:")
        st.write(null_report[null_report > 0])
        
    return True

if not validate_data(df):
    st.stop()

# Clean data 
df = df.dropna(subset=['Crop', 'Farm Location'])
df['Crop'] = df['Crop'].str.strip().str.title()
df['Farm Location'] = df['Farm Location'].str.strip()
df.columns = df.columns.str.strip()

if st.checkbox("Show sample data"):
    st.write(df.sample(5))

# ======================
# DSS CORE FUNCTIONS 
# ======================
def get_recommendations(farm_loc, crop_type):
    try:
        results = df[
            (df['Farm Location'].str.lower() == farm_loc.strip().lower()) &
            (df['Crop'].str.lower() == crop_type.strip().lower())
        ]
        
        if results.empty:
            results = df[
                df['Farm Location'].str.lower().str.contains(farm_loc.strip().lower()) &
                df['Crop'].str.lower().str.contains(crop_type.strip().lower())
            ]
            
        if not results.empty:
            nearest = results.sort_values('farm to cold storage(km)').iloc[0]
            return {
                "storage_name": nearest['cold storage location'],
                "storage_km": nearest['farm to cold storage(km)'],
                "storage_hrs": nearest['farm to cold storage(hrs)'],
                "market_name": nearest['market location'],
                "market_km": nearest['cold storage to market(km)'],
                "market_hrs": nearest['cold storage to market(hrs)'],
                "optimal_temp": nearest['optimal storage temp(degree c)'],
                "spoilage_rate": nearest['spoilage rate at optimal temp(%)per week'],
                "storage_cost": f"₦{nearest['storage cost(#/crate/day)']}/crate/day",
                "transport_cost": f"₦{int(nearest['transport cost for 20 ton load(#/km)'] * nearest['farm to cold storage(km)']):,}"
            }
        return None
    except Exception as e:
        st.error(f"Error in recommendation: {str(e)}")
        return None

# ======================
# DSS USER INTERFACE
# ======================

# Header
st.title("🌱 AgriSmart Decision Support System")
st.markdown("""
**Reducing Post-Harvest Losses for Nigerian Farmers**  
*Developed for AgriConnect Summit Hackathon - Team DSS*
""")

# Main DSS Interface
with st.container():
    st.header("1. Enter Farm Details")
    col1, col2 = st.columns(2)
    with col1:
        farm_location = st.selectbox(
            "SELECT FARM LOCATION",
            options=sorted(df['Farm Location'].unique()),
            help="Choose your farm location"
        )
    with col2:
        crop = st.selectbox(
            "SELECT CROP",
            options=sorted(df['Crop'].unique()),
            help="Choose your crop"
        )

# Viewer for Valid Crop-Location Combinations
with st.expander("📋 View Valid Crop-Location Combinations"):
    valid_combinations = df[['Farm Location', 'Crop']].drop_duplicates().sort_values(by=['Farm Location', 'Crop'])
    st.dataframe(valid_combinations.reset_index(drop=True), use_container_width=True)

# DSS Analysis
if st.button("Generate Recommendations", type="primary", key="recommend_button"):
    rec = get_recommendations(farm_location, crop)
    
    if not rec:
        st.error("No recommendations found for this location/crop combination")
    else:
        st.header("2. DSS Analysis Report")
        
        cols = st.columns(3)
        cols[0].metric("Distance to Storage", f"{rec['storage_km']} km")
        cols[1].metric("Optimal Temp", f"{rec['optimal_temp']}°C")
        cols[2].metric("Weekly Spoilage", f"{rec['spoilage_rate']}%")
        
        with st.expander("Location Details"):
            st.markdown(f"""
            **Farm Location:** {farm_location}  
            **Nearest Cold Storage:** {rec['storage_name']} ({rec['storage_km']} km away)  
            **Recommended Market:** {rec['market_name']} ({rec['market_km']} km from storage)
            """)
        
        with st.expander("Cost Breakdown"):
            st.markdown(f"""
            - **Cold Storage Cost:** {rec['storage_cost']}
            - **Estimated Transport Cost (20-ton):** {rec['transport_cost']}
            - **Total Transit Time:** {rec['storage_hrs'] + rec['market_hrs']} hours
            """)

        # Heatmap
        with st.expander("Regional Spoilage Rates"):
            try:
                heatmap_data = df.pivot_table(
                    index='Farm Location',
                    columns='Crop',
                    values='spoilage rate at optimal temp(%)per week',
                    aggfunc='mean'
                )
                st.dataframe(
                    heatmap_data.style.background_gradient(cmap='Reds'),
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error generating heatmap: {str(e)}")

# ======================
# DSS Knowledge Base
# ======================
with st.container():
    st.header("3. DSS Knowledge Base")
    tab1, tab2 = st.tabs(["Crop Guidelines", "About This System"])
    
with tab1:
    focus_crops = sorted(df['Crop'].unique())
    for crop_name in focus_crops:
        with st.expander(f"{crop_name.upper()} GUIDELINES"):
            try:
                crop_data = df[df['Crop'].str.lower() == crop_name.lower()]
                crop_data = crop_data.dropna(subset=[
                    'optimal storage temp(degree c)',
                    'spoilage rate at optimal temp(%)per week'
                ])
                
                if not crop_data.empty:
                    avg_temp = crop_data['optimal storage temp(degree c)'].mean()
                    avg_spoilage = crop_data['spoilage rate at optimal temp(%)per week'].mean()
                    
                    st.metric("Optimal Storage Temp", f"{avg_temp:.1f}°C")
                    st.metric("Avg Weekly Spoilage", f"{avg_spoilage:.1f}%")
                    
                    top_locs = crop_data['cold storage location'].value_counts().head(3)
                    if not top_locs.empty:
                        st.write("**Top Storage Facilities:**")
                        for loc, count in top_locs.items():
                            st.markdown(f"- {loc} ({count} farms served)")
                    else:
                        st.warning("No storage facility data available")
                else:
                    st.warning(f"No data available for {crop_name}")
            except Exception as e:
                st.error(f"Error loading {crop_name} data: {str(e)}")
    
with tab2:
    st.markdown("""
    ## About AgriSmart DSS

    **Youth-Focused Decision Support**  
    Designed for young Nigerian farmers to:
    - Locate nearest cold storage in 2 clicks
    - Compare transport/storage costs instantly
    - Reduce losses via science-backed recommendations

    **Key Features**:
    - Mobile-first design (works on basic smartphones)
    - Low-data usage mode
    - Partnership with 28+ ColdHubs locations

    **Development Progress**:
    1. Phase 1: Live MVP with 1,000 farm dataset (current)
    2. Phase 2: Real-time price integration (Q3 2025)
    3. Phase 3: AI loss prediction (Q1 2026)

    **Data Sources**:
    - Primary Data: 
      - 1,000 farm records (collected May 2025)
      - ColdHubs facility network (28 states)
      - Transport cost surveys (₦3,791/km avg)
    - Research Partners:
      - NARO storage guidelines
      - FAO spoilage rate studies
    """)

# ======================
# Bonus Section
# ======================
st.header("Regional Investment Opportunities")
with st.expander("View Top Infrastructure Needs", expanded=False):
    
    investment_needs = {
        "Tomatoes": ["Cold storage hubs", "Evaporative coolers"],
        "Yams": ["Solar dryers", "Ventilated warehouses"],
        "Okra": ["Cooling systems", "Packaging lines"],          
        "Cabbage": ["Refrigerated transport", "Pre-coolers"],    
        "Peppers": ["Drying facilities", "Controlled atmosphere storage"]
    }.get(crop, ["General storage improvement"])
    
    st.write(f"**Priority investments for {crop}:**")
    for need in investment_needs:
        st.markdown(f"- {need}")

st.subheader("Investment ROI Estimates")
roi_table = {
    "Project": ["Cold Storage Hub", "Processing Center", "Mobile Cooling Units"],
    "ROI (Years)": [3.2, 4.5, 2.8],  
    "Key Benefit": [
        "40-60% spoilage reduction (best for tomatoes/yam)",
        "Value addition for 80% of produce (okra/cabbage)",
        "Youth-friendly low-cost entry (₦50k starter kits)"  
    ]
}
st.table(pd.DataFrame(roi_table))

# Footer
st.markdown("---")
st.caption("""
Developed for AgriConnect Summit Hackathon | Data sources: FMARD, FAO, NARO  
Team Members: Ibrahim Yisau | Osazuwa Micheal | Hauwa Salihu | Yussuff Yussuff  
Contact: i.yisau@gmail.com | Streamlit App | All rights reserved © 2025
""")
