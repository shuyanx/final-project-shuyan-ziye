# preprocessing.py

import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path


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



def build_data():

    PROJECT_ROOT = Path(__file__).parent

    # Load Data
    
    health = pd.read_csv(
        PROJECT_ROOT / "Health.csv"
    )

    health_professional = pd.read_csv(
        PROJECT_ROOT / "AHRF" / "AHRF2025hp.csv"
    )

    health_facility = pd.read_csv(
        PROJECT_ROOT / "AHRF" / "AHRF2025hf.csv"
    )

    counties = gpd.read_file(
        PROJECT_ROOT /
        "tl_2025_us_county" /
        "tl_2025_us_county.shp"
    )


    # Clean Data

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


    # Aggregate

    health_county = aggregate_to_county(health)


    # Merge

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


    # Save Derived Dataset
    
    output = PROJECT_ROOT / "data" / "cleaned_data.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    health_county.to_csv(output, index=False)
    print("Derived dataset created.")


if __name__ == "__main__":

    build_data()