# dependency-graph

A python script to show the "include" dependency of C++ classes.

It is useful to check the presence of circular dependencies.

## Differences from original version

The original version does not work properly when files from different directories have the same names or when the source and header files have the same names. This has been fixed in this version.

--gv argument generates a graph.gv file with a graph for use in third-party applications.

--text argument generates a graph.txt file with a text file containing graph data.

--line argument adds information about the number of lines in files in graph.txt (Requires the --text argument).

--ignore-tests argument adds ignoring to files with names that includes "test".

--show-path argument adds path in nodes labels.

## Installation

The script depends on [Graphviz](https://www.graphviz.org/) to draw the graph. 

On Ubuntu, you can install the dependencies with these two commands:

```
sudo apt install graphviz
pip3 install -r requirements.txt
```

## Manual

```
usage: dependency_graph.py [-h] [-f {bmp,gif,jpg,png,pdf,svg}] [-v] [-c] [--cluster-labels] [-s] [--gv] [--text] [--lines] [--ignore-tests] folder output

positional arguments:
  folder                Path to the folder to scan
  output                Path of the output file without the extension

options:
  -h, --help            show this help message and exit
  -f {bmp,gif,jpg,png,pdf,svg}, --format {bmp,gif,jpg,png,pdf,svg}
                        Format of the output
  -v, --view            View the graph
  -c, --cluster         Create a cluster for each subfolder
  --cluster-labels      Label subfolder clusters
  -s, --strict          Rendering should merge multi-edges
  --gv                  Create graph.gv
  --text                Create graph.txt with filenames and edges
  --lines               Add to graph.txt number of lines in files
  --ignore-tests        Files with names that includes "test" will be ignored in graph
  --show-path           Files will be labeled with path
```

## Examples

Example of a graph produced by the script:

![Example 1](https://github.com/pvigier/dependency-graph/raw/master/examples/example1.png)

Graph produced for the same project with clusters (`-c`):

![Example 2](https://github.com/pvigier/dependency-graph/raw/master/examples/example2.png)
