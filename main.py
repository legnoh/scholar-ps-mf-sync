import logging,os,time,sys,yaml
import modules.scholarps as sp
import modules.prometheus as prom
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from pyvirtualdisplay import Display
from prometheus_client import CollectorRegistry, start_http_server

HTTP_PORT = os.environ.get('PORT', 8000)
LOGLEVEL = os.environ.get('LOGLEVEL', logging.INFO)
CONF_FILE = 'config/metrics.yml'
SP_USERNAME = os.environ['SCHOLARPS_ID']
SP_PASSWORD = os.environ['SCHOLARPS_PASSWORD']
SP_NUMBER = os.environ['SCHOLARPS_NUMBER']

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s : %(message)s', datefmt="%Y-%m-%dT%H:%M:%S%z")

def main():
    logging.info("# initializing exporter...")
    registry = CollectorRegistry()
    start_http_server(int(HTTP_PORT), registry=registry)

    logging.info("# loading config files...")
    with open('config/metrics.yml', 'r') as stream:
        metrics = yaml.load(stream, Loader=yaml.FullLoader)

    logging.info("# initializing chromium options...")
    options = webdriver.ChromeOptions()
    options.add_argument('--user-data-dir=/tmp/scholorps-exporter/userdata')

    root_metrics = {}

    for definition in metrics['scholarship']['metrics']:
        m = prom.create_metric_instance(definition, registry)
        root_metrics[definition['name']] = m

    while True:
        if os.path.isfile("/.dockerenv"):
            logging.info("# start display...")
            display = Display(visible=0, size=(1024, 768))
            display.start()

        logging.info("# start selenium...")
        driver = webdriver.Chrome(service=Service(), options=options)
        driver.implicitly_wait(0.5)

        logging.info("# login to Scholarnet Personal...")
        driver = sp.login(driver, SP_USERNAME, SP_PASSWORD, SP_NUMBER)
        if driver == None:
            sys.exit(1)

        logging.info("# get scholarship list...")
        scholarship_infolist = sp.get_scholarship_list(driver)

        logging.info("# update metrics...")
        if scholarship_infolist != None:
            for scholarship_info in scholarship_infolist:
                common_labels = [scholarship_info['奨学生番号']]
                for key, instance in root_metrics.items():
                    if key == "scholarship_prev_repayment_amount_jpy":
                        labels = [scholarship_info['奨学生番号']]
                        labels.append(scholarship_info['前回入金年月日'].strftime("%Y-%m-%d"))
                        prom.set_metrics(instance, labels, scholarship_info['前回入金額'])
                    elif key == "scholarship_prev_transfer_amount_jpy":
                        labels = [scholarship_info['奨学生番号']]
                        labels.append(scholarship_info['振替日'].strftime("%Y-%m-%d"))
                        labels.append(scholarship_info['振替結果'])
                        prom.set_metrics(instance, labels, scholarship_info['振替額'])
                    else:
                        labels = [scholarship_info['奨学生番号']]
                        target_metrics = next((r for r in metrics['scholarship']['metrics'] if r.get("name") == key), None)
                        if target_metrics['desc'] in scholarship_info:
                            prom.set_metrics(instance, labels, scholarship_info[target_metrics['desc']])

        logging.info("# exporting scrolarship data successfully!")
        driver.quit()
        if os.path.isfile("/.dockerenv"):
            display.stop()
        time.sleep(60*24) # 24時間に1回実行

if __name__ == "__main__":
    main()
