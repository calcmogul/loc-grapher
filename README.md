# Lines of Code Grapher

Generates a graph of the lines of C++, Java, and Python source code in WPILib's Git repository commits.

`./generate.py` clones WPILib into /tmp or performs a pull if the repository already exists, extracts data from the git log, generates graphs from it, then writes them to a file called `loc.pdf` in the current directory. The repository is left in /tmp to avoid recloning during subsequent runs.

`./upload.sh` uploads the results to https://file.tavsys.net/wpilib/loc.pdf.
