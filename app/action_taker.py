import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

def take_action(host_id, action_code, container_name):
	if action_code == 0:
		stop_url = 'http://' + host_id + ':4243/containers/' + container_name + '/stop'
		resp = request_retry_session(backoff_factor = 1).post(stop_url)
		print(resp.status_code)
		if resp.status_code != 204 and resp.status_code != 304:
			raise Exception('Unable to stop the container! ' + resp.text)
	elif action_code == 1:
		restart_url = 'http://' + host_id + ':4243/containers/' + container_name + '/restart'
		resp = request_retry_session(backoff_factor = 1).post(restart_url)
		print(resp.status_code)
		if resp.status_code != 204:
			raise Exception('Unable to stop the container! ' + resp.text)

# Create a custom retry session with an exponential backoff strategy
def request_retry_session(
	retries=3,
	backoff_factor=0.3,
	status_forcelist=(500),
	session=None):
	session = session or requests.Session()
	retry = Retry(
		total=retries,
		read=retries,
		connect=retries,
		backoff_factor=backoff_factor,
		status_forcelist=status_forcelist,
	)
	adapter = HTTPAdapter(max_retries=retry)
	session.mount('http://', adapter)
	session.mount('https://', adapter)
	return session

take_action('54.183.224.168', 1, 'testphoton')