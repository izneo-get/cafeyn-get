# Changelog

## cafeyn_get.py 

### Version 0.06.3 (2021-03-13)
- [BUGFIX] Adaptation à la nouvelle façon d'appeler les pages. 
- [NEW] Vérification de la version au lancement de l'application. 

### Version 0.06.2 (2021-03-07)
- [CHANGE] L'URL peut contenir un autre code pays que "fr". 

### Version 0.06.1 (2021-03-06)
- [NEW] Ajout de l'option `--pause SECONDS` qui permet de faire une pause entre chaque récupération de page. 

### Version 0.06.0 (2020-10-21)
- [NEW] Mise à jour du bookmark pour passer la publication en "lu". 
- [NEW] Ajout du paramètre "--no-bookmark" pour ne pas mettre à jour le bookmark. 

### Version 0.05.0 (2020-10-18)
- [NEW] Compatibilité avec les anciennes publications. 

### Version 0.04.0 (2020-10-18)
- [CHANGE] Utilisation d'une nouvelle clé RSA à chaque appel. 

### Version 0.03.1 (2020-10-09)
- [NEW] Si aucune URL passée en paramètre, on la demande. Cela permet d'exécuter le programme sans passer par une ligne de commande. 
- [NEW] Avertissement quand la publication n'est pas dans l'abonnement. 
- [NEW] Alerte si le fichier de destination existe déjà. 

### Version 0.02.0 (2020-10-08)
- [NEW] Utilisation de la date de sortie de la publication dans le nom du fichier. 

### Version 0.01.0 (2020-10-08)
- [NEW] Version initiale. 
- [NEW] Récupération des PDF en direct. 


## cafeyn_get_selenium.py 

### Version 0.01.0 (2020-10-06)
- [NEW] Ajout d'un paramètre "--no-pdf" pour ne pas créer de PDF. 
- [NEW] Ajout d'un paramètre "--no-clean" pour ne pas nettoyer les répertoire d'image après avoir généré un PDF. 
- [NEW] Ajout d'un paramètre "--image-format" (ou "-f") pour choisir le format des images ("jpg" ou "png"). 
- [NEW] Ajout d'un paramètre "--output-folder" (ou "-o") pour choisir le répertoire racine de téléchargement. 
- [CHANGE] Recherche du driver Chrome de manière récursive. 
- [BUGFIX] Détection des images vides. 

### Version 0.01.0 (2020-10-06) 
- [NEW] Version initiale. 
- [NEW] Récupération des images en pilotant un navigateur Chrome. 
