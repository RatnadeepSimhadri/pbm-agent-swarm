import logging
from datetime import date

from sqlalchemy.orm import Session

from app.models.drug import Drug
from app.models.formulary import Formulary, FormularyDrug
from app.models.member import Member
from app.models.pharmacy import Pharmacy
from app.models.plan import Plan
from app.models.prescriber import Prescriber

logger = logging.getLogger(__name__)


def seed_database(db: Session) -> None:
    if db.query(Plan).count() > 0:
        logger.info("Database already seeded, skipping")
        return

    logger.info("Seeding database...")

    # --- Plans ---
    plans = [
        Plan(
            id=1,
            name="Gold Plan",
            description="Premium coverage with the lowest copays. Ideal for members with ongoing prescriptions or complex medication needs.",
        ),
        Plan(
            id=2,
            name="Silver Plan",
            description="Balanced coverage with moderate copays. A great choice for members who fill prescriptions regularly.",
        ),
        Plan(
            id=3,
            name="Bronze Plan",
            description="Essential coverage with higher copays and lower premiums. Best for members with occasional prescription needs.",
        ),
    ]
    db.add_all(plans)
    db.flush()

    # --- Drugs (50 real FDA drugs) ---
    drugs_data = [
        # Tier 1 — Preferred Generics
        ("Metformin", "00378-0234-01", "metformin", None, "500mg", "tablet", "Mylan Pharmaceuticals", "Oral diabetes medicine that helps control blood sugar levels."),
        ("Lisinopril", "00378-0560-01", "lisinopril", None, "10mg", "tablet", "Mylan Pharmaceuticals", "ACE inhibitor used to treat high blood pressure and heart failure."),
        ("Amlodipine", "00378-0074-01", "amlodipine", None, "5mg", "tablet", "Mylan Pharmaceuticals", "Calcium channel blocker for high blood pressure and chest pain."),
        ("Omeprazole", "00378-6140-01", "omeprazole", None, "20mg", "capsule", "Mylan Pharmaceuticals", "Proton pump inhibitor for acid reflux and stomach ulcers."),
        ("Simvastatin", "00378-4272-01", "simvastatin", None, "20mg", "tablet", "Mylan Pharmaceuticals", "Statin that lowers cholesterol and reduces cardiovascular risk."),
        ("Levothyroxine", "00378-1805-01", "levothyroxine", None, "50mcg", "tablet", "Mylan Pharmaceuticals", "Thyroid hormone replacement for hypothyroidism."),
        ("Metoprolol Succinate", "00378-3612-01", "metoprolol succinate", None, "25mg", "tablet ER", "Mylan Pharmaceuticals", "Beta-blocker for high blood pressure, chest pain, and heart failure."),
        ("Losartan", "00378-0614-01", "losartan", None, "50mg", "tablet", "Mylan Pharmaceuticals", "ARB used to treat high blood pressure and protect kidneys in diabetes."),
        ("Gabapentin", "00378-4012-01", "gabapentin", None, "300mg", "capsule", "Mylan Pharmaceuticals", "Anticonvulsant also used for nerve pain."),
        ("Hydrochlorothiazide", "00378-0042-01", "hydrochlorothiazide", None, "25mg", "tablet", "Mylan Pharmaceuticals", "Thiazide diuretic for high blood pressure and fluid retention."),
        ("Sertraline", "00378-4187-01", "sertraline", None, "50mg", "tablet", "Mylan Pharmaceuticals", "SSRI antidepressant for depression, anxiety, and OCD."),
        ("Atorvastatin", "00378-2077-01", "atorvastatin", None, "20mg", "tablet", "Mylan Pharmaceuticals", "Statin that lowers cholesterol. Generic form of Lipitor."),
        ("Montelukast", "00378-6063-01", "montelukast", None, "10mg", "tablet", "Mylan Pharmaceuticals", "Leukotriene inhibitor for asthma and allergies."),
        ("Escitalopram", "00378-3853-01", "escitalopram", None, "10mg", "tablet", "Mylan Pharmaceuticals", "SSRI for depression and generalized anxiety disorder."),
        ("Pantoprazole", "00378-8140-01", "pantoprazole", None, "40mg", "tablet DR", "Mylan Pharmaceuticals", "Proton pump inhibitor for GERD and erosive esophagitis."),

        # Tier 2 — Non-Preferred Generics
        ("Clopidogrel", "63304-0098-90", "clopidogrel", None, "75mg", "tablet", "Ranbaxy Pharmaceuticals", "Antiplatelet drug to prevent blood clots after heart attack or stroke."),
        ("Tamsulosin", "00378-6105-01", "tamsulosin", None, "0.4mg", "capsule", "Mylan Pharmaceuticals", "Alpha-blocker for benign prostatic hyperplasia (BPH)."),
        ("Carvedilol", "00378-3635-01", "carvedilol", None, "12.5mg", "tablet", "Mylan Pharmaceuticals", "Beta-blocker for heart failure and high blood pressure."),
        ("Meloxicam", "00378-0076-01", "meloxicam", None, "15mg", "tablet", "Mylan Pharmaceuticals", "NSAID for osteoarthritis and rheumatoid arthritis pain."),
        ("Duloxetine", "00378-4075-01", "duloxetine", None, "30mg", "capsule DR", "Mylan Pharmaceuticals", "SNRI for depression, anxiety, nerve pain, and fibromyalgia."),
        ("Bupropion XL", "00378-5248-01", "bupropion", None, "150mg", "tablet XL", "Mylan Pharmaceuticals", "Antidepressant also used for smoking cessation."),
        ("Venlafaxine ER", "00378-3792-01", "venlafaxine", None, "75mg", "capsule ER", "Mylan Pharmaceuticals", "SNRI for depression, anxiety, and panic disorder."),
        ("Trazodone", "00378-5050-01", "trazodone", None, "50mg", "tablet", "Mylan Pharmaceuticals", "Antidepressant commonly used for insomnia."),
        ("Spironolactone", "00378-0243-01", "spironolactone", None, "25mg", "tablet", "Mylan Pharmaceuticals", "Potassium-sparing diuretic for heart failure and fluid retention."),
        ("Glipizide", "00378-0170-01", "glipizide", None, "5mg", "tablet", "Mylan Pharmaceuticals", "Sulfonylurea for type 2 diabetes."),
        ("Fluoxetine", "00378-3200-01", "fluoxetine", None, "20mg", "capsule", "Mylan Pharmaceuticals", "SSRI antidepressant (generic Prozac) for depression and OCD."),
        ("Allopurinol", "00378-0164-01", "allopurinol", None, "100mg", "tablet", "Mylan Pharmaceuticals", "Xanthine oxidase inhibitor for gout prevention."),
        ("Pravastatin", "00378-5200-01", "pravastatin", None, "40mg", "tablet", "Mylan Pharmaceuticals", "Statin for cholesterol management."),
        ("Citalopram", "00378-3612-05", "citalopram", None, "20mg", "tablet", "Mylan Pharmaceuticals", "SSRI antidepressant for depression."),
        ("Doxycycline", "00378-6205-01", "doxycycline", None, "100mg", "capsule", "Mylan Pharmaceuticals", "Tetracycline antibiotic for infections, acne, and malaria prevention."),

        # Tier 3 — Preferred Brands
        ("Lipitor", "00071-0155-23", None, "lipitor", "20mg", "tablet", "Pfizer", "Brand-name statin for high cholesterol. (Generic: atorvastatin)"),
        ("Crestor", "00310-0755-90", None, "crestor", "10mg", "tablet", "AstraZeneca", "Brand-name statin for high cholesterol. (Generic: rosuvastatin)"),
        ("Eliquis", "00003-0894-21", None, "eliquis", "5mg", "tablet", "Bristol-Myers Squibb", "Anticoagulant to prevent blood clots and stroke in atrial fibrillation."),
        ("Xarelto", "50458-0580-30", None, "xarelto", "20mg", "tablet", "Janssen Pharmaceuticals", "Blood thinner for DVT, PE, and stroke prevention."),
        ("Jardiance", "00597-0152-30", None, "jardiance", "10mg", "tablet", "Boehringer Ingelheim", "SGLT2 inhibitor for type 2 diabetes and heart failure."),
        ("Entresto", "00078-0620-15", None, "entresto", "49/51mg", "tablet", "Novartis", "Combination drug for heart failure with reduced ejection fraction."),
        ("Ozempic", "00169-4132-12", None, "ozempic", "1mg", "injection", "Novo Nordisk", "GLP-1 receptor agonist for type 2 diabetes."),
        ("Trulicity", "00002-1465-01", None, "trulicity", "1.5mg", "injection", "Eli Lilly", "GLP-1 receptor agonist for type 2 diabetes."),
        ("Januvia", "00006-0277-31", None, "januvia", "100mg", "tablet", "Merck", "DPP-4 inhibitor for type 2 diabetes."),
        ("Symbicort", "00186-0372-20", None, "symbicort", "160/4.5mcg", "inhaler", "AstraZeneca", "Combination inhaler for asthma and COPD maintenance."),

        # Tier 4 — Specialty
        ("Humira", "00074-4339-02", None, "humira", "40mg", "injection", "AbbVie", "TNF blocker for rheumatoid arthritis, Crohn's, psoriasis, and more."),
        ("Enbrel", "58406-0425-04", None, "enbrel", "50mg", "injection", "Amgen", "TNF blocker for rheumatoid arthritis and psoriasis."),
        ("Stelara", "57894-0060-03", None, "stelara", "45mg", "injection", "Janssen Biotech", "IL-12/23 blocker for psoriasis and Crohn's disease."),
        ("Keytruda", "00006-3026-02", None, "keytruda", "200mg", "IV infusion", "Merck", "Immunotherapy for various cancers."),
        ("Revlimid", "59572-0405-00", None, "revlimid", "25mg", "capsule", "Bristol-Myers Squibb", "Immunomodulator for multiple myeloma."),
        ("Dupixent", "00024-5918-01", None, "dupixent", "300mg", "injection", "Regeneron", "IL-4/IL-13 blocker for eczema, asthma, and nasal polyps."),
        ("Otezla", "00003-0535-11", None, "otezla", "30mg", "tablet", "Amgen", "PDE4 inhibitor for psoriatic arthritis and plaque psoriasis."),
        ("Rinvoq", "00074-2306-30", None, "rinvoq", "15mg", "tablet ER", "AbbVie", "JAK inhibitor for rheumatoid arthritis and ulcerative colitis."),
        ("Skyrizi", "00074-2150-01", None, "skyrizi", "150mg", "injection", "AbbVie", "IL-23 blocker for plaque psoriasis."),
        ("Cosentyx", "00078-0639-98", None, "cosentyx", "150mg", "injection", "Novartis", "IL-17A blocker for psoriasis and ankylosing spondylitis."),
    ]

    drugs = []
    for i, (name, ndc, generic, brand, strength, form, mfr, desc) in enumerate(drugs_data, 1):
        drugs.append(Drug(
            id=i, name=name, ndc_code=ndc, generic_name=generic,
            brand_name=brand, strength=strength, form=form,
            manufacturer=mfr, description=desc,
        ))
    db.add_all(drugs)
    db.flush()

    # --- Formularies & Drug Mappings ---
    #   Tier copays: Gold ($10/$25/$50/$75), Silver ($15/$35/$65/$100), Bronze ($20/$45/$80/$125)
    tier_copays = {
        1: {1: 10.0, 2: 15.0, 3: 20.0},   # Tier 1 copays per plan
        2: {1: 25.0, 2: 35.0, 3: 45.0},   # Tier 2
        3: {1: 50.0, 2: 65.0, 3: 80.0},   # Tier 3
        4: {1: 75.0, 2: 100.0, 3: 125.0}, # Tier 4
    }

    # Drug tier assignments (by drug index, 0-based)
    # Tier 1: drugs 0-14 (generics), Tier 2: drugs 15-29, Tier 3: drugs 30-39, Tier 4: drugs 40-49
    def get_tier(drug_index: int) -> int:
        if drug_index < 15:
            return 1
        elif drug_index < 30:
            return 2
        elif drug_index < 40:
            return 3
        else:
            return 4

    formularies = []
    formulary_drugs = []
    fd_id = 1

    for plan_id in [1, 2, 3]:
        formulary = Formulary(
            id=plan_id,
            plan_id=plan_id,
            name=f"{plans[plan_id - 1].name} Formulary",
            effective_date=date(2025, 1, 1),
        )
        formularies.append(formulary)

        for drug_idx, drug in enumerate(drugs):
            tier = get_tier(drug_idx)
            copay = tier_copays[tier][plan_id]

            # Some drugs require prior auth (specialty tier mostly)
            prior_auth = tier == 4
            # Quantity limits on controlled/expensive drugs
            quantity_limit = 30 if tier <= 2 else (90 if tier == 3 else None)
            # Step therapy on tier 3+ brands
            step_therapy = tier >= 3

            formulary_drugs.append(FormularyDrug(
                id=fd_id,
                formulary_id=plan_id,
                drug_id=drug.id,
                tier=tier,
                copay_amount=copay,
                prior_auth_required=prior_auth,
                quantity_limit=quantity_limit,
                step_therapy_required=step_therapy,
            ))
            fd_id += 1

    db.add_all(formularies)
    db.add_all(formulary_drugs)
    db.flush()

    # --- Members ---
    members = [
        Member(id=1, first_name="Sarah", last_name="Johnson", email="sarah.johnson@example.com", date_of_birth=date(1985, 3, 15), plan_id=1),
        Member(id=2, first_name="Michael", last_name="Chen", email="michael.chen@example.com", date_of_birth=date(1990, 7, 22), plan_id=1),
        Member(id=3, first_name="Emily", last_name="Rodriguez", email="emily.rodriguez@example.com", date_of_birth=date(1978, 11, 8), plan_id=2),
        Member(id=4, first_name="James", last_name="Wilson", email="james.wilson@example.com", date_of_birth=date(1965, 5, 30), plan_id=2),
        Member(id=5, first_name="Priya", last_name="Patel", email="priya.patel@example.com", date_of_birth=date(1992, 9, 12), plan_id=3),
    ]
    db.add_all(members)

    # --- Pharmacies ---
    pharmacies = [
        Pharmacy(id=1, name="CVS Pharmacy #4521", address="123 Main Street", city="Boston", state="MA", zip_code="02101", phone="617-555-0100", pharmacy_type="retail"),
        Pharmacy(id=2, name="Walgreens #9832", address="456 Oak Avenue", city="Cambridge", state="MA", zip_code="02139", phone="617-555-0200", pharmacy_type="retail"),
        Pharmacy(id=3, name="Rite Aid #1245", address="789 Elm Boulevard", city="Somerville", state="MA", zip_code="02143", phone="617-555-0300", pharmacy_type="retail"),
        Pharmacy(id=4, name="Express Scripts Mail Pharmacy", address="4600 N Hanley Rd", city="St. Louis", state="MO", zip_code="63134", phone="800-555-0400", pharmacy_type="mail_order"),
        Pharmacy(id=5, name="OptumRx Mail Order", address="2300 Main Street", city="Irvine", state="CA", zip_code="92614", phone="800-555-0500", pharmacy_type="mail_order"),
    ]
    db.add_all(pharmacies)

    # --- Prescribers ---
    prescribers = [
        Prescriber(id=1, first_name="Robert", last_name="Martinez", npi="1234567890", specialty="Internal Medicine", phone="617-555-1001"),
        Prescriber(id=2, first_name="Lisa", last_name="Thompson", npi="2345678901", specialty="Cardiology", phone="617-555-1002"),
        Prescriber(id=3, first_name="David", last_name="Kim", npi="3456789012", specialty="Endocrinology", phone="617-555-1003"),
        Prescriber(id=4, first_name="Amanda", last_name="Foster", npi="4567890123", specialty="Psychiatry", phone="617-555-1004"),
        Prescriber(id=5, first_name="Kevin", last_name="O'Brien", npi="5678901234", specialty="Rheumatology", phone="617-555-1005"),
    ]
    db.add_all(prescribers)

    db.commit()
    logger.info("Database seeded successfully: %d drugs, %d plans, %d members", len(drugs), len(plans), len(members))
