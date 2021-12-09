import os
import click
from capitainizer.position import PositionThese
from capitainizer.capitainizer_whitout_metadata import Capitainizer_files
#SRC_DIR, cli en arguement
SRC_PATH="../encpos/data"
#Publication_package_dir ou Result_package
DEST_PATH="./data"
#Argument optionnel et discuter
METADATA = '../encpos/data/encpos.tsv'

#transformer ça en cli avec des possibilités de faire un dossier, l'intégral ou rien du tout

@click.command()
@click.option('--input', type=str, help='Enter the name of the folder who contains the XML files or the differents folders who contains the XML files')
@click.option('--metadata', type=str, help='Enter the metadata files of the XML files')
@click.option('--output', type=str, help='Enter the destination path')
def main(input, metadata, output):
    if input is not None:
        SRC_PATH = input
    if metadata is not None :
        METADATA = metadata
    if output is not None :
        DEST_PATH = output
    if not os.path.isdir(DEST_PATH):
        os.makedirs(DEST_PATH)
    list_file_or_dir = sorted(os.listdir(SRC_PATH))
    list_dir = []
    for name_dir in list_file_or_dir:
        if os.path.isdir(os.path.join(SRC_PATH, name_dir)):
            #Ajouter le nom des dossiers que vous ne souhaitez pas capitanizer
            list_dir.append(name_dir)

    folder_name = None
    if metadata is not None :
        pt = PositionThese(SRC_PATH, METADATA, 'templates/__capitains_collection.xml', 'templates/__capitains_work.xml', 'templates/edition.xml', 'templates/refs_decl.xml', 'templates/Add_EncodingDesc.xsl')
        pt.write_textgroup(folder_name, DEST_PATH, list_dir)
    else:
        cpt = Capitainizer_files(SRC_PATH, 'templates/__capitains_collection.xml', 'templates/__capitains_work.xml', 'templates/edition.xml', 'templates/refs_decl.xml', 'templates/Add_EncodingDesc.xsl')
        cpt.write_textgroup(folder_name, DEST_PATH, list_dir)
    list_dir = []
    for root, dirs, files in os.walk(SRC_PATH):
        for file in files:
            if "xml" in file:
                if root not in list_dir:
                    list_dir.append(root)

    for root_folder in list_dir:
        #évite d'intégrer les dossiers ou fichiers
        folder_name = root_folder.split("/")[-1]
        if "ENCPOS" not in folder_name:
            continue
        #list_works contient tous le fichiers à capitainiser
        list_works = [f for f in os.listdir("{0}".format(root_folder)) if "xml" in f]
        if metadata is not None :
            year = folder_name.split("_")[-1]
            if pt.write_textgroup(year, DEST_PATH, list_works):
                if pt.write_work(folder_name, year, DEST_PATH):
                    pt.write_edition(folder_name, DEST_PATH)
        else:
            if cpt.write_textgroup(folder_name, DEST_PATH, list_works):
                if cpt.write_work(folder_name, DEST_PATH, list_works):
                    cpt.write_edition(folder_name, DEST_PATH, list_works)



if __name__ == "__main__":
    main()
