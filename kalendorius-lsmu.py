from datetime import datetime
from time import sleep
import icalendar
import requests
import csv
import sys
import re

from simple_term_menu import TerminalMenu

CAL_URL = "https://lsmusis.lsmuni.lt/Tvarkarasciai/ManoTvarkarastis/ICal?lang=Lt&id=LkRwDqvySWE%3D"
CSV_FNAME = "tvarkarastis.csv"  # Must end with .csv
CAL_FNAME = "cal.ics"


class Event:
    def __init__(self, description, summary, dtstart, dtend):

        self.description = description
        self.summary = summary
        self.dtstart = dtstart
        self.dtend = dtend

        self.set_numeris()
        self.set_data()
        self.set_pavadinimas()
        self.set_tipas()
        self.set_ciklas()

    def get_combo_dict(self, ciklas):
        if self.ciklas == ciklas:
            combo = {
                "numeris": self.numeris,
                "ds": self.ds,
                "de": self.de,
                "pavadinimas": self.pavadinimas,
                "tipas": self.tipas,
                "ciklas": self.ciklas,
            }
            return combo

    def set_numeris(self):
        pattern = r"([0-9]\.[0-9]+).*?\n"
        string_to_search = self.description
        result = re.search(pattern, string_to_search)
        if result:

            line = result.group(0)
            number = line.split()[0].strip(".")

            # Kad ištaisyti 4.5 --> 4.05
            # Kad ištaisyti 4.3/1 --> 4.03/2
            number_split = number.split(".")

            if len(number_split) == 2:
                if len(number_split[1]) == 1 and len(number_split[1].split("/")) == 1:
                    number = number_split[0] + ".0" + number_split[1]
                elif len(number_split[1].split("/")) == 2:
                    if len(number_split[1].split("/")[0]) == 1:
                        number = number_split[0] + ".0" + number_split[1]
            else:
                print("UNKNOWN NUMBER:", number)

            self.numeris = number
            self.has_valid_number = True
            # Jei yra numeris, tai yra ir pavadinimas
            self.pavadinimas = " ".join(line.split()[1:])
        else:
            self.numeris = "0.00"
            self.has_valid_number = False
            self.pavadinimas = None

    def set_tipas(self):
        dirty_tipas = (
            self.description.strip()
            .split("\n")[0]
            .replace("(Tiesioginė transliacija)", "")
            .strip()
            .split(" ")
        )
        # Remove random symbols and take only first word
        tipas = [i for i in dirty_tipas if len(i) != 1][0]
        self.tipas = tipas

    def set_ciklas(self):
        # Remove random symbols
        ciklas = (
            self.summary.replace("(Tiesioginė transliacija)", "")
            .replace("🏠", " ")
            .replace("🔴", " ")
            .strip()
        )
        self.ciklas = ciklas

    def set_data(self):
        # start = self.dtstart.dt.strftime("%Y/%m/%d %H:%M")
        # end = self.dtend.dt.strftime("%H:%M")
        # date = start + "-" + end
        # self.data = date

        self.ds = int(self.dtstart.dt.strftime("%s")) * 1000
        self.de = int(self.dtend.dt.strftime("%s")) * 1000

    def set_pavadinimas(self):
        if not self.has_valid_number:
            pavadinimas = self.description.split("\n")[1].strip()
            if pavadinimas:
                self.pavadinimas = pavadinimas
            else:
                pavadinimas = "None"
        else:
            pass


def get_shit_list_from_file(flocation):
    jeez_lsmu_list = []
    with open(flocation, "r", encoding="UTF-8") as fin:
        result = re.findall(r"([0-9]\.[0-9]+)\.\s(.*\n){,7}Padalinys –(.*)", fin.read())
        # result = re.findall(r"[0-9]\.[0-9]+\.\s", fin.read())
        for i in result:
            number = i[0].strip()
            if len(number.split(".")[1]) == 1:
                number = ".0".join(number.split("."))
            katedra = i[2].strip()
            jeez_lsmu = {"numeris": number, "katedra": katedra}
            jeez_lsmu_list.append(jeez_lsmu)
    return jeez_lsmu_list


def cal_to_csv(fname, cal_list):
    with open(fname, "w", newline="", encoding="utf-8") as f:
        thewriter = csv.writer(f)
        thewriter.writerow(["Numeris", "ds", "de", "Pavadinimas", "Tipas", "Ciklas"])
        for row in cal_list:
            lsmu_list = [
                row["numeris"],
                row["ds"],
                row["de"],
                row["pavadinimas"],
                row["tipas"],
                row["ciklas"],
            ]
            thewriter.writerow(lsmu_list)
        print("File Saved to:", fname)
        print("All good, Bye :)")


def get_cal_from_url(cal_url):
    req = requests.get(cal_url)
    if req.status_code == 200:
        print("Calendar URL status: OK!")
    else:
        print("Calendar URL status: Boo!")
        sleep(3)
        sys.exit(req)
    req.encoding = "UTF-8"
    cal = icalendar.Calendar.from_ical(req.text)

    with open("cal.ics", "w", encoding="UTF-8") as fout:
        fout.write(req.text)

    return cal


def get_cal_from_file(cal_fname):
    with open(cal_fname, "r", encoding="UTF-8") as fin:
        cal = icalendar.Calendar.from_ical(fin.read())
    return cal


def get_event_obejct_list(calendar):
    obj_list = []
    for component in calendar.walk("VEVENT"):
        description = component.get("DESCRIPTION")
        summary = component.get("SUMMARY")
        dtstart = component.get("DTSTART")
        dtend = component.get("DTEND")
        obj_list.append(Event(description, summary, dtstart, dtend))
    return obj_list


def get_cal_events_list(obj_list, ciklas):

    events_list = []

    for event in obj_list:
        combo_dict = event.get_combo_dict(ciklas)
        if combo_dict:
            events_list.append(combo_dict)

    return events_list


def lol(event_object_list):
    good_count = 0
    bad_count = 0

    for i in event_object_list:
        if i.has_valid_number:
            good_count += 1
        else:
            bad_count += 1

    total_count = good_count + bad_count

    print("Total Events:", total_count)
    print("Events without 'paskaitos numeris':", bad_count)
    print("Events with 'paskaitos numeris':", good_count)
    print(
        "Tinginiai, kurie nesugeba įvesti paskaitos numerio:",
        (bad_count / total_count) * 100,
        "%",
    )


def get_ciklai_list(event_object_list):
    ciklai = []
    for event in event_object_list:
        if event.ciklas not in ciklai:
            ciklai.append(event.ciklas)
    return ciklai


def main():

    cal_url = input("Enter Calendar URL (Enter for default): ")
    if not cal_url:
        cal_url = "https://lsmusis.lsmuni.lt/Tvarkarasciai/ManoTvarkarastis/ICal?lang=Lt&id=LkRwDqvySWE%3D"

    # Get Calendar from File or from URL:
    cal = get_cal_from_url(cal_url)
    # cal = get_cal_from_file(CAL_FNAME)

    # Get Event object list from Calendar:
    event_object_list = get_event_obejct_list(cal)

    # Extras:
    # lol(event_object_list)

    options = get_ciklai_list(event_object_list)
    terminal_menu = TerminalMenu(options, title="Pasirinkite Ciklą:")
    menu_entry_index = terminal_menu.show()
    print(f"Jūs pasirinkote: {options[menu_entry_index]}!")

    csv_fname = input("Enter CSV file output location (enter for default): ")

    if not csv_fname:
        csv_fname = "tvarkarastis.csv"

    # Write Calendar List to CSV file:
    cal_list = get_cal_events_list(event_object_list, options[menu_entry_index])
    cal_to_csv(csv_fname, cal_list)


if __name__ == "__main__":
    main()
