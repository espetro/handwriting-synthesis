# Copyright 2020 Amazon.com, Inc.
# https://github.com/awslabs/handwritten-text-recognition-for-apache-mxnet
# Modified by Quino Terrasa <quino.terrasa+dev@gmail.com>

import os
import tarfile
import urllib
import sys
import json
import numpy as np
import zipfile
import logging


class IAMDataset():
    """ The (Online) IAMDataset provides strokes of handwritten passages written by 
    multiple individuals. The data is available at http://www.fki.inf.unibe.ch
    This script must be executed within the project folder.

    Parameters
    ----------
    credentials: (str, str), Default None 
        Your (username, password) for the IAM dataset. Register at
        http://www.fki.inf.unibe.ch/DBs/iamOnDB/iLogin/index.php
    
    root: str, default: data/raw
        Location to save the database. If the folder is not already present, it's created.
    """

    def __init__(self, credentials=None, root=None):
        if credentials is None or type(credentials) is not None:
            raise ValueError("Credentials must be a tuple '(username, password')")

        self._credentials = credentials
        self._root = os.path.join(".", "data", "raw")  # os-independent path

        url_partial = "http://www.fki.inf.unibe.ch/DBs/iamOnDB/data/{fname}.tar.gz"
        filenames = ["ascii-all", "lineStrokes-all", "original-xml-all"]

        self._data_urls = [url_partial.format(fname=fname) for fname in filenames]
        self._output_dirs = [os.path.join(self._root, _dir) for _dir in ["ascii", "lineStrokes", "original"]]

        if not os.path.isdir(self._root):
            os.makedirs(self._root)

        
        # data = self._get_data()
        # super(IAMDataset, self).__init__(data)

    @staticmethod
    def _reporthook(count, block_size, total_size):
        ''' Prints a process bar that is compatible with urllib.request.urlretrieve
        '''
        toolbar_width = 40
        percentage = float(count * block_size) / total_size * 100
        # Taken from https://gist.github.com/sibosutd/c1d9ef01d38630750a1d1fe05c367eb8
        sys.stdout.write('\r')
        sys.stdout.write("Completed: [{:{}}] {:>3}%"
                         .format('-' * int(percentage / (100.0 / toolbar_width)),
                                 toolbar_width, int(percentage)))
        sys.stdout.flush()

    def _extract(self, archive_file, archive_type, output_dir):
        ''' Helper function to extract archived files. Available for tar.tgz and zip files
        
        Parameter
        ---------
        archive_file: str
            Filepath to the archive file
        archive_type: str, options: [tar, tar.gz, zip]
            Select the type of file you want to extract
        output_dir: str
            Location where you want to extract the files to
        '''
        logging.info("Extracting {}".format(archive_file))

        _available_types = ["tar", "tar.gz", "zip"]
        assert archive_type in _available_types, f"Archive_type {archive_type} is not an available option ({_available_types})"

        if archive_type == "tar.gz":
            tar = tarfile.open(archive_file, "r:gz")
            tar.extractall(os.path.join(self._root, output_dir))
            tar.close()
        elif archive_type == "tar":
            tar = tarfile.open(archive_file, "r:")
            tar.extractall(os.path.join(self._root, output_dir))
            tar.close()
        elif archive_type == "zip":
            zip_ref = zipfile.ZipFile(archive_file, 'r')
            zip_ref.extractall(os.path.join(self._root, output_dir))
            zip_ref.close()

    def _download(self, url):
        ''' Helper function to download using the credentials provided
        Parameter
        ---------
        url: str
            The url of the file you want to download.
        '''
        password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, url, self._credentials[0], self._credentials[1])

        handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
        opener = urllib.request.build_opener(handler)

        urllib.request.install_opener(opener)
        opener.open(url)

        filename = os.path.basename(url)

        print("Downloading {}: ".format(filename)) 
        urllib.request.urlretrieve(
            url,
            reporthook=self._reporthook,
            filename=os.path.join(self._root, filename)
        )[0]
        sys.stdout.write("\n")
            
    def download_data(self):
        ''' Helper function to download and extract the data of the IAM database
        '''
        for url, output_dir in zip(self._data_urls, self._output_dirs):
            logging.info("Downloding data from {}".format(url))
            archive_file = os.path.join(self._root, os.path.basename(url))
            if not os.path.isfile(archive_file):
                self._download(url)
                self._extract(archive_file, archive_type="tar.gz", output_dir=output_dir)
    
