# Module 3 placeholder — School System Impact

import pandas as pd


STUDENT_RATE_3BD = 0.60
STUDENT_RATE_2BD = 0.20

# TEMPORARY until professor confirms product mix
DEFAULT_3BD_SHARE = 0.60
DEFAULT_2BD_SHARE = 0.40

# Waiting for professor guidance
CAPACITY_DISCOUNT = 0.9


def load_f33_data(f33_file):

    f33 = pd.read_csv(
        f33_file,
        sep="\t",
        dtype=str,
        low_memory=False
    )

    f33.columns = f33.columns.str.strip()

    f33["NAME"] = f33["NAME"].astype(str).str.strip()
    f33["STNAME"] = f33["STNAME"].astype(str).str.strip()

    return f33


def find_school_district(f33, state, school_district):

    state_clean = str(state).strip().lower()
    district_clean = str(school_district).strip().lower()

    district = f33[
        (f33["STNAME"].str.lower() == state_clean)
        &
        (f33["NAME"].str.lower() == district_clean)
    ]

    if district.empty:
        raise ValueError(
            f"District not found: {school_district}, {state}"
        )

    if len(district) > 1:
        raise ValueError(
            f"Multiple districts found: {school_district}, {state}"
        )

    return district.iloc[0]


def calculate_school_impact(county_row, f33):

    county = county_row["County"]
    state = county_row["State"]
    total_homes = float(county_row["Homes"])

    school_district = county_row["School District"]
    district_capacity = float(county_row["District Capacity"])

    # STEP 1: Temporary 3BD / 2BD mix
    homes_3bd = total_homes * DEFAULT_3BD_SHARE
    homes_2bd = total_homes * DEFAULT_2BD_SHARE

    # STEP 2: New students
    new_students = (
        homes_3bd * STUDENT_RATE_3BD
        + homes_2bd * STUDENT_RATE_2BD
    )

    # STEP 3: Find district in F-33
    district = find_school_district(
        f33,
        state,
        school_district
    )

    # Automatically obtained from F-33
    lea_id = district["LEAID"]

    # STEP 4: F-33 data
    enrollment = float(district["V33"])
    total_state_revenue = float(district["TSTREV"])
    operating_expenditure = float(district["TCURELSC"])

    # STEP 5: State revenue per pupil
    state_revenue_per_pupil = (
        total_state_revenue / enrollment
    )

    state_aid_received = (
        new_students * state_revenue_per_pupil
    )

    # STEP 6: Operating cost per pupil
    operating_cost_per_pupil = (
        operating_expenditure / enrollment
    )

    # STEP 7: Capacity utilization
    capacity_utilization = (
        enrollment / district_capacity
    )

    # STEP 8: Capacity status
    if capacity_utilization < 0.85:
        capacity_status = "Below 85% capacity"
        over_capacity_flag = False

    elif capacity_utilization <= 1.00:
        capacity_status = "85%-100% capacity"
        over_capacity_flag = False

    else:
        capacity_status = "Over capacity"
        over_capacity_flag = True

    # STEP 9-11
    # Waiting for professor to confirm discount
    if CAPACITY_DISCOUNT is not None:

        marginal_cost = (
            new_students
            * operating_cost_per_pupil
            * (1 - CAPACITY_DISCOUNT)
        )

        net_school_impact = (
            state_aid_received - marginal_cost
        )

    else:
        marginal_cost = None
        net_school_impact = None

    return {
        "County": county,
        "State": state,
        "School District": school_district,
        "NCES LEA ID": lea_id,

        "Total Homes": total_homes,
        "3BD Homes": homes_3bd,
        "2BD Homes": homes_2bd,

        "Estimated New Students": new_students,

        "F33 Enrollment V33": enrollment,
        "F33 Total State Revenue TSTREV": total_state_revenue,
        "State Revenue Per Pupil": state_revenue_per_pupil,
        "State Aid Received": state_aid_received,

        "F33 Operating Expenditure TCURELSC":
            operating_expenditure,

        "Operating Cost Per Pupil":
            operating_cost_per_pupil,

        "District Capacity":
            district_capacity,

        "Capacity Utilization":
            capacity_utilization,

        "Capacity Utilization %":
            capacity_utilization * 100,

        "Capacity Status":
            capacity_status,

        "Over Capacity Flag":
            over_capacity_flag,

        "Capacity Discount":
            CAPACITY_DISCOUNT,

        "Marginal Cost":
            marginal_cost,

        "Net School Impact":
            net_school_impact
    }
    
def school_capacity_sensitivity(base_result):
    """
    School-capacity sensitivity analysis.

    Compares:
      1. 85% capacity utilization
      2. 110% capacity utilization

    Modeling assumptions:
      - 85% utilization -> 90% capacity discount
      - 110% utilization -> 0% capacity discount

    These discount percentages are scenario assumptions because
    the Lagom syllabus defines the capacity conditions but does
    not provide exact numerical discount percentages.
    """

    new_students = float(
        base_result["Estimated New Students"]
    )

    state_revenue_per_pupil = float(
        base_result["State Revenue Per Pupil"]
    )

    operating_cost_per_pupil = float(
        base_result["Operating Cost Per Pupil"]
    )

    state_aid_received = (
        new_students
        * state_revenue_per_pupil
    )

    scenarios = [
        {
            "Scenario": "85% Capacity",
            "Capacity Utilization": 0.85,
            "Capacity Discount": 0.90,
            "Capacity Status": "At 85% Threshold",
            "Over Capacity Flag": False,
        },
        {
            "Scenario": "110% Capacity",
            "Capacity Utilization": 1.10,
            "Capacity Discount": 0.00,
            "Capacity Status": "Over Capacity",
            "Over Capacity Flag": True,
        },
    ]

    rows = []

    for scenario in scenarios:

        discount = scenario["Capacity Discount"]

        marginal_cost_per_student = (
            operating_cost_per_pupil
            * (1 - discount)
        )

        marginal_cost = (
            new_students
            * marginal_cost_per_student
        )

        net_school_impact = (
            state_aid_received
            - marginal_cost
        )

        rows.append(
            {
                "County": base_result["County"],
                "State": base_result["State"],
                "School District": base_result["School District"],

                "Scenario": scenario["Scenario"],

                "Capacity Utilization":
                    scenario["Capacity Utilization"],

                "Capacity Status":
                    scenario["Capacity Status"],

                "Over Capacity Flag":
                    scenario["Over Capacity Flag"],

                "Capacity Discount":
                    scenario["Capacity Discount"],

                "Estimated New Students":
                    new_students,

                "State Revenue Per Pupil":
                    state_revenue_per_pupil,

                "State Aid Received":
                    state_aid_received,

                "Operating Cost Per Pupil":
                    operating_cost_per_pupil,

                "Marginal Cost Per Student":
                    marginal_cost_per_student,

                "Marginal Cost":
                    marginal_cost,

                "Net School Impact":
                    net_school_impact,

                "Discount Basis":
                    "Sensitivity scenario assumption",
            }
        )

    return pd.DataFrame(rows)