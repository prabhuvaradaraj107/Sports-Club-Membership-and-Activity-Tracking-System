"""
FINAL GUI + SIMPLE LOGIN
Sports Club Management System
"""

import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import mysql.connector

# ---------------------------------------
# DB CONFIG
# ---------------------------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "1234",
    "database": "sportsclubdb"
}

# ---------------------------------------
# DB UTILS
# ---------------------------------------
def db():
    return mysql.connector.connect(**DB_CONFIG)

def run_select(q, args=None):
    conn = db()
    cur = conn.cursor()
    try:
        cur.execute(q, args or ())
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()
    return rows

def run_dml(q, args=None):
    conn = db()
    cur = conn.cursor()
    try:
        cur.execute(q, args or ())
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()

def call_proc(name, args=None):
    conn = db()
    cur = conn.cursor()
    try:
        cur.callproc(name, args or ())
        result = []
        for r in cur.stored_results():
            result.extend(r.fetchall())
        return True, result
    except Exception as e:
        return False, str(e)
    finally:
        cur.close()
        conn.close()

def call_func(q, args=None):
    conn = db()
    cur = conn.cursor()
    try:
        cur.execute(q, args or ())
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        cur.close()
        conn.close()


# ---------------------------------------
# INPUT VALIDATION
# ---------------------------------------
def validate_entries(entry_dict):
    for key, widget in entry_dict.items():
        if widget.get().strip() == "":
            messagebox.showwarning("Input Required", f"Please enter value for: {key}")
            return False
    return True



# =============================================================================
# MAIN WINDOW (YOUR GUI — UNCHANGED)
# =============================================================================
class App(ttk.Window):
    def __init__(self):
        super().__init__(themename="flatly")
        self.title("Sports Club Management System")
        self.geometry("1400x850")

        tabs = ttk.Notebook(self, bootstyle="info")
        tabs.pack(fill="both", expand=True, padx=10, pady=10)

        tabs.add(MemberTab(tabs), text="Members")
        tabs.add(PaymentTab(tabs), text="Payments")
        tabs.add(CoachActivityTab(tabs), text="Coaches / Activities")
        tabs.add(EventParticipationTab(tabs), text="Events / Participation")
        tabs.add(ReportsTab(tabs), text="Procedures / Functions")


# =============================================================================
# MEMBER TAB
# =============================================================================
class MemberTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.entries = {}
        self.build()

    def build(self):
        box = ttk.Labelframe(self, text="Member Details", bootstyle="primary")
        box.pack(fill=X, padx=10, pady=10)

        fields = ["MemberID","Name","Age","Gender","ContactNo","Email","MembershipType","JoinDate"]

        for i, f in enumerate(fields):
            ttk.Label(box, text=f).grid(row=i//4, column=(i%4)*2)
            e = ttk.Entry(box, width=20)
            e.grid(row=i//4, column=(i%4)*2 + 1, padx=4, pady=6)
            self.entries[f] = e

        ttk.Button(box, text="Add", command=self.add, bootstyle=SUCCESS).grid(row=3, column=0)
        ttk.Button(box, text="Update", command=self.update, bootstyle=WARNING).grid(row=3, column=1)
        ttk.Button(box, text="Delete", command=self.delete, bootstyle=DANGER).grid(row=3, column=2)
        ttk.Button(box, text="Refresh", command=self.load, bootstyle=INFO).grid(row=3, column=3)
        ttk.Button(box, text="Show Member Log", command=self.show_logs, bootstyle=SECONDARY).grid(row=3, column=4)

        self.tree = ttk.Treeview(
            self,
            columns=("MemberID","Name","Age","Gender","ContactNo","Email","MembershipType","JoinDate"),
            show="headings"
        )
        for c in self.tree["columns"]:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=160, anchor="center")

        self.tree.pack(fill=BOTH, expand=True)
        self.tree.bind("<Double-1>", self.fill_form)
        self.load()

    def fill_form(self, _):
        sel = self.tree.focus()
        if not sel: return
        data = self.tree.item(sel)["values"]
        for i, key in enumerate(self.entries.keys()):
            self.entries[key].delete(0, tk.END)
            if i < len(data): self.entries[key].insert(0, data[i])

    def load(self):
        self.tree.delete(*self.tree.get_children())
        for r in run_select("SELECT MemberID,Name,Age,Gender,ContactNo,Email,MembershipType,JoinDate FROM Member"):
            self.tree.insert("", tk.END, values=r)

    def add(self):
        if not validate_entries(self.entries): return
        vals = tuple(self.entries[k].get() for k in self.entries)
        ok, err = run_dml("""
            INSERT INTO Member (MemberID,Name,Age,Gender,ContactNo,Email,MembershipType,JoinDate)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, vals)
        messagebox.showinfo("Success","Member Added") if ok else messagebox.showerror("Error", err)
        self.load()

    def update(self):
        if not validate_entries(self.entries): return
        vals = tuple(self.entries[k].get() for k in self.entries)
        ok, err = run_dml("""
            UPDATE Member SET Name=%s,Age=%s,Gender=%s,
            ContactNo=%s,Email=%s,MembershipType=%s,JoinDate=%s
            WHERE MemberID=%s
        """, vals[1:] + (vals[0],))
        messagebox.showinfo("Success","Member Updated") if ok else messagebox.showerror("Error", err)
        self.load()

    def delete(self):
        mid = self.entries["MemberID"].get()
        ok, err = run_dml("DELETE FROM Member WHERE MemberID=%s", (mid,))
        messagebox.showinfo("Deleted","Member Deleted") if ok else messagebox.showerror("Error", err)
        self.load()

    def show_logs(self):
        rows = run_select("SELECT LogID, MemberID, Action, LogDate FROM Member_Log ORDER BY LogDate DESC")
        win = tk.Toplevel(self)
        win.title("Member Log")

        tree = ttk.Treeview(win, columns=("LogID","MemberID","Action","LogDate"), show="headings")
        for c in ("LogID","MemberID","Action","LogDate"):
            tree.heading(c, text=c)
            tree.column(c, width=150, anchor="center")
        tree.pack(fill=BOTH, expand=True)
        for r in rows: tree.insert("", tk.END, values=r)



# =============================================================================
# PAYMENT TAB (unchanged)
# =============================================================================
class PaymentTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.entries = {}
        self.build()

    def build(self):
        box = ttk.Labelframe(self, text="Payments", bootstyle="primary")
        box.pack(fill=X, padx=10, pady=10)

        fields = ["PaymentID","MemberID","Amount","PaymentDate","PaymentMode"]
        for i,f in enumerate(fields):
            ttk.Label(box, text=f).grid(row=i//3, column=(i%3)*2)
            e = ttk.Entry(box, width=20)
            e.grid(row=i//3, column=(i%3)*2+1, padx=4, pady=6)
            self.entries[f] = e

        ttk.Button(box, text="Add", command=self.add, bootstyle=SUCCESS).grid(row=2, column=0)
        ttk.Button(box, text="Update", command=self.update, bootstyle=WARNING).grid(row=2, column=1)
        ttk.Button(box, text="Delete", command=self.delete, bootstyle=DANGER).grid(row=2, column=2)
        ttk.Button(box, text="Refresh", command=self.load, bootstyle=INFO).grid(row=2, column=3)

        self.tree = ttk.Treeview(self, columns=fields, show="headings")
        for c in fields:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=150, anchor="center")
        self.tree.pack(fill=BOTH, expand=True)
        self.tree.bind("<Double-1>", self.fill)
        self.load()

    def fill(self, _):
        sel = self.tree.focus()
        if not sel: return
        vals = self.tree.item(sel)["values"]
        for i,k in enumerate(self.entries):
            self.entries[k].delete(0, tk.END)
            if i < len(vals): self.entries[k].insert(0, vals[i])

    def load(self):
        self.tree.delete(*self.tree.get_children())
        for r in run_select("SELECT PaymentID,MemberID,Amount,PaymentDate,PaymentMode FROM Payment"):
            self.tree.insert("", tk.END, values=r)

    def add(self):
        if not validate_entries(self.entries): return
        vals = tuple(self.entries[k].get() for k in self.entries)
        ok, err = run_dml("INSERT INTO Payment VALUES (%s,%s,%s,%s,%s)", vals)
        messagebox.showinfo("Added","Payment Added") if ok else messagebox.showerror("Error", err)
        self.load()

    def update(self):
        if not validate_entries(self.entries): return
        vals = tuple(self.entries[k].get() for k in self.entries)
        ok, err = run_dml("""
            UPDATE Payment SET MemberID=%s,Amount=%s,PaymentDate=%s,PaymentMode=%s
            WHERE PaymentID=%s
        """, vals[1:] + (vals[0],))
        messagebox.showinfo("Updated","Payment Updated") if ok else messagebox.showerror("Error", err)
        self.load()

    def delete(self):
        pid = self.entries["PaymentID"].get()
        ok, err = run_dml("DELETE FROM Payment WHERE PaymentID=%s", (pid,))
        messagebox.showinfo("Deleted","Payment Deleted") if ok else messagebox.showerror("Error", err)
        self.load()



# =============================================================================
# COACH + ACTIVITY TAB (unchanged)
# =============================================================================
class CoachActivityTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.e = {}
        self.a = {}
        self.build()

    def build(self):
        # Coach UI
        cbox = ttk.Labelframe(self, text="Coach", bootstyle="primary")
        cbox.pack(fill=X, padx=10, pady=10)

        fields = ["CoachID","Name","Specialization","ContactNo","Email"]
        for i,f in enumerate(fields):
            ttk.Label(cbox, text=f).grid(row=0, column=i*2)
            e = ttk.Entry(cbox, width=20)
            e.grid(row=0, column=i*2+1, padx=6, pady=4)
            self.e[f] = e

        ttk.Button(cbox, text="Add", command=self.add_c, bootstyle=SUCCESS).grid(row=1, column=0)
        ttk.Button(cbox, text="Update", command=self.up_c, bootstyle=WARNING).grid(row=1, column=1)
        ttk.Button(cbox, text="Delete", command=self.del_c, bootstyle=DANGER).grid(row=1, column=2)
        ttk.Button(cbox, text="Refresh", command=self.load_c, bootstyle=INFO).grid(row=1, column=3)

        self.tree = ttk.Treeview(self, columns=fields, show="headings")
        for c in fields:
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor="center", width=140)
        self.tree.pack(fill=X, expand=True)
        self.tree.bind("<Double-1>", self.fill_c)
        self.load_c()

        # Activity UI
        abox = ttk.Labelframe(self, text="Activity", bootstyle="primary")
        abox.pack(fill=X, padx=10, pady=10)

        fields = ["ActivityID","ActivityName","Description","CoachID"]
        for i,f in enumerate(fields):
            ttk.Label(abox, text=f).grid(row=0, column=i*2)
            e = ttk.Entry(abox, width=20)
            e.grid(row=0, column=i*2+1, padx=6, pady=4)
            self.a[f] = e

        ttk.Button(abox, text="Add", command=self.add_a, bootstyle=SUCCESS).grid(row=1, column=0)
        ttk.Button(abox, text="Update", command=self.up_a, bootstyle=WARNING).grid(row=1, column=1)
        ttk.Button(abox, text="Delete", command=self.del_a, bootstyle=DANGER).grid(row=1, column=2)
        ttk.Button(abox, text="Refresh", command=self.load_a, bootstyle=INFO).grid(row=1, column=3)

        self.tree2 = ttk.Treeview(self, columns=fields, show="headings")
        for c in fields:
            self.tree2.heading(c, text=c)
            self.tree2.column(c, anchor="center", width=140)
        self.tree2.pack(fill=BOTH, expand=True)
        self.tree2.bind("<Double-1>", self.fill_a)
        self.load_a()

    # COACH
    def load_c(self):
        self.tree.delete(*self.tree.get_children())
        for r in run_select("SELECT CoachID,Name,Specialization,ContactNo,Email FROM Coach"):
            self.tree.insert("", tk.END, values=r)

    def fill_c(self, _):
        sel = self.tree.focus()
        if not sel: return
        vals = self.tree.item(sel)["values"]
        for i,k in enumerate(self.e):
            self.e[k].delete(0, tk.END)
            self.e[k].insert(0, vals[i])

    def add_c(self):
        if not validate_entries(self.e): return
        vals = tuple(self.e[k].get() for k in self.e)
        ok, err = run_dml("INSERT INTO Coach VALUES (%s,%s,%s,%s,%s)", vals)
        messagebox.showinfo("Added","Coach Added") if ok else messagebox.showerror("Error", err)
        self.load_c()

    def up_c(self):
        if not validate_entries(self.e): return
        v = tuple(self.e[k].get() for k in self.e)
        ok, err = run_dml(
            "UPDATE Coach SET Name=%s,Specialization=%s,ContactNo=%s,Email=%s WHERE CoachID=%s",
            v[1:] + (v[0],)
        )
        messagebox.showinfo("Updated","Coach Updated") if ok else messagebox.showerror("Error", err)
        self.load_c()

    def del_c(self):
        cid = self.e["CoachID"].get()
        ok, err = run_dml("DELETE FROM Coach WHERE CoachID=%s", (cid,))
        messagebox.showinfo("Deleted","Coach Deleted") if ok else messagebox.showerror("Error", err)
        self.load_c()

    # ACTIVITY
    def load_a(self):
        self.tree2.delete(*self.tree2.get_children())
        for r in run_select("SELECT ActivityID,ActivityName,Description,CoachID FROM Activity"):
            self.tree2.insert("", tk.END, values=r)

    def fill_a(self, _):
        sel = self.tree2.focus()
        if not sel: return
        vals = self.tree2.item(sel)["values"]
        for i,k in enumerate(self.a):
            self.a[k].delete(0, tk.END)
            self.a[k].insert(0, vals[i])

    def add_a(self):
        if not validate_entries(self.a): return
        vals = tuple(self.a[k].get() for k in self.a)
        ok, err = run_dml("INSERT INTO Activity VALUES (%s,%s,%s,%s)", vals)
        messagebox.showinfo("Added","Activity Added") if ok else messagebox.showerror("Error", err)
        self.load_a()

    def up_a(self):
        if not validate_entries(self.a): return
        v = tuple(self.a[k].get() for k in self.a)
        ok, err = run_dml("""
            UPDATE Activity SET ActivityName=%s,Description=%s,CoachID=%s WHERE ActivityID=%s
        """, v[1:] + (v[0],))
        messagebox.showinfo("Updated","Activity Updated") if ok else messagebox.showerror("Error", err)
        self.load_a()

    def del_a(self):
        aid = self.a["ActivityID"].get()
        ok, err = run_dml("DELETE FROM Activity WHERE ActivityID=%s", (aid,))
        messagebox.showinfo("Deleted","Activity Deleted") if ok else messagebox.showerror("Error", err)
        self.load_a()



# =============================================================================
# EVENT + PARTICIPATION TAB (unchanged)
# =============================================================================
class EventParticipationTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.e = {}
        self.p = {}
        self.build()

    def build(self):
        # EVENT
        box = ttk.Labelframe(self, text="Event", bootstyle="primary")
        box.pack(fill=X, padx=10, pady=10)

        fields = ["EventID","EventName","Date","Location","ActivityID"]
        for i,f in enumerate(fields):
            ttk.Label(box, text=f).grid(row=0, column=i*2)
            e = ttk.Entry(box, width=20)
            e.grid(row=0, column=i*2+1, padx=6, pady=4)
            self.e[f] = e

        ttk.Button(box, text="Add", command=self.add_e, bootstyle=SUCCESS).grid(row=1, column=0)
        ttk.Button(box, text="Update", command=self.up_e, bootstyle=WARNING).grid(row=1, column=1)
        ttk.Button(box, text="Delete", command=self.del_e, bootstyle=DANGER).grid(row=1, column=2)
        ttk.Button(box, text="Refresh", command=self.load_e, bootstyle=INFO).grid(row=1, column=3)

        self.tree = ttk.Treeview(self, columns=fields, show="headings")
        for c in fields:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=160, anchor="center")
        self.tree.pack(fill=X, expand=True)
        self.tree.bind("<Double-1>", self.fill_e)
        self.load_e()

        # PARTICIPATION
        pbox = ttk.Labelframe(self, text="Participation", bootstyle="primary")
        pbox.pack(fill=X, padx=10, pady=10)

        fields = ["ParticipationID","MemberID","EventID","Result"]
        for i,f in enumerate(fields):
            ttk.Label(pbox, text=f).grid(row=0, column=i*2)
            e = ttk.Entry(pbox, width=20)
            e.grid(row=0, column=i*2+1, padx=6, pady=4)
            self.p[f] = e

        ttk.Button(pbox, text="Add", command=self.add_p, bootstyle=SUCCESS).grid(row=1, column=0)
        ttk.Button(pbox, text="Update", command=self.up_p, bootstyle=WARNING).grid(row=1, column=1)
        ttk.Button(pbox, text="Delete", command=self.del_p, bootstyle=DANGER).grid(row=1, column=2)
        ttk.Button(pbox, text="Refresh", command=self.load_p, bootstyle=INFO).grid(row=1, column=3)

        self.tree2 = ttk.Treeview(self, columns=fields, show="headings")
        for c in fields:
            self.tree2.heading(c, text=c)
            self.tree2.column(c, width=160, anchor="center")
        self.tree2.pack(fill=BOTH, expand=True)
        self.tree2.bind("<Double-1>", self.fill_p)
        self.load_p()

    # EVENT CRUD
    def load_e(self):
        self.tree.delete(*self.tree.get_children())
        for r in run_select("SELECT EventID,EventName,Date,Location,ActivityID FROM Event"):
            self.tree.insert("", tk.END, values=r)

    def fill_e(self, _):
        sel = self.tree.focus()
        if not sel: return
        vals = self.tree.item(sel)["values"]
        for i,k in enumerate(self.e):
            self.e[k].delete(0, tk.END)
            self.e[k].insert(0, vals[i])

    def add_e(self):
        if not validate_entries(self.e): return
        v = tuple(self.e[k].get() for k in self.e)
        ok, err = run_dml("INSERT INTO Event VALUES (%s,%s,%s,%s,%s)", v)
        messagebox.showinfo("Added","Event Added") if ok else messagebox.showerror("Error", err)
        self.load_e()

    def up_e(self):
        if not validate_entries(self.e): return
        v = tuple(self.e[k].get() for k in self.e)
        ok, err = run_dml("""
            UPDATE Event SET EventName=%s,Date=%s,Location=%s,ActivityID=%s WHERE EventID=%s
        """, v[1:] + (v[0],))
        messagebox.showinfo("Updated","Event Updated") if ok else messagebox.showerror("Error", err)
        self.load_e()

    def del_e(self):
        eid = self.e["EventID"].get()
        ok, err = run_dml("DELETE FROM Event WHERE EventID=%s", (eid,))
        messagebox.showinfo("Deleted","Event Deleted") if ok else messagebox.showerror("Error", err)
        self.load_e()

    # PARTICIPATION CRUD
    def load_p(self):
        self.tree2.delete(*self.tree2.get_children())
        for r in run_select("SELECT ParticipationID,MemberID,EventID,Result FROM Participation"):
            self.tree2.insert("", tk.END, values=r)

    def fill_p(self, _):
        sel = self.tree2.focus()
        if not sel: return
        vals = self.tree2.item(sel)["values"]
        for i,k in enumerate(self.p):
            self.p[k].delete(0, tk.END)
            self.p[k].insert(0, vals[i])

    def add_p(self):
        if not validate_entries(self.p): return
        v = tuple(self.p[k].get() for k in self.p)
        ok, err = run_dml("INSERT INTO Participation VALUES (%s,%s,%s,%s)", v)
        messagebox.showinfo("Added","Participation Added") if ok else messagebox.showerror("Error", err)
        self.load_p()

    def up_p(self):
        if not validate_entries(self.p): return
        v = tuple(self.p[k].get() for k in self.p)
        ok, err = run_dml("""
            UPDATE Participation SET MemberID=%s,EventID=%s,Result=%s WHERE ParticipationID=%s
        """, v[1:] + (v[0],))
        messagebox.showinfo("Updated","Participation Updated") if ok else messagebox.showerror("Error", err)
        self.load_p()

    def del_p(self):
        pid = self.p["ParticipationID"].get()
        ok, err = run_dml("DELETE FROM Participation WHERE ParticipationID=%s", (pid,))
        messagebox.showinfo("Deleted","Participation Deleted") if ok else messagebox.showerror("Error", err)
        self.load_p()



# =============================================================================
# REPORTS TAB (unchanged)
# =============================================================================
class ReportsTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.build()

    def build(self):
        box = ttk.Labelframe(self, text="Stored Procedures & Functions", bootstyle="primary")
        box.pack(fill=X, padx=10, pady=10)

        ttk.Label(box, text="Min Amount:").grid(row=0, column=0)
        self.amt = ttk.Entry(box, width=10)
        self.amt.grid(row=0, column=1)
        ttk.Button(box, text="Get High Paying Members", command=self.high, bootstyle=INFO).grid(row=0, column=2)

        ttk.Label(box, text="Event Name:").grid(row=1, column=0)
        self.evt = ttk.Entry(box, width=15)
        self.evt.grid(row=1, column=1)
        ttk.Button(box, text="Event Participation Report", command=self.rep, bootstyle=INFO).grid(row=1, column=2)

        ttk.Label(box, text="Coach Name:").grid(row=3, column=0)
        self.coachname = ttk.Entry(box, width=15)
        self.coachname.grid(row=3, column=1)
        ttk.Button(box,text="Get Activities By Coach",command=self.acbych,bootstyle=PRIMARY).grid(row=3, column=2)


        ttk.Label(box, text="MemberID:").grid(row=2, column=0)
        self.mid = ttk.Entry(box, width=15)
        self.mid.grid(row=2, column=1)

        ttk.Button(box, text="Total Payment", command=self.tp, bootstyle=SUCCESS).grid(row=2, column=2)
        ttk.Button(box, text="Participation Count", command=self.pc, bootstyle=WARNING).grid(row=2, column=3)
        ttk.Button(box, text="Is Active?", command=self.ac, bootstyle=INFO).grid(row=2, column=4)

        self.out = ttk.Treeview(self, show="headings")
        self.out.pack(fill=BOTH, expand=True, pady=10)

    def show(self, rows, cols):
        self.out.delete(*self.out.get_children())
        self.out["columns"] = cols
        for c in cols:
            self.out.heading(c, text=c)
            self.out.column(c, anchor="center", width=200)
        for r in rows:
            self.out.insert("", tk.END, values=r)

    def high(self):
        ok, res = call_proc("GetHighPayingMembers", [self.amt.get()])
        if ok: self.show(res, ("MemberID","Name","Amount"))
        else: messagebox.showerror("Error", res)

    def rep(self):
        ok, res = call_proc("EventParticipationReport", [self.evt.get()])
        if ok: self.show(res, ("EventName","MemberName","Result"))
        else: messagebox.showerror("Error", res)
    
    def acbych(self):
        ok, res = call_proc("GetActivitiesByCoach", [self.coachname.get()])
        if ok:self.show(res, ("ActivityID", "ActivityName", "Description"))
        else:messagebox.showerror("Error", res)


    def tp(self):
        r = call_func("SELECT GetTotalPayment(%s)", (self.mid.get(),))
        messagebox.showinfo("Total Payment", f"₹ {r}")

    def pc(self):
        r = call_func("SELECT GetParticipationCount(%s)", (self.mid.get(),))
        messagebox.showinfo("Participation Count", r)

    def ac(self):
        r = call_func("SELECT IsMemberActive(%s)", (self.mid.get(),))
        messagebox.showinfo("Active?", "YES" if r else "NO")



# =============================================================================
# LOGIN WINDOW (NEW PART — CLEAN & SIMPLE)
# =============================================================================
class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Login")
        self.geometry("400x300")
        self.config(bg="#f0f0f0")
        self.resizable(False, False)

        # TITLE
        title = tk.Label(self, text="Sports Club Login",
                         font=("Arial", 20, "bold"),
                         bg="#f0f0f0")
        title.pack(pady=20)

        frame = tk.Frame(self, bg="#f0f0f0")
        frame.pack(pady=10)

        tk.Label(frame, text="Username:",
                 font=("Arial", 12),
                 bg="#f0f0f0").grid(row=0, column=0, pady=10)
        self.user_entry = tk.Entry(frame, font=("Arial", 12))
        self.user_entry.grid(row=0, column=1, pady=10)

        tk.Label(frame, text="Password:",
                 font=("Arial", 12),
                 bg="#f0f0f0").grid(row=1, column=0, pady=10)
        self.pass_entry = tk.Entry(frame, show="*", font=("Arial", 12))
        self.pass_entry.grid(row=1, column=1, pady=10)

        login_btn = tk.Button(self, text="Login",
                              font=("Arial", 14),
                              width=12,
                              bg="#0078D7", fg="white",
                              command=self.check_login)
        login_btn.pack(pady=20)

    def check_login(self):
        u = self.user_entry.get().strip()
        p = self.pass_entry.get().strip()

        if u == "admin" and p == "admin123":
            self.destroy()
            app = App()
            app.mainloop()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")



# =============================================================================
# RUN PROGRAM
# =============================================================================
if __name__ == "__main__":
    LoginWindow().mainloop()
