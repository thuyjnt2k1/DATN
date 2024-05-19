from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

print('fuck')
# Set up Chrome driver
options = webdriver.ChromeOptions()
# options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36")
# options.add_argument("--start-maximized")
# options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=options)

# Navigate to ResearchGate login page
driver.get("https://www.researchgate.net/profile/Nicolas-Gratiot")

# Find and fill in the email field
# email_field = WebDriverWait(driver, 10).until(
#     EC.presence_of_element_located((By.ID, "input-login"))
# )
# email_field.send_keys("THUY.NT194687@sis.hust.edu.vn")

# # Find and fill in the password field
# password_field = driver.find_element(By.ID, "input-password")
# password_field.send_keys("tolathuy")

# # Submit the login form
# login_button = driver.find_element(By.CLASS_NAME, "nova-legacy-c-button")
# action = ActionChains(driver)
# action.click_and_hold(login_button)
# # Initiate click and hold action on button
# action.perform()
# time.sleep(10)

# action.release(login_button)

# # Wait for the login process to complete (you can adjust the wait time as needed)
# WebDriverWait(driver, 20).until(EC.url_contains("researchgate.net/home"))

# # Now you are logged in and can perform further actions or navigate to other pages

# # Close the driver
# driver.quit()