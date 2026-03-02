import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import altair as alt
from pathlib import Path
from preprocessing import build_data

st.set_page_config(layout="wide")

@st.cache_data(show_spinner=True)
def load_health_county():

    data_path = Path("data/cleaned_data.csv")

    if not data_path.exists():
        build_data()

    return pd.read_csv(
        data_path,
        dtype={"CountyFIPS":str}
    )


@st.cache_data(show_spinner=True)
def load_health_gis():

    gis_path = Path("data/cleaned_data_gis.parquet")

    if not gis_path.exists():
        build_data()

    gdf = gpd.read_parquet(gis_path)

    # FIX MAP SCALE (remove AK HI PR)
    gdf = gdf[
        ~gdf["STATEFP"].isin(["02","15","72"])
    ]

    return gdf


health_county = load_health_county()
health_gis_proj = load_health_gis()

st.title("Targeted Physician Supply Policy Simulator")

st.markdown("""
Separate regressions are estimated within baseline supply groups.
Users can simulate increases or decreases in physician supply.
Population control uses adult population (18+).
""")

disease = st.sidebar.selectbox(
    "Select Disease",
    ["Diabetes","CHD","Depression"]
)

mapping = {

    "Diabetes":(
        "DIABETES_CrudePrev",
        "general_internal_med_per10k",
        "diabetes_supply_group",
        "Internal Medicine Physicians",
        "Reds"
    ),

    "CHD":(
        "CHD_CrudePrev",
        "cardiologists_per10k",
        "chd_supply_group",
        "Cardiologists",
        "Oranges"
    ),

    "Depression":(
        "DEPRESSION_CrudePrev",
        "psych_per10k",
        "depression_supply_group",
        "Psychiatrists",
        "Purples"
    )

}

disease_var,supply_var,group_var,doctor_label,map_cmap = mapping[disease]

order=[
"No Providers",
"Very Low",
"Low",
"Medium",
"High",
"Very High"
]

df = health_county.dropna(

subset=[
disease_var,
supply_var,
"TotalPop18plus",
"beds_per10k",
"MedianIncome",
group_var
]

).copy()

df[group_var]=pd.Categorical(
df[group_var],
categories=order,
ordered=True
)

# FULL MODEL
X_full=sm.add_constant(

df[[

supply_var,
"TotalPop18plus",
"beds_per10k",
"MedianIncome"

]]

)

y_full=df[disease_var]

full_model=sm.OLS(y_full,X_full).fit()

betas={}
group_stats=[]

for g in order:

    sub=df[df[group_var]==g]

    if len(sub)==0:
        continue

    group_stats.append({

        "Supply Group":g,
        "Number of Counties":len(sub),

        "Total Adult Population":
        int(sub["TotalPop18plus"].sum()),

        "Average Beds per 10k":
        sub["beds_per10k"].mean(),

        "Median Income (Average)":
        sub["MedianIncome"].median()

    })

    if g=="No Providers":
        continue

    if sub[supply_var].nunique()>1:

        X=sm.add_constant(

        sub[[

        supply_var,
        "TotalPop18plus",
        "beds_per10k",
        "MedianIncome"

        ]]

        )

        y=sub[disease_var]

        model=sm.OLS(y,X).fit()

        betas[g]=model.params[supply_var]


group_stats_df=pd.DataFrame(group_stats)

st.sidebar.markdown("### Supply Adjustment by Group")

delta_dict={}

for g in order:

    if g=="No Providers":

        delta_dict[g]=st.sidebar.slider(

        f"{g} Set {doctor_label} (per 10k)",
        0.0,5.0,0.0,0.5

        )

    else:

        delta_dict[g]=st.sidebar.slider(

        f"{g} Group: Change in {doctor_label} (per 10k)",
        -5.0,5.0,0.0,0.5

        )

df["predicted_change"]=0

for g,beta in betas.items():

    delta=delta_dict[g]

    mask=df[group_var]==g

    df.loc[mask,"predicted_change"]=beta*delta


mask_np=df[group_var]=="No Providers"

if mask_np.sum()>0:

    df["pred_old"]=full_model.predict(

    sm.add_constant(

    df[[

    supply_var,
    "TotalPop18plus",
    "beds_per10k",
    "MedianIncome"

    ]]

    )

    )

    df["new_supply"]=df[supply_var]

    df.loc[mask_np,"new_supply"]=delta_dict["No Providers"]

    X_new=sm.add_constant(

    df[[

    "new_supply",
    "TotalPop18plus",
    "beds_per10k",
    "MedianIncome"

    ]]

    )

    df["pred_new"]=full_model.predict(X_new)

    df.loc[mask_np,"predicted_change"]=(
    df.loc[mask_np,"pred_new"]-
    df.loc[mask_np,"pred_old"]
    )


total_weighted_change=(

df["predicted_change"]
*df["TotalPop18plus"]

).sum()/df["TotalPop18plus"].sum()


left,right=st.columns([1.2,1])

with left:

    st.subheader("Current Disease Distribution")

    fig,ax=plt.subplots(figsize=(7,5))

    health_gis_proj.plot(

    column=disease_var,
    cmap=map_cmap,
    linewidth=0.05,
    edgecolor="white",
    legend=True,
    ax=ax

    )

    ax.axis("off")

    st.pyplot(fig)


with right:

    st.subheader("Predicted Change by Supply Group")

    impact_df=(

    df.groupby(group_var,observed=False)

    .agg(

    Initial_Mean_Prevalence=
    (disease_var,"mean"),

    Mean_Change=
    ("predicted_change","mean")

    )

    .reset_index()

    .rename(columns={

    group_var:"Physician Supply Group",

    "Initial_Mean_Prevalence":
    "Initial Prevalence on Average (%)",

    "Mean_Change":
    "Average Predicted Change (pp)"

    })

    )

    impact_df=impact_df.sort_values(
    "Physician Supply Group"
    )

    st.dataframe(impact_df)

    chart=alt.Chart(impact_df).mark_bar().encode(

    x=alt.X(

    "Physician Supply Group:N",
    sort=order,
    title=f"{doctor_label} Supply Group"

    ),

    y=alt.Y(

    "Average Predicted Change (pp):Q",
    title="Average Predicted Change (pp)"

    ),

    color=alt.condition(

    alt.datum["Average Predicted Change (pp)"]>0,

    alt.value("#d73027"),

    alt.value("#1a9850")

    )

    ).properties(width=500,height=350)

    st.altair_chart(chart,width="stretch")


st.markdown("### Overall Population-Weighted Change")

st.metric(

"Change in Prevalence (percentage points)",

f"{total_weighted_change:.3f}"

)

st.markdown("### Sample Statistics")

st.dataframe(group_stats_df)