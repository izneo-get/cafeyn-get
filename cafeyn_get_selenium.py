# -*- coding: utf-8 -*-
__version__ = "0.02.0"
"""
Source : https://github.com/izneo-get/cafeyn-get

Ce script permet de récupérer un journal ou un magazine présent sur https://www.cafeyn.co dans la limite des capacités de notre compte existant.
"""
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import argparse
import configparser
import re
import sys
import os
import glob
from io import BytesIO
from PIL import Image, ImageOps
import base64
import time
import img2pdf
import shutil


def get_file_content_chrome(driver, uri):
    result = driver.execute_async_script(
        """
    var uri = arguments[0];
    var callback = arguments[1];
    var toBase64 = function(buffer){for(var r,n=new Uint8Array(buffer),t=n.length,a=new Uint8Array(4*Math.ceil(t/3)),i=new Uint8Array(64),o=0,c=0;64>c;++c)i[c]="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/".charCodeAt(c);for(c=0;t-t%3>c;c+=3,o+=4)r=n[c]<<16|n[c+1]<<8|n[c+2],a[o]=i[r>>18],a[o+1]=i[r>>12&63],a[o+2]=i[r>>6&63],a[o+3]=i[63&r];return t%3===1?(r=n[t-1],a[o]=i[r>>2],a[o+1]=i[r<<4&63],a[o+2]=61,a[o+3]=61):t%3===2&&(r=(n[t-2]<<8)+n[t-1],a[o]=i[r>>10],a[o+1]=i[r>>4&63],a[o+2]=i[r<<2&63],a[o+3]=61),new TextDecoder("ascii").decode(a)};
    var xhr = new XMLHttpRequest();
    xhr.responseType = 'arraybuffer';
    xhr.onload = function(){ callback(toBase64(xhr.response)) };
    xhr.onerror = function(){ callback(xhr.status) };
    xhr.open('GET', uri);
    xhr.send();
    """,
        uri,
    )
    if type(result) == int:
        raise Exception("Request failed with status %s" % result)
    return base64.b64decode(result)


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

def is_only_white(im):
    """Permet de supprimer les bords blancs. 

    Parameters
    ----------
    im : Image
        L'image que l'on souhaite traiter.

    Returns
    -------
    Image
        L'image sans les bords blancs.
    """
    tmp_im = im.convert("RGB")
    tmp_im = ImageOps.invert(tmp_im)
    bbox = tmp_im.getbbox()
    if not bbox:
        return True
    else:
        return False

if __name__ == "__main__":
    
    # Parse des arguments passés en ligne de commande.
    parser = argparse.ArgumentParser(
        description="""Ce script permet de récupérer un journal ou un magazine présent sur https://www.cafeyn.co dans la limite des capacités de notre compte existant."""
    )
    parser.add_argument(
        "--no-pdf",
        action="store_true",
        default=False,
        help="Ne génère pas de PDF.",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        default=False,
        help="Ne supprime pas le répertoire temporaire dans le cas où un PDF a été généré.",
    )
    parser.add_argument(
        "--image-format",
        "-f",
        choices={"png", "jpg"},
        type=str,
        default="jpg",
        help="Format des images.",
    )
    parser.add_argument(
        "--output-folder",
        "-o",
        type=str,
        default=None,
        help="Répertoire racine de téléchargement",
    )

    args = parser.parse_args()

    to_pdf = not args.no_pdf
    no_clean = args.no_clean
    output_format = args.image_format

    config = configparser.ConfigParser()
    config_file = re.sub(r"(.+)\.(.+)", r"\1", sys.argv[0]) + ".ini"
    prefered_driver = "./bin/chromedriver.exe"
    if os.path.isfile(config_file):
        config.read(config_file, encoding="utf-8")
        prefered_driver = config.get(
            "DEFAULT", "prefered_driver", fallback=prefered_driver
        )

    # On se rattache a une instance de Chrome existante
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    chrome_driver = prefered_driver
    try:
        driver = webdriver.Chrome(chrome_driver, options=chrome_options)
    except:
        # Ce driver n'est pas compatible.
        print(f'Impossible de se connecter avec le driver "{chrome_driver}"')
        for filename in glob.iglob("./**/chromedriver*.exe", recursive=True):
            chrome_driver = filename
            try:
                driver = webdriver.Chrome(chrome_driver, options=chrome_options)
            except:
                print(f'Impossible de se connecter avec le driver "{chrome_driver}"')
                continue
            prefered_driver = filename
            break

    config["DEFAULT"]["prefered_driver"] = prefered_driver
    with open(config_file, "w") as configfile:
        config.write(configfile)

    body = driver.find_element_by_tag_name("body")
    title = (
        driver.find_element_by_tag_name("h1").text
        + " ("
        + driver.current_url.replace("https://reader.cafeyn.co/fr/", "")
        + ")"
    )

    output_folder = os.path.dirname(os.path.abspath(sys.argv[0])) + "/DOWNLOADS"
    if args.output_folder:
        output_folder = args.output_folder
    
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    save_path = output_folder + "/" + clean_name(title)
    if not os.path.exists(save_path):
        os.mkdir(save_path)

    termine = 0
    pages_done = []
    while termine <= 3:
        canvas = driver.execute_script(
            "return document.getElementsByTagName('canvas');"
        )
        new_pages = 0
        for c in canvas:
            parent_element = driver.execute_script(
                "return arguments[0].parentElement.id",
                c,
            )
            if parent_element not in pages_done:
                loaded = False
                attempts = 20
                while not loaded and attempts > 0:
                    try:
                        blob_url = driver.execute_script(
                            """
                        const blob = await new Promise(resolve => arguments[0].toBlob(resolve));
                        return URL.createObjectURL(blob);
                        """,
                            c,
                        )
                    except:
                        attempts = attempts - 1
                        continue
                    bytes = get_file_content_chrome(driver, blob_url)
                    if len(bytes) > 20000:
                        im = Image.open(BytesIO(bytes))
                        # Pour vérifier si ce n'est pas une image entièrement blanche, on la crop.
                        if not is_only_white(im):
                            loaded = True
                if loaded:
                    filename = ("00000" + parent_element.replace("canvas", ""))[-3:]
                    if output_format == 'jpg':
                        im = im.convert("RGB")
                        im.save(f"{save_path}/{filename}.{output_format}", quality=95)
                    else:
                        im.save(f"{save_path}/{filename}.{output_format}")
                    pages_done.append(parent_element)
                    new_pages = new_pages + 1
                    driver.execute_script(f"URL.revokeObjectURL('{blob_url}');")
                else:
                    print("Waiting")
                    attempts = attempts - 1
                    time.sleep(1)
        if new_pages == 0:
            termine = termine + 1
        else:
            termine = 0
        body.send_keys(Keys.ARROW_RIGHT)
        print(".", end="", flush=True)
        time.sleep(1)

    print("\nToutes les pages sont récupérées.")
    
    if to_pdf:
        print("Création du PDF...")
        with open(output_folder + "/" + clean_name(title) + ".pdf", "wb") as f:
            imgs = []
            for fname in os.listdir(save_path):
                if not fname.endswith(".jpg"):
                    continue
                path = os.path.join(save_path, fname)
                if os.path.isdir(path):
                    continue
                imgs.append(path)
            f.write(img2pdf.convert(imgs))

        if not no_clean:
            shutil.rmtree(save_path)
        print("OK")
        