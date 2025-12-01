import os

import requests
import selenium.webdriver as webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

url = 'https://www.fahasa.com/blog/review-sach-thao-tung-tam-ly-dam-dong-chia-khoa-van-nang-dan-den-thanh-cong/'

driver = webdriver.Chrome()
driver.get(url)
driver.implicitly_wait(10)
content_element = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.wpb_wrapper'))
)
driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')

# lay url hinh anh bai viet
parent_image = driver.find_element(By.CSS_SELECTOR, 'div.td_block_wrap.tdi_56')
image_element = parent_image.find_element(
    By.CSS_SELECTOR, 'div.tdb-block-inner img'
)
image_url = image_element.get_attribute('src')
driver.quit()
print('URL hình ảnh:', image_url)

# Tải hình ảnh về

save_folder = '/Users/htrang/Documents/University/PBL4/BookReview_Server'
api_adress = 'static/images'
os.makedirs(save_folder, exist_ok=True)

# Tự lấy tên file cuối URL
file_name = image_url.split('/')[-1]

save_path = os.path.join(
    save_folder, api_adress, file_name
)  # Đường dẫn lưu file

response = requests.get(image_url)
with open(save_path, 'wb') as f:  # Mở file để ghi
    f.write(response.content)  # Ghi nội dung ảnh vào file

Address = os.path.join('/' + api_adress, file_name)
print('Đã tải:', Address)
