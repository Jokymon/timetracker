# -*- coding: latin-1 -*-
import sys
import sqlite3
import datetime
import gettext
from getch import getch
from menu import Menu
from storm.locals import *

def uraw_input(prompt=u""):
    """Unicode friendly version of the standard raw_input method"""
    import sys
    return raw_input( prompt.encode(sys.stdout.encoding) ).decode(sys.stdin.encoding)

def date_is_today(d):
    now = datetime.datetime.now()
    if now.date()==d:
        return True
    else:
        return False


class Activity(object):
    __storm_table__ = "activities"
    id = Int(primary=True)
    name = Unicode()
    is_work = Bool()

class LogEntry(object):
    __storm_table__ = "timelog"
    id = Int(primary=True)
    activity_id = Int()
    activity = Reference(activity_id, Activity.id)
    ts = DateTime()
    details = Unicode()

class Timelog:
    def __init__(self, db_file):
        self.db_file = db_file

    def init(self):
        conn = sqlite3.connect(self.db_file, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        cur = conn.cursor()
        cur.execute("select name from SQLite_Master")
        tables = map(lambda x: x[0], cur.fetchall())

        # TODO: also check that the existing tables have the correct data-types
        if not "activities" in tables:
            cur.execute("create table activities (id integer primary key, name text, is_work int)")
        if not "timelog" in tables:
            cur.execute("create table timelog (id integer primary key, activity_id integer, ts text, details text)")
        cur.close()
        conn.close()

    def open(self):
        self.database = create_database("sqlite:%s" % self.db_file)
        self.store    = Store(self.database)

    def day_report(self, d):
        """Generate a list of activities for the given date d (type
           datetime.date) in the form

           [ (True,  4.0, "Activity 1", "Details"),
             (False, 2.0, "Activity 2", "Some more details here"),
             (True,  2.0, "Activity 3", "And some"),
           ]

           Where the first column says if it is work time (true) or not (false)
           and the numbers in the second column indicate the amount of hours
           spent on that activity"""
        # TODO: create nicer grouping by activity name
        import time

        day_start = datetime.datetime( d.year, d.month, d.day,   0, 0, 0)
        day_end   = day_start + datetime.timedelta(1)
        if date_is_today( d ):
            day_end = datetime.datetime.now()
        day_log = self.store.find( LogEntry, LogEntry.ts > day_start, LogEntry.ts < day_end ).order_by(LogEntry.ts)

        start_times = [day_start] + map( lambda x: x.ts, day_log )
        end_times   = map( lambda x: x.ts, day_log ) + [day_end]

        report = []
        totalwork = 0
        for (idx, (start, end)) in enumerate(zip(start_times, end_times)):
            activity_name = ""
            activity_is_work = False
            details = ""
            if idx!=0:
                activity = day_log[idx-1].activity
                activity_name    = activity.name
                activity_is_work = activity.is_work
                details          = day_log[idx-1].details
            diff = float( (end-start).seconds / 60) / 60
            if activity_is_work:
                totalwork += diff
            report.append( ( activity_is_work, diff, activity_name, details) )
        total_details = ""
        if date_is_today( d ):
            now = datetime.datetime.now()
            total_details = _("until now (%s)") % now.strftime("%H:%M")
        report.append( (True, totalwork, _("Total work"), total_details) )

        return report

    def month_report(self, year, month):
        """Similar to day_report() this function will return an activity report
        of a whole month. The report is a list of tuples where each tuple
        consists of a date object and the day report for that date."""
        import calendar
        report = []
        (start_day, end_day) = calendar.monthrange(year, month)
        for day in range( start_day, end_day+1 ):
            d = datetime.date( year, month, day )
            report.append( (d, self.day_report(d)) )
        return report

class TimelogUi:
    def __init__(self, timelogdb):
        self.tdb = timelogdb

    def add_activity(self):
        print "\r"
        new_activity = uraw_input(_("New activity: "))
        # TODO: ask whether this is a work activity or not
    
        act = Activity()
        act.name = unicode(new_activity)
        act.is_work = True
        self.tdb.store.add(act)
        self.tdb.store.commit()
    
    def list_activities(self):
        all = self.tdb.store.find(Activity)
        print "\r"
        print _("Known activities:")+"\r"
        for act in all:
            classification = _("spare")
            if act.is_work:
                classification = _("work")
            print " %u %-10s %s\r" % ( act.id, classification, act.name)
        print "\r"
    
    def choose_activity(self):
        activities = self.tdb.store.find(Activity)
        l = []
        for idx, a in enumerate(activities):
            l.append( (str(idx+1), a.id, a.name) )
        selection = Menu( l ).choose()
        return selection
    
    def log_activity(self, activity_id, details, timestamp = datetime.datetime.now()):
        tl = LogEntry()
        tl.activity_id = activity_id
        tl.ts = timestamp
        tl.details = unicode(details)
        self.tdb.store.add(tl)
        self.tdb.store.commit()
    
    def show_activity_log(self):
        import time
        all = self.tdb.store.find(LogEntry)
        print "\r"
        print "---------------------------------------\r"
        for log in all.order_by(LogEntry.ts):
            print " %s -   %-20s %s\r" % (time.strftime("%Y.%m.%d %H:%M:%S", log.ts.timetuple()), log.activity.name, log.details)
        print "---------------------------------------\r"
        print "\r"
    
    def switch_activity(self):
        print _("Switch to new activity")
        selection = self.choose_activity()
        if selection!='':
            details = uraw_input(_("Details: "))
            self.log_activity(selection[1], details)
    
    def add_activity_log(self):
        print _("Log an activity with a specified start time")
        selection = self.choose_activity()
        if selection!='':
            details = uraw_input(_("Details: "))
            date = ""
            ts = None
            import time
            while date=="":
                date = uraw_input(_("Enter a valid date in the format 'yyyy.mm.dd HH:MM': "))
                try:
                    dt = time.strptime(date, "%Y.%m.%d %H:%M")
                    ts = datetime.datetime( *dt[:7] )
                except ValueError:
                    print _("Your date is not valid, please check the format")
                    date = ""
            self.log_activity(selection[1], details, ts)

    def show_month_report(self):
        now = datetime.datetime.now()
        report = self.tdb.month_report( now.year, now.month )
        for (d, r) in report:
            print "\r"
            print "---------------------------------------\r"
            print "%s\r" % d.strftime("%Y.%m.%d")
            for item in r:
                if item[0]:
                    print "  %-3.2f  %s - %s\r" % item[1:]
        print "---------------------------------------\r"
        print "\r"

def main():
    import gettext
    gettext.install('timetracker', 'locale', unicode=1)
    from optparse import OptionParser
    parser = OptionParser(usage = "usage: %prog [options]")
    parser.add_option("-d", "--debug", action="store_true", dest="debug", default=False,
                      help="Load a debug database instead of the production one")

    (options, args) = parser.parse_args()

    database_file = "life_time_protocol.db"
    if options.debug:
        database_file = "time_protocol.db"
    db = Timelog( database_file )
    db.init()
    db.open()

    ui = TimelogUi(db)

    Menu([
        ('s', ui.switch_activity,   _("Start new activity")),
        ('l', ui.show_activity_log, _("Show last logged activities")),
        ('d', ui.add_activity_log,  _("Log activity with specified start")),
        (' ', None, None),
        ('a', ui.list_activities,   _("Show available activities")),
        ('n', ui.add_activity,      _("Add new activity")),
        (' ', None, None), 
        ('t', ui.show_month_report, _("Show monthly report")),
        ]
    ).run()

if __name__=="__main__":
    main()
