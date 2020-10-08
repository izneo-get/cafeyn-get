# -*- coding: utf-8 -*-

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
from bs4 import BeautifulSoup
from PIL import Image
import json
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Util import Padding
import base64
from datetime import datetime
import math
from PyPDF2 import PdfFileMerger

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

if __name__ == "__main__":
    # Parse des arguments passés en ligne de commande.
    parser = argparse.ArgumentParser(
        description="""Script pour sauvegarder une publication Cafeyn."""
    )
    parser.add_argument(
        "url",
        type=str,
        default=None,
        help="L'URL de la publication à récupérer ou le chemin vers un fichier local contenant une liste d'URLs",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        default=False,
        help="Ne supprime pas le répertoire temporaire dans le cas où un PDF a été généré.",
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

    args = parser.parse_args()
    no_clean = args.no_clean


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

    if not cafeyn_authtoken or not cafeyn_webSessionId or not cafeyn_userGroup:
        print("[ERREUR] Impossible de trouver les valeurs dans la configuration.")
        print(f"cafeyn_authtoken = \"{cafeyn_authtoken}\"")
        print(f"cafeyn_webSessionId = \"{cafeyn_webSessionId}\"")
        print(f"cafeyn_userGroup = \"{cafeyn_userGroup}\"")

    if not user_agent:
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
    s = requests.Session()
    
    
    publication = re.match("https://reader.cafeyn.co/fr/(.+?)/(.+?)", base_url)[1]
    issue = re.match("https://reader.cafeyn.co/fr/(.+?)/(.+)", base_url)[2]

    mag_infos_url = f"https://api.lekiosk.com/api/v1/reader/publications/{publication}/issues/{issue}/signedurls"

    # Cela correspond à l'export "spki" de la clé privée.
    baseValue = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDzJYI8Xm+HyF0vn6qGZgM/AezQ2k9nIkyZBThhTOYWGQFDMloaSgP7JWzJOXJd0nu9TsFwV6jJAtth0hclC+KcXIgZF1ZKEr/p5F3xhMlkKDYwduLj5BmboUZ9zDlpzZyQpbm7JHQb/dwzfR5DkNPYbnHe7DAxaTKOiPfvAzevSwIDAQAB"
    
    headers = {
        'authority': 'api.lekiosk.com',
        'pragma': 'no-cache',
        'cache-control': 'no-cache',
        'accept': f"accesskeyid:123456;isretina:false;appversion:5.0.0;content-type:application/json;cookieprefix:Cafeyn_;appId:canal;webSessionId:{cafeyn_webSessionId};authtoken:{cafeyn_authtoken};baseValue:{baseValue}",
        'user-agent': user_agent,
        'x-usergroup': cafeyn_userGroup,
        'origin': 'https://reader.cafeyn.co',
        'sec-fetch-site': 'cross-site',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://reader.cafeyn.co/',
        'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'dnt': '1',
    }

    timestamp = math.floor(datetime.timestamp(datetime.now()))
    params = (
        ('timestamp', f"{timestamp}000"),
    )

    r = requests_retry_session(session=s).get(
            mag_infos_url,
            # cookies=s.cookies,
            allow_redirects=True,
            headers=headers,
            params=params
        )
    mag_infos = json.loads(r.text)['result']

    enc_session_key = base64.b64decode(mag_infos['baseValue'])

    priv_key = RSA.import_key(open('privatekey.pkcs8').read())
    cipher = PKCS1_OAEP.new(priv_key)
    cipher_dec = cipher.decrypt(enc_session_key)

    e = mag_infos["issueId"] * ord('#')
    t = mag_infos["publicationId"] * ord('*')
    b = (hex(t)[2:].upper() + '00000000000')[0:10]
    a = (hex(e)[2:].upper() + '00000000000')[0:10]
    key = b + cipher_dec.decode() + a
    
    done = 0
    total = len(mag_infos['signedUrls'])
    print(f"[{done} / {total}]", end="\r", flush=True)
    for page in mag_infos['signedUrls']:
        r = requests_retry_session(session=s).get(
            mag_infos['signedUrls'][page]['pdfUrl'],
            # cookies=s.cookies,
            allow_redirects=True,
            headers=headers
        )
        if r.status_code != 200:
            print(f"Impossible de récupérer la page {page}")
            break
        title = clean_name(mag_infos['title'])
        issueNumber = clean_name(str(mag_infos['issueNumber']))
        page_str = ('000' + page)[-3:]
        # f = open(f"{title} {issueNumber} - {page_str}.bin", "wb")
        # f.write(r.content)
        # f.close()
        
        save_path = output_folder + "/" + title + '_' + issueNumber
        if not os.path.exists(save_path):
            os.mkdir(save_path)
            
        aes = AES.new(key.encode('utf-8'), AES.MODE_CBC, key[0:16].encode('utf-8'))
        #decrypted_content = aes.decrypt(r.content)
        decrypted_content = Padding.unpad(aes.decrypt(r.content), AES.block_size)

        f = open(f"{save_path}/{title} {issueNumber} - {page_str}.pdf", "wb")
        f.write(decrypted_content)
        f.close()
        done = done + 1
        print(f"[{done} / {total}]", end="\r", flush=True)

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
    merger.write(output_folder + "/" + clean_name(title + ' ' + issueNumber) + ".pdf")
    merger.close()

    if not no_clean:
        shutil.rmtree(save_path)
    print("Terminé !")
