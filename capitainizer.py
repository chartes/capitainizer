import os
from capitainizer.position import PositionThese
SRC_PATH="../encpos/data"

DEST_PATH="./data"

METADATA = '../encpos/data/encpos.tsv'

if __name__ == "__main__":
    if not os.path.isdir(DEST_PATH):
        os.makedirs(DEST_PATH)
    list_dir = sorted(os.listdir(SRC_PATH))
    for direct in list_dir:
        if not os.path.isdir(os.path.join(SRC_PATH, direct)):
            list_dir.remove(direct)
    pt = PositionThese(SRC_PATH, METADATA, 'templates/__capitains_collection.xml', 'templates/__capitains_work.xml', 'templates/edition.xml', 'templates/refs_decl.xml', 'templates/Add_EncodingDesc.xsl')
    year = None
    pt.write_textgroup(year, DEST_PATH, list_dir)
    for folder_name in list_dir:
        #évite d'intégrer les dossiers ou fichiers
        if not "ENCPOS" in folder_name:
            continue
        else:
            year = folder_name.split("_")[1]
            list_works = os.listdir("{0}/{1}".format(SRC_PATH, folder_name))
            if pt.write_textgroup(year, DEST_PATH, list_works):
                if pt.write_work(folder_name, year, DEST_PATH):
                    pt.write_edition(folder_name, year, SRC_PATH, DEST_PATH)