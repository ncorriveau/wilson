import logging
import sys
from typing import List

# from openai import OpenAI
# from pydantic import BaseModel, Field

# from src.db import CREATE_QUERIES, create_connection, query_db
# from src.queries.open_ai.appointments import OAIRequest, send_rqt

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

driver = webdriver.Chrome()
driver.get("https://zocdoc.com")
input("Please solve the CAPTCHA and then press Enter in this terminal...")

search_field = driver.find_element(By.NAME, "patient-powered-search-input")
# Enter search text
search_field.send_keys("Lisette Giraud")
# Submit the search by simulating the Enter key
search_field.send_keys(Keys.ENTER)
# assert "Python" in driver.title
# elem = driver.find_element(By.NAME, "q")
# elem.clear()
# elem.send_keys("pycon")
# elem.send_keys(Keys.RETURN)
# assert "No results found." not in driver.page_source
driver.close()
