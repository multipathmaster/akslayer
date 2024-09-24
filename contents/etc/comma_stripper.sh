#!/bin/bash
#pass our file name to this script as $1
FILE=$1
#var check
if [[ ${FILE} == "" ]]; then
  echo -e "Variable FILE has a null value, expecting it to have one"
  exit 1
fi

#open the file and replace wild characters and single quotes to double quotes
#then use awk to pull in the entire file and strip the last possible comma in the whole file
do_it(){
  cat ${FILE} | sed -e s/\\\\ufeff//g | sed -e s/\'/\"/g | awk '/,/{for(i=1;i<=n;i++)print s[i];n=0}{s[++n]=$0}END{p=1;while(i=index(substr(s[1],p),","))p+=i;s[1]=substr(s[1],1,p-2)substr(s[1],p);for(i=1;i<=n;i++)print s[i]}' > ${FILE}_nocomma
  if [[ `echo ${PIPESTATUS[@]} | grep -v 0` == "" ]]; then
    echo -e "No errors detected during wild characters and single to double conversion. Continuing..."
  else
    echo -e "Error with the sed/sed/awk portion of the bash script"
    exit 1
  fi
}

#replace the original file with the new string file with the edits called nocomma_FILENAME.json
create_final_file(){
mv ${FILE}_nocomma ${FILE}
  if [[ $? -ne 0 ]]; then
    echo -e "Could not move the file to the new file name, there was an error."
    exit 1
  fi
}

main(){
  do_it
  create_final_file
}

main
