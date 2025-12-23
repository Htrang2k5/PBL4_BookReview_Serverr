import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.constants import Regex

SAVE_FOLDER = '/Users/htrang/Documents/University/PBL4/BookReview_Server'
API_ADDRESS = 'static/images'


def get_default_chrome_options():
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    # chạy nhẹ hơn (có thể bật nếu muốn)
    # options.add_argument("--headless=new")
    # options.add_argument("--disable-gpu")
    # options.add_argument("--no-sandbox")
    return options


def make_driver():
    options = get_default_chrome_options()
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    return driver


def download_image(image_url: str) -> str:
    os.makedirs(os.path.join(SAVE_FOLDER, API_ADDRESS), exist_ok=True)

    file_name = image_url.split('/')[-1]
    save_path = os.path.join(SAVE_FOLDER, API_ADDRESS, file_name)
    address = os.path.join('/' + API_ADDRESS, file_name)

    # timeout + raise_for_status để tránh treo
    r = requests.get(image_url, timeout=20)
    r.raise_for_status()
    with open(save_path, 'wb') as f:
        f.write(r.content)
    return address


def click_detail_review(url: str, month: int):
    driver = None
    try:
        driver = make_driver()
        driver.get(url)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'time.entry-date'))
        )

        time_element = driver.find_element(By.CSS_SELECTOR, 'time.entry-date')
        publish_time = time_element.get_attribute('datetime')
        created_at = datetime.fromisoformat(publish_time)

        if created_at.month != month:
            return None

        title = driver.find_element(By.CSS_SELECTOR, 'h1.tdb-title-text').text

        parent_image = driver.find_element(By.CSS_SELECTOR, 'div.td_block_wrap.tdi_56')
        image_element = parent_image.find_element(By.CSS_SELECTOR, 'div.tdb-block-inner a')
        image_url = image_element.get_attribute('href')

        parent_content = driver.find_element(By.CSS_SELECTOR, 'div.vc_column.tdi_50')
        content_element = parent_content.find_element(By.CSS_SELECTOR, 'div.td_block_wrap.tdi_57')
        content = content_element.get_attribute('outerHTML')
        content = re.sub(Regex.pattern, '', content)

        address = download_image(image_url)

        return [created_at, title, content, address, url]
    except Exception as e:
        print('Loi crawl bai viet:', url, '-', e)
        return None
    finally:
        if driver:
            driver.quit()


def get_links_from_page(page_url: str) -> list[str]:
    driver = None
    try:
        driver = make_driver()
        driver.get(page_url)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.td-module-container'))
        )

        time.sleep(2)
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        time.sleep(1)

        reviews = driver.find_elements(By.CSS_SELECTOR, '.entry-title a')
        return [r.get_attribute('href') for r in reviews if r.get_attribute('href')]
    finally:
        if driver:
            driver.quit()


def find_reviews_threaded(month: int, start_page=18, end_page=22, max_workers=3):
    # 1) lấy link (tuần tự) để tránh mở quá nhiều driver cùng lúc
    all_links = []
    for i in range(start_page, end_page + 1):
        page_url = f'https://www.fahasa.com/blog/category/review-sach/page/{i}'
        links = get_links_from_page(page_url)
        all_links.extend(links)

    print('Tong link:', len(all_links))

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(click_detail_review, link, month) for link in all_links]

        for fut in as_completed(futures):
            item = fut.result()
            if item is not None:
                results.append(item)

    return results


if __name__ == '__main__':
    # ví dụ crawl tháng 12
    data = find_reviews_threaded(month=12, start_page=18, end_page=22, max_workers=3)
    print('Crawl duoc:', len(data))
