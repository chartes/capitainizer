import os
from itertools import chain
import re

import lxml.etree as ET
from lxml import etree
import shutil

CTS_NS = "http://chs.harvard.edu/xmlns/cts"
XML_NS = "http://www.w3.org/XML/1998/namespace"
DC_NS = "http://purl.org/dc/elements/1.1/"
CPT_NS = "http://purl.org/capitains/ns/1.0#"
HTML_NS = "http://www.w3.org/1999/xhtml/"
DCT_NS = "http://purl.org/dc/terms/"
DTS_NS = "https://w3id.org/dts/api#"

class Capitainizer_files:

    def __init__(self, src_path, textgroup_template, work_template, edition_template, refs_decl_template, xslt_encondingDesc):
        self.__tg_template_filename = textgroup_template
        self.__w_template_filename = work_template
        self.__e_template_filename = edition_template
        self.__enconding_desc_template_filename = refs_decl_template
        self.__xslt_encodingDesc_filename = xslt_encondingDesc
        self.__src_path = src_path
        self.__nsti = {"ti": 'http://www.tei-c.org/ns/1.0'}

    @staticmethod
    def stringify(node):
        parts = ([node.text] +
                 list(chain((ET.tounicode(c) for c in node.getchildren()))) +
                 [node.tail])
        parts = filter(None, parts)
        return ''.join(parts).strip()

    def src_edition(self, id, folder_name = None):
        parser = etree.XMLParser()
        id = "{0}.xml".format(id) if "xml" not in id else id
        if folder_name in self.__src_path:
            src_edition_fn = os.path.join(self.__src_path, id)
        else:
            src_edition_fn = os.path.join(self.__src_path, folder_name, id)
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
                tree_str = etree.tostring(tree, pretty_print=True, doctype='<?xml version="1.0" encoding="utf-8"?>', encoding='unicode')
                f.write(tree_str)

    def write_textgroup(self,  folder_name, dest_path, list_works):
        # get a fresh new etree
        template = self.__tg_template
        # Update the URN part : pos -> pos2015
        textgroup = template.xpath("//cpt:identifier", namespaces=template.getroot().nsmap)
        if textgroup is None:
            raise ValueError('No textgroup detected in the textgroup template document')
        elif folder_name is None:
            # Information correspond aux templates donc à mettre à jour en fonction du contexte
            textgroup[0].text = "{0}".format(textgroup[0].text)
            groupname = template.xpath("//dc:title", namespaces=template.getroot().nsmap)
            groupname[0].text = "{0}".format(groupname[0].text)
            # écrire les membres par année
            collection = (template.xpath("//cpt:members", namespaces=template.getroot().nsmap))
            for work in sorted(list_works):
                w = etree.SubElement(collection[0], etree.QName(CPT_NS, "collection"))
                w.attrib["path"] = "./{0}/__capitains__.xml".format(work.split(".")[0])
                w.attrib["identifier"] = work.split(".")[0]
            print(dest_path)
            self.write_to_file(os.path.join(dest_path, "__capitains__.xml"), template)
            return True
        else:
            #Choisir une méthode pour mettre à jour ces infos qui concernent le titre et la position
            textgroup[0].text = "{0}".format(folder_name)
            groupname = template.xpath("//dc:title", namespaces=template.getroot().nsmap)
            groupname[0].text = "{0} de {1}".format(groupname[0].text, folder_name)
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
    def obtain_metadata (self, folder_name, id):
        meta = {}
        src_edition = self.src_edition(id, folder_name)
        meta["id"] = id.replace(".xml", "")
        meta["title"] = src_edition.xpath('//ti:titleStmt/ti:title', namespaces=self.__nsti)[0].text
        try:
            meta["author"] = src_edition.xpath('//ti:titleStmt/ti:author', namespaces=self.__nsti)[0].text
        except:
            meta["author"] = None
        meta["promotion_year"] = src_edition.xpath('//ti:profileDesc/ti:creation/ti:date[@when]', namespaces=self.__nsti)[0].text
        return meta

    #Fonction qui écrit __capitains__.xml au niveau des éditions
    def write_work(self, folder_name, pos_year, dest_path, list_works, from_scratch=True):
        for works in list_works:
            meta = self.obtain_metadata(folder_name, works)
            template = self.__wg_template

            #Ajout des valeurs du tableau dans les valeurs dublin core classique
            work = template.xpath("//cpt:members/cpt:collection", namespaces=template.getroot().nsmap)
            work[0].attrib["path"] = meta["id"]

            identifier = template.xpath("//cpt:identifier", namespaces=template.getroot().nsmap)
            for ide in identifier:
                ide.text = "{0}".format(meta["id"])

            parent = template.xpath("//cpt:parent", namespaces=template.getroot().nsmap)
            for par in parent:
                par.text = folder_name

            titles = template.xpath("//dc:title", namespaces=template.getroot().nsmap)
            for tit in titles:
                tit.text = meta["title"]


            #Ajout des valeurs dans les entrées dtc
            structuredMetadata = template.xpath("//cpt:structured-metadata", namespaces=template.getroot().nsmap)
            elem = etree.Element(ET.QName(DCT_NS, "rights"), nsmap={'dct': DCT_NS})
            elem.text = "https://creativecommons.org/licenses/by-nc-nd/3.0/fr/"
            structuredMetadata[0].append(elem)

            if meta["author"]:
                elem = etree.Element(ET.QName(DC_NS, "creator"), nsmap={'dc': DC_NS})
                elem.text = "{0}".format(meta["author"])
                structuredMetadata[0].append(elem)

            year = template.xpath("//dct:date", namespaces=template.getroot().nsmap)
            year[0].text = meta["promotion_year"]

            if work is None:
                raise ValueError('No work detected in the work template document')
            else:
                # title
                if from_scratch is False:
                    src_edition = self.src_edition(meta["id"], folder_name)
                    titles = src_edition.xpath("//ti:teiHeader//ti:titleStmt//ti:title", namespaces=self.__nsti)
                else:
                    src_edition = self.src_edition(meta["id"], folder_name)
                    titles = src_edition.xpath("//ti:front/ti:head", namespaces=self.__nsti)

                # make workgroup dir
                w_dirname = os.path.join(dest_path, folder_name, "{0}".format(meta["id"]))
                if os.path.isdir(w_dirname):
                    shutil.rmtree(w_dirname)
                os.makedirs(w_dirname)
                self.write_to_file(os.path.join(w_dirname, "__capitains__.xml"), template)

        return True

    #Ecriture de la position avec les nouvelles valeurs
    def write_edition(self, folder_name, pos_year, src_path, dest_path, list_works):
        for work in list_works:
            refs_decl = self.__refs_decl_template
            e_dirname = os.path.join(dest_path, folder_name , "{0}".format(work.replace(".xml", "")))
            e_filepath = os.path.join(e_dirname, work)

            src_edition = self.src_edition(work, folder_name)
            root = src_edition.xpath('//ti:text', namespaces=self.__nsti)

            try:
                root[0].set("{0}base".format("{" + XML_NS + "}"), "{0}".format(work))
            except:
                print(work + "not present")
                continue

            TEIheader = src_edition.xpath("//ti:teiHeader", namespaces={"ti": 'http://www.tei-c.org/ns/1.0'})
            TEIheader[0].append(refs_decl.getroot())
            etree.strip_tags(TEIheader[0], 'temp')

            body = src_edition.xpath("//ti:body", namespaces=self.__nsti)
            body[0].set("type", "textpart")
            body[0].set("subtype", "position")
            body[0].set("n", "1")
            self.write_to_file(e_filepath, src_edition)