import datetime, logging, time, base64, os, pyotp
from zoneinfo import ZoneInfo
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import Select

logger = logging.getLogger(__name__)

def login(driver:WebDriver, email:str, password:str, shogksei_id:str) -> WebDriver | None:
    try:
        logging.info("## jump to scholarnet sign_in page...")
        driver.get('https://scholar-ps.sas.jasso.go.jp/mypage/login_open.do')

        # メール・パスワード入力
        email_box = driver.find_element(By.NAME, 'userId')
        email_box.send_keys(email)
        password_box = driver.find_element(By.NAME, 'password')
        password_box.send_keys(password)
        
        login_button = driver.find_element(By.CSS_SELECTOR, "input#login")
        login_button.click()

        # 奨学生番号入力
        first_box = driver.find_element(By.NAME, "syogkseiBg1")
        second_box = Select(driver.find_element(By.NAME, "syogkseiBg2"))
        third_box = driver.find_element(By.NAME, "syogkseiBg3")

        shogsei_ids = shogksei_id.split("-")

        first_box.send_keys(shogsei_ids[0])
        second_box.select_by_value(shogsei_ids[1])
        third_box.send_keys(shogsei_ids[2])

        next_button = driver.find_element(By.CSS_SELECTOR, "input#syogkseibgKakunin_open_syogkseibgKakunin_submit")
        next_button.click()
        time.sleep(1)

        if driver.title == "全体概要 - スカラネット・パーソナル":
            logging.info("### login successfully!")
            return driver
        logging.error("### login failed: invalid scholarnet personal id")
        save_debug_information(driver, "login_invalid_id")
        return None

    except NoSuchElementException as e:
        logging.error("## login failed with selenium error: %s", e.msg)
        save_debug_information(driver, "login")
        return None

def get_scholarship_list(driver:WebDriver) -> list[dict] | None:
    try:
        logging.info("## jump to scholarship list page...")
        driver.find_element(By.CSS_SELECTOR, "a#syosaiJohoTab").click()

        logging.info("## get scholarship list...")

        # このページはクリックの度にPOSTで再描画されるため、取得した配列を順にクリックするという手法は使えない
        # よって最初に取得した情報は配列処理の要素数取得のみに利用し、その後は再度要素を取得し、現在の要素数から1つ先の要素をクリックする、という流れで処理を行う
        info_table = driver.find_element(By.CSS_SELECTOR, "form#syosaiJoho_open > div.content-main-shosai > div.content-inner > div.content-large-main-syosaiJoho > table > tbody > tr")
        scholarship_list_tr = info_table.find_elements(By.CSS_SELECTOR, "td.syosaiJoho-button-area > input.syogkseiBg-button")
        scholarship_num = len(scholarship_list_tr)

        # 1つ目のから順にクリックし、テーブル情報を取得しKV形式に変換して配列に格納する
        scholarships = []
        for i in range(scholarship_num):
            info_table = driver.find_element(By.CSS_SELECTOR, "form#syosaiJoho_open > div.content-main-shosai > div.content-inner > div.content-large-main-syosaiJoho > table > tbody > tr")
            scholarship_list_tr = info_table.find_elements(By.CSS_SELECTOR, "td.syosaiJoho-button-area > input.syogkseiBg-button")
            scholarship_number = scholarship_list_tr[i].get_attribute("value")
            logging.info("### get scholarship info: %s", scholarship_number)
            scholarship_list_tr[i].click()

            info_table = driver.find_element(By.CSS_SELECTOR, "form#syosaiJoho_open > div.content-main-shosai > div.content-inner > div.content-large-main-syosaiJoho > table > tbody > tr")
            scholarship_info = driver.find_elements(By.CSS_SELECTOR, "td.content-large-main-syosaiJoho-bgColor > table.content-large-main-syosaiJoho-bgColor > tbody > tr.henkan-joho-row, td.content-large-main-syosaiJoho-bgColor > table.content-large-main-syosaiJoho-bgColor > tbody > tr.kinyu-kikan-joho-row")
            scholarship_info_kv = {}
            for row in scholarship_info:
                key = row.find_element(By.CSS_SELECTOR, "th.content-td-syosaiJoho").text.strip()
                value = row.find_element(By.CSS_SELECTOR, "td.content-td-syosaiJoho").text.strip()
                if key == "振替日" or key == "前回入金年月日":
                    # 振替日は日付形式に変換して格納する
                    value = value.split("\n")[0].strip()
                    date_str = value.strip().replace("年", "-").replace("月", "-").replace("日", "")
                    try:
                        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").astimezone(ZoneInfo("Asia/Tokyo"))
                        scholarship_info_kv[key.strip()] = date_obj.date()
                    except ValueError:
                        scholarship_info_kv[key.strip()] = value.strip()
                elif "額" in key or "回数" in key:
                    # 額、回数は数値形式に変換して格納する
                    amount_str = value.strip().replace("円", "").replace("回", "").replace(",", "")
                    try:
                        amount_int = int(amount_str)
                        scholarship_info_kv[key.strip()] = amount_int
                    except ValueError:
                        scholarship_info_kv[key.strip()] = value.strip()
                elif key == "利率":
                    # 利率は小数形式に変換して格納する
                    rate_str = value.strip().replace("％", "")
                    try:
                        rate_float = float(rate_str)
                        scholarship_info_kv[key.strip()] = rate_float
                    except ValueError:
                        scholarship_info_kv[key.strip()] = value.strip()
                else:
                    scholarship_info_kv[key.strip()] = value.strip()
            scholarships.append(scholarship_info_kv)

        return scholarships

    except NoSuchElementException as e:
        logging.error("## get_scholarship_list failed with selenium error: %s", e.msg)
        save_debug_information(driver, "get_scholarship_list")
        return None

def save_debug_information(driver:WebDriver, error_slug: str) -> None:

    issuetitle = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + "-" + error_slug
    debugfile_dir = os.getenv("DEBUGFILE_DIR", "/tmp/scholarps_exporter")

    if not os.path.exists(debugfile_dir):
        os.makedirs(debugfile_dir)

    # save sourcecode
    sourcecode = driver.execute_script("return document.body.innerHTML;")
    sourcecode_path = debugfile_dir + "/" + issuetitle + ".html"
    with open(sourcecode_path, "w") as f:
        f.write(sourcecode)
    logging.info("### sourcecode: %s", sourcecode_path)

    # save screenshot
    screenshot_data = base64.urlsafe_b64decode(driver.execute_cdp_cmd("Page.captureScreenshot", {"captureBeyondViewport": True})["data"])
    screenshot_path = debugfile_dir + "/" + issuetitle + ".png"
    with open(screenshot_path, "wb") as f:
        f.write(screenshot_data)
    logging.info("### screenshot: %s", screenshot_path)
