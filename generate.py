#!/usr/bin/env python3

import argparse
import datetime
import os
import re
import subprocess
import sys
import tempfile

import matplotlib.dates as mdate
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import MultipleLocator
import numpy as np


def clone_repo(url, branch):
    repo = os.path.basename(url)
    dest = os.path.join(os.getcwd(), repo).rstrip(".git")

    # Clone Git repository into current directory or update it
    if not os.path.exists(dest):
        subprocess.run(["git", "clone", url, dest])
        os.chdir(dest)
    else:
        os.chdir(dest)
        subprocess.run(["git", "pull"])

    # Quash rename limit warning
    subprocess.run(["git", "config", "diff.renameLimit", "999999"])

    # Check out branch before retrieving log info so branch exists
    subprocess.run(["git", "switch", branch])


class Category:
    def __init__(self, name, name_regex):
        self.name = name
        self.name_regex = re.compile(name_regex)
        self.line_count = 0


def generate_plot_data(categories, output_list):
    """Returns dates, counts, and labels to pass to generate_plot()."""
    # Fields are additions, subtractions, and filename
    line_regex = re.compile(r"^([0-9]+)\s+([0-9]+)\s+(.*?)$")

    dates = []
    counts = []
    for i in range(len(categories)):
        counts.append([])

    for line in output_list:
        if line.startswith("date "):
            # If line designates a new commit, record the date
            date = datetime.datetime.strptime(line[5:], "%Y-%m-%d %H:%M:%S %z")
            dates.append(date)

            dates.append(dates[-1])
            for i, category in enumerate(categories):
                if len(dates) == 2:
                    counts[i].append(0)
                else:
                    # Append previous count to move horizontally from
                    # previous date to current date
                    counts[i].append(counts[i][-1])
                # Append current count to move vertically
                counts[i].append(category.line_count)
        elif m := line_regex.search(line):
            # Lines with "- -" for counts are for binary files and are
            # ignored by line_regex
            for category in categories:
                if category.name_regex.search(m.group(3)):
                    category.line_count += int(m.group(1))
                    category.line_count -= int(m.group(2))

                    # Each file belongs to only one category
                    break

    # Write rest of data
    dates.append(dates[-1])
    dates.append(dates[-1])
    for i, category in enumerate(categories):
        # Append previous count to move horizontally from previous
        # date to current date
        counts[i].append(counts[i][-1])
        # Append current count to move vertically
        counts[i].append(category.line_count)

    labels = [category.name for category in categories]

    return dates, counts, labels


def generate_plot(pdf, dates, counts, labels, title, years=None):
    plt.figure(figsize=(11, 8.5))
    plt.stackplot(dates, counts, labels=labels)

    if years:
        if years[0] + 1 == years[1]:
            plt.title(f"{title} ({years[0]})")
        else:
            plt.title(f"{title} ({years[0]}-{years[1]})")
    else:
        plt.title(title)

    plt.ylabel("Lines of Code")

    ax = plt.gca()
    ax.yaxis.set_major_locator(MultipleLocator(50e3))
    ax.ticklabel_format(axis="y", style="scientific", scilimits=(3, 3), useOffset=False)

    if years:
        ax.set_xlim([datetime.date(years[0], 1, 1), datetime.date(years[1], 1, 1)])
        ax.xaxis.set_major_locator(mdate.MonthLocator(bymonthday=2))
    else:
        ax.set_xlim(
            [
                datetime.date(dates[0].year, 1, 1),
                datetime.date(dates[-1].year + 1, 1, 1),
            ]
        )
        ax.xaxis.set_major_locator(mdate.YearLocator(day=2))
    plt.gcf().autofmt_xdate()

    plt.grid()

    plt.legend(labels, loc="upper left")

    pdf.savefig()
    plt.close()


def main():
    branch = "main"

    cwd = os.getcwd()
    os.chdir(tempfile.gettempdir())
    clone_repo("https://github.com/wpilibsuite/allwpilib", branch)

    # Collect commit data
    print("Collecting commit data...", end="")
    sys.stdout.flush()
    args = [
        "git",
        "--no-pager",
        "log",
        "--numstat",
        "--no-renames",
        "--reverse",
        "--format=date %ci",
        branch,
    ]
    output_list = subprocess.check_output(args, encoding="utf-8").splitlines()
    print(" done.")

    lang_categories = []
    lang_categories.append(
        Category("thirdparty", r"Eigen/|drake/|libuv/|llvm/|thirdparty/|unsupported/")
    )
    lang_categories.append(Category("generated", r"generated/"))
    lang_categories.append(Category("C++", r"\.(cc|cpp|h|hpp|inc|inl)$"))
    lang_categories.append(Category("Java", r"\.java$"))
    lang_categories.append(Category("Python", r"\.py$"))

    lang_dates, lang_counts, lang_labels = generate_plot_data(
        lang_categories, output_list
    )

    # Move thirdparty and generated to top of stackplot by placing it at the end
    # of the list
    lang_counts.append(lang_counts.pop(0))
    lang_counts.append(lang_counts.pop(0))
    lang_labels.append(lang_labels.pop(0))
    lang_labels.append(lang_labels.pop(0))

    subproject_categories = []
    subproject_categories.append(
        Category("thirdparty", r"Eigen/|drake/|libuv/|llvm/|thirdparty/|unsupported/")
    )
    subproject_categories.append(Category("generated", r"generated/"))
    subproject_categories.append(Category("CSCore", r"^(cameraserver|cscore)/"))
    subproject_categories.append(Category("Commands", r"^wpilibNewCommands/"))
    subproject_categories.append(Category("Epilogue", r"epilogue-(processor|runtime)/"))
    subproject_categories.append(Category("Examples", r"Examples/"))
    subproject_categories.append(Category("HAL", r"^hal/"))
    subproject_categories.append(
        Category(
            "ImGUI tools",
            r"^(datalogtool|glass|outlineviewer|roborioteamnumbersetter|sysid|wpigui)/",
        )
    )
    subproject_categories.append(Category("Integration tests", r"IntegrationTests/"))
    subproject_categories.append(Category("NTCore", r"^(ntcore|ntcoreffi)/"))
    subproject_categories.append(
        Category("Simulation", r"^(simulation|romiVendordep|xrpVendordep)/")
    )
    subproject_categories.append(Category("WPILib", r"^(wpilibc|wpilibj)/"))
    subproject_categories.append(Category("WPIMath", r"^wpimath/"))
    subproject_categories.append(Category("WPINet", r"^wpinet/"))
    subproject_categories.append(Category("WPIUnits", r"^wpiunits/"))
    subproject_categories.append(Category("WPIUtil", r"^wpiutil/"))

    subproject_dates, subproject_counts, subproject_labels = generate_plot_data(
        subproject_categories, output_list
    )

    # Move thirdparty and generated to top of stackplot by placing it at the end
    # of the list
    subproject_counts.append(subproject_counts.pop(0))
    subproject_counts.append(subproject_counts.pop(0))
    subproject_labels.append(subproject_labels.pop(0))
    subproject_labels.append(subproject_labels.pop(0))

    # Generate plots
    os.chdir(cwd)
    print("Generating plots...", end="")
    sys.stdout.flush()
    with PdfPages("loc.pdf") as pdf:
        generate_plot(
            pdf, lang_dates, lang_counts, lang_labels, "WPILib Language Lines of Code"
        )

        generate_plot(
            pdf,
            subproject_dates,
            subproject_counts,
            subproject_labels,
            "WPILib Subproject Lines of Code",
        )

        min_year = min(date.year for date in lang_dates)
        max_year = max(date.year for date in lang_dates)
        for year in range(min_year, max_year + 1):
            generate_plot(
                pdf,
                lang_dates,
                lang_counts,
                lang_labels,
                "WPILib Language Lines of Code",
                (year, year + 1),
            )
    print(" done.")


if __name__ == "__main__":
    main()
