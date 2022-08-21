from time import sleep

from tasks import pull_issues

if __name__ == "__main__":
    while True:
        pull_issues()
        sleep(float(60 * 10))
