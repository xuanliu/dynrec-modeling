#!/usr/bin/python

"""
This script is to convert the output by ampl to the cplex lp file. So that 
cplex can solve the larger problem that student version of ampl cannot solve. 

"""

import re
import sys

from optparse import OptionParser

def read_file(filename):
    ''' read the file contains raw code '''
    fopen = open(filename, 'r')
    lines = fopen.readlines()
    return lines


def print_file(filename,toprint, mode):
    ''' print item into file '''
    f_handle = open(filename, mode)
    f_handle.writelines(toprint)
    f_handle.close()

def parse_variable(line):
    ''' Convert variables to cplex format '''
    p1 = re.compile('(\[|,)')
    p2 = re.compile('(\]|;|\t|\n)')
    tmp_line = p1.sub('_', line)
    tmp_line = tmp_line.replace('*', ' ')
    new_line = p2.sub('', tmp_line)
    return new_line


def remove_constrain_begin(line):
    ''' Remote "subject to " in the constrain line '''
    tmp_line = line.replace('subject to ', '')
    tmp_line = tmp_line.replace('\n', ' ')
    p1 = re.compile('(\[|,)')
    tmp_line = p1.sub('_', tmp_line)
    new_line = tmp_line.replace(']', '')
    return new_line


def modify_header(line, obj_name):
    new_header = line.replace(''.join([' ', obj_name,':']), '')
    return new_header


def convert_code(lines, obj_name):
    ''' Convert code to cplex format '''
    update_lines = []
    header = modify_header(lines[0], obj_name)
    update_lines.append(header)
    for line in lines:
        if "subject to" in line:
            new_constrain = remove_constrain_begin(line)
            update_lines.append(new_constrain)
        else:
            var_line = parse_variable(line)
            update_lines.append(var_line)
    return update_lines

def print_obj_fun(lines, obj_name, output_file):
    ''' print cplex objective function and headings for constrains '''
    obj_lines = []
    header = modify_header(lines[0], obj_name)
    obj_lines.append(header)
    print_file(output_file, header, 'w')
    for line in lines[1:]:
        if "subject to" in line:
            print_file(output_file, '\n', 'a')
            print_file(output_file, "subject to \n", 'a')
            break
        else:
            var_line = parse_variable(line)
            obj_lines.append(var_line)
            print_file(output_file, var_line, 'a')
    #return obj_lines


def print_constrain(lines, output_file):
    ''' print constrains '''
    constrains = []
    equations = []
    index = 0
    while (index < len(lines)):
        if ("subject to" in lines[index]) and "0 <=" not in lines[index+1]:
            cs_name = remove_constrain_begin(lines[index])
            constrains.append(cs_name)
            index = index + 1
            if "0 <=" in lines[index]:
                print lines[index]
            while(lines[index] != '\n'):
                cs_equation = parse_variable(lines[index])
                equations.append(cs_equation)
                constrains.append(cs_equation)
                cs_name = ' '.join([cs_name, cs_equation])
                index = index + 1
            print_file(output_file, cs_name, 'a')
            print_file(output_file, '\n','a')
        else:
            index = index + 1
    print_file(output_file, '\n', 'a')
    return equations
    #return constrains

def get_variables(obj_lines, bin_var_list):
    ''' get a list of variables '''
    var_list = []
    for line in obj_lines:
        tmp = line.split()
        for item in tmp:
            if item[0] in bin_var_list:
                var_list.append(item)
            else:
                pass
    #var_list.append('\n')
    return list(set(var_list))

def print_variables(var_list, output_file):
    ''' print variables to cplex file '''
    print_file(output_file, 'integer \n', 'a')
    count = 10
    index = 0
    start = 0
    new_line = []
    while index < len(var_list):
#        if len(var_list) <= count:
#            new_line.append(var_list[index])
#            index = index + 1
#            if index == len(var_list):
#                new_line.append('\n')
#                variables = ' '.join(new_line)
#                print_file(output_file, variables, 'a')
#        else:
        if start < count:
            new_line.append(var_list[index])
            start = start + 1
            index = index + 1
            if index == len(var_list):
                new_line.append('\n')
                variables = ' '.join(new_line)
                print_file(output_file, variables, 'a')
        elif start == count:
            new_line.append('\n')
            variables = ' '.join(new_line)
            print_file(output_file, variables, 'a')
            start = 0
            new_line = []
            #index = index + 1

        
        
    #print_file(output_file, variables, 'a')

def print_end(output_file):
    ''' print END '''
    print_file(output_file, 'END', 'a')


def get_cplex_code(ampl_input, cplex_output, bin_vars, obj_name):
    ''' Take the expand output from ampl, and convert it into cplex code '''
    lines = read_file(ampl_input)
    # check binary variables
    bin_var_list = eval(bin_vars)
    #obj_name = 'Total_Cost'
    print_obj_fun(lines, obj_name, cplex_output)
    cs_equations = print_constrain(lines, cplex_output)
    if bin_var_list != None:
        var_list = get_variables(cs_equations, bin_var_list)
        #print "variable", var_list
        print_variables(var_list, cplex_output)
    else:
        # all variables are real number, does not need to specify in the lp file
        pass
    print_end(cplex_output)


def create_option(parser):
    """
    add options to parse
    take arguments from commandline
    """
    parser.add_option("-v", action="store_true",
                      dest="verbose",
                      help="Print output to screen")
    parser.add_option("-r", dest="ampl_equa",
                      type="str",
                      default="dyn_equa.txt",
                      help="read ampl expanded equations")
    parser.add_option("-w", dest="cplex_lp",
                      type="str",
                      default="dyn_cplex.lp",
                      help="create cplex lp file from ampl expanded equation")
    parser.add_option("-b", dest="bin_vars",
                      type="str",
                      default="None",
                      help="indicate binary variables in form of list")
    parser.add_option("--obj", dest="obj_name",
                      type="str",
                      default="Total_Cost",
                      help="The objective name in the ample model file")
                      
                      
                      
def main(argv=None):
    ''' main function (program wrapper) '''
    if not argv:
        argv=sys.argv[1:]
    usage = ("%prog [-v verbose] [-r ampl_equa] \
            [-w cplex_lp] [-b bin_vars] [--obj obj_name]")
    parser = OptionParser(usage=usage)
    create_option(parser)
    (options, _) = parser.parse_args(argv)
    ampl_equa = options.ampl_equa
    cplex_lp = options.cplex_lp
    bin_vars = options.bin_vars
    obj_name = options.obj_name
    #print bin_vars, type(bin_vars)
    get_cplex_code(ampl_equa, cplex_lp, bin_vars, obj_name)
    
    
if __name__ == '__main__':
    sys.exit(main())