# Module 4 placeholder — Infrastructure Cost Offset
import pandas as pd


# ============================================================
# MODULE 4 - INFRASTRUCTURE COST OFFSET
# ============================================================

# Sponsor-approved standard assumptions
TRADITIONAL_INSPECTIONS = 6
SIP_INSPECTIONS = 3
INSPECTOR_COST_PER_TRIP = 150


def calculate_infrastructure_offset(counties):
    """
    Calculate the one-time infrastructure cost offset created by
    fewer field inspections for SIP-built Lagom homes.

    Formula:
        Saved inspections per unit
        x Inspector cost per trip
        x Total homes

    Standard assumptions:
        Traditional inspections = 6
        SIP inspections = 3
        Inspector cost per trip = $150

    IMPORTANT:
        This is a ONE-TIME benefit, not an annual benefit.
    """

    results = []

    saved_inspections_per_unit = (
        TRADITIONAL_INSPECTIONS
        - SIP_INSPECTIONS
    )

    for _, row in counties.iterrows():

        # Your existing input file uses "Homes"
        homes = row["Homes"]

        total_avoided_inspections = (
            homes
            * saved_inspections_per_unit
        )

        infrastructure_cost_offset = (
            total_avoided_inspections
            * INSPECTOR_COST_PER_TRIP
        )

        results.append({
            "County": row["County"],
            "State": row["State"],
            "Homes": homes,

            "Traditional Inspections per Unit":
                TRADITIONAL_INSPECTIONS,

            "SIP Inspections per Unit":
                SIP_INSPECTIONS,

            "Saved Inspections per Unit":
                saved_inspections_per_unit,

            "Inspector Cost per Trip":
                INSPECTOR_COST_PER_TRIP,

            "Total Avoided Inspections":
                total_avoided_inspections,

            "Infrastructure Cost Offset":
                infrastructure_cost_offset,

            "Benefit Type":
                "One-Time",

            "Cost Source":
                "Sponsor-approved standard assumption",

            "Inspection Count Source":
                "Track A methodology"
        })

    return pd.DataFrame(results)