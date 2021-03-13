# -*- coding: utf-8 -*-
__version__ = "0.06.3"
"""
Source : https://github.com/izneo-get/izneo-get

usage: cafeyn_get.py [-h] [--no-clean] [--no-bookmark]
                     [--output-folder OUTPUT_FOLDER] [--config CONFIG]
                     [--user-agent USER_AGENT] [--force]
                     [url]

Script pour sauvegarder une publication Cafeyn.

positional arguments:
  url                   L'URL de la publication à récupérer ou le chemin vers
                        un fichier local contenant une liste d'URLs

optional arguments:
  -h, --help            show this help message and exit
  --no-clean            Ne supprime pas le répertoire temporaire dans le cas
                        où un PDF a été généré
  --no-bookmark         Ne met pas à jour le statut "lu" de la publication
  --output-folder OUTPUT_FOLDER, -o OUTPUT_FOLDER
                        Répertoire racine de téléchargement
  --config CONFIG       Fichier de configuration
  --user-agent USER_AGENT
                        User agent à utiliser
  --force               Ne demande pas la confirmation d'écrasement de fichier
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import re
import os
import sys
import html
import argparse
import configparser
import shutil
import time
# from bs4 import BeautifulSoup
from PIL import Image
import json
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Util import Padding
import base64
from datetime import datetime
import math
from PyPDF2 import PdfFileMerger
import os.path
from os import path
import time


def requests_retry_session(
    retries=3,
    backoff_factor=1,
    status_forcelist=(500, 502, 504),
    session=None,
):
    """Permet de gérer les cas simples de problèmes de connexions."""
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def clean_name(name):
    """Permet de supprimer les caractères interdits dans les chemins.

    Parameters
    ----------
    name : str
        La chaine de caractère d'entrée.

    Returns
    -------
    str
        La chaine purgée des tous les caractères non désirés.
    """
    chars = '\\/:*<>?"|'
    for c in chars:
        name = name.replace(c, "_")
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"\.+$", "", name)
    return name

def check_version():
    latest_version_url = 'https://raw.githubusercontent.com/izneo-get/cafeyn-get/master/VERSION'
    res = requests.get(latest_version_url)
    if res.status_code != 200:
        print(f"Version {__version__} (impossible to check official version)")
    else:
        latest_version = res.text.strip()
        if latest_version == __version__:
            print(f"Version {__version__} (official version)")
        else:
            print(f"Version {__version__} (official version is different: {latest_version})")
            print("Please check https://github.com/izneo-get/cafeyn-get/releases/latest")
    print()

if __name__ == "__main__":
    # Parse des arguments passés en ligne de commande.
    parser = argparse.ArgumentParser(
        description="""Script pour sauvegarder une publication Cafeyn."""
    )
    parser.add_argument(
        "url",
        type=str,
        default="",
        nargs="?",
        help="L'URL de la publication à récupérer ou le chemin vers un fichier local contenant une liste d'URLs",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        default=False,
        help="Ne supprime pas le répertoire temporaire dans le cas où un PDF a été généré",
    )
    parser.add_argument(
        "--no-bookmark",
        action="store_true",
        default=False,
        help="Ne met pas à jour le statut \"lu\" de la publication",
    )
    parser.add_argument(
        "--output-folder",
        "-o",
        type=str,
        default=None,
        help="Répertoire racine de téléchargement",
    )
    parser.add_argument(
        "--config", type=str, default=None, help="Fichier de configuration"
    )
    parser.add_argument(
        "--user-agent", type=str, default=None, help="User agent à utiliser"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Ne demande pas la confirmation d'écrasement de fichier",
    )
    parser.add_argument(
        "--pause",
        "-p",
        type=float,
        metavar="SECONDS",
        default=0,
        help="Faire une pause (en secondes) entre chaque page",
    )

    # Vérification que c'est la dernière version.
    check_version() 

    args = parser.parse_args()
    no_clean = args.no_clean
    no_bookmark = args.no_bookmark
    force_overwrite = args.force
    pause_sec = args.pause

    # Lecture de la config.
    config = configparser.RawConfigParser()
    if args.config:
        config_name = args.config
    else:
        config_name = re.sub(r"\.py$", ".cfg", os.path.abspath(sys.argv[0]))
        config_name = re.sub(r"\.exe$", ".cfg", config_name)
    config.read(config_name)

    def get_param_or_default(config, param_name, default_value, cli_value=None):
        if cli_value is None:
            return (
                config.get("DEFAULT", param_name)
                if config.has_option("DEFAULT", param_name)
                else default_value
            )
        else:
            return cli_value

    output_folder = get_param_or_default(
        config,
        "output_folder",
        os.path.dirname(os.path.abspath(sys.argv[0])) + "/DOWNLOADS",
        args.output_folder,
    )
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    user_agent = get_param_or_default(config, "user_agent", "", args.user_agent)
    # Paramétrages liés à la session.
    cafeyn_authtoken = get_param_or_default(config, "cafeyn_authtoken", "")
    cafeyn_webSessionId = get_param_or_default(config, "cafeyn_webSessionId", "")
    cafeyn_userGroup = get_param_or_default(config, "cafeyn_userGroup", "")

    base_url = args.url
    while base_url.upper() != "Q" and not re.match(
        "https://reader.cafeyn.co/(.+?)/(.+?)/(.+)", base_url
    ):
        base_url = input(
            'URL de la publication au format "https://reader.cafeyn.co/{pays}/{publicationId}/{issueId}" ("Q" pour quitter) : '
        )

    if base_url.upper() == "Q":
        sys.exit()

    if not cafeyn_authtoken or not cafeyn_webSessionId or not cafeyn_userGroup:
        print("[ERREUR] Impossible de trouver les valeurs dans la configuration.")
        print(f'cafeyn_authtoken = "{cafeyn_authtoken}"')
        print(f'cafeyn_webSessionId = "{cafeyn_webSessionId}"')
        print(f'cafeyn_userGroup = "{cafeyn_userGroup}"')

    if not user_agent:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"
    s = requests.Session()

    _, publication, issue = re.match("https://reader.cafeyn.co/(.+?)/(.+?)/(.+)", base_url).groups()

    mag_infos_url = f"https://api.lekiosk.com/api/v1/reader/publications/{publication}/issues/{issue}/signedurls"

    # On génère une nouvelle clé RSA.
    # priv_key = RSA.import_key(open('privatekey.pkcs8').read())
    priv_key = RSA.generate(1024)
    pub_key = priv_key.publickey().exportKey("PEM").decode("utf-8")
    for e in ["-----BEGIN PUBLIC KEY-----", "-----END PUBLIC KEY-----", "\n"]:
        pub_key = pub_key.replace(e, "")

    baseValue = pub_key

    headers = {
        "authority": "api.lekiosk.com",
        "pragma": "no-cache",
        "cache-control": "no-cache",
        "accept": f"accesskeyid:123456;isretina:false;appversion:5.0.0;content-type:application/json;cookieprefix:Cafeyn_;appId:canal;webSessionId:{cafeyn_webSessionId};authtoken:{cafeyn_authtoken};baseValue:{baseValue}",
        "user-agent": user_agent,
        "x-usergroup": cafeyn_userGroup,
        "origin": "https://reader.cafeyn.co",
        "sec-fetch-site": "cross-site",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "referer": "https://reader.cafeyn.co/",
        "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "dnt": "1",
    }

    timestamp = math.floor(datetime.timestamp(datetime.now()))
    params = (("timestamp", f"{timestamp}000"),)

    r = requests_retry_session(session=s).get(
        mag_infos_url,
        # cookies=s.cookies,
        allow_redirects=True,
        headers=headers,
        params=params,
    )
    mag_infos = json.loads(r.text)["result"]

    if mag_infos["isPurchased"] == False:
        print(
            "[WARNING] Cette publication n'est pas disponible dans votre abonnement. Vous n'aurez que les pages gratuites. "
        )

    enc_session_key = base64.b64decode(mag_infos["baseValue"])

    cipher = PKCS1_OAEP.new(priv_key)
    cipher_dec = cipher.decrypt(enc_session_key)

    title = clean_name(mag_infos["title"])
    issueNumber = clean_name(str(mag_infos["issueNumber"]))
    releaseDate = clean_name(str(mag_infos["releaseDate"]))
    if len(releaseDate) > 10:
        releaseDate = " (" + releaseDate[0:10] + ")"
    else:
        releaseDate = ""

    full_pdf_path = (
        output_folder
        + "/"
        + clean_name(title + " " + issueNumber + releaseDate)
        + ".pdf"
    )

    answer = ""
    if force_overwrite:
        answer = "O"
    while path.exists(full_pdf_path) and answer not in ["O", "Y", "N", "Q"]:
        answer = input(
            f'Le fichier de destination "{full_pdf_path}" existe déjà. Voulez-vous l\'écraser ? [O]ui / [N]on : '
        ).upper()

    if answer.upper() in ["N", "Q"]:
        sys.exit()

    done = 0
    total = len(mag_infos["signedUrls"])
    print(f"[{done} / {total}]", end="\r", flush=True)
    max_page = 0
    for page in mag_infos["signedUrls"]:
        headers = {
            'User-Agent': user_agent,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
            'AppId': 'lk',
            'Origin': 'https://reader.cafeyn.co',
            'Connection': 'keep-alive',
            'Referer': base_url,
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'TE': 'Trailers',
            }
        r = requests_retry_session(session=s).get(
            mag_infos["signedUrls"][page]["pdfUrl"],
            # cookies=s.cookies,
            allow_redirects=True,
            headers=headers,
        )
        if r.status_code != 200:
            print(f"Impossible de récupérer la page {page}")
            break
        page_str = ("000" + page)[-3:]
        # f = open(f"{title} {issueNumber} - {page_str}.bin", "wb")
        # f.write(r.content)
        # f.close()

        save_path = output_folder + "/" + title + "_" + issueNumber
        if not os.path.exists(save_path):
            os.mkdir(save_path)

        if re.fullmatch(r"^[0-9a-fA-F]+$", cipher_dec.decode()) is not None:
            # Nouveau format
            e = mag_infos["issueId"] * ord("#")
            t = mag_infos["publicationId"] * ord("*")
            b = (hex(t)[2:].upper() + "00000000000")[0:10]
            a = (hex(e)[2:].upper() + "00000000000")[0:10]
            key = b + cipher_dec.decode() + a
            iv = key[0:16]
        else:
            # Ancien format
            key = (str(mag_infos["issueId"]) + "-" + page + cipher_dec.decode())[0:16]
            # iv = ''
            # for k in key:
            #     iv = iv + hex(ord(k))[2:]
            iv = key

        key = key.encode("utf-8")
        iv = iv.encode("utf-8")

        aes = AES.new(key, AES.MODE_CBC, iv)
        # decrypted_content = aes.decrypt(r.content)
        decrypted_content = Padding.unpad(aes.decrypt(r.content), AES.block_size)

        f = open(f"{save_path}/{title} {issueNumber} - {page_str}.pdf", "wb")
        f.write(decrypted_content)
        f.close()
        done = done + 1
        max_page = int(page) if int(page) > max_page else max_page
        print(f"[{done} / {total}]", end="\r", flush=True)
        time.sleep(pause_sec)

    print("\nCompilation du PDF...")

    pdfs = []
    for fname in os.listdir(save_path):
        if not fname.endswith(".pdf"):
            continue
        path = os.path.join(save_path, fname)
        if os.path.isdir(path):
            continue
        pdfs.append(path)

    merger = PdfFileMerger()
    for pdf in pdfs:
        merger.append(pdf)
    merger.write(full_pdf_path)
    merger.close()

    if not no_clean:
        shutil.rmtree(save_path)

    # On indique à Cafeyn que le magazine est lu.
    if not no_bookmark:
        print("Mise à jour du bookmark...")
        headers = {
            "authority": "api.lekiosk.com",
            "pragma": "no-cache",
            "cache-control": "no-cache",
            "accept": f"accesskeyid:123456;isretina:false;appversion:5.0.0;content-type:application/json;cookieprefix:Cafeyn_;appId:canal;webSessionId:{cafeyn_webSessionId};authtoken:{cafeyn_authtoken};baseValue:{baseValue}",
            "user-agent": user_agent,
            "x-usergroup": cafeyn_userGroup,
            'content-type': 'application/json;charset=UTF-8',
            "origin": "https://reader.cafeyn.co",
            "sec-fetch-site": "cross-site",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": base_url,
            "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            "dnt": "1",
        }

        data = (
            '[{"issueId":'
            + str(mag_infos["issueId"])
            + ',"lastReadPage":'
            + str(max_page)
            + ',"lastReadMode":0}]'
        )
        r = requests_retry_session(session=s).put(
            "https://api.lekiosk.com/api/v1/users/me/readings/issues",
            # cookies=s.cookies,
            allow_redirects=True,
            headers=headers,
            params=params,
            data=data,
        )
        if r.status_code != 200:
            print("[WARNING] Impossible de mettre à jour le marque page.")

    print("Terminé !")
