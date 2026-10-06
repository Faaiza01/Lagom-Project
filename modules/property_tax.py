from __future__ import annotations
import pandas as pd

REQUIRED_COLUMNS = [
    "County",
    "State",
    "Homes",
    "Average Sale Price",
    "Assessment Ratio",
    "County Millage",
    "Fire EMS Millage",
    "School Millage",
    "Municipal Millage",
    "Other Levies",
]

def _number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip(),
        errors="coerce",
    )

def _ratio(series: pd.Series) -> pd.Series:
    raw = series.astype(str).str.replace("%", "", regex=False).str.strip()
    x = pd.to_numeric(raw, errors="coerce")
    return x.where(x <= 1, x / 100)

def validate_inputs(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))

def calculate_property_tax(df: pd.DataFrame) -> pd.DataFrame:
    validate_inputs(df)
    out = df.copy()

    out["Homes"] = _number(out["Homes"])
    out["Average Sale Price"] = _number(out["Average Sale Price"])
    out["Assessment Ratio"] = _ratio(out["Assessment Ratio"])

    millage_cols = [
        "County Millage",
        "Fire EMS Millage",
        "School Millage",
        "Municipal Millage",
        "Other Levies",
    ]
    for c in millage_cols:
        out[c] = _number(out[c]).fillna(0)

    if "Applicable Municipal Millage" in out.columns:
        out["Applicable Municipal Millage"] = _number(
            out["Applicable Municipal Millage"]
        ).fillna(out["Municipal Millage"])
    else:
        out["Applicable Municipal Millage"] = out["Municipal Millage"]

    if "PILOT Annual Payment" in out.columns:
        out["PILOT Annual Payment"] = _number(out["PILOT Annual Payment"])
    else:
        out["PILOT Annual Payment"] = pd.NA

    out["Gross Market Value"] = out["Homes"] * out["Average Sale Price"]
    out["Gross Assessed Value"] = (
        out["Homes"] * out["Average Sale Price"] * out["Assessment Ratio"]
    )

    out["Total Applicable Millage"] = (
        out["County Millage"]
        + out["Fire EMS Millage"]
        + out["School Millage"]
        + out["Applicable Municipal Millage"]
        + out["Other Levies"]
    )

    out["Gross Annual Property Tax"] = (
        out["Gross Assessed Value"] * out["Total Applicable Millage"] / 1000
    )

    out["Gross Tax Per Home"] = (
        out["Gross Annual Property Tax"] / out["Homes"]
    )

    return out

def tax_breakdown(results: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        "County": "County Millage",
        "Fire/EMS": "Fire EMS Millage",
        "School": "School Millage",
        "Municipal": "Applicable Municipal Millage",
        "Other": "Other Levies",
    }

    rows = []
    for _, r in results.iterrows():
        for authority, col in mapping.items():
            mills = r[col]
            rows.append({
                "County": r["County"],
                "State": r["State"],
                "Authority": authority,
                "Millage": mills,
                "Annual Revenue": r["Gross Assessed Value"] * mills / 1000,
            })
    return pd.DataFrame(rows)

def abatement_sensitivity(results: pd.DataFrame) -> pd.DataFrame:
    """
    Three syllabus-required scenarios:
      1) No abatement / gross
      2) 5-year phase-in: 20%, 40%, 60%, 80%, 100%
      3) Full PILOT: fixed payment input; TBD if unavailable
    """
    rows = []
    phase = {1: 0.20, 2: 0.40, 3: 0.60, 4: 0.80, 5: 1.00}

    for _, r in results.iterrows():
        gross = float(r["Gross Annual Property Tax"])

        for year in range(1, 6):
            rows.append({
                "County": r["County"],
                "State": r["State"],
                "Scenario": "No Abatement / Gross",
                "Year": year,
                "Taxable Share": 1.00,
                "Gross Annual Property Tax": gross,
                "Net Annual Revenue": gross,
                "Scenario Note": "Ceiling case; full gross property tax",
            })

        for year, share in phase.items():
            rows.append({
                "County": r["County"],
                "State": r["State"],
                "Scenario": "5-Year Phase-In",
                "Year": year,
                "Taxable Share": share,
                "Gross Annual Property Tax": gross,
                "Net Annual Revenue": gross * share,
                "Scenario Note": "Syllabus sensitivity: 20%, 40%, 60%, 80%, 100%",
            })

        pilot = r.get("PILOT Annual Payment", pd.NA)
        for year in range(1, 6):
            rows.append({
                "County": r["County"],
                "State": r["State"],
                "Scenario": "Full PILOT",
                "Year": year,
                "Taxable Share": pd.NA,
                "Gross Annual Property Tax": gross,
                "Net Annual Revenue": pilot if pd.notna(pilot) else "TBD",
                "Scenario Note": (
                    "Fixed PILOT payment from agreement/input"
                    if pd.notna(pilot)
                    else "TBD — no documented/approved PILOT input supplied"
                ),
            })

    return pd.DataFrame(rows)

def home_price_sensitivity(results: pd.DataFrame,
                           homes=(100, 150, 200),
                           prices=(220000, 250000, 280000)) -> pd.DataFrame:
    """
    Deliverable sensitivity for community size and average sale price.
    Uses each county's assessment ratio and applicable millage.
    """
    rows = []
    for _, r in results.iterrows():
        for h in homes:
            for p in prices:
                assessed = h * p * r["Assessment Ratio"]
                tax = assessed * r["Total Applicable Millage"] / 1000
                rows.append({
                    "County": r["County"],
                    "State": r["State"],
                    "Homes": h,
                    "Average Sale Price": p,
                    "Assessment Ratio": r["Assessment Ratio"],
                    "Total Applicable Millage": r["Total Applicable Millage"],
                    "Gross Assessed Value": assessed,
                    "Gross Annual Property Tax": tax,
                })
    return pd.DataFrame(rows)
