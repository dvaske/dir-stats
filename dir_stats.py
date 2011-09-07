#!/usr/bin/env python
# encoding: utf-8
"""
dir-stats.py

Run analysis on directory

Created by Aske Olsson 2011-09-05.
Copyright (c) 2011 Aske Olsson. All rights reserved.
"""
#!/usr/bin/env python
# encoding: utf-8
import os
from subprocess import Popen, PIPE
import operator

def extract_file_types(files, dirs):
    dict = {}
    for file in files.keys():
        # get file extension
        extension = os.path.splitext(file)[1]
        if extension == '':
            # which file is it then, makefiles should be detectable
            if os.path.split(file)[1].lower().startswith('make'):
                extension = 'makefile'
            elif os.path.split(file)[1].lower() == 'readme':
                extension = 'readme'
            elif os.path.split(file)[1].lower() == 'doxyfile':
                extension = 'doxyfile'
            else:
                extension = "NO-EXT"
        else:
            # Remove the . from the extension
            extension = extension.lstrip('.')
        if dict.has_key(extension):
            dict[extension].append(file)
        else:
            dict[extension] = [file]

    dict['directories'] = dirs.keys()
    return dict


def extract_size_info(files, file_types, dirs):
    total_size = sum(files.values()) + sum(dirs.values())

    type_size = {}
    for type in file_types.keys():
        if not type == 'directories':
            type_size[type] = sum([files[file] for file in file_types[type]])

    type_size['directories'] = sum(dirs.values())
    return type_size, total_size

def largest_files(content, num_of_files):
    """ Get the largest files in the dir """
    sorted_size = sorted(content.iteritems(), key=operator.itemgetter(1))
    sorted_size.reverse()
    return sorted_size[:num_of_files]


def analyze_dir(files, dirs):

    file_types = extract_file_types(files, dirs)
    total_files = 0
    for type in sorted(file_types.keys()):
        #print 'Number of %s: %d' %(type, len(file_types[type]))
        total_files += len(file_types[type])
    #print "Total files: %d" %total_files

    size_info, total_size = extract_size_info(files, file_types, dirs)
    return file_types, size_info, total_size


def format_content(content):
    dict = {}
    for line in content.splitlines():
        tmp = line.split('|SPLIT|')
        dict[tmp[0]] = float(tmp[1])

    return dict

def get_files(dir):
    cmd = ['find', dir, '-type', 'f', '-printf', '%p|SPLIT|%s\n']
    content = run_command(cmd)
    content = format_content(content)
    return content

def get_dirs(dir):
    cmd = ['find', dir, '-type', 'd', '-printf', '%p|SPLIT|%s\n']
    content = run_command(cmd)
    content = format_content(content)
    return content

def find_empty_dirs(files, dirs):
    # Used dirs:
    used_dirs = [os.path.split(d)[0] for d in files.keys()]
    # Find leaf dirs
    leaf = []
    last = sorted(dirs.keys())[0]
    for dir in sorted(dirs.keys())[1:]:
        if not dir.startswith(last):
            leaf.append(last)
        else:
            # Check if current dir just starts with same name as last dir
            if os.path.split(last)[0] == os.path.split(dir)[0]:
                if os.path.split(last)[1] != os.path.split(dir)[1]:
                    leaf.append(last)
        last = dir
    leaf.append(last)

    for dir in set(used_dirs):
        if dir in leaf:
            leaf.remove(dir)
    return leaf

def run_command(command):
    """Execute a command"""
    p = Popen(command, stdout=PIPE, stderr=PIPE)

    # Store the result as a single string.
    stdout, stderr = p.communicate()

    if stderr:
        return stderr
    return stdout

def pretty_print_size(size):
    """Convert a file size to human-readable form."""
    SUFFIXES = ['KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    if size < 0:
        raise ValueError('number must be non-negative')

    multiple = 1024
    for suffix in SUFFIXES:
        size /= multiple
        if size < multiple:
            return '{0:.1f} {1}'.format(size, suffix)

def longest_path( paths ):
    key = lambda path:path.count('/')
    return max(paths, key=key)

def get_dir_stats(dir):
    dir = dir.strip('/')
    files = get_files(dir)
    dirs = get_dirs(dir)
    file_types, size_info,total_size = analyze_dir(files, dirs)
#    return file_types, size_info
    print '{0:<15} {1:>6s} {2:>12s}'.format('File types', 'count', 'size')
    for type in sorted(file_types.keys()):
        print '{0:.<15}.{1:.>6s}.{2:.>12s}'.format(type, str(len(file_types[type])), pretty_print_size(size_info[type]))
        #print 'Size of %s files: %d kb' %(type, size_info[type]/(1024))
    largest = largest_files(files, 50)
    for file, size in largest:
        print pretty_print_size(size), file
    print "Total size %s" % pretty_print_size(total_size)

    path = longest_path(dirs.keys())
    print "Longest path: ", path

    empty = find_empty_dirs(files, dirs)
    #print "empty:"
    #print '\n'.join(empty)
    print 'Empty directories: %d' %len(empty)



