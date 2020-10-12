import os
from Capitainizer.capitainizer.position import PositionThese
SRC_PATH="../data"

DEST_PATH="../../data"

METADATA = '../data/encpos.tsv'

if __name__ == "__main__":
    list_dir = os.listdir(SRC_PATH)
    print(list_dir)
    pt = PositionThese(SRC_PATH, METADATA, 'templates/__capitains_collection.xml', 'templates/__capitains_work.xml', 'templates/edition.xml', 'templates/refs_decl.xml')
    #réécrire le code pour générer automatiquement les entrées
    for folder_name in list_dir:
        if not "ENCPOS" in folder_name:
            continue
        else:
            year = folder_name.split("_")[1]
            list_works =os.listdir("{0}/{1}".format(SRC_PATH, folder_name))
        if pt.write_textgroup(year, DEST_PATH, list_works):
            if pt.write_work(folder_name, year, DEST_PATH):
                pt.write_edition(folder_name, year, SRC_PATH, DEST_PATH)

            # from_scratch = False : se base sur les fichiers decapitainisés
            """
            if pt.write_work(folder_name, year, DEST_PATH, from_scratch=False):
                pt.add_refs_decl(folder_name, year, SRC_PATH, DEST_PATH)
            """