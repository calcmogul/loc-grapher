# Lines of Code Grapher

Generates a graph of the lines of C++ and Java source code in WPILib's Git repository commits.

`./graph.py` will clone WPILib into /tmp or perform a pull if the repository already exists, create a CSV file containing the data, and generate a graph in LaTeX from that data. Upon completion, there will be a `loc.pdf` file in the current directory. The repository is left in /tmp to avoid recloning during subsequent runs.

`./upload.sh` will upload the results to https://file.tavsys.net/wpilib/loc.pdf.
