import os

from crontab import CronTab

# change directory to the project root
print("Changing directory to the project root...")
os.chdir("/home/galkepler/Projects/plasticityhub")

# update the database
print("Updating the database...")
os.system(
    "/home/galkepler/Projects/plasticityhub/.venv/bin/python manage.py update_database"
)

# populate the procedures
print("Populating procedures...")
os.system(
    "/home/galkepler/Projects/plasticityhub/.venv/bin/python manage.py populate_procedures --overwrite"
)

# aggregate kepost procedures
print("Aggregating KePost procedures...")
os.system(
    "/home/galkepler/Projects/plasticityhub/.venv/bin/python manage.py aggregate_kepost_parcellations --destination /media/storage/yalab-dev/plasticityhub --metrics adc --overwrite"
)
