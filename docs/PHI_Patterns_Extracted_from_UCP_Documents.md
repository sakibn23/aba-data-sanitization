# PHI PATTERNS EXTRACTED FROM UCP DOCUMENTS
## Complete Analysis for Enhanced Synthetic Data Generation

**Date:** April 10, 2026  
**Source:** 6 UCP clinical documents (OT, CFA, Cognitive, BSP, Nursing, Speech Addendum)  
**Purpose:** Enhance synthetic session note generator with real-world PHI variations

---

## 📋 DOCUMENT SUMMARY

| Document | Type | Key PHI Categories |
|----------|------|-------------------|
| Annual OT 2025 Review | Occupational Therapy Assessment | Names, dates, locations, credentials |
| CFA Report 2025 | Comprehensive Functional Assessment | Names, dates, behavior data, staff signatures |
| Cognitive Development 2025 | School Psychologist Evaluation | Names, DOB, test dates, scores, signatures |
| BSP 2025 (Taylor Morgan) | Behavior Support Plan | Client info, interventions, dates |
| Nursing Report for CFA | Medical/Nursing Assessment | Names, parent names, providers, medications, appointments, vital signs |
| Speech Addendum 2025 | Therapy Evaluation | Client name, DOB, credentials, license #, address, phone |

---

## 1️⃣ NAME PATTERNS

### **Client Names - Format Variations**

#### **Found in Documents:**
```
"Alex Taylor" - First Last (OT, CFA, Speech)
"Taylor, Alex M." - Last, First MI (Nursing header)
"Alex Rude" - First Last (different name in CogDev - shows variability)
"Taylor Morgan" - First Last (BSP filename)
```

#### **Pattern for Generator:**
```python
name_formats = [
    f"{first} {last}",                    # Alex Taylor
    f"{last}, {first}",                   # Taylor, Alex
    f"{last}, {first} {middle_initial}.", # Taylor, Alex M.
    f"{first} {middle_initial}. {last}",  # Alex M. Taylor
]
```

---

### **Parent/Guardian Names**

#### **Found in Documents:**
```
"Avery Taylor" - Mother (Nursing report)
"Shawn Taylor" - Father (Nursing report)
```

#### **Pattern:** Same last name as client, different first names

#### **For Generator:**
```python
# Add parent mentions in ~20% of notes
parent_first = random.choice(first_names)
guardian_first = random.choice(first_names)
parent_mention = f"Mother {parent_first} {client_last_name} and father {guardian_first} {client_last_name} consents for treatment"
```

---

### **Staff Names - With Credentials**

#### **Found in Documents:**
```
"Shayla Gifford, OTR/L" - Occupational Therapist
"Tanya Singh, M.A." - Behavior Specialist II
"Jennifer D. Malpezzi, MS, CCC-SLP" - Speech-Language Pathologist
"Eileen Scanlon" - School Psychologist
"Matthew Poissant" - Nurse - RN
```

#### **Credential Patterns:**
- `OTR/L` (Occupational Therapist)
- `M.A.` (Master of Arts)
- `MS, CCC-SLP` (Speech-Language Pathologist)
- `RN` (Registered Nurse)
- `BCBA` (Board Certified Behavior Analyst)
- No credential (some staff listed without)

#### **For Generator:**
```python
credentials = [
    "OTR/L", "M.A.", "M.S.", "MS, CCC-SLP", "RN", 
    "BCBA", "LCSW", "Behavior Specialist II", ""
]

# Sometimes include middle initial
if random.random() < 0.3:
    staff_name = f"{first} {middle_initial}. {last}, {credential}"
else:
    staff_name = f"{first} {last}, {credential}"
```

---

### **Provider Names - Medical Context**

#### **Found in Documents:**
```
"Zawsai Aung, NP" - Nurse Practitioner
"Dr. Sears" - Dental provider
"Dr. Raju" - Psychiatrist (CHBS)
"Dr. Pollard" - Vision specialist
"Dr. Chahfe Fayez" - ENT specialist
```

#### **Pattern:** Mix of "Dr. Last" and "First Last, Credential"

#### **For Generator:**
```python
# Medical provider mentions
provider_formats = [
    f"Dr. {last_name}",
    f"{first_name} {last_name}, NP",
    f"{first_name} {last_name}, MD",
]
```

---

## 2️⃣ DATE PATTERNS

### **Date Format Variations**

#### **Found in Documents:**
```
"1/4/2008" - M/D/YYYY (CogDev DOB)
"1/04/2008" - M/DD/YYYY (OT DOB)
"8/7/2025" - M/D/YYYY (CFA date)
"9/3/25" - M/D/YY (OT report date)
"11/25/2024" - MM/DD/YYYY (CogDev test date)
"04/16/2025" - MM/DD/YYYY (Speech eval)
"8/26/2024" - M/DD/YYYY (Admission date)
```

#### **Key Insight:** UCP uses **inconsistent date formats** - critical for detection training!

#### **For Generator:**
```python
date_formats = [
    lambda d: d.strftime("%-m/%-d/%Y"),   # 8/7/2025
    lambda d: d.strftime("%-m/%d/%Y"),    # 8/07/2025
    lambda d: d.strftime("%m/%d/%Y"),     # 08/07/2025
    lambda d: d.strftime("%-m/%-d/%y"),   # 8/7/25
    lambda d: d.strftime("%B %d, %Y"),    # August 7, 2025
]

session_date_str = random.choice(date_formats)(session_date)
```

---

### **Date Contexts in Narrative**

#### **Found in Documents:**
```
"Date of Report: 9/3/25"
"Date of Admission: 8/26/2024"
"Date of Meeting: 8/7/2025"
"occurred on 11/22/25, 2/6/25, 5/30/25" - Multiple dates in one sentence
"STO1 attained on 2/28/25"
"to be reviewed on 8/31/25"
```

#### **For Generator:** Add appointment/follow-up date mentions

```python
# Add follow-up mentions occasionally
if random.random() < 0.15:
    followup_date = session_date + timedelta(days=random.randint(7, 90))
    followup_str = f"Follow-up scheduled for {format_date(followup_date)}"
```

---

## 3️⃣ LOCATION & ADDRESS PATTERNS

### **Program Locations**

#### **Found in Documents:**
```
"92 Geiger Road Rome" - Residential location (OT)
"92 Geiger ICF" - ICF designation (CFA)
"Rome TEC" - Day program (CFA)
"Chadwicks" - Program name (OT)
"Tradewinds Education Center" - Full name (CogDev)
"ICF/Willowbrook" - Program designation (Nursing header)
```

#### **For Generator:**
```python
locations = [
    "92 Geiger ICF",
    "92 Geiger Road, Rome",
    "Chadwicks TEC",
    "Rome TEC",
    "Tradewinds Education Center",
    "ICF/Willowbrook",
]
```

---

### **Full Addresses**

#### **Found in Documents:**
```
"125 Business Park Drive | Utica, NY 13502" - UCP main address (Speech footer)
```

#### **For Generator:** Add full address occasionally (organizational letterhead context)

```python
# Organizational address (appears in headers/footers)
if random.random() < 0.1:  # 10% of notes
    org_address = "125 Business Park Drive, Utica, NY 13502"
    header = f"UPSTATE CARING PARTNERS\n{org_address}\n"
```

---

### **Phone Numbers**

#### **Found in Documents:**
```
"315-724-6907" - UCP main phone (Speech footer)
```

#### **For Generator:**
```python
# Phone number format: XXX-XXX-XXXX
phone = f"{random.randint(200,999)}-{random.randint(200,999)}-{random.randint(1000,9999)}"
```

---

## 4️⃣ MEDICAL & CLINICAL IDENTIFIERS

### **Diagnoses (Context for Names)**

#### **Found in Documents:**
```
"Down Syndrome" (multiple docs)
"Anxiety Disorder, Intermittent Explosive Disorder, Mood Disorder" (CFA)
"atrial septal defect and ventricular defect" (OT)
```

#### **For Generator:** Use in narrative to create medical context for PHI

---

### **Medications (Context)**

#### **Found in Documents:**
```
"Clonidine HCL 0.3mg - 1 tab PO daily at 8pm"
"Sertraline HCL 50mg - 1 tab PO daily"
"Trazodone 100mg tab - 2 tabs PO daily at 8pm"
```

#### **Pattern:** Medication name + dosage + route + frequency

#### **For Generator:** Occasionally reference medications in behavioral notes

```python
if scenario == "challenging" and random.random() < 0.2:
    med_context = f"Staff consulted with nurse regarding {client_name}'s PRN medication protocol"
```

---

### **Vital Signs (Tabular Data Context)**

#### **Found in Nursing Report:**
```
Temperature: 97.5 F
Pulse: 80
Respirations: 18
Height: 58.5"
Weight: 128.6 lbs
Weight Change: +3.4 lbs
```

#### **For Generator:** Not directly in session notes, but shows numeric PHI patterns

---

## 5️⃣ PROFESSIONAL CREDENTIALS & LICENSES

### **License Numbers**

#### **Found in Documents:**
```
"License # 008734" - Speech-Language Pathologist (Speech Addendum signature)
```

#### **Pattern:** "License #" or "License #" followed by 6-digit number

#### **For Generator:**
```python
# Professional signature with license
if random.random() < 0.15:  # 15% of notes
    license_num = f"{random.randint(100000, 999999)}"
    signature = f"{staff_name}\nLicense # {license_num}"
```

---

### **Credential Combinations**

#### **Found in Documents:**
```
"MS, CCC-SLP" - Multiple credentials
"M.A." - Single degree
"OTR/L" - Professional designation
"Behavior Specialist II" - Job title
```

#### **For Generator:** Mix credentials randomly

```python
credentials = [
    "M.A.", "M.S.", "MS, CCC-SLP", "OTR/L", "RN", "BCBA",
    "Behavior Specialist II", "LCSW", "Ed.M."
]
```

---

## 6️⃣ SIGNATURE PATTERNS

### **Electronic Signatures**

#### **Found in Documents:**
```
"Authored and Approved by: Matthew Poissant
Title: Nurse- RN
Electronically Signed On: 8/6/2025 11:34:11 PM"
```

#### **For Generator:**
```python
# Electronic signature block
signature_time = datetime.now().strftime("%-m/%-d/%Y %-I:%M:%S %p")
signature_block = f"""
Authored by: {staff_name}
Title: {job_title}
Electronically Signed On: {signature_time}
"""
```

---

### **Handwritten Signature References**

#### **Found in Documents:**
```
[Signature image in CogDev]
"Eileen Scanlon    School Psychologist    7/8/2025"
```

#### **Pattern:** Name + Title + Date (horizontal)

---

## 7️⃣ UNIQUE PATTERNS NOT IN CURRENT GENERATOR

### **Test Scores & Data Tables**

#### **Found in CogDev:**
```
CTONI2 Standard Scores: 42*
Vineland-3 ABC: 69
Communication Domain: 77
```

**Not directly in session notes** but shows PHI in different contexts

---

### **Multiple Appointments in Narrative**

#### **Found in Nursing Report:**
```
"2/21/2025 - Station MD appt for rash"
"3/27/2025 - Station MD for facial rash/swollen lips"
"3/28/2025 - Station MD for right eye, red with drainage"
"4/27/2025 - WellNow Urgent Care for ear pain"
```

#### **Pattern:** Multiple embedded dates with brief descriptions

#### **For Generator:**
```python
# Reference past appointments occasionally
if random.random() < 0.1:
    past_date = session_date - timedelta(days=random.randint(7, 60))
    appt_ref = f"Following up on {format_date(past_date)} medical appointment"
```

---

### **Time-of-Day Mentions**

#### **Found in Documents:**
```
"at 8pm" - Medication timing
"11:34:11 PM" - Electronic signature timestamp
```

#### **For Generator:**
```python
# Add time-of-day to events
event_time = f"{random.randint(8,16)}:{random.choice(['00','15','30','45'])} {'AM' if random.randint(8,16) < 12 else 'PM'}"
event = f"At {event_time}, {client_name} demonstrated..."
```

---

## 8️⃣ BEHAVIORAL INTERVENTION TERMINOLOGY (UCP-Specific)

### **Interventions**

#### **Found in Documents:**
```
"SCIP-R Restrictive Physical Interventions"
"three-person supine"
"Blocking Pads"
"Delayed locks"
"Bedroom window alarms"
```

#### **Already in your generator** - Good coverage

---

### **Goal Terminology**

#### **Found in CFA:**
```
"STO1 attained on 2/28/25"
"STO2 extended to be reviewed on 8/31/25"
"LTO Goals"
```

#### **For Generator:** Reference goals in session notes

```python
if scenario == "positive":
    goal_ref = f"{client_name} made progress toward STO1 completion"
```

---

## 9️⃣ SUMMARY: KEY ENHANCEMENTS NEEDED

### **Critical Additions:**

1. **Name Format Variations** (4 formats: First Last, Last First, Last First MI, First MI Last)
2. **Parent/Guardian Names** (20% of notes)
3. **Date Format Variations** (5 different formats)
4. **Staff Credentials** (Mix of degrees, certifications, job titles)
5. **Provider Name Mentions** (Dr. [Last], [First Last], Credential)
6. **Full Addresses** (10% of notes - organizational context)
7. **Phone Numbers** (10% of notes)
8. **License Numbers** (15% of notes in signatures)
9. **Multiple Dates in Narrative** (appointment references)
10. **Time-of-Day Specifications** (event timing)

### **Moderate Priority:**

11. **Middle Initials** (30% of names)
12. **Medication References** (20% of challenging scenarios)
13. **Appointment Follow-up Dates** (15% of notes)
14. **Electronic Signature Blocks** (25% of notes)

### **Lower Priority (Not in Session Notes Typically):**

15. Test scores (different document type)
16. Vital signs (nursing-specific)
17. Immunization records (nursing-specific)

---

## 🎯 EXPECTED IMPACT ON DETECTION

### **Current Issues (68.3% Recall):**

**False Negatives Likely From:**
- Name format variations not in training data ("Taylor, Alex M." missed)
- Non-standard date formats ("8/7/25" vs "08/07/2025")
- Parent names not recognized as PHI
- Provider names in medical context
- Embedded phone numbers and addresses

### **After Enhancement (Estimated 75-80% Recall):**

**Improvements:**
- ✅ Detects "Last, First MI" name format
- ✅ Recognizes parent/guardian names
- ✅ Catches diverse date formats
- ✅ Identifies provider names with credentials
- ✅ Detects full addresses and phone numbers
- ✅ Recognizes license numbers

---

## 📝 IMPLEMENTATION CHECKLIST

### **New Identifier Files to Create:**

- [ ] `middle_initials.txt` (26 letters A-Z)
- [ ] `parent_first_names.txt` (50+ common parent names)
- [ ] `phone_numbers.txt` (100 random phone numbers)
- [ ] `credentials.txt` (15+ professional credentials)
- [ ] `provider_last_names.txt` (50+ provider surnames)

### **Generator Script Modifications:**

- [ ] Add name format variation logic
- [ ] Add parent name generation (20% probability)
- [ ] Add date format variation logic
- [ ] Add staff credential randomization
- [ ] Add full address insertion (10% probability)
- [ ] Add phone number insertion (10% probability)
- [ ] Add license number to signatures (15% probability)
- [ ] Add time-of-day to events
- [ ] Add appointment reference logic
- [ ] Add electronic signature blocks (25% probability)

### **Testing:**

- [ ] Generate 10 test notes with new variations
- [ ] Manually verify PHI diversity
- [ ] Check readability and clinical authenticity
- [ ] Run Presidio detection on test set
- [ ] Compare to original 150 notes

---

## 💾 FILES EXTRACTED FROM:

1. ✅ Annual_OT_2025_review_example.docx
2. ✅ CFA_report_2025_example.docx
3. ✅ CogDev_2025_example.pdf
4. ✅ ICF-TEC-BSP-2025-Taylor_Morgan.docx (already had)
5. ✅ Nursing_report_for_CFA_example.pdf
6. ✅ Addendum_2025_example.pdf

---

**END OF PHI PATTERN EXTRACTION**

**Next Steps:**
1. Create new identifier files
2. Modify synthetic note generator script
3. Generate 150 enhanced notes
4. Re-run evaluation
5. Compare results
