# Disease Prevalence and Health Resource Distrubution in the US
## Does healthcare supply relate to disease prevalence across U.S. counties?
Data and Programming II Final Project (Winter 2026)

Team members:
Shuyan Xin & Ziye Yang

Qmd: PROJECT_ROOT / "code" / "write up.qmd"

Streamlit dashboard: https://final-project-shuyan-ziye-g5wwnpknculjgrhma5qzpj.streamlit.app/


These research questions emerged from a shared interest in health equity and the geographic distribution of medical resources. While searching for data, we encountered a county-level disease burden dataset capturing prevalence rates of various chronic conditions across different regions. This naturally led us to ask: do differences in regional health outcomes relate to the availability of healthcare resources?

Building on this question, we incorporated a more policy-relevant dimension — healthcare workforce supply (e.g., specialist physician counts, healthcare capacity by county) — to examine whether a systematic relationship exists between health burden and resource supply. To make the analysis more complete and interpretable, we further introduced demographic and socioeconomic baseline variables (e.g., income, adult population size) that allow us to control for structural differences across counties and produce more robust, comparable results.

Data Sources:
- Disease Burden (Health Outcomes from [CDC](https://data.cdc.gov/browse?category=500+Cities+%26+Places&q=2025&sortBy=relevance&tags=places&pageSize=20)): County-level prevalence rates for various chronic conditions, serving as our dependent variables.
- Healthcare Workforce Supply (from [HRSA](https://data.hrsa.gov/data/download?)): Physician supply by specialty and healthcare capacity metrics, organized into supply tiers by county.
- Socioeconomic & Demographic Baselines(from [U.S. Census / ACS 5-year estimates](https://www.census.gov/en.html)): Income levels, adult population size, and related structural controls used to standardize cross-county comparisons.

After cleaning and merging the datasets using county identifiers as keys, we standardized key variables (e.g., normalized to adult population) to make comparisons across counties more intuitive and suitable for visualization and regression modeling.

One practical challenge we encountered was that some raw data sources were too large to upload directly to GitHub. Rather than storing large files in the repository, we embedded the data acquisition step into our Python pipeline. When users run our preprocessing code chunk in the "write up.qmd", it automatically searches for and downloads the required data from public sources, then performs all cleaning, merging, and lightweight output generation locally. This approach ensures that no oversized files stored in the repository and improves reproducibility.


Exploratory Analysis (Static Figures)

After cleaning and integrating the data, we conducted an initial exploratory analysis to describe the overall distributions of health burden and healthcare resource supply. This produced several sets of static visualizations, including:
- Distribution characteristics of disease prevalence and health supply at county level
- Relationship between the two factors
- Geographic distribution and regional clustering patterns


Note on Causality

Through this process, we also recognized that the factors influencing health outcomes and resource distribution are deeply complex. Economic development, demographic structure, detection rates, care-seeking behavior, and governance capacity may all operate simultaneously. Strict causal identification is  beyond the scope of this project. Rather than attempting to prescribe a single answer for "how resources should be allocated," we positioned our project as an interactive simulation tool: a policy sandbox that helps decision-makers quickly explore the direction and size of impacts of each policy set.


Streamlit Dashboard

The core purpose of our Streamlit dashboard is to allow users (e.g., policymakers on programs like NHSC) to test their own policy ideas interactively. Users can:
- Select different disease cases via a selectbox menu
- Adjust the magnitude of changes through slider across different healthcare supply tier counties
- Select a physician supply group from a selectbox menu; and the map will locate and highlight the corresponding counties, using color intensity to display the disease prevalence distribution across those regions
- View dynamically updated projections of how predicted disease prevalence shifts under selected conditions, including population-weighted aggregate outcomes


Revisions Based on Comments after Presentation (March 3)

Following feedback received after our March 3rd presentation, we made targeted improvements focused on readability and interpretability:
- Visual consistency in regression/relationship plots: We applied uniform, consistent color coding across six supply tiers in our "disease prevalence - healthcare supply" figures and introduced clearer regression line displays, making it easier to observe the overall trend (disease prevalence tends to decrease as healthcare supply increases) and to detect potential nonlinear differences across tiers.
- Enhanced map contrast: We adopted higher-contrast color schemes and cleaner map layouts to make spatial comparisons more immediately legible. We also added an interactive selector in the Streamlit map view (left column) to allow users to dynamically choose a physician supply tier, which highlights the corresponding counties on the map and reveals its disease prevalence with regional clustering patterns for the chosen disease.
- Interpretive depth: In response to questions raised during the presentation, we expanded our discussion and interpretation of key findings in the write-up, providing additional context for the relationships observed in the data.

To run the project locally, clone the repository to your laptop. Cd to the project folder, then run the preprocessing script first to download and generate the required data locally. 
For Streamlit app: Once preprocessing is complete, launch the Streamlit app by running streamlit run app.py in your terminal or use [this link](https://final-project-shuyan-ziye-g5wwnpknculjgrhma5qzpj.streamlit.app/) to interact with the dashboard and explore our findings.


Disclosure: All ideas in this README.md are our own; some wording in this file has been polished with AI tools assistance.