def filtrer_liste_temporaire(liste, id_operation):
    liste_temporaire = []
    for element in liste:
        for operation in element['operations']:
            if operation['id'] == id_operation:
                liste_temporaire.append(element)
                break
    return liste_temporaire