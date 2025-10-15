import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter.scrolledtext import ScrolledText

class AttendanceTracker:
    def __init__(self):
        self.subjects = {}
        self.timetable = {}  # {day: [(time, subject), ...]}
        self.holidays = set()
        self.attendance_records = defaultdict(list)  # {subject: [{'date': date, 'status': 'present'/'absent'}, ...]}
        self.minimum_attendance = 75  # Default minimum attendance percentage
        self.data_file = "attendance_data.json"
        self.load_data()
        
    def save_data(self):
        """Save all data to JSON file"""
        data = {
            'subjects': self.subjects,
            'timetable': {day: [(time, subject) for time, subject in classes] 
                         for day, classes in self.timetable.items()},
            'holidays': list(self.holidays),
            'attendance_records': {subject: records for subject, records in self.attendance_records.items()},
            'minimum_attendance': self.minimum_attendance
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
            except Exception as e:
                print(f"Error loading data: {e}")
    
    def add_subject(self, subject_code, subject_name, credits=1):
        """Add a new subject"""
        self.subjects[subject_code] = {
            'name': subject_name,
            'credits': credits
        }
        self.save_data()
    
    def add_timetable_entry(self, day, time, subject_code):
        """Add a class to the timetable"""
        if day not in self.timetable:
            self.timetable[day] = []
        self.timetable[day].append((time, subject_code))
        self.timetable[day].sort()  # Sort by time
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
        if not records:
            return {'total': 0, 'present': 0, 'absent': 0, 'percentage': 0}
        
        total = len(records)
        present = len([r for r in records if r['status'] == 'present'])
        absent = total - present
        percentage = (present / total) * 100 if total > 0 else 0
        
        return {
            'total': total,
            'present': present,
            'absent': absent,
            'percentage': round(percentage, 2)
        }
    
    def calculate_bunkable_classes(self, subject_code):
        """Calculate how many classes can be bunked while maintaining minimum attendance"""
        stats = self.get_attendance_stats(subject_code)
        if stats['total'] == 0:
            return 0
        
        present = stats['present']
        total = stats['total']
        
        # Calculate maximum classes that can be bunked
        # Formula: (present_classes / (total_classes + future_classes)) >= min_attendance/100
        # Solving for maximum future_absent_classes
        min_ratio = self.minimum_attendance / 100
        
        if stats['percentage'] <= self.minimum_attendance:
            return 0
        
        # Calculate maximum total classes possible while maintaining minimum attendance
        max_total = present / min_ratio
        bunkable = int(max_total - total)
        
        return max(0, bunkable)
    
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
        
        ttk.Button(add_frame, text="Add Subject", command=self.add_subject).grid(row=0, column=6, padx=5, pady=5)
        
        add_frame.columnconfigure(1, weight=1)
        add_frame.columnconfigure(3, weight=1)
        
        # Subjects list
        list_frame = ttk.LabelFrame(self.subjects_frame, text="Current Subjects")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.subjects_tree = ttk.Treeview(list_frame, columns=('Name', 'Credits'), show='tree headings')
        self.subjects_tree.heading('#0', text='Subject Code')
        self.subjects_tree.heading('Name', text='Subject Name')
        self.subjects_tree.heading('Credits', text='Credits')
        self.subjects_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def create_timetable_tab(self):
        """Create the timetable management tab"""
        self.timetable_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.timetable_frame, text="Timetable")
        
        # Add timetable entry form
        add_frame = ttk.LabelFrame(self.timetable_frame, text="Add Class to Timetable")
        add_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(add_frame, text="Day:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.day_combo = ttk.Combobox(add_frame, values=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
        self.day_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        
        ttk.Label(add_frame, text="Time:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.time_entry = ttk.Entry(add_frame, width=15)
        self.time_entry.grid(row=0, column=3, padx=5, pady=5)
        self.time_entry.insert(0, "09:00")
        
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
        
        self.tracker.add_subject(code, name, credits)
        self.subject_code_entry.delete(0, tk.END)
        self.subject_name_entry.delete(0, tk.END)
        self.credits_entry.delete(0, tk.END)
        self.credits_entry.insert(0, "1")
        
        self.refresh_all()
        messagebox.showinfo("Success", f"Subject {code} added successfully!")
    
    def add_timetable_entry(self):
        """Add entry to timetable"""
        day = self.day_combo.get()
        time = self.time_entry.get().strip()
        subject = self.timetable_subject_combo.get()
        
        if not day or not time or not subject:
            messagebox.showerror("Error", "Please fill all fields")
            return
        
        self.tracker.add_timetable_entry(day, time, subject)
        self.day_combo.set('')
        self.time_entry.delete(0, tk.END)
        self.time_entry.insert(0, "09:00")
        self.timetable_subject_combo.set('')
        
        self.refresh_timetable()
        messagebox.showinfo("Success", f"Class added to {day} at {time}")
    
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
            self.subjects_tree.insert('', 'end', text=code, values=(info['name'], info['credits']))
        
        # Update combo boxes
        subject_codes = list(self.tracker.subjects.keys())
        self.timetable_subject_combo['values'] = subject_codes
        self.manual_subject_combo['values'] = subject_codes
    
    def refresh_timetable(self):
        """Refresh timetable display"""
        for item in self.timetable_tree.get_children():
            self.timetable_tree.delete(item)
        
        for day, classes in self.tracker.timetable.items():
            day_item = self.timetable_tree.insert('', 'end', text=day)
            for time, subject in classes:
                subject_name = self.tracker.subjects.get(subject, {}).get('name', subject)
                self.timetable_tree.insert(day_item, 'end', text='', values=(time, f"{subject} - {subject_name}"))
    
    def refresh_holidays(self):
        """Refresh holidays display"""
        self.holidays_listbox.delete(0, tk.END)
        for holiday in sorted(self.tracker.holidays):
            self.holidays_listbox.insert(tk.END, holiday)
    
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
            output += f"  Total Classes: {stats['total']}\n"
            output += f"  Present: {stats['present']}, Absent: {stats['absent']}\n"
            output += f"  Current Attendance: {stats['percentage']:.2f}%\n"
            
            if stats['percentage'] >= self.tracker.minimum_attendance:
                output += f"  Status: ✅ SAFE (Can bunk {bunkable} more classes)\n"
                if bunkable > 0:
                    bunkable_subjects.append((subject_code, subject_info['name'], bunkable))
            else:
                classes_needed = max(0, int((self.tracker.minimum_attendance * stats['total'] - stats['present'] * 100) / (100 - self.tracker.minimum_attendance)))
                output += f"  Status: ⚠️  CRITICAL (Need to attend next {classes_needed} classes)\n"
                critical_subjects.append((subject_code, subject_info['name'], classes_needed))
            
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
            output += "No attendance data available yet.\n"
        
        self.analytics_text.insert(1.0, output)
    
    def refresh_all(self):
        """Refresh all displays"""
        self.refresh_subjects()
        self.refresh_timetable()
        self.refresh_holidays()
        self.refresh_analytics()
    
    def run(self):
        """Run the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = AttendanceGUI()
    app.run()