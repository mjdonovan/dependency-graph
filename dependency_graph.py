import os
import re
import argparse
import codecs
from collections import defaultdict
from graphviz import Digraph

include_regex = re.compile('#include\s+["<"](.*)[">]')
valid_headers = [['.h', '.hpp'], 'red']
valid_sources = [['.c', '.cc', '.cpp'], 'blue']
valid_extensions = valid_headers[0] + valid_sources[0]

def normalize(path):
	""" Return the name of the node that will represent the file at path. """
	filename = os.path.basename(path)
	end = filename.rfind('.')
	end = end if end != -1 else len(filename)
	return filename[:end]

def get_extension(path):
	""" Return the extension of the file targeted by path. """
	return path[path.rfind('.'):]

def find_all_files(path, recursive=True):
	""" 
	Return a list of all the files in the folder.
	If recursive is True, the function will search recursively.
	"""
	files = []
	for entry in os.scandir(path):
		if entry.is_dir() and recursive:
			files += find_all_files(entry.path)
		elif get_extension(entry.path) in valid_extensions:
			files.append(entry.path)
	return files

def find_neighbors(path):
	""" Find all the other nodes included by the file targeted by path. """
	f = codecs.open(path, 'r', "utf-8", "ignore")
	code = f.read()
	f.close()
	return [include for include in include_regex.findall(code)]

def count_lines(filename, chunk_size=1<<13):
    with open(filename) as file:
        return sum(chunk.count('\n')
                   for chunk in iter(lambda: file.read(chunk_size), '')) + 1

def get_absolute_path(path, include):
	parsed_include = include.split('/')
	parsed_path = path.split('/')
	higher_directory_counter = 1
	for directory in parsed_include:
		if directory != '..':
			break	
		higher_directory_counter += 1
	return '/'.join(parsed_path[:-higher_directory_counter] + parsed_include[higher_directory_counter - 1:]) 

def create_graph(folder, create_cluster, label_cluster, strict, gv, text, lines):
	""" Create a graph from a folder. """
	# Find nodes and clusters
	files = find_all_files(folder)
 
	folder_to_files = defaultdict(list)
	for path in files:
		folder_to_files[os.path.dirname(path)].append(path)
  
	nodes = set(files)
	# Create graph
	graph = Digraph(strict=strict)
	# Find edges and create clusters
	
	files_to_numbers = defaultdict(int)
	if text:
		str_lines = ['', 'Nodes:\n']
		for i in range(len(files)):
			normalized_name = normalize(files[i]) + get_extension(files[i]) 
			if lines:
				str_lines.append(f'{i + 1} {normalized_name} {count_lines(files[i])}\n')
			else:
				str_lines.append(f'{i + 1} {normalized_name}\n')
			files_to_numbers[files[i]] = i + 1
		str_lines.append('Edges:\n')
	if gv:
		gv_lines = []
		gv_lines.append('digraph ' + str(normalize(folder)) + ' {\n')
		for i in range(len(files)):
			normalized_name = normalize(files[i]) + get_extension(files[i]) 
			files_to_numbers[files[i]] = i + 1
			gv_lines.append(f'\t{i + 1} [label="{normalized_name}"];\n')
	
	subgraph_counter = 0
	for folder in folder_to_files:
		with graph.subgraph(name='cluster_{}'.format(folder)) as cluster:
			subgraph_nodes = []
			for path in folder_to_files[folder]:
				color = 'black'
				label = normalize(path) + get_extension(path)

				ext = get_extension(path)
				if ext in valid_headers[0]:
					color = valid_headers[1]
				if ext in valid_sources[0]:
					color = valid_sources[1]
				if create_cluster:
					cluster.node(path, label)
					subgraph_nodes.append(files_to_numbers[path])
				else:
					graph.node(path, label)
				neighbors = find_neighbors(path)
				for neighbor in neighbors:
					abs_path = get_absolute_path(path, neighbor)
					if abs_path != path and abs_path in nodes:
						graph.edge(path, abs_path, color=color)
						if text:
							str_lines.append(f'{files_to_numbers[path]} {files_to_numbers[abs_path]}\n')
						if gv:
							gv_lines.append(f'\t{files_to_numbers[path]} -> {files_to_numbers[abs_path]} [color = {color}];\n')
			if create_cluster:
				if gv:
					gv_lines.append(f'\tsubgraph cluster_{subgraph_counter} ' + '{\n')
					subgraph_counter += 1
				if label_cluster:
					cluster.attr(label=folder)
					if gv:
						gv_lines.append(f'\t\tlabel = "{folder}";\n')
				if gv:
					for node in subgraph_nodes:
						gv_lines.append(f'\t\t{node};\n')
					gv_lines.append('\t}\n')
	if text:
		with open('graph.txt', mode='w') as file:
			str_lines[0] = f'Nodes count: {len(files)} Edges count: {len(str_lines) - len(files) - 3}\n'
			file.writelines(str_lines)
	if gv:
		with open('graph.gv', mode='w') as file:
			gv_lines.append('}')
			file.writelines(gv_lines)
	return graph

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('folder', help='Path to the folder to scan')
	parser.add_argument('output', help='Path of the output file without the extension')
	parser.add_argument('-f', '--format', help='Format of the output', default='pdf', \
		choices=['bmp', 'gif', 'jpg', 'png', 'pdf', 'svg'])
	parser.add_argument('-v', '--view', action='store_true', help='View the graph')
	parser.add_argument('-c', '--cluster', action='store_true', help='Create a cluster for each subfolder')
	parser.add_argument('--cluster-labels', dest='cluster_labels', action='store_true', help='Label subfolder clusters')
	parser.add_argument('-s', '--strict', action='store_true', help='Rendering should merge multi-edges', default=False)
	parser.add_argument('--gv', action='store_true', help='Create graph.gv', default=False)
	parser.add_argument('--text', action='store_true', help='Create graph.txt with filenames and edges', default=False)
	parser.add_argument('--lines', action='store_true', help='Add to graph.txt number of lines in files', default=False)
  
	args = parser.parse_args()
	graph = create_graph(args.folder, args.cluster, args.cluster_labels, args.strict, args.gv, args.text, args.lines)
	graph.format = args.format
	graph.render(args.output, cleanup=True, view=args.view)
