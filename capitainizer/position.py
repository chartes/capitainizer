import csv
import os
from collections import defaultdict
from itertools import chain
import re

import lxml.etree as ET
from lxml import etree
import copy
import shutil
from datetime import date

CTS_NS = "http://chs.harvard.edu/xmlns/cts"
XML_NS = "http://www.w3.org/XML/1998/namespace"
DC_NS = "http://purl.org/dc/elements/1.1/"
CPT_NS = "http://purl.org/capitains/ns/1.0#"
HTML_NS = "http://www.w3.org/1999/xhtml/"
DCT_NS = "http://purl.org/dc/terms/"
DTS_NS = "https://w3id.org/dts/api#"

class PositionThese:

    def __init__(self, src_path, metadata, textgroup_template, work_template, edition_template, refs_decl_template, xslt_encondingDesc):
        self.__tg_template_filename = textgroup_template
        self.__w_template_filename = work_template
        self.__e_template_filename = edition_template
        self.__enconding_desc_template_filename = refs_decl_template
        self.__xslt_encodingDesc_filename = xslt_encondingDesc
        self.__metadata = defaultdict(str)
        self.__src_path = src_path
        self.__nsti = {"ti": 'http://www.tei-c.org/ns/1.0'}

        with open(metadata, 'r', newline='') as meta:
            reader = csv.DictReader(meta, delimiter='\t', dialect="unix")
            for line in reader:
                self.__metadata[line["id"]] = line


    @staticmethod
    def stringify(node):
        parts = ([node.text] +
                 list(chain((ET.tounicode(c) for c in node.getchildren()))) +
                 [node.tail])
        parts = filter(None, parts)
        return ''.join(parts).strip()

    def src_edition(self, folder_name, id):
        parser = etree.XMLParser()
        src_edition_fn = os.path.join(self.__src_path, folder_name, "{0}.xml".format(id))
        if not os.path.isfile(src_edition_fn):
            return ET.Element("div")
        return ET.parse(src_edition_fn, parser)

    @property
    def __tg_template(self):
        parser = etree.XMLParser(remove_blank_text=True)
        return ET.parse(self.__tg_template_filename, parser)

    @property
    def __refs_decl_template(self):
        return ET.parse(self.__enconding_desc_template_filename)

    @property
    def __wg_template(self):
        parser = etree.XMLParser(remove_blank_text=True)
        return ET.parse(self.__w_template_filename, parser)

    @property
    def __e_template(self):
        parser = etree.XMLParser(remove_blank_text=True)
        return ET.parse(self.__e_template_filename, parser)

    @property
    def __xslt_encodingDesc(self):
        parser = etree.XMLParser()
        return ET.parse(self.__xslt_encodingDesc_filename, parser)

    def write_to_file(self, filepath, tree):
        if not os.path.isfile(filepath):
            with open(filepath, 'w') as f:
                #tree_str = ET.tounicode(tree, pretty_print=True)
                etree.indent(tree, space="    ")
                tree_str = etree.tostring(tree, pretty_print=True, encoding='unicode')
                f.write(tree_str)

    def write_textgroup(self,  pos_year, dest_path, list_works):
        # get a fresh new etree
        template = self.__tg_template
        # Update the URN part : pos -> pos2015
        textgroup = template.xpath("//cpt:identifier", namespaces=template.getroot().nsmap)
        if textgroup is None:
            raise ValueError('No textgroup detected in the textgroup template document')
        elif pos_year is None:
            #Met à jour l'identifier avec l'année
            textgroup[0].text = "{0}".format(textgroup[0].text)
            # Update the groupe name : Position de thèse -> Position de thèse 2015
            groupname = template.xpath("//dc:title", namespaces=template.getroot().nsmap)
            groupname[0].text = "{0}".format(groupname[0].text)
            # écrire les membres par année
            collection = (template.xpath("//cpt:members", namespaces=template.getroot().nsmap))
            for work in sorted(list_works):
                w = etree.SubElement(collection[0], etree.QName(CPT_NS, "collection"))
                w.attrib["path"] = "./{0}/__capitains__.xml".format(work.split(".")[0])
                w.attrib["identifier"] = work.split(".")[0]
            self.write_to_file(os.path.join(dest_path, "__capitains__.xml"), template)
            return True
        else:
            #Met à jour l'identifier avec l'année
            textgroup[0].text = "{0}_{1}".format(textgroup[0].text, pos_year)
            # Update the groupe name : Position de thèse -> Position de thèse 2015
            groupname = template.xpath("//dc:title", namespaces=template.getroot().nsmap)
            groupname[0].text = "{0} de {1}".format(groupname[0].text, pos_year)
            # Ecrit les membres par année
            collection = (template.xpath("//cpt:members", namespaces=template.getroot().nsmap))
            for work in sorted(list_works):
                w = etree.SubElement(collection[0], etree.QName(CPT_NS, "collection"))
                w.attrib["path"] = "./{0}/__capitains__.xml".format(work.split(".")[0])
                w.attrib["identifier"] = work.split(".")[0]
            tg_dirname = os.path.join(dest_path, textgroup[0].text)
            if not os.path.isdir(tg_dirname):
                os.makedirs(tg_dirname)

            self.write_to_file(os.path.join(tg_dirname, "__capitains__.xml"), template)
            return True

    def encapsulate(self, tag, node, ns):
        return ET.fromstring("<ti:{0} xmlns:ti='{1}' xml:lang='fr'>{2}</ti:{0}>".format(
            tag, ns, self.stringify(node))
        )

    #Fonction qui écrit __capitains__.xml au niveau des éditions
    def write_work(self, folder_name, pos_year, dest_path, from_scratch=True):
        for meta in [m for m in self.__metadata.values() if folder_name.split("_")[1] == m["id"].split("_")[1]]:
            cleanr = re.compile('<.*?>')
            # get a fresh new etree
            template = self.__wg_template

            #Ajout des valeurs du tableau dans les valeurs dublin core classique
            work = template.xpath("//cpt:members/cpt:collection", namespaces=template.getroot().nsmap)
            work[0].attrib["path"] = "./{0}.xml".format(meta["id"])

            identifier = template.xpath("//cpt:identifier", namespaces=template.getroot().nsmap)
            for ide in identifier:
                ide.text = "{0}".format(meta["id"])

            parent = template.xpath("//cpt:parent", namespaces=template.getroot().nsmap)
            for par in parent:
                par.text = "ENCPOS_{0}".format(meta["promotion_year"])

            if meta["author_fullname_label"] :
                creator = template.xpath("//dct:creator", namespaces=template.getroot().nsmap)
                creator[0].text = "{0}".format(meta["author_fullname_label"])

            titles = template.xpath("//dc:title", namespaces=template.getroot().nsmap)
            for tit in titles:
                if meta["title_rich"] == "":
                    tit.text = "{0}".format(meta["title_text"])
                else:
                    tit.text = "{0}".format(re.sub(cleanr,'',meta["title_rich"]))

            titles = template.xpath("//dct:title", namespaces=template.getroot().nsmap)
            for tit in titles:
                if meta["title_rich"] == "":
                    tit.text = "{0}".format(meta["title_text"])
                else:
                    tit.text = "{0}".format(re.sub(cleanr,'',meta["title_rich"]))


            #Ajout des valeurs dans les entrées dtc
            structuredMetadata = template.xpath("//cpt:structured-metadata", namespaces=template.getroot().nsmap)
            elem = etree.Element(ET.QName(DCT_NS, "rights"), nsmap={'dct': DCT_NS})
            elem.text = "https://creativecommons.org/licenses/by-nc-nd/3.0/fr/"
            structuredMetadata[0].append(elem)

            elem = etree.Element(ET.QName(HTML_NS, "h1"), nsmap={'xml': HTML_NS})
            elem.text = "{0}".format(meta["title_rich"])
            structuredMetadata[0].append(elem)

            download_xml = etree.Element(ET.QName(DTS_NS, "download"), nsmap={'dts': DTS_NS})
            download_xml.text = "https://github.com/chartes/encpos/raw/metadata/data/ENCPOS_{0}/{1}.xml".format(meta["promotion_year"],meta["id"] )
            structuredMetadata[0].append(download_xml)

            download_pdf = etree.Element(ET.QName(DTS_NS, "download"), nsmap={'dts': DTS_NS})
            download_pdf.text = "https://github.com/chartes/encpos/raw/metadata/data/ENCPOS_{0}/{1}.PDF".format(meta["promotion_year"],meta["id"] )
            structuredMetadata[0].append(download_pdf)

            if meta["pagination"]:
                elem = etree.Element(ET.QName(DCT_NS, "extend"), nsmap={'dct': DCT_NS})
                elem.text = meta["pagination"]
                structuredMetadata[0].append(elem)
            if meta["topic_notBefore"]:
                elem = etree.Element(ET.QName(DCT_NS, "coverage"), nsmap={'dct': DCT_NS})
                elem.text = "{0}/{1}".format(meta["topic_notBefore"], meta["topic_notAfter"])
                structuredMetadata[0].append(elem)


            if meta["author_idref_ppn"]:
                elem = etree.Element(ET.QName(DCT_NS, "creator"), nsmap={'dct': DCT_NS})
                elem.text = "{0}{1}".format("https://www.idref.fr/", meta["author_idref_ppn"])
                structuredMetadata[0].append(elem)
            if meta["author_bnf_ark"]:
                elem = etree.Element(ET.QName(DCT_NS, "creator"), nsmap={'dct': DCT_NS})
                elem.text = "https://catalogue.bnf.fr/{0}".format(meta["author_bnf_ark"])
                structuredMetadata[0].append(elem)
                elem = etree.Element(ET.QName(DCT_NS, "creator"), nsmap={'dct': DCT_NS})
                elem.text = "https://data.bnf.fr/{0}".format(meta["author_bnf_ark"])
                structuredMetadata[0].append(elem)
            if meta["author_wikidata_id"]:
                elem = etree.Element(ET.QName(DCT_NS, "creator"), nsmap={'dct': DCT_NS})
                elem.text = "https://wikidata.org/entity/{0}".format(meta["author_wikidata_id"])
                structuredMetadata[0].append(elem)
            if meta["author_wikipedia_url"]:
                elem = etree.Element(ET.QName(DCT_NS, "creator"), nsmap={'dct': DCT_NS})
                elem.text = "{0}".format(meta["author_wikipedia_url"])
                structuredMetadata[0].append(elem)
            if meta["author_dbpedia_id"]:
                elem = etree.Element(ET.QName(DCT_NS, "creator"), nsmap={'dct': DCT_NS})
                elem.text = "https://dbpedia.org/resource/{0}".format(meta["author_dbpedia_id"])
                structuredMetadata[0].append(elem)
            #Ajouter ici les informations pour wikidata, wikipedia, wikidata
            if meta["sudoc_these-record_ppn"]:
                elem = etree.Element(ET.QName(DCT_NS, "isVersionOf"), nsmap={'dct': DCT_NS})
                elem.text = "{0}{1}".format("https://www.sudoc.fr/", meta["sudoc_these-record_ppn"])
                structuredMetadata[0].append(elem)
            if meta["thenca_these-record_id"]:
                elem = etree.Element(ET.QName(DCT_NS, "isVersionOf"), nsmap={'dct': DCT_NS})
                elem.text = "{0}{1}".format("http://bibnum.chartes.psl.eu/s/thenca/item/", meta["thenca_these-record_id"])
                structuredMetadata[0].append(elem)
            if meta["hal-these-record_id"]:
                elem = etree.Element(ET.QName(DCT_NS, "isVersionOf"), nsmap={'dct': DCT_NS})
                elem.text = "{0}{1}".format("https://halshs.archives-ouvertes.fr/", meta["hal-these-record_id"])
                structuredMetadata[0].append(elem)
            #Ajout l'entrée these biblio-ben
            if meta["benc_these-record_id"]:
                elem = etree.Element(ET.QName(DCT_NS, "isVersionOf"), nsmap={'dct': DCT_NS})
                elem.text = "https://catalogue.chartes.psl.eu/cgi-bin/koha/opac-detail.pl?biblionumber={1}".format("benc_number: ", meta["benc_these-record_id"])
                structuredMetadata[0].append(elem)

            if int(meta["promotion_year"]) < 2000:
                elem = etree.Element(ET.QName(DCT_NS, "source"), nsmap={'dct': DCT_NS})
                elem.text = "https://iiif.chartes.psl.eu/encpos/{}/manifest".format(meta["id"].lower())
                structuredMetadata[0].append(elem)

            year = template.xpath("//dct:date", namespaces=template.getroot().nsmap)
            year[0].text = pos_year

            if work is None:
                raise ValueError('No work detected in the work template document')
            else:
                # title
                if from_scratch is False:
                    src_edition = self.src_edition(folder_name, meta["id"])
                    titles = src_edition.xpath("//ti:teiHeader//ti:titleStmt//ti:title", namespaces=self.__nsti)
                else:
                    src_edition = self.src_edition(folder_name, meta["id"])
                    titles = src_edition.xpath("//ti:front/ti:head", namespaces=self.__nsti)

                # Méthode pour encapsuler les données et ajouter au niveau du root
                #template.getroot().insert(0, self.encapsulate("title", titles[0], CTS_NS))



                # make workgroup dir
                w_dirname = os.path.join(dest_path, folder_name, "{0}".format(meta["id"]))
                if os.path.isdir(w_dirname):
                    shutil.rmtree(w_dirname)
                os.makedirs(w_dirname)
                self.write_to_file(os.path.join(w_dirname, "__capitains__.xml"), template)

        return True

    #Ecriture de la position avec les nouvelles valeurs
    def write_edition(self, folder_name, pos_year, src_path, dest_path):
        refs_decl = self.__refs_decl_template
        for meta in [m for m in self.__metadata.values() if folder_name.split("_")[1] == m["id"].split("_")[1]]:
            template = self.__e_template
            e_dirname = os.path.join(dest_path, folder_name , "{0}".format(meta["id"]))
            e_filepath = os.path.join(e_dirname, "{0}.xml".format(
                "{0}".format(meta["id"])
            ))

            src_edition = self.src_edition(folder_name, meta["id"])
            root = src_edition.xpath('//ti:text', namespaces=self.__nsti)
            try:
                root[0].set("{0}base".format("{" + XML_NS + "}"), "{0}".format(meta["id"]))
            except:
                print(meta["id"] + "not present")
                continue

            #Si il y a pas d'encodingDesc refs_decl
            transfrom = self.__xslt_encodingDesc
            transfrom = etree.XSLT(transfrom)
            src_edition = transfrom(src_edition)
            header = src_edition.find("//ti:encodingDesc", namespaces=self.__nsti)
            header.append(refs_decl.getroot())
            """
            #Ajout du titlerich des metadonnées
            title = src_edition.xpath("//ti:titleStmt//ti:title", namespaces=self.__nsti)
            title[0].text = meta["title_text"]

            #Ajout de l'identifier dans le fichier XML ENCPOS

            # test la présence de la balise auteur et la rajoute
            #Ajout d'un traitement pour passer le title_rich du format html au format TEI
            auth = src_edition.xpath("//ti:teiHeader//ti:author", namespaces=self.__nsti)
            if not auth:
                auth = src_edition.xpath("//ti:titleStmt", namespaces=self.__nsti)
                author = etree.Element("author", nsmap=self.__nsti)
                author.text ="{1} {0}".format(meta["author_name"], meta["author_firstname"])
                auth[0].append(author)
            else:
                auth[0].text = "{1} {0}".format(meta["author_name"], meta["author_firstname"])

            # Ajout de la promotion
            pub_date = src_edition.xpath("//ti:teiHeader//ti:publicationStmt/ti:date", namespaces=self.__nsti)
            pub_date[0].set("when", meta["promotion_year"])
            """

            body = src_edition.xpath("//ti:body", namespaces=self.__nsti)
            body[0].set("type", "textpart")
            body[0].set("subtype", "position")
            body[0].set("n", "1")
            self.write_to_file(e_filepath, src_edition)


    def add_refs_decl(self, folder_name, pos_year, src_path, dest_path):
        refs_decl = self.__refs_decl_template

        for meta in [m for m in self.__metadata.values() if m["promotion_year"] == pos_year]:
            # get a fresh new etree
            template = self.src_edition(folder_name, meta["id"])

            e_dirname = os.path.join(dest_path, "ENCPOS_{0}".format(meta["promotion_year"]), "ENCPOS_{0}".format(meta["id"]))

            e_filepath = os.path.join(e_dirname, "{0}.{1}.{2}".format(
                "ENCPOS_{0}".format(meta["promotion_year"]), "ENCPOS_{0}".format(meta["id"]), "positionThese-fr1.xml"
            ))

            #src_edition = self.src_edition(folder_name, meta["id"])

            header = template.xpath("//ti:teiHeader//ti:encodingDesc", namespaces=self.__nsti)
            header[0].append(refs_decl.getroot())

            # write the edition file
            self.write_to_file(e_filepath, template)

        return True