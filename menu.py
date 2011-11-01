# -*- coding: latin-1 -*-
import getch

class Menu:
    def __init__(self, entries):
        """Creates a menu given the menu items specified in entries as follows.
        The parameter 'entries' must be a list of tuples where each tuple
        represents one menu item. The tuple contains 1) the shortcut-key 2) a
        function to call when this item is select and 3) and menu text.
        Example:

            [ ( 'n', new_address, "Create a new address book entry"),
              ( 's', search_address, "Search the address book"),
              ( 'd', delete_address, "Delete an address book entry"),
            ]

        It is possible to add an empty entry to separate items in the menu.

          ... ( ' ', None, None ),

        In this case the function and the menu text are disregarded and can be
        None. """
        self.entries = entries
        self.functions = {}
        for item in self.entries:
            if item[0]!=' ':
                self.functions[item[0]] = item[1]

    def run(self):
        """Display this menu, accept user input and execute the assigned
        functions until the user presses ESC."""
        ESC_CHAR = '\x1b'
        ch = ''
        while ch!=ESC_CHAR:
            for item in self.entries:
                if item[0]==' ':
                    print "\r"
                else:
                    print " %s - %s\r" % (item[0], item[2])
            print "Press 'ESC' to quit this menu\r"
            ch = getch.getch()
            if ch in self.functions.keys():
                self.functions[ch]()
            elif ch==ESC_CHAR:
                pass # ESC character handled by the while loop
            else:
                print "Unknown menu item '%s'\r" % ch

    def choose(self):
        """The choose function is a degenerate version of run. It only shows
        the available menu items once and let's the user choose an item. The
        menu is redisplayed only when the user chooses an item not in the list.
        The function element of the entry tuples are not used by choose().
        However the returned value will contain a tuple consisting of the
        selected character and the function part of the selected item. This can
        be used to get a relationship between the selection character and the
        menu item."""
        ESC_CHAR = '\x1b'
        ch = ''
        while ch != ESC_CHAR and not ch in self.functions.keys():
            for item in self.entries:
                if item[0]==' ':
                    print "\r"
                else:
                    print " %s - %s\r" % (item[0], item[2])
            print "Press 'ESC' to quit this menu\r"
            ch = getch.getch()
            if ch!=ESC_CHAR and not ch in self.functions.keys():
                print "Unknown menu item '%s'\r" % ch
        if ch==ESC_CHAR:
            return ''
        else:
            return (ch, self.functions[ch])

if __name__=="__main__":
    def add_address():
        print "Adding address\r"

    def delete_address():
        print "Deleting an address:\r"
        ch = Menu([
                ('1', "jd", "Jon Doe"),
                ('2', "peterm", "Peter Muster"),
                ('3', "es", "Erik Svensson"), ]).choose()
        if ch!='':
            print "Deleting item '%s' with value '%s'" % ch
        else:
            print "Not deleting any item"

    def show_addresses():
        print "All addresses: ....."

    sub = Menu([
            ('1', lambda: None, "Some item"),
            ('2', lambda: None, "Some second item"), ])

    m = Menu([
            ('1', add_address, "Add new address"),
            ('2', delete_address, "Delete an address"),
            ('s', sub.run, "Submenu"),
            (' ', None, None),
            ('a', show_addresses, "Show all adresses"), ])
    m.run()
