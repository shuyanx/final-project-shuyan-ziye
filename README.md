# Disease Prevalence and Health Resource Distrubution in the US
## Does healthcare supply relate to disease prevalence across U.S. counties?
Data and Programming II Final Project (Winter 2026)

Team members:
Shuyan Xin & Ziye Yang

Qmd: PROJECT_ROOT / "code" / "write up.qmd"

Streamlit dashboard: https://final-project-shuyan-ziye-6pkom6vbzap9avqyw3m3ek.streamlit.app/

## Following Revisions after Presentation
We received constructive suggestions from Professor Ganong after the March 3 presentation, and we made improvements and clarifications accordingly.
- Visual in relationship plot: We now use uniform color coding for six different supply tiers and introduced a clearer regression line to show a more obvious overall trend. 
- Enhanced map color contrast: We now use higher-contrast colors to distinguish regions with different prevalence and supply levels on the map, making the patterns and conclusions clearer. The "YlOrRd" color scale we choose is commonly applied in public health research.
- Streamlit map: We now add a dynamic and interactive selector in the map view to show the regional distribution of disease prevalence across different supply tier counties.
- Clearer interpretations: In the write-up, we also now address several issues that were not fully resolved during the presentation. Including: possible explanations for different statistical distributions of the prevalence of different kinds of disease, the potential reasons of why higher healthcare supply may be associated with higher or lower observed prevalence, and what may partially explain why these associations vary across physician supply groups.


## Introduction
The research topic came from our shared interest of healthcare section. When searching for data, we found a set of county-level health burden data that captures the health rates of multiple chronic diseases across the US. Thus, we came up with our main question: what factors may affect the health level of different regions?

Based on the question, we went through more database and finally focused our study on the relationship between disease prevalence and healthcare supply. To be more specific, health workforce supply, such as specialist physician counts, healthcare capacity (ICU beds) by county, etc. To further explore, we also introduced baseline variables, such as median income and county-level population (18+), so that the analysis could be more robust and comparable.

Data Sources:
- Disease Burden (Health Rates from [CDC](https://data.cdc.gov/browse?category=500+Cities+%26+Places&q=2025&sortBy=relevance&tags=places&pageSize=20)): County-level prevalence rates for multiple chronic conditions, as well as adult population.
- Healthcare Supply (from [HRSA](https://data.hrsa.gov/data/download?)): Overall physician supply, physician supply by specialty and healthcare capacity metrics, also at county level.
- Baseline Variables (from [U.S. Census / ACS 5-year estimates](https://api.census.gov/data/2023/acs/acs5?get=NAME,B19013_001E&for=county:*)): Median income at county level as control.
- Geographic Data (from [U.S. Census TIGER](https://www2.census.gov/geo/tiger/TIGER2025/COUNTY/tl_2025_us_county.zip)): County-level geographic boundary data.

Using county identifiers as keys, we processed the large-volume raw data and constructed a standardized dataset with baseline variables, preparing for more meaningful comparisons and helping rule out the influence of large-population counties.

[!NOTE]
- One challenge was that some of the raw data files were too large to upload directly to GitHub. We initially considered storing them in Box file, but later found a clearer solution: incorporating the data acquisition step directly into our pipeline. When running our code in the preprocessing chunk in final write up qmd, it automatically searches for and downloads the required data from public sources to the folder. Then user can perform cleaning and merging locally. This ensures that no oversized files stored in the repository and improves reproducibility. As a result, we only uploaded CDC data ("Health.csv") and HRSA data (include "AHRF2025hf.csv" and "AHRF2025hp.csv") to git, and two cleaned datasets generated after preprocessing to the repository.
- Although the healthcare-related databases we used were updated in 2025, the observations are actually obtained in 2023, which are the latest available data we can get. To ensure the consistency, we use the median income of 2023. Gis information of county in 2023 and 2025 is the same, so we use the 2025 version.

Then we conducted an initial analysis to illustrate the overall patterns of health burden, healthcare resources, and their geographic distribution, providing a basic overview of the data. To be more specific: 
- Basic patterns of disease prevalence and healthcare supply at county level
- Relationship between the two factors
- Geographic distribution patterns or the two factors

In the [Streamlit dashboard app](https://final-project-shuyan-ziye-6pkom6vbzap9avqyw3m3ek.streamlit.app/), our core purpose is to allow users (i.e., policymakers on programs like NHSC) to test their own policy ideas interactively, instead of showing the casual relationship. They can:
- Select different disease types through a dropdown menu (select box)
- Adjust the size and direction of additional healthcare supply through slider
- Select physician supply group from a dropdown menu (select box); and the map will locate the corresponding counties and use certain color to show its disease prevalence
- Dynamic view: the predicted disease prevalence for each tier and for whole population (population-weighed aggregated)

