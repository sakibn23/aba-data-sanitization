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
        self.scenarios = [
            'exceptional_progress',      # 10%
            'skill_acquisition',         # 15%
            'positive_social',           # 10%
            'standard_session',          # 20%
            'maintenance',               # 10%
            'mild_challenging',          # 10%
            'moderate_challenging',      # 10%
            'environmental_triggers',    # 5%
            'medical_appointment',       # 5%
            'medication_monitoring',     # 5%
            'crisis_intervention',       # 3%
            'post_crisis_recovery'       # 2%
        ]
        
        # Weights must sum to 1.0 for 1000 notes
        self.scenario_weights = [
            0.10,  # exceptional_progress (100 notes)
            0.15,  # skill_acquisition (150 notes)
            0.10,  # positive_social (100 notes)
            0.20,  # standard_session (200 notes)
            0.10,  # maintenance (100 notes)
            0.10,  # mild_challenging (100 notes)
            0.10,  # moderate_challenging (100 notes)
            0.05,  # environmental_triggers (50 notes)
            0.05,  # medical_appointment (50 notes)
            0.05,  # medication_monitoring (50 notes)
            0.03,  # crisis_intervention (30 notes)
            0.02   # post_crisis_recovery (20 notes)
        ]
        
        
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
        
        # NEW: Load 5 additional identifier files
        with open(self.data_dir / 'middle_initials.txt', 'r') as f:
            self.middle_initials = [line.strip() for line in f]
        
        with open(self.data_dir / 'parent_first_names.txt', 'r') as f:
            self.parent_first_names = [line.strip() for line in f]
        
        with open(self.data_dir / 'phone_numbers.txt', 'r') as f:
            self.phone_numbers = [line.strip() for line in f]
        
        with open(self.data_dir / 'credentials.txt', 'r') as f:
            self.credentials = [line.strip() for line in f]
        
        with open(self.data_dir / 'provider_last_names.txt', 'r') as f:
            self.provider_last_names = [line.strip() for line in f]
        
        # Print confirmation
        print(f"  ✓ Loaded {len(self.first_names)} first names")
        print(f"  ✓ Loaded {len(self.last_names)} last names")
        print(f"  ✓ Loaded {len(self.addresses)} addresses")
        print(f"  ✓ Loaded {len(self.medicaid_ids)} Medicaid IDs")
        print(f"  ✓ Loaded {len(self.middle_initials)} middle initials")
        print(f"  ✓ Loaded {len(self.parent_first_names)} parent names")
        print(f"  ✓ Loaded {len(self.phone_numbers)} phone numbers")
        print(f"  ✓ Loaded {len(self.credentials)} credentials")
        print(f"  ✓ Loaded {len(self.provider_last_names)} provider names")
    def generate_name_variations(self, first_name, last_name):
        """Generate name in 4 different formats"""
        # Get middle initial (40% of the time)
        use_middle = random.random() < 0.4
        middle_initial = random.choice(self.middle_initials) if use_middle else None
        
        # Choose name format (4 variations)
        format_choice = random.choice([1, 2, 3, 4])
        
        if format_choice == 1:
            # Format 1: First Last (e.g., "Emma Rodriguez")
            return f"{first_name} {last_name}"
        
        elif format_choice == 2:
            # Format 2: Last, First (e.g., "Rodriguez, Emma")
            return f"{last_name}, {first_name}"
        
        elif format_choice == 3:
            # Format 3: Last, First MI (e.g., "Rodriguez, Emma M.")
            if middle_initial:
                return f"{last_name}, {first_name} {middle_initial}."
            else:
                return f"{last_name}, {first_name}"
        
        else:  # format_choice == 4
            # Format 4: First MI Last (e.g., "Emma M. Rodriguez")
            if middle_initial:
                return f"{first_name} {middle_initial}. {last_name}"
            else:
                return f"{first_name} {last_name}"
    def generate_date_variations(self, date_obj):
        """Generate date in 5 different formats"""
        # Choose date format (5 variations)
        format_choice = random.choice([1, 2, 3, 4, 5])
        
        month = date_obj.month
        day = date_obj.day
        year = date_obj.year
        
        if format_choice == 1:
            # Format 1: M/D/YYYY (e.g., "3/5/2025")
            return f"{month}/{day}/{year}"
        
        elif format_choice == 2:
            # Format 2: M/DD/YYYY (e.g., "3/05/2025")
            return f"{month}/{day:02d}/{year}"
        
        elif format_choice == 3:
            # Format 3: MM/DD/YYYY (e.g., "03/05/2025")
            return f"{month:02d}/{day:02d}/{year}"
        
        elif format_choice == 4:
            # Format 4: M/D/YY (e.g., "3/5/25")
            return f"{month}/{day}/{year % 100}"
        
        else:  # format_choice == 5
            # Format 5: Month D, YYYY (e.g., "March 5, 2025")
            month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                          'July', 'August', 'September', 'October', 'November', 'December']
            return f"{month_names[month-1]} {day}, {year}"    
    
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
        """Generate realistic staff name with varied credentials"""
        staff_first = random.choice(self.first_names)
        staff_last = random.choice(self.last_names)
        
        # Use credentials from file (80% of time) or staff_titles (20% of time)
        if random.random() < 0.8:
            # Use credential from loaded file
            credential = random.choice(self.credentials)
            # Split into title and credential if it contains both
            if ',' in credential:
                title, cred = credential.split(',', 1)
                return staff_first, staff_last, title.strip(), cred.strip()
            else:
                # Just a credential/title
                return staff_first, staff_last, credential, ""
        else:
            # Use traditional staff_titles
            title, credentials = random.choice(self.staff_titles)
            return staff_first, staff_last, title, credentials
    def generate_provider_name(self):
        """Generate provider name (doctors, nurses, therapists)"""
        provider_last = random.choice(self.provider_last_names)
        
        # 70% chance of being "Dr. [Last]", 30% chance of being full name with credential
        if random.random() < 0.7:
            return f"Dr. {provider_last}"
        else:
            provider_first = random.choice(self.first_names)
            credential = random.choice(self.credentials)
            return f"{provider_first} {provider_last}, {credential}"
    
    def generate_dob_object(self, min_age=3, max_age=18):
        """Generate random date of birth as datetime object"""
        today = datetime.today()
        age_years = random.randint(min_age, max_age)
        age_days = age_years * 365 + random.randint(0, 364)
        dob = today - timedelta(days=age_days)
        return dob
    def generate_client(self):
        """Generate complete client profile with enhanced PHI"""
        first_name = random.choice(self.first_names)
        last_name = random.choice(self.last_names)
        # Use name variation function
        full_name = self.generate_name_variations(first_name, last_name)
        
        # Generate DOB as datetime object first
        dob_obj = self.generate_dob_object()
        dob = self.generate_date_variations(dob_obj)
        
        medicaid_id = random.choice(self.medicaid_ids)
        residential_program = random.choice(self.residential_programs)
        day_program = random.choice(self.day_programs)
        
        # Generate parent names (40% chance of having both parents)
        parent1_first = random.choice(self.parent_first_names)
        has_two_parents = random.random() < 0.4
        parent2_first = random.choice(self.parent_first_names) if has_two_parents else None
        
        # Generate phone numbers
        phone_number = random.choice(self.phone_numbers)
        parent2_phone = random.choice(self.phone_numbers) if has_two_parents else None
        
        # Generate address (30% of notes will have home address)
        has_address = random.random() < 0.3
        if has_address and len(self.addresses) > 0:
            address_data = random.choice(self.addresses)
            # Handle CSV DictReader format
            try:
                home_address = f"{address_data['street']}, {address_data['city']}, {address_data['state']} {address_data['zip']}"
            except (KeyError, TypeError):
                # Fallback if address format is different
                home_address = None
        else:
            home_address = None
        
        return {
            'first_name': first_name,
            'last_name': last_name,
            'full_name': full_name,
            'dob': dob,
            'medicaid_id': medicaid_id,
            'residential_program': residential_program,
            'day_program': day_program,
            'parent1_first': parent1_first,
            'parent2_first': parent2_first,
            'phone_number': phone_number,
            'parent2_phone': parent2_phone,
            'home_address': home_address
        }
        
    def generate_exceptional_progress(self, client, session_info, staff_info):
        """Generate exceptional progress scenario"""
        provider_name = self.generate_provider_name()
        goal_date = self.generate_date_variations(datetime.today() + timedelta(days=random.randint(30, 90)))
        
        note = f"""# UCP SESSION NOTE - EXCEPTIONAL PROGRESS

**Client:** {client['full_name']}
**Date of Birth:** {client['dob']}
**Session Date:** {session_info['date']}
**Session Time:** {session_info['start_time']} - {session_info['end_time']}
**Location:** {client['residential_program']}
**Staff:** {staff_info['full_name']}, {staff_info['credentials']}
**Medicaid ID:** {client['medicaid_id']}

---

## EXCEPTIONAL PROGRESS SESSION

{client['first_name']} demonstrated outstanding progress during today's session at {client['residential_program']}. 
{client['first_name']} achieved functional communication goal three weeks ahead of schedule, marking significant 
advancement in expressive language skills.

Throughout the session from {session_info['start_time']} to {session_info['end_time']}, {client['first_name']} 
consistently exhibited appropriate verbal requesting, independent task completion, and positive peer engagement. 
Completed all scheduled activities independently with 95% accuracy.

**PARENT NOTIFICATION:**
{client['parent1_first']} {client['last_name']} contacted at {client['phone_number']} expressed pride in 
{client['first_name']}'s achievements.

**STAFF OBSERVATIONS:**
- Mastered three-step sequencing task with minimal prompting
- Generalized skills across multiple settings
- Positive peer interactions during group activity

**RECOMMENDATIONS:**
- Continue current intervention strategies
- Advance to next skill level in functional communication program
- Schedule review with {provider_name} on {goal_date}

**Documentation:** {staff_info['full_name']}, {staff_info['credentials']}
**Date:** {session_info['date']}

---
END OF SESSION NOTE
"""
        return note
    
    def generate_skill_acquisition(self, client, session_info, staff_info):
        """Generate skill acquisition scenario"""
        vocational_staff = self.generate_staff_name()
        phone = client['phone_number']
        
        note = f"""# UCP SESSION NOTE - SKILL ACQUISITION

**Client:** {client['full_name']}
**Date of Birth:** {client['dob']}
**Session Date:** {session_info['date']}
**Program:** {client['day_program']}
**Time:** {session_info['start_time']} - {session_info['end_time']}
**Behavior Specialist:** {staff_info['full_name']}, {staff_info['credentials']}

---

## SKILL ACQUISITION SESSION

**Target Skill:** Multi-step vocational task completion
**Teaching Method:** Discrete trial training with naturalistic teaching

**SESSION SUMMARY:**
{client['first_name']} participated in 45 discrete trial training sessions focusing on lunch service 
preparation skills at {client['day_program']}. Session began at {session_info['start_time']} with 
hand washing and apron donning.

**TRIAL DATA:**
- Trial block 1: {random.randint(70, 80)}% accuracy across 15 trials
- Trial block 2: {random.randint(80, 90)}% accuracy across 15 trials  
- Trial block 3: {random.randint(85, 95)}% accuracy across 15 trials
- Overall session accuracy: {random.randint(78, 90)}%

**PROMPTING HIERARCHY:**
Initial trials required full physical prompting, progressing to verbal prompting only by session end. 
{client['first_name']} demonstrated improvement in response latency from 8.5 seconds to 3.2 seconds.

**VOCATIONAL INTEGRATION:**
{client['first_name']} practiced food service skills during lunch preparation. Staff {vocational_staff[0]} {vocational_staff[1]}, 
{vocational_staff[2]} supervised and reported successful completion of assigned tasks with minimal support.

**PARENT COLLABORATION:**
Contacted {client['parent1_first']} {client['last_name']} at {phone} to discuss home practice strategies. 
Parent reported {client['first_name']} has been practicing sorting tasks at home with good success.

**NEXT SESSION GOALS:**
- Increase trial complexity for vocational skills
- Reduce prompting to gestural level only
- Incorporate generalization setting

**Therapist:** {staff_info['full_name']}, {staff_info['credentials']}
**Date signed:** {session_info['date']}

---
END OF SESSION NOTE
"""
        return note
    
    def generate_positive_social(self, client, session_info, staff_info):
        """Generate positive social interaction scenario"""
        co_staff = self.generate_staff_name()
        slp_name = self.generate_provider_name()
        peer1 = random.choice(self.first_names)
        peer2 = random.choice(self.first_names)
        
        note = f"""# UCP SESSION NOTE - POSITIVE SOCIAL INTERACTION

**Client:** {client['full_name']}
**Date of Service:** {session_info['date']}
**Program Location:** {client['day_program']}
**Lead Therapist:** {staff_info['full_name']}, {staff_info['credentials']}
**Co-Facilitator:** {co_staff[0]} {co_staff[1]}, {co_staff[2]}

---

## POSITIVE SOCIAL ENGAGEMENT SESSION

{client['first_name']} demonstrated exceptional social skills during structured group activity at 
{client['day_program']} from {session_info['start_time']} to {session_info['end_time']}.

**PEER INTERACTIONS:**
{client['first_name']} engaged appropriately with peers {peer1} and {peer2} during board game activity. 
Initiated {random.randint(5, 9)} social interactions, including:
- Sharing game pieces with {peer1}
- Inviting {peer2} to join activity
- Requesting turn-taking using functional communication strategies

**COMMUNICATION SUCCESSES:**
Following recommendations from {slp_name}, {client['first_name']} utilized total communication approach 
effectively. Verbally expressed wants/needs {random.randint(10, 15)} times throughout session.

**STAFF INTERACTIONS:**
Responded positively to prompts from {staff_info['full_name']} and {co_staff[0]} {co_staff[1]}. 
Built rapport through shared interest in activities. Accepted redirection appropriately when needed.

**GROUP ACTIVITY PARTICIPATION:**
Activity: Cooperative board game
Duration: 45 minutes
Peers present: {peer1}, {peer2}
Adult supervision: 1:3 staff-to-client ratio

**PARENT FEEDBACK:**
{client['parent1_first']} {client['last_name']} attended pickup and reported {client['first_name']} has 
been initiating play with siblings at home more frequently. Contact maintained via daily communication log.

**RECOMMENDATIONS:**
- Continue social skills group at {client['day_program']}
- Increase peer interaction opportunities during unstructured time
- Collaborate with {slp_name} for social-emotional assessment

**Documentation:** {staff_info['full_name']}, {staff_info['credentials']}
**Date:** {session_info['date']}

---
END OF SESSION NOTE
"""
        return note
    
    def generate_standard_session(self, client, session_info, staff_info):
        """Generate standard/routine session scenario"""
        medication = random.choice(['Sertraline 50mg', 'Clonidine 0.3mg', 'Risperidone 1mg'])
        prescriber = self.generate_provider_name()
        
        note = f"""# UCP SESSION NOTE - STANDARD SESSION

**Client:** {client['full_name']}
**Date of Birth:** {client['dob']}
**Session Date:** {session_info['date']}
**Location:** {client['residential_program']}
**Staff:** {staff_info['full_name']}, {staff_info['credentials']}
**Medicaid ID:** {client['medicaid_id']}

---

## STANDARD SESSION REPORT

Session conducted at {client['residential_program']} from {session_info['start_time']} to {session_info['end_time']}. 
{client['first_name']} engaged in 5 scheduled activities with mixed performance.

**ACTIVITIES COMPLETED:**
1. Fine motor skills: {random.randint(75, 90)}% independent completion
2. Functional communication practice: {random.randint(65, 85)}% accuracy with verbal prompting
3. Self-care routines: Required moderate physical prompting
4. Academic tasks: {random.randint(55, 75)}% completion rate
5. Leisure skills: High engagement, appropriate duration

Overall completion rate: {random.randint(70, 80)}%

**BEHAVIOR SUPPORT PLAN IMPLEMENTATION:**
Current BSP was followed throughout session. {client['first_name']} responded to {random.randint(2, 4)} 
planned interventions including:
- Visual schedule transitions
- Token economy system (earned {random.randint(15, 22)} tokens toward preferred activity)
- Functional communication training

**CHALLENGES NOTED:**
Brief verbal refusal when transitioning from self-care routine to academic tasks. Redirected using 
first-then board per BSP protocol. No restrictive interventions required.

**PARENT COMMUNICATION:**
{client['parent1_first']} {client['last_name']} contacted at {client['phone_number']} regarding 
upcoming program meeting. Confirmed attendance and requested transportation information.

**MEDICATION OBSERVATION:**
{client['first_name']} takes {medication} daily per prescription from {prescriber}. 
No side effects observed during session.

**FOLLOW-UP:**
Next session scheduled for {self.generate_date_variations(datetime.today() + timedelta(days=2))} at {client['residential_program']}.

**Authored by:** {staff_info['full_name']}, {staff_info['credentials']}
**Date:** {session_info['date']}

---
END OF SESSION NOTE
"""
        return note
    
    def generate_maintenance(self, client, session_info, staff_info):
        """Generate maintenance/generalization scenario"""
        home_staff = self.generate_staff_name()
        ot_name = self.generate_provider_name()
        slp_name = self.generate_provider_name()
        ot_phone = random.choice(self.phone_numbers)
        slp_phone = random.choice(self.phone_numbers)
        home_address = client['home_address'] if client['home_address'] else f"{random.randint(100, 999)} {random.choice(['Oak', 'Main', 'Elm', 'Maple'])} Street, Syracuse, NY 13204"
        
        note = f"""# UCP SESSION NOTE - GENERALIZATION SESSION

**Client:** {client['full_name']}
**Session Date:** {session_info['date']}
**Settings:** {client['residential_program']}, {client['day_program']}, {home_address}
**Lead Staff:** {staff_info['full_name']}, {staff_info['credentials']}
**Home Visit Staff:** {home_staff[0]} {home_staff[1]}, {home_staff[2]}

---

## MAINTENANCE AND GENERALIZATION ASSESSMENT

{client['first_name']} demonstrated skill maintenance across multiple settings during coordinated session on {session_info['date']}.

**SETTING 1:** {client['residential_program']}
Skills assessed: Self-care routines, task completion, social communication
Performance: {random.randint(82, 92)}% independent completion across all tasks
Staff observer: {staff_info['full_name']}, {staff_info['credentials']}

**SETTING 2:** {client['day_program']}
Skills assessed: Vocational tasks, peer interaction, following multi-step directions
Performance: {random.randint(75, 88)}% accuracy with minimal prompting
Transition quality: Smooth transition with visual schedule support

**HOME VISIT:** {home_address}
Parent participants: {client['parent1_first']} {client['last_name']}"""
        
        if client['parent2_first']:
            note += f" and {client['parent2_first']} {client['last_name']}"
        
        note += f"""
Home phone: {client['phone_number']}
Skills assessed: Home routines, family interactions, leisure skills
Performance: {random.randint(70, 85)}% independent completion in home environment

**PARENT REPORT:**
{client['parent1_first']} {client['last_name']} reported {client['first_name']} has been completing 
morning routine independently at home {random.randint(4, 6)} days per week."""
        
        if client['parent2_first']:
            note += f" {client['parent2_first']} {client['last_name']} noted improvement in communication with younger sibling during play activities."
        
        note += f"""

**Parent training provided on:**
- Visual schedule implementation at home
- Positive reinforcement strategies
- Data collection procedures for home implementation

**CONSISTENCY ANALYSIS:**
{client['first_name']} maintained {random.randint(78, 88)}% consistency across settings for target skills. 
Variability noted in task initiation between {client['residential_program']} and home setting.

**PROVIDER COORDINATION:**
Information shared with:
- {ot_name} (Occupational Therapy) - contact: {ot_phone}
- {slp_name} (Speech Therapy) - contact: {slp_phone}

**RECOMMENDATIONS:**
- Continue generalization trials across all settings weekly
- Increase home practice frequency to {random.randint(3, 5)} times per week
- Schedule tri-setting observation on {self.generate_date_variations(datetime.today() + timedelta(days=random.randint(40, 60)))}

**Documentation:** {staff_info['full_name']}, {staff_info['credentials']}
**Date:** {session_info['date']}

---
END OF SESSION NOTE
"""
        return note
    
    def generate_mild_challenging(self, client, session_info, staff_info):
        """Generate mild challenging behavior scenario"""
        behavior = random.choice(['Verbal refusal', 'Minor non-compliance', 'Brief withdrawal'])
        provider = self.generate_provider_name()
        
        note = f"""# UCP SESSION NOTE - MILD CHALLENGING BEHAVIOR

**Client:** {client['full_name']}
**Incident Date:** {session_info['date']}
**Incident Time:** {random.choice(['10:45 AM', '2:15 PM', '11:20 AM'])}
**Location:** {client['residential_program']}
**Staff Present:** {staff_info['full_name']}, {staff_info['credentials']}

---

## MILD CHALLENGING BEHAVIOR - SUCCESSFULLY REDIRECTED

**ANTECEDENT:**
{client['first_name']} was engaged in art activity at {client['residential_program']} when peer 
requested to share art materials.

**BEHAVIOR DESCRIPTION:**
{client['first_name']} exhibited {behavior} characterized by:
- Loud vocal tone stating "No, mine!"
- Crossing arms and turning away
- Refusing to make eye contact with staff
- Duration: {random.randint(2, 5)} minutes
- Intensity: Mild (Level 1 on BSP scale)

**INTERVENTION APPLIED:**
Staff {staff_info['full_name']}, {staff_info['credentials']} implemented:
1. Pause and proximity
2. Visual first-then board presentation
3. Choice offering between sharing materials or selecting different activity

{client['first_name']} responded to choice offering intervention and returned to baseline within 
{random.randint(4, 7)} minutes.

**CONSEQUENCE:**
Brief access to preferred activity delayed by 2 minutes per Behavior Support Plan, followed by 
praise for appropriate choice-making.

**POST-INCIDENT:**
{client['first_name']} participated in cooperative art activity with appropriate sharing behaviors 
observed. No further incidents during remainder of session.

**FUNCTIONAL COMMUNICATION:**
{client['first_name']} was able to verbally request "my turn please" following de-escalation, 
demonstrating understanding of replacement behavior.

**PARENT NOTIFICATION:**
Phone contact with {client['parent1_first']} {client['last_name']} at {client['phone_number']}. 
Parent reported similar sharing difficulties at home with sibling. Discussed consistency in 
intervention approach across settings.

**FOLLOW-UP ACTIONS:**
- Data entered into tracking system by {staff_info['full_name']}
- No modifications to current BSP recommended at this time
- Continue monitoring for pattern development

**Next session:** {self.generate_date_variations(datetime.today() + timedelta(days=2))} at {client['residential_program']}
**Provider check-in:** {provider} on {self.generate_date_variations(datetime.today() + timedelta(days=random.randint(8, 15)))}

**Report filed by:** {staff_info['full_name']}, {staff_info['credentials']}
**Filed:** {session_info['date']}

---
END OF SESSION NOTE
"""
        return note
    
    def generate_moderate_challenging(self, client, session_info, staff_info):
        """Generate moderate challenging behavior scenario"""
        staff2 = self.generate_staff_name()
        nurse = self.generate_provider_name()
        provider = self.generate_provider_name()
        parent2_phone = client['parent2_phone'] if client['parent2_phone'] else client['phone_number']
        
        note = f"""# UCP SESSION NOTE - MODERATE CHALLENGING BEHAVIOR

**UPSTATE CARING PARTNERS**
125 Business Park Drive, Utica, NY 13502
Phone: 315-724-6907

**Client Name:** {client['full_name']}
**Date of Birth:** {client['dob']}
**Incident Date:** {session_info['date']}
**Incident Time:** {random.choice(['2:15 PM', '10:30 AM', '3:45 PM'])}
**Location:** {client['residential_program']}
**Staff Involved:** {staff_info['full_name']}, {staff_info['credentials']}; {staff2[0]} {staff2[1]}, {staff2[2]}

---

## MODERATE CHALLENGING BEHAVIOR - MULTIPLE INTERVENTIONS

**INDIVIDUALS PRESENT:**
Staff: {staff_info['full_name']}, {staff_info['credentials']}; {staff2[0]} {staff2[1]}, {staff2[2]}
Location: Community room, {client['residential_program']}

**INCIDENT TIMELINE:**

{random.choice(['2:10 PM', '10:25 AM', '3:40 PM'])} - ANTECEDENT
{client['first_name']} was participating in group activity when transition announcement was made 
to end preferred activity.

{random.choice(['2:15 PM', '10:30 AM', '3:45 PM'])} - BEHAVIOR ONSET
{client['first_name']} engaged in physical aggression including:
- Pushing peer
- Throwing materials
- Verbal aggression (yelling, protesting)

{random.choice(['2:17 PM', '10:32 AM', '3:47 PM'])} - INITIAL INTERVENTION
{staff_info['full_name']}, {staff_info['credentials']} implemented verbal de-escalation and visual supports.
Limited effectiveness. Behavior escalated to Level 2 (moderate severity).

{random.choice(['2:20 PM', '10:35 AM', '3:50 PM'])} - SECONDARY INTERVENTION
{staff2[0]} {staff2[1]}, {staff2[2]} joined intervention team.
SCIP-R blocking pads utilized per BSP protocol.
{client['first_name']} responded to planned ignoring combined with blocking strategy.

{random.choice(['2:28 PM', '10:43 AM', '3:58 PM'])} - DE-ESCALATION ACHIEVED
{client['first_name']} returned to baseline. Moved to quiet room for recovery.

**INJURIES/DAMAGE:**
Staff: {staff_info['full_name']} sustained minor scratch on left forearm, no medical treatment required
Property: Game materials damaged, approximate cost ${random.randint(25, 60)}
Client: No injuries sustained

**IMMEDIATE PARENT CONTACT:**
{client['parent1_first']} {client['last_name']} contacted at {client['phone_number']}.
Parent acknowledged incident and requested details of antecedent triggers."""

        if client['parent2_first']:
            note += f"""

{client['parent2_first']} {client['last_name']} contacted at {parent2_phone}.
Parent confirmed evening check-in call and discussed home consistency strategies."""

        note += f"""

**MEDICAL CONSULTATION:**
Nurse {nurse} consulted. Visual assessment of minor staff injury completed. 
No client injuries noted. No medical intervention required.

**RESTRICTIVE INTERVENTIONS USED:**
- SCIP-R Blocking Pads: Yes (Duration: {random.randint(6, 10)} minutes)
- Physical Restraint: No
- Seclusion: No
- PRN Medication: Not administered

**FUNCTIONAL BEHAVIOR ASSESSMENT UPDATE:**
Data suggests escape function related to transition from preferred activities. 
Recommend FBA review with {staff_info['full_name']}, {staff_info['credentials']} scheduled for 
{self.generate_date_variations(datetime.today() + timedelta(days=random.randint(8, 14)))}.

**PSYCHIATRIC CONSULTATION:**
{provider} notified via phone message. Appointment maintained for 
{self.generate_date_variations(datetime.today() + timedelta(days=random.randint(15, 25)))}.

**NOTIFICATIONS COMPLETED:**
☑ Parents (contacted)
☑ Program Director (notified)
☑ Nurse (consulted)
☑ Psychiatrist (message left)
☐ OPWDD (Not required - internal incident)

**FOLLOW-UP ACTIONS:**
- Incident review meeting scheduled
- BSP modification considered for transition protocols
- Staff debriefing completed
- Additional transition warnings for next 72 hours

**Report compiled by:** {staff_info['full_name']}, {staff_info['credentials']}
**Report filed:** {session_info['date']}

---
END OF SESSION NOTE
"""
        return note
    
    def generate_environmental_triggers(self, client, session_info, staff_info):
        """Generate environmental triggers scenario"""
        provider = self.generate_provider_name()
        ot_name = self.generate_provider_name()
        ot_phone = random.choice(self.phone_numbers)
        location2 = random.choice([p for p in self.day_programs if p != client['day_program']])
        
        note = f"""# UCP SESSION NOTE - ENVIRONMENTAL TRIGGER ANALYSIS

**Client:** {client['full_name']}
**Session Date:** {session_info['date']}
**Locations Observed:** {client['residential_program']}, {client['day_program']}, {location2}
**Observing Staff:** {staff_info['full_name']}, {staff_info['credentials']}

---

## ENVIRONMENTAL TRIGGER DOCUMENTATION

**TRANSITION 1:** {client['residential_program']} → {client['day_program']}
Time: {random.choice(['9:30 AM', '10:15 AM', '8:45 AM'])}
Trigger: Unexpected staff change (regular driver unavailable)
Client Response: Moderate anxiety, verbal questioning, increased pacing

{client['first_name']} demonstrated heightened anxiety when informed of transition from 
{client['residential_program']} to {client['day_program']} with unfamiliar driver. 
Environmental factors noted:
- Different vehicle than typical transport
- Substitute staff member instead of usual {staff_info['full_name']}, {staff_info['credentials']}

**TRANSITION 2:** {client['day_program']} → {location2}
Time: {random.choice(['11:45 AM', '1:30 PM', '2:15 PM'])}
Trigger: Schedule modification due to building maintenance
Client Response: Mild agitation, requesting return to familiar setting

**SCHEDULE DISRUPTION ANALYSIS:**
Originally scheduled appointment with {provider} at {client['day_program']} on 
{self.generate_date_variations(datetime.today() - timedelta(days=random.randint(3, 8)))} was 
rescheduled to {self.generate_date_variations(datetime.today() + timedelta(days=random.randint(8, 15)))} 
due to provider illness. {client['first_name']} exhibited increased anxiety and repetitive questioning 
about appointment status.

**PARENT CONTACT:**
{client['parent1_first']} {client['last_name']} contacted at {client['phone_number']} to discuss 
schedule sensitivity. Parent reported {client['first_name']} frequently references upcoming appointments 
at home and struggles with last-minute changes.

**SENSORY ENVIRONMENT ASSESSMENT:**
{client['residential_program']}: Familiar lighting, low noise level, preferred seating available
{client['day_program']}: Moderate noise level, fluorescent lighting, multiple peer interactions
{location2}: High activity level, variable noise, open floor plan

Consultation with {ot_name} scheduled for {self.generate_date_variations(datetime.today() + timedelta(days=random.randint(25, 40)))} 
to assess sensory processing needs and environmental accommodation recommendations.

**RECOMMENDATIONS:**
- Increase transition warnings from 5 minutes to 15 minutes advance notice
- Environmental modifications at {client['day_program']}:
  * Provide noise-canceling headphones during high-activity periods
  * Designate quiet space for breaks
- Schedule consistency protocol - avoid changes within 48 hours when possible
- Provider coordination for appointment preparation with visual schedule

**FOLLOW-UP:**
Meeting with {client['parent1_first']} {client['last_name']} scheduled 
{self.generate_date_variations(datetime.today() + timedelta(days=random.randint(10, 18)))} 
to review environmental sensitivities.

Contact {ot_name} at {ot_phone} for sensory consultation.

**Documented by:** {staff_info['full_name']}, {staff_info['credentials']}
**Date:** {session_info['date']}

---
END OF SESSION NOTE
"""
        return note
    
    def generate_medical_appointment(self, client, session_info, staff_info):
        """Generate medical appointment scenario"""
        provider_name = self.generate_provider_name()
        nurse_name = self.generate_provider_name()
        clinic_name = random.choice(['WellNow Urgent Care', 'Community Health Center', 'Syracuse Medical Associates'])
        clinic_address = f"{random.randint(400, 850)} {random.choice(['South Salina', 'James', 'University', 'Erie'])} Street, Syracuse, NY 13202"
        clinic_phone = random.choice(self.phone_numbers)
        pharmacy_phone = random.choice(self.phone_numbers)
        medication = random.choice(['Amoxicillin 500mg', 'Neomycin-Polymyxin ear drops', 'Fluticasone nasal spray'])
        
        note = f"""# UCP SESSION NOTE - MEDICAL APPOINTMENT COORDINATION

**Client:** {client['full_name']}
**Session Date:** {session_info['date']}
**Primary Location:** {client['day_program']}
**Staff:** {staff_info['full_name']}, {staff_info['credentials']}

---

## MODIFIED SESSION - MEDICAL APPOINTMENT

**SESSION MODIFICATION:**
Standard session time modified to accommodate appointment with {provider_name} at {clinic_name}, {clinic_address}.

Modified session: Morning abbreviated session and afternoon return

**MEDICAL APPOINTMENT PREPARATION:**
Departure time: {random.choice(['10:45 AM', '11:15 AM', '1:30 PM'])}
Destination: {clinic_name}, {clinic_address}
Clinic phone: {clinic_phone}
Provider: {provider_name}
Appointment time: {random.choice(['11:15 AM', '11:45 AM', '2:00 PM'])}

Transportation: UCP van
Accompanied by: {staff_info['full_name']}, {staff_info['credentials']}

**PARENT COORDINATION:**
{client['parent1_first']} {client['last_name']} met at clinic.
Contact number: {client['phone_number']}

**MEDICAL CONCERN ADDRESSED:**
Chief complaint: {random.choice(['Bilateral ear pain', 'Upper respiratory symptoms', 'Seasonal allergies', 'Skin rash'])}
Onset: {self.generate_date_variations(datetime.today() - timedelta(days=random.randint(2, 5)))}

**APPOINTMENT OUTCOME:**
Per {provider_name}:
- Diagnosis: {random.choice(['Otitis Externa', 'Upper Respiratory Infection', 'Allergic Rhinitis', 'Contact Dermatitis'])}
- Treatment: {medication}
- Medication changes: Added antibiotic/medication
- Follow-up: Return if symptoms worsen, otherwise f/u with PCP in 2 weeks

Prescription: {medication} - {random.choice(['4 drops each ear 4x daily × 7 days', 'Take twice daily × 10 days', 'Apply topically twice daily'])}
Prescribing provider: {provider_name}
Pharmacy: {random.choice(['Kinney Drugs', 'Walgreens', 'CVS Pharmacy'])}, {pharmacy_phone}

**POST-APPOINTMENT SESSION:**
{client['first_name']} returned to {client['day_program']}. Appeared fatigued but engaged in preferred 
leisure activity. Minimal task demands placed due to medical visit stress.

**BEHAVIORAL OBSERVATIONS:**
{random.choice(['Increased requests for quiet activities and headphone use', 'Appropriate communication of discomfort using visual pain scale', 'Calm and cooperative throughout medical visit'])}

**MEDICATION MONITORING:**
Current medications updated. Nurse {nurse_name} notified to add new medication to 
medication administration record.

**PARENT COMMUNICATION:**
{client['parent1_first']} {client['last_name']} contacted at {client['phone_number']} to discuss:
- Appointment outcome and diagnosis
- Medication administration schedule
- Home observation for symptom improvement
- Next appointment (PCP follow-up in 2 weeks)

**RECOMMENDATIONS:**
- Monitor for medication side effects
- Modified schedule for medical appointment days - reduce academic demands
- Parent communication log for symptom tracking

**Documented by:** {staff_info['full_name']}, {staff_info['credentials']}
**Medical liaison:** {nurse_name}
**Date:** {session_info['date']}

---
END OF SESSION NOTE
"""
        return note
    
    def generate_medication_monitoring(self, client, session_info, staff_info):
        """Generate medication monitoring scenario"""
        psychiatrist = self.generate_provider_name()
        nurse = self.generate_provider_name()
        med1 = random.choice(['Clonidine HCL 0.3mg', 'Aripiprazole 5mg', 'Guanfacine 2mg'])
        med2 = random.choice(['Sertraline HCL 50mg', 'Fluoxetine 20mg', 'Escitalopram 10mg'])
        med3 = random.choice(['Trazodone 100mg', 'Melatonin 5mg', 'Clonazepam 0.5mg'])
        
        note = f"""# UCP SESSION NOTE - MEDICATION MONITORING

**Client:** {client['full_name']}
**Date of Birth:** {client['dob']}
**Session Date:** {session_info['date']}
**Location:** {client['residential_program']}
**Monitoring Staff:** {staff_info['full_name']}, {staff_info['credentials']}
**Consulting Nurse:** {nurse}

---

## MEDICATION-FOCUSED BEHAVIORAL OBSERVATION

**CURRENT MEDICATION REGIMEN:**
Prescribed by {psychiatrist}
Last appointment: {self.generate_date_variations(datetime.today() - timedelta(days=random.randint(20, 45)))}
Next appointment: {self.generate_date_variations(datetime.today() + timedelta(days=random.randint(35, 65)))}

**ROUTINE MEDICATIONS:**
1. {med1} - PO daily at 8:00 PM
   Indication: {random.choice(['Sleep disturbance, anxiety', 'Agitation', 'ADHD symptoms'])}
   Start date: {self.generate_date_variations(datetime.today() - timedelta(days=random.randint(180, 400)))}
   
2. {med2} - PO daily at 8:00 AM
   Indication: Anxiety disorder, mood disorder
   Start date: {self.generate_date_variations(datetime.today() - timedelta(days=random.randint(120, 300)))}
   
3. {med3} - PO daily at 8:00 PM
   Indication: Sleep support
   Start date: {self.generate_date_variations(datetime.today() - timedelta(days=random.randint(90, 200)))}

**RECENT CHANGE:**
{self.generate_date_variations(datetime.today() - timedelta(days=random.randint(10, 20)))}: 
{med2} dosage increased
Ordered by: {psychiatrist}

**BEHAVIORAL OBSERVATIONS POST-CHANGE:**

**MORNING OBSERVATIONS:**
Increased alertness noted compared to previous week. {client['first_name']} readily engaged in 
morning routine with {random.randint(80, 90)}% independence. Sleep quality per parent report: 
"Best week in months, sleeping through the night."

**MIDDAY OBSERVATIONS:**
Participation in structured activities excellent. {client['first_name']} completed tasks with 
minimal prompting. Appetite: Normal, consumed full lunch.

**AFTERNOON OBSERVATIONS:**
Sustained attention during tasks improved. {client['first_name']} worked for {random.randint(20, 30)}-minute 
intervals. Energy level: Appropriate, no signs of hyperactivity or lethargy.

**SIDE EFFECTS MONITORING:**
☑ Drowsiness: {random.choice(['None observed', 'Mild improvement from baseline'])}
☑ Agitation: None observed
☐ Sleep disturbance: Improved sleep continuity per parent report
☐ Appetite changes: Stable, appropriate intake
☐ Motor coordination: No changes noted

**PRN MEDICATION ADMINISTRATION:**
{random.choice(['10:30 AM', '2:15 PM'])}: Ibuprofen 200mg administered for {random.choice(['headache', 'minor discomfort'])} complaint
Administered by: {nurse}
Response: Symptoms resolved within 45 minutes

**VITAL SIGNS:**
Time: {random.choice(['10:25 AM', '2:10 PM'])}
Temperature: {random.choice(['98.2°F', '98.6°F', '97.9°F'])}
Pulse: {random.randint(72, 84)} bpm
Respirations: {random.randint(14, 18)} per minute
Recorded by: {nurse}

**PARENT CONSULTATION:**
{client['parent1_first']} {client['last_name']} contacted at {client['phone_number']}.

Home observations reported:
- Sleep pattern: Falling asleep faster
- Morning behavior: More cooperative, less irritable
- Evening behavior: Calmer during bedtime routine
- Medication compliance: 100% adherence, no missed doses

**CLINICAL RECOMMENDATIONS:**
- Continue current dosing schedule
- Monitor {random.choice(['sleep quality', 'daytime alertness', 'mood stability'])} for next 30 days
- Report findings to {psychiatrist} at next appointment
- Parent daily monitoring log for sleep onset time and morning mood

**FOLLOW-UP:**
Medication review: {self.generate_date_variations(datetime.today() + timedelta(days=random.randint(25, 35)))}
Prescriber appointment: {self.generate_date_variations(datetime.today() + timedelta(days=random.randint(50, 70)))}

**Documented by:** {staff_info['full_name']}, {staff_info['credentials']}
**Reviewed by:** {nurse}
**Date:** {session_info['date']}

---
END OF SESSION NOTE
"""
        return note
    
    def generate_crisis_intervention(self, client, session_info, staff_info):
        """Generate crisis intervention scenario"""
        staff2 = self.generate_staff_name()
        staff3 = self.generate_staff_name()
        supervisor = self.generate_staff_name()
        nurse = self.generate_provider_name()
        psychiatrist = self.generate_provider_name()
        director = self.generate_staff_name()
        home_address = client['home_address'] if client['home_address'] else f"{random.randint(50, 299)} Geiger Road, Rome, NY 13440"
        facility_address = f"{client['residential_program']}, {random.randint(80, 105)} Geiger Road, Rome, NY 13440"
        
        note = f"""# UCP CRITICAL INCIDENT REPORT

**UPSTATE CARING PARTNERS**
125 Business Park Drive, Utica, NY 13502
Emergency Contact: 315-724-6907

**CLIENT INFORMATION:**
Name: {client['full_name']}
Date of Birth: {client['dob']}
Primary Residence: {home_address}
Emergency Contact 1: {client['parent1_first']} {client['last_name']} - {client['phone_number']}"""

        if client['parent2_first'] and client['parent2_phone']:
            note += f"""
Emergency Contact 2: {client['parent2_first']} {client['last_name']} - {client['parent2_phone']}"""

        note += f"""

**INCIDENT DETAILS:**
Date: {session_info['date']}
Time of Onset: {random.choice(['11:22 AM', '2:15 PM', '9:45 AM'])}
Location: {facility_address}
Incident Category: CRISIS - Level 3 (Severe)

**STAFF RESPONSE TEAM:**
Primary: {staff_info['full_name']}, {staff_info['credentials']}
Secondary: {staff2[0]} {staff2[1]}, {staff2[2]}
Tertiary: {staff3[0]} {staff3[1]}, {staff3[2]}
Supervisor notified: {supervisor[0]} {supervisor[1]}, {supervisor[2]}
Medical: {nurse}

**DETAILED INCIDENT TIMELINE:**

{random.choice(['11:18 AM', '2:11 PM', '9:41 AM'])}: PRECIPITATING EVENT
{client['first_name']} was engaged in activity when trigger occurred.

{random.choice(['11:22 AM', '2:15 PM', '9:45 AM'])}: BEHAVIOR ESCALATION - LEVEL 1
Verbal refusal escalated to yelling.
Staff {staff_info['full_name']}, {staff_info['credentials']} implemented verbal de-escalation.

{random.choice(['11:25 AM', '2:18 PM', '9:48 AM'])}: BEHAVIOR ESCALATION - LEVEL 2
Physical aggression toward peer.
Additional staff {staff2[0]} {staff2[1]}, {staff2[2]} joined response.

{random.choice(['11:28 AM', '2:21 PM', '9:51 AM'])}: BEHAVIOR ESCALATION - LEVEL 3 (CRISIS)
Continued physical aggression toward staff. Property destruction.
{supervisor[0]} {supervisor[1]}, {supervisor[2]} notified.

{random.choice(['11:30 AM', '2:23 PM', '9:53 AM'])}: RESTRICTIVE INTERVENTION INITIATED
Type: SCIP-R three-person supine restraint
Staff involved: {staff_info['full_name']}, {staff2[0]} {staff2[1]}, {staff3[0]} {staff3[1]}
Reason: Imminent danger to self and others

{random.choice(['11:45 AM', '2:38 PM', '10:08 AM'])}: DE-ESCALATION PROGRESS
{client['first_name']} showing decreased muscle tension, verbal communication restored.

{random.choice(['11:52 AM', '2:45 PM', '10:15 AM'])}: RESTRAINT RELEASED
Total restraint duration: {random.randint(18, 25)} minutes
{client['first_name']} moved to quiet room for recovery.

**INJURIES SUSTAINED:**

CLIENT:
Minor redness on wrists from restraint contact, no skin breakdown
Assessed by: {nurse}
Treatment: Visual inspection only, ice pack offered
Medical follow-up: Monitor for 24 hours

STAFF INJURIES:
{staff_info['full_name']}: Superficial scratch - Treatment: Cleaned, bandaged
{staff2[0]} {staff2[1]}: Contusion from impact - Treatment: Ice pack applied
{staff3[0]} {staff3[1]}: No injuries

PROPERTY DAMAGE:
{random.choice(['Folding chair damaged', 'Activity table scratched', 'Materials broken'])}
Estimated cost: ${random.randint(150, 250)}

**EMERGENCY CONTACTS MADE:**

{random.choice(['11:35 AM', '2:28 PM', '9:58 AM'])}: {client['parent1_first']} {client['last_name']} contacted at {client['phone_number']}
Reached: Yes, answered immediately
Notified by: {supervisor[0]} {supervisor[1]}, {supervisor[2]}"""

        if client['parent2_first'] and client['parent2_phone']:
            note += f"""

{random.choice(['12:00 PM', '2:45 PM', '10:15 AM'])}: {client['parent2_first']} {client['last_name']} contacted at {client['parent2_phone']}
Reached: Yes, callback received"""

        note += f"""

**MEDICAL CONSULTATION:**
{nurse} assessed. 
Vital signs: Temp {random.choice(['98.6°F', '98.4°F'])}, Pulse {random.randint(82, 94)}, BP {random.randint(115, 125)}/{random.randint(72, 82)}, Respirations {random.randint(16, 20)}
Recommendation: Continue monitoring, no medical intervention needed

**PSYCHIATRIC CONSULTATION:**
{psychiatrist} contacted.
Emergency appointment: {self.generate_date_variations(datetime.today() + timedelta(days=1))}

**INCIDENT CLASSIFICATION:**
☑ SCIP-R Restrictive Physical Intervention
☑ Multiple staff required (3+)
☑ Duration > 10 minutes
☐ Emergency medical services called
☑ Parent immediate notification
☑ Property damage
☑ Staff injury requiring treatment
☑ Psychiatric consultation required

**RESTRICTIVE INTERVENTION DETAILS:**
Start time: {random.choice(['11:30 AM', '2:23 PM', '9:53 AM'])}
End time: {random.choice(['11:52 AM', '2:45 PM', '10:15 AM'])}
Total duration: {random.randint(18, 25)} minutes
Type: Three-person supine restraint per SCIP-R protocol
Medical monitoring: {nurse} checked vital signs every 5 minutes

**REGULATORY NOTIFICATIONS:**

☑ Program Director: {director[0]} {director[1]} - notified
☑ Clinical Director: {supervisor[0]} {supervisor[1]} - notified
☑ OPWDD: Incident report submitted
☑ Agency Administration: Executive Director notified
☐ Law Enforcement: Not required
☐ Emergency Medical Services: Not required

**POST-INCIDENT PROCEDURES:**

**STAFF DEBRIEFING:**
Conducted by: {supervisor[0]} {supervisor[1]}, {supervisor[2]}
Attendees: {staff_info['full_name']}, {staff2[0]} {staff2[1]}, {staff3[0]} {staff3[1]}

**REQUIRED REVIEWS:**
☑ BSP Review: Scheduled
☑ FBA Update: Scheduled
☑ Medication Review: {psychiatrist} emergency appt {self.generate_date_variations(datetime.today() + timedelta(days=1))}
☑ Safety Protocol Review: Scheduled
☑ Incident Review Team: Scheduled

**Report compiled by:** {staff_info['full_name']}, {staff_info['credentials']}
**Reviewed by:** {supervisor[0]} {supervisor[1]}, {supervisor[2]}
**Medical review:** {nurse}
**Report filed:** {session_info['date']}
**Report ID:** INC-{datetime.today().year}-{random.randint(1000, 9999)}

---
END OF INCIDENT REPORT
"""
        return note
    
    def generate_post_crisis_recovery(self, client, session_info, staff_info):
        """Generate post-crisis recovery scenario"""
        supervisor = self.generate_staff_name()
        bcba = self.generate_staff_name()
        ot = self.generate_provider_name()
        slp = self.generate_provider_name()
        nurse = self.generate_provider_name()
        psychiatrist = self.generate_provider_name()
        incident_date = self.generate_date_variations(datetime.today() - timedelta(days=2))
        
        note = f"""# UCP POST-CRISIS RECOVERY SESSION NOTE

**Client:** {client['full_name']}
**Recovery Session Date:** {session_info['date']}
**Original Incident Date:** {incident_date}
**Location:** {client['residential_program']}
**Staff:** {staff_info['full_name']}, {staff_info['credentials']}
**Clinical Supervisor:** {supervisor[0]} {supervisor[1]}, {supervisor[2]}

---

## POST-CRISIS THERAPEUTIC INTERVENTION

**INCIDENT REFERENCE:**
Critical incident on {incident_date} at {client['residential_program']}.
Incident Report ID: INC-{datetime.today().year}-{random.randint(1000, 9999)}
Type: Physical aggression toward peer and staff, property destruction
Duration: Escalation {random.randint(5, 8)} minutes, restraint {random.randint(18, 25)} minutes

TIME SINCE INCIDENT: 48 hours

**CURRENT SESSION PURPOSE:**
1. Therapeutic processing of incident
2. Safety planning reinforcement
3. Skill rebuilding for emotion regulation
4. Relationship repair with staff and peers

**SESSION ACTIVITIES:**

**THERAPEUTIC PROCESSING:**
{client['first_name']} participated in cognitive-behavioral processing with {staff_info['full_name']}, {staff_info['credentials']}.

Discussion topics:
- Event sequence understanding using visual timeline
- Emotional identification (anger, frustration, feeling out of control)
- Alternative response strategies (asking for break, using calm-down space)
- Safety understanding (why restraint was necessary)

{client['first_name']}'s insight: Demonstrated good understanding of event sequence, identified trigger, 
recognized inappropriate choice and impact on others.

**SAFETY PLANNING:**
Reviewed and updated safety protocols with {client['first_name']}.

**NEW SAFETY MEASURES IMPLEMENTED:**
Following incident on {incident_date}:
1. Individual activity schedule - Implemented {self.generate_date_variations(datetime.today() - timedelta(days=1))}
2. Enhanced visual supports for emotion regulation - Implemented {self.generate_date_variations(datetime.today() - timedelta(days=1))}
3. Enhanced monitoring during peer activities (1:2 ratio)

**PARENT COLLABORATION:**
Joint session with {client['parent1_first']} {client['last_name']}"""
        
        if client['parent2_first']:
            note += f" and {client['parent2_first']} {client['last_name']}"
        
        note += f""".

Parents contacted at {client['phone_number']} to confirm session attendance.

Discussion points:
- Home-program consistency for emotion regulation strategies
- Warning sign recognition (escalating voice volume, body tension, pacing)
- De-escalation support at home (offering break space, reducing demands)
- Communication protocols between home and program

**STAFF RELATIONSHIP REPAIR:**
{client['first_name']} met individually with staff involved in incident.
Facilitated by: {supervisor[0]} {supervisor[1]}, {supervisor[2]}

Process included: {client['first_name']}'s verbal apology, staff reassurance of continued support, 
discussion of moving forward. Staff reported positive interaction quality.

**BEHAVIORAL SUPPORT PLAN UPDATES:**
Modified BSP implemented {self.generate_date_variations(datetime.today() - timedelta(days=1))} following comprehensive review.

Changes include:
- Enhanced antecedent strategies (increased warnings before transitions)
- Additional teaching of replacement behaviors (requesting break using visual card)
- Updated crisis protocols (specific de-escalation sequence)
- Modified reinforcement schedule

Review team:
- {bcba[0]} {bcba[1]}, {bcba[2]} (Behavior Specialist)
- {ot} (Occupational Therapist)
- {slp} (Speech-Language Pathologist)
- {nurse} (Nursing)
- Parents: {client['parent1_first']} {client['last_name']}"""
        
        if client['parent2_first']:
            note += f", {client['parent2_first']} {client['last_name']}"
        
        note += f"""

**PSYCHIATRIC FOLLOW-UP:**
Emergency consultation with {psychiatrist} on {self.generate_date_variations(datetime.today() - timedelta(days=1))}.

Medication adjustments:
- {random.choice(['Increased evening anxiety medication', 'Added PRN protocol', 'Dosage adjustment made'])}
- Continue current regimen with modifications

Next psychiatric appointment: {self.generate_date_variations(datetime.today() + timedelta(days=random.randint(20, 35)))}

**SKILL REBUILDING:**
Focus areas identified:
1. Emotion regulation and identification
2. Requesting breaks appropriately
3. Appropriate peer interactions

Teaching sessions scheduled:
- Daily emotion identification practice with {staff_info['full_name']}, {staff_info['credentials']}
- Twice weekly skills practice
- Break request training as needed throughout day

**ENVIRONMENTAL MODIFICATIONS:**
Changes made at {client['residential_program']} following incident:

Physical environment:
- Designated "calm corner" with visual supports (Completed {self.generate_date_variations(datetime.today() - timedelta(days=1))})
- Additional soft seating for de-escalation space

Schedule modifications:
- Individual time for preferred activities
- Structured peer activities with higher staff ratio for 1 week

**MONITORING PROTOCOL:**
Enhanced monitoring period: {session_info['date']} through {self.generate_date_variations(datetime.today() + timedelta(days=14))} (2 weeks)

Monitoring frequency: Hourly emotion check-ins using 5-point scale
Documentation: Electronic incident tracking system + daily narrative notes

**CHECK-IN SCHEDULE:**
Daily check-ins with rotating staff:
- Morning: 8:30 AM (baseline mood assessment)
- Midday: 12:00 PM (activity participation check)
- Afternoon: 3:00 PM (end-of-day processing)

**PARENT COMMUNICATION PLAN:**
Daily updates to {client['parent1_first']} {client['last_name']}:
- Method: Phone call
- Time: 4:00 PM daily
- Contact: {client['phone_number']}

**PROGRESS INDICATORS:**
Since incident on {incident_date} (48 hours post-incident):
- Zero physical aggression incidents
- Appropriate use of break request card {random.randint(2, 4)} times
- Positive peer interactions during structured activities (100% appropriate)
- Verbal communication of emotions using 5-point scale with {random.randint(75, 90)}% accuracy

**NEXT STEPS:**
☑ Continue daily monitoring through {self.generate_date_variations(datetime.today() + timedelta(days=14))}
☑ BSP implementation fidelity checks (daily by supervisor)
☑ Ongoing parent collaboration (daily calls)
☑ Psychiatric follow-up {self.generate_date_variations(datetime.today() + timedelta(days=random.randint(20, 35)))}
☑ Incident review team meeting scheduled
☑ FBA update completion target: {self.generate_date_variations(datetime.today() + timedelta(days=random.randint(8, 14)))}

**DOCUMENTATION:**
Recovery session documented by: {staff_info['full_name']}, {staff_info['credentials']}
Clinical supervision: {supervisor[0]} {supervisor[1]}, {supervisor[2]}
Parent consent obtained: {session_info['date']}
Treatment plan updated: {self.generate_date_variations(datetime.today() - timedelta(days=1))}

Session date: {session_info['date']}
Next recovery session: {self.generate_date_variations(datetime.today() + timedelta(days=7))}

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
        
        # Generate note based on scenario type (12 scenarios)
        if scenario_type == 'exceptional_progress':
            return self.generate_exceptional_progress(client, session_info, staff_info)
        elif scenario_type == 'skill_acquisition':
            return self.generate_skill_acquisition(client, session_info, staff_info)
        elif scenario_type == 'positive_social':
            return self.generate_positive_social(client, session_info, staff_info)
        elif scenario_type == 'standard_session':
            return self.generate_standard_session(client, session_info, staff_info)
        elif scenario_type == 'maintenance':
            return self.generate_maintenance(client, session_info, staff_info)
        elif scenario_type == 'mild_challenging':
            return self.generate_mild_challenging(client, session_info, staff_info)
        elif scenario_type == 'moderate_challenging':
            return self.generate_moderate_challenging(client, session_info, staff_info)
        elif scenario_type == 'environmental_triggers':
            return self.generate_environmental_triggers(client, session_info, staff_info)
        elif scenario_type == 'medical_appointment':
            return self.generate_medical_appointment(client, session_info, staff_info)
        elif scenario_type == 'medication_monitoring':
            return self.generate_medication_monitoring(client, session_info, staff_info)
        elif scenario_type == 'crisis_intervention':
            return self.generate_crisis_intervention(client, session_info, staff_info)
        elif scenario_type == 'post_crisis_recovery':
            return self.generate_post_crisis_recovery(client, session_info, staff_info)
    
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
    scenario_counts = generator.generate_batch(n=1000)
    
    print("✅ Synthetic note generation complete!")
    print("\nNext steps:")
    print("  1. Review generated notes in data/synthetic/raw/")
    print("  2. Test PHI recognizers on sample notes")
    print("  3. Generate ground truth annotations")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
