#!/usr/bin/env python3

import os
import re
import shutil
import subprocess
import sys
import tempfile


def clone_repo(url, branch):
    repo = os.path.basename(url)

    # Clone Git repository into current directory or update it
    if not os.path.exists(repo):
        dest = os.path.join(os.getcwd(), repo)
        subprocess.run(["git", "clone", url, dest])
        os.chdir(repo)
    else:
        os.chdir(repo)
        subprocess.run(["git", "pull"])

    # Quash rename limit warning
    subprocess.run(["git", "config", "diff.renameLimit", "999999"])

    # Check out branch before retrieving log info so branch exists
    subprocess.run(["git", "checkout", branch])


def main():
    branch = "master"

    cwd = os.getcwd()
    os.chdir(tempfile.gettempdir())
    clone_repo("git://github.com/wpilibsuite/allwpilib", branch)

    # Create list of commit hashes
    print("Collecting commit data...", end="")
    sys.stdout.flush()
    args = [
        "git",
        "--no-pager",
        "log",
        "--numstat",
        "--reverse",
        "--pretty=oneline",
        branch,
    ]
    output_list = subprocess.check_output(args, encoding="utf-8").splitlines()
    print(" done.")

    line_regex = re.compile("([0-9]+)\s+([0-9]+)\s+(\S+)")
    ext_regex = re.compile("\.(c|cpp|h|hpp|inc|inl|java|py)$")
    commit_count = 0
    line_count = 0
    with open("data.csv", "w") as data:
        for line in output_list:
            if "\t" not in line[:40]:
                # Write entry to file
                data.write(str(commit_count))
                data.write(",")
                data.write(str(line_count))
                data.write("\n")

                commit_count += 1
            else:
                match = line_regex.search(line)
                if match and ext_regex.search(match.group(3)):
                    line_count += int(match.group(1))
                    line_count -= int(match.group(2))
        # Write rest of data
        data.write(str(commit_count))
        data.write(",")
        data.write(str(line_count))
        data.write("\n")

    # Generate graphs
    shutil.move("data.csv", cwd + "/loc/data.csv")
    os.chdir(cwd + "/loc")
    subprocess.run(["latexmk", "-pdf", "-silent", "loc"])
    shutil.copy("loc.pdf", "../loc.pdf")


if __name__ == "__main__":
    main()
