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


class NoteBuilder:
    """Build note text and PHI spans together (provenance ground truth)."""

    def __init__(self):
        self._parts = []
        self.entities = []

    def plain(self, s):
        if s:
            self._parts.append(s)

    def phi(self, s, typ):
        if not s:
            return
        buf = "".join(self._parts)
        start = len(buf)
        self._parts.append(s)
        self.entities.append({"text": s, "type": typ, "start": start, "end": start + len(s)})

    def build(self):
        text = "".join(self._parts)
        entities = sorted(self.entities, key=lambda e: e["start"])
        return text, entities


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
        """Generate name in 6 different formats"""
        use_middle = random.random() < 0.4
        middle_initial = random.choice(self.middle_initials) if use_middle else None

        format_choice = random.choice([1, 2, 3, 4, 5, 6])

        if format_choice == 1:
            # Format 1: First Last  (e.g., "Emma Rodriguez")
            return f"{first_name} {last_name}"

        elif format_choice == 2:
            # Format 2: Last, First  (e.g., "Rodriguez, Emma")
            return f"{last_name}, {first_name}"

        elif format_choice == 3:
            # Format 3: Last, First MI  (e.g., "Rodriguez, Emma M.")
            if middle_initial:
                return f"{last_name}, {first_name} {middle_initial}."
            return f"{last_name}, {first_name}"

        elif format_choice == 4:
            # Format 4: First MI Last  (e.g., "Emma M. Rodriguez")
            if middle_initial:
                return f"{first_name} {middle_initial}. {last_name}"
            return f"{first_name} {last_name}"

        elif format_choice == 5:
            # Format 5: Initial. Last  (e.g., "E. Rodriguez")  — partial name
            return f"{first_name[0]}. {last_name}"

        else:
            # Format 6: First Last MI  (e.g., "Emma Rodriguez M.")  — informal
            if middle_initial:
                return f"{first_name} {last_name} {middle_initial}."
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
    def generate_phone_variant(self, phone: str) -> str:
        """Return phone in one of 4 formats. Input assumed NXX-NXX-XXXX."""
        import re as _re
        m = _re.fullmatch(r"(\d{3})-(\d{3})-(\d{4})", phone.strip())
        if not m:
            return phone
        area, mid, last = m.group(1), m.group(2), m.group(3)
        fmt = random.choice([1, 2, 3, 4])
        if fmt == 1:
            return f"{area}-{mid}-{last}"      # 315-555-1234  (original)
        elif fmt == 2:
            return f"({area}) {mid}-{last}"    # (315) 555-1234
        elif fmt == 3:
            return f"{area}.{mid}.{last}"      # 315.555.1234
        else:
            return f"({area}){mid}-{last}"     # (315)555-1234

    def generate_address_variant(self, address_data: dict) -> tuple:
        """
        Return (address_string, variant_type).
        variant_type: 'full' | 'street_only' | 'city_state'
        """
        try:
            street = address_data['street']
            city   = address_data['city']
            state  = address_data['state']
            zip_   = address_data['zip']
        except (KeyError, TypeError):
            return None, None

        variant = random.choice(['full', 'full', 'street_only', 'city_state'])
        if variant == 'full':
            return f"{street}, {city}, {state} {zip_}", 'full'
        elif variant == 'street_only':
            return street, 'street_only'
        else:
            return f"{city}, {state}", 'city_state'

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
        
        # Generate phone numbers with format variants
        phone_number = self.generate_phone_variant(random.choice(self.phone_numbers))
        parent2_phone = self.generate_phone_variant(random.choice(self.phone_numbers)) if has_two_parents else None

        # Generate address (30% of notes will have home address)
        has_address = random.random() < 0.3
        if has_address and len(self.addresses) > 0:
            address_data = random.choice(self.addresses)
            home_address, _ = self.generate_address_variant(address_data)
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

    def _staff_cred(self, b, staff_info):
        b.phi(staff_info["full_name"], "PERSON")
        if staff_info.get("credentials"):
            b.plain(", ")
            b.phi(staff_info["credentials"], "CREDENTIAL")

    def _staff_tuple_name_title(self, b, t):
        """t = (first, last, title, cred) from generate_staff_name."""
        b.phi(f"{t[0]} {t[1]}", "PERSON")
        if t[2]:
            b.plain(", ")
            b.phi(t[2], "CREDENTIAL")
        if len(t) > 3 and t[3]:
            b.plain(", ")
            b.phi(t[3], "CREDENTIAL")

    def generate_exceptional_progress(self, client, session_info, staff_info):
        """Generate exceptional progress scenario"""
        provider_name = self.generate_provider_name()
        goal_date = self.generate_date_variations(datetime.today() + timedelta(days=random.randint(30, 90)))
        b = NoteBuilder()
        b.plain("# UCP SESSION NOTE - EXCEPTIONAL PROGRESS\n\n**Client:** ")
        b.phi(client["full_name"], "PERSON")
        b.plain("\n**Date of Birth:** ")
        b.phi(client["dob"], "DATE")
        b.plain("\n**Session Date:** ")
        b.phi(session_info["date"], "DATE")
        b.plain(f"\n**Session Time:** {session_info['start_time']} - {session_info['end_time']}\n**Location:** ")
        b.plain(client["residential_program"])
        b.plain("\n**Staff:** ")
        self._staff_cred(b, staff_info)
        b.plain("\n**Medicaid ID:** ")
        b.phi(client["medicaid_id"], "MEDICAID_ID")
        b.plain("\n\n---\n\n## EXCEPTIONAL PROGRESS SESSION\n\n")
        b.phi(client["first_name"], "PERSON")
        b.plain(" demonstrated outstanding progress during today's session at ")
        b.plain(client["residential_program"])
        b.plain(". \n")
        b.phi(client["first_name"], "PERSON")
        b.plain(" achieved functional communication goal three weeks ahead of schedule, marking significant \nadvancement in expressive language skills.\n\nThroughout the session from ")
        b.plain(f"{session_info['start_time']} to {session_info['end_time']}, ")
        b.phi(client["first_name"], "PERSON")
        b.plain(" \nconsistently exhibited appropriate verbal requesting, independent task completion, and positive peer engagement. \nCompleted all scheduled activities independently with 95% accuracy.\n\n**PARENT NOTIFICATION:**\n")
        b.phi(client["parent1_first"], "PERSON")
        b.plain(" ")
        b.phi(client["last_name"], "PERSON")
        b.plain(" contacted at ")
        b.phi(client["phone_number"], "PHONE")
        b.plain(" expressed pride in \n")
        b.phi(client["first_name"], "PERSON")
        b.plain("'s achievements.\n\n**STAFF OBSERVATIONS:**\n- Mastered three-step sequencing task with minimal prompting\n- Generalized skills across multiple settings\n- Positive peer interactions during group activity\n\n**RECOMMENDATIONS:**\n- Continue current intervention strategies\n- Advance to next skill level in functional communication program\n- Schedule review with ")
        b.phi(provider_name, "PERSON")
        b.plain(" on ")
        b.phi(goal_date, "DATE")
        b.plain("\n\n**Documentation:** ")
        self._staff_cred(b, staff_info)
        b.plain("\n**Date:** ")
        b.phi(session_info["date"], "DATE")
        b.plain("\n\n---\nEND OF SESSION NOTE\n")
        return b.build()
    
    def generate_skill_acquisition(self, client, session_info, staff_info):
        """Generate skill acquisition scenario"""
        vocational_staff = self.generate_staff_name()
        phone = client["phone_number"]
        t1, t2, t3 = random.randint(70, 80), random.randint(80, 90), random.randint(85, 95)
        overall = random.randint(78, 90)
        b = NoteBuilder()
        b.plain("# UCP SESSION NOTE - SKILL ACQUISITION\n\n**Client:** ")
        b.phi(client["full_name"], "PERSON")
        b.plain("\n**Date of Birth:** ")
        b.phi(client["dob"], "DATE")
        b.plain("\n**Session Date:** ")
        b.phi(session_info["date"], "DATE")
        b.plain("\n**Program:** ")
        b.plain(client["day_program"])
        b.plain(f"\n**Time:** {session_info['start_time']} - {session_info['end_time']}\n**Behavior Specialist:** ")
        self._staff_cred(b, staff_info)
        b.plain("\n\n---\n\n## SKILL ACQUISITION SESSION\n\n**Target Skill:** Multi-step vocational task completion\n**Teaching Method:** Discrete trial training with naturalistic teaching\n\n**SESSION SUMMARY:**\n")
        b.phi(client["first_name"], "PERSON")
        b.plain(" participated in 45 discrete trial training sessions focusing on lunch service \npreparation skills at ")
        b.plain(client["day_program"])
        b.plain(f". Session began at {session_info['start_time']} with \nhand washing and apron donning.\n\n**TRIAL DATA:**\n- Trial block 1: {t1}% accuracy across 15 trials\n- Trial block 2: {t2}% accuracy across 15 trials  \n- Trial block 3: {t3}% accuracy across 15 trials\n- Overall session accuracy: {overall}%\n\n**PROMPTING HIERARCHY:**\nInitial trials required full physical prompting, progressing to verbal prompting only by session end. \n")
        b.phi(client["first_name"], "PERSON")
        b.plain(" demonstrated improvement in response latency from 8.5 seconds to 3.2 seconds.\n\n**VOCATIONAL INTEGRATION:**\n")
        b.phi(client["first_name"], "PERSON")
        b.plain(" practiced food service skills during lunch preparation. Staff ")
        b.phi(f"{vocational_staff[0]} {vocational_staff[1]}", "PERSON")
        if vocational_staff[2]:
            b.plain(", ")
            b.phi(vocational_staff[2], "CREDENTIAL")
        b.plain(" supervised and reported successful completion of assigned tasks with minimal support.\n\n**PARENT COLLABORATION:**\nContacted ")
        b.phi(client["parent1_first"], "PERSON")
        b.plain(" ")
        b.phi(client["last_name"], "PERSON")
        b.plain(" at ")
        b.phi(phone, "PHONE")
        b.plain(" to discuss home practice strategies. \nParent reported ")
        b.phi(client["first_name"], "PERSON")
        b.plain(" has been practicing sorting tasks at home with good success.\n\n**NEXT SESSION GOALS:**\n- Increase trial complexity for vocational skills\n- Reduce prompting to gestural level only\n- Incorporate generalization setting\n\n**Therapist:** ")
        self._staff_cred(b, staff_info)
        b.plain("\n**Date signed:** ")
        b.phi(session_info["date"], "DATE")
        b.plain("\n\n---\nEND OF SESSION NOTE\n")
        return b.build()
    
    def generate_positive_social(self, client, session_info, staff_info):
        """Generate positive social interaction scenario"""
        co_staff = self.generate_staff_name()
        slp_name = self.generate_provider_name()
        peer1 = random.choice(self.first_names)
        peer2 = random.choice(self.first_names)
        n1, n2 = random.randint(5, 9), random.randint(10, 15)
        b = NoteBuilder()
        b.plain("# UCP SESSION NOTE - POSITIVE SOCIAL INTERACTION\n\n**Client:** ")
        b.phi(client["full_name"], "PERSON")
        b.plain("\n**Date of Service:** ")
        b.phi(session_info["date"], "DATE")
        b.plain("\n**Program Location:** ")
        b.plain(client["day_program"])
        b.plain("\n**Lead Therapist:** ")
        self._staff_cred(b, staff_info)
        b.plain("\n**Co-Facilitator:** ")
        self._staff_tuple_name_title(b, co_staff)
        b.plain("\n\n---\n\n## POSITIVE SOCIAL ENGAGEMENT SESSION\n\n")
        b.phi(client["first_name"], "PERSON")
        b.plain(" demonstrated exceptional social skills during structured group activity at \n")
        b.plain(client["day_program"])
        b.plain(f" from {session_info['start_time']} to {session_info['end_time']}.\n\n**PEER INTERACTIONS:**\n")
        b.phi(client["first_name"], "PERSON")
        b.plain(" engaged appropriately with peers ")
        b.phi(peer1, "PERSON")
        b.plain(" and ")
        b.phi(peer2, "PERSON")
        b.plain(f" during board game activity. \nInitiated {n1} social interactions, including:\n- Sharing game pieces with ")
        b.phi(peer1, "PERSON")
        b.plain("\n- Inviting ")
        b.phi(peer2, "PERSON")
        b.plain(f" to join activity\n- Requesting turn-taking using functional communication strategies\n\n**COMMUNICATION SUCCESSES:**\nFollowing recommendations from ")
        b.phi(slp_name, "PERSON")
        b.plain(", ")
        b.phi(client["first_name"], "PERSON")
        b.plain(f" utilized total communication approach \neffectively. Verbally expressed wants/needs {n2} times throughout session.\n\n**STAFF INTERACTIONS:**\nResponded positively to prompts from ")
        b.phi(staff_info["full_name"], "PERSON")
        b.plain(" and ")
        b.phi(f"{co_staff[0]} {co_staff[1]}", "PERSON")
        b.plain(". \nBuilt rapport through shared interest in activities. Accepted redirection appropriately when needed.\n\n**GROUP ACTIVITY PARTICIPATION:**\nActivity: Cooperative board game\nDuration: 45 minutes\nPeers present: ")
        b.phi(peer1, "PERSON")
        b.plain(", ")
        b.phi(peer2, "PERSON")
        b.plain("\nAdult supervision: 1:3 staff-to-client ratio\n\n**PARENT FEEDBACK:**\n")
        b.phi(client["parent1_first"], "PERSON")
        b.plain(" ")
        b.phi(client["last_name"], "PERSON")
        b.plain(" attended pickup and reported ")
        b.phi(client["first_name"], "PERSON")
        b.plain(" has \nbeen initiating play with siblings at home more frequently. Contact maintained via daily communication log.\n\n**RECOMMENDATIONS:**\n- Continue social skills group at ")
        b.plain(client["day_program"])
        b.plain("\n- Increase peer interaction opportunities during unstructured time\n- Collaborate with ")
        b.phi(slp_name, "PERSON")
        b.plain(" for social-emotional assessment\n\n**Documentation:** ")
        self._staff_cred(b, staff_info)
        b.plain("\n**Date:** ")
        b.phi(session_info["date"], "DATE")
        b.plain("\n\n---\nEND OF SESSION NOTE\n")
        return b.build()
    
    def generate_standard_session(self, client, session_info, staff_info):
        """Generate standard/routine session scenario"""
        medication = random.choice(["Sertraline 50mg", "Clonidine 0.3mg", "Risperidone 1mg"])
        prescriber = self.generate_provider_name()
        next_sess = self.generate_date_variations(datetime.today() + timedelta(days=2))
        a1, a2, a4 = random.randint(75, 90), random.randint(65, 85), random.randint(55, 75)
        overall = random.randint(70, 80)
        n_int = random.randint(2, 4)
        tokens = random.randint(15, 22)
        b = NoteBuilder()
        b.plain("# UCP SESSION NOTE - STANDARD SESSION\n\n**Client:** ")
        b.phi(client["full_name"], "PERSON")
        b.plain("\n**Date of Birth:** ")
        b.phi(client["dob"], "DATE")
        b.plain("\n**Session Date:** ")
        b.phi(session_info["date"], "DATE")
        b.plain("\n**Location:** ")
        b.plain(client["residential_program"])
        b.plain("\n**Staff:** ")
        self._staff_cred(b, staff_info)
        b.plain("\n**Medicaid ID:** ")
        b.phi(client["medicaid_id"], "MEDICAID_ID")
        b.plain("\n\n---\n\n## STANDARD SESSION REPORT\n\nSession conducted at ")
        b.plain(client["residential_program"])
        b.plain(f" from {session_info['start_time']} to {session_info['end_time']}. \n")
        b.phi(client["first_name"], "PERSON")
        b.plain(" engaged in 5 scheduled activities with mixed performance.\n\n**ACTIVITIES COMPLETED:**\n")
        b.plain(f"1. Fine motor skills: {a1}% independent completion\n2. Functional communication practice: {a2}% accuracy with verbal prompting\n3. Self-care routines: Required moderate physical prompting\n4. Academic tasks: {a4}% completion rate\n5. Leisure skills: High engagement, appropriate duration\n\nOverall completion rate: {overall}%\n\n**BEHAVIOR SUPPORT PLAN IMPLEMENTATION:**\nCurrent BSP was followed throughout session. ")
        b.phi(client["first_name"], "PERSON")
        b.plain(f" responded to {n_int} \nplanned interventions including:\n- Visual schedule transitions\n- Token economy system (earned {tokens} tokens toward preferred activity)\n- Functional communication training\n\n**CHALLENGES NOTED:**\nBrief verbal refusal when transitioning from self-care routine to academic tasks. Redirected using \nfirst-then board per BSP protocol. No restrictive interventions required.\n\n**PARENT COMMUNICATION:**\n")
        b.phi(client["parent1_first"], "PERSON")
        b.plain(" ")
        b.phi(client["last_name"], "PERSON")
        b.plain(" contacted at ")
        b.phi(client["phone_number"], "PHONE")
        b.plain(" regarding \nupcoming program meeting. Confirmed attendance and requested transportation information.\n\n**MEDICATION OBSERVATION:**\n")
        b.phi(client["first_name"], "PERSON")
        b.plain(f" takes {medication} daily per prescription from ")
        b.phi(prescriber, "PERSON")
        b.plain(". \nNo side effects observed during session.\n\n**FOLLOW-UP:**\nNext session scheduled for ")
        b.phi(next_sess, "DATE")
        b.plain(" at ")
        b.plain(client["residential_program"])
        b.plain(".\n\n**Authored by:** ")
        self._staff_cred(b, staff_info)
        b.plain("\n**Date:** ")
        b.phi(session_info["date"], "DATE")
        b.plain("\n\n---\nEND OF SESSION NOTE\n")
        return b.build()
    
    def generate_maintenance(self, client, session_info, staff_info):
        """Generate maintenance/generalization scenario"""
        home_staff = self.generate_staff_name()
        ot_name = self.generate_provider_name()
        slp_name = self.generate_provider_name()
        ot_phone = random.choice(self.phone_numbers)
        slp_phone = random.choice(self.phone_numbers)
        home_address = client["home_address"] if client["home_address"] else f"{random.randint(100, 999)} {random.choice(['Oak', 'Main', 'Elm', 'Maple'])} Street, Syracuse, NY 13204"
        p1, p2 = random.randint(82, 92), random.randint(75, 88)
        p3 = random.randint(70, 85)
        p4 = random.randint(78, 88)
        days_wk = random.randint(4, 6)
        freq = random.randint(3, 5)
        tri_date = self.generate_date_variations(datetime.today() + timedelta(days=random.randint(40, 60)))
        b = NoteBuilder()
        b.plain("# UCP SESSION NOTE - GENERALIZATION SESSION\n\n**Client:** ")
        b.phi(client["full_name"], "PERSON")
        b.plain("\n**Session Date:** ")
        b.phi(session_info["date"], "DATE")
        b.plain("\n**Settings:** ")
        b.plain(f"{client['residential_program']}, {client['day_program']}, ")
        b.phi(home_address, "ADDRESS")
        b.plain("\n**Lead Staff:** ")
        self._staff_cred(b, staff_info)
        b.plain("\n**Home Visit Staff:** ")
        self._staff_tuple_name_title(b, home_staff)
        b.plain("\n\n---\n\n## MAINTENANCE AND GENERALIZATION ASSESSMENT\n\n")
        b.phi(client["first_name"], "PERSON")
        b.plain(" demonstrated skill maintenance across multiple settings during coordinated session on ")
        b.phi(session_info["date"], "DATE")
        b.plain(f".\n\n**SETTING 1:** {client['residential_program']}\nSkills assessed: Self-care routines, task completion, social communication\nPerformance: {p1}% independent completion across all tasks\nStaff observer: ")
        self._staff_cred(b, staff_info)
        b.plain(f"\n\n**SETTING 2:** {client['day_program']}\nSkills assessed: Vocational tasks, peer interaction, following multi-step directions\nPerformance: {p2}% accuracy with minimal prompting\nTransition quality: Smooth transition with visual schedule support\n\n**HOME VISIT:** ")
        b.phi(home_address, "ADDRESS")
        b.plain("\nParent participants: ")
        b.phi(client["parent1_first"], "PERSON")
        b.plain(" ")
        b.phi(client["last_name"], "PERSON")
        if client["parent2_first"]:
            b.plain(" and ")
            b.phi(client["parent2_first"], "PERSON")
            b.plain(" ")
            b.phi(client["last_name"], "PERSON")
        b.plain("\nHome phone: ")
        b.phi(client["phone_number"], "PHONE")
        b.plain(f"\nSkills assessed: Home routines, family interactions, leisure skills\nPerformance: {p3}% independent completion in home environment\n\n**PARENT REPORT:**\n")
        b.phi(client["parent1_first"], "PERSON")
        b.plain(" ")
        b.phi(client["last_name"], "PERSON")
        b.plain(" reported ")
        b.phi(client["first_name"], "PERSON")
        b.plain(f" has been completing \nmorning routine independently at home {days_wk} days per week.")
        if client["parent2_first"]:
            b.plain(" ")
            b.phi(client["parent2_first"], "PERSON")
            b.plain(" ")
            b.phi(client["last_name"], "PERSON")
            b.plain(" noted improvement in communication with younger sibling during play activities.")
        b.plain("\n\n**Parent training provided on:**\n- Visual schedule implementation at home\n- Positive reinforcement strategies\n- Data collection procedures for home implementation\n\n**CONSISTENCY ANALYSIS:**\n")
        b.phi(client["first_name"], "PERSON")
        b.plain(f" maintained {p4}% consistency across settings for target skills. \nVariability noted in task initiation between ")
        b.plain(client["residential_program"])
        b.plain(" and home setting.\n\n**PROVIDER COORDINATION:**\nInformation shared with:\n- ")
        b.phi(ot_name, "PERSON")
        b.plain(" (Occupational Therapy) - contact: ")
        b.phi(ot_phone, "PHONE")
        b.plain("\n- ")
        b.phi(slp_name, "PERSON")
        b.plain(" (Speech Therapy) - contact: ")
        b.phi(slp_phone, "PHONE")
        b.plain(f"\n\n**RECOMMENDATIONS:**\n- Continue generalization trials across all settings weekly\n- Increase home practice frequency to {freq} times per week\n- Schedule tri-setting observation on ")
        b.phi(tri_date, "DATE")
        b.plain("\n\n**Documentation:** ")
        self._staff_cred(b, staff_info)
        b.plain("\n**Date:** ")
        b.phi(session_info["date"], "DATE")
        b.plain("\n\n---\nEND OF SESSION NOTE\n")
        return b.build()
    
    def generate_mild_challenging(self, client, session_info, staff_info):
        """Generate mild challenging behavior scenario"""
        behavior = random.choice(["Verbal refusal", "Minor non-compliance", "Brief withdrawal"])
        provider = self.generate_provider_name()
        inc_time = random.choice(["10:45 AM", "2:15 PM", "11:20 AM"])
        dur1, dur2 = random.randint(2, 5), random.randint(4, 7)
        next_s = self.generate_date_variations(datetime.today() + timedelta(days=2))
        prov_d = self.generate_date_variations(datetime.today() + timedelta(days=random.randint(8, 15)))
        b = NoteBuilder()
        b.plain("# UCP SESSION NOTE - MILD CHALLENGING BEHAVIOR\n\n**Client:** ")
        b.phi(client["full_name"], "PERSON")
        b.plain("\n**Incident Date:** ")
        b.phi(session_info["date"], "DATE")
        b.plain(f"\n**Incident Time:** {inc_time}\n**Location:** ")
        b.plain(client["residential_program"])
        b.plain("\n**Staff Present:** ")
        self._staff_cred(b, staff_info)
        b.plain("\n\n---\n\n## MILD CHALLENGING BEHAVIOR - SUCCESSFULLY REDIRECTED\n\n**ANTECEDENT:**\n")
        b.phi(client["first_name"], "PERSON")
        b.plain(f" was engaged in art activity at {client['residential_program']} when peer \nrequested to share art materials.\n\n**BEHAVIOR DESCRIPTION:**\n")
        b.phi(client["first_name"], "PERSON")
        b.plain(f" exhibited {behavior} characterized by:\n- Loud vocal tone stating \"No, mine!\"\n- Crossing arms and turning away\n- Refusing to make eye contact with staff\n- Duration: {dur1} minutes\n- Intensity: Mild (Level 1 on BSP scale)\n\n**INTERVENTION APPLIED:**\nStaff ")
        self._staff_cred(b, staff_info)
        b.plain(" implemented:\n1. Pause and proximity\n2. Visual first-then board presentation\n3. Choice offering between sharing materials or selecting different activity\n\n")
        b.phi(client["first_name"], "PERSON")
        b.plain(f" responded to choice offering intervention and returned to baseline within \n{dur2} minutes.\n\n**CONSEQUENCE:**\nBrief access to preferred activity delayed by 2 minutes per Behavior Support Plan, followed by \npraise for appropriate choice-making.\n\n**POST-INCIDENT:**\n")
        b.phi(client["first_name"], "PERSON")
        b.plain(" participated in cooperative art activity with appropriate sharing behaviors \nobserved. No further incidents during remainder of session.\n\n**FUNCTIONAL COMMUNICATION:**\n")
        b.phi(client["first_name"], "PERSON")
        b.plain(' was able to verbally request "my turn please" following de-escalation, \ndemonstrating understanding of replacement behavior.\n\n**PARENT NOTIFICATION:**\nPhone contact with ')
        b.phi(client["parent1_first"], "PERSON")
        b.plain(" ")
        b.phi(client["last_name"], "PERSON")
        b.plain(" at ")
        b.phi(client["phone_number"], "PHONE")
        b.plain(". \nParent reported similar sharing difficulties at home with sibling. Discussed consistency in \nintervention approach across settings.\n\n**FOLLOW-UP ACTIONS:**\n- Data entered into tracking system by ")
        b.phi(staff_info["full_name"], "PERSON")
        b.plain("\n- No modifications to current BSP recommended at this time\n- Continue monitoring for pattern development\n\n**Next session:** ")
        b.phi(next_s, "DATE")
        b.plain(" at ")
        b.plain(client["residential_program"])
        b.plain("\n**Provider check-in:** ")
        b.phi(provider, "PERSON")
        b.plain(" on ")
        b.phi(prov_d, "DATE")
        b.plain("\n\n**Report filed by:** ")
        self._staff_cred(b, staff_info)
        b.plain("\n**Filed:** ")
        b.phi(session_info["date"], "DATE")
        b.plain("\n\n---\nEND OF SESSION NOTE\n")
        return b.build()
    
    def generate_moderate_challenging(self, client, session_info, staff_info):
        """Generate moderate challenging behavior scenario"""
        staff2 = self.generate_staff_name()
        nurse = self.generate_provider_name()
        provider = self.generate_provider_name()
        parent2_phone = client["parent2_phone"] if client["parent2_phone"] else client["phone_number"]
        hdr_time = random.choice(["2:15 PM", "10:30 AM", "3:45 PM"])
        t_ant = random.choice(["2:10 PM", "10:25 AM", "3:40 PM"])
        t_on = random.choice(["2:15 PM", "10:30 AM", "3:45 PM"])
        t_ini = random.choice(["2:17 PM", "10:32 AM", "3:47 PM"])
        t_sec = random.choice(["2:20 PM", "10:35 AM", "3:50 PM"])
        t_de = random.choice(["2:28 PM", "10:43 AM", "3:58 PM"])
        cost = random.randint(25, 60)
        block_dur = random.randint(6, 10)
        fba_d = self.generate_date_variations(datetime.today() + timedelta(days=random.randint(8, 14)))
        psych_d = self.generate_date_variations(datetime.today() + timedelta(days=random.randint(15, 25)))
        b = NoteBuilder()
        b.plain("# UCP SESSION NOTE - MODERATE CHALLENGING BEHAVIOR\n\n**UPSTATE CARING PARTNERS**\n")
        b.phi("125 Business Park Drive, Utica, NY 13502", "ADDRESS")
        b.plain("\nPhone: ")
        b.phi("315-724-6907", "PHONE")
        b.plain("\n\n**Client Name:** ")
        b.phi(client["full_name"], "PERSON")
        b.plain("\n**Date of Birth:** ")
        b.phi(client["dob"], "DATE")
        b.plain("\n**Incident Date:** ")
        b.phi(session_info["date"], "DATE")
        b.plain(f"\n**Incident Time:** {hdr_time}\n**Location:** ")
        b.plain(client["residential_program"])
        b.plain("\n**Staff Involved:** ")
        self._staff_cred(b, staff_info)
        b.plain("; ")
        self._staff_tuple_name_title(b, staff2)
        b.plain("\n\n---\n\n## MODERATE CHALLENGING BEHAVIOR - MULTIPLE INTERVENTIONS\n\n**INDIVIDUALS PRESENT:**\nStaff: ")
        self._staff_cred(b, staff_info)
        b.plain("; ")
        self._staff_tuple_name_title(b, staff2)
        b.plain(f"\nLocation: Community room, {client['residential_program']}\n\n**INCIDENT TIMELINE:**\n\n{t_ant} - ANTECEDENT\n")
        b.phi(client["first_name"], "PERSON")
        b.plain(" was participating in group activity when transition announcement was made \nto end preferred activity.\n\n")
        b.plain(f"{t_on} - BEHAVIOR ONSET\n")
        b.phi(client["first_name"], "PERSON")
        b.plain(" engaged in physical aggression including:\n- Pushing peer\n- Throwing materials\n- Verbal aggression (yelling, protesting)\n\n")
        b.plain(f"{t_ini} - INITIAL INTERVENTION\n")
        self._staff_cred(b, staff_info)
        b.plain(" implemented verbal de-escalation and visual supports.\nLimited effectiveness. Behavior escalated to Level 2 (moderate severity).\n\n")
        b.plain(f"{t_sec} - SECONDARY INTERVENTION\n")
        self._staff_tuple_name_title(b, staff2)
        b.plain(" joined intervention team.\nSCIP-R blocking pads utilized per BSP protocol.\n")
        b.phi(client["first_name"], "PERSON")
        b.plain(" responded to planned ignoring combined with blocking strategy.\n\n")
        b.plain(f"{t_de} - DE-ESCALATION ACHIEVED\n")
        b.phi(client["first_name"], "PERSON")
        b.plain(" returned to baseline. Moved to quiet room for recovery.\n\n**INJURIES/DAMAGE:**\nStaff: ")
        b.phi(staff_info["full_name"], "PERSON")
        b.plain(f" sustained minor scratch on left forearm, no medical treatment required\nProperty: Game materials damaged, approximate cost ${cost}\nClient: No injuries sustained\n\n**IMMEDIATE PARENT CONTACT:**\n")
        b.phi(client["parent1_first"], "PERSON")
        b.plain(" ")
        b.phi(client["last_name"], "PERSON")
        b.plain(" contacted at ")
        b.phi(client["phone_number"], "PHONE")
        b.plain(".\nParent acknowledged incident and requested details of antecedent triggers.")
        if client["parent2_first"]:
            b.plain("\n\n")
            b.phi(client["parent2_first"], "PERSON")
            b.plain(" ")
            b.phi(client["last_name"], "PERSON")
            b.plain(" contacted at ")
            b.phi(parent2_phone, "PHONE")
            b.plain(".\nParent confirmed evening check-in call and discussed home consistency strategies.")
        b.plain("\n\n**MEDICAL CONSULTATION:**\nNurse ")
        b.phi(nurse, "PERSON")
        b.plain(" consulted. Visual assessment of minor staff injury completed. \nNo client injuries noted. No medical intervention required.\n\n**RESTRICTIVE INTERVENTIONS USED:**\n- SCIP-R Blocking Pads: Yes (Duration: ")
        b.plain(f"{block_dur} minutes)\n- Physical Restraint: No\n- Seclusion: No\n- PRN Medication: Not administered\n\n**FUNCTIONAL BEHAVIOR ASSESSMENT UPDATE:**\nData suggests escape function related to transition from preferred activities. \nRecommend FBA review with ")
        self._staff_cred(b, staff_info)
        b.plain(" scheduled for \n")
        b.phi(fba_d, "DATE")
        b.plain(".\n\n**PSYCHIATRIC CONSULTATION:**\n")
        b.phi(provider, "PERSON")
        b.plain(" notified via phone message. Appointment maintained for \n")
        b.phi(psych_d, "DATE")
        b.plain(".\n\n**NOTIFICATIONS COMPLETED:**\n☑ Parents (contacted)\n☑ Program Director (notified)\n☑ Nurse (consulted)\n☑ Psychiatrist (message left)\n☐ OPWDD (Not required - internal incident)\n\n**FOLLOW-UP ACTIONS:**\n- Incident review meeting scheduled\n- BSP modification considered for transition protocols\n- Staff debriefing completed\n- Additional transition warnings for next 72 hours\n\n**Report compiled by:** ")
        self._staff_cred(b, staff_info)
        b.plain("\n**Report filed:** ")
        b.phi(session_info["date"], "DATE")
        b.plain("\n\n---\nEND OF SESSION NOTE\n")
        return b.build()
    
    def generate_environmental_triggers(self, client, session_info, staff_info):
        """Generate environmental triggers scenario"""
        provider = self.generate_provider_name()
        ot_name = self.generate_provider_name()
        ot_phone = random.choice(self.phone_numbers)
        location2 = random.choice([p for p in self.day_programs if p != client["day_program"]])
        t1 = random.choice(["9:30 AM", "10:15 AM", "8:45 AM"])
        t2 = random.choice(["11:45 AM", "1:30 PM", "2:15 PM"])
        d1 = self.generate_date_variations(datetime.today() - timedelta(days=random.randint(3, 8)))
        d2 = self.generate_date_variations(datetime.today() + timedelta(days=random.randint(8, 15)))
        d3 = self.generate_date_variations(datetime.today() + timedelta(days=random.randint(25, 40)))
        d4 = self.generate_date_variations(datetime.today() + timedelta(days=random.randint(10, 18)))
        b = NoteBuilder()
        b.plain("# UCP SESSION NOTE - ENVIRONMENTAL TRIGGER ANALYSIS\n\n**Client:** ")
        b.phi(client["full_name"], "PERSON")
        b.plain("\n**Session Date:** ")
        b.phi(session_info["date"], "DATE")
        b.plain(f"\n**Locations Observed:** {client['residential_program']}, {client['day_program']}, ")
        b.plain(location2)
        b.plain("\n**Observing Staff:** ")
        self._staff_cred(b, staff_info)
        b.plain(f"\n\n---\n\n## ENVIRONMENTAL TRIGGER DOCUMENTATION\n\n**TRANSITION 1:** {client['residential_program']} → {client['day_program']}\nTime: {t1}\nTrigger: Unexpected staff change (regular driver unavailable)\nClient Response: Moderate anxiety, verbal questioning, increased pacing\n\n")
        b.phi(client["first_name"], "PERSON")
        b.plain(" demonstrated heightened anxiety when informed of transition from \n")
        b.plain(client["residential_program"])
        b.plain(" to ")
        b.plain(client["day_program"])
        b.plain(" with unfamiliar driver. \nEnvironmental factors noted:\n- Different vehicle than typical transport\n- Substitute staff member instead of usual ")
        self._staff_cred(b, staff_info)
        b.plain(f"\n\n**TRANSITION 2:** {client['day_program']} → {location2}\nTime: {t2}\nTrigger: Schedule modification due to building maintenance\nClient Response: Mild agitation, requesting return to familiar setting\n\n**SCHEDULE DISRUPTION ANALYSIS:**\nOriginally scheduled appointment with ")
        b.phi(provider, "PERSON")
        b.plain(f" at {client['day_program']} on \n")
        b.phi(d1, "DATE")
        b.plain(" was \nrescheduled to ")
        b.phi(d2, "DATE")
        b.plain(" \ndue to provider illness. ")
        b.phi(client["first_name"], "PERSON")
        b.plain(" exhibited increased anxiety and repetitive questioning \nabout appointment status.\n\n**PARENT CONTACT:**\n")
        b.phi(client["parent1_first"], "PERSON")
        b.plain(" ")
        b.phi(client["last_name"], "PERSON")
        b.plain(" contacted at ")
        b.phi(client["phone_number"], "PHONE")
        b.plain(" to discuss \nschedule sensitivity. Parent reported ")
        b.phi(client["first_name"], "PERSON")
        b.plain(" frequently references upcoming appointments \nat home and struggles with last-minute changes.\n\n**SENSORY ENVIRONMENT ASSESSMENT:**\n")
        b.plain(f"{client['residential_program']}: Familiar lighting, low noise level, preferred seating available\n{client['day_program']}: Moderate noise level, fluorescent lighting, multiple peer interactions\n{location2}: High activity level, variable noise, open floor plan\n\nConsultation with ")
        b.phi(ot_name, "PERSON")
        b.plain(" scheduled for ")
        b.phi(d3, "DATE")
        b.plain(" \nto assess sensory processing needs and environmental accommodation recommendations.\n\n**RECOMMENDATIONS:**\n- Increase transition warnings from 5 minutes to 15 minutes advance notice\n- Environmental modifications at ")
        b.plain(client["day_program"])
        b.plain(":\n  * Provide noise-canceling headphones during high-activity periods\n  * Designate quiet space for breaks\n- Schedule consistency protocol - avoid changes within 48 hours when possible\n- Provider coordination for appointment preparation with visual schedule\n\n**FOLLOW-UP:**\nMeeting with ")
        b.phi(client["parent1_first"], "PERSON")
        b.plain(" ")
        b.phi(client["last_name"], "PERSON")
        b.plain(" scheduled \n")
        b.phi(d4, "DATE")
        b.plain(" \nto review environmental sensitivities.\n\nContact ")
        b.phi(ot_name, "PERSON")
        b.plain(" at ")
        b.phi(ot_phone, "PHONE")
        b.plain(" for sensory consultation.\n\n**Documented by:** ")
        self._staff_cred(b, staff_info)
        b.plain("\n**Date:** ")
        b.phi(session_info["date"], "DATE")
        b.plain("\n\n---\nEND OF SESSION NOTE\n")
        return b.build()
    
    def generate_medical_appointment(self, client, session_info, staff_info):
        """Generate medical appointment scenario"""
        provider_name = self.generate_provider_name()
        nurse_name = self.generate_provider_name()
        clinic_name = random.choice(["WellNow Urgent Care", "Community Health Center", "Syracuse Medical Associates"])
        clinic_address = f"{random.randint(400, 850)} {random.choice(['South Salina', 'James', 'University', 'Erie'])} Street, Syracuse, NY 13202"
        clinic_phone = random.choice(self.phone_numbers)
        pharmacy_phone = random.choice(self.phone_numbers)
        medication = random.choice(["Amoxicillin 500mg", "Neomycin-Polymyxin ear drops", "Fluticasone nasal spray"])
        dep = random.choice(["10:45 AM", "11:15 AM", "1:30 PM"])
        appt_t = random.choice(["11:15 AM", "11:45 AM", "2:00 PM"])
        chief = random.choice(["Bilateral ear pain", "Upper respiratory symptoms", "Seasonal allergies", "Skin rash"])
        onset = self.generate_date_variations(datetime.today() - timedelta(days=random.randint(2, 5)))
        dx = random.choice(["Otitis Externa", "Upper Respiratory Infection", "Allergic Rhinitis", "Contact Dermatitis"])
        rx_inst = random.choice(["4 drops each ear 4x daily × 7 days", "Take twice daily × 10 days", "Apply topically twice daily"])
        pharm = random.choice(["Kinney Drugs", "Walgreens", "CVS Pharmacy"])
        beh = random.choice(["Increased requests for quiet activities and headphone use", "Appropriate communication of discomfort using visual pain scale", "Calm and cooperative throughout medical visit"])
        b = NoteBuilder()
        b.plain("# UCP SESSION NOTE - MEDICAL APPOINTMENT COORDINATION\n\n**Client:** ")
        b.phi(client["full_name"], "PERSON")
        b.plain("\n**Session Date:** ")
        b.phi(session_info["date"], "DATE")
        b.plain("\n**Primary Location:** ")
        b.plain(client["day_program"])
        b.plain("\n**Staff:** ")
        self._staff_cred(b, staff_info)
        b.plain("\n\n---\n\n## MODIFIED SESSION - MEDICAL APPOINTMENT\n\n**SESSION MODIFICATION:**\nStandard session time modified to accommodate appointment with ")
        b.phi(provider_name, "PERSON")
        b.plain(" at ")
        b.plain(clinic_name)
        b.plain(", ")
        b.phi(clinic_address, "ADDRESS")
        b.plain(".\n\nModified session: Morning abbreviated session and afternoon return\n\n**MEDICAL APPOINTMENT PREPARATION:**\nDeparture time: ")
        b.plain(dep)
        b.plain("\nDestination: ")
        b.plain(clinic_name)
        b.plain(", ")
        b.phi(clinic_address, "ADDRESS")
        b.plain("\nClinic phone: ")
        b.phi(clinic_phone, "PHONE")
        b.plain("\nProvider: ")
        b.phi(provider_name, "PERSON")
        b.plain(f"\nAppointment time: {appt_t}\n\nTransportation: UCP van\nAccompanied by: ")
        self._staff_cred(b, staff_info)
        b.plain("\n\n**PARENT COORDINATION:**\n")
        b.phi(client["parent1_first"], "PERSON")
        b.plain(" ")
        b.phi(client["last_name"], "PERSON")
        b.plain(" met at clinic.\nContact number: ")
        b.phi(client["phone_number"], "PHONE")
        b.plain(f"\n\n**MEDICAL CONCERN ADDRESSED:**\nChief complaint: {chief}\nOnset: ")
        b.phi(onset, "DATE")
        b.plain("\n\n**APPOINTMENT OUTCOME:**\nPer ")
        b.phi(provider_name, "PERSON")
        b.plain(f":\n- Diagnosis: {dx}\n- Treatment: {medication}\n- Medication changes: Added antibiotic/medication\n- Follow-up: Return if symptoms worsen, otherwise f/u with PCP in 2 weeks\n\nPrescription: {medication} - {rx_inst}\nPrescribing provider: ")
        b.phi(provider_name, "PERSON")
        b.plain(f"\nPharmacy: {pharm}, ")
        b.phi(pharmacy_phone, "PHONE")
        b.plain("\n\n**POST-APPOINTMENT SESSION:**\n")
        b.phi(client["first_name"], "PERSON")
        b.plain(f" returned to {client['day_program']}. Appeared fatigued but engaged in preferred \nleisure activity. Minimal task demands placed due to medical visit stress.\n\n**BEHAVIORAL OBSERVATIONS:**\n")
        b.plain(beh)
        b.plain("\n\n**MEDICATION MONITORING:**\nCurrent medications updated. Nurse ")
        b.phi(nurse_name, "PERSON")
        b.plain(" notified to add new medication to \nmedication administration record.\n\n**PARENT COMMUNICATION:**\n")
        b.phi(client["parent1_first"], "PERSON")
        b.plain(" ")
        b.phi(client["last_name"], "PERSON")
        b.plain(" contacted at ")
        b.phi(client["phone_number"], "PHONE")
        b.plain(" to discuss:\n- Appointment outcome and diagnosis\n- Medication administration schedule\n- Home observation for symptom improvement\n- Next appointment (PCP follow-up in 2 weeks)\n\n**RECOMMENDATIONS:**\n- Monitor for medication side effects\n- Modified schedule for medical appointment days - reduce academic demands\n- Parent communication log for symptom tracking\n\n**Documented by:** ")
        self._staff_cred(b, staff_info)
        b.plain("\n**Medical liaison:** ")
        b.phi(nurse_name, "PERSON")
        b.plain("\n**Date:** ")
        b.phi(session_info["date"], "DATE")
        b.plain("\n\n---\nEND OF SESSION NOTE\n")
        return b.build()
    
    def generate_medication_monitoring(self, client, session_info, staff_info):
        """Generate medication monitoring scenario"""
        psychiatrist = self.generate_provider_name()
        nurse = self.generate_provider_name()
        med1 = random.choice(["Clonidine HCL 0.3mg", "Aripiprazole 5mg", "Guanfacine 2mg"])
        med2 = random.choice(["Sertraline HCL 50mg", "Fluoxetine 20mg", "Escitalopram 10mg"])
        med3 = random.choice(["Trazodone 100mg", "Melatonin 5mg", "Clonazepam 0.5mg"])
        la = self.generate_date_variations(datetime.today() - timedelta(days=random.randint(20, 45)))
        na = self.generate_date_variations(datetime.today() + timedelta(days=random.randint(35, 65)))
        sd1 = self.generate_date_variations(datetime.today() - timedelta(days=random.randint(180, 400)))
        sd2 = self.generate_date_variations(datetime.today() - timedelta(days=random.randint(120, 300)))
        sd3 = self.generate_date_variations(datetime.today() - timedelta(days=random.randint(90, 200)))
        chg = self.generate_date_variations(datetime.today() - timedelta(days=random.randint(10, 20)))
        ind1 = random.choice(["Sleep disturbance, anxiety", "Agitation", "ADHD symptoms"])
        pct = random.randint(80, 90)
        wmin = random.randint(20, 30)
        drow = random.choice(["None observed", "Mild improvement from baseline"])
        prn_t = random.choice(["10:30 AM", "2:15 PM"])
        prn_r = random.choice(["headache", "minor discomfort"])
        vs_t = random.choice(["10:25 AM", "2:10 PM"])
        temp = random.choice(["98.2°F", "98.6°F", "97.9°F"])
        pulse = random.randint(72, 84)
        resp = random.randint(14, 18)
        mon = random.choice(["sleep quality", "daytime alertness", "mood stability"])
        fu1 = self.generate_date_variations(datetime.today() + timedelta(days=random.randint(25, 35)))
        fu2 = self.generate_date_variations(datetime.today() + timedelta(days=random.randint(50, 70)))
        b = NoteBuilder()
        b.plain("# UCP SESSION NOTE - MEDICATION MONITORING\n\n**Client:** ")
        b.phi(client["full_name"], "PERSON")
        b.plain("\n**Date of Birth:** ")
        b.phi(client["dob"], "DATE")
        b.plain("\n**Session Date:** ")
        b.phi(session_info["date"], "DATE")
        b.plain("\n**Location:** ")
        b.plain(client["residential_program"])
        b.plain("\n**Monitoring Staff:** ")
        self._staff_cred(b, staff_info)
        b.plain("\n**Consulting Nurse:** ")
        b.phi(nurse, "PERSON")
        b.plain("\n\n---\n\n## MEDICATION-FOCUSED BEHAVIORAL OBSERVATION\n\n**CURRENT MEDICATION REGIMEN:**\nPrescribed by ")
        b.phi(psychiatrist, "PERSON")
        b.plain("\nLast appointment: ")
        b.phi(la, "DATE")
        b.plain("\nNext appointment: ")
        b.phi(na, "DATE")
        b.plain(f"\n\n**ROUTINE MEDICATIONS:**\n1. {med1} - PO daily at 8:00 PM\n   Indication: {ind1}\n   Start date: ")
        b.phi(sd1, "DATE")
        b.plain(f"\n   \n2. {med2} - PO daily at 8:00 AM\n   Indication: Anxiety disorder, mood disorder\n   Start date: ")
        b.phi(sd2, "DATE")
        b.plain(f"\n   \n3. {med3} - PO daily at 8:00 PM\n   Indication: Sleep support\n   Start date: ")
        b.phi(sd3, "DATE")
        b.plain("\n\n**RECENT CHANGE:**\n")
        b.phi(chg, "DATE")
        b.plain(f": \n{med2} dosage increased\nOrdered by: ")
        b.phi(psychiatrist, "PERSON")
        b.plain("\n\n**BEHAVIORAL OBSERVATIONS POST-CHANGE:**\n\n**MORNING OBSERVATIONS:**\nIncreased alertness noted compared to previous week. ")
        b.phi(client["first_name"], "PERSON")
        b.plain(f" readily engaged in \nmorning routine with {pct}% independence. Sleep quality per parent report: \n\"Best week in months, sleeping through the night.\"\n\n**MIDDAY OBSERVATIONS:**\nParticipation in structured activities excellent. ")
        b.phi(client["first_name"], "PERSON")
        b.plain(" completed tasks with \nminimal prompting. Appetite: Normal, consumed full lunch.\n\n**AFTERNOON OBSERVATIONS:**\nSustained attention during tasks improved. ")
        b.phi(client["first_name"], "PERSON")
        b.plain(f" worked for {wmin}-minute \nintervals. Energy level: Appropriate, no signs of hyperactivity or lethargy.\n\n**SIDE EFFECTS MONITORING:**\n☑ Drowsiness: ")
        b.plain(drow)
        b.plain("\n☑ Agitation: None observed\n☐ Sleep disturbance: Improved sleep continuity per parent report\n☐ Appetite changes: Stable, appropriate intake\n☐ Motor coordination: No changes noted\n\n**PRN MEDICATION ADMINISTRATION:**\n")
        b.plain(f"{prn_t}: Ibuprofen 200mg administered for {prn_r} complaint\nAdministered by: ")
        b.phi(nurse, "PERSON")
        b.plain(f"\nResponse: Symptoms resolved within 45 minutes\n\n**VITAL SIGNS:**\nTime: {vs_t}\nTemperature: {temp}\nPulse: {pulse} bpm\nRespirations: {resp} per minute\nRecorded by: ")
        b.phi(nurse, "PERSON")
        b.plain("\n\n**PARENT CONSULTATION:**\n")
        b.phi(client["parent1_first"], "PERSON")
        b.plain(" ")
        b.phi(client["last_name"], "PERSON")
        b.plain(" contacted at ")
        b.phi(client["phone_number"], "PHONE")
        b.plain(".\n\nHome observations reported:\n- Sleep pattern: Falling asleep faster\n- Morning behavior: More cooperative, less irritable\n- Evening behavior: Calmer during bedtime routine\n- Medication compliance: 100% adherence, no missed doses\n\n**CLINICAL RECOMMENDATIONS:**\n- Continue current dosing schedule\n- Monitor ")
        b.plain(mon)
        b.plain(" for next 30 days\n- Report findings to ")
        b.phi(psychiatrist, "PERSON")
        b.plain(" at next appointment\n- Parent daily monitoring log for sleep onset time and morning mood\n\n**FOLLOW-UP:**\nMedication review: ")
        b.phi(fu1, "DATE")
        b.plain("\nPrescriber appointment: ")
        b.phi(fu2, "DATE")
        b.plain("\n\n**Documented by:** ")
        self._staff_cred(b, staff_info)
        b.plain("\n**Reviewed by:** ")
        b.phi(nurse, "PERSON")
        b.plain("\n**Date:** ")
        b.phi(session_info["date"], "DATE")
        b.plain("\n\n---\nEND OF SESSION NOTE\n")
        return b.build()
    
    def generate_crisis_intervention(self, client, session_info, staff_info):
        """Generate crisis intervention scenario"""
        staff2 = self.generate_staff_name()
        staff3 = self.generate_staff_name()
        supervisor = self.generate_staff_name()
        nurse = self.generate_provider_name()
        psychiatrist = self.generate_provider_name()
        director = self.generate_staff_name()
        home_address = client["home_address"] if client["home_address"] else f"{random.randint(50, 299)} Geiger Road, Rome, NY 13440"
        facility_address = f"{client['residential_program']}, {random.randint(80, 105)} Geiger Road, Rome, NY 13440"
        t_onset = random.choice(["11:22 AM", "2:15 PM", "9:45 AM"])
        tp, tl1, tl2, tl3 = random.choice(["11:18 AM", "2:11 PM", "9:41 AM"]), random.choice(["11:22 AM", "2:15 PM", "9:45 AM"]), random.choice(["11:25 AM", "2:18 PM", "9:48 AM"]), random.choice(["11:28 AM", "2:21 PM", "9:51 AM"])
        tl4, tl5, tl6, tl7 = random.choice(["11:30 AM", "2:23 PM", "9:53 AM"]), random.choice(["11:45 AM", "2:38 PM", "10:08 AM"]), random.choice(["11:52 AM", "2:45 PM", "10:15 AM"]), random.choice(["11:35 AM", "2:28 PM", "9:58 AM"])
        rd1, rd2 = random.randint(18, 25), random.randint(18, 25)
        prop = random.choice(["Folding chair damaged", "Activity table scratched", "Materials broken"])
        pcost = random.randint(150, 250)
        t_p2 = random.choice(["12:00 PM", "2:45 PM", "10:15 AM"])
        temp = random.choice(["98.6°F", "98.4°F"])
        pulse = random.randint(82, 94)
        sbp, dbp = random.randint(115, 125), random.randint(72, 82)
        resp = random.randint(16, 20)
        em_appt = self.generate_date_variations(datetime.today() + timedelta(days=1))
        med_rev = self.generate_date_variations(datetime.today() + timedelta(days=1))
        rs, re = random.choice(["11:30 AM", "2:23 PM", "9:53 AM"]), random.choice(["11:52 AM", "2:45 PM", "10:15 AM"])
        rdur = random.randint(18, 25)
        rid = random.randint(1000, 9999)
        b = NoteBuilder()
        b.plain("# UCP CRITICAL INCIDENT REPORT\n\n**UPSTATE CARING PARTNERS**\n")
        b.phi("125 Business Park Drive, Utica, NY 13502", "ADDRESS")
        b.plain("\nEmergency Contact: ")
        b.phi("315-724-6907", "PHONE")
        b.plain("\n\n**CLIENT INFORMATION:**\nName: ")
        b.phi(client["full_name"], "PERSON")
        b.plain("\nDate of Birth: ")
        b.phi(client["dob"], "DATE")
        b.plain("\nPrimary Residence: ")
        b.phi(home_address, "ADDRESS")
        b.plain("\nEmergency Contact 1: ")
        b.phi(client["parent1_first"], "PERSON")
        b.plain(" ")
        b.phi(client["last_name"], "PERSON")
        b.plain(" - ")
        b.phi(client["phone_number"], "PHONE")
        if client["parent2_first"] and client["parent2_phone"]:
            b.plain("\nEmergency Contact 2: ")
            b.phi(client["parent2_first"], "PERSON")
            b.plain(" ")
            b.phi(client["last_name"], "PERSON")
            b.plain(" - ")
            b.phi(client["parent2_phone"], "PHONE")
        b.plain("\n\n**INCIDENT DETAILS:**\nDate: ")
        b.phi(session_info["date"], "DATE")
        b.plain(f"\nTime of Onset: {t_onset}\nLocation: ")
        b.phi(facility_address, "ADDRESS")
        b.plain("\nIncident Category: CRISIS - Level 3 (Severe)\n\n**STAFF RESPONSE TEAM:**\nPrimary: ")
        self._staff_cred(b, staff_info)
        b.plain("\nSecondary: ")
        self._staff_tuple_name_title(b, staff2)
        b.plain("\nTertiary: ")
        self._staff_tuple_name_title(b, staff3)
        b.plain("\nSupervisor notified: ")
        self._staff_tuple_name_title(b, supervisor)
        b.plain("\nMedical: ")
        b.phi(nurse, "PERSON")
        b.plain(f"\n\n**DETAILED INCIDENT TIMELINE:**\n\n{tp}: PRECIPITATING EVENT\n")
        b.phi(client["first_name"], "PERSON")
        b.plain(" was engaged in activity when trigger occurred.\n\n")
        b.plain(f"{tl1}: BEHAVIOR ESCALATION - LEVEL 1\nVerbal refusal escalated to yelling.\nStaff ")
        self._staff_cred(b, staff_info)
        b.plain(" implemented verbal de-escalation.\n\n")
        b.plain(f"{tl2}: BEHAVIOR ESCALATION - LEVEL 2\nPhysical aggression toward peer.\nAdditional staff ")
        self._staff_tuple_name_title(b, staff2)
        b.plain(" joined response.\n\n")
        b.plain(f"{tl3}: BEHAVIOR ESCALATION - LEVEL 3 (CRISIS)\nContinued physical aggression toward staff. Property destruction.\n")
        self._staff_tuple_name_title(b, supervisor)
        b.plain(" notified.\n\n")
        b.plain(f"{tl4}: RESTRICTIVE INTERVENTION INITIATED\nType: SCIP-R three-person supine restraint\nStaff involved: ")
        self._staff_cred(b, staff_info)
        b.plain(", ")
        b.phi(f"{staff2[0]} {staff2[1]}", "PERSON")
        b.plain(", ")
        b.phi(f"{staff3[0]} {staff3[1]}", "PERSON")
        b.plain("\nReason: Imminent danger to self and others\n\n")
        b.plain(f"{tl5}: DE-ESCALATION PROGRESS\n")
        b.phi(client["first_name"], "PERSON")
        b.plain(" showing decreased muscle tension, verbal communication restored.\n\n")
        b.plain(f"{tl6}: RESTRAINT RELEASED\nTotal restraint duration: {rd1} minutes\n")
        b.phi(client["first_name"], "PERSON")
        b.plain(" moved to quiet room for recovery.\n\n**INJURIES SUSTAINED:**\n\nCLIENT:\nMinor redness on wrists from restraint contact, no skin breakdown\nAssessed by: ")
        b.phi(nurse, "PERSON")
        b.plain("\nTreatment: Visual inspection only, ice pack offered\nMedical follow-up: Monitor for 24 hours\n\nSTAFF INJURIES:\n")
        b.phi(staff_info["full_name"], "PERSON")
        b.plain(": Superficial scratch - Treatment: Cleaned, bandaged\n")
        b.phi(f"{staff2[0]} {staff2[1]}", "PERSON")
        b.plain(": Contusion from impact - Treatment: Ice pack applied\n")
        b.phi(f"{staff3[0]} {staff3[1]}", "PERSON")
        b.plain(": No injuries\n\nPROPERTY DAMAGE:\n")
        b.plain(prop)
        b.plain(f"\nEstimated cost: ${pcost}\n\n**EMERGENCY CONTACTS MADE:**\n\n{tl7}: ")
        b.phi(client["parent1_first"], "PERSON")
        b.plain(" ")
        b.phi(client["last_name"], "PERSON")
        b.plain(" contacted at ")
        b.phi(client["phone_number"], "PHONE")
        b.plain("\nReached: Yes, answered immediately\nNotified by: ")
        self._staff_tuple_name_title(b, supervisor)
        if client["parent2_first"] and client["parent2_phone"]:
            b.plain(f"\n\n{t_p2}: ")
            b.phi(client["parent2_first"], "PERSON")
            b.plain(" ")
            b.phi(client["last_name"], "PERSON")
            b.plain(" contacted at ")
            b.phi(client["parent2_phone"], "PHONE")
            b.plain("\nReached: Yes, callback received")
        b.plain("\n\n**MEDICAL CONSULTATION:**\n")
        b.phi(nurse, "PERSON")
        b.plain(f" assessed. \nVital signs: Temp {temp}, Pulse {pulse}, BP {sbp}/{dbp}, Respirations {resp}\nRecommendation: Continue monitoring, no medical intervention needed\n\n**PSYCHIATRIC CONSULTATION:**\n")
        b.phi(psychiatrist, "PERSON")
        b.plain(" contacted.\nEmergency appointment: ")
        b.phi(em_appt, "DATE")
        b.plain("\n\n**INCIDENT CLASSIFICATION:**\n☑ SCIP-R Restrictive Physical Intervention\n☑ Multiple staff required (3+)\n☑ Duration > 10 minutes\n☐ Emergency medical services called\n☑ Parent immediate notification\n☑ Property damage\n☑ Staff injury requiring treatment\n☑ Psychiatric consultation required\n\n**RESTRICTIVE INTERVENTION DETAILS:**\nStart time: ")
        b.plain(rs)
        b.plain("\nEnd time: ")
        b.plain(re)
        b.plain(f"\nTotal duration: {rdur} minutes\nType: Three-person supine restraint per SCIP-R protocol\nMedical monitoring: ")
        b.phi(nurse, "PERSON")
        b.plain(" checked vital signs every 5 minutes\n\n**REGULATORY NOTIFICATIONS:**\n\n☑ Program Director: ")
        b.phi(f"{director[0]} {director[1]}", "PERSON")
        b.plain(" - notified\n☑ Clinical Director: ")
        b.phi(f"{supervisor[0]} {supervisor[1]}", "PERSON")
        b.plain(" - notified\n☑ OPWDD: Incident report submitted\n☑ Agency Administration: Executive Director notified\n☐ Law Enforcement: Not required\n☐ Emergency Medical Services: Not required\n\n**POST-INCIDENT PROCEDURES:**\n\n**STAFF DEBRIEFING:**\nConducted by: ")
        self._staff_tuple_name_title(b, supervisor)
        b.plain("\nAttendees: ")
        b.phi(staff_info["full_name"], "PERSON")
        b.plain(", ")
        b.phi(f"{staff2[0]} {staff2[1]}", "PERSON")
        b.plain(", ")
        b.phi(f"{staff3[0]} {staff3[1]}", "PERSON")
        b.plain("\n\n**REQUIRED REVIEWS:**\n☑ BSP Review: Scheduled\n☑ FBA Update: Scheduled\n☑ Medication Review: ")
        b.phi(psychiatrist, "PERSON")
        b.plain(" emergency appt ")
        b.phi(med_rev, "DATE")
        b.plain("\n☑ Safety Protocol Review: Scheduled\n☑ Incident Review Team: Scheduled\n\n**Report compiled by:** ")
        self._staff_cred(b, staff_info)
        b.plain("\n**Reviewed by:** ")
        self._staff_tuple_name_title(b, supervisor)
        b.plain("\n**Medical review:** ")
        b.phi(nurse, "PERSON")
        b.plain("\n**Report filed:** ")
        b.phi(session_info["date"], "DATE")
        b.plain(f"\n**Report ID:** INC-{datetime.today().year}-{rid}\n\n---\nEND OF INCIDENT REPORT\n")
        return b.build()
    
    def generate_post_crisis_recovery(self, client, session_info, staff_info):
        """Generate post-crisis recovery scenario"""
        supervisor = self.generate_staff_name()
        bcba = self.generate_staff_name()
        ot = self.generate_provider_name()
        slp = self.generate_provider_name()
        nurse = self.generate_provider_name()
        psychiatrist = self.generate_provider_name()
        incident_date = self.generate_date_variations(datetime.today() - timedelta(days=2))
        inc_id = random.randint(1000, 9999)
        esc_m, rst_m = random.randint(5, 8), random.randint(18, 25)
        impl1 = self.generate_date_variations(datetime.today() - timedelta(days=1))
        impl2 = self.generate_date_variations(datetime.today() - timedelta(days=1))
        bsp_impl = self.generate_date_variations(datetime.today() - timedelta(days=1))
        psych_em = self.generate_date_variations(datetime.today() - timedelta(days=1))
        med_adj = random.choice(["Increased evening anxiety medication", "Added PRN protocol", "Dosage adjustment made"])
        psych_next = self.generate_date_variations(datetime.today() + timedelta(days=random.randint(20, 35)))
        calm_done = self.generate_date_variations(datetime.today() - timedelta(days=1))
        mon_end = self.generate_date_variations(datetime.today() + timedelta(days=14))
        brk_n = random.randint(2, 4)
        acc_n = random.randint(75, 90)
        ns_mon = self.generate_date_variations(datetime.today() + timedelta(days=14))
        ns_psy = self.generate_date_variations(datetime.today() + timedelta(days=random.randint(20, 35)))
        fba_tgt = self.generate_date_variations(datetime.today() + timedelta(days=random.randint(8, 14)))
        tp_upd = self.generate_date_variations(datetime.today() - timedelta(days=1))
        next_rec = self.generate_date_variations(datetime.today() + timedelta(days=7))
        b = NoteBuilder()
        b.plain("# UCP POST-CRISIS RECOVERY SESSION NOTE\n\n**Client:** ")
        b.phi(client["full_name"], "PERSON")
        b.plain("\n**Recovery Session Date:** ")
        b.phi(session_info["date"], "DATE")
        b.plain("\n**Original Incident Date:** ")
        b.phi(incident_date, "DATE")
        b.plain("\n**Location:** ")
        b.plain(client["residential_program"])
        b.plain("\n**Staff:** ")
        self._staff_cred(b, staff_info)
        b.plain("\n**Clinical Supervisor:** ")
        self._staff_tuple_name_title(b, supervisor)
        b.plain("\n\n---\n\n## POST-CRISIS THERAPEUTIC INTERVENTION\n\n**INCIDENT REFERENCE:**\nCritical incident on ")
        b.phi(incident_date, "DATE")
        b.plain(f" at {client['residential_program']}.\nIncident Report ID: INC-{datetime.today().year}-{inc_id}\nType: Physical aggression toward peer and staff, property destruction\nDuration: Escalation {esc_m} minutes, restraint {rst_m} minutes\n\nTIME SINCE INCIDENT: 48 hours\n\n**CURRENT SESSION PURPOSE:**\n1. Therapeutic processing of incident\n2. Safety planning reinforcement\n3. Skill rebuilding for emotion regulation\n4. Relationship repair with staff and peers\n\n**SESSION ACTIVITIES:**\n\n**THERAPEUTIC PROCESSING:**\n")
        b.phi(client["first_name"], "PERSON")
        b.plain(" participated in cognitive-behavioral processing with ")
        self._staff_cred(b, staff_info)
        b.plain(".\n\nDiscussion topics:\n- Event sequence understanding using visual timeline\n- Emotional identification (anger, frustration, feeling out of control)\n- Alternative response strategies (asking for break, using calm-down space)\n- Safety understanding (why restraint was necessary)\n\n")
        b.phi(client["first_name"], "PERSON")
        b.plain("'s insight: Demonstrated good understanding of event sequence, identified trigger, \nrecognized inappropriate choice and impact on others.\n\n**SAFETY PLANNING:**\nReviewed and updated safety protocols with ")
        b.phi(client["first_name"], "PERSON")
        b.plain(".\n\n**NEW SAFETY MEASURES IMPLEMENTED:**\nFollowing incident on ")
        b.phi(incident_date, "DATE")
        b.plain(":\n1. Individual activity schedule - Implemented ")
        b.phi(impl1, "DATE")
        b.plain("\n2. Enhanced visual supports for emotion regulation - Implemented ")
        b.phi(impl2, "DATE")
        b.plain("\n3. Enhanced monitoring during peer activities (1:2 ratio)\n\n**PARENT COLLABORATION:**\nJoint session with ")
        b.phi(client["parent1_first"], "PERSON")
        b.plain(" ")
        b.phi(client["last_name"], "PERSON")
        if client["parent2_first"]:
            b.plain(" and ")
            b.phi(client["parent2_first"], "PERSON")
            b.plain(" ")
            b.phi(client["last_name"], "PERSON")
        b.plain(".\n\nParents contacted at ")
        b.phi(client["phone_number"], "PHONE")
        b.plain(" to confirm session attendance.\n\nDiscussion points:\n- Home-program consistency for emotion regulation strategies\n- Warning sign recognition (escalating voice volume, body tension, pacing)\n- De-escalation support at home (offering break space, reducing demands)\n- Communication protocols between home and program\n\n**STAFF RELATIONSHIP REPAIR:**\n")
        b.phi(client["first_name"], "PERSON")
        b.plain(" met individually with staff involved in incident.\nFacilitated by: ")
        self._staff_tuple_name_title(b, supervisor)
        b.plain("\n\nProcess included: ")
        b.phi(client["first_name"], "PERSON")
        b.plain("'s verbal apology, staff reassurance of continued support, \ndiscussion of moving forward. Staff reported positive interaction quality.\n\n**BEHAVIORAL SUPPORT PLAN UPDATES:**\nModified BSP implemented ")
        b.phi(bsp_impl, "DATE")
        b.plain(" following comprehensive review.\n\nChanges include:\n- Enhanced antecedent strategies (increased warnings before transitions)\n- Additional teaching of replacement behaviors (requesting break using visual card)\n- Updated crisis protocols (specific de-escalation sequence)\n- Modified reinforcement schedule\n\nReview team:\n- ")
        self._staff_tuple_name_title(b, bcba)
        b.plain(" (Behavior Specialist)\n- ")
        b.phi(ot, "PERSON")
        b.plain(" (Occupational Therapist)\n- ")
        b.phi(slp, "PERSON")
        b.plain(" (Speech-Language Pathologist)\n- ")
        b.phi(nurse, "PERSON")
        b.plain(" (Nursing)\n- Parents: ")
        b.phi(client["parent1_first"], "PERSON")
        b.plain(" ")
        b.phi(client["last_name"], "PERSON")
        if client["parent2_first"]:
            b.plain(", ")
            b.phi(client["parent2_first"], "PERSON")
            b.plain(" ")
            b.phi(client["last_name"], "PERSON")
        b.plain("\n\n**PSYCHIATRIC FOLLOW-UP:**\nEmergency consultation with ")
        b.phi(psychiatrist, "PERSON")
        b.plain(" on ")
        b.phi(psych_em, "DATE")
        b.plain(".\n\nMedication adjustments:\n- ")
        b.plain(med_adj)
        b.plain("\n- Continue current regimen with modifications\n\nNext psychiatric appointment: ")
        b.phi(psych_next, "DATE")
        b.plain("\n\n**SKILL REBUILDING:**\nFocus areas identified:\n1. Emotion regulation and identification\n2. Requesting breaks appropriately\n3. Appropriate peer interactions\n\nTeaching sessions scheduled:\n- Daily emotion identification practice with ")
        self._staff_cred(b, staff_info)
        b.plain("\n- Twice weekly skills practice\n- Break request training as needed throughout day\n\n**ENVIRONMENTAL MODIFICATIONS:**\nChanges made at ")
        b.plain(client["residential_program"])
        b.plain(" following incident:\n\nPhysical environment:\n- Designated \"calm corner\" with visual supports (Completed ")
        b.phi(calm_done, "DATE")
        b.plain(")\n- Additional soft seating for de-escalation space\n\nSchedule modifications:\n- Individual time for preferred activities\n- Structured peer activities with higher staff ratio for 1 week\n\n**MONITORING PROTOCOL:**\nEnhanced monitoring period: ")
        b.phi(session_info["date"], "DATE")
        b.plain(" through ")
        b.phi(mon_end, "DATE")
        b.plain(" (2 weeks)\n\nMonitoring frequency: Hourly emotion check-ins using 5-point scale\nDocumentation: Electronic incident tracking system + daily narrative notes\n\n**CHECK-IN SCHEDULE:**\nDaily check-ins with rotating staff:\n- Morning: 8:30 AM (baseline mood assessment)\n- Midday: 12:00 PM (activity participation check)\n- Afternoon: 3:00 PM (end-of-day processing)\n\n**PARENT COMMUNICATION PLAN:**\nDaily updates to ")
        b.phi(client["parent1_first"], "PERSON")
        b.plain(" ")
        b.phi(client["last_name"], "PERSON")
        b.plain(":\n- Method: Phone call\n- Time: 4:00 PM daily\n- Contact: ")
        b.phi(client["phone_number"], "PHONE")
        b.plain("\n\n**PROGRESS INDICATORS:**\nSince incident on ")
        b.phi(incident_date, "DATE")
        b.plain(f" (48 hours post-incident):\n- Zero physical aggression incidents\n- Appropriate use of break request card {brk_n} times\n- Positive peer interactions during structured activities (100% appropriate)\n- Verbal communication of emotions using 5-point scale with {acc_n}% accuracy\n\n**NEXT STEPS:**\n☑ Continue daily monitoring through ")
        b.phi(ns_mon, "DATE")
        b.plain("\n☑ BSP implementation fidelity checks (daily by supervisor)\n☑ Ongoing parent collaboration (daily calls)\n☑ Psychiatric follow-up ")
        b.phi(ns_psy, "DATE")
        b.plain("\n☑ Incident review team meeting scheduled\n☑ FBA update completion target: ")
        b.phi(fba_tgt, "DATE")
        b.plain("\n\n**DOCUMENTATION:**\nRecovery session documented by: ")
        self._staff_cred(b, staff_info)
        b.plain("\nClinical supervision: ")
        self._staff_tuple_name_title(b, supervisor)
        b.plain("\nParent consent obtained: ")
        b.phi(session_info["date"], "DATE")
        b.plain("\nTreatment plan updated: ")
        b.phi(tp_upd, "DATE")
        b.plain("\n\nSession date: ")
        b.phi(session_info["date"], "DATE")
        b.plain("\nNext recovery session: ")
        b.phi(next_rec, "DATE")
        b.plain("\n\n---\nEND OF SESSION NOTE\n")
        return b.build()
    
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
    
    # Numeric label assigned to each scenario for ML classification.
    # 0 = routine/positive  1 = mild issues  2 = crisis/severe
    SCENARIO_LABELS = {
        'exceptional_progress':   0,
        'skill_acquisition':      0,
        'positive_social':        0,
        'standard_session':       0,
        'maintenance':            0,
        'mild_challenging':       1,
        'environmental_triggers': 1,
        'medical_appointment':    1,
        'medication_monitoring':  1,
        'post_crisis_recovery':   1,
        'moderate_challenging':   2,
        'crisis_intervention':    2,
    }

    def generate_batch(self, n=150, output_dir="data/synthetic/raw",
                       annotations_path="data/annotated/annotations_generated.json",
                       documents_path="data/raw/documents.json",
                       noise_variants=0, llm_rewrite=False):
        """
        Generate batch of synthetic notes, ground-truth annotations, and documents.json.

        Parameters
        ----------
        n               : number of unique (clean) notes to generate
        output_dir      : where to save .txt files
        annotations_path: where to save ground-truth annotations JSON
        documents_path  : where to save documents JSON (for ML pipeline)
        noise_variants  : number of additional noisy copies per note (0 = no noise)
        llm_rewrite     : if True, apply LLM rewriting after noise injection
                          (requires ANTHROPIC_API_KEY env var)
        """
        # Lazy import so noise/LLM deps don't break plain generation
        injector = None
        if noise_variants > 0:
            from noise_injector import NoiseInjector
            injector = NoiseInjector()

        rewriter = None
        if llm_rewrite:
            from llm_rewriter import LLMRewriter
            rewriter = LLMRewriter()

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        ann_path = Path(annotations_path)
        ann_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path = Path(documents_path)
        doc_path.parent.mkdir(parents=True, exist_ok=True)

        total = n * (1 + noise_variants)
        print(f"\n{'='*80}")
        print(f"GENERATING {n} CLEAN + {n * noise_variants} NOISY = {total} NOTES")
        print(f"{'='*80}\n")

        scenario_counts = {s: 0 for s in self.scenarios}
        annotations = []
        documents = []
        doc_id = 0

        for i in range(1, n + 1):
            scenario = random.choices(self.scenarios, weights=self.scenario_weights)[0]
            scenario_counts[scenario] += 1

            note_text, entities = self.generate_note(scenario)

            # ── save clean note ───────────────────────────────────────────────
            doc_id += 1
            filename = output_path / f"note_{doc_id:04d}_{scenario}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(note_text)

            annotations.append({"doc_id": doc_id, "entities": entities})
            documents.append({
                "id": doc_id,
                "text": note_text,
                "label": self.SCENARIO_LABELS[scenario],
                "scenario": scenario,
                "variant": "clean",
            })

            # ── save noisy variants ───────────────────────────────────────────
            for v in range(noise_variants):
                noisy_text, noisy_ents = injector.inject(note_text, entities)

                if rewriter is not None:
                    noisy_text, noisy_ents = rewriter.rewrite(noisy_text, noisy_ents)

                doc_id += 1
                v_filename = output_path / f"note_{doc_id:04d}_{scenario}_noisy{v+1}.txt"
                with open(v_filename, "w", encoding="utf-8") as f:
                    f.write(noisy_text)

                annotations.append({"doc_id": doc_id, "entities": noisy_ents})
                documents.append({
                    "id": doc_id,
                    "text": noisy_text,
                    "label": self.SCENARIO_LABELS[scenario],
                    "scenario": scenario,
                    "variant": f"noisy_{v+1}",
                })

            if i % 10 == 0:
                print(f"  Generated {i}/{n} base notes ({doc_id} total)...")

        with open(ann_path, "w", encoding="utf-8") as f:
            json.dump(annotations, f, indent=2)

        with open(doc_path, "w", encoding="utf-8") as f:
            json.dump(documents, f, indent=2)

        print(f"\n{'='*80}")
        print(f"GENERATION COMPLETE!")
        print(f"{'='*80}")
        print(f"\nScenario Distribution (clean notes):")
        for scenario, count in scenario_counts.items():
            percentage = (count / n) * 100
            print(f"  {scenario.capitalize():25} {count:3d} notes ({percentage:5.1f}%)")

        print(f"\n  Notes saved to      : {output_path}")
        print(f"  Total files         : {doc_id}  ({n} clean + {doc_id - n} noisy)")
        print(f"  Ground truth        : {ann_path}")
        print(f"  Documents JSON      : {doc_path}")
        print(f"\n{'='*80}\n")

        return scenario_counts


def main():
    """Main execution"""
    import argparse
    parser = argparse.ArgumentParser(description="Generate synthetic ABA session notes.")
    parser.add_argument(
        "--count", type=int, default=1000,
        help="Number of unique (clean) notes to generate (default: 1000)"
    )
    parser.add_argument(
        "--noise-variants", type=int, default=2,
        help="Noisy copies per clean note via noise_injector (default: 2). "
             "Total notes = count * (1 + noise-variants). Use 0 to disable."
    )
    parser.add_argument(
        "--llm-rewrite", action="store_true",
        help="Apply LLM rewriting after noise injection (optional, requires "
             "ANTHROPIC_API_KEY). Off by default."
    )
    parser.add_argument(
        "--output-dir",   default="data/synthetic/raw"
    )
    parser.add_argument(
        "--annotations",  default="data/annotated/annotations_generated.json"
    )
    parser.add_argument(
        "--documents",    default="data/raw/documents.json"
    )
    args = parser.parse_args()

    print("\n" + "="*80)
    print("UCP SYNTHETIC ABA SESSION NOTE GENERATOR")
    print("="*80)
    print("\nInitializing generator...")

    generator = SyntheticNoteGenerator()

    total = args.count * (1 + args.noise_variants)
    print(f"\n  Clean notes       : {args.count}")
    print(f"  Noise variants    : {args.noise_variants} per note")
    print(f"  LLM rewrite       : {'yes' if args.llm_rewrite else 'no'}")
    print(f"  Total output      : {total} notes\n")

    generator.generate_batch(
        n=args.count,
        output_dir=args.output_dir,
        annotations_path=args.annotations,
        documents_path=args.documents,
        noise_variants=args.noise_variants,
        llm_rewrite=args.llm_rewrite,
    )

    print("Synthetic note generation complete!")
    print("\nNext steps:")
    print("  1. Train: python scripts/train_ner.py")
    print("  2. Detect: python scripts/run_phi_detection.py --detector deberta --test-ids data/annotated/test_ids.json")
    print("  3. Evaluate: python scripts/run_evaluation_fixed.py --test-ids data/annotated/test_ids.json")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
