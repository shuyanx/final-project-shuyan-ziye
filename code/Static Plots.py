# Static Plots

# Set Up
import pandas as pd
import geopandas as gpd
import altair as alt
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib as mpl
from pathlib import Path

alt.data_transformers.disable_max_rows()

# Load datasets
data_path = Path("data/derived-data/cleaned_data.csv")
health_county = pd.read_csv(data_path, dtype={"CountyFIPS": str})

# Disease Prevalence Boxplot
prevalence_df = health_county.melt(
    id_vars=["CountyName"],
    value_vars=[
        "DIABETES_CrudePrev",
        "DEPRESSION_CrudePrev",
        "CHD_CrudePrev"
    ],
    var_name="Disease",
    value_name="Prevalence"
)

prevalence = alt.Chart(prevalence_df).mark_boxplot().encode(
    x=alt.X(
        "Disease:N",
        title="Disease",
        sort=["DIABETES_CrudePrev", "CHD_CrudePrev", "DEPRESSION_CrudePrev"],
        axis=alt.Axis(
            labelExpr="{'DIABETES_CrudePrev':'Diabetes','CHD_CrudePrev':'CHD','DEPRESSION_CrudePrev':'Depression'}[datum.label]"
        )
    ),
    y=alt.Y(
        "Prevalence:Q",
        title="Prevalence (%)"
    ),
    color=alt.Color(
        "Disease:N",
        legend=alt.Legend(
            title="Disease",
            labelExpr="{'DIABETES_CrudePrev':'Diabetes', 'CHD_CrudePrev':'CHD','DEPRESSION_CrudePrev':'Depression'}[datum.label]"
        )
    )
).properties(
    width=400,
    height=400,
    title="Disease Prevalence Descriptive Statistics"
)

prevalence

df = health_county[
    (health_county["DIABETES_CrudePrev"] > 0) & 
    (health_county["CHD_CrudePrev"] > 0) & 
    (health_county["DEPRESSION_CrudePrev"] > 0)
    ].copy()

diabetes = alt.Chart(df).mark_bar().encode(
    x = alt.X("DIABETES_CrudePrev:Q", 
    bin=alt.Bin(step=2), 
    title="Diabetes (%)",
    scale=alt.Scale(domain=[0, 36]),
    axis=alt.Axis(values=list(range(0,36,2)))),
    y = alt.Y("count()", title="Number of Counties", scale=alt.Scale(domain=[0, 1200]))
).properties(width=100, height=100)

chd = alt.Chart(df).mark_bar().encode(
    x = alt.X("CHD_CrudePrev:Q", 
    bin=alt.Bin(step=2), 
    title="CHD (%)", 
    scale=alt.Scale(domain=[0, 36]),
    axis=alt.Axis(values=list(range(0,36,2)))),
    y = alt.Y("count()", title="Number of Counties", scale=alt.Scale(domain=[0, 1200]))
).properties(width=100, height=100)

depression = alt.Chart(df).mark_bar().encode(
    x = alt.X("DEPRESSION_CrudePrev:Q", 
    bin=alt.Bin(step=2), 
    title="Depression (%)", 
    scale=alt.Scale(domain=[0, 36]),
    axis=alt.Axis(values=list(range(0,36,2)))),
    y = alt.Y("count()", title="Number of Counties", scale=alt.Scale(domain=[0, 1200]))
).properties(width=100, height=100)

diabetes | chd | depression


bins = [0,5,10,15,20,25,30,35,40,45,50,np.inf]
order = ["0–5","5–10","10–15","15–20","20–25","25–30","30–35","35–40","40–45","45–50","≥50"]
labels = order

health_county["physician_bins"] = pd.cut(
    health_county["physicians_per10k"],
    bins=bins,
    labels=labels,
    include_lowest=True
)

health_county["bed_bins"] = pd.cut(
    health_county["beds_per10k"],
    bins=bins,
    labels=labels,
    include_lowest=True
)

df_phys = health_county.dropna(subset=["physician_bins"])
df_bed = health_county.dropna(subset=["bed_bins"])

physicians_coverage = alt.Chart(df_phys).mark_bar().encode(
    x=alt.X(
        "physician_bins:N",
        sort=order,
        title="Physicians per 10k Adults"
    ),
    y=alt.Y(
        "count()",
        title="Number of Counties",
        scale=alt.Scale(domain=[0,900]),
        axis=alt.Axis(tickCount=10)
    )
).properties(width=100, height=150)

beds_coverage = alt.Chart(df_bed).mark_bar().encode(
    x=alt.X(
        "bed_bins:N",
        sort=order,
        title="Beds per 10k Adults"
    ),
    y=alt.Y(
        "count()",
        title="Number of Counties",
        scale=alt.Scale(domain=[0,900]),
        axis=alt.Axis(tickCount=10)
    )
).properties(width=100, height=150)


model_map = {
    "CHD_CrudePrev": [
        "physicians_per10k",
        "cardiologists_per10k",
        "beds_per10k",
        "beds_acute_per10k",
        "beds_icu_per10k"
    ],
    "DIABETES_CrudePrev": [
        "physicians_per10k",
        "general_internal_med_per10k",
        "beds_per10k",
        "beds_acute_per10k",
        "beds_icu_per10k"
    ],
    "DEPRESSION_CrudePrev": [
        "physicians_per10k",
        "psych_per10k",
        "beds_per10k",
        "beds_acute_per10k",
        "beds_icu_per10k"
    ]
}
results = []

for disease, supplies in model_map.items():
    for supply in supplies:
        df = health_county[[disease, supply]].dropna()
        X = sm.add_constant(df[supply])
        y = df[disease]
        model = sm.OLS(y, X).fit()
        coef = model.params[supply]
        results.append({
            "Disease": disease,
            "Supply": supply,
            "Coefficient": coef
        })

coef_df = pd.DataFrame(results)

rename_supply = {
    "physicians_per10k":"Physicians Count",
    "cardiologists_per10k":"Cardiologists Count",
    "general_internal_med_per10k":"Internal Medicine Physicians Count",
    "psych_per10k":"Psychiatrists Count",
    "beds_per10k":"Total Beds Count",
    "beds_acute_per10k":"Acute Beds Count",
    "beds_icu_per10k":"ICU Beds Count"
}

rename_disease = {
    "CHD_CrudePrev":"CHD",
    "DIABETES_CrudePrev":"Diabetes",
    "DEPRESSION_CrudePrev":"Depression"
}

coef_df["Supply"] = coef_df["Supply"].replace(rename_supply)

coef_df["Disease"] = coef_df["Disease"].replace(rename_disease)

max_coef = abs(coef_df["Coefficient"]).max()

heatmap = alt.Chart(coef_df).mark_rect().encode(
    x=alt.X("Supply:N", title="Healthcare Supply per 10k Adults",
    sort=[
        "Physicians Count",
        "Total Beds Count",
        "Acute Beds Count",
        "ICU Beds Count",
        "Cardiologists Count",
        "Internal Medicine Physicians Count",
        "Psychiatrists Count",
    ]),
    y=alt.Y("Disease:N", title="Disease Prevalence",
            sort=["CHD", "Diabetes", "Depression"]),
    color=alt.Color(
        "Coefficient:Q",
        scale=alt.Scale(
            scheme="redblue",
            domain=[-max_coef, max_coef]
        ),
        title="Regression Coefficient"
    )
).properties(
    width=400,
    height=200,
    title="Single-Variable Regressions: Disease Prevalence vs Supply per 10k Adults"
)

heatmap


health_gis = gpd.read_parquet("data/derived-data/cleaned_data_gis.parquet")
health_gis_proj = health_gis.to_crs(epsg=5070)

health_gis_proj = health_gis_proj[
    ~health_gis_proj["STATEFP"].isin(["02","15","72"])
]

fig, axes = plt.subplots(1, 3, figsize=(18,6))
disease_bins = [0,5,10,15,20,25,30,35]

disease_map = health_gis_proj[
    (health_gis_proj["DIABETES_CrudePrev"] > 0) &
    (health_gis_proj["CHD_CrudePrev"] > 0) &
    (health_gis_proj["DEPRESSION_CrudePrev"] > 0)
].copy()

disease_map.plot(
    column="DIABETES_CrudePrev",
    cmap="YlOrRd",
    scheme="user_defined",
    classification_kwds={"bins": disease_bins},
    linewidth=0.1,
    edgecolor="white",
    legend=False,
    ax=axes[0]
)
axes[0].set_title("Diabetes")
axes[0].axis("off")

disease_map.plot(
    column="CHD_CrudePrev",
    cmap="YlOrRd",
    scheme="user_defined",
    classification_kwds={"bins": disease_bins},
    linewidth=0.1,
    edgecolor="white",
    legend=False,
    ax=axes[1]
)
axes[1].set_title("CHD")
axes[1].axis("off")

disease_map.plot(
    column="DEPRESSION_CrudePrev",
    cmap="YlOrRd",
    scheme="user_defined",
    classification_kwds={"bins": disease_bins},
    linewidth=0.1,
    edgecolor="white",
    legend=False,
    ax=axes[2]
)
axes[2].set_title("Depression")
axes[2].axis("off")

cmap = mpl.cm.YlOrRd
norm = mpl.colors.BoundaryNorm(disease_bins, cmap.N)

sm = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])

plt.subplots_adjust(bottom=-0.05)

cbar = fig.colorbar(
    sm,
    ax=axes,
    orientation="horizontal",
    fraction=0.05,
    pad=0.08
)

cbar.set_label("Disease Prevalence (%)")

plt.tight_layout()
plt.show()


fig, axes = plt.subplots(1, 2, figsize=(8,4))
supply_bins = [0,5,10,20,30,40,50,np.inf]
supply_labels = ["0–5","5–10","10–20","20–30","30–40","40-50",">=50"]

health_gis_proj["physician_cat"] = pd.cut(
    health_gis_proj["physicians_per10k"],
    bins=supply_bins,
    labels=supply_labels,
    include_lowest=True
)

health_gis_proj.plot(
    column="physician_cat",
    cmap="Blues",
    linewidth=0.1,
    edgecolor="black",
    legend=True,
    ax=axes[0],
    missing_kwds={
        "color": "grey",
        "label": "Missing data"
    },
    legend_kwds={
        "title":"Physicians per 10k Adults",
        "loc":"lower right",
        "bbox_to_anchor":(1.25, 0),
        "frameon":True,
        "fontsize":5,
        "title_fontsize":6,
        "markerscale":0.7
    }
)

axes[0].set_title("County-Level Physician Supply (per 10k Adults)", fontsize=8)
axes[0].axis("off")

health_gis_proj["bed_cat"] = pd.cut(
    health_gis_proj["beds_per10k"],
    bins=supply_bins,
    labels=supply_labels,
    include_lowest=True
)

health_gis_proj.plot(
    column="bed_cat",
    cmap="Blues",
    linewidth=0.1,
    edgecolor="black",
    legend=True,
    ax=axes[1],
    missing_kwds={
        "color": "grey",
        "label": "Missing data"
    },
    legend_kwds={
        "title":"Beds per 10k Adults",
        "loc":"lower right",
        "bbox_to_anchor":(1.2, 0),
        "frameon":True,
        "fontsize":5,
        "title_fontsize":6,
        "markerscale":0.7
    }
)

axes[1].set_title("County-Level Bed Supply (per 10k Adults)", fontsize=8)
axes[1].axis("off")

plt.tight_layout()
plt.show()