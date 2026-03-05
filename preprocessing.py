# Set Up
import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path
import requests
import zipfile
import io


# Create The Function for Aggregation
def aggregate_to_county(df):

    df["TotalPop18plus"] = (
        df["TotalPop18plus"]
        .astype(str)
        .str.replace(",", "")
        .astype(float)
    )

    prev_cols = [
        col for col in df.columns
        if col.endswith("_CrudePrev")
    ]

    for col in prev_cols:
        df[col + "_Cases"] = (
            df[col] / 100 *
            df["TotalPop18plus"]
        ).round(0)

    health_county = df.groupby(
        [
            "StateAbbr",
            "StateDesc",
            "CountyName",
            "CountyFIPS"
        ]
    ).sum(numeric_only=True).reset_index()

    for col in prev_cols:

        health_county[col] = (
            health_county[col + "_Cases"]
            /
            health_county["TotalPop18plus"]
            * 100
        ).round(4)

    return health_county


# Download ACS 2023 Median Household Income
def download_income_data():

    print("Downloading ACS 2023 Median Household Income...")

    url = (
        "https://api.census.gov/data/2023/acs/acs5?get=NAME,B19013_001E&for=county:*"
    )

    r = requests.get(url, timeout=120)

    if r.status_code != 200:
        raise RuntimeError("Failed to download income data.")

    data = r.json()

    income = pd.DataFrame(
        data[1:],
        columns=data[0]
    )

    income = income.rename(
        columns={
            "B19013_001E": "MedianIncome"
        }
    )

    income["CountyFIPS"] = (
        income["state"]
        + income["county"]
    )

    income["MedianIncome"] = pd.to_numeric(
        income["MedianIncome"],
        errors="coerce"
    )

    income = income[
        ["CountyFIPS", "MedianIncome"]
    ]

    return income


# Load Data and Clean Data
def build_data():

    PROJECT_ROOT = Path(__file__).parent
    
    health = pd.read_csv(
        PROJECT_ROOT / "data" / "Health.csv"
    )

    health_professional = pd.read_csv(
        PROJECT_ROOT / "data" / "AHRF" / "AHRF2025hp.csv"
    )

    health_facility = pd.read_csv(
        PROJECT_ROOT / "data" / "AHRF" / "AHRF2025hf.csv"
    )

    shp_path = PROJECT_ROOT / "data" / "tl_2025_us_county.shp"

    # Only download shapefile if it does not exist
    if not shp_path.exists():

        print("Downloading Census TIGER county shapefile...")

        url = ("https://www2.census.gov/geo/tiger/TIGER2025/COUNTY/tl_2025_us_county.zip")

        r = requests.get(url, timeout=120)
        
        if r.status_code != 200:
            raise RuntimeError("Failed to download GIS data.")
        
        shp_path.parent.mkdir(parents=True, exist_ok=True)
        
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(shp_path.parent)
        
        print("GIS downloaded.")
    
    counties = gpd.read_file(shp_path)

    income = download_income_data()

    health["CountyFIPS"] = (
        health["CountyFIPS"]
        .astype(str)
        .str.zfill(5)
    )

    health = health.drop(
        columns=["TractFIPS", "Geolocation"]
    )

    health = health.drop(
        columns=[
            col for col in health.columns
            if "95CI" in col
        ]
    )

    health_professional["fips_st_cnty"] = (
        health_professional["fips_st_cnty"]
        .astype(int)
        .astype(str)
        .str.zfill(5)
    )

    health_facility["fips_st_cnty"] = (
        health_facility["fips_st_cnty"]
        .astype(int)
        .astype(str)
        .str.zfill(5)
    )

    health_professional = health_professional[
        [
            "fips_st_cnty",
            "md_nf_activ_23",
            "md_nf_psych_23",
            "md_nf_card_dis_23",
            "md_nf_genintmed_23",
            "md_nf_ped_gen_23"
        ]
    ]

    health_professional = health_professional.rename(
        columns={
            "md_nf_activ_23":"physicians_total",
            "md_nf_psych_23":"psychiatrists",
            "md_nf_card_dis_23":"cardiologists",
            "md_nf_genintmed_23":"general_internal_med",
            "md_nf_ped_gen_23":"pediatricians"
        }
    )

    health_professional["physicians_total"] = (
        health_professional["physicians_total"]
        -
        health_professional["pediatricians"]
    )

    health_professional = health_professional.drop(
        columns=["pediatricians"]
    )

    health_facility = health_facility[
        [
            "fips_st_cnty",
            "hosp_beds_23",
            "stgh_hosp_beds_23",
            "stgh_med_surg_icu_beds_23"
        ]
    ]

    health_facility = health_facility.rename(
        columns={
            "hosp_beds_23":"beds_total",
            "stgh_hosp_beds_23":"beds_acute",
            "stgh_med_surg_icu_beds_23":"beds_icu"
        }
    )

    # Run The Function for Aggregation
    health_county = aggregate_to_county(health)

    # Merge DataSets
    health_county = health_county.merge(
        health_professional,
        left_on="CountyFIPS",
        right_on="fips_st_cnty",
        how="inner"
    ).drop(columns=["fips_st_cnty"])

    health_county = health_county.merge(
        health_facility,
        left_on="CountyFIPS",
        right_on="fips_st_cnty",
        how="inner"
    ).drop(columns=["fips_st_cnty"])

    health_county = health_county.merge(
        income,
        on="CountyFIPS",
        how="left"
    )

    # Add Columns Needed
    health_county["physicians_per10k"] = np.where(
        health_county["physicians_total"] > 0,
        health_county["physicians_total"] /
        health_county["TotalPop18plus"] * 10000,
        np.nan
    )
    
    health_county["general_internal_med_per10k"] = np.where(
        health_county["physicians_total"] > 0,
        health_county["general_internal_med"] /
        health_county["TotalPop18plus"] * 10000,
        np.nan
    )
    
    health_county["cardiologists_per10k"] = np.where(
        health_county["physicians_total"] > 0,
        health_county["cardiologists"] /
        health_county["TotalPop18plus"] * 10000,
        np.nan
    )
    
    health_county["psych_per10k"] = np.where(
        health_county["physicians_total"] > 0,
        health_county["psychiatrists"] /
        health_county["TotalPop18plus"] * 10000,
        np.nan
    )
    
    health_county["beds_per10k"] = np.where(
        health_county["beds_total"] > 0,
        health_county["beds_total"] /
        health_county["TotalPop18plus"] * 10000,
        np.nan
    )
    
    health_county["beds_acute_per10k"] = np.where(
        health_county["beds_acute"] > 0,
        health_county["beds_acute"] /
        health_county["TotalPop18plus"] * 10000,
        np.nan
    )

    health_county["beds_icu_per10k"] = np.where(
        health_county["beds_icu"] > 0,
        health_county["beds_icu"] /
        health_county["TotalPop18plus"] * 10000,
        np.nan
    )
    
    health_county["pop_quintile"] = pd.qcut(
        np.log1p(health_county["TotalPop18plus"]),
        5,
        labels=[
            "Very Small",
            "Small",
            "Medium",
            "Large",
            "Very Large"
        ]
    )

    # Fix dtype warning by initializing column as object
    def create_supply_groups(df, supply_var, new_col_name):

        df[new_col_name] = pd.Series(index=df.index, dtype="object")

        zero_mask = df[supply_var] == 0

        df.loc[zero_mask, new_col_name] = "No Providers"

        nonzero = df.loc[
            ~zero_mask & df[supply_var].notna(),
            supply_var
        ]

        df.loc[nonzero.index, new_col_name] = pd.qcut(
            nonzero,
            5,
            labels=["Very Low", "Low", "Medium", "High", "Very High"]
        )

        df[new_col_name] = pd.Categorical(
            df[new_col_name],
            categories=[
                "No Providers",
                "Very Low",
                "Low",
                "Medium",
                "High",
                "Very High"
            ],
            ordered=True
        )
        
    create_supply_groups(
        health_county,
        "general_internal_med_per10k",
        "diabetes_supply_group"
    )
    
    create_supply_groups(
        health_county,
        "cardiologists_per10k",
        "chd_supply_group"
    )
    
    create_supply_groups(
        health_county,
        "psych_per10k",
        "depression_supply_group"
    )

    health_gis = health_county.merge(
        counties,
        left_on="CountyFIPS",
        right_on="GEOID",
        how="inner"
    )

    health_gis = gpd.GeoDataFrame(
        health_gis,
        geometry="geometry",
        crs=counties.crs
    )
    
    
    output = PROJECT_ROOT / "data" / "cleaned_data.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    health_county.to_csv(output, index=False)

    health_gis["geometry"] = health_gis.geometry.simplify(0.01, preserve_topology=True)

    float_cols = health_gis.select_dtypes(include="float64").columns
    health_gis[float_cols] = health_gis[float_cols].astype("float32")

    gis_output = PROJECT_ROOT / "data" / "cleaned_data_gis.parquet"
    health_gis.to_parquet(gis_output, index=False, compression="zstd")

    print("Derived datasets created.")


if __name__ == "__main__":

    build_data()