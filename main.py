from pathlib import Path

import pandas as pd


# ============================================================
# IMPORT MODULE 1
# ============================================================

from modules.property_tax import (
    calculate_property_tax,
    tax_breakdown,
    abatement_sensitivity,
    home_price_sensitivity,
)


# ============================================================
# IMPORT MODULE 2
# ============================================================

from modules.sales_tax import (
    calculate_sales_tax_uplift,
    save_module2_output,
)


# ============================================================
# IMPORT MODULE 3
# ============================================================

from modules.school_impact import (
    load_f33_data,
    calculate_school_impact,
    school_capacity_sensitivity,
)

# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

DATA_DIR = PROJECT_ROOT / "data"

OUTPUT_DIR = PROJECT_ROOT / "outputs"

COUNTY_INPUTS_FILE = DATA_DIR / "county_inputs.xlsx"

F33_FILE = DATA_DIR / "sdf24_1a.txt"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# MODULE 1 - PROPERTY TAX
# ============================================================

def run_module1():

    print()
    print("=" * 70)
    print("MODULE 1 - PROPERTY TAX REVENUE")
    print("=" * 70)


    # --------------------------------------------------------
    # 1. Load county input file
    # --------------------------------------------------------

    print()
    print("Loading county inputs...")

    inputs = pd.read_excel(
        COUNTY_INPUTS_FILE
    )


    # --------------------------------------------------------
    # 2. Run property tax calculation
    # --------------------------------------------------------

    results = calculate_property_tax(
        inputs
    )


    # --------------------------------------------------------
    # 3. Tax breakdown
    # --------------------------------------------------------

    breakdown = tax_breakdown(
        results
    )


    # --------------------------------------------------------
    # 4. Abatement sensitivity
    # --------------------------------------------------------

    abatement = abatement_sensitivity(
        results
    )


    # --------------------------------------------------------
    # 5. Home / price sensitivity
    # --------------------------------------------------------

    sensitivity = home_price_sensitivity(
        results
    )


    # --------------------------------------------------------
    # 6. Print main results
    # --------------------------------------------------------

    print()
    print("PROPERTY TAX RESULTS")
    print("-" * 70)

    for _, row in results.iterrows():

        print()

        print(
            f"County: "
            f"{row['County']}, {row['State']}"
        )

        print(
            "Homes: "
            f"{row['Homes']:,.0f}"
        )

        print(
            "Average Sale Price: "
            f"${row['Average Sale Price']:,.2f}"
        )

        print(
            "Assessment Ratio: "
            f"{row['Assessment Ratio']:.2%}"
        )

        print(
            "Gross Market Value: "
            f"${row['Gross Market Value']:,.2f}"
        )

        print(
            "Gross Assessed Value: "
            f"${row['Gross Assessed Value']:,.2f}"
        )

        print(
            "Total Applicable Millage: "
            f"{row['Total Applicable Millage']:,.3f} mills"
        )

        print(
            "Gross Annual Property Tax: "
            f"${row['Gross Annual Property Tax']:,.2f}"
        )

        print(
            "Gross Tax Per Home: "
            f"${row['Gross Tax Per Home']:,.2f}"
        )


    # --------------------------------------------------------
    # 7. Save Module 1 Excel
    # --------------------------------------------------------

    output_file = (
        OUTPUT_DIR
        / "module1_property_tax.xlsx"
    )

    with pd.ExcelWriter(
        output_file,
        engine="openpyxl"
    ) as writer:

        # Original inputs
        inputs.to_excel(
            writer,
            sheet_name="Inputs",
            index=False
        )

        # Main calculations
        results.to_excel(
            writer,
            sheet_name="Property_Tax_Results",
            index=False
        )

        # Tax authority breakdown
        breakdown.to_excel(
            writer,
            sheet_name="Tax_Breakdown",
            index=False
        )

        # Abatement scenarios
        abatement.to_excel(
            writer,
            sheet_name="Abatement_Sensitivity",
            index=False
        )

        # Home / price sensitivity
        sensitivity.to_excel(
            writer,
            sheet_name="Home_Price_Sensitivity",
            index=False
        )


    print()
    print(
        "Module 1 Excel saved to:"
    )

    print(output_file)

    print()
    print("MODULE 1 COMPLETED")

    return results


# ============================================================
# MODULE 2 - SALES TAX UPLIFT
# ============================================================

def run_module2():

    print()
    print("=" * 70)
    print("MODULE 2 - SALES TAX UPLIFT")
    print("=" * 70)


    # --------------------------------------------------------
    # 1. Run Module 2
    # --------------------------------------------------------

    (
        results,
        mapping_detail,
        quintile_summary

    ) = calculate_sales_tax_uplift(

        county_name="Sedgwick",
        state_name="Kansas",
        lagom_homes=150,
        taxable_share=0.32

    )


    # --------------------------------------------------------
    # 2. County / household information
    # --------------------------------------------------------

    print()
    print("COUNTY / HOUSEHOLD DATA")
    print("-" * 70)

    print(
        f"County: "
        f"{results['County']}"
    )

    print(
        "ACS Total Households: "
        f"{results['ACS Total Households']:,.0f}"
    )

    print(
        "Mapped Households: "
        f"{results['Mapped Households']:,.2f}"
    )


    # --------------------------------------------------------
    # 3. Spending calculation
    # --------------------------------------------------------

    print()
    print("HOUSEHOLD SPENDING")
    print("-" * 70)

    print(
        "Weighted Annual Spending / HH: "
        f"${results['Weighted Annual Spending per Household']:,.2f}"
    )

    print(
        "Taxable Share: "
        f"{results['Taxable Share']:.2%}"
    )

    print(
        "Taxable Spending / HH: "
        f"${results['Taxable Spending per Household']:,.2f}"
    )


    # --------------------------------------------------------
    # 4. Lagom community
    # --------------------------------------------------------

    print()
    print("LAGOM COMMUNITY")
    print("-" * 70)

    print(
        "Lagom Homes: "
        f"{results['Lagom Homes']}"
    )

    print(
        "Community Taxable Spending: "
        f"${results['Community Taxable Spending']:,.2f}"
    )


    # --------------------------------------------------------
    # 5. Sales tax rates
    # --------------------------------------------------------

    print()
    print("SALES TAX RATES")
    print("-" * 70)

    print(
        "State Sales Tax: "
        f"{results['State Sales Tax Rate']:.2%}"
    )

    print(
        "County Sales Tax: "
        f"{results['County Sales Tax Rate']:.2%}"
    )

    print(
        "City/Local Sales Tax: "
        f"{results['City/Local Sales Tax Rate']:.2%}"
    )

    print(
        "Combined Sales Tax: "
        f"{results['Combined Sales Tax Rate']:.2%}"
    )

    print(
        "Calculated State + County + Local: "
        f"{results['Calculated Combined Rate']:.2%}"
    )


    # --------------------------------------------------------
    # 6. Gross sales tax
    # --------------------------------------------------------

    print()
    print("GROSS SALES TAX GENERATED")
    print("-" * 70)

    print(
        "Gross Sales Tax / HH: "
        f"${results['Gross Sales Tax per Household']:,.2f}"
    )

    print(
        "Gross Community Sales Tax: "
        f"${results['Gross Community Sales Tax']:,.2f}"
    )


    # --------------------------------------------------------
    # 7. Sales tax components
    # --------------------------------------------------------

    print()
    print("SALES TAX COMPONENTS")
    print("-" * 70)

    print(
        "State Component - Community: "
        f"${results['State Sales Tax Component - Community']:,.2f}"
    )

    print(
        "County Component / HH: "
        f"${results['County Sales Tax Component per Household']:,.2f}"
    )

    print(
        "County Component - Community: "
        f"${results['County Sales Tax Component - Community']:,.2f}"
    )

    print(
        "City/Local Component - Community: "
        f"${results['City/Local Sales Tax Component - Community']:,.2f}"
    )


    # --------------------------------------------------------
    # 8. Important county-retention note
    # --------------------------------------------------------

    print()
    print("IMPORTANT NOTE")
    print("-" * 70)

    print(
        "The County Sales Tax Component is calculated using "
        "the 'County Sales Tax' field in county_inputs.xlsx."
    )

    print(
        "For Sedgwick, your current input is 1.00%."
    )

    print(
        "This is not yet labeled final county-retained fiscal "
        "benefit until the Kansas/Sedgwick revenue-sharing "
        "rule is verified."
    )


    # --------------------------------------------------------
    # 9. Save Module 2 Excel
    # --------------------------------------------------------

    output_file = save_module2_output(
        results,
        mapping_detail,
        quintile_summary
    )

    print()

    print(
        "Module 2 Excel saved to:"
    )

    print(output_file)

    print()
    print("MODULE 2 COMPLETED")

    return results


# ============================================================
# MODULE 3 - SCHOOL SYSTEM IMPACT
# ============================================================

def run_module3(counties):

    print("\n==============================")
    print("MODULE 3 - SCHOOL SYSTEM IMPACT")
    print("==============================")

    # --------------------------------------------------------
    # 1. Load NCES F-33 data
    # --------------------------------------------------------

    f33 = load_f33_data(
        DATA_DIR / "sdf24_1a.txt"
    )

    results = []
    sensitivity_results = []

    # --------------------------------------------------------
    # 2. Run base school impact model
    # --------------------------------------------------------

    for _, county_row in counties.iterrows():

        # Skip counties without school information
        if pd.isna(county_row["School District"]):
            continue

        if pd.isna(county_row["District Capacity"]):
            continue

        print(
            f"Processing {county_row['County']} "
            f"- {county_row['School District']}"
        )

        try:

            result = calculate_school_impact(
                county_row,
                f33
            )

            results.append(result)

            # ------------------------------------------------
            # 3. Sedgwick County sensitivity analysis
            # ------------------------------------------------

            county_name = str(
                county_row["County"]
            ).strip().lower()

            if "sedgwick" in county_name:

                sensitivity = (
                    school_capacity_sensitivity(
                        result
                    )
                )

                sensitivity_results.append(
                    sensitivity
                )

        except Exception as e:

            print(
                f"ERROR: {county_row['County']} - {e}"
            )

    # --------------------------------------------------------
    # 4. Convert results to DataFrames
    # --------------------------------------------------------

    results_df = pd.DataFrame(results)

    if sensitivity_results:

        sensitivity_df = pd.concat(
            sensitivity_results,
            ignore_index=True
        )

    else:

        sensitivity_df = pd.DataFrame()

    # --------------------------------------------------------
    # 5. Save Module 3 Excel
    # --------------------------------------------------------

    output_file = (
        OUTPUT_DIR
        / "module3_school_impact.xlsx"
    )

    with pd.ExcelWriter(
        output_file,
        engine="openpyxl"
    ) as writer:

        results_df.to_excel(
            writer,
            sheet_name="School_Impact_Results",
            index=False
        )

        sensitivity_df.to_excel(
            writer,
            sheet_name="Capacity_Sensitivity",
            index=False
        )

    # --------------------------------------------------------
    # 6. Print sensitivity results
    # --------------------------------------------------------

    print()
    print("SEDGWICK SCHOOL CAPACITY SENSITIVITY")
    print("-" * 70)

    if not sensitivity_df.empty:

        print(
            sensitivity_df[
                [
                    "Scenario",
                    "Capacity Utilization",
                    "Capacity Discount",
                    "Marginal Cost",
                    "Net School Impact",
                    "Over Capacity Flag",
                ]
            ].to_string(index=False)
        )

    print()
    print(
        "Module 3 results saved to:"
    )
    print(output_file)

    print()
    print("MODULE 3 COMPLETED")

    return results_df

    print()
    print("=" * 70)
    print("MODULE 3 - SCHOOL SYSTEM IMPACT")
    print("=" * 70)


    # --------------------------------------------------------
    # 1. Load NCES F-33 data
    # --------------------------------------------------------

    print()
    print("Loading NCES F-33 school finance data...")

    f33 = load_f33_data(
        F33_FILE
    )


    # --------------------------------------------------------
    # 2. Run Module 3 for counties with school data
    # --------------------------------------------------------

    results = []

    for _, county_row in counties.iterrows():

        # Skip if School District is missing
        if pd.isna(
            county_row.get("School District")
        ):
            continue

        # Skip if District Capacity is missing
        if pd.isna(
            county_row.get("District Capacity")
        ):
            continue


        print()

        print(
            f"Processing: "
            f"{county_row['County']}, "
            f"{county_row['State']} "
            f"- {county_row['School District']}"
        )


        try:

            result = calculate_school_impact(
                county_row,
                f33
            )

            results.append(
                result
            )


        except Exception as e:

            print(
                f"ERROR for "
                f"{county_row['County']}: {e}"
            )


    # --------------------------------------------------------
    # 3. Convert results to DataFrame
    # --------------------------------------------------------

    results_df = pd.DataFrame(
        results
    )


    # --------------------------------------------------------
    # 4. Check if any districts were processed
    # --------------------------------------------------------

    if results_df.empty:

        print()
        print(
            "No Module 3 results were generated."
        )

        print(
            "Check School District and District Capacity "
            "in county_inputs.xlsx."
        )

        return results_df


    # --------------------------------------------------------
    # 5. Print Module 3 results
    # --------------------------------------------------------

    print()
    print("SCHOOL SYSTEM IMPACT RESULTS")
    print("-" * 70)


    for _, row in results_df.iterrows():

        print()

        print(
            f"County: "
            f"{row['County']}, {row['State']}"
        )

        print(
            "School District: "
            f"{row['School District']}"
        )

        print(
            "NCES LEA ID: "
            f"{row['NCES LEA ID']}"
        )

        print(
            "Total Homes: "
            f"{row['Total Homes']:,.0f}"
        )

        print(
            "3BD Homes: "
            f"{row['3BD Homes']:,.0f}"
        )

        print(
            "2BD Homes: "
            f"{row['2BD Homes']:,.0f}"
        )

        print(
            "Estimated New Students: "
            f"{row['Estimated New Students']:,.2f}"
        )

        print(
            "F-33 Enrollment (V33): "
            f"{row['F33 Enrollment V33']:,.0f}"
        )

        print(
            "State Revenue Per Pupil: "
            f"${row['State Revenue Per Pupil']:,.2f}"
        )

        print(
            "State Aid Received: "
            f"${row['State Aid Received']:,.2f}"
        )

        print(
            "Operating Cost Per Pupil: "
            f"${row['Operating Cost Per Pupil']:,.2f}"
        )

        print(
            "District Capacity: "
            f"{row['District Capacity']:,.0f}"
        )

        print(
            "Capacity Utilization: "
            f"{row['Capacity Utilization %']:.2f}%"
        )

        print(
            "Capacity Status: "
            f"{row['Capacity Status']}"
        )

        print(
            "Over Capacity Flag: "
            f"{row['Over Capacity Flag']}"
        )


        # Capacity discount may still be None
        if pd.notna(
            row["Capacity Discount"]
        ):

            print(
                "Capacity Discount: "
                f"{row['Capacity Discount']:.2%}"
            )

        else:

            print(
                "Capacity Discount: "
                "TBD - waiting for assumption"
            )


        # Marginal cost may still be None
        if pd.notna(
            row["Marginal Cost"]
        ):

            print(
                "Marginal Cost: "
                f"${row['Marginal Cost']:,.2f}"
            )

        else:

            print(
                "Marginal Cost: "
                "TBD"
            )


        # Net impact may still be None
        if pd.notna(
            row["Net School Impact"]
        ):

            print(
                "Net School Impact: "
                f"${row['Net School Impact']:,.2f}"
            )

        else:

            print(
                "Net School Impact: "
                "TBD"
            )


    # --------------------------------------------------------
    # 6. Save Module 3 Excel
    # --------------------------------------------------------

    output_file = (
        OUTPUT_DIR
        / "module3_school_impact.xlsx"
    )

    results_df.to_excel(
        output_file,
        index=False
    )


    print()
    print(
        "Module 3 Excel saved to:"
    )

    print(output_file)

    print()
    print("MODULE 3 COMPLETED")

    return results_df


# ============================================================
# MAIN - RUN ALL AVAILABLE MODULES
# ============================================================

def main():

    print()
    print("=" * 70)
    print("LAGOM MUNICIPAL FISCAL IMPACT MODEL")
    print("=" * 70)


    # --------------------------------------------------------
    # Load county inputs for Module 3
    # --------------------------------------------------------

    counties = pd.read_excel(
        COUNTY_INPUTS_FILE
    )


    # --------------------------------------------------------
    # Module 1
    # --------------------------------------------------------

    run_module1()


    # --------------------------------------------------------
    # Module 2
    # --------------------------------------------------------

    run_module2()


    # --------------------------------------------------------
    # Module 3
    # --------------------------------------------------------

    run_module3(
        counties
    )


    # --------------------------------------------------------
    # Finished
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print(
        "ALL AVAILABLE MODULES COMPLETED SUCCESSFULLY"
    )
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()