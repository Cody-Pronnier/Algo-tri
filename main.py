import json
import requests

def recup_operationbyworkunit():
    base_url = "http://82.64.231.72:8000/operations_by_workunit/"
    ids = range(1, 27)  # Liste des ID de 1 à 26
    data_list = []

    for id in ids:
        url = base_url + str(id)
        response = requests.get(url)
        data = response.json()
        data_list.append(data)

    for index, sublist in enumerate(data_list, start=1):
        sublist.append({'id': index})
    return data_list

def recup_donnees(type):
    url = "http://82.64.231.72:8000/" + type
    # Envoie une requête GET à l'URL et récupère la réponse.
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
    # Envoie des données récupérées.
    return data






# Fonction pour trouver une recette pour un article donné.
def trouver_recette(article_id, liste_recette=None):
    # Si la liste_recette n'est pas encore initialisée, la créer.
    if liste_recette is None:
        liste_recette = []

    recette = None
    # Recherche de la recette correspondante à l'article_id.
    for r in recettes:
        if r['id_article'] == article_id:
            recette = r
            break

    # Si une recette a été trouvée, on ajoute les informations à la liste_recette et on recherche récursivement.
    if recette:
        recette_temp = {'id_article': recette.get('id_article'),
                        'id_operation': recette.get('id_operation'),
                        'id_composant1': recette.get('id_composant1'),
                        'quantite1': recette.get('quantite1'),
                        'id_composant2': recette.get('id_composant2'),
                        'quantite2': recette.get('quantite2')
                        }
        liste_recette.append(recette_temp)

        # Check si premier composant est un article et on cherche sa recette.
        if recette.get('id_composant1'):
            trouver_recette(recette.get('id_composant1'), liste_recette)

        # Check si deuxième composant est un article et on cherche sa recette.
        if recette.get('id_composant2'):
            trouver_recette(recette.get('id_composant2'), liste_recette)

    # Si aucune recette n'a été trouvée, on informe que l'article est un article primaire.
    else:
        if recette is None:
            global articles_primaire
            articles_primaire.append(article_id)
        
    # On retourne la liste de toutes les recettes trouvées.
    return liste_recette

def multi_quantite(liste_recettes, quantite):
    for recette in liste_recettes:
        if recette.get('quantite1') is not None:
            recette['quantite1'] *= quantite
        if recette.get('quantite2') is not None:
            recette['quantite2'] *= quantite
    return liste_recettes

def transformer_recettes(liste_recette):
    nouvelle_liste = []

    while liste_recette:
        recette = liste_recette.pop(0)  # Prenez la première recette de la liste.

        # Chercher si la recette existe déjà dans la nouvelle liste.
        for index, r in enumerate(nouvelle_liste):
            if r['id_article'] == recette['id_article'] and r['id_operation'] == recette['id_operation']:
                # si elle existe, mettez à jour la quantité et déplacez-la en haut de la liste.
                r['quantite1'] += recette['quantite1']
                if recette['id_composant2'] is not None:
                    if r['id_composant2'] == recette['id_composant2']:
                        r['quantite2'] += recette['quantite2']
                nouvelle_liste.insert(0, nouvelle_liste.pop(index))
                break
        else:
            # si la recette n'existe pas dans la nouvelle liste, ajoutez-la en haut.
            nouvelle_liste.insert(0, recette)

    return nouvelle_liste

def fusion_dictionnaire(workunits, operations):
    # Créer une nouvelle liste de workunits avec les opérations ajoutées
    workunits_avec_operations = []
    for i in range(len(workunits)):
        workunit = workunits[i]
        if i < len(operations):
            workunit['operations'] = operations[i]
        else:
            workunit['operations'] = []
        workunits_avec_operations.append(workunit)
        
    return workunits_avec_operations

def supprimer_derniere_operation(workunits):
    for workunit in workunits:
        if 'operations' in workunit and workunit['operations']:
            workunit['operations'].pop()
    return workunits

def ajouter_delai(workunits):
    for workunit in workunits:
        workunit['delai'] = 0
    return workunits


def calculer_temps_production(nouvelle_liste, operations, liste_workunits, articles_primaires):

    # Initialiser une liste pour garder une trace des articles en cours de production.
    articles_en_production = []
    # Initialiser un dictionnaire pour garder une trace des articles disponibles.
    articles_disponibles = {article: float('inf') for article in articles_primaires}
    
    

    # Tant qu'il y a des recettes dans la liste.
    while nouvelle_liste:
        
            
        liste_temporaire = []
        id_operation = nouvelle_liste[0]['id_operation']
        for element in liste_workunits:
            for operation in element['operations']:    
                if operation['id'] == id_operation:
                    liste_temporaire.append(element)  
    
        element_plus_petit = min(liste_temporaire, key=lambda x: x['delai'])  
        
        for recette in nouvelle_liste:
            # Vérifier si tous les composants nécessaires sont disponibles.
            if (recette['id_composant1'] in articles_disponibles and
                (recette['id_composant2'] is None or recette['id_composant2'] in articles_disponibles)):
                # Retirer les composants nécessaires des articles disponibles.
                articles_disponibles[recette['id_composant1']] -= recette['quantite1']
                if recette['id_composant2'] is not None:
                    articles_disponibles[recette['id_composant2']] -= recette['quantite2']

                # Trouver le temps de l'opération pour cette recette.
                for operation in operations:
                    if operation['id'] == recette['id_operation']:
                        temps_operation = operation['delaiInstallation'] + recette['quantite1'] * operation['delai']
                        if recette['id_composant2'] is not None:
                            temps_operation += recette['quantite2'] * operation['delai']
                        break
                
                # Mettre à jour le temps de fin de cette unité de travail.
                for element1 in liste_workunits:
                    if element1['id'] == element_plus_petit['id']:
                        element1['delai'] += temps_operation

                # Marquer l'article comme "en cours de production".
                articles_en_production.append(recette['id_article'])

                # Ajouter l'article produit aux articles disponibles.
                if recette['id_article'] in articles_disponibles:
                    articles_disponibles[recette['id_article']] += 1
                else:
                    articles_disponibles[recette['id_article']] = 1

                # Retirer la recette de la liste.
                nouvelle_liste.remove(recette)
                break
        else:
            break

    for element in liste_workunits:
        code = element['code']
        delai = element['delai']
        print(f"Code: {code}, Délai: {delai}")
    # Le temps total de production est le temps de fin de la dernière unité de travail à terminer.
    total_temps = max(liste_workunits, key=lambda x: x['delai'])  

    return total_temps['delai']

def print_article(article_id, delai, quantite):
        print("L'article d'id", article_id, "a été créé avec succès pour un délai de", delai, "et une quantite de",  quantite)

# Initialisation d'une variable globale pour les articles primaires.
articles_primaire = []

# Charger les données JSON dans des variables.
articles = recup_donnees("articles")
operations = recup_donnees("operations")
recettes = recup_donnees("recipes")
workunits = recup_donnees("workunits")
workunitsbyoperations = recup_operationbyworkunit()
liste_workunits = fusion_dictionnaire(workunits, workunitsbyoperations)
liste_workunits = supprimer_derniere_operation(liste_workunits)
liste_workunits = ajouter_delai(liste_workunits)

# Exemple d'utilisation des fonctions pour créer un article en fonction d'une quantite.
article_id = 309
quantite = 1


# Lancement des fonctions
## On trouve les recettes de l'article
recette = trouver_recette(article_id)

## On multiplie par la quantite
recette_quantite = multi_quantite(recette, quantite)

## On enlève les doublons
nouvelle_recette = transformer_recettes(recette_quantite)

## On calcule le délai
delai = calculer_temps_production(nouvelle_recette, operations, liste_workunits, articles_primaire)

## On imprime le délai
print_article(article_id, delai, quantite)

