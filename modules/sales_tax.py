from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

ACS_FILE = DATA_DIR / "ACSDT5Y2024.B19001-Data.csv"
BLS_FILE = DATA_DIR / "cu-income-quintiles-before-taxes-2024.xlsx"
COUNTY_INPUTS_FILE = DATA_DIR / "county_inputs.xlsx"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# MODEL ASSUMPTIONS
# ============================================================

# Lagom representative community size
LAGOM_HOMES = 150

# Lagom syllabus says approximately 28%-35%.
# 32% is used as the base case.
TAXABLE_SHARE = 0.32


# ============================================================
# BLS CE 2024 QUINTILE BOUNDARIES
# ============================================================

# Income before taxes:
#
# Q1: < $29,932
# Q2: $29,932 - $57,451
# Q3: $57,452 - $94,510
# Q4: $94,511 - $155,924
# Q5: $155,925+

CE_QUINTILES = {
    "Q1": (0, 29932),
    "Q2": (29932, 57452),
    "Q3": (57452, 94511),
    "Q4": (94511, 155925),
    "Q5": (155925, np.inf),
}


# ============================================================
# ACS B19001 INCOME BANDS
# ============================================================

# Upper bound is exclusive.
#
# Example:
# $10,000-$14,999 is represented as:
# [10000, 15000)

ACS_INCOME_BANDS = {
    "B19001_002E": (0, 10000),
    "B19001_003E": (10000, 15000),
    "B19001_004E": (15000, 20000),
    "B19001_005E": (20000, 25000),
    "B19001_006E": (25000, 30000),
    "B19001_007E": (30000, 35000),
    "B19001_008E": (35000, 40000),
    "B19001_009E": (40000, 45000),
    "B19001_010E": (45000, 50000),
    "B19001_011E": (50000, 60000),
    "B19001_012E": (60000, 75000),
    "B19001_013E": (75000, 100000),
    "B19001_014E": (100000, 125000),
    "B19001_015E": (125000, 150000),
    "B19001_016E": (150000, 200000),
    "B19001_017E": (200000, np.inf),
}


ACS_LABELS = {
    "B19001_002E": "<$10,000",
    "B19001_003E": "$10,000-$14,999",
    "B19001_004E": "$15,000-$19,999",
    "B19001_005E": "$20,000-$24,999",
    "B19001_006E": "$25,000-$29,999",
    "B19001_007E": "$30,000-$34,999",
    "B19001_008E": "$35,000-$39,999",
    "B19001_009E": "$40,000-$44,999",
    "B19001_010E": "$45,000-$49,999",
    "B19001_011E": "$50,000-$59,999",
    "B19001_012E": "$60,000-$74,999",
    "B19001_013E": "$75,000-$99,999",
    "B19001_014E": "$100,000-$124,999",
    "B19001_015E": "$125,000-$149,999",
    "B19001_016E": "$150,000-$199,999",
    "B19001_017E": "$200,000+",
}


# ============================================================
# LOAD ACS DATA
# ============================================================

def load_acs():
    """
    Load ACS B19001 household-income data.

    Uses:
        NAME
        B19001_001E
        B19001_002E through B19001_017E

    Margin-of-error columns ending in M are not used.
    """

    df = pd.read_csv(ACS_FILE)

    required_columns = (
        ["NAME", "B19001_001E"]
        + list(ACS_INCOME_BANDS.keys())
    )

    missing = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            "ACS file is missing required columns:\n"
            f"{missing}"
        )

    return df


# ============================================================
# LOAD BLS CONSUMER EXPENDITURE DATA
# ============================================================

def load_bls_ce():
    """
    BLS Consumer Expenditure Survey 2024
    Table 1101 - Income before taxes quintiles.

    Average annual expenditures:

        Q1 = $35,046
        Q2 = $50,054
        Q3 = $66,900
        Q4 = $89,972
        Q5 = $150,342

    Source file:
        data/cu-income-quintiles-before-taxes-2024.xlsx

    These values are entered explicitly because the official
    BLS workbook contains formatting/merged cells that make
    automated row extraction unreliable.

    Returns:
        Dictionary of annual household expenditure by quintile.
    """

    # Make sure the source workbook exists.
    if not BLS_FILE.exists():
        raise FileNotFoundError(
            f"BLS source file not found: {BLS_FILE}"
        )

    expenditures = {
        "Q1": 35046.0,
        "Q2": 50054.0,
        "Q3": 66900.0,
        "Q4": 89972.0,
        "Q5": 150342.0,
    }

    return expenditures

    """
    Read BLS Consumer Expenditure Table 1101.

    Finds the row:
        Average annual expenditures

    Returns annual expenditure for:
        Q1
        Q2
        Q3
        Q4
        Q5
    """

    raw = pd.read_excel(
        BLS_FILE,
        sheet_name="Table 1101",
        header=None
    )

    target_row = None

    for i in range(len(raw)):

        row_text = " ".join(
            raw.iloc[i]
            .fillna("")
            .astype(str)
            .str.lower()
            .tolist()
        )

        if "average annual expenditures" in row_text:
            target_row = raw.iloc[i]
            break

    if target_row is None:
        raise ValueError(
            "Could not find 'Average annual expenditures' "
            "in BLS Table 1101."
        )

    numbers = pd.to_numeric(
        target_row,
        errors="coerce"
    ).dropna().tolist()

    if len(numbers) < 5:
        raise ValueError(
            "Could not extract the five BLS "
            "quintile expenditure values."
        )

    # The final five numeric values correspond to
    # Lowest 20%, Second 20%, Third 20%,
    # Fourth 20%, Highest 20%.
    q_values = numbers[-5:]

    return {
        "Q1": float(q_values[0]),
        "Q2": float(q_values[1]),
        "Q3": float(q_values[2]),
        "Q4": float(q_values[3]),
        "Q5": float(q_values[4]),
    }


# ============================================================
# INTERVAL OVERLAP
# ============================================================

def overlap_fraction(
    band_low,
    band_high,
    quintile_low,
    quintile_high
):
    """
    Determine what fraction of an ACS income band falls
    into a BLS income quintile.

    Assumption:
        Household income is uniformly distributed
        within an ACS income band.

    Example:
        ACS $50K-$60K crosses the BLS Q2/Q3 boundary.
        Therefore the households are proportionally
        allocated between Q2 and Q3.
    """

    # Special case:
    # ACS $200K+ belongs to Q5.
    if np.isinf(band_high):

        if np.isinf(quintile_high):
            return 1.0

        return 0.0

    overlap_low = max(
        band_low,
        quintile_low
    )

    overlap_high = min(
        band_high,
        quintile_high
    )

    overlap = max(
        0,
        overlap_high - overlap_low
    )

    band_width = (
        band_high - band_low
    )

    if band_width <= 0:
        return 0.0

    return overlap / band_width


# ============================================================
# ACS -> BLS QUINTILE MAPPING
# ============================================================

def map_acs_to_bls(county_row):
    """
    Convert the 16 ACS B19001 income bands into
    the five BLS CE income quintiles.

    Returns:
        quintile_totals
        detail_df
    """

    quintile_totals = {
        "Q1": 0.0,
        "Q2": 0.0,
        "Q3": 0.0,
        "Q4": 0.0,
        "Q5": 0.0,
    }

    detail_rows = []

    for column, (
        band_low,
        band_high
    ) in ACS_INCOME_BANDS.items():

        households = pd.to_numeric(
            county_row[column],
            errors="coerce"
        )

        if pd.isna(households):
            households = 0

        households = float(households)

        for quintile, (
            q_low,
            q_high
        ) in CE_QUINTILES.items():

            fraction = overlap_fraction(
                band_low,
                band_high,
                q_low,
                q_high
            )

            allocated_households = (
                households * fraction
            )

            if allocated_households > 0:

                quintile_totals[
                    quintile
                ] += allocated_households

                detail_rows.append({
                    "ACS Column":
                        column,

                    "ACS Income Band":
                        ACS_LABELS[column],

                    "ACS Households":
                        households,

                    "BLS Quintile":
                        quintile,

                    "Allocation Fraction":
                        fraction,

                    "Allocated Households":
                        allocated_households,
                })

    detail_df = pd.DataFrame(
        detail_rows
    )

    return (
        quintile_totals,
        detail_df
    )


# ============================================================
# WEIGHTED BLS HOUSEHOLD SPENDING
# ============================================================

def calculate_weighted_spending(
    quintile_households,
    bls_expenditures
):
    """
    Calculate the county-weighted average
    annual household expenditure.

    Formula:

        Sum(
            households in quintile
            x
            BLS spending for quintile
        )
        --------------------------------
              total households
    """

    rows = []

    total_households = sum(
        quintile_households.values()
    )

    if total_households <= 0:
        raise ValueError(
            "Total mapped households must "
            "be greater than zero."
        )

    total_estimated_spending = 0.0

    for quintile in [
        "Q1",
        "Q2",
        "Q3",
        "Q4",
        "Q5"
    ]:

        households = (
            quintile_households[
                quintile
            ]
        )

        spending_per_household = (
            bls_expenditures[
                quintile
            ]
        )

        estimated_total_spending = (
            households
            * spending_per_household
        )

        total_estimated_spending += (
            estimated_total_spending
        )

        rows.append({
            "BLS Quintile":
                quintile,

            "County Households":
                households,

            "BLS Annual Spending per Household":
                spending_per_household,

            "Estimated Total Spending":
                estimated_total_spending,
        })

    weighted_average = (
        total_estimated_spending
        / total_households
    )

    summary_df = pd.DataFrame(
        rows
    )

    return (
        weighted_average,
        summary_df
    )


# ============================================================
# LOAD COUNTY INPUTS
# ============================================================

def load_county_inputs(county_name, state_name):
    """
    Load the requested county/state from county_inputs.xlsx.

    Nothing is hard-coded here.
    County and state are supplied by main.py.
    """

    df = pd.read_excel(COUNTY_INPUTS_FILE)

    # Clean column names in case Excel contains extra spaces
    df.columns = df.columns.astype(str).str.strip()

    if "County" not in df.columns:
        raise ValueError(
            "county_inputs.xlsx must contain a 'County' column."
        )

    if "State" not in df.columns:
        raise ValueError(
            "county_inputs.xlsx must contain a 'State' column."
        )

    # Exact county + state match
    mask = (
        df["County"].astype(str).str.strip().str.casefold()
        == county_name.strip().casefold()
    ) & (
        df["State"].astype(str).str.strip().str.casefold()
        == state_name.strip().casefold()
    )

    matches = df[mask]

    if matches.empty:
        raise ValueError(
            f"Could not find {county_name}, {state_name} "
            "in county_inputs.xlsx."
        )

    if len(matches) > 1:
        raise ValueError(
            f"Multiple rows found for {county_name}, {state_name} "
            "in county_inputs.xlsx."
        )

    return matches.iloc[0]


# ============================================================
# PERCENT -> DECIMAL
# ============================================================

def to_decimal(value):
    """
    Convert percentages safely.

    Examples:

        "7.50%" -> 0.075
        7.50    -> 0.075
        0.075   -> 0.075
    """

    if pd.isna(value):
        return 0.0

    if isinstance(value, str):

        value = value.strip()

        if "%" in value:

            return (
                float(
                    value.replace(
                        "%",
                        ""
                    ).strip()
                )
                / 100
            )

        value = float(value)

    value = float(value)

    if value > 1:
        value = value / 100

    return value


# ============================================================
# MODULE 2 - SALES TAX UPLIFT
# ============================================================

def calculate_sales_tax_uplift(
    county_name,
    state_name,
    lagom_homes=LAGOM_HOMES,
    taxable_share=TAXABLE_SHARE
):
    """
    Complete Lagom Module 2 calculation.

    Process:

    ACS household income
        ->
    BLS expenditure quintiles
        ->
    Weighted annual spending / HH
        ->
    Taxable share
        ->
    Taxable spending / HH
        ->
    150 Lagom homes
        ->
    Community taxable spending
        ->
    Combined sales tax
        ->
    Gross sales tax generated

    Separately:

    Community taxable spending
        x
    County sales tax component

    NOTE:
    County Sales Tax Component is NOT automatically
    assumed to equal the final county-retained revenue.
    Kansas revenue-sharing rules must be verified.
    """

    # ========================================================
    # 1. ACS
    # ========================================================

    acs = load_acs()

    county_mask = (
    acs["NAME"]
    .astype(str)
    .str.contains(
        county_name,
        case=False,
        na=False,
        regex=False
    )
    &
    acs["NAME"]
    .astype(str)
    .str.contains(
        state_name,
        case=False,
        na=False,
        regex=False
    )
)

    matches = acs[county_mask]

    if matches.empty:
        raise ValueError(
            f"{county_name}, {state_name} "
            "was not found in the ACS file."
    )

    if len(matches) > 1:
       raise ValueError(
           f"Multiple ACS rows found for "
           f"{county_name}, {state_name}."
    )

    county_acs = matches.iloc[0]

    full_county_name = (
        county_acs["NAME"]
    )

    acs_total_households = (
        pd.to_numeric(
            county_acs[
                "B19001_001E"
            ],
            errors="coerce"
        )
    )

    # ========================================================
    # 2. BLS CE
    # ========================================================

    bls_expenditures = (
        load_bls_ce()
    )

    # ========================================================
    # 3. ACS -> BLS
    # ========================================================

    (
        quintile_households,
        mapping_detail
    ) = map_acs_to_bls(
        county_acs
    )

    mapped_households = sum(
        quintile_households.values()
    )

    # ========================================================
    # 4. WEIGHTED ANNUAL SPENDING
    # ========================================================

    (
        weighted_spending,
        quintile_summary
    ) = calculate_weighted_spending(
        quintile_households,
        bls_expenditures
    )

    # ========================================================
    # 5. TAXABLE SPENDING / HOUSEHOLD
    # ========================================================

    # Formula:
    #
    # weighted annual spending
    # x
    # taxable share

    taxable_spending_per_hh = (
        weighted_spending
        * taxable_share
    )

    # ========================================================
    # 6. COMMUNITY TAXABLE SPENDING
    # ========================================================

    # Formula:
    #
    # taxable spending per household
    # x
    # Lagom homes

    community_taxable_spending = (
        taxable_spending_per_hh
        * lagom_homes
    )

    # ========================================================
    # 7. SALES TAX INPUTS
    # ========================================================

    county_inputs = (
        load_county_inputs(
            county_name,
    state_name
        )
    )

    state_rate = to_decimal(
        county_inputs[
            "State Sales Tax"
        ]
    )

    county_rate = to_decimal(
        county_inputs[
            "County Sales Tax"
        ]
    )

    city_rate = to_decimal(
        county_inputs[
            "City/Local Sales Tax"
        ]
    )

    combined_rate = to_decimal(
        county_inputs[
            "Combined Sales Tax"
        ]
    )

    effective_rate = to_decimal(
        county_inputs[
            "Tax Foundation 2024 Effective Rate"
        ]
    )

    # ========================================================
    # 8. VALIDATE COMBINED RATE
    # ========================================================

    calculated_combined_rate = (
        state_rate
        + county_rate
        + city_rate
    )

    combined_rate_difference = (
        combined_rate
        - calculated_combined_rate
    )

    # ========================================================
    # 9. GROSS SALES TAX
    # ========================================================

    # Formula:
    #
    # community taxable spending
    # x
    # combined sales tax rate

    gross_sales_tax_per_hh = (
        taxable_spending_per_hh
        * combined_rate
    )

    gross_community_sales_tax = (
        community_taxable_spending
        * combined_rate
    )

    # ========================================================
    # 10. COUNTY SALES TAX COMPONENT
    # ========================================================

    # Formula:
    #
    # community taxable spending
    # x
    # County Sales Tax
    #
    # IMPORTANT:
    # county_rate comes from the
    # "County Sales Tax" column in county_inputs.xlsx.
    #
    # We are NOT yet calling this final
    # "county-retained revenue" because Kansas
    # revenue-sharing rules still need verification.

    county_sales_tax_per_hh = (
        taxable_spending_per_hh
        * county_rate
    )

    county_sales_tax_component = (
        community_taxable_spending
        * county_rate
    )

    # ========================================================
    # 11. STATE COMPONENT
    # ========================================================

    state_sales_tax_component = (
        community_taxable_spending
        * state_rate
    )

    # ========================================================
    # 12. CITY/LOCAL COMPONENT
    # ========================================================

    city_local_sales_tax_component = (
        community_taxable_spending
        * city_rate
    )

    # ========================================================
    # 13. FINAL RESULTS
    # ========================================================

    results = {
        "County":
            full_county_name,

        "ACS Total Households":
            acs_total_households,

        "Mapped Households":
            mapped_households,

        "Lagom Homes":
            lagom_homes,

        "Weighted Annual Spending per Household":
            weighted_spending,

        "Taxable Share":
            taxable_share,

        "Taxable Spending per Household":
            taxable_spending_per_hh,

        "Community Taxable Spending":
            community_taxable_spending,

        "State Sales Tax Rate":
            state_rate,

        "County Sales Tax Rate":
            county_rate,

        "City/Local Sales Tax Rate":
            city_rate,

        "Combined Sales Tax Rate":
            combined_rate,

        "Calculated Combined Rate":
            calculated_combined_rate,

        "Combined Rate Difference":
            combined_rate_difference,

        "Tax Foundation 2024 Effective Rate":
            effective_rate,

        "Gross Sales Tax per Household":
            gross_sales_tax_per_hh,

        "Gross Community Sales Tax":
            gross_community_sales_tax,

        "State Sales Tax Component - Community":
            state_sales_tax_component,

        "County Sales Tax Component per Household":
            county_sales_tax_per_hh,

        "County Sales Tax Component - Community":
            county_sales_tax_component,

        "City/Local Sales Tax Component - Community":
            city_local_sales_tax_component,
    }

    return (
        results,
        mapping_detail,
        quintile_summary
    )


# ============================================================
# CREATE FORMULA / SOURCE TABLE
# ============================================================

def create_formula_source_table():
    """
    Create documentation table showing where
    each Module 2 value comes from.
    """

    rows = [
        {
            "Item":
                "Household Income Distribution",
            "Formula / Value":
                "ACS B19001",
            "Source":
                "ACSDT5Y2024.B19001-Data.csv",
            "Type":
                "Source"
        },
        {
            "Item":
                "BLS Annual Household Spending",
            "Formula / Value":
                "CE spending by Q1-Q5",
            "Source":
                "cu-income-quintiles-before-taxes-2024.xlsx",
            "Type":
                "Source"
        },
        {
            "Item":
                "Weighted Annual Spending per Household",
            "Formula / Value":
                "SUM(Quintile HH x BLS Spending) / Total HH",
            "Source":
                "ACS + BLS",
            "Type":
                "Calculated"
        },
        {
            "Item":
                "Taxable Share",
            "Formula / Value":
                "32% base case",
            "Source":
                "Lagom syllabus; approx. 28%-35%",
            "Type":
                "Assumption"
        },
        {
            "Item":
                "Lagom Homes",
            "Formula / Value":
                "150",
            "Source":
                "Lagom project assumption",
            "Type":
                "Assumption"
        },
        {
            "Item":
                "State Sales Tax",
            "Formula / Value":
                "Read from workbook",
            "Source":
                "county_inputs.xlsx - State Sales Tax",
            "Type":
                "Source"
        },
        {
            "Item":
                "County Sales Tax",
            "Formula / Value":
                "Read from workbook",
            "Source":
                "county_inputs.xlsx - County Sales Tax",
            "Type":
                "Source"
        },
        {
            "Item":
                "City/Local Sales Tax",
            "Formula / Value":
                "Read from workbook",
            "Source":
                "county_inputs.xlsx - City/Local Sales Tax",
            "Type":
                "Source"
        },
        {
            "Item":
                "Combined Sales Tax",
            "Formula / Value":
                "State + County + City/Local",
            "Source":
                "county_inputs.xlsx - Combined Sales Tax",
            "Type":
                "Source / Validation"
        },
        {
            "Item":
                "Taxable Spending per Household",
            "Formula / Value":
                "Weighted Spending x Taxable Share",
            "Source":
                "Model calculation",
            "Type":
                "Calculated"
        },
        {
            "Item":
                "Community Taxable Spending",
            "Formula / Value":
                "Taxable Spending/HH x Lagom Homes",
            "Source":
                "Model calculation",
            "Type":
                "Calculated"
        },
        {
            "Item":
                "Gross Community Sales Tax",
            "Formula / Value":
                "Community Taxable Spending x Combined Sales Tax",
            "Source":
                "Model calculation",
            "Type":
                "Calculated"
        },
        {
            "Item":
                "County Sales Tax Component",
            "Formula / Value":
                "Community Taxable Spending x County Sales Tax",
            "Source":
                "Model calculation using county_inputs.xlsx",
            "Type":
                "Calculated"
        },
        {
            "Item":
                "County-Retained Fiscal Benefit",
            "Formula / Value":
                "Pending verification",
            "Source":
                "Kansas revenue-sharing rule must be verified",
            "Type":
                "Pending"
        },
    ]

    return pd.DataFrame(rows)


# ============================================================
# SAVE MODULE 2 EXCEL OUTPUT
# ============================================================

def save_module2_output(
    results,
    mapping_detail,
    quintile_summary
):
    """
    Save Module 2 calculations to Excel.
    """

    output_file = (
        OUTPUT_DIR
        / "module2_sales_tax_uplift.xlsx"
    )

    results_df = pd.DataFrame(
        list(results.items()),
        columns=[
            "Metric",
            "Value"
        ]
    )

    formula_source_df = (
        create_formula_source_table()
    )

    with pd.ExcelWriter(
        output_file,
        engine="openpyxl"
    ) as writer:

        # --------------------------------
        # Final Module 2 results
        # --------------------------------

        results_df.to_excel(
            writer,
            sheet_name="Module2_Summary",
            index=False
        )

        # --------------------------------
        # Detailed ACS -> BLS mapping
        # --------------------------------

        mapping_detail.to_excel(
            writer,
            sheet_name="ACS_to_BLS_Detail",
            index=False
        )

        # --------------------------------
        # BLS quintile calculation
        # --------------------------------

        quintile_summary.to_excel(
            writer,
            sheet_name="BLS_Quintile_Summary",
            index=False
        )

        # --------------------------------
        # Sources and formulas
        # --------------------------------

        formula_source_df.to_excel(
            writer,
            sheet_name="Formula_and_Sources",
            index=False
        )

    return output_file