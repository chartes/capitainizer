import csv
import os
from collections import defaultdict
from itertools import chain

import lxml.etree as ET
from lxml import etree
import copy
import shutil
from datetime import date

CTS_NS = "http://chs.harvard.edu/xmlns/cts"
XML_NS = "http://www.w3.org/XML/1998/namespace"
DC_NS = "http://purl.org/dc/elements/1.1/"

class PositionThese:

    def __init__(self, src_path, metadata, textgroup_template, work_template, edition_template, refs_decl_template):
        self.__tg_template_filename = textgroup_template
        self.__w_template_filename = work_template
        self.__e_template_filename = edition_template
        self.__enconding_desc_template_filename = refs_decl_template
        self.__metadata = defaultdict(str)
        self.__src_path = src_path
        self.__nsmap = {"ti": 'http://www.tei-c.org/ns/1.0'}

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
        parser = etree.XMLParser(remove_blank_text=True)
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

    def write_to_file(self, filepath, tree):
        if not os.path.isfile(filepath):
            with open(filepath, 'w') as f:
                tree_str = ET.tounicode(tree, pretty_print=True
                                        )
                f.write(tree_str)

    def write_textgroup(self,  pos_year, dest_path, list_works):
        # get a fresh new etree
        template = self.__tg_template
        # Update the URN part : pos -> pos2015
        textgroup = template.xpath("//cpt:identifier", namespaces=template.getroot().nsmap)
        if textgroup is None:
            raise ValueError('No textgroup detected in the textgroup template document')
        else:
            #Met à jour l'identifier avec l'année
            textgroup[0].text = "{0}_{1}".format(textgroup[0].text, pos_year)
            # Update the groupe name : Position de thèse -> Position de thèse 2015
            groupname = template.xpath("//dc:title", namespaces=template.getroot().nsmap)
            groupname[0].text = "{0} {1}".format(groupname[0].text, pos_year)
            # écrire les membres par année
            collection = (template.xpath("//cpt:members", namespaces=template.getroot().nsmap))
            for work in list_works:
                w = etree.SubElement(collection[0], "collection", nsmap=template.getroot().nsmap)
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

    def write_work(self, folder_name, pos_year, dest_path, from_scratch=True):
        for meta in [m for m in self.__metadata.values() if m["promotion_year"] == str(pos_year)]:
            # get a fresh new etree
            template = self.__wg_template

            # Update the URN parts : pos -> pos2015
            work = template.xpath("//cpt:collection", namespaces=template.getroot().nsmap)
            work[0].attrib["path"] = "./{0}.xml".format(meta["id"])

            identifier = template.xpath("//cpt:identifier", namespaces=template.getroot().nsmap)
            for ide in identifier:
                ide.text = "{0}_work".format(meta["id"])

            parent = template.xpath("//cpt:parent", namespaces=template.getroot().nsmap)
            for par in parent:
                par.text = "ENCPOS_{0}".format(meta["promotion_year"])

            creator = template.xpath("//dc:creator", namespaces=template.getroot().nsmap)
            creator[0].text = "{0}, {1}".format(meta["author_name"], meta["author_firstname"])

            titles = template.xpath("//dc:title", namespaces=template.getroot().nsmap)
            for tit in titles:
                tit.text = "{0}".format(meta["title_text"])
            lang = template.find("//dc:language", namespaces=template.getroot().nsmap)
            if meta["topic_notBefore"]:
                coverage = ET.Element(etree.QName(DC_NS,"coverage"), nsmap={'dc': DC_NS})
                coverage.text = "{0}-{1}".format(meta["topic_notBefore"], meta["topic_notAfter"])
                lang.addnext(coverage)

            year = template.xpath("//dc:date", namespaces=template.getroot().nsmap)
            year[0].text = pos_year


            if work is None:
                raise ValueError('No work detected in the work template document')
            else:
                # title
                if from_scratch is False:
                    src_edition = self.src_edition(folder_name, meta["id"])
                    titles = src_edition.xpath("//ti:teiHeader//ti:titleStmt//ti:title", namespaces=self.__nsmap)
                else:
                    src_edition = self.src_edition(folder_name, meta["id"])
                    titles = src_edition.xpath("//ti:front/ti:head", namespaces=self.__nsmap)

                # Méthode pour encapsuler les données et ajouter au niveau du root
                #template.getroot().insert(0, self.encapsulate("title", titles[0], CTS_NS))

                # make workgroup dir
                w_dirname = os.path.join(dest_path, "ENCPOS_{0}".format(meta["promotion_year"]), "{0}".format(meta["id"]))
                if os.path.isdir(w_dirname):
                    shutil.rmtree(w_dirname)
                os.makedirs(w_dirname)
                self.write_to_file(os.path.join(w_dirname, "__capitains__.xml"), template)

        return True

    def write_edition(self, folder_name, pos_year, src_path, dest_path):
        refs_decl = self.__refs_decl_template
        for meta in [m for m in self.__metadata.values() if m["promotion_year"] == pos_year]:
            # get a fresh new etree
            template = self.__e_template

            e_dirname = os.path.join(dest_path, "ENCPOS_{0}".format(meta["promotion_year"]), "{0}".format(meta["id"]))
            e_filepath = os.path.join(e_dirname, "{0}_{1}".format(
                "{0}".format(meta["id"]), "work"
            ))

            src_edition = self.src_edition(folder_name, meta["id"])
            root = template.xpath('//ti:text', namespaces=self.__nsmap)
            root[0].set("{0}id".format("{" + XML_NS + "}"), "{0}".format(meta["id"]))

            #refs_decl
            """
            header = template.xpath("//ti:teiHeader//ti:encodingDesc", namespaces=self.__nsmap)
            header[0].append(refs_decl.getroot())
            """
            # titles
            titles = src_edition.xpath("//ti:teiHeader//ti:titleStmt", namespaces=self.__nsmap)
            titleStmt = template.xpath("//ti:teiHeader//ti:titleStmt", namespaces=self.__nsmap)

            if len(titles) > 0:
                t = self.encapsulate("title", titles[0], self.__nsmap["ti"])
                t.set('type', 'main')
                titleStmt[0].insert(0, t)

            if len(titles) > 1:
                sub_title = self.encapsulate("title", titles[1], self.__nsmap["ti"])
                sub_title.set('type', 'sub')
                titleStmt[0].insert(1, sub_title)

            auth = template.xpath("//ti:teiHeader//ti:author", namespaces=self.__nsmap)
            auth[0].text = "{1} {0}".format(meta["author_name"], meta["author_firstname"])

            # publicationStmt
            pub_date = template.xpath("//ti:teiHeader//ti:publicationStmt/ti:date", namespaces=self.__nsmap)
            pub_date[0].set("when", meta["promotion_year"])

            part_index = 1
            part_p = 1
            body = template.xpath("//ti:body/ti:div", namespaces=self.__nsmap)
            src_edition_inbody = src_edition.xpath("//ti:body/node()", namespaces=self.__nsmap)
            for i, part in enumerate(src_edition_inbody):
                body[0].insert(i, part)

            # parts
            # réfléchir à comment améliorer cette partie qui permet l'injection des données, travailler à partir de body
            #Copier le body
            #Vérifier si il y a des divs, si il y a les décompter et rajouter le chapter
            #Puis compter les p dans chaque div

            parts = template.xpath("//ti:body/ti:div/ti:div", namespaces=self.__nsmap)
            if not parts:
                paragrapahe = template.xpath("//ti:body/ti:div/ti:p", namespaces=self.__nsmap)
                part_p = 1
                for par in paragrapahe:
                    part_p += 1
            else:
                for part in parts:
                    part.attrib["n"] = str(part_index)
                    part.attrib["subtype"] = "chapter"
                    part_p = 1
                    for c in part.getchildren():
                        if etree.QName(c).localname == "p":
                            c.attrib["n"] = str(part_p)
                            part_p += 1
                    part_index += 1

            #Ajout du refscdesc en fonction de la structure du fichier d'entrer et écrire les regex
            # back
            #struct = template.xpath('//ti:body//ti:p[1]/ancestor::*', namespaces=self.__nsmap)
            # write the edition file
            self.write_to_file(e_filepath, template)


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

            header = template.xpath("//ti:teiHeader//ti:encodingDesc", namespaces=self.__nsmap)
            header[0].append(refs_decl.getroot())

            # write the edition file
            self.write_to_file(e_filepath, template)

        return True