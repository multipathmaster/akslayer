from flask import Flask, render_template, redirect, url_for, flash, jsonify, request, Response
from pygtail import Pygtail
import logging, os, time, subprocess, csv, json, psutil
from forms import UpgradeForm

app = Flask(__name__)
app.config["SECRET_KEY"] = "A Moose Goes Burp"
app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", True)
app.config["JSON_AS_ASCII"] = False

LOG_FILE = 'akslayer_logviewer.log'
log = logging.getLogger('__name__')
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG)


def is_process_running(process_name):
    try:
        result = subprocess.run(['ps', 'aux'], stdout=subprocess.PIPE)
        processes = result.stdout.decode('utf-8')
        if process_name in processes:
            return True
        return False
    except Exception as e:
        log.error(f"Error checking process: {e}")
        return False


@app.route('/', methods=['get', 'post'])
def entry_point():
    log.info("route =>'/env' - hit!")
    form = UpgradeForm()
    if (form.validate_on_submit()):
        if is_process_running('main.py'):
            log.info("Upgrade process is already running.")
            return render_template('base.html', form=form, error="Upgrade process is already running!")
        file_json = form.file_json.data
        environment = form.environment.data
        webhook_url = form.webhook_url.data
        kube_version_low = form.kube_version_low.data
        kube_version_mid = form.kube_version_mid.data
        kube_version_hi = form.kube_version_hi.data
        kube_version_final = form.kube_version_final.data
        rc_authtoken = form.rc_authtoken.data
        rc_userid = form.rc_userid.data
        rc_alias = form.rc_alias.data
        rc_channel = form.rc_channel.data
        #if no data in our rc variables
        if not rc_authtoken and not rc_userid and not rc_alias and not rc_channel:
            #build our command from our form data
            upgrade_kube_cmd = "python3 main.py etc/{} {} {} {} {} {} {} &".format(file_json, environment, webhook_url, kube_version_low, kube_version_mid, kube_version_hi, kube_version_final)
            log.warning(upgrade_kube_cmd)
            os.system(upgrade_kube_cmd)
            log.warning("Data received: Now redirecting and starting upgrade process...")
            flash("Starting upgrade process...")
            return redirect(url_for('entry_point'))
        else:
            #if there is data in our rc variables 
            #build our command from our form data
            upgrade_kube_cmd = "python3 main.py etc/{} {} {} {} {} {} {} {} {} {} {} &".format(file_json, environment, webhook_url, kube_version_low, kube_version_mid, kube_version_hi, kube_version_final, rc_authtoken, rc_userid, rc_alias, rc_channel)
            log.warning(upgrade_kube_cmd)
            os.system(upgrade_kube_cmd)
            log.warning("Data received: Now redirecting and starting upgrade process...")
            flash("Starting upgrade process...")
            return redirect(url_for('entry_point'))
    else:
        log.info("Standard GET method...")
        return render_template('base.html', form=form)


@app.route('/progress')
def progress():
    def generate():
        x = 0
        while x <= 100:
            #yield "data:" + str(x) + "\n\n"
            x = x + 10
            time.sleep(0.05)
    return Response(generate(), mimetype= 'text/event-stream')


@app.route('/log')
def progress_log():
    def generate():
        for line in Pygtail('log/upgrade_kube.log', every_n=1):
            yield "data:" + str(line) + "\n\n"
            time.sleep(0.05)
    return Response(generate(), mimetype= 'text/event-stream')


@app.route('/env')
def show_env():
	log.info("route =>'/env' - hit")
	env = {}
	for k,v in request.environ.items(): 
		env[k] = str(v)
	log.info("route =>'/env' [env]:\n%s" % env)
	return env


@app.route('/upload', methods=['post'])
def upload_file():
    if 'csv_file' not in request.files:
        log.info("No file part in request")
        return redirect(url_for('entry_point'))

    csv_file = request.files['csv_file']

    if csv_file.filename == '':
        log.info("No selected file")
        return redirect(url_for('entry_point'))
    
    if csv_file and csv_file.filename.endswith('.csv'):
        # Save the file to the /usr/local/bin/etc folder
        csv_path = os.path.join('/usr/local/bin/etc', csv_file.filename)
        csv_file.save(csv_path)
        log.info(f"File {csv_file.filename} uploaded successfully.")
        flash("Uploaded successfully...")

        # Convert CSV to JSON
        json_path = os.path.splitext(csv_path)[0] + '.json'
        try:
            with open(csv_path, mode='r', encoding='utf-8-sig') as file:
                csv_reader = csv.DictReader(file)
                rows = list(csv_reader)
            
            with open(json_path, mode='w', encoding='utf-8') as json_file:
                json.dump(rows, json_file, indent=2)
            
            log.info(f"File {csv_file.filename} converted to JSON successfully - {json_path}.")
            json_path_filename_only = os.path.basename(json_path)
            flash(json_path_filename_only)
        except Exception as e:
            log.error(f"Error during conversion: {e}")
            flash("Error during conversion")
            return redirect(url_for('entry_point'))
        
        return redirect(url_for('entry_point'))
    else:
        log.info("Invalid file format. Please upload a CSV file.")
        flash("Invalid file format.  CSV files only.")
        return redirect(url_for('entry_point'))
    

@app.route('/stop', methods=['post'])
def stop_process():
    log.info("Terminating the process...")
    kill_cmd = "for x in $(ps -ef | grep -i 'python3 main.py' | grep -v grep | awk '{ print $2 }'); do kill -9 $x; done"
    subprocess.Popen(kill_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    log.info(kill_cmd)
    log.info("Process terminated successfully...")
    flash("Upgrade process terminated successfully...")
    return redirect(url_for('entry_point'))


@app.route('/system_stats')
def system_stats():
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    memory_percent = memory_info.percent
    # Check if 'main.py' is running
    process_running = False
    for process in psutil.process_iter(['pid', 'name', 'cmdline']):
        cmdline = process.info.get('cmdline')
        if cmdline and 'main.py' in cmdline:
            process_running = True
            break
    return jsonify(cpu=cpu_percent, memory=memory_percent, main_running=process_running)


if (__name__ == '__main__'):
    app.run(debug=True, host='0.0.0.0', port=5000)
