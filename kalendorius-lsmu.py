import icalendar
from time import sleep
import requests
import re
import sys
import csv
from datetime import datetime

CIKLAS = "Krūtinės ligos, alergologija ir klinikinė imunologija"
CAL_URL = "https://lsmusis.lsmuni.lt/Tvarkarasciai/ManoTvarkarastis/ICal?lang=Lt&id=LkRwDqvySWE%3D"
CSV_FNAME = "tvarkarastis.csv" # Must end with .csv


def get_shit_list(flocation):
    fuck_lsmu_list = []
    with open(flocation, "r", encoding="UTF-8") as fin:
        result = re.findall(
            r"([0-9]\.[0-9]+)\.\s(.*\n){,7}Padalinys –(.*)", fin.read())
        # result = re.findall(r"[0-9]\.[0-9]+\.\s", fin.read())
        for i in result:
            number = i[0].strip()
            if len(number.split(".")[1]) == 1:
                number = ".0".join(number.split("."))
            katedra = i[2].strip()
            fuck_lsmu = {"numeris": number, "katedra": katedra}
            fuck_lsmu_list.append(fuck_lsmu)
    return fuck_lsmu_list



def get_cal_dates():

    req = requests.get(CAL_URL)
    if req.status_code == 200:
        print("OK!")
    else:
        print("Boo!")
        sleep(3)
        sys.exit(req)
    req.encoding = "UTF-8"
    gcal = icalendar.Calendar.from_ical(req.text)
    cal_dates = []

    for component in gcal.walk():
        if component.name == "VEVENT":
            summ = component["DESCRIPTION"]
            result = re.search(r"[0-9]\.[0-9]+(.*?)\n", summ)
            if result:
                tipas = ""
                ciklas = ""
                for k, v in component.items():
                    if k == "DESCRIPTION":
                        dirty_tipas = (
                            v.strip()
                            .split("\n")[0]
                            .replace(" (Tiesioginė transliacija)", "")
                            .strip()
                            .split(" ")
                        )
                        tipas = [i for i in dirty_tipas if len(i) != 1][0]
                    if k == "SUMMARY":
                        ciklas = (
                            v.replace(" (Tiesioginė transliacija)", "")
                            .replace("🏠", " ")
                            .replace("🔴", " ")
                            .strip()
                        )
                if ciklas == CIKLAS:
                    cname = result[0].strip()
                    number = cname.split(" ")[0]
                    pavadinimas = " ".join(cname.split(" ")[1:])

                    if len(number.split(".")[1]) == 1:
                        number = ".0".join(number.split("."))

                    dtstart = component["DTSTART"].dt.strftime(
                        "%Y.%m.%d %H:%M")
                    dtend = component["DTEND"].dt.strftime("%H:%M")
                    date = dtstart + "-" + dtend

                    combo = {
                        "numeris": number,
                        "data": date,
                        "pavadinimas": pavadinimas,
                        "tipas": tipas,
                        "ciklas": ciklas,
                    }
                    # print(number)
                    # print(tipas)
                    # print(pavadinimas)
                    # print()
                    cal_dates.append(combo)
    return cal_dates


def cal_to_csv(fname, cal_list):
    with open(fname, "w", newline="", encoding="utf-8") as f:
        print(":::")
        print("Opened file")
        thewriter = csv.writer(f)
        thewriter.writerow(
            ["Numeris", "Data", "Pavadinimas", "Tipas", "Ciklas"])
        for row in cal_list:
            lsmu_list = [
                row["numeris"],
                row["data"],
                row["pavadinimas"],
                row["tipas"],
                row["ciklas"],
            ]
            thewriter.writerow(lsmu_list)
        print("All good, Bye :)")
        print(":::")


# Fun part
cal_list = get_cal_dates()
cal_to_csv(CSV_FNAME, cal_list)
