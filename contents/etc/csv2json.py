import sys
import csv
import subprocess

#variables for utility
CSV_PATH = sys.argv[1]
if("csv" in CSV_PATH):
  print("Generating...")
elif("-h" in CSV_PATH or "--help" in CSV_PATH or "?" in CSV_PATH):
  print("Usage: python3 csv2json.py input_file.csv output_file.json")
  sys.exit()
elif("-h" not in CSV_PATH or "--help" not in CSV_PATH or "?" not in CSV_PATH):
  print("Usage: python3 csv2json.py input_file.csv output_file.json")
  sys.exit()

JSON_PATH = sys.argv[2]
if(JSON_PATH == ""):
  print("Usage: python3 csv2json.py input_file.csv output_file.json")
  sys.exit()

#function for var check
def var_check():
  if("csv" in CSV_PATH):
    print("var CSV_PATH checks out...")
  else:
    print("Usage: python3 csv2json.py input_file.csv output_file.json")
    sys.exit()

  if("json" in JSON_PATH):
    print("var JSON_PATH checks out...")
  else:
    print("Usage: python3 csv2json.py input_file.csv output_file.json")
    sys.exit()

#function for the initial format
def initial_format():
  csv_file = csv.DictReader(open(CSV_PATH, 'r'))
  initial_msg = "Building initial file..."
  print(initial_msg)
  file = open(JSON_PATH, 'w')
  file.write("["+"\n")
  for row in csv_file:
    file.write(str(row)+","+"\n")
  file.write("]")
  file.close()

#function to strip wild characters and strip the last comma in the json output
#this is because rstrip will not work with python3 on this as the last character is actually a
#trailing bracket ']' therefore sed and awk to save the day
def final_format():
  building_msg = "Building final file: {}".format(JSON_PATH)
  print(building_msg)
  final_cleanup = "./comma_stripper.sh {}".format(JSON_PATH)
  output = subprocess.Popen(final_cleanup, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  response = output.communicate()[0]
  response2 = str(response, 'UTF-8')
  print(response2)

#main function to call upon var_check, initial_format and then final_format
def main():
  var_check()
  initial_format()
  final_format()

#main function call out
main()

#update initial spreadsheet and change the header values to match the script --> i.e. cluster_name env version location subscription resource_group we won't touch GHS tag
#usage: python3 csv2json.py input_file_name.csv output_file_name.json
