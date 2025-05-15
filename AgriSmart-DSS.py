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
        
    # Check for null values in key columns
    null_report = df[required_cols].isnull().sum()
    if null_report.sum() > 0:
        st.warning("Null values found:")
        st.write(null_report[null_report > 0])
        
    return True

if not validate_data(df):
    st.stop()

# Clean data 
df = df.dropna(subset=['Crop', 'Farm Location'])
df['Crop'] = df['Crop'].str.strip().str.title()  # Standardize case
df['Farm Location'] = df['Farm Location'].str.strip()
    
# Clean column names if needed
df.columns = df.columns.str.strip()

if st.checkbox("Show sample data"):
    st.write(df.sample(5))
# ======================
# DSS CORE FUNCTIONS 
# ======================
def get_recommendations(farm_loc, crop_type):
    """Case-insensitive search with exact matching"""
    try:
        # Convert both to lowercase for comparison
        results = df[
            (df['Farm Location'].str.strip().str.lower() == farm_loc.strip().lower()) & 
            (df['Crop'].str.strip().str.lower() == crop_type.strip().lower())
        ]
        
        if results.empty:
            # Try fuzzy matching if exact match fails
            results = df[
                df['Farm Location'].str.strip().str.lower().str.contains(farm_loc.strip().lower()) & 
                df['Crop'].str.strip().str.lower().str.contains(crop_type.strip().lower())
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
        
    # Get the nearest storage facility
    nearest = results.sort_values('farm to cold storage(km)').iloc[0]
    
    return {
        # Distances
        "storage_name": nearest['cold storage location'],
        "storage_km": nearest['farm to cold storage(km)'],
        "storage_hrs": nearest['farm to cold storage(hrs)'],
        "market_name": nearest['market location'],
        "market_km": nearest['cold storage to market(km)'],
        "market_hrs": nearest['cold storage to market(hrs)'],
        
        # Crop specs
        "optimal_temp": nearest['optimal storage temp(degree c)'],
        "spoilage_rate": nearest['spoilage rate at optimal temp(%)per week'],
        
        # Costs
        "storage_cost": f"₦{nearest['storage cost(#/crate/day)']}/crate/day",
        "transport_cost": f"₦{int(nearest['transport cost for 20 ton load(#/km)'] * nearest['farm to cold storage(km)']):,}"
    }

if st.button("Generate Recommendations", type="primary"):
    st.write(f"Debug - Searching for: Location='{farm_location}', Crop='{crop}'")
    st.write(f"Available Locations: {df['Farm Location'].unique()[:5]}...")
    st.write(f"Available Crops: {df['Crop'].unique()}")
    
    rec = get_recommendations(farm_location, crop)

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
        # Get unique locations from dataset
        farm_location = st.selectbox(
            "SELECT FARM LOCATION",
            options=sorted(df['Farm Location'].unique()),
            help="Choose your farm location"
        )
    with col2:
        # Focus on the 5 key crops
        crop = st.selectbox(
            "SELECT CROP",
            options=["Tomato", "Okra", "Cabbage", "Yam", "Pepper"],
            help="Choose your crop"
        )

# DSS Analysis
if st.button("Generate Recommendations", type="primary"):
    rec = get_recommendations(farm_location, crop)
    
    if not rec:
        st.error("No recommendations found for this location/crop combination")
    else:
        st.header("2. DSS Analysis Report")
        
        # Key Metrics
        cols = st.columns(3)
        cols[0].metric("Distance to Storage", f"{rec['storage_km']} km")
        cols[1].metric("Optimal Temp", f"{rec['optimal_temp']}°C")
        cols[2].metric("Weekly Spoilage", f"{rec['spoilage_rate']}%")
        
        # Location Details
        with st.expander("Location Details"):
            st.markdown(f"""
            **Farm Location:** {farm_location}  
            **Nearest Cold Storage:** {rec['storage_name']} ({rec['storage_km']} km away)  
            **Recommended Market:** {rec['market_name']} ({rec['market_km']} km from storage)
            """)
        
        # Cost Analysis
        with st.expander("Cost Breakdown"):
            st.markdown(f"""
            - **Cold Storage Cost:** {rec['storage_cost']}
            - **Estimated Transport Cost (20-ton):** {rec['transport_cost']}
            - **Total Transit Time:** {rec['storage_hrs'] + rec['market_hrs']} hours
            """)
        
        # Heatmap Visualization
        with st.expander("Regional Spoilage Rates"):
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
            
# DSS Knowledge Base
with st.container():
    st.header("3. DSS Knowledge Base")
    tab1, tab2 = st.tabs(["Crop Guidelines", "About This System"])
    
with tab1:
    focus_crops = ["Tomato", "Okra", "Cabbage", "Yam", "Pepper"]
    for crop_name in focus_crops:
        with st.expander(f"{crop_name.upper()} GUIDELINES"):
            try:
                # Get and clean data
                crop_data = df[df['Crop'].str.strip().str.lower() == crop_name.lower().strip()]
                crop_data = crop_data.dropna(subset=[
                    'optimal storage temp(degree c)',
                    'spoilage rate at optimal temp(%)per week'
                ])
                
                if not crop_data.empty:
                    # Calculate metrics
                    avg_temp = crop_data['optimal storage temp(degree c)'].mean()
                    avg_spoilage = crop_data['spoilage rate at optimal temp(%)per week'].mean()
                    
                    # Display metrics
                    st.metric("Optimal Storage Temp", 
                             f"{avg_temp:.1f}°C" if not pd.isna(avg_temp) else "Data unavailable")
                    st.metric("Avg Weekly Spoilage", 
                             f"{avg_spoilage:.1f}%" if not pd.isna(avg_spoilage) else "Data unavailable")
                    
                    # Show top locations
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
        
# Investment Priorities (Bonus Feature)
st.header("Regional Investment Opportunities")
with st.expander("View Top Infrastructure Needs", expanded=False):
    
    # Dynamic needs based on selected crop
   investment_needs = {
    "tomato": ["Cold storage hubs", "Evaporative coolers"],
    "yam": ["Solar dryers", "Ventilated warehouses"],
    "okra": ["Cooling systems", "Packaging lines"],          
    "cabbage": ["Refrigerated transport", "Pre-coolers"],    
    "pepper": ["Drying facilities", "Controlled atmosphere storage"]
    }.get(crop, ["General storage improvement"])
    
st.write(f"**Priority investments for {crop.capitalize()}:**")
for need in investment_needs:
        st.markdown(f"- {need}")
    
# ROI Calculation
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
Team Members: Ibrahim Yisau|Osazuwa Micheal|Hauwa Salihu|Yussuff Yussuff | Contact: i.yisau@gmail.com  
Streamlit App | All rights reserved © 2025
""")
