import sys
import subprocess
import json
import time
import logging
from httplib2 import Http
from datetime import datetime

#sys.argv from akslayer_upgrader.py
if len(sys.argv) == 8:
  clusters = sys.argv[1]
  actuate = sys.argv[2]
  webhook_url = sys.argv[3]
  kube_version_low = sys.argv[4]
  kube_version_mid = sys.argv[5]
  kube_version_hi = sys.argv[6]
  kube_version_final = sys.argv[7]
elif len(sys.argv) == 12:
  clusters = sys.argv[1]
  actuate = sys.argv[2]
  webhook_url = sys.argv[3]
  kube_version_low = sys.argv[4]
  kube_version_mid = sys.argv[5]
  kube_version_hi = sys.argv[6]
  kube_version_final = sys.argv[7]

  rc_authtoken = sys.argv[8]
  rc_userid = sys.argv[9]
  rc_alias = sys.argv[10]
  rc_channel = sys.argv[11]

  rocketc_message_headers = {
    'Accept': 'application/json; charset=UTF8',
    'Content-Type': 'application/json; charset=UTF-8',
    'X-Auth-Token': rc_authtoken,
    'X-User-Id': rc_userid
  }
else:
  print("Missing sys.argv's!")
  sys.exit(1)

#file content extraction into variable
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

#webhook URL wildcard slack identifier
slack_url_wildcard = "slack"

#webhook URL wildcard rc identifier
rocketc_url_wildcard = "3000"

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

#setup logging
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

#strip the major minor version away from the inputed data to compare
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
  #slack under here
  if slack_url_wildcard in WEBHOOK_URL:
    response = http_obj.request(
      url,
      method='POST',
      headers=message_headers,
      data=json.dumps(bot_message),
    )
    return response
  #rocketchat under here
  elif rocketc_url_wildcard in WEBHOOK_URL:
    rc_bot_message = {
      'alias': rc_alias,
      'channel': rc_channel,
      'text': collision + spaceme + cluster_status_google + returnme
    }
    response = http_obj.request(
      url,
      method='POST',
      headers=rocketc_message_headers,
      body=json.dumps(rc_bot_message),
    )
    return response
  # google below here
  else:
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
  if slack_url_wildcard in WEBHOOK_URL:
    response = http_obj.request(
      url,
      method='POST',
      headers=message_headers,
      data=json.dumps(bot_message),
    )
    return response
  elif rocketc_url_wildcard in WEBHOOK_URL:
    rc_bot_message = {
      'alias': rc_alias,
      'channel': rc_channel,
      'text': collision + spaceme + cluster_status_google + returnme
    }
    response = http_obj.request(
      url,
      method='POST',
      headers=rocketc_message_headers,
      body=json.dumps(rc_bot_message),
    )
    return response
  else:
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
  if slack_url_wildcard in WEBHOOK_URL:
    response = http_obj.request(
      url,
      method='POST',
      headers=message_headers,
      data=json.dumps(bot_message),
    )
    return response
  elif rocketc_url_wildcard in WEBHOOK_URL:
    rc_bot_message = {
      'alias': rc_alias,
      'channel': rc_channel,
      'text': collision + spaceme + cluster_status_google + returnme
    }
    response = http_obj.request(
      url,
      method='POST',
      headers=rocketc_message_headers,
      body=json.dumps(rc_bot_message),
    )
    return response
  else:
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
  if slack_url_wildcard in WEBHOOK_URL:
    response = http_obj.request(
      url,
      method='POST',
      headers=message_headers,
      data=json.dumps(bot_message),
    )
    return response
  elif rocketc_url_wildcard in WEBHOOK_URL:
    rc_bot_message = {
      'alias': rc_alias,
      'channel': rc_channel,
      'text': collision + spaceme + cluster_status_google + returnme
    }
    response = http_obj.request(
      url,
      method='POST',
      headers=rocketc_message_headers,
      body=json.dumps(rc_bot_message),
    )
    return response
  else:
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
  if slack_url_wildcard in WEBHOOK_URL:
    response = http_obj.request(
      url,
      method='POST',
      headers=message_headers,
      data=json.dumps(bot_message),
    )
    return response
  elif rocketc_url_wildcard in WEBHOOK_URL:
    rc_bot_message = {
      'alias': rc_alias,
      'channel': rc_channel,
      'text': collision + spaceme + cluster_status_google + returnme
    }
    response = http_obj.request(
      url,
      method='POST',
      headers=rocketc_message_headers,
      body=json.dumps(rc_bot_message),
    )
    return response
  else:
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
  if slack_url_wildcard in WEBHOOK_URL:
    response = http_obj.request(
      url,
      method='POST',
      headers=message_headers,
      data=json.dumps(bot_message),
    )
    return response
  elif rocketc_url_wildcard in WEBHOOK_URL:
    rc_bot_message = {
      'alias': rc_alias,
      'channel': rc_channel,
      'text': cluster_head
    }
    response = http_obj.request(
      url,
      method='POST',
      headers=rocketc_message_headers,
      body=json.dumps(rc_bot_message),
    )
    return response
  else:
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
    if slack_url_wildcard in WEBHOOK_URL:
      response = http_obj.request(
        url,
        method='POST',
        headers=message_headers,
        data=json.dumps(bot_message),
      )
      return response
    elif rocketc_url_wildcard in WEBHOOK_URL:
      rc_bot_message = {
      'alias': rc_alias,
      'channel': rc_channel,
      'text': agent_pools
    }
      response = http_obj.request(
        url,
        method='POST',
        headers=rocketc_message_headers,
        body=json.dumps(rc_bot_message),
      )
      return response
    else:
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
  if slack_url_wildcard in WEBHOOK_URL:
    response = http_obj.request(
      url,
      method='POST',
      headers=message_headers,
      data=json.dumps(bot_message),
    )
    return response
  elif rocketc_url_wildcard in WEBHOOK_URL:
    rc_bot_message = {
      'alias': rc_alias,
      'channel': rc_channel,
      'text': collision + spaceme + display_skipping_google + returnme
    }
    response = http_obj.request(
      url,
      method='POST',
      headers=rocketc_message_headers,
      body=json.dumps(rc_bot_message),
    )
    return response
  else:
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
  if slack_url_wildcard in WEBHOOK_URL:
    response = http_obj.request(
      url,
      method='POST',
      headers=message_headers,
      data=json.dumps(bot_message),
    )
    return response
  elif rocketc_url_wildcard in WEBHOOK_URL:
    rc_bot_message = {
      'alias': rc_alias,
      'channel': rc_channel,
      'text': skull + spaceme + display_failed_google + spaceme + returnme
    }
    response = http_obj.request(
      url,
      method='POST',
      headers=rocketc_message_headers,
      body=json.dumps(rc_bot_message),
    )
    return response
  else:
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
  if slack_url_wildcard in WEBHOOK_URL:
    response = http_obj.request(
      url,
      method='POST',
      headers=message_headers,
      data=json.dumps(bot_message),
    )
    return response
  elif rocketc_url_wildcard in WEBHOOK_URL:
    rc_bot_message = {
      'alias': rc_alias,
      'channel': rc_channel,
      'text': collision + spaceme + cluster_status_google + returnme
    }
    response = http_obj.request(
      url,
      method='POST',
      headers=rocketc_message_headers,
      body=json.dumps(rc_bot_message),
    )
    return response
  else:
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


# Start of getdepinfo() section
# Helper function to run a subprocess and log the output
def run_command(cmd, description):
  logging.info(description)
  logging.info(cmd)
  process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  output = process.communicate()[0]
  output_str = str(output, 'UTF-8')
  logging.info(output_str)
  return output_str

# Helper function for kubent and node processing
def process_kubent_and_nodes(env_path, cluster_name, env):
  kubent_script = "{}_script_path_{}".format('kubent', env.lower())
  nodes_list = "{}/{}.{}.nodes".format(env_path, cluster_name, env)
    
  # Running kubent
  logging.info(kubent_script)
  run_command(kubent_script, f"Running kubent for {env}")

  # Process nodes
  try:
    with open(nodes_list, "r") as nodes_items:
      logging.info(f"{cluster_name} has these nodes:")
      for node in nodes_items:
        logging.info(node.strip())
      logging.info(f"Nodes are populated to {env_path}/{cluster_name}.{env}.nodes")
  except Exception as e:
    logging.error(f"Error processing nodes: {e}")

# Helper function for upgrade status
def process_upgrade_status(env_path, cluster_name, env, resource_group):
  upgrade_status_file = "{}/{}.{}.status".format(env_path, cluster_name, env)
  upgrade_cmd = f"az aks show --name {cluster_name} --resource-group {resource_group} > {upgrade_status_file}"
    
  # Running upgrade status command
  run_command(upgrade_cmd, f"Gathering upgrade status for {env}")
    
  # Load status
  try:
    with open(upgrade_status_file, "r") as upgrade_file:
      global agentpoolprofiles, current_upgrade_status, ustatus_load
      ustatus_load = json.load(upgrade_file)
      agentpoolprofiles = ustatus_load['agentPoolProfiles']
      head_prs = ustatus_load['provisioningState']
      current_upgrade_status = head_prs if head_prs != "Succeeded" else "Succeeded"
  except Exception as e:
    logging.error(f"Error processing upgrade status: {e}")

# info gathering function
def getdepinfo():
  global agentpoolprofiles, current_upgrade_status, ustatus_load, outputcred2
  # Setting subscription
  run_command(f"az account set --subscription {x['subscription']}", "Setting up subscription")
  # Getting credentials
  outputcred2 = run_command(f"az aks get-credentials --resource-group {x['resource_group']} --name {x['cluster_name']}", "Getting AKS credentials")
  if "ERROR" in outputcred2:
    logging.critical("Detected an error in credentials, sending message to webhook")
    communicate_teams() if teams_url_wildcard in WEBHOOK_URL else communicate_google_chat()
    remove_config_file()
    return
  # Fixing kube config
  run_command(fixconfig_script_path, "Running sed on kube config")
  # Processing environment-based data
  env_paths = {
    "Development": "dev",
    "UAT": "uat",
    "Stage": "stage",
    "QA": "qa",
    "Production": "prod"
  }
  if x['env'] in env_paths:
    process_kubent_and_nodes(env_paths[x['env']], x['cluster_name'], x['env'])
    process_upgrade_status(env_paths[x['env']], x['cluster_name'], x['env'], x['resource_group'])
  else:
    logging.critical(f"{x['cluster_name']} {x['env']} {x['version']} No valid environment detected...")
    return
# End of getdepinfo() section


# Start of upgrade_aks
def upgrade_aks(group_number, kube_version):
  logging.info('In the upgrade_aks function -- GROUP {}'.format(group_number))

  if current_upgrade_status == "Failed":
    failed_message = "ERROR: {} {} {}, the current provisioningState is: {}".format(x['cluster_name'], x['env'], x['version'], current_upgrade_status)
    logging.critical(failed_message)
    logging.info('Sending message to WEBHOOK_URL')
    if teams_url_wildcard in WEBHOOK_URL:
      display_head_teams()
      display_agentpoolprofiles_teams()
      display_failed_teams()
    else:
      display_head_google_chat()
      display_agentpoolprofiles_google_chat()
      display_failed_google_chat()
    remove_config_file()
    return
    
  elif current_upgrade_status != "Succeeded":
    cant_message = "WARNING: Cannot upgrade {} {} {}, the current provisioningState is: {}".format(x['cluster_name'], x['env'], x['version'], current_upgrade_status)
    logging.warning(cant_message)
    logging.info('Sending message to WEBHOOK_URL')
    if teams_url_wildcard in WEBHOOK_URL:
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
    
  if "ERROR" in outputcred2:
    cluster_opc2_check = "{} {} {} Aborting upgrade process, context was not switched to current iteration of cluster.".format(x['cluster_name'], x['env'], x['version'])
    logging.critical(cluster_opc2_check)
    remove_config_file()
    return
    
  yes_message = "INFO: Upgrading {} {} {}, the current provisioningState is: {}".format(x['cluster_name'], x['env'], x['version'], current_upgrade_status)
  logging.info(yes_message)
  logging.info('Sending message to WEBHOOK_URL')
    
  if teams_url_wildcard in WEBHOOK_URL:
    display_head_teams()
    display_agentpoolprofiles_teams()
  else:
    display_head_google_chat()
    display_agentpoolprofiles_google_chat()
    
  logging.info('Function - Running az command to upgrade control plane. Group {}'.format(group_number))
  logging.info('Sending upgrade message to WEBHOOK_URL')
    
  if teams_url_wildcard in WEBHOOK_URL:
    upgrade_teams()
  else:
    upgrade_google_chat()
    
  ucp_cmd = "az aks upgrade --resource-group {} --name {} --kubernetes-version {} --no-wait -y".format(x['resource_group'], x['cluster_name'], kube_version)
  output = subprocess.Popen(ucp_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  response = output.communicate()[0]
  response2 = str(response, 'UTF-8')
    
  if "ERROR" in response2:
    logging.critical('Sending message to WEBHOOK_URL')
    if teams_url_wildcard in WEBHOOK_URL:
      error_upgrade_teams()
    else:
      error_upgrade_google_chat()
    cluster_resp2_check = "{} {} {} Detected an error in response2 variable".format(x['cluster_name'], x['env'], x['version'])
    logging.critical(cluster_resp2_check)
    remove_config_file()
    return
    
  cluster_version_upgrade = "{} {} going to version {}".format(x['cluster_name'], x['env'], kube_version)
  logging.info(cluster_version_upgrade)
    
  if teams_url_wildcard in WEBHOOK_URL:
    positive_upgrade_teams()
  else:
    positive_upgrade_google_chat()
    
  logging.info(ucp_cmd)
  x['version'] = "{}".format(kube_version)
  cluster_version_upgrade = "{} {} going to version {}".format(x['cluster_name'], x['env'], x['version'])
  logging.info(cluster_version_upgrade)
  updatejson()
  remove_config_file()
# End of upgrade_aks


# Start of cycle
#function to assign a cluster to a cycle type for upgrading
def cycle():
  logging.info('In the cycle function')
    
  versions = {
    'low': get_major_minor(kube_version_low),
    'mid': get_major_minor(kube_version_mid),
    'hi': get_major_minor(kube_version_hi),
    'final': get_major_minor(kube_version_final)
  }
    
  def handle_version(version, upgrade_function, final_check=False):
    getdepinfo()
    if version not in ustatus_load['kubernetesVersion']:
      error_msg = "{} does not have a version of {}, it has a value of: {}".format(x['cluster_name'], version, ustatus_load['kubernetesVersion'])
      logging.critical(error_msg)
      logging.warning("Updating json file and skipping until next run...")
      send_version_mismatch_message()
      x['version'] = ustatus_load['kubernetesVersion']
      updatejson()
      remove_config_file()
      return False
        
    if final_check:
      logging.info("{} {} {} is already up to date.".format(x['cluster_name'], x['env'], x['version']))
      logging.warning('Not upgrading, this cluster is already up to date...')
      send_already_upgraded_message()
      remove_config_file()
      return False
        
    upgrade_function()
    return True

  def send_version_mismatch_message():
    logging.info('Sending message to WEBHOOK_URL')
    if teams_url_wildcard in WEBHOOK_URL:
      version_mismatch_teams()
    else:
      version_mismatch_google_chat()

  def send_already_upgraded_message():
    logging.info('Sending already upgraded message to WEBHOOK_URL')
    if teams_url_wildcard in WEBHOOK_URL:
      already_upgraded_teams()
    else:
      already_upgraded_google_chat()

  # Version checks and respective function calls
  if versions['low'] in x['version']:
    if not handle_version(versions['low'], lambda: upgrade_aks(2, kube_version_mid)):
      return
  elif versions['mid'] in x['version']:
    if not handle_version(versions['mid'], lambda: upgrade_aks(1, kube_version_hi)):
      return
  elif versions['hi'] in x['version']:
    if not handle_version(versions['hi'], lambda: upgrade_aks(0, kube_version_final)):
      return
  elif versions['final'] in x['version']:
    if not handle_version(versions['final'], None, final_check=True):
      return
  else:
    error_msg = "{} at version {} is too old to be upgraded with AKSlayer...".format(x['cluster_name'], x['version'])
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
    #ever need to terminate the while loop, can simply keep_while_alive = "False"
    if (keep_while_alive == "False"):
      sys.exit(1)
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
      else:
        timestampme()
        cluster_env_error = "{} {} {} does not match the environment selected with the AKS Upgrader".format(x['cluster_name'],x['env'],x['version'])
        logging.critical(cluster_env_error)
        cluster_env_error2 = "Please fix any issues within the CSV file and try again..."
        logging.critical(cluster_env_error2)
        keep_while_alive = False

