import time

start = time.time()

def splitter():
    url = input("Enter url: ")
    splitted_url = url.split("/")

    while "" in splitted_url:
        splitted_url.remove("")

    domain = ""

    for i in range(len(splitted_url)):
        if splitted_url[i] == "https:" or splitted_url[i] == "http:":
            domain = splitted_url[i + 1]

    return domain, url

def time_manager(url):
    if url == "":
        return 0

    start_time = time.time()

    time.sleep(5)

    end_time = time.time()

    elapsed_time = end_time - start_time

    return elapsed_time
