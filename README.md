# cafeyn-get
Ce script permet de récupérer un journal ou un magazine présent sur https://www.cafeyn.co dans la limite des capacités de notre compte existant.

Le but est de pouvoir lire un journal ou un magazine sur un support non compatible avec les applications fournies par Cafeyn. 
Il est évident que les fichiers ne doivent en aucun cas être conservées une fois la lecture terminée ou lorsque votre abonnement ne vous permet plus de les lire.


## Utilisation

### cafeyn_get
**Utilisation**  
```
usage: cafeyn_get.py [-h] [--no-clean] [--no-bookmark] [--output-folder OUTPUT_FOLDER] [--config CONFIG]
                     [--user-agent USER_AGENT] [--force] [--pause SECONDS]
                     [url]

Script pour sauvegarder une publication Cafeyn.

positional arguments:
  url                   L'URL de la publication à récupérer ou le chemin vers un fichier local contenant une liste
                        d'URLs

optional arguments:
  -h, --help            show this help message and exit
  --no-clean            Ne supprime pas le répertoire temporaire dans le cas où un PDF a été généré
  --no-bookmark         Ne met pas à jour le statut "lu" de la publication
  --output-folder OUTPUT_FOLDER, -o OUTPUT_FOLDER
                        Répertoire racine de téléchargement
  --config CONFIG       Fichier de configuration
  --user-agent USER_AGENT
                        User agent à utiliser
  --force               Ne demande pas la confirmation d'écrasement de fichier
  --pause SECONDS, -p SECONDS
                        Faire une pause (en secondes) entre chaque page
```

- L'URL doit ressembler à :
```
https://reader.cafeyn.co/{pays}/{identifiant_journal}/{identifiant_numero}
``` 

- Il est impératif d'avoir un fichier de configuration "cafeyn_get.cfg" dans lequel les 3 variables de cookies sont renseignées : 
```
cafeyn_authtoken = ...
cafeyn_webSessionId = ...
cafeyn_userGroup = ...
```
Pour les obtenir, identifiez vous sur https://www.cafeyn.co et recherchez vos cookies avec votre navigateur web.

#### Chrome  
Menu --> Plus d'outils --> Outils de développements  
Application / Storage / Cookies  
et recherchez le cookie "https://reader.cafeyn.co".  


#### Firefox  
Menu --> Developpement web --> Inspecteur de stockage --> Cookies  
et recherchez le cookie "https://reader.cafeyn.co".  



### cafeyn_get_selenium
**Utilisation**  
- Il faut tout d'abord lancer un navigateur Chrome en mode "debug". 
Pour cela, on peut exécuter le script : 
```
chrome_debug.bat
```
 
Ou adapter et exécuter cette ligne de commande : 
```
"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\temp\AutomationProfile"
```
  
- Il faut aller sur https://www.cafeyn.co s'identifier, choisir un journal, ouvrir le lecteur et se placer sur la première page. 
- L'URL doit ressembler à :
```
https://reader.cafeyn.co/fr/{identifiant_numero}/{identifiant_journal}
``` 
  
- On exécute le script Python : 
```
python cafeyn_get_selenium.py
```
  
- Les fichiers seront enregistrés dans le répertoire de téléchargement. 


## Installation
### Prérequis
- Python 3.7+ (non testé avec les versions précédentes)
- pip
- Librairies SSL
- Drivers Chrome

#### Sous Windows
##### Python
Allez sur ce site :  
https://www.python.org/downloads/windows/  
et suivez les instructions d'installation de Python 3.

##### Pip
- Téléchargez [get-pip.py](https://bootstrap.pypa.io/get-pip.py) dans un répertoire.
- Ouvrez une ligne de commande et mettez vous dans ce répertoire.
- Entrez la commande suivante :  
```
python get-pip.py
```
- Voilà ! Pip est installé !
- Vous pouvez vérifier en tapant la commande :  
```
pip -v
```

##### Librairies SSL
- Vous pouvez essayer de les installer avec la commande :  
```
pip install pyopenssl
```
- Vous pouvez télécharger [OpenSSL pour Windows](http://gnuwin32.sourceforge.net/packages/openssl.htm). 

##### Drivers Chrome
- Il faut télécharger le fichier "chromedriver.exe" [sur le site de Chromium](https://chromedriver.chromium.org/downloads) et le copier dans le répertoire 
```
bin\
```
- Il est possible de le renommer en "chromedriverXX.exe" où "XX" est le numéro de la version. Le système ira chercher celui qui convient à votre version de Chrome installée.


#### Sous Linux
Si vous êtes sous Linux, vous n'avez pas besoin de moi pour installer Python, Pip ou SSL...  

### Téléchargement
- Vous pouvez cloner le repo git :  
```
git clone https://github.com/izneo-get/cafeyn-get.git
```
ou  
- Vous pouvez télécharger uniquement le binaire Windows (expérimental).  


### Configuration
(pour la version "script" uniquement)
```
pip install -r requirements.txt
```
