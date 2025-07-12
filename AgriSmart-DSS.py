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

# Validate required columns
def validate_data(df):
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

# Clean column names and values
df.columns = df.columns.str.strip()
df['Crop'] = df['Crop'].str.strip().str.title()
df['Farm Location'] = df['Farm Location'].str.strip()

# Ensure transport time columns are float
for col in ['farm to cold storage(hrs)', 'cold storage to market(hrs)']:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

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
                "transport_cost": round(nearest['transport cost for 20 ton load(#/km)'] * nearest['farm to cold storage(km)'], -3)
            }
        return None
    except Exception as e:
        st.error(f"Error in recommendation: {str(e)}")
        return None

# ======================
# DSS USER INTERFACE
# ======================

st.title("🌱 AgriSmart Decision Support System")
st.markdown("""
**Reducing Post-Harvest Losses for Nigerian Farmers**  
*Built by - Team DSS*
""")

# Input form
with st.container():
    st.header("1. Enter Farm Details")
    col1, col2 = st.columns(2)
    with col1:
        farm_location = st.selectbox("SELECT FARM LOCATION", sorted(df['Farm Location'].unique()))
    with col2:
        crop = st.selectbox("SELECT CROP", sorted(df['Crop'].unique()))

# Crop-location combinations section
with st.expander("Valid Crop-Location Combinations"):
    grouped = df.groupby('Crop')['Farm Location'].unique().reset_index()
    for _, row in grouped.iterrows():
        crop_name = row['Crop']
        locations = ', '.join(sorted(row['Farm Location']))
        st.markdown(f"**{crop_name}**: {locations}")

# DSS Recommendation
if st.button("Generate Recommendations", type="primary"):
    rec = get_recommendations(farm_location, crop)

    if rec:
        st.header("2. DSS Analysis Report")
        cols = st.columns(3)
        cols[0].metric("Distance to Storage", f"{rec['storage_km']} km")
        cols[1].metric("Optimal Temp", f"{rec['optimal_temp']}°C")
        cols[2].metric("Weekly Spoilage", f"{rec['spoilage_rate']}%")

        with st.expander("Location Details"):
            st.markdown(f"""
            **Farm Location:** {farm_location}  
            **Nearest Cold Storage:** {rec['storage_name']} ({rec['storage_km']} km)  
            **Market:** {rec['market_name']} ({rec['market_km']} km from storage)
            """)

        with st.expander("Cost Breakdown"):
            st.markdown(f"""
            - **Cold Storage Cost:** {rec['storage_cost']}
            - **Transport Cost (20-ton):** ₦{rec['transport_cost']:,}
            - **Transit Time:** {rec['storage_hrs'] + rec['market_hrs']} hrs
            """)

    elif farm_location and crop:
        st.error("No recommendations available for this location and crop.")
        with st.expander("Why this happened and how to fix it"):
            valid_locs = df[df['Crop'].str.lower() == crop.strip().lower()]['Farm Location'].unique()
            if len(valid_locs) > 0:
                st.markdown(f"The crop **{crop}** is not recorded in **{farm_location}**.")
                st.markdown("Try one of these valid locations instead:")
                st.markdown(", ".join(sorted(valid_locs)))
            else:
                st.markdown(f"No data found for crop **{crop}**. Try a different crop.")

# ======================
# DSS Knowledge Base
# ======================
with st.container():
    st.header("3. DSS Knowledge Base")
    tab1, tab2 = st.tabs(["Crop Guidelines", "About This System"])

with tab1:
    for crop_name in sorted(df['Crop'].unique()):
        with st.expander(f"{crop_name.upper()} GUIDELINES"):
            crop_data = df[df['Crop'].str.lower() == crop_name.lower()]
            crop_data = crop_data.dropna(subset=[
                'optimal storage temp(degree c)',
                'spoilage rate at optimal temp(%)per week'
            ])
            if not crop_data.empty:
                st.metric("Optimal Temp", f"{crop_data['optimal storage temp(degree c)'].mean():.1f}°C")
                st.metric("Avg Spoilage Rate", f"{crop_data['spoilage rate at optimal temp(%)per week'].mean():.1f}%")
            else:
                st.warning("No data available")

# ======================
# Investment Section
# ======================
st.header("4. Investment Opportunities")
with st.expander("Priority Infrastructure by Crop", expanded=False):
    investment_needs = {
        "Tomatoes": ["Cold storage hubs", "Evaporative coolers"],
        "Yams": ["Solar dryers", "Ventilated warehouses"],
        "Okra": ["Cooling systems", "Packaging lines"],
        "Cabbage": ["Refrigerated transport", "Pre-coolers"],
        "Peppers": ["Drying facilities", "Controlled atmosphere storage"]
    }.get(crop, ["General cold storage support"])
    for item in investment_needs:
        st.markdown(f"- {item}")

st.subheader("Estimated ROI for Key Projects")
roi_data = {
    "Project": ["Cold Storage Hub", "Processing Center", "Mobile Cooling Units"],
    "ROI (Years)": [3.2, 4.5, 2.8],
    "Key Benefit": [
        "Up to 60% spoilage reduction",
        "Value-addition for local crops",
        "Affordable access for youth farmers"
    ]
}
st.table(pd.DataFrame(roi_data))

# ======================
# Footer
# ======================
st.markdown("---")
st.caption("""
AgriSmart DSS | For Startup Innovation Challenge 2025  
Team Members: Ibrahim Yisau, Osazuwa Michael, Hauwa Salihu, Yussuff Yussuff  
""")
