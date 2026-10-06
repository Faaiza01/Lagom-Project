import pandas as pd
from modules.property_tax import calculate_property_tax, abatement_sensitivity

def test_sedgwick_example():
    df = pd.DataFrame([{
        "County":"Sedgwick","State":"KS","Homes":150,
        "Average Sale Price":223000,"Assessment Ratio":0.115,
        "County Millage":27.567,"Fire EMS Millage":16.754,
        "School Millage":51.402,"Municipal Millage":32.34,
        "Other Levies":0,"Applicable Municipal Millage":0,
        "PILOT Annual Payment":None,
    }])
    r = calculate_property_tax(df).iloc[0]
    assert round(r["Gross Assessed Value"], 2) == 3846750.00
    assert round(r["Total Applicable Millage"], 3) == 95.723
    assert round(r["Gross Annual Property Tax"], 2) == 368222.45

    s = abatement_sensitivity(pd.DataFrame([r]))
    phase = s[s["Scenario"] == "5-Year Phase-In"]
    assert list(phase["Taxable Share"]) == [0.2,0.4,0.6,0.8,1.0]
