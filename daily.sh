#!/bin/zsh

today=$(date +"%d-%m-%Y")
echo "###### Today is $today ######"

cd /home/galkepler/Projects/plasticityhub
source /home/galkepler/Projects/plasticityhub/.venv/bin/activate
echo "Running daily.sh"

## Update the database
echo "Updating database"
python manage.py update_database

## Update the derivatives
echo "Updating derivatives"
python manage.py update_derivatives

## populate the procedures
## echo "Populating procedures"
## python manage.py populate_procedures --overwrite

## aggregate the parcellations
## echo "Aggregating parcellations"
## python manage.py aggregate_kepost_parcellations --destination /media/storage/yalab-dev/plasticityhub --metrics adc --overwrite
