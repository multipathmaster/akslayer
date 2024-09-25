import sys
import subprocess
import json
import time
import logging
from httplib2 import Http
from datetime import datetime

#variables
clusters = sys.argv[1]
actuate = sys.argv[2]
webhook_url = sys.argv[3]
kube_version_low = sys.argv[4]
kube_version_mid = sys.argv[5]
kube_version_hi = sys.argv[6]
kube_version_final = sys.argv[7]
file = open(clusters)
jload = json.load(file)
#closing file immediately
file.close()

#global for while loop
global keep_while_alive
keep_while_alive = "True"

#webhook URL
WEBHOOK_URL = webhook_url
#webhook URL wildcard teams identifier
teams_url_wildcard = "office"

#path to bash utils
path_to_bashutils = "/usr/local/bin/bash_utils"

#path to kube config removal command
path_to_kube_config_rm = "rm /root/.kube/config"

#bash scripts for bash / kubectl tasks
fixconfig_script_path = "{}/fix_config.sh".format(path_to_bashutils)
kubent_script_path_dev = "{}/kubent_dep_dev.sh".format(path_to_bashutils)
kubent_script_path_uat = "{}/kubent_dep_uat.sh".format(path_to_bashutils)
kubent_script_path_stage = "{}/kubent_dep_stage.sh".format(path_to_bashutils)
kubent_script_path_qa = "{}/kubent_dep_qa.sh".format(path_to_bashutils)
kubent_script_path_prod = "{}/kubent_dep_prod.sh".format(path_to_bashutils)

#logging
logging.basicConfig(filename='log/upgrade_kube.log', filemode='w', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
logging.info('Starting up...')


# Start of functions
#function to handle all the writes, i.e. updating the json file after each successful 'az aks upgrade' run
def updatejson():
  logging.info('Updating json file...')
  file = open(clusters, "w+")
  file.write(json.dumps(jload, indent=2))
  file.close()

#function to handle an append when a skip is occured (adds to the end of the jload dict)
def appendit():
  logging.info('Appending function')
  append_it = {
    "cluster_name": x['cluster_name'],
    "env": x['env'],
    "version": x['version'],
    "resource_group": x['resource_group'],
    "location": x['location'],
    "subscription": x['subscription']
  }
  jload.append(append_it)

#function to handle deletions when a skip occurs
def delete_element():
  logging.info('delete json element')
  for i in range(len(jload)):
    if (jload[i]["cluster_name"] == x['cluster_name']):
      jload.pop(i)
      break

#function for a time stamp for every single run -- REPORTING
def timestampme():
  tstamp = time.time()
  date_time = datetime.fromtimestamp(tstamp)
  logging.info(date_time)
  #print(date_time)

#finally implemented a remove_config_file function as i am tired of messing with $HOME/.kube/config 
def remove_config_file():
  rmconfig = subprocess.Popen(path_to_kube_config_rm, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  outputrmconfig = rmconfig.communicate()[0]
  outputrmconfig2 = str(outputrmconfig, 'UTF-8')
  #print(outputrmconfig2)

#strip the major minor version away from the inputted data to compare
def get_major_minor(version):
  return ".".join(version.split(".")[:2])
# End of functions


# Start of comms
#initial communication to g-chat/slack
def communicate_google_chat():
  url = WEBHOOK_URL
  returnme = "\n"
  spaceme = " "
  if ("ERROR" in outputcred2):
    cluster_status_google = "{} {} {} Detected an ERROR with context switching, not upgrading...".format(x['cluster_name'],x['env'],x['version'])
    collision = " 💥"
  else:  
    cluster_status_google = "{} {} {} Is good for an upgrade...".format(x['cluster_name'],x['env'],x['version'])
    collision = " ✅"
  bot_message = {
    'text': collision + spaceme + cluster_status_google + returnme
  }
  message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
  http_obj = Http()
  response = http_obj.request(
    uri=url,
    method='POST',
    headers=message_headers,
    body=json.dumps(bot_message),
  )
  return response

#communication to g-chat / slack if we are going to upgrade
def upgrade_google_chat():
  url = WEBHOOK_URL
  returnme = "\n"
  spaceme = " "
  collision = " ✅"
  cluster_status_google = "{} {} {} Is upgrading now with --no-wait.  This will take time for this cluster...".format(x['cluster_name'],x['env'],x['version'])
  bot_message = {
    'text': collision + spaceme + cluster_status_google + returnme
  }
  message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
  http_obj = Http()
  response = http_obj.request(
    uri=url,
    method='POST',
    headers=message_headers,
    body=json.dumps(bot_message),
  )
  return response

#communication to g-chat / slack
def already_upgraded_google_chat():
  url = WEBHOOK_URL
  returnme = "\n"
  spaceme = " "
  collision = " ✅"
  cluster_status_google = "{} {} {} Has already been upgraded to the latest version...".format(x['cluster_name'],x['env'],x['version'])
  bot_message = {
    'text': collision + spaceme + cluster_status_google + returnme
  }
  message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
  http_obj = Http()
  response = http_obj.request(
    uri=url,
    method='POST',
    headers=message_headers,
    body=json.dumps(bot_message),
  )
  return response

#communication to g-chat / slack if the upgrade encountered any errors
def error_upgrade_google_chat():
  url = WEBHOOK_URL
  returnme = "\n"
  spaceme = " "
  collision = " 💥"
  cluster_status_google = "{} {} {} Detected an ERROR with the upgrade...".format(x['cluster_name'],x['env'],x['version'])
  bot_message = {
    'text': collision + spaceme + cluster_status_google + returnme
  }
  message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
  http_obj = Http()
  response = http_obj.request(
    uri=url,
    method='POST',
    headers=message_headers,
    body=json.dumps(bot_message),
  )
  return response

#communication to g-chat / slack if the upgrade command was successful - i.e. the command, not the WHOLE job (of upgrading)
def positive_upgrade_google_chat():
  url = WEBHOOK_URL
  returnme = "\n"
  spaceme = " "
  collision = " ✅"
  cluster_status_google = "{} {} {} Upgrade has been initiated, please check on this cluster in Azure...".format(x['cluster_name'],x['env'],x['version'])
  bot_message = {
    'text': collision + spaceme + cluster_status_google + returnme
  }
  message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
  http_obj = Http()
  response = http_obj.request(
    uri=url,
    method='POST',
    headers=message_headers,
    body=json.dumps(bot_message),
  )
  return response

#communication to g-chat / slack displaying the head of the cluster from az aks show
def display_head_google_chat():
  url = WEBHOOK_URL
  head_name = ustatus_load['name']
  head_ps = ustatus_load['powerState']['code']
  head_prs = ustatus_load['provisioningState']
  head_kv = ustatus_load['kubernetesVersion']
  head_ckv = ustatus_load['currentKubernetesVersion']
  head_loc = ustatus_load['location']
  triple_space = "   "
  cluster_head = "{}{}, Power: {}, State: {}, version: {}, location: {} \n".format(triple_space, head_name, head_ps, head_prs, head_kv, head_loc)
  bot_message = {
    'text': cluster_head
  }
  message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
  http_obj = Http()
  response = http_obj.request(
    uri=url,
    method='POST',
    headers=message_headers,
    body=json.dumps(bot_message),
  )
  return response

#communication to g-chat / slack displaying the agentpoolprofiles from az aks show
def display_agentpoolprofiles_google_chat():
  url = WEBHOOK_URL
  for z in agentpoolprofiles:
    mode = z.get('mode')
    name = z.get('name')
    count = z.get('count')
    power_state = z.get('powerState', {}).get('code')
    state = z.get('provisioningState')
    version = z.get('orchestratorVersion')
    current_version = z.get('currentOrchestratorVersion')
    triple_space = "   "
    agent_pools = "{}{}, name: {}, Count: {}, Power: {}, State: {}, Version: {} \n".format(triple_space, mode, name, count, power_state, state, version)
    bot_message = {
      'text': agent_pools
    }
    message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
    http_obj = Http()
    response = http_obj.request(
      uri=url,
      method='POST',
      headers=message_headers,
      body=json.dumps(bot_message),
    )
    return response

#communication to g-chat / slack that x iteration is skipping the upgrade
def display_skipping_google_chat():
  url = WEBHOOK_URL
  returnme = "\n"
  spaceme = " "
  collision = " ⏱"
  display_skipping_google = "{} {} {} Skipping upgrade because provisioningState is: {}".format(x['cluster_name'],x['env'],x['version'],current_upgrade_status)
  bot_message = {
    'text': collision + spaceme + display_skipping_google + returnme
  }
  message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
  http_obj = Http()
  response = http_obj.request(
    uri=url,
    method='POST',
    headers=message_headers,
    body=json.dumps(bot_message),
  )
  return response

#communicaiton to g-chat / slack that x iteration is in a failed state
def display_failed_google_chat():
  url = WEBHOOK_URL
  returnme = "\n"
  spaceme = " "
  skull = " ☠"
  display_failed_google = "{} {} {} Skipping upgrade because provisioningState is: {}".format(x['cluster_name'],x['env'],x['version'],current_upgrade_status)
  bot_message = {
    'text': skull + spaceme + display_failed_google + spaceme + returnme
  }
  message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
  http_obj = Http()
  response = http_obj.request(
    uri=url,
    method='POST',
    headers=message_headers,
    body=json.dumps(bot_message),
  )
  return response

#communication to g-chat / slack  that x iteration spreadsheet and azure reporting are a mismatch
def version_mismatch_google_chat():
  url = WEBHOOK_URL
  returnme = "\n"
  spaceme = " "
  collision = " ⏱"
  cluster_status_google = "{} {} {} is not the same version from azure which is : {} \n Updating version in spreadsheet and skipping until next run...".format(x['cluster_name'],x['env'],x['version'],ustatus_load['kubernetesVersion'])
  bot_message = {
    'text': collision + spaceme + cluster_status_google + returnme
  }
  message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
  http_obj = Http()
  response = http_obj.request(
    uri=url,
    method='POST',
    headers=message_headers,
    body=json.dumps(bot_message),
  )
  return response

# teams chat for comms
#initial communication to teams
def communicate_teams():
  url = WEBHOOK_URL
  if "ERROR" in outputcred2:
    cluster_status_teams = "{} {} {} Detected an ERROR with context switching, not upgrading...".format(x['cluster_name'], x['env'], x['version'])
    collision = "💥"
  else:
    cluster_status_teams = "{} {} {} Is good for an upgrade...".format(x['cluster_name'], x['env'], x['version'])
    collision = "✅"
  bot_message = {
    "@type": "MessageCard",
    "@context": "http://schema.org/extensions",
    "themeColor": "0076D7",
    "summary": "AKS Upgrade Status",
    "sections": [{
      "activityTitle": f"{collision} {cluster_status_teams}",
      "activitySubtitle": "Upgrade Notification",
      "text": "Status of the Kubernetes upgrade."
    }]
  }
  message_headers = {'Content-Type': 'application/json'}
  http_obj = Http()
  response = http_obj.request(url, method='POST', headers=message_headers, data=json.dumps(bot_message))
  return response

#communication to teams if we are going to upgrade
def upgrade_teams():
  url = WEBHOOK_URL
  collision = " ✅"
  cluster_status_teams = "{} {} {} Is upgrading now with --no-wait.  This will take time for this cluster...".format(x['cluster_name'],x['env'],x['version'])
  bot_message = {
    "@type": "MessageCard",
    "@context": "http://schema.org/extensions",
    "themeColor": "0076D7",
    "summary": "AKS Upgrading",
    "sections": [{
      "activityTitle": f"{collision} {cluster_status_teams}",
      "activitySubtitle": "Upgrade Notification",
      "text": "Upgrading."
    }]
  }
  message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
  http_obj = Http()
  response = http_obj.request(url, method='POST', headers=message_headers, data=json.dumps(bot_message))
  return response

#communication to teams if we are already upgraded
def already_upgraded_teams():
  url = WEBHOOK_URL
  collision = " ✅"
  cluster_status_teams = "{} {} {} Has already been upgraded to the latest version...".format(x['cluster_name'],x['env'],x['version'])
  bot_message = {
    "@type": "MessageCard",
    "@context": "http://schema.org/extensions",
    "themeColor": "0076D7",
    "summary": "Already Upgraded",
    "sections": [{
      "activityTitle": f"{collision} {cluster_status_teams}",
      "activitySubtitle": "Already Upgraded",
      "text": "Already Upgraded."
    }]
  }
  message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
  http_obj = Http()
  response = http_obj.request(url, method='POST', headers=message_headers, data=json.dumps(bot_message))
  return response

#communication to teams if the upgrade encountered any errors
def error_upgrade_teams():
  url = WEBHOOK_URL
  collision = " 💥"
  cluster_status_teams = "{} {} {} Detected an ERROR with the upgrade...".format(x['cluster_name'],x['env'],x['version'])
  bot_message = {
    "@type": "MessageCard",
    "@context": "http://schema.org/extensions",
    "themeColor": "0076D7",
    "summary": "Detected Error",
    "sections": [{
      "activityTitle": f"{collision} {cluster_status_teams}",
      "activitySubtitle": "Error Detected",
      "text": "Error Detected With The Upgrade."
    }]
  }
  message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
  http_obj = Http()
  response = http_obj.request(url, method='POST', headers=message_headers, data=json.dumps(bot_message))
  return response

#communication to teams if the upgrade command was successful - i.e. the command, not the WHOLE job (of upgrading)
def positive_upgrade_teams():
  url = WEBHOOK_URL
  collision = " ✅"
  cluster_status_teams = "{} {} {} Upgrade has been initiated, please check on this cluster in Azure...".format(x['cluster_name'],x['env'],x['version'])
  bot_message = {
    "@type": "MessageCard",
    "@context": "http://schema.org/extensions",
    "themeColor": "0076D7",
    "summary": "Upgrade Initiated",
    "sections": [{
      "activityTitle": f"{collision} {cluster_status_teams}",
      "activitySubtitle": "Upgrade Initiated",
      "text": "Upgrade Initiated."
    }]
  }
  message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
  http_obj = Http()
  response = http_obj.request(url, method='POST', headers=message_headers, data=json.dumps(bot_message))
  return response

#communication to teams displaying the head of the cluster from az aks show
def display_head_teams():
  url = WEBHOOK_URL
  head_name = ustatus_load['name']
  head_ps = ustatus_load['powerState']['code']
  head_prs = ustatus_load['provisioningState']
  head_kv = ustatus_load['kubernetesVersion']
  head_ckv = ustatus_load['currentKubernetesVersion']
  head_loc = ustatus_load['location']
  cluster_head = "{}, Power: {}, State: {}, version: {}, location: {} \n".format(head_name, head_ps, head_prs, head_kv, head_loc)
  bot_message = {
    "@type": "MessageCard",
    "@context": "http://schema.org/extensions",
    "themeColor": "0076D7",
    "summary": "Cluster Head",
    "sections": [{
      "activityTitle": f"{cluster_head}",
      "activitySubtitle": "Cluster Head",
      "text": "Showing Cluster Head."
    }]
  }
  message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
  http_obj = Http()
  response = http_obj.request(url, method='POST', headers=message_headers, data=json.dumps(bot_message))
  return response

#communication to teams displaying the agentpoolprofiles from az aks show
def display_agentpoolprofiles_teams():
  url = WEBHOOK_URL
  for z in agentpoolprofiles:
    mode = z.get('mode')
    name = z.get('name')
    count = z.get('count')
    power_state = z.get('powerState', {}).get('code')
    state = z.get('provisioningState')
    version = z.get('orchestratorVersion')
    current_version = z.get('currentOrchestratorVersion')
    agent_pools = "{}, name: {}, Count: {}, Power: {}, State: {}, Version: {} \n".format(mode, name, count, power_state, state, version)
    bot_message = {
      "@type": "MessageCard",
      "@context": "http://schema.org/extensions",
      "themeColor": "0076D7",
      "summary": "Agent Pools",
      "sections": [{
        "activityTitle": f"{agent_pools}",
        "activitySubtitle": "Agent Pools",
        "text": "Showing Agent Pools."
      }]
    }
    message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
    http_obj = Http()
    response = http_obj.request(url, method='POST', headers=message_headers, data=json.dumps(bot_message))
    return response

#communication to teams that x iteration is skipping the upgrade
def display_skipping_teams():
  url = WEBHOOK_URL
  collision = " ⏱"
  display_skipping_teams = "{} {} {} Skipping upgrade because provisioningState is: {}".format(x['cluster_name'],x['env'],x['version'],current_upgrade_status)
  bot_message = {
    "@type": "MessageCard",
    "@context": "http://schema.org/extensions",
    "themeColor": "0076D7",
    "summary": "Skipping Upgrade",
    "sections": [{
      "activityTitle": f"{collision} {display_skipping_teams}",
      "activitySubtitle": "Skipping Upgrade",
      "text": "Skipping Upgrade."
    }]
  }
  message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
  http_obj = Http()
  response = http_obj.request(url, method='POST', headers=message_headers, data=json.dumps(bot_message))
  return response

#communication to teams that x iteration is in a failed state
def display_failed_teams():
  url = WEBHOOK_URL
  skull = " ☠"
  display_failed_teams = "{} {} {} Skipping upgrade because provisioningState is: {}".format(x['cluster_name'],x['env'],x['version'],current_upgrade_status)
  bot_message = {
    "@type": "MessageCard",
    "@context": "http://schema.org/extensions",
    "themeColor": "0076D7",
    "summary": "Failed State",
    "sections": [{
      "activityTitle": f"{skull} {display_failed_teams}",
      "activitySubtitle": "Failed State",
      "text": "Cluster Is In A Failed State."
    }]
  }
  message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
  http_obj = Http()
  response = http_obj.request(url, method='POST', headers=message_headers, data=json.dumps(bot_message))
  return response

#communication to teams that x iteration spreadsheet and azure reporting are a mismatch
def version_mismatch_teams():
  url = WEBHOOK_URL
  collision = " ⏱"
  cluster_status_teams = "{} {} {} is not the same version from azure which is : {} \n Updating version in spreadsheet and skipping until next run...".format(x['cluster_name'],x['env'],x['version'],ustatus_load['kubernetesVersion'])
  bot_message = {
    "@type": "MessageCard",
    "@context": "http://schema.org/extensions",
    "themeColor": "0076D7",
    "summary": "Version Mismatch",
    "sections": [{
      "activityTitle": f"{collision} {cluster_status_teams}",
      "activitySubtitle": "Version Mismatch",
      "text": "Version Mismatch Between The CSV File And The Actual Version."
    }]
  }
  message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
  http_obj = Http()
  response = http_obj.request(url, method='POST', headers=message_headers, data=json.dumps(bot_message))
  return response
# End of comms


# Start of info gathering
#function for kubent -t 1.27.3 as well as context switching, resource gathering, and upgrade status checking
def getdepinfo():
  #globals so we can send messages to the g-chat functions above
  global agentpoolprofiles
  global current_upgrade_status
  global ustatus_load
  global outputcred2
  #set subscription
  #print("INFO: Setting up subscription...")
  cluster_sub_setup = "{} {} {} Setting up subscription...".format(x['cluster_name'],x['env'],x['version'])
  logging.info(cluster_sub_setup)
  subcmd = "az account set --subscription {}".format(x['subscription'])
  get_sub = subprocess.Popen(subcmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  outputsub = get_sub.communicate()[0]
  outputsub2 = str(outputsub, 'UTF-8')
  #print(outputsub2)
  #get credentials (merges to local config file)
  credscmd = "az aks get-credentials --resource-group {} --name {}".format(x['resource_group'],x['cluster_name'])
  get_creds = subprocess.Popen(credscmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  outputcred = get_creds.communicate()[0]
  #we need a global variable to if condition key/return to break the loop for x iteration
  outputcred2 = str(outputcred, 'UTF-8')
  #print(outputcred2)
  if ("ERROR" in outputcred2):
    logging.critical('Sending message to WEBHOOK_URL')
    if(teams_url_wildcard in WEBHOOK_URL):
      communicate_teams()
    else:
      communicate_google_chat()
    #print("ERROR: Detected an error in outputcred2 variable")
    cluster_opc2_check = "{} {} {} Detected an error in outputcred2 variable".format(x['cluster_name'],x['env'],x['version'])
    logging.critical(cluster_opc2_check)
    remove_config_file()
    return
  logging.info('Sending message to WEBHOOK_URL')
  if (teams_url_wildcard in WEBHOOK_URL):
    communicate_teams()
  else:
    communicate_google_chat()
  #fix the local config file for kube for ignore-tls-verify: true
  #print("INFO: Running sed...")
  cluster_sed_run = "{} {} {} Running sed...".format(x['cluster_name'],x['env'],x['version'])
  logging.info(cluster_sed_run)
  fixconfig = subprocess.Popen(fixconfig_script_path, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  outputconfig = fixconfig.communicate()[0]
  outputconfig2 = str(outputconfig, 'UTF-8')
  #print(outputconfig2)
  #run the bash utilities scripts in bash_utils, as well as gathering the nodes (kubectl get nodes -o wide)
  #print("INFO: Running kubent to gather deps...")
  cluster_kubent_run = "{} {} {} Running kubent to gather deps...".format(x['cluster_name'],x['env'],x['version'])
  logging.info(cluster_kubent_run)
  if (x['env'] == "Development"):
    getkubent = subprocess.Popen(kubent_script_path_dev, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    outputkubent = getkubent.communicate()[0]
    outputkubent2 = str(outputkubent, 'UTF-8')
    #print(outputkubent2)
    nodes_list = "dev/{}.{}.nodes".format(x['cluster_name'],x['env'])
    nodes_items = open(nodes_list, "r")
    iterate_nodes = nodes_items
    print_message_nodes = "{} has these nodes: ".format(x['cluster_name'])
    print(print_message_nodes)
    for y in iterate_nodes:
      cluster_nodes_list = "{}".format(y)
      print(cluster_nodes_list)
    nodes_logging_message = "Nodes are populated to dev/{}.{}.nodes".format(x['cluster_name'],x['env'])
    logging.info(nodes_logging_message)
    #need to get the state of the cluster below this line for the env type so we can skip if need be
    upgrade_status = "az aks show --name {} --resource-group {} > dev/{}.{}.status".format(x['cluster_name'],x['resource_group'],x['cluster_name'],x['env'])
    upgrade_status_cmd = subprocess.Popen(upgrade_status, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output_upgrade_status_cmd = upgrade_status_cmd.communicate()[0]
    output_upgrade_status_cmd2 = str(output_upgrade_status_cmd, 'UTF-8')
    #print(output_upgrade_status_cmd2)
    upgrade_status_file = "dev/{}.{}.status".format(x['cluster_name'],x['env'])
    open_upgrade_status_file = open(upgrade_status_file)
    ustatus_load = json.load(open_upgrade_status_file)
    open_upgrade_status_file.close()
    agentpoolprofiles = ustatus_load['agentPoolProfiles']
    head_prs = ustatus_load['provisioningState']
    if (head_prs != "Succeeded"):
      current_upgrade_status = head_prs
    elif (head_prs == "Succeeded"):
      current_upgrade_status = head_prs
      #
  elif (x['env'] == "UAT"):
    getkubent = subprocess.Popen(kubent_script_path_uat, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    outputkubent = getkubent.communicate()[0]
    outputkubent2 = str(outputkubent, 'UTF-8')
    nodes_list = "uat/{}.{}.nodes".format(x['cluster_name'],x['env'])
    nodes_items = open(nodes_list, "r")
    iterate_nodes = nodes_items
    print_message_nodes = "{} has these nodes: ".format(x['cluster_name'])
    print(print_message_nodes)
    for y in iterate_nodes:
      cluster_nodes_list = "{}".format(y)
      print(cluster_nodes_list)
    nodes_logging_message = "Nodes are populated to uat/{}.{}.nodes".format(x['cluster_name'],x['env'])
    logging.info(nodes_logging_message)
    upgrade_status = "az aks show --name {} --resource-group {} > uat/{}.{}.status".format(x['cluster_name'],x['resource_group'],x['cluster_name'],x['env'])
    upgrade_status_cmd = subprocess.Popen(upgrade_status, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output_upgrade_status_cmd = upgrade_status_cmd.communicate()[0]
    output_upgrade_status_cmd2 = str(output_upgrade_status_cmd, 'UTF-8')
    upgrade_status_file = "uat/{}.{}.status".format(x['cluster_name'],x['env'])
    open_upgrade_status_file = open(upgrade_status_file)
    ustatus_load = json.load(open_upgrade_status_file)
    open_upgrade_status_file.close()
    agentpoolprofiles = ustatus_load['agentPoolProfiles']
    head_prs = ustatus_load['provisioningState']
    if (head_prs != "Succeeded"):
      current_upgrade_status = head_prs
    elif (head_prs == "Succeeded"):
      current_upgrade_status = head_prs
      #
  elif (x['env'] == "Stage"):
    getkubent = subprocess.Popen(kubent_script_path_stage, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    outputkubent = getkubent.communicate()[0]
    outputkubent2 = str(outputkubent, 'UTF-8')
    nodes_list = "stage/{}.{}.nodes".format(x['cluster_name'],x['env'])
    nodes_items = open(nodes_list, "r")
    iterate_nodes = nodes_items
    print_message_nodes = "{} has these nodes: ".format(x['cluster_name'])
    print(print_message_nodes)
    for y in iterate_nodes:
      cluster_nodes_list = "{}".format(y)
      print(cluster_nodes_list)
    nodes_logging_message = "Nodes are populated to stage/{}.{}.nodes".format(x['cluster_name'],x['env'])
    logging.info(nodes_logging_message)
    upgrade_status = "az aks show --name {} --resource-group {} > stage/{}.{}.status".format(x['cluster_name'],x['resource_group'],x['cluster_name'],x['env'])
    upgrade_status_cmd = subprocess.Popen(upgrade_status, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output_upgrade_status_cmd = upgrade_status_cmd.communicate()[0]
    output_upgrade_status_cmd2 = str(output_upgrade_status_cmd, 'UTF-8')
    upgrade_status_file = "stage/{}.{}.status".format(x['cluster_name'],x['env'])
    open_upgrade_status_file = open(upgrade_status_file)
    ustatus_load = json.load(open_upgrade_status_file)
    open_upgrade_status_file.close()
    agentpoolprofiles = ustatus_load['agentPoolProfiles']
    head_prs = ustatus_load['provisioningState']
    if (head_prs != "Succeeded"):
      current_upgrade_status = head_prs
    elif (head_prs == "Succeeded"):
      current_upgrade_status = head_prs
      #
  elif (x['env'] == "QA"):
    getkubent = subprocess.Popen(kubent_script_path_qa, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    outputkubent = getkubent.communicate()[0]
    outputkubent2 = str(outputkubent, 'UTF-8')
    nodes_list = "qa/{}.{}.nodes".format(x['cluster_name'],x['env'])
    nodes_items = open(nodes_list, "r")
    iterate_nodes = nodes_items
    print_message_nodes = "{} has these nodes: ".format(x['cluster_name'])
    print(print_message_nodes)
    for y in iterate_nodes:
      cluster_nodes_list = "{}".format(y)
      print(cluster_nodes_list)
    nodes_logging_message = "Nodes are populated to qa/{}.{}.nodes".format(x['cluster_name'],x['env'])
    logging.info(nodes_logging_message)
    upgrade_status = "az aks show --name {} --resource-group {} > qa/{}.{}.status".format(x['cluster_name'],x['resource_group'],x['cluster_name'],x['env'])
    upgrade_status_cmd = subprocess.Popen(upgrade_status, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output_upgrade_status_cmd = upgrade_status_cmd.communicate()[0]
    output_upgrade_status_cmd2 = str(output_upgrade_status_cmd, 'UTF-8')
    upgrade_status_file = "qa/{}.{}.status".format(x['cluster_name'],x['env'])
    open_upgrade_status_file = open(upgrade_status_file)
    ustatus_load = json.load(open_upgrade_status_file)
    open_upgrade_status_file.close()
    agentpoolprofiles = ustatus_load['agentPoolProfiles']
    head_prs = ustatus_load['provisioningState']
    if (head_prs != "Succeeded"):
      current_upgrade_status = head_prs
    elif (head_prs == "Succeeded"):
      current_upgrade_status = head_prs
      #
  elif (x['env'] == "Production"):
    getkubent = subprocess.Popen(kubent_script_path_prod, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    outputkubent = getkubent.communicate()[0]
    outputkubent2 = str(outputkubent, 'UTF-8')
    nodes_list = "prod/{}.{}.nodes".format(x['cluster_name'],x['env'])
    nodes_items = open(nodes_list, "r")
    iterate_nodes = nodes_items
    print_message_nodes = "{} has these nodes: ".format(x['cluster_name'])
    print(print_message_nodes)
    for y in iterate_nodes:
      cluster_nodes_list = "{}".format(y)
      print(cluster_nodes_list)
    nodes_logging_message = "Nodes are populated to prod/{}.{}.nodes".format(x['cluster_name'],x['env'])
    logging.info(nodes_logging_message)
    upgrade_status = "az aks show --name {} --resource-group {} > prod/{}.{}.status".format(x['cluster_name'],x['resource_group'],x['cluster_name'],x['env'])
    upgrade_status_cmd = subprocess.Popen(upgrade_status, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output_upgrade_status_cmd = upgrade_status_cmd.communicate()[0]
    output_upgrade_status_cmd2 = str(output_upgrade_status_cmd, 'UTF-8')
    upgrade_status_file = "prod/{}.{}.status".format(x['cluster_name'],x['env'])
    open_upgrade_status_file = open(upgrade_status_file)
    ustatus_load = json.load(open_upgrade_status_file)
    open_upgrade_status_file.close()
    agentpoolprofiles = ustatus_load['agentPoolProfiles']
    head_prs = ustatus_load['provisioningState']
    if (head_prs != "Succeeded"):
      current_upgrade_status = head_prs
    elif (head_prs == "Succeeded"):
      current_upgrade_status = head_prs
      #
  else:
    cluster_nv_env = "{} {} {} No valid environment detected...".format(x['cluster_name'],x['env'],x['version'])
    logging.critical(cluster_nv_env)
    return
  #print("INFO: get sub -", subcmd)
  logging.info(subcmd)
  #print("INFO: get credentials -", credscmd)
  logging.info(credscmd)
# End of info gathering


# Start of upgrades
#function to upgrade GROUP 2's control plane
def upgradecontrolplane2():
  logging.info('In the upgradecontrolplane2 function -- GROUP 2')
  #global variable check from current_upgrade_status in depinfo func
  if (current_upgrade_status == "Failed"):
    failed_message = "ERROR: {} {} {}, the current provisioningState is: {}".format(x['cluster_name'],x['env'],x['version'],current_upgrade_status)
    #print(failed_message)
    logging.critical(failed_message)
    logging.info('Sending message to WEBHOOK_URL')
    if (teams_url_wildcard in WEBHOOK_URL):
      display_head_teams()
      display_agentpoolprofiles_teams()
      display_failed_teams()
    else:
      display_head_google_chat()
      display_agentpoolprofiles_google_chat()
      display_failed_google_chat()
    remove_config_file()
    return
  elif(current_upgrade_status != "Succeeded"):
    cant_message = "WARNING: Cannot upgrade {} {} {}, the current provisioningState is: {}".format(x['cluster_name'],x['env'],x['version'],current_upgrade_status)
    #print(cant_message)
    logging.warning(cant_message)
    logging.info('Sending message to WEBHOOK_URL')
    if (teams_url_wildcard in WEBHOOK_URL):
      display_head_teams()
      display_agentpoolprofiles_teams()
      display_skipping_teams()
    else:
      display_head_google_chat()
      display_agentpoolprofiles_google_chat()
      display_skipping_google_chat()
    logging.info('Skipping upgrade: Appending to end of jload dict')
    #appendit()
    remove_config_file()
    return
  #global variable check from outputcred2 in depinfo func  
  if ("ERROR" in outputcred2):
    cluster_opc2_check = "{} {} {} Aborting upgrade process, context was not switched to current iteration of cluster.".format(x['cluster_name'],x['env'],x['version'])
    logging.critical(cluster_opc2_check)
    #print("ERROR: Aborting upgrade process, context was not switched to current iteration of cluster.")
    remove_config_file()
    return
  yes_message = "INFO: Upgrading {} {} {}, the current provisioningState is: {}".format(x['cluster_name'],x['env'],x['version'],current_upgrade_status)
  #print(yes_message)
  logging.info(yes_message)
  logging.info('Sending message to WEBHOOK_URL')
  if (teams_url_wildcard in WEBHOOK_URL):
    display_head_teams()
    display_agentpoolprofiles_teams()
  else:
    display_head_google_chat()
    display_agentpoolprofiles_google_chat()
  logging.info('Function - Running az command to upgrade control plane. Group 2')
  logging.info('Sending upgrade message to WEBHOOK_URL')
  if (teams_url_wildcard in WEBHOOK_URL):
    upgrade_teams()
  else:
    upgrade_google_chat()
  KUBERNETES_VERSION = kube_version_mid
  ucp2cmd = "az aks upgrade --resource-group {} --name {} --kubernetes-version {} --no-wait -y".format(x['resource_group'],x['cluster_name'],KUBERNETES_VERSION)
  output = subprocess.Popen(ucp2cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  response = output.communicate()[0]
  response2 = str(response, 'UTF-8')
  #print(response2)
  if ("ERROR" in response2):
    logging.critical('Sending message to WEBHOOK_URL')
    if (teams_url_wildcard in WEBHOOK_URL):
      error_upgrade_teams()
    else:
      error_upgrade_google_chat()
    #print("ERROR: Detected an error in response2 variable")
    cluster_resp2_check = "{} {} {} Detected an error in response2 variable".format(x['cluster_name'],x['env'],x['version'])
    logging.critical(cluster_resp2_check)
    remove_config_file()
    return
  cluster_version_upgrade = "{} {} going to version {}".format(x['cluster_name'],x['env'],KUBERNETES_VERSION)
  logging.info(cluster_version_upgrade)
  if (teams_url_wildcard in WEBHOOK_URL):
    positive_upgrade_teams()
  else:
    positive_upgrade_google_chat()
  #print("INFO: Upgrade command: -", ucp2cmd)
  logging.info(ucp2cmd)
  x['version'] = "{}".format(KUBERNETES_VERSION)
  #print(x['cluster_name'], x['env'], "going to version", x['version'])
  cluster_version_upgrade = "{} {} going to version {}".format(x['cluster_name'],x['env'],x['version'])
  logging.info(cluster_version_upgrade)
  updatejson()
  remove_config_file()

#function to upgrade GROUP 1's control plane
def upgradecontrolplane1():
  logging.info('In the upgradecontrolplane1 function -- GROUP 1')
  if (current_upgrade_status == "Failed"):
    failed_message = "ERROR: {} {} {}, the current provisioningState is: {}".format(x['cluster_name'],x['env'],x['version'],current_upgrade_status)
    logging.critical(failed_message)
    logging.info('Sending message to WEBHOOK_URL')
    if (teams_url_wildcard in WEBHOOK_URL):
      display_head_teams()
      display_agentpoolprofiles_teams()
      display_failed_teams()
    else:
      display_head_google_chat()
      display_agentpoolprofiles_google_chat()
      display_failed_google_chat()
    remove_config_file()
    return
  elif(current_upgrade_status != "Succeeded"):
    cant_message = "WARNING: Cannot upgrade {} {} {}, the current provisioningState is: {}".format(x['cluster_name'],x['env'],x['version'],current_upgrade_status)
    logging.warning(cant_message)
    logging.info('Sending message to WEBHOOK_URL')
    if (teams_url_wildcard in WEBHOOK_URL):
      display_head_teams()
      display_agentpoolprofiles_teams()
      display_skipping_teams()
    else:
      display_head_google_chat()
      display_agentpoolprofiles_google_chat()
      display_skipping_google_chat()
    logging.info('Skipping upgrade: Appending to end of jload dict')
    remove_config_file()
    return  
  if ("ERROR" in outputcred2):
    cluster_opc2_check = "{} {} {} Aborting upgrade process, context was not switched to current iteration of cluster.".format(x['cluster_name'],x['env'],x['version'])
    logging.critical(cluster_opc2_check)
    remove_config_file()
    return
  yes_message = "INFO: Upgrading {} {} {}, the current provisioningState is: {}".format(x['cluster_name'],x['env'],x['version'],current_upgrade_status)
  logging.info(yes_message)
  logging.info('Sending message to WEBHOOK_URL')
  if (teams_url_wildcard in WEBHOOK_URL):
    display_head_teams()
    display_agentpoolprofiles_teams()
  else:
    display_head_google_chat()
    display_agentpoolprofiles_google_chat()
  logging.info('Function - Running az command to upgrade control plane. Group 1')
  logging.info('Sending upgrade message to WEBHOOK_URL')
  if (teams_url_wildcard in WEBHOOK_URL):
    upgrade_teams()
  else:
    upgrade_google_chat()
  KUBERNETES_VERSION = kube_version_hi
  ucp1cmd = "az aks upgrade --resource-group {} --name {} --kubernetes-version {} --no-wait -y".format(x['resource_group'],x['cluster_name'],KUBERNETES_VERSION)
  output = subprocess.Popen(ucp1cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  response = output.communicate()[0]
  response2 = str(response, 'UTF-8')
  if ("ERROR" in response2):
    logging.critical('Sending message to WEBHOOK_URL')
    if (teams_url_wildcard in WEBHOOK_URL):
      error_upgrade_teams()
    else:
      error_upgrade_google_chat()
    cluster_resp2_check = "{} {} {} Detected an error in response2 variable".format(x['cluster_name'],x['env'],x['version'])
    logging.critical(cluster_resp2_check)
    remove_config_file()
    return
  cluster_version_upgrade = "{} {} going to version {}".format(x['cluster_name'],x['env'],KUBERNETES_VERSION)
  logging.info(cluster_version_upgrade)
  if (teams_url_wildcard in WEBHOOK_URL):
    positive_upgrade_teams()
  else:
    positive_upgrade_google_chat()
  logging.info(ucp1cmd)
  x['version'] = "{}".format(KUBERNETES_VERSION)
  cluster_version_upgrade = "{} {} going to version {}".format(x['cluster_name'],x['env'],x['version'])
  logging.info(cluster_version_upgrade)
  updatejson()
  remove_config_file()

#function to upgrade GROUP 0's control plane
def upgradecontrolplane0():
  logging.info('In the upgradecontrolplane0 function -- GROUP 0')
  if (current_upgrade_status == "Failed"):
    failed_message = "ERROR: {} {} {}, the current provisioningState is: {}".format(x['cluster_name'],x['env'],x['version'],current_upgrade_status)
    logging.critical(failed_message)
    logging.info('Sending message to WEBHOOK_URL')
    if (teams_url_wildcard in WEBHOOK_URL):
      display_head_teams()
      display_agentpoolprofiles_teams()
      display_failed_teams()
    else:
      display_head_google_chat()
      display_agentpoolprofiles_google_chat()
      display_failed_google_chat()
    remove_config_file()
    return
  elif(current_upgrade_status != "Succeeded"):
    cant_message = "WARNING: Cannot upgrade {} {} {}, the current provisioningState is: {}".format(x['cluster_name'],x['env'],x['version'],current_upgrade_status)
    logging.warning(cant_message)
    logging.info('Sending message to WEBHOOK_URL')
    if (teams_url_wildcard in WEBHOOK_URL):
      display_head_teams()
      display_agentpoolprofiles_teams()
      display_skipping_teams()
    else:
      display_head_google_chat()
      display_agentpoolprofiles_google_chat()
      display_skipping_google_chat()
    logging.info('Skipping upgrade: Appending to end of jload dict')
    remove_config_file()
    return  
  if ("ERROR" in outputcred2):
    cluster_opc2_check = "{} {} {} Aborting upgrade process, context was not switched to current iteration of cluster.".format(x['cluster_name'],x['env'],x['version'])
    logging.critical(cluster_opc2_check)
    remove_config_file()
    return
  yes_message = "INFO: Upgrading {} {} {}, the current provisioningState is: {}".format(x['cluster_name'],x['env'],x['version'],current_upgrade_status)
  logging.info(yes_message)
  logging.info('Sending message to WEBHOOK_URL')
  if (teams_url_wildcard in WEBHOOK_URL):
    display_head_teams()
    display_agentpoolprofiles_teams()
  else:
    display_head_google_chat()
    display_agentpoolprofiles_google_chat()
  logging.info('Function - Running az command to upgrade control plane. Group Final')
  KUBERNETES_VERSION = kube_version_final
  logging.info('Sending upgrade message to WEBHOOK_URL')
  if (teams_url_wildcard in WEBHOOK_URL):
    upgrade_teams()
  else:
    upgrade_google_chat()
  ucp0cmd = "az aks upgrade --resource-group {} --name {} --kubernetes-version {} --no-wait -y".format(x['resource_group'],x['cluster_name'],KUBERNETES_VERSION)
  output = subprocess.Popen(ucp0cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  response = output.communicate()[0]
  response2 = str(response, 'UTF-8')
  if ("ERROR" in response2):
    logging.critical('Sending message to WEBHOOK_URL')
    if (teams_url_wildcard in WEBHOOK_URL):
      error_upgrade_teams()
    else:
      error_upgrade_google_chat()
    cluster_resp2_check = "{} {} {} Detected an error in response2 variable".format(x['cluster_name'],x['env'],x['version'])
    logging.critical(cluster_resp2_check)
    remove_config_file()
    return
  cluster_version_upgrade = "{} {} going to version {}".format(x['cluster_name'],x['env'],KUBERNETES_VERSION)
  logging.info(cluster_version_upgrade)
  if (teams_url_wildcard in WEBHOOK_URL):
    positive_upgrade_teams()
  else:
    positive_upgrade_google_chat()
  logging.info(ucp0cmd)
  x['version'] = "{}".format(KUBERNETES_VERSION)
  cluster_version_upgrade = "{} {} going to version {}".format(x['cluster_name'],x['env'],x['version'])
  logging.info(cluster_version_upgrade)
  updatejson()
  remove_config_file()
# End of upgrades


# Start of cycle
#function to assign a cluster to a cycle type for upgrading
#if "1.24" to pick up any subversions, i.e. 1.24.4 or 1.25.6 etc...
def cycle():
  logging.info('In the cycle function')
  version_low = get_major_minor(kube_version_low)
  version_mid = get_major_minor(kube_version_mid)
  version_hi = get_major_minor(kube_version_hi)
  version_final = get_major_minor(kube_version_final)
  #if ("1.24" in x['version']):
  if (version_low in x['version']):
    getdepinfo()
    #we have to validate that the info in the spreadsheet/json file
    #matches what was received in the getdepinfo() function call (az aks show json return)
    #and if it doesn't we need to update the json file, skip and resume the queue
    #if ("1.24" not in ustatus_load['kubernetesVersion']):
    if (version_low not in ustatus_load['kubernetesVersion']):
      error_msg = "{} does not have a version of {}, it has a value of: {}".format(x['cluster_name'], version_low, ustatus_load['kubernetesVersion'])
      logging.critical(error_msg)
      logging.warning("Updating json file and skipping until next run...")
      logging.info('Sending message to WEBHOOK_URL')
      if (teams_url_wildcard in WEBHOOK_URL):
        version_mismatch_teams()
      else:
        version_mismatch_google_chat()
      x['version'] = ustatus_load['kubernetesVersion']
      updatejson()
      remove_config_file()
      return
    upgradecontrolplane2()
  elif (version_mid in x['version']):
    getdepinfo()
    if (version_mid not in ustatus_load['kubernetesVersion']):
      error_msg = "{} does not have a version of {}, it has a value of: {}".format(x['cluster_name'], version_mid, ustatus_load['kubernetesVersion'])
      logging.critical(error_msg)
      logging.warning("Updating json file and skipping until next run...")
      logging.info('Sending message to WEBHOOK_URL')
      if (teams_url_wildcard in WEBHOOK_URL):
        version_mismatch_teams()
      else:
        version_mismatch_google_chat()
      x['version'] = ustatus_load['kubernetesVersion']
      updatejson()
      remove_config_file()
      return
    upgradecontrolplane1()
  elif (version_hi in x['version']):
    getdepinfo()
    if (version_hi not in ustatus_load['kubernetesVersion']):
      error_msg = "{} does not have a version of {}, it has a value of: {}".format(x['cluster_name'], version_hi, ustatus_load['kubernetesVersion'])
      logging.critical(error_msg)
      logging.warning("Updating json file and skipping until next run...")
      logging.info('Sending message to WEBHOOK_URL')
      if (teams_url_wildcard in WEBHOOK_URL):
        version_mismatch_teams()
      else:
        version_mismatch_google_chat()
      x['version'] = ustatus_load['kubernetesVersion']
      updatejson()
      remove_config_file()
      return
    upgradecontrolplane0()
  elif (version_final in x['version']):
    getdepinfo()
    if (version_final not in ustatus_load['kubernetesVersion']):
      error_msg = "{} does not have a version of {}, it has a value of: {}".format(x['cluster_name'], version_final, ustatus_load['kubernetesVersion'])
      logging.critical(error_msg)
      logging.warning("Updating json file and skipping until next run...")
      logging.info('Sending message to WEBHOOK_URL')
      if (teams_url_wildcard in WEBHOOK_URL):
        version_mismatch_teams()
      else:
        version_mismatch_google_chat()
      x['version'] = ustatus_load['kubernetesVersion']
      updatejson()
      remove_config_file()
      return
    cluster_final_check = "{} {} {} is already up to date.".format(x['cluster_name'],x['env'],x['version'])
    logging.info(cluster_final_check)
    logging.warning('Not upgrading, this cluster is already up to date...')
    logging.info('Sending already upgraded message to WEBHOOK_URL')
    if (teams_url_wildcard in WEBHOOK_URL):
      already_upgraded_teams()
    else:
      already_upgraded_google_chat()
    remove_config_file()
    return
  else:
    error_msg = "{} at version {} is too old to be upgraded with AKSlayer...".format(x['cluster'], x['version'])
    logging.critical(error_msg)
    remove_config_file()
    return
# End of cycle


# Start of bonus feature
#function if all cycle types are called (i.e. all environments)
#why would we need this? this is dangerous. 
#What if we needed to upgrade everything all at once due to some security flaw within AKS?
#perhaps a security breach or something of the sort and we had to act fast.
#now do you see?
#but yeah, don't ever ever run this unless it's absolutely necessary
def actuateall():
  if (x['env'] == "Development"):
    timestampme()
    cluster_env_version = "{} {} {} is going to be in the DEV cycle".format(x['cluster_name'],x['env'],x['version'])
    logging.info(cluster_env_version)
    cycle()
  elif (x['env'] == "UAT"):
    timestampme()
    cluster_env_version = "{} {} {} is going to be in the UAT cycle".format(x['cluster_name'],x['env'],x['version'])
    logging.info(cluster_env_version)
    cycle()
  elif (x['env'] == "QA"):
    timestampme()
    cluster_env_version = "{} {} {} is going to be in the QA cycle".format(x['cluster_name'],x['env'],x['version'])
    logging.info(cluster_env_version)
    cycle()
  elif (x['env'] == "Stage"):
    timestampme()
    cluster_env_version = "{} {} {} is going to be in the STAGE cycle".format(x['cluster_name'],x['env'],x['version'])
    logging.info(cluster_env_version)
    cycle()
  elif (x['env'] == "Production"):
    timestampme()
    cluster_env_version = "{} {} {} is going to be in the PROD cycle".format(x['cluster_name'],x['env'],x['version'])
    logging.info(cluster_env_version)
    cycle()
  logging.info('--------------')
# End of bonus feature


# MAIN PORTION BELOW
#while loop, for loop with if/elif statements within to parse version and environment types
if (__name__ == "__main__"):
  while True:
    #ever need to terminate the while loop, can simply keep_while_alive == "False" somewhere else above
    if (keep_while_alive == "False"):
      sys.exit()
    #start off script by removing the config file for kube
    remove_config_file()
    for x in jload:
      if (actuate == "dev" and x['env'] == "Development"):
        timestampme()
        cluster_env_version = "{} {} {} is going to be in the DEV cycle".format(x['cluster_name'],x['env'],x['version'])
        logging.info(cluster_env_version)
        cycle()
        logging.info('--------------')
      elif (actuate == "qa" and x['env'] == "QA" or actuate == "qa" and x['env'] == "UAT"):
        timestampme()
        cluster_env_version = "{} {} {} is going to be in the QA/UAT cycle".format(x['cluster_name'],x['env'],x['version'])
        logging.info(cluster_env_version)
        cycle()
        logging.info('--------------')
      elif (actuate == "stage" and x['env'] == "Stage"):
        timestampme()
        cluster_env_version = "{} {} {} is going to be in the STAGE cycle".format(x['cluster_name'],x['env'],x['version'])
        logging.info(cluster_env_version)
        cycle()
        logging.info('--------------')
      elif (actuate == "prod" and x['env'] == "Production"):
        timestampme()
        cluster_env_version = "{} {} {} is going to be in the PROD cycle".format(x['cluster_name'],x['env'],x['version'])
        logging.info(cluster_env_version)
        cycle()
        logging.info('--------------')
      elif (actuate == "all"):
        timestampme()
        actuateall()

