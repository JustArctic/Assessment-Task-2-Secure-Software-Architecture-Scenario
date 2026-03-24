from urllib.parse import urlparse, urljoin
from flask import request

# Check if redirects are hosted in the same domain, if not then it is a invalid redirect
def is_safe_url(target):
    host_url = request.host_url
    test_url = urljoin(host_url, target)
    return urlparse(test_url).netloc == urlparse(host_url).netloc