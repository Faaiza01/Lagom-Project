# Lagom Fiscal Impact Model — Track A

This is the project scaffold for the full Track A fiscal-impact model.

## Current implementation
Only **Module 1 — Property Tax Revenue** is implemented now.

Future modules have placeholder files so the project can grow without restructuring:
- Module 2 Sales Tax Uplift
- Module 3 School System Impact
- Module 4 Infrastructure Cost Offset
- Module 5/6 Job Creation + BEA RIMS II
- Municipal Value Summary
- Priority County Ranking

## Module 1 methodology

Gross assessed value:

`homes × average sale price × assessment ratio`

Gross annual property tax:

`gross assessed value × (total applicable millage / 1000)`

The model also decomposes tax by:
- county
- fire/EMS
- school district
- municipal
- other applicable levies

### Required sensitivity scenarios
1. No abatement / gross case
2. 5-year phase-in:
   - Year 1 = 20%
   - Year 2 = 40%
   - Year 3 = 60%
   - Year 4 = 80%
   - Year 5 = 100%
3. Full PILOT:
   - fixed annual payment supplied as an input
   - if no documented/approved PILOT amount is available, output is `TBD`

### Additional deliverable sensitivity
The model also tests:
- 100, 150, 200 homes
- $220K, $250K, $280K average sale price

These are separate from the three abatement scenarios.

## Input workbook

Default file: `data/county_inputs.xlsx`

Required columns:
- County
- State
- Homes
- Average Sale Price
- Assessment Ratio
- County Millage
- Fire EMS Millage
- School Millage
- Municipal Millage
- Other Levies
- Applicable Municipal Millage
- PILOT Annual Payment
- Tax District Scenario
- Property Tax Source URL
- Assessment Ratio Source URL
- PILOT Source URL
- Notes

Important:
- Keep raw municipal millage if useful, but use `Applicable Municipal Millage` for the actual selected tax district.
- PILOT payment should be blank unless supported by a real agreement or an explicitly approved modeling assumption.
- Source URLs should point to primary county/state sources where possible.

## Run

From the project folder:

```bash
pip install -r requirements.txt
python main.py --input data/county_inputs.xlsx --output outputs/module1_results.xlsx
```

## Output sheets

- Module1 Summary
- Tax Breakdown
- Abatement Sensitivity
- Home Price Sensitivity
- Input Data

