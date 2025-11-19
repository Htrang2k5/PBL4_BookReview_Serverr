import re
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.constants import Regex


def get_default_chrome_options():
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    return options


def make_driver():
    options = get_default_chrome_options()
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    return driver


def fine_content(url):
    driver = make_driver()
    driver.get(url)
    wait = WebDriverWait(driver, 15)
    wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, '.td-module-container')
        )
    )
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
    time.sleep(3)
    driver.implicitly_wait(10)
    elements = driver.find_elements(By.CSS_SELECTOR, '.td-module-meta-info')

    for element in elements:
        html_content = element.get_attribute('outerHTML')
        clean_content = re.sub(Regex.pattern, '', html_content)
        print('----- Article Info -----')
        print(clean_content)
        print('------------------------')
    driver.quit()


def click_detail_review(url, month: int) -> list[datetime, str, str] | None:
    driver = make_driver()
    driver.get(url)
    time.sleep(3)
    driver.implicitly_wait(10)
    content_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (
                By.CLASS_NAME,
                'wpb_wrapper',
            )
        )
    )
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
    # lay thoi gian cua bai viet
    time_element = driver.find_element(By.CSS_SELECTOR, 'time.entry-date')
    publish_time = time_element.get_attribute('datetime')
    created_at = datetime.fromisoformat(publish_time)
    if created_at.month != month:
        driver.quit()
        return None
    # lay title bai viet
    title_element = driver.find_element(By.CSS_SELECTOR, 'h1.tdb-title-text')
    title = title_element.text
    print(f'Tieu de bai viet: {title}')
    # lay noi dung bai viet
    parent_content = driver.find_element(
        By.CSS_SELECTOR, 'div.vc_column.tdi_50'
    )
    content_element = parent_content.find_element(
        By.CSS_SELECTOR, 'div.td_block_wrap.tdi_57'
    )
    content = content_element.get_attribute('outerHTML')
    content = re.sub(Regex.pattern, '', content)

    print('----- Noi dung bai viet -----')
    print(content)
    print('-----------------------------')
    driver.quit()

    return created_at, title, content


def find_reviews(month: int) -> list[list[datetime, str, str, str]]:
    i = 1
    results = []
    for i in range(1, 23):
        url = f'https://www.fahasa.com/blog/category/review-sach/page/{i}'
        driver = make_driver()
        driver.get(url)
        wait = WebDriverWait(driver, 15)
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '.td-module-container')
            )
        )
        time.sleep(3)
        driver.implicitly_wait(10)
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        reviews = driver.find_elements(By.CSS_SELECTOR, '.entry-title a')
        review_links = [review.get_attribute('href') for review in reviews]
        for link in review_links:
            result = click_detail_review(link, month)
            if result is not None:
                result.append(link)
                results.append(result)
        driver.quit()
    return results


if __name__ == '__main__':
    # test_start_learning_chrome()
    # fine_content('https://www.fahasa.com/blog/category/review-sach')
    # click_detail_review('https://www.fahasa.com/blog/category/review-sach')
    find_reviews()
