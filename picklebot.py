from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from argparse import ArgumentParser
from datetime import date, datetime, time, timedelta
from pytz import timezone
from time import sleep
import os

# Calculates the date of the next weekday
def next_weekday(weekday):
	today = datetime.today()
	days_ahead = weekday - today.weekday()
	if days_ahead <= 0:
		days_ahead += 7
	return today + timedelta(days_ahead)

def print_with_timestamp(message):
	current_datetime = datetime.now(timezone('America/Chicago'))
	print(f"[{current_datetime:%x %H:%M:%S.%f}] {message}")
	
def sleep_until(sleep_until_datetime, sleep_interval):
	zone = timezone('America/Chicago')
	while sleep_until_datetime > datetime.now(zone):
		current_datetime = datetime.now(zone)
		remaining_time = sleep_until_datetime - datetime.now(zone)
		print_with_timestamp(f"Will wait until {sleep_until_datetime:%c}: {remaining_time} remaining...")
		sleep(sleep_interval)

# Load arguments
arg_parser = ArgumentParser("picklebot")
arg_parser.add_argument("-c", "--court", help="What court to reserve.", type=str, default="John Simpson 1")
arg_parser.add_argument("-d", "--day", help="What day to reserve (Mon(0) - Sun(6)).", type=int, default=3)
arg_parser.add_argument("-t", "--time", help="What time to reserve (HH:MM:SS)(24 Hour Format).", type=str, default="20:00:00")
arg_parser.add_argument("-u", "--duration", help="Duration to reserve (30 Minutes, 60 Minutes, 90 Minutes, 2 Hours).", type=str, default="2 Hours")
arg_parser.add_argument("-y", "--type", help="Type to reserve (Casual Play, Pickleball Casual Play).", type=str, default="Pickleball Casual Play")
arg_parser.add_argument("-r", "--run", help="What time to run (HH:MM:SS)(24 Hour Format).", type=str, default="07:00:00")
args = arg_parser.parse_args()

COURT = args.court
DAY = args.day
DATE = next_weekday(DAY).date()
TIME = time.fromisoformat(args.time)
DURATION = args.duration
TYPE = args.type
RUN_TIME = time.fromisoformat(args.run)
RUN_DELTA = timedelta(days=-3)
RUN_DATETIME = timezone('America/Chicago').localize(datetime.combine(DATE + RUN_DELTA, RUN_TIME))
WAIT_INTERVAL = 1
PATH = os.path.dirname(os.path.realpath(__file__))

print_with_timestamp(f"{COURT} | {DATE:%A, %B %d, %Y} @{TIME:%l:%M%p} FOR {DURATION} | Running {RUN_DATETIME:%A, %B %d, %Y} @{RUN_TIME:%l:%M%p}")

# Setup Chrome options
print_with_timestamp("Setting up chrome drivers...")
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument('--ignore-ssl-errors=yes')
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--window-size=1920,1080')
# chrome_options.add_argument("--remote-debugging-port=9222")

# Set path to Chrome binary
chrome_options.binary_location = "/opt/chrome/chrome-linux64/chrome"

# Set path to ChromeDriver
chrome_service = ChromeService(executable_path="/opt/chromedriver/chromedriver-linux64/chromedriver")

# Set up driver
driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

# Load credentials
print_with_timestamp("Loading credentials...")
credentials_path = os.path.join(PATH, "credentials")
credentials = open(credentials_path, "r")
USERNAME = credentials.readline().rstrip()
PASSWORD = credentials.readline().rstrip()
# print_with_timestamp(f"{USERNAME}:{PASSWORD}")
credentials.close()

def login():
	# Login
	print_with_timestamp("Logging in...")
	driver.get('https://www.yourcourts.com/yourcourts/security/showLogin')
	WebDriverWait(driver, 10).until(
		EC.presence_of_element_located((By.ID, 'password-field'))
	)
	driver.save_screenshot(os.path.join(PATH, 'login_load.png'))
	field_username = driver.find_element(By.NAME,'username')
	field_username.send_keys(USERNAME)
	field_password = driver.find_element(By.ID,'password-field')
	field_password.send_keys(PASSWORD)
	driver.save_screenshot(os.path.join(PATH, 'login_credentials.png'))
	field_password.submit()

	# Wait for login to complete
	WebDriverWait(driver, 10).until(
		EC.presence_of_element_located((By.ID, 'reservationQuickLink'))
	)
	print_with_timestamp("Logged in...")
	driver.save_screenshot(os.path.join(PATH, 'homepage.png'))

def wait_for_court_reservation():
	# Poll calendar for open reservations up to 12 times (2 minutes)
	tries_remaining = 12
	reservation_url = None
	while reservation_url is None and tries_remaining > 0:
		try:
			# Load calendar page
			tries_remaining -= 1
			formatted_date = DATE.strftime("%m") + "%2F" + DATE.strftime("%d") + "%2F" + DATE.strftime("%Y")
			print_with_timestamp("Retrieving Calendar...")
			driver.get('https://www.yourcourts.com/yourcourts/facility/viewschedule?reservationDate=' + formatted_date)

			# Get reservation url
			title = COURT + " @" + TIME.strftime("%l") + ":" + TIME.strftime("%M") + TIME.strftime("%p")
			xpath = "//a[@title='" + title + "']"
			WebDriverWait(driver, 10).until(
				EC.presence_of_element_located((By.XPATH, xpath))
			)
			reservation_url = driver.find_element(By.XPATH, xpath).get_attribute('href')
			driver.save_screenshot(os.path.join(PATH, 'schedule.png'))
			print_with_timestamp(f"Reservation url found: {reservation_url}")
			
		except Exception as e:
			print_with_timestamp(f"No open reservations found, {tries_remaining} tries remaining...")
			
	return reservation_url
	
def reserve_court(reservation_url):
	# Try to reserve the court up to 6 times (1 minute)
	tries_remaining = 6
	success = None
	while success is None and tries_remaining > 0:
		try:
			# Load reservation page
			tries_remaining -= 1
			driver.get(reservation_url)
			sleep(1) # frustrating, but without this there is a >50% that the duration field doesn't update
			
			# Set reservation duration
			print_with_timestamp("Setting reservation duration...")
			select_duration = Select(driver.find_element(By.ID, 'duration'))
			select_duration.select_by_visible_text(DURATION)
			selected_duration = select_duration.first_selected_option.text

			# Set reservation type
			print_with_timestamp("Setting reservation type...")
			select_type = Select(driver.find_element(By.ID, 'reservationTypeId'))
			select_type.select_by_visible_text(TYPE)
			selected_type = select_type.first_selected_option.text

			# Submit reservation
			print_with_timestamp(f"Submitting reservation: {selected_type} - {selected_duration}")
			driver.find_element(By.ID,'submitButtonId').click()

			# Confirm reservation
			elem = WebDriverWait(driver, 10).until(
				EC.presence_of_element_located((By.XPATH, "//div[@class='alert alert-success alert-styled-left alert-arrow-left alert-bordered']"))
			)
			success = True
			print_with_timestamp("Reservation booked successfully!")
			driver.save_screenshot(os.path.join(PATH, 'reservation_confirmation.png'))

		except Exception as e:
			print_with_timestamp(f"Reservation failed, {tries_remaining} tries remaining: {e}")
			driver.save_screenshot(os.path.join(PATH, f"reservation_error_{tries_remaining}.png"))

def start():
	try:
		# Wait until 1 minute before RUN_TIME
		sleep_until(RUN_DATETIME + timedelta(minutes=-1), WAIT_INTERVAL)

		# Login
		login()
		
		# Wait until RUN_TIME
		sleep_until(RUN_DATETIME, WAIT_INTERVAL)
		
		# Reserve court
		reservation_url = wait_for_court_reservation()
		if reservation_url is not None:
			reserve_court(reservation_url)

	except Exception as e:
		print_with_timestamp(f"An error occurred: {e}")
		driver.save_screenshot(os.path.join(PATH, 'error.png'))

	finally:
		# Close driver
		driver.quit()

# Start
start()