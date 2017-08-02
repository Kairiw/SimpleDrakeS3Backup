import datetime
import gnupg
import os
import zipfile

from time import strftime, localtime, sleep

import boto3

FORMATED_DATE = strftime("%m%d%Y", localtime())

# Set your list gnupg recipient for the encryption
GPG_RECIPIENTS=[]

# Set S3 bucket upload
S3_BUCKET_NAME = ''


def zipDir(dir_to_zip):

    zip_file_name = "{}.zip".format(dir_to_zip.replace('/', '_'))
    dest_dir = "Backup/tmp"
    zip_file = zipfile.ZipFile(os.path.join(dest_dir, zip_file_name), 'w', zipfile.ZIP_DEFLATED)
    rootlen = len(dir_to_zip) + 1

    for base, dir, files in os.walk(dir_to_zip):
        for file in files:
            fn = os.path.join(base, file)
            zip_file.write(fn, fn[rootlen:])
    zip_file.close()

    return zip_file_name


def encryptZipFile(zip_file_name, gpg_client):

    encrypt_file_name = "{}.zip.gpg".format(zip_file_name.replace('/', '_'))
    dest_dir = "Backup/tmp"

    with open(os.path.join(dest_dir, zip_file_name), 'rb') as f:
        status = gpg_client.encrypt_file(f, recipients=GPG_RECIPIENTS,
                                         output=(os.path.join(dest_dir, encrypt_file_name)))
    return encrypt_file_name

def main():

    # TODO this needs to be configurable rather than just getting the creds and region from .aws
    s3_client = boto3.resource('s3')

    gpg_client = gnupg.GPG()

    # Drake software backs up into directors in the format DS%SoftwareYear%month%day%year-01

    # TODO 2016 software switched to 7zip for backup, so no need to do any ziping just, encypt and upload
    folder_dirs = ['DS2012', 'DS2013', 'DS2014', 'DS2015']

    dirs_to_zip = []

    for dir in folder_dirs:

        # Assumes you are backing up to C:\Backups
        backup_dir = "Backup/" + dir + FORMATED_DATE + '-01'
        if os.path.isdir(backup_dir):
            dirs_to_zip.append(backup_dir)
        else:
            continue

    for dir in dirs_to_zip:

        zip_file_name = zipDir(dir)

        encrypt_file_name = encryptZipFile(zip_file_name, gpg_client)

        key = "{}_{}".format(datetime.date.today(), encrypt_file_name)

        with open(os.path.join("Backup/tmp", encrypt_file_name), 'rb') as ef:
            s3_client.Object(bucket_name=S3_BUCKET_NAME, key=key).put(Body=ef, StorageClass='STANDARD_IA')

        # Sometimes need to sleep a few seconds to let the s3 connection close and file to get freed

        sleep(30)

        # Remove the old files
        os.remove(os.path.join("Backup/tmp", zip_file_name))
        os.remove(os.path.join("Backup/tmp", encrypt_file_name))

if __name__ == '__main__':
    main()
