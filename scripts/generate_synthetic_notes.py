#!/usr/bin/env python3
"""
Synthetic ABA Session Note Generator
Generates realistic UCP-style session notes for PHI detection testing

Author: Sakib (Nazmus Sakib)
Project: UCP Data Sanitization Research
Date: March 2026
"""

import csv
import random
import json
from datetime import datetime, timedelta
from pathlib import Path


class SyntheticNoteGenerator:
    """Generate realistic UCP-style ABA session notes"""
    
    def __init__(self, data_dir='data/identifiers'):
        """Initialize generator with identifier data"""
        self.data_dir = Path(data_dir)
        self.load_identifiers()
        
        # UCP-specific data
        self.residential_programs = [
            "88 Geiger ICF", "92 Geiger ICF", "95 Geiger ICF", 
            "96 Geiger ICF", "100 Geiger ICF"
        ]
        
        self.day_programs = [
            "Chadwicks TEC", "Liverpool TEC", "Cicero TEC",
            "Baldwinsville TEC", "Syracuse TEC"
        ]
        
        self.locations = [
            "Residential Setting", "Day Program", "Community Setting",
            "School-based Setting"
        ]
        
        self.staff_titles = [
            ("Behavior Specialist II", "M.A."),
            ("Behavior Specialist", "M.Ed."),
            ("BCBA", "BCBA, LBA"),
            ("Sr. BCBA", "PhD, BCBA"),
            ("RBT", ""),
            ("Direct Support Professional", ""),
            ("DSP", "")
        ]
        
        # Scenario types
        self.scenarios = ['positive', 'routine', 'challenging', 'crisis']
        self.scenario_weights = [0.35, 0.40, 0.20, 0.05]  # Most sessions are positive/routine
        
    def load_identifiers(self):
        """Load all identifier files"""
        print("Loading identifiers...")
        
        # Load first names
        with open(self.data_dir / 'first_names.csv', 'r') as f:
            reader = csv.DictReader(f)
            self.first_names = [row['first_name'] for row in reader]
        
        # Load last names
        with open(self.data_dir / 'last_names.csv', 'r') as f:
            reader = csv.DictReader(f)
            self.last_names = [row['last_name'] for row in reader]
        
        # Load addresses
        with open(self.data_dir / 'syracuse_addresses.csv', 'r') as f:
            reader = csv.DictReader(f)
            self.addresses = list(reader)
        
        # Load Medicaid IDs
        with open(self.data_dir / 'medicaid_ids.txt', 'r') as f:
            self.medicaid_ids = [line.strip() for line in f]
        
        print(f"  ✓ Loaded {len(self.first_names)} first names")
        print(f"  ✓ Loaded {len(self.last_names)} last names")
        print(f"  ✓ Loaded {len(self.addresses)} addresses")
        print(f"  ✓ Loaded {len(self.medicaid_ids)} Medicaid IDs")
    
    def generate_dob(self, min_age=3, max_age=18):
        """Generate random date of birth for child"""
        today = datetime.today()
        age_years = random.randint(min_age, max_age)
        age_days = age_years * 365 + random.randint(0, 364)
        dob = today - timedelta(days=age_days)
        return dob.strftime("%m/%d/%Y")
    
    def generate_session_date(self):
        """Generate random session date in 2025"""
        # Generate dates in October-November 2025
        start_date = datetime(2025, 10, 1)
        end_date = datetime(2025, 11, 30)
        time_between_dates = end_date - start_date
        days_between_dates = time_between_dates.days
        random_number_of_days = random.randrange(days_between_dates)
        session_date = start_date + timedelta(days=random_number_of_days)
        return session_date.strftime("%m/%d/%Y")
    
    def generate_session_time(self):
        """Generate random session time"""
        start_hours = [9, 10, 13, 14, 15]  # 9 AM, 10 AM, 1 PM, 2 PM, 3 PM
        start_hour = random.choice(start_hours)
        
        # Duration: 60, 90, or 120 minutes
        duration = random.choice([60, 90, 120])
        
        start_time = f"{start_hour % 12 or 12}:00 {'AM' if start_hour < 12 else 'PM'}"
        
        end_hour = start_hour + (duration // 60)
        end_min = duration % 60
        end_time = f"{end_hour % 12 or 12}:{end_min:02d} {'AM' if end_hour < 12 else 'PM'}"
        
        return start_time, end_time, duration
    
    def generate_staff_name(self):
        """Generate realistic staff name"""
        staff_first = random.choice(self.first_names)
        staff_last = random.choice(self.last_names)
        title, credentials = random.choice(self.staff_titles)
        return staff_first, staff_last, title, credentials
    
    def generate_client(self):
        """Generate complete client profile"""
        first_name = random.choice(self.first_names)
        last_name = random.choice(self.last_names)
        dob = self.generate_dob()
        medicaid_id = random.choice(self.medicaid_ids)
        residential_program = random.choice(self.residential_programs)
        day_program = random.choice(self.day_programs)
        
        return {
            'first_name': first_name,
            'last_name': last_name,
            'full_name': f"{first_name} {last_name}",
            'dob': dob,
            'medicaid_id': medicaid_id,
            'residential_program': residential_program,
            'day_program': day_program
        }
    
    def generate_positive_session(self, client, session_info, staff_info):
        """Generate a positive progress session note"""
        
        note = f"""# UCP SESSION NOTE - POSITIVE PROGRESS

## HEADER SECTION

**Name:** {client['full_name']}
**Date of Birth:** {client['dob']}
**Residential Program:** {client['residential_program']}
**Day Program:** {client['day_program']}

**Session Date:** {session_info['date']}
**Session Time:** {session_info['start_time']} - {session_info['end_time']}
**Session Duration:** {session_info['duration']} minutes
**Service Location:** {session_info['location']}

**Staff Present:** {staff_info['full_name']}, {staff_info['title']}
**Medicaid ID:** {client['medicaid_id']}

---

## SESSION SUMMARY

{client['first_name']} participated in scheduled activities including functional communication training and social skills practice. Staff implemented individualized universal protocol with access to preferred items such as staff attention, {random.choice(['art supplies', 'music', 'outdoor time', 'tablet videos', 'basketball'])} and peer interactions. {client['first_name']} demonstrated good cooperation throughout the session with minimal prompting required.

The session proceeded smoothly with {client['first_name']} engaging positively in all planned activities. {random.choice(['He', 'She'])} showed improvement in target behaviors and maintained appropriate engagement throughout. Staff provided continuous reinforcement for appropriate behaviors.

---

## BEHAVIORAL TARGETS ADDRESSED

### Target 1: Functional Communication - Requesting Preferred Items
- **Baseline:** {random.randint(3, 5)} appropriate requests per session
- **Goal:** {random.randint(7, 10)} appropriate requests per session by 12/31/2025
- **Today's Performance:** {random.randint(7, 12)} appropriate requests
- **Progress Notes:** {client['first_name']} exceeded baseline with {random.randint(7, 12)} appropriate requests today. Required minimal prompting ({random.randint(1, 3)} verbal prompts). Demonstrated good use of functional communication skills.

### Target 2: {random.choice(['Peer Social Interactions', 'Following Directions', 'Task Completion'])}
- **Baseline:** {random.randint(2, 4)}/session
- **Goal:** {random.randint(5, 8)}/session by 12/31/2025
- **Today's Performance:** {random.randint(5, 9)} instances
- **Progress Notes:** Excellent progress on this target. {client['first_name']} demonstrated increased independence and skill development.

---

## CHALLENGING BEHAVIORS

**No challenging behaviors observed during today's session.**

{client['first_name']} maintained appropriate behaviors throughout. Staff reinforced all positive behaviors continuously.

---

## DATA COLLECTION

| Behavior/Target | Baseline | Today's Data | Progress |
|----------------|----------|--------------|----------|
| Functional Communication | {random.randint(3, 5)}/session | {random.randint(7, 12)} instances | ↑ Improving |
| Target 2 | {random.randint(2, 4)}/session | {random.randint(5, 9)} instances | ↑ Improving |

---

## PROGRESS OBSERVATIONS

**Areas of Progress:**
- {client['first_name']} is making excellent progress on functional communication
- Demonstrated increased independence in target skills
- Responded positively to reinforcement throughout session

**Comparison to Previous Session:**
Compared to previous session, {client['first_name']} showed continued improvement across all targets.

---

## STAFF SIGNATURE

**Completed By:** {staff_info['full_name']}, {staff_info['credentials']}
**Title:** {staff_info['title']}
**Date:** {session_info['date']}

---

END OF SESSION NOTE
"""
        return note
    
    def generate_routine_session(self, client, session_info, staff_info):
        """Generate a routine session note"""
        
        note = f"""# UCP SESSION NOTE - ROUTINE SESSION

## HEADER SECTION

**Name:** {client['full_name']}
**Date of Birth:** {client['dob']}
**Residential Program:** {client['residential_program']}
**Day Program:** {client['day_program']}

**Session Date:** {session_info['date']}
**Session Time:** {session_info['start_time']} - {session_info['end_time']}
**Session Duration:** {session_info['duration']} minutes
**Service Location:** {session_info['location']}

**Staff Present:** {staff_info['full_name']}, {staff_info['title']}
**Medicaid ID:** {client['medicaid_id']}

---

## SESSION SUMMARY

{client['first_name']} participated in routine programming activities. Staff implemented individualized universal protocol including access to preferred activities and staff attention. Session proceeded as planned with {client['first_name']} engaging appropriately in scheduled tasks.

---

## BEHAVIORAL TARGETS ADDRESSED

### Target 1: {random.choice(['Communication Skills', 'Social Interaction', 'Task Compliance'])}
- **Today's Performance:** {random.randint(3, 6)} instances
- **Progress Notes:** {client['first_name']} maintained baseline performance on this target.

---

## CHALLENGING BEHAVIORS

**Behavior: {random.choice(['Verbal Aggression', 'Refusing Tasks', 'Minor Non-Compliance'])}**
- **Frequency:** {random.randint(1, 2)} instances
- **Duration:** Approximately {random.randint(1, 3)} minutes
- **Intensity:** Low
- **Staff Response:** SCIP-R verbal calming techniques, active listening
- **Effectiveness:** {client['first_name']} responded appropriately to interventions

---

## DATA COLLECTION

| Behavior/Target | Baseline | Today's Data | Progress |
|----------------|----------|--------------|----------|
| Target 1 | {random.randint(3, 5)}/session | {random.randint(3, 6)} instances | → Stable |
| Challenging Behavior | {random.randint(1, 3)}/week | {random.randint(1, 2)} instances | → Stable |

---

## STAFF SIGNATURE

**Completed By:** {staff_info['full_name']}, {staff_info['credentials']}
**Title:** {staff_info['title']}
**Date:** {session_info['date']}

---

END OF SESSION NOTE
"""
        return note
    
    def generate_challenging_session(self, client, session_info, staff_info):
        """Generate a session with challenging behaviors"""
        
        behavior = random.choice(['Verbal Aggression', 'Physical Aggression', 'Refusing Tasks'])
        
        note = f"""# UCP SESSION NOTE - CHALLENGING BEHAVIORS

## HEADER SECTION

**Name:** {client['full_name']}
**Date of Birth:** {client['dob']}
**Residential Program:** {client['residential_program']}
**Day Program:** {client['day_program']}

**Session Date:** {session_info['date']}
**Session Time:** {session_info['start_time']} - {session_info['end_time']}
**Session Duration:** {session_info['duration']} minutes
**Service Location:** {session_info['location']}

**Staff Present:** {staff_info['full_name']}, {staff_info['title']}
**Medicaid ID:** {client['medicaid_id']}

---

## SESSION SUMMARY

{client['first_name']} participated in scheduled activities. Multiple instances of challenging behaviors occurred during the session. Staff implemented SCIP-R techniques and BSP protocols. {client['first_name']} was able to calm with staff support and completed the session appropriately.

---

## CHALLENGING BEHAVIORS

### Behavior: {behavior}

**Frequency:** {random.randint(3, 6)} instances
**Duration:** Total approximately {random.randint(8, 15)} minutes
**Intensity:** {random.choice(['Low-to-Moderate', 'Moderate', 'Moderate-to-High'])}

**Setting Events/Antecedents:**
- {random.choice(['Being told no', 'Transition from preferred to non-preferred activity', 'Delayed gratification', 'Peer antagonization'])}

**Staff Response:**
- SCIP-R verbal calming techniques
- Active listening and empathy statements
- {random.choice(['Provided choices', 'Removed from situation', 'Second staff called for support'])}

**Restrictive Interventions Used:** {random.choice(['None', 'Blocking pads (2 instances, 6 minutes total)'])}

---

## POST-INTERVENTION PROCEDURES

**Body Check Completed:** Yes - No marks or injuries noted
**Clinician Contacted:** {random.choice(['Yes - Behavior Specialist notified', 'Not required'])}

---

## DATA COLLECTION

| Behavior/Target | Baseline | Today's Data | Progress |
|----------------|----------|--------------|----------|
| {behavior} | {random.randint(2, 4)}/week | {random.randint(3, 6)} instances | ↑ Elevated |

---

## STAFF SIGNATURE

**Completed By:** {staff_info['full_name']}, {staff_info['credentials']}
**Title:** {staff_info['title']}
**Date:** {session_info['date']}

---

END OF SESSION NOTE
"""
        return note
    
    def generate_crisis_session(self, client, session_info, staff_info):
        """Generate a crisis session requiring restrictive intervention"""
        
        # Generate second staff for support
        staff2_first, staff2_last, staff2_title, _ = self.generate_staff_name()
        
        note = f"""# UCP SESSION NOTE - RESTRICTIVE INTERVENTION REQUIRED

## HEADER SECTION

**Name:** {client['full_name']}
**Date of Birth:** {client['dob']}
**Residential Program:** {client['residential_program']}
**Day Program:** {client['day_program']}

**Session Date:** {session_info['date']}
**Session Time:** {session_info['start_time']} - {session_info['end_time']}
**Session Duration:** {session_info['duration']} minutes
**Service Location:** {session_info['location']}

**Staff Present:** {staff_info['full_name']}, {staff_info['title']} (Primary); {staff2_first} {staff2_last}, {staff2_title} (Support)
**Medicaid ID:** {client['medicaid_id']}

---

## SESSION SUMMARY

{client['first_name']} engaged in severe challenging behavior requiring SCIP-R restrictive physical intervention. Incident occurred at approximately {random.choice(['9:15 AM', '10:30 AM', '2:15 PM', '3:25 PM'])}. All BSP protocols followed. Post-intervention procedures completed per protocol.

---

## CHALLENGING BEHAVIORS

### Behavior: Physical Aggression

**Frequency:** 1 instance requiring restraint
**Duration:** Approximately {random.randint(4, 8)} minutes (including restraint time)
**Intensity:** High

**SCIP-R Restrictive Physical Intervention:**
- **Type:** Two-person supine restraint
- **Duration:** {random.randint(3, 6)} minutes
- **Staff Involved:** {staff_info['full_name']} and {staff2_first} {staff2_last}
- **Reason:** Immediate health and safety risk

---

## POST-INTERVENTION PROCEDURES COMPLETED

**Body Check:**
- Conducted By: {random.choice(['Maria Santos, LPN', 'Lisa Chen, RN', 'Robert Johnson, RN'])}
- Time: Within 3 minutes of restraint conclusion
- Findings: No marks, bruises, or injuries noted

**Clinician Contact:**
- Clinician: {random.choice(['Casey Lane, M.A., Behavior Specialist II', 'Sarah Mitchell, M.A., Behavior Specialist II'])}
- Reviewed incident details and confirmed appropriate intervention per BSP

**Program Administrator Contact:**
- Administrator: {random.choice(['Robert Chen, Program Manager', 'Jennifer Williams, Program Director'])}
- All post-intervention procedures completed correctly

**Justice Center Notification:** No - Restraint per approved BSP

---

## RIGHTS RESTRICTIONS UTILIZED

**SCIP-R Restrictive Physical Interventions:**
- Duration: {random.randint(3, 6)} minutes
- Justification: Immediate health and safety risk per BSP

---

## STAFF SIGNATURE

**Completed By:** {staff_info['full_name']}, {staff_info['credentials']}
**Title:** {staff_info['title']}
**Date:** {session_info['date']}

**Reviewed By:** {random.choice(['Casey Lane, M.A., Behavior Specialist II', 'Sarah Mitchell, M.A., Behavior Specialist II'])}

---

END OF SESSION NOTE
"""
        return note
    
    def generate_note(self, scenario_type=None):
        """Generate a single synthetic note"""
        
        # Select scenario type
        if scenario_type is None:
            scenario_type = random.choices(self.scenarios, weights=self.scenario_weights)[0]
        
        # Generate client and session info
        client = self.generate_client()
        
        start_time, end_time, duration = self.generate_session_time()
        session_date = self.generate_session_date()
        
        session_info = {
            'date': session_date,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'location': random.choice(self.locations)
        }
        
        staff_first, staff_last, staff_title, staff_cred = self.generate_staff_name()
        staff_info = {
            'full_name': f"{staff_first} {staff_last}",
            'title': staff_title,
            'credentials': staff_cred
        }
        
        # Generate note based on scenario
        if scenario_type == 'positive':
            return self.generate_positive_session(client, session_info, staff_info)
        elif scenario_type == 'routine':
            return self.generate_routine_session(client, session_info, staff_info)
        elif scenario_type == 'challenging':
            return self.generate_challenging_session(client, session_info, staff_info)
        elif scenario_type == 'crisis':
            return self.generate_crisis_session(client, session_info, staff_info)
    
    def generate_batch(self, n=150, output_dir='data/synthetic/raw'):
        """Generate batch of synthetic notes"""
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"\n{'='*80}")
        print(f"GENERATING {n} SYNTHETIC ABA SESSION NOTES")
        print(f"{'='*80}\n")
        
        scenario_counts = {s: 0 for s in self.scenarios}
        
        for i in range(1, n + 1):
            scenario = random.choices(self.scenarios, weights=self.scenario_weights)[0]
            scenario_counts[scenario] += 1
            
            note = self.generate_note(scenario)
            
            filename = output_path / f"note_{i:04d}_{scenario}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(note)
            
            if i % 10 == 0:
                print(f"  Generated {i}/{n} notes...")
        
        print(f"\n{'='*80}")
        print(f"✅ GENERATION COMPLETE!")
        print(f"{'='*80}")
        print(f"\nScenario Distribution:")
        for scenario, count in scenario_counts.items():
            percentage = (count / n) * 100
            print(f"  {scenario.capitalize():15} {count:3d} notes ({percentage:5.1f}%)")
        
        print(f"\n📁 Notes saved to: {output_path}")
        print(f"📊 Total files generated: {n}")
        print(f"\n{'='*80}\n")
        
        return scenario_counts


def main():
    """Main execution"""
    print("\n" + "="*80)
    print("UCP SYNTHETIC ABA SESSION NOTE GENERATOR")
    print("="*80)
    print("\nInitializing generator...")
    
    generator = SyntheticNoteGenerator()
    
    print("\nGenerator ready!")
    print(f"  Scenarios: {', '.join(generator.scenarios)}")
    print(f"  Weights: {generator.scenario_weights}")
    
    # Generate notes
    scenario_counts = generator.generate_batch(n=150)
    
    print("✅ Synthetic note generation complete!")
    print("\nNext steps:")
    print("  1. Review generated notes in data/synthetic/raw/")
    print("  2. Test PHI recognizers on sample notes")
    print("  3. Generate ground truth annotations")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
