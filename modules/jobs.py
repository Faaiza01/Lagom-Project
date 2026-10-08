from pathlib import Path

import pandas as pd


# ============================================================
# MODULE 5 - DIRECT JOB CREATION
# ============================================================
#
# Purpose:
#   Estimate direct factory employment and annual payroll.
#
# Input:
#   job_creation_inputs.xlsx
#
# Required columns:
#   County
#   State
#   Factory Host
#   Direct Jobs
#
# Wage source:
#   BLS OEWS May 2025
#   MSA_M2025_dl.xlsx
#
# Current Sedgwick modeling assumption:
#   75% Assemblers / Fabricators
#   15% Material Movers
#   10% Quality Control / Inspectors
#
# IMPORTANT:
#   The occupation allocation is a modeling assumption.
#   BLS provides the wage data, not the Lagom staffing mix.
# ============================================================


# ============================================================
# OCCUPATION MIX ASSUMPTION
# ============================================================

OCCUPATION_MIX = [
    {
        "SOC": "51-2090",
        "Occupation Group": "Assemblers / Fabricators",
        "Job Share": 0.75,
    },
    {
        "SOC": "53-7062",
        "Occupation Group": "Material Movers",
        "Job Share": 0.15,
    },
    {
        "SOC": "51-9061",
        "Occupation Group": "Quality Control / Inspectors",
        "Job Share": 0.10,
    },
]


# ============================================================
# COUNTY -> BLS METRO AREA
# ============================================================
#
# Sedgwick County is represented by the Wichita OEWS metro.
#
# Add additional counties here later as you expand the model.
# ============================================================

COUNTY_BLS_AREA = {
    ("sedgwick", "kansas"): "Wichita",
}


# ============================================================
# HELPER - CLEAN SOC CODE
# ============================================================

def _clean_soc_code(value):

    if pd.isna(value):
        return None

    return str(value).strip()


# ============================================================
# HELPER - FIND COLUMN
# ============================================================

def _find_column(df, possible_names):
    """
    Find a column even if capitalization is slightly different.
    """

    column_lookup = {
        str(col).strip().lower(): col
        for col in df.columns
    }

    for possible_name in possible_names:

        key = possible_name.strip().lower()

        if key in column_lookup:
            return column_lookup[key]

    return None


# ============================================================
# LOAD JOB CREATION INPUTS
# ============================================================

def _load_job_inputs(job_inputs_file):
    """
    Load job_creation_inputs.xlsx.

    Required structure:

        County
        State
        Factory Host
        Direct Jobs

    Example:

        Sedgwick
        Kansas
        TRUE
        80
    """

    job_inputs_file = Path(job_inputs_file)

    if not job_inputs_file.exists():

        raise FileNotFoundError(
            f"Module 5 input file not found: "
            f"{job_inputs_file}"
        )

    inputs = pd.read_excel(
        job_inputs_file
    )

    # --------------------------------------------------------
    # Clean column names
    # --------------------------------------------------------

    inputs.columns = [
        str(col).strip()
        for col in inputs.columns
    ]

    # --------------------------------------------------------
    # Required columns
    # --------------------------------------------------------

    required_columns = [
        "County",
        "State",
        "Factory Host",
        "Direct Jobs",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in inputs.columns
    ]

    if missing_columns:

        raise ValueError(
            "job_creation_inputs.xlsx is missing required "
            "columns: "
            + ", ".join(missing_columns)
        )

    # --------------------------------------------------------
    # Clean County / State
    # --------------------------------------------------------

    inputs["County"] = (
        inputs["County"]
        .astype(str)
        .str.strip()
    )

    inputs["State"] = (
        inputs["State"]
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------
    # Convert Direct Jobs to number
    # --------------------------------------------------------

    inputs["Direct Jobs"] = pd.to_numeric(
        inputs["Direct Jobs"],
        errors="coerce"
    ).fillna(0)

    return inputs


# ============================================================
# LOAD BLS OEWS DATA
# ============================================================

def _load_bls_oews(bls_file):
    """
    Load BLS May 2025 OEWS metro-area data.

    Expected important BLS fields:

        AREA_TITLE
        OCC_CODE
        OCC_TITLE
        A_MEDIAN
    """

    bls_file = Path(bls_file)

    if not bls_file.exists():

        raise FileNotFoundError(
            f"BLS OEWS file not found: "
            f"{bls_file}"
        )

    print()
    print("Loading BLS OEWS wage data...")

    bls = pd.read_excel(
        bls_file
    )

    # --------------------------------------------------------
    # Find relevant BLS columns
    # --------------------------------------------------------

    area_col = _find_column(
        bls,
        [
            "AREA_TITLE",
            "Area Title",
        ]
    )

    soc_col = _find_column(
        bls,
        [
            "OCC_CODE",
            "SOC",
            "SOC Code",
        ]
    )

    occupation_col = _find_column(
        bls,
        [
            "OCC_TITLE",
            "Occupation Title",
        ]
    )

    wage_col = _find_column(
        bls,
        [
            "A_MEDIAN",
            "Annual Median Wage",
            "Median Annual Wage",
        ]
    )

    # --------------------------------------------------------
    # Validate BLS columns
    # --------------------------------------------------------

    missing = []

    if area_col is None:
        missing.append("AREA_TITLE")

    if soc_col is None:
        missing.append("OCC_CODE")

    if occupation_col is None:
        missing.append("OCC_TITLE")

    if wage_col is None:
        missing.append("A_MEDIAN")

    if missing:

        raise ValueError(
            "BLS OEWS file is missing required columns: "
            + ", ".join(missing)
        )

    # --------------------------------------------------------
    # Keep only columns needed by Module 5
    # --------------------------------------------------------

    bls = bls[
        [
            area_col,
            soc_col,
            occupation_col,
            wage_col,
        ]
    ].copy()

    bls.columns = [
        "BLS Area",
        "SOC",
        "BLS Occupation",
        "Median Annual Wage",
    ]

    # --------------------------------------------------------
    # Clean values
    # --------------------------------------------------------

    bls["SOC"] = (
        bls["SOC"]
        .apply(_clean_soc_code)
    )

    bls["BLS Area"] = (
        bls["BLS Area"]
        .astype(str)
        .str.strip()
    )

    # BLS sometimes uses symbols such as * or #
    # when a wage is unavailable.
    bls["Median Annual Wage"] = pd.to_numeric(
        bls["Median Annual Wage"],
        errors="coerce"
    )

    return bls


# ============================================================
# FACTORY HOST CONVERTER
# ============================================================

def _is_factory_host(value):
    """
    Convert Excel TRUE/FALSE, Yes/No, 1/0, etc.
    into a Python Boolean.
    """

    if isinstance(value, bool):
        return value

    if pd.isna(value):
        return False

    value = str(value).strip().lower()

    true_values = [
        "true",
        "yes",
        "y",
        "1",
    ]

    return value in true_values


# ============================================================
# GET BLS AREA
# ============================================================

def _get_bls_area(county, state):
    """
    Determine which BLS metro area should represent the county.
    """

    key = (
        str(county).strip().lower(),
        str(state).strip().lower(),
    )

    if key not in COUNTY_BLS_AREA:

        raise ValueError(
            f"No BLS metro-area mapping has been defined "
            f"for {county}, {state}. "
            f"Add this county to COUNTY_BLS_AREA in jobs.py."
        )

    return COUNTY_BLS_AREA[key]


# ============================================================
# FILTER BLS DATA TO METRO AREA
# ============================================================

def _filter_bls_area(bls, area_name):
    """
    Filter BLS data to the requested metro area.

    Example:
        Wichita
    """

    area_data = bls[
        bls["BLS Area"]
        .str.contains(
            area_name,
            case=False,
            na=False,
        )
    ].copy()

    if area_data.empty:

        raise ValueError(
            f"No BLS OEWS area containing "
            f"'{area_name}' was found."
        )

    return area_data


# ============================================================
# ALLOCATE DIRECT JOBS
# ============================================================

def _allocate_jobs(total_jobs):
    """
    Allocate total direct jobs across the occupation mix.

    For 80 jobs:

        Assemblers       = 60
        Material Movers  = 12
        Inspectors       = 8
    """

    total_jobs = int(
        round(total_jobs)
    )

    allocations = []

    jobs_allocated = 0

    for index, occupation in enumerate(
        OCCUPATION_MIX
    ):

        # ----------------------------------------------------
        # Last occupation gets remainder
        # ----------------------------------------------------

        if index == len(OCCUPATION_MIX) - 1:

            jobs = (
                total_jobs
                -
                jobs_allocated
            )

        else:

            jobs = int(
                round(
                    total_jobs
                    *
                    occupation["Job Share"]
                )
            )

        jobs_allocated += jobs

        allocations.append(
            {
                "SOC":
                    occupation["SOC"],

                "Occupation Group":
                    occupation[
                        "Occupation Group"
                    ],

                "Job Share":
                    occupation["Job Share"],

                "Jobs":
                    jobs,
            }
        )

    return pd.DataFrame(
        allocations
    )


# ============================================================
# CALCULATE DIRECT JOB CREATION
# ============================================================

def calculate_direct_jobs(
    job_inputs_file,
    bls_file,
):
    """
    Run Module 5.

    Steps:

        1. Load county job assumptions.
        2. Check whether county hosts a factory.
        3. Read total direct factory jobs.
        4. Allocate jobs across SOC occupations.
        5. Match SOC codes to BLS OEWS wages.
        6. Calculate payroll by occupation.
        7. Calculate total direct payroll.
        8. Calculate weighted average wage.

    Returns:

        results_df
        occupation_detail_df
    """

    # ========================================================
    # 1. LOAD INPUT FILES
    # ========================================================

    inputs = _load_job_inputs(
        job_inputs_file
    )

    bls = _load_bls_oews(
        bls_file
    )

    summary_results = []

    occupation_results = []

    # ========================================================
    # 2. PROCESS EACH COUNTY
    # ========================================================

    for _, county_row in inputs.iterrows():

        county = (
            str(
                county_row["County"]
            ).strip()
        )

        state = (
            str(
                county_row["State"]
            ).strip()
        )

        factory_host = _is_factory_host(
            county_row["Factory Host"]
        )

        direct_jobs = int(
            round(
                county_row["Direct Jobs"]
            )
        )

        print()
        print("-" * 70)

        print(
            f"Processing Module 5: "
            f"{county}, {state}"
        )

        print(
            f"Factory Host: "
            f"{factory_host}"
        )

        # ====================================================
        # 3. NON-FACTORY COUNTY
        # ====================================================

        if not factory_host:

            print(
                "No Lagom factory assumed for this county."
            )

            summary_results.append(
                {
                    "County":
                        county,

                    "State":
                        state,

                    "Factory Host":
                        False,

                    "Direct Jobs":
                        0,

                    "Direct Payroll":
                        0.0,

                    "Weighted Average Wage":
                        0.0,

                    "BLS Area":
                        None,

                    "Wage Source":
                        "BLS OEWS May 2025",

                    "Staffing Mix Source":
                        "Modeling assumption",
                }
            )

            continue

        # ====================================================
        # 4. GET BLS AREA
        # ====================================================

        area_name = _get_bls_area(
            county,
            state
        )

        area_data = _filter_bls_area(
            bls,
            area_name
        )

        print(
            f"BLS Wage Area: "
            f"{area_name}"
        )

        print(
            f"Direct Factory Jobs: "
            f"{direct_jobs}"
        )

        # ====================================================
        # 5. ALLOCATE JOBS TO OCCUPATIONS
        # ====================================================

        job_allocation = _allocate_jobs(
            direct_jobs
        )

        # ====================================================
        # 6. PREPARE BLS WAGE TABLE
        # ====================================================

        wage_table = area_data[
            [
                "SOC",
                "BLS Area",
                "BLS Occupation",
                "Median Annual Wage",
            ]
        ].copy()

        # Remove BLS rows where wage is unavailable
        wage_table = wage_table[
            wage_table[
                "Median Annual Wage"
            ].notna()
        ]

        # If duplicates exist for the same SOC,
        # retain one usable record.
        wage_table = (
            wage_table
            .drop_duplicates(
                subset=["SOC"],
                keep="first",
            )
        )

        # ====================================================
        # 7. JOIN JOB ALLOCATION TO BLS WAGES
        # ====================================================

        detail = job_allocation.merge(
            wage_table,
            on="SOC",
            how="left",
        )

        # ====================================================
        # 8. CHECK FOR MISSING WAGES
        # ====================================================

        missing_wage_rows = detail[
            detail[
                "Median Annual Wage"
            ].isna()
        ]

        if not missing_wage_rows.empty:

            missing_soc = (
                missing_wage_rows[
                    "SOC"
                ]
                .astype(str)
                .tolist()
            )

            raise ValueError(
                f"BLS median annual wage was not found "
                f"for {county}, {state} for SOC code(s): "
                f"{', '.join(missing_soc)}"
            )

        # ====================================================
        # 9. CALCULATE PAYROLL
        # ====================================================

        detail[
            "Occupation Payroll"
        ] = (
            detail["Jobs"]
            *
            detail["Median Annual Wage"]
        )

        # Add county information
        detail.insert(
            0,
            "State",
            state
        )

        detail.insert(
            0,
            "County",
            county
        )

        detail["Factory Host"] = True

        detail[
            "Wage Source"
        ] = "BLS OEWS May 2025"

        detail[
            "Staffing Mix Source"
        ] = "Modeling assumption"

        # ====================================================
        # 10. COUNTY SUMMARY
        # ====================================================

        calculated_jobs = (
            detail["Jobs"].sum()
        )

        direct_payroll = (
            detail[
                "Occupation Payroll"
            ].sum()
        )

        if calculated_jobs > 0:

            weighted_average_wage = (
                direct_payroll
                /
                calculated_jobs
            )

        else:

            weighted_average_wage = 0.0

        actual_bls_area = (
            detail[
                "BLS Area"
            ].dropna()
        )

        if not actual_bls_area.empty:

            actual_bls_area = (
                actual_bls_area.iloc[0]
            )

        else:

            actual_bls_area = area_name

        # ====================================================
        # 11. PRINT OCCUPATION DETAIL
        # ====================================================

        print()
        print("OCCUPATION DETAIL")
        print("-" * 70)

        for _, occupation_row in detail.iterrows():

            print()

            print(
                f"SOC: "
                f"{occupation_row['SOC']}"
            )

            print(
                f"Occupation: "
                f"{occupation_row['BLS Occupation']}"
            )

            print(
                f"Jobs: "
                f"{occupation_row['Jobs']:,.0f}"
            )

            print(
                f"Median Annual Wage: "
                f"${occupation_row['Median Annual Wage']:,.2f}"
            )

            print(
                f"Occupation Payroll: "
                f"${occupation_row['Occupation Payroll']:,.2f}"
            )

        # ====================================================
        # 12. CREATE SUMMARY ROW
        # ====================================================

        summary_results.append(
            {
                "County":
                    county,

                "State":
                    state,

                "Factory Host":
                    True,

                "Direct Jobs":
                    calculated_jobs,

                "Direct Payroll":
                    direct_payroll,

                "Weighted Average Wage":
                    weighted_average_wage,

                "BLS Area":
                    actual_bls_area,

                "Wage Source":
                    "BLS OEWS May 2025",

                "Staffing Mix Source":
                    "Modeling assumption",
            }
        )

        occupation_results.append(
            detail
        )

    # ========================================================
    # 13. CREATE FINAL DATAFRAMES
    # ========================================================

    results_df = pd.DataFrame(
        summary_results
    )

    if occupation_results:

        occupation_detail_df = pd.concat(
            occupation_results,
            ignore_index=True
        )

    else:

        occupation_detail_df = pd.DataFrame()

    # ========================================================
    # 14. RETURN
    # ========================================================

    return (
        results_df,
        occupation_detail_df
    )