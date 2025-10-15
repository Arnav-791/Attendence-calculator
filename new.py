import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter.scrolledtext import ScrolledText
import math

class AttendanceTracker:
    def __init__(self):
        self.subjects = {}
        self.timetable = {}  # {day: [(time, subject), ...]}
        self.holidays = set()
        self.attendance_records = defaultdict(list)  # {subject: [{'date': date, 'status': 'present'/'absent'}, ...]}
        self.minimum_attendance = 75  # Default minimum attendance percentage
        self.absence_reasons = {}  # {date: {'reason': reason, 'type': type}}
        self.semester_end_date = "2025-12-13"  # Semester end date
        self.initial_attendance = {}  # {subject: {'present': int, 'absent': int, 'yet_to_go': int}}
        self.data_file = "attendance_data.json"
        self.load_data()
        self.mark_weekends_as_holidays()
        
    def save_data(self):
        """Save all data to JSON file"""
        data = {
            'subjects': self.subjects,
            'timetable': {day: [(time, subject) for time, subject in classes] 
                         for day, classes in self.timetable.items()},
            'holidays': list(self.holidays),
            'attendance_records': {subject: records for subject, records in self.attendance_records.items()},
            'minimum_attendance': self.minimum_attendance,
            'absence_reasons': self.absence_reasons,
            'semester_end_date': self.semester_end_date,
            'initial_attendance': self.initial_attendance
        }
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def load_data(self):
        """Load data from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                self.subjects = data.get('subjects', {})
                self.timetable = {day: [(time, subject) for time, subject in classes] 
                                for day, classes in data.get('timetable', {}).items()}
                self.holidays = set(data.get('holidays', []))
                self.attendance_records = defaultdict(list, data.get('attendance_records', {}))
                self.minimum_attendance = data.get('minimum_attendance', 75)
                self.absence_reasons = data.get('absence_reasons', {})
                self.initial_attendance = data.get('initial_attendance', {})
                
                # Convert old format to new format if needed
                for subject_code, data in self.initial_attendance.items():
                    if 'total_classes' in data and 'attended' in data:
                        # Old format - convert to new format
                        total = data['total_classes']
                        attended = data['attended']
                        absent = total - attended
                        self.initial_attendance[subject_code] = {
                            'present': attended,
                            'absent': absent,
                            'yet_to_go': 0
                        }
                        
            except Exception as e:
                print(f"Error loading data: {e}")
                self.absence_reasons = {}
    
    def add_subject(self, subject_code, subject_name, credits=1, is_lab=False):
        """Add a new subject"""
        self.subjects[subject_code] = {
            'name': subject_name,
            'credits': credits,
            'is_lab': is_lab
        }
        self.save_data()
        
    def delete_subject(self, subject_code):
        """Delete a subject"""
        if subject_code in self.subjects:
            del self.subjects[subject_code]
            # Clean up related data
            if subject_code in self.attendance_records:
                del self.attendance_records[subject_code]
            if subject_code in self.initial_attendance:
                del self.initial_attendance[subject_code]
            # Remove from timetable
            for day in self.timetable:
                self.timetable[day] = [(time, subj) for time, subj in self.timetable[day] if subj != subject_code]
            self.save_data()
    
    def add_timetable_entry(self, day, period_slot, subject_code):
        """Add a class to the timetable"""
        if day not in self.timetable:
            self.timetable[day] = []
            
        # Check if the subject is a lab subject
        is_lab = self.subjects.get(subject_code, {}).get('is_lab', False)
        
        # Parse period slot to get time and period number
        period_info = period_slot.split(" (")[0]  # Get "Period X" part
        period_num = int(period_info.split(" ")[1])  # Get the period number
        
        # If it's a lab subject, check if the next period is available
        if is_lab:
            next_period_taken = any(time.startswith(f"Period {period_num + 1}") for time, _ in self.timetable[day])
            if period_num >= 7 or next_period_taken:
                raise ValueError("Cannot add lab subject here - requires two consecutive periods")
                
        # Remove any existing classes in these slots
        self.timetable[day] = [(t, s) for t, s in self.timetable[day] 
                              if not t.startswith(f"Period {period_num}")]
        if is_lab:
            self.timetable[day] = [(t, s) for t, s in self.timetable[day] 
                                  if not t.startswith(f"Period {period_num + 1}")]
        
        # Add the class(es)
        self.timetable[day].append((period_slot, subject_code))
        if is_lab:
            next_slot = f"Period {period_num + 1} ({self.get_period_time(period_num + 1)})"
            self.timetable[day].append((next_slot, subject_code))
            
        self.timetable[day].sort()  # Sort by time
        self.save_data()
        
    def get_period_time(self, period_num):
        """Get the time slot for a given period number"""
        period_times = {
            1: "8:30-9:25",
            2: "9:25-10:20",
            3: "10:40-11:35",
            4: "11:35-12:30",
            5: "1:25-2:20",
            6: "2:20-3:15",
            7: "3:15-4:10"
        }
        return period_times.get(period_num, "")
        
    def set_initial_attendance(self, subject_code, present, absent, yet_to_go):
        """Set initial attendance for a subject"""
        self.initial_attendance[subject_code] = {
            'present': present,
            'absent': absent,
            'yet_to_go': yet_to_go
        }
        self.save_data()

    def mark_weekends_as_holidays(self):
        """Mark all Saturdays and Sundays as holidays until semester end"""
        start_date = datetime.now().date()
        end_date = datetime.strptime(self.semester_end_date, '%Y-%m-%d').date()
        
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() >= 5:  # 5 is Saturday, 6 is Sunday
                self.holidays.add(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        self.save_data()
        
    def get_remaining_classes(self, subject_code):
        """Get the number of remaining classes for a subject until semester end"""
        end_date = datetime.strptime(self.semester_end_date, '%Y-%m-%d').date()
        current_date = datetime.now().date()
        remaining_classes = 0
        
        while current_date <= end_date:
            day_name = current_date.strftime('%A')
            date_str = current_date.strftime('%Y-%m-%d')
            
            if day_name in self.timetable and date_str not in self.holidays:
                # Count how many times this subject appears in this day's timetable
                subject_classes = sum(1 for _, subj in self.timetable[day_name] if subj == subject_code)
                remaining_classes += subject_classes
                
            current_date += timedelta(days=1)
            
        return remaining_classes

    def delete_timetable_entry(self, day, period_slot, subject_code):
        """Delete a class from the timetable"""
        if day in self.timetable:
            # Get time from period slot format or use as is
            time_to_find = period_slot
            if " (" in period_slot:
                # New format: "Period X (HH:MM-HH:MM)"
                period_info = period_slot.split(" (")[0]
                period_num = int(period_info.split(" ")[1])
                time_map = {
                    1: "08:30", 2: "09:25", 3: "10:40",
                    4: "11:35", 5: "01:25", 6: "02:20",
                    7: "03:15"
                }
                time_to_find = time_map.get(period_num)

            # Find and remove matching entries
            new_entries = []
            skip_next = False
            for i, (time, subj) in enumerate(self.timetable[day]):
                if skip_next:
                    skip_next = False
                    continue
                    
                # Check if this entry matches what we want to delete
                if (time == time_to_find or time == period_slot) and subj == subject_code:
                    # If this is a lab subject, skip the next entry too
                    if i < len(self.timetable[day]) - 1 and self.timetable[day][i + 1][1] == subject_code:
                        skip_next = True
                    continue
                new_entries.append((time, subj))

            # Update timetable
            if new_entries:
                self.timetable[day] = new_entries
            else:
                del self.timetable[day]
            
            self.save_data()
    
    def add_holiday(self, date_str):
        """Add a holiday"""
        self.holidays.add(date_str)
        self.save_data()
    
    def mark_attendance(self, subject_code, date_str, status):
        """Mark attendance for a subject on a specific date"""
        record = {'date': date_str, 'status': status}
        # Check if record already exists for this date
        existing_records = [r for r in self.attendance_records[subject_code] if r['date'] == date_str]
        if existing_records:
            # Update existing record
            for r in self.attendance_records[subject_code]:
                if r['date'] == date_str:
                    r['status'] = status
        else:
            # Add new record
            self.attendance_records[subject_code].append(record)
        self.save_data()
    
    def get_attendance_stats(self, subject_code):
        """Get attendance statistics for a subject"""
        records = self.attendance_records[subject_code]
        initial = self.initial_attendance.get(subject_code, {'present': 0, 'absent': 0, 'yet_to_go': 0})
        
        # Calculate current attendance based on actual records and initial attendance
        current_present = len([r for r in records if r['status'] == 'present']) + initial['present']
        current_absent = len([r for r in records if r['status'] == 'absent']) + initial['absent']
        remaining = self.get_remaining_classes(subject_code)
        yet_to_go = initial['yet_to_go']
        
        # Calculate total possible classes (present + absent + yet_to_go + remaining)
        total_possible = current_present + current_absent + yet_to_go
        
        # Calculate current attendance percentage based on held classes only
        current_total = current_present + current_absent
        current_percentage = (current_present / current_total) * 100 if current_total > 0 else 0
        
        # Calculate required classes needed for minimum attendance
        if total_possible > 0:
            # Formula: classes_needed = (min_attendance * total_possible - present) / 100
            min_required_present = (self.minimum_attendance * total_possible) / 100
            classes_needed = math.ceil(min_required_present - current_present)
            # Can't attend more than remaining + yet_to_go classes
            available_future = remaining + yet_to_go
            classes_needed = min(max(0, classes_needed), available_future)
        else:
            classes_needed = 0
        
        return {
            'current_present': current_present,
            'current_absent': current_absent,
            'current_total': current_total,
            'percentage': round(current_percentage, 2),
            'remaining_classes': remaining,
            'yet_to_go': yet_to_go,
            'classes_needed': classes_needed,
            'total_possible': total_possible
        }
    
    def calculate_bunkable_classes(self, subject_code):
        """Calculate how many classes can be bunked while maintaining minimum attendance"""
        stats = self.get_attendance_stats(subject_code)
        if stats['current_total'] == 0:
            return 0
        
        current_present = stats['current_present']
        total_possible = stats['total_possible']
        
        # Calculate minimum classes that need to be attended out of total possible
        min_required_present = (self.minimum_attendance / 100) * total_possible
        
        # Calculate how many more can be bunked
        max_bunkable = total_possible - min_required_present
        already_absent = stats['current_absent']
        
        can_bunk = max(0, int(max_bunkable - already_absent))
        
        return can_bunk
    
    def get_weekly_schedule(self, start_date=None):
        """Get the weekly schedule starting from a specific date"""
        if start_date is None:
            start_date = datetime.now().date()
        
        schedule = {}
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            day_name = current_date.strftime('%A')
            
            if day_name in self.timetable and current_date.strftime('%Y-%m-%d') not in self.holidays:
                schedule[current_date.strftime('%Y-%m-%d')] = {
                    'day': day_name,
                    'classes': self.timetable[day_name]
                }
        
        return schedule

class AttendanceGUI:
    def __init__(self):
        self.tracker = AttendanceTracker()
        self.root = tk.Tk()
        self.root.title("Student Attendance Tracker")
        self.root.geometry("1000x700")
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_subjects_tab()
        self.create_timetable_tab()
        self.create_attendance_tab()
        self.create_analytics_tab()
        self.create_holidays_tab()
        self.create_absence_reasons_tab()
        
        self.refresh_all()
    
    def create_subjects_tab(self):
        """Create the subjects management tab"""
        self.subjects_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.subjects_frame, text="Subjects")
        
        # Add subject form
        add_frame = ttk.LabelFrame(self.subjects_frame, text="Add New Subject")
        add_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(add_frame, text="Subject Code:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.subject_code_entry = ttk.Entry(add_frame)
        self.subject_code_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        
        ttk.Label(add_frame, text="Subject Name:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.subject_name_entry = ttk.Entry(add_frame)
        self.subject_name_entry.grid(row=0, column=3, padx=5, pady=5, sticky=tk.EW)
        
        ttk.Label(add_frame, text="Credits:").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.credits_entry = ttk.Entry(add_frame, width=10)
        self.credits_entry.grid(row=0, column=5, padx=5, pady=5)
        self.credits_entry.insert(0, "1")
        
        self.is_lab_var = tk.BooleanVar()
        ttk.Checkbutton(add_frame, text="Lab Subject", variable=self.is_lab_var).grid(row=0, column=6, padx=5, pady=5)
        
        ttk.Button(add_frame, text="Add Subject", command=self.add_subject).grid(row=0, column=7, padx=5, pady=5)
        
        add_frame.columnconfigure(1, weight=1)
        add_frame.columnconfigure(3, weight=1)
        
        # Subjects list
        list_frame = ttk.LabelFrame(self.subjects_frame, text="Current Subjects")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.subjects_tree = ttk.Treeview(list_frame, columns=('Name', 'Credits', 'Lab'), show='tree headings')
        self.subjects_tree.heading('#0', text='Subject Code')
        self.subjects_tree.heading('Name', text='Subject Name')
        self.subjects_tree.heading('Credits', text='Credits')
        self.subjects_tree.heading('Lab', text='Lab Subject')
        self.subjects_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add Delete button and Initial Attendance button
        button_frame = ttk.Frame(list_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(button_frame, text="Set Initial Attendance", 
                  command=self.set_initial_attendance_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Selected Subject", 
                  command=self.delete_subject).pack(side=tk.RIGHT)
    
    def create_timetable_tab(self):
        """Create the timetable management tab"""
        self.timetable_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.timetable_frame, text="Timetable")
        
        # Define period slots
        self.period_slots = [
            ("Period 1", "8:30-9:25"),
            ("Period 2", "9:25-10:20"),
            ("Tea Break", "10:20-10:40"),
            ("Period 3", "10:40-11:35"),
            ("Period 4", "11:35-12:30"),
            ("Lunch Break", "12:30-1:25"),
            ("Period 5", "1:25-2:20"),
            ("Period 6", "2:20-3:15"),
            ("Period 7", "3:15-4:10")
        ]
        
        # Add timetable entry form
        add_frame = ttk.LabelFrame(self.timetable_frame, text="Add Class to Timetable")
        add_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(add_frame, text="Day:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.day_combo = ttk.Combobox(add_frame, values=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
        self.day_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        
        ttk.Label(add_frame, text="Period:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        period_values = [f"{name} ({time})" for name, time in self.period_slots if "Break" not in name]
        self.period_combo = ttk.Combobox(add_frame, values=period_values, width=20)
        self.period_combo.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(add_frame, text="Subject:").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.timetable_subject_combo = ttk.Combobox(add_frame)
        self.timetable_subject_combo.grid(row=0, column=5, padx=5, pady=5, sticky=tk.EW)
        
        ttk.Button(add_frame, text="Add to Timetable", command=self.add_timetable_entry).grid(row=0, column=6, padx=5, pady=5)
        
        add_frame.columnconfigure(1, weight=1)
        add_frame.columnconfigure(5, weight=1)
        
        # Timetable display
        display_frame = ttk.LabelFrame(self.timetable_frame, text="Weekly Timetable")
        display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.timetable_tree = ttk.Treeview(display_frame, columns=('Time', 'Subject'), show='tree headings')
        self.timetable_tree.heading('#0', text='Day')
        self.timetable_tree.heading('Time', text='Time')
        self.timetable_tree.heading('Subject', text='Subject')
        self.timetable_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Delete button
        delete_frame = ttk.Frame(display_frame)
        delete_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(delete_frame, text="Delete Selected Class", command=self.delete_timetable_entry).pack(side=tk.RIGHT)
    
    def create_attendance_tab(self):
        """Create the attendance marking tab"""
        self.attendance_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.attendance_frame, text="Mark Attendance")
        
        # Quick attendance marking
        quick_frame = ttk.LabelFrame(self.attendance_frame, text="Mark Today's Attendance")
        quick_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.today_date = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        ttk.Label(quick_frame, text="Date:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(quick_frame, textvariable=self.today_date, width=15).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(quick_frame, text="Load Today's Classes", command=self.load_todays_classes).grid(row=0, column=2, padx=10, pady=5)
        
        # Today's classes frame
        self.todays_classes_frame = ttk.LabelFrame(self.attendance_frame, text="Today's Classes")
        self.todays_classes_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Manual attendance entry
        manual_frame = ttk.LabelFrame(self.attendance_frame, text="Manual Attendance Entry")
        manual_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(manual_frame, text="Subject:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.manual_subject_combo = ttk.Combobox(manual_frame)
        self.manual_subject_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        
        ttk.Label(manual_frame, text="Date:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.manual_date_entry = ttk.Entry(manual_frame, width=15)
        self.manual_date_entry.grid(row=0, column=3, padx=5, pady=5)
        self.manual_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        ttk.Label(manual_frame, text="Status:").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.status_combo = ttk.Combobox(manual_frame, values=['present', 'absent'], width=10)
        self.status_combo.grid(row=0, column=5, padx=5, pady=5)
        self.status_combo.set('present')
        
        ttk.Button(manual_frame, text="Mark Attendance", command=self.mark_manual_attendance).grid(row=0, column=6, padx=5, pady=5)
        
        manual_frame.columnconfigure(1, weight=1)
    
    def create_analytics_tab(self):
        """Create the analytics and bunkability tab"""
        self.analytics_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.analytics_frame, text="Analytics & Bunkability")
        
        # Settings frame
        settings_frame = ttk.LabelFrame(self.analytics_frame, text="Settings")
        settings_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(settings_frame, text="Minimum Attendance %:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.min_attendance_var = tk.StringVar(value=str(self.tracker.minimum_attendance))
        min_attendance_entry = ttk.Entry(settings_frame, textvariable=self.min_attendance_var, width=10)
        min_attendance_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(settings_frame, text="Update", command=self.update_min_attendance).grid(row=0, column=2, padx=5, pady=5)
        
        # Analytics display
        analytics_display_frame = ttk.LabelFrame(self.analytics_frame, text="Attendance Analytics")
        analytics_display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.analytics_text = ScrolledText(analytics_display_frame, wrap=tk.WORD, font=('Consolas', 10))
        self.analytics_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Button(analytics_display_frame, text="Refresh Analytics", command=self.refresh_analytics).pack(pady=5)
    
    def create_holidays_tab(self):
        """Create the holidays management tab"""
        self.holidays_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.holidays_frame, text="Holidays")
        
        # Add holiday form
        add_frame = ttk.LabelFrame(self.holidays_frame, text="Add Holiday")
        add_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(add_frame, text="Holiday Date (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.holiday_date_entry = ttk.Entry(add_frame, width=15)
        self.holiday_date_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(add_frame, text="Add Holiday", command=self.add_holiday).grid(row=0, column=2, padx=5, pady=5)
        
        # Holidays list
        list_frame = ttk.LabelFrame(self.holidays_frame, text="Holidays List")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.holidays_listbox = tk.Listbox(list_frame)
        self.holidays_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Button(list_frame, text="Remove Selected", command=self.remove_holiday).pack(pady=5)
    
    def add_subject(self):
        """Add a new subject"""
        code = self.subject_code_entry.get().strip()
        name = self.subject_name_entry.get().strip()
        try:
            credits = int(self.credits_entry.get().strip())
        except ValueError:
            credits = 1
        
        if not code or not name:
            messagebox.showerror("Error", "Please enter both subject code and name")
            return
        
        is_lab = self.is_lab_var.get()
        self.tracker.add_subject(code, name, credits, is_lab)
        self.subject_code_entry.delete(0, tk.END)
        self.subject_name_entry.delete(0, tk.END)
        self.credits_entry.delete(0, tk.END)
        self.credits_entry.insert(0, "1")
        self.is_lab_var.set(False)
        
        self.refresh_all()
        messagebox.showinfo("Success", f"Subject {code} added successfully!")
    
    def delete_subject(self):
        """Delete selected subject"""
        selection = self.subjects_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a subject to delete")
            return
        
        subject_code = self.subjects_tree.item(selection[0])['text']
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete subject {subject_code}?\nThis will also delete all attendance records for this subject."):
            self.tracker.delete_subject(subject_code)
            self.refresh_all()
            messagebox.showinfo("Success", f"Subject {subject_code} deleted successfully!")
    
    def add_timetable_entry(self):
        """Add entry to timetable"""
        day = self.day_combo.get()
        period = self.period_combo.get()
        subject = self.timetable_subject_combo.get()
        
        if not day or not period or not subject:
            messagebox.showerror("Error", "Please fill all fields")
            return
        
        try:
            self.tracker.add_timetable_entry(day, period, subject)
            self.day_combo.set('')
            self.period_combo.set('')
            self.timetable_subject_combo.set('')
            
            self.refresh_timetable()
            messagebox.showinfo("Success", f"Class added to {day} at {period}")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
    
    def load_todays_classes(self):
        """Load today's classes for quick attendance marking"""
        # Clear previous widgets
        for widget in self.todays_classes_frame.winfo_children():
            widget.destroy()
        
        date = self.today_date.get()
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
            day_name = date_obj.strftime('%A')
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
            return
        
        if day_name not in self.tracker.timetable:
            ttk.Label(self.todays_classes_frame, text="No classes scheduled for this day").pack(pady=10)
            return
        
        if date in self.tracker.holidays:
            ttk.Label(self.todays_classes_frame, text="This is a holiday - no classes").pack(pady=10)
            return
        
        classes = self.tracker.timetable[day_name]
        self.attendance_vars = {}
        
        for i, (time, subject_code) in enumerate(classes):
            frame = ttk.Frame(self.todays_classes_frame)
            frame.pack(fill=tk.X, padx=5, pady=2)
            
            subject_name = self.tracker.subjects.get(subject_code, {}).get('name', subject_code)
            ttk.Label(frame, text=f"{time} - {subject_code} ({subject_name})", width=40).pack(side=tk.LEFT, padx=5)
            
            var = tk.StringVar(value='present')
            self.attendance_vars[(subject_code, date)] = var
            
            ttk.Radiobutton(frame, text="Present", variable=var, value='present').pack(side=tk.LEFT, padx=5)
            ttk.Radiobutton(frame, text="Absent", variable=var, value='absent').pack(side=tk.LEFT, padx=5)
        
        if classes:
            ttk.Button(self.todays_classes_frame, text="Mark All Attendance", 
                      command=lambda: self.mark_all_attendance(date)).pack(pady=10)
    
    def mark_all_attendance(self, date):
        """Mark attendance for all classes in a day"""
        for (subject_code, date_key), var in self.attendance_vars.items():
            if date_key == date:
                self.tracker.mark_attendance(subject_code, date, var.get())
        
        messagebox.showinfo("Success", "Attendance marked for all classes!")
        self.refresh_analytics()
    
    def mark_manual_attendance(self):
        """Mark attendance manually"""
        subject = self.manual_subject_combo.get()
        date = self.manual_date_entry.get().strip()
        status = self.status_combo.get()
        
        if not subject or not date or not status:
            messagebox.showerror("Error", "Please fill all fields")
            return
        
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
            return
        
        self.tracker.mark_attendance(subject, date, status)
        messagebox.showinfo("Success", f"Attendance marked: {subject} - {status} on {date}")
        self.refresh_analytics()
    
    def add_holiday(self):
        """Add a holiday"""
        date = self.holiday_date_entry.get().strip()
        
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
            return
        
        self.tracker.add_holiday(date)
        self.holiday_date_entry.delete(0, tk.END)
        self.refresh_holidays()
        messagebox.showinfo("Success", f"Holiday added: {date}")
    
    def remove_holiday(self):
        """Remove selected holiday"""
        selection = self.holidays_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a holiday to remove")
            return
        
        holiday = self.holidays_listbox.get(selection[0])
        self.tracker.holidays.discard(holiday)
        self.tracker.save_data()
        self.refresh_holidays()
        messagebox.showinfo("Success", f"Holiday removed: {holiday}")
    
    def update_min_attendance(self):
        """Update minimum attendance percentage"""
        try:
            min_att = float(self.min_attendance_var.get())
            if 0 <= min_att <= 100:
                self.tracker.minimum_attendance = min_att
                self.tracker.save_data()
                messagebox.showinfo("Success", f"Minimum attendance updated to {min_att}%")
                self.refresh_analytics()
            else:
                messagebox.showerror("Error", "Percentage must be between 0 and 100")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")
    
    def refresh_subjects(self):
        """Refresh subjects display"""
        for item in self.subjects_tree.get_children():
            self.subjects_tree.delete(item)
        
        for code, info in self.tracker.subjects.items():
            is_lab = info.get('is_lab', False)
            self.subjects_tree.insert('', 'end', text=code, 
                                   values=(info['name'], info['credits'], 'Yes' if is_lab else 'No'))
        
        # Update combo boxes
        subject_codes = list(self.tracker.subjects.keys())
        self.timetable_subject_combo['values'] = subject_codes
        self.manual_subject_combo['values'] = subject_codes
    
    def delete_timetable_entry(self):
        """Delete selected timetable entry"""
        selection = self.timetable_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a class to delete")
            return
            
        item = self.timetable_tree.item(selection[0])
        parent_id = self.timetable_tree.parent(selection[0])
        
        # If no parent, it's a day item, not a class
        if not parent_id:
            messagebox.showwarning("Warning", "Please select a specific class, not a day")
            return
            
        # Get the day and class details
        day = self.timetable_tree.item(parent_id)['text']
        values = item['values']
        if not values or len(values) < 2:
            messagebox.showerror("Error", "Invalid selection")
            return
            
        time_slot = values[0]
        # Extract subject code from "CODE - Name" format
        subject = values[1].split(' - ')[0].strip()
        
        if messagebox.askyesno("Confirm Delete", 
                             f"Are you sure you want to delete this class?\n\n"
                             f"Day: {day}\n"
                             f"Time: {time_slot}\n"
                             f"Subject: {subject}"):
            try:
                self.tracker.delete_timetable_entry(day, time_slot, subject)
                self.refresh_timetable()
                messagebox.showinfo("Success", "Class deleted successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete class: {str(e)}")
    
    def refresh_timetable(self):
        """Refresh timetable display"""
        for item in self.timetable_tree.get_children():
            self.timetable_tree.delete(item)
        
        # Time format mapping
        time_to_period = {
            "08:30": "Period 1 (8:30-9:25)",
            "09:25": "Period 2 (9:25-10:20)",
            "10:40": "Period 3 (10:40-11:35)",
            "11:35": "Period 4 (11:35-12:30)",
            "01:25": "Period 5 (1:25-2:20)",
            "02:20": "Period 6 (2:20-3:15)",
            "03:15": "Period 7 (3:15-4:10)"
        }
        
        for day, classes in self.tracker.timetable.items():
            day_item = self.timetable_tree.insert('', 'end', text=day)
            for time, subject in classes:
                # Convert old time format to new period format if needed
                display_time = time_to_period.get(time, time)
                subject_name = self.tracker.subjects.get(subject, {}).get('name', subject)
                self.timetable_tree.insert(day_item, 'end', text='', values=(display_time, f"{subject} - {subject_name}"))
    
    def refresh_holidays(self):
        """Refresh holidays display"""
        self.holidays_listbox.delete(0, tk.END)
        for holiday in sorted(self.tracker.holidays):
            self.holidays_listbox.insert(tk.END, holiday)
    
    def set_initial_attendance_dialog(self):
        """Show dialog to set initial attendance"""
        selection = self.subjects_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a subject")
            return
            
        subject_code = self.subjects_tree.item(selection[0])['text']
        subject_name = self.subjects_tree.item(selection[0])['values'][0]
        
        # Create a dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Set Initial Attendance - {subject_code}")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        
        # Add form elements
        ttk.Label(dialog, text=f"Subject: {subject_code} - {subject_name}", font=('Helvetica', 11, 'bold')).pack(pady=10)
        
        form_frame = ttk.Frame(dialog)
        form_frame.pack(pady=10)
        
        # Present Classes
        ttk.Label(form_frame, text="Present Classes:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        present_entry = ttk.Entry(form_frame, width=10)
        present_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Absent Classes
        ttk.Label(form_frame, text="Absent Classes:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        absent_entry = ttk.Entry(form_frame, width=10)
        absent_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Yet to Go Classes
        ttk.Label(form_frame, text="Yet to Go Classes:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        yet_to_go_entry = ttk.Entry(form_frame, width=10)
        yet_to_go_entry.grid(row=2, column=1, padx=5, pady=5)
        
        # Add explanations
        ttk.Label(form_frame, text="(Classes already attended)", font=('Helvetica', 8)).grid(row=0, column=2, padx=5, pady=5, sticky='w')
        ttk.Label(form_frame, text="(Classes missed/bunked)", font=('Helvetica', 8)).grid(row=1, column=2, padx=5, pady=5, sticky='w')
        ttk.Label(form_frame, text="(Future classes scheduled)", font=('Helvetica', 8)).grid(row=2, column=2, padx=5, pady=5, sticky='w')
        
        # Total Classes Held (auto-calculated)
        held_var = tk.StringVar(value="0")
        ttk.Label(form_frame, text="Total Classes Held:").grid(row=3, column=0, padx=5, pady=5, sticky='e')
        ttk.Label(form_frame, textvariable=held_var, font=('Helvetica', 10, 'bold')).grid(row=3, column=1, padx=5, pady=5)
        ttk.Label(form_frame, text="(Present + Absent)", font=('Helvetica', 8)).grid(row=3, column=2, padx=5, pady=5, sticky='w')
        
        # Current Attendance Percentage
        percentage_var = tk.StringVar(value="0%")
        ttk.Label(form_frame, text="Current Attendance:").grid(row=4, column=0, padx=5, pady=5, sticky='e')
        ttk.Label(form_frame, textvariable=percentage_var, font=('Helvetica', 10, 'bold')).grid(row=4, column=1, padx=5, pady=5)
        
        def update_calculations(*args):
            try:
                present = int(present_entry.get() or 0)
                absent = int(absent_entry.get() or 0)
                yet_to_go = int(yet_to_go_entry.get() or 0)
                
                held = present + absent
                held_var.set(str(held))
                
                if held > 0:
                    percentage = (present / held) * 100
                    percentage_var.set(f"{percentage:.2f}%")
                else:
                    percentage_var.set("0%")
                    
            except ValueError:
                held_var.set("Invalid")
                percentage_var.set("Invalid")
        
        # Bind updates to entry changes
        present_entry.bind('<KeyRelease>', update_calculations)
        absent_entry.bind('<KeyRelease>', update_calculations)
        yet_to_go_entry.bind('<KeyRelease>', update_calculations)
        
        # Set current values if they exist
        current = self.tracker.initial_attendance.get(subject_code, {'present': 0, 'absent': 0, 'yet_to_go': 0})
        
        present_entry.insert(0, str(current['present']))
        absent_entry.insert(0, str(current['absent']))
        yet_to_go_entry.insert(0, str(current['yet_to_go']))
        update_calculations()
        
        def save_attendance():
            try:
                present = int(present_entry.get() or 0)
                absent = int(absent_entry.get() or 0)
                yet_to_go = int(yet_to_go_entry.get() or 0)
                
                if present < 0 or absent < 0 or yet_to_go < 0:
                    messagebox.showerror("Error", "Values cannot be negative")
                    return
                
                self.tracker.set_initial_attendance(subject_code, present, absent, yet_to_go)
                self.refresh_analytics()
                dialog.destroy()
                messagebox.showinfo("Success", "Initial attendance saved")
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers")
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Save", command=save_attendance).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
    
    def refresh_analytics(self):
        """Refresh analytics display"""
        self.analytics_text.delete(1.0, tk.END)
        
        output = "=== ATTENDANCE ANALYTICS ===\n\n"
        output += f"Minimum Required Attendance: {self.tracker.minimum_attendance}%\n\n"
        
        if not self.tracker.subjects:
            output += "No subjects added yet.\n"
            self.analytics_text.insert(1.0, output)
            return
        
        bunkable_subjects = []
        critical_subjects = []
        
        for subject_code, subject_info in self.tracker.subjects.items():
            stats = self.tracker.get_attendance_stats(subject_code)
            bunkable = self.tracker.calculate_bunkable_classes(subject_code)
            
            output += f"Subject: {subject_code} - {subject_info['name']}\n"
            output += f"  Classes Held: {stats['current_total']} (Present: {stats['current_present']}, Absent: {stats['current_absent']})\n"
            output += f"  Current Attendance: {stats['percentage']:.2f}% (based on {stats['current_total']} held classes)\n"
            output += f"  Yet to Go Classes: {stats['yet_to_go']}\n"
            output += f"  Total Possible Classes: {stats['total_possible']} (Present + Absent + Yet to Go)\n"
            output += f"  Classes Needed for {self.tracker.minimum_attendance}%: {stats['classes_needed']} (out of {stats['yet_to_go']} available)\n"
            
            if stats['current_total'] == 0:
                output += f"  Status: ⚪ NO DATA (Set initial attendance first)\n"
            elif stats['classes_needed'] == 0:
                output += f"  Status: ✅ SAFE (Can bunk {bunkable} more classes)\n"
                if bunkable > 0:
                    bunkable_subjects.append((subject_code, subject_info['name'], bunkable))
            else:
                remaining_classes = stats['yet_to_go']
                if remaining_classes == 0:
                    output += f"  Status: 💀 FUCKED (No future classes available, but need {stats['classes_needed']} more)\n"
                    critical_subjects.append((subject_code, subject_info['name'], stats['classes_needed']))
                    continue
                needed_percentage = (stats['classes_needed'] / remaining_classes) * 100
                if needed_percentage >= 100:
                    output += f"  Status: � FUCKED (Need ALL {remaining_classes} classes + {stats['classes_needed'] - remaining_classes} more somehow)\n"
                elif needed_percentage >= 90:
                    output += f"  Status: 🚫 CAN'T BUNK (Need {stats['classes_needed']} out of {remaining_classes} classes - {needed_percentage:.1f}%)\n"
                elif needed_percentage >= 80:
                    output += f"  Status: 🚨 CRITICAL (Need {stats['classes_needed']} out of {remaining_classes} classes - {needed_percentage:.1f}%)\n"
                elif needed_percentage >= 70:
                    output += f"  Status: ⚠️ ATTENTION (Need {stats['classes_needed']} out of {remaining_classes} classes - {needed_percentage:.1f}%)\n"
                elif needed_percentage >= 60:
                    output += f"  Status: 🟡 MEDIUM (Need {stats['classes_needed']} out of {remaining_classes} classes - {needed_percentage:.1f}%)\n"
                else:
                    output += f"  Status: ✅ SAFE (Need {stats['classes_needed']} out of {remaining_classes} classes - {needed_percentage:.1f}%)\n"
                if needed_percentage >= 70:
                    critical_subjects.append((subject_code, subject_info['name'], stats['classes_needed']))
            
            output += "\n"
        
        output += "=== BUNKABILITY SUMMARY ===\n\n"
        
        if bunkable_subjects:
            output += "🎯 SUBJECTS YOU CAN BUNK:\n"
            for code, name, count in sorted(bunkable_subjects, key=lambda x: x[2], reverse=True):
                output += f"  • {code} ({name}): {count} classes\n"
            output += "\n"
        
        if critical_subjects:
            output += "🚨 CRITICAL SUBJECTS (ATTEND MANDATORY):\n"
            for code, name, needed in critical_subjects:
                output += f"  • {code} ({name}): Attend next {needed} classes\n"
            output += "\n"
        
        if not bunkable_subjects and not critical_subjects:
            output += "Set initial attendance for subjects to see bunkability analysis.\n"
        
        self.analytics_text.insert(1.0, output)
    
    def create_absence_reasons_tab(self):
        """Create the absence reasons tab"""
        self.absence_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.absence_frame, text="Absence Reasons")
        
        # Add absence reason form
        add_frame = ttk.LabelFrame(self.absence_frame, text="Add Absence Reason")
        add_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(add_frame, text="Date:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.absence_date_entry = ttk.Entry(add_frame, width=15)
        self.absence_date_entry.grid(row=0, column=1, padx=5, pady=5)
        self.absence_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        ttk.Label(add_frame, text="Type:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.absence_type_combo = ttk.Combobox(add_frame, values=['Medical', 'Event', 'Personal', 'Other'])
        self.absence_type_combo.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(add_frame, text="Reason:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.absence_reason_entry = ttk.Entry(add_frame, width=60)
        self.absence_reason_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky=tk.EW)
        
        ttk.Button(add_frame, text="Add Reason", command=self.add_absence_reason).grid(row=2, column=3, padx=5, pady=5)
        
        # Absence reasons list
        list_frame = ttk.LabelFrame(self.absence_frame, text="Absence Records")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.absence_tree = ttk.Treeview(list_frame, columns=('Type', 'Reason'), show='tree headings')
        self.absence_tree.heading('#0', text='Date')
        self.absence_tree.heading('Type', text='Type')
        self.absence_tree.heading('Reason', text='Reason')
        self.absence_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Delete button
        delete_frame = ttk.Frame(list_frame)
        delete_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(delete_frame, text="Delete Selected", command=self.delete_absence_reason).pack(side=tk.RIGHT)
    
    def add_absence_reason(self):
        """Add an absence reason"""
        date = self.absence_date_entry.get().strip()
        absence_type = self.absence_type_combo.get()
        reason = self.absence_reason_entry.get().strip()
        
        if not date or not absence_type or not reason:
            messagebox.showerror("Error", "Please fill all fields")
            return
        
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
            return
        
        self.tracker.absence_reasons[date] = {
            'type': absence_type,
            'reason': reason
        }
        self.tracker.save_data()
        
        self.absence_date_entry.delete(0, tk.END)
        self.absence_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.absence_type_combo.set('')
        self.absence_reason_entry.delete(0, tk.END)
        
        self.refresh_absence_reasons()
        messagebox.showinfo("Success", f"Absence reason added for {date}")
    
    def delete_absence_reason(self):
        """Delete selected absence reason"""
        selection = self.absence_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an absence record to delete")
            return
        
        date = self.absence_tree.item(selection[0])['text']
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the absence record for {date}?"):
            del self.tracker.absence_reasons[date]
            self.tracker.save_data()
            self.refresh_absence_reasons()
            messagebox.showinfo("Success", "Absence record deleted")
    
    def refresh_absence_reasons(self):
        """Refresh absence reasons display"""
        for item in self.absence_tree.get_children():
            self.absence_tree.delete(item)
        
        for date, info in sorted(self.tracker.absence_reasons.items()):
            self.absence_tree.insert('', 'end', text=date, values=(info['type'], info['reason']))
    
    def refresh_all(self):
        """Refresh all displays"""
        self.refresh_subjects()
        self.refresh_timetable()
        self.refresh_holidays()
        self.refresh_analytics()
        self.refresh_absence_reasons()
    
    def run(self):
        """Run the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = AttendanceGUI()
    app.run()