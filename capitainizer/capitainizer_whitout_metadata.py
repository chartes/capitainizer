import os
from itertools import chain

import lxml.etree as ET
from lxml import etree
import shutil
import re
import html

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
        """
         Write __capitinais__.xml files who must
        :param folder_name:
        :param dest_path:
        :param list_works:
        :return:
        """
        # get a fresh new etree
        template = self.__tg_template
        # Update the URN part : pos -> pos2015
        textgroup = template.xpath("//cpt:identifier", namespaces=template.getroot().nsmap)
        if textgroup is None:
            raise ValueError('No textgroup detected in the textgroup template document')
        elif folder_name is None:
            print(list_works)
            # Information correspond aux templates donc à mettre à jour en fonction du contexte
            textgroup[0].text = "{0}".format(textgroup[0].text)
            groupname = template.xpath("//dc:title", namespaces=template.getroot().nsmap)
            groupname[0].text = "{0}".format(groupname[0].text)
            # écrire les membres par année
            collection = (template.xpath("//cpt:members", namespaces=template.getroot().nsmap))
            for work in sorted(list_works):
                print(work.split(".")[0])
                w = etree.SubElement(collection[0], etree.QName(CPT_NS, "collection"))
                w.attrib["path"] = "./{0}/__capitains__.xml".format(work.split(".")[0])
                w.attrib["identifier"] = work.split(".")[0]
            print(etree.tostring(template))
            self.write_to_file(os.path.join(dest_path, "__capitains__.xml"), template)
            return True
        else:
            #Choisir une méthode pour mettre à jour ces infos qui concernent le titre et la position
            textgroup[0].text = "{0}".format(folder_name)
            groupname = template.xpath("//dc:title", namespaces=template.getroot().nsmap)
            groupname[0].text = "{0} : {1}".format(groupname[0].text, folder_name)
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

    def obtain_identifier(self, xml_source):
        try:
            identifier = xml_source.xpath('//ti:teiHeader/ti:fileDesc/ti:publicationStmt/ti:idno', namespaces=self.__nsti)[0]
            identifier = identifier.text
        except:
            identifier = None
        return identifier

    def obtain_title(self, xml_source, meta):
        """
        titles = xml_source.xpath('//ti:titleStmt/ti:title[not(@type)]', namespaces=self.__nsti)
        for title in titles:
            title = etree.tostring(title, encoding='unicode')
            title = re.match(r"<title.*?>(.*)<\/title>", title)
            title = title.group(1)
            title = re.sub('<hi.*?>',"<i>", title)
            title = re.sub('<\/hi.*?>', "</i>", title)
            if "title" not in meta.keys():
                titleXML = title
            else:
                titleXML = "{0} . {1}".format(titleXML, title)
        titles_sub = xml_source.xpath('//ti:teiHeader/ti:fileDesc/ti:titleStmt/ti:title[@type="sub"]', namespaces=self.__nsti)
        for title_sub in titles_sub:
            title_sub = etree.tostring(title_sub, encoding='unicode')
            title_sub = re.match(r"<title.*?>(.*)<\/title>", title_sub)
            title_sub = title_sub.group(1)
            title_sub = re.sub('<hi.*?>',"<i>", title_sub)
            title_sub = re.sub('<\/hi.*?>', "</i>", title_sub)
            titleXML = "{0}. {1}".format(titleXML, title_sub)
        """
        xsltTitle = ET.parse("./templates/Titles_capitains.xsl")
        transformTitle = ET.XSLT(xsltTitle)
        titleXML = transformTitle(xml_source)
        titleXML = "\n".join([s for s in titleXML.__str__().split("\n") if s])
        titleXML = html.unescape(titleXML)
        return titleXML

    def obtain_author(self, xml_source):
        authors = xml_source.xpath('//ti:titleStmt/ti:author[not(@ana)]/@key', namespaces=self.__nsti)
        list_author = []
        if authors is not None:
            for author in authors:
                list_author.append(author)
        else:
            authors = xml_source.xpath('//ti:titleStmt/ti:author[not(@ana)]', namespaces=self.__nsti)
            for author in authors:
                list_author.append(author)
        return list_author

    def obtain_contributor(self, xml_source):
        contributors = xml_source.xpath("//ti:titleStmt/ti:author[@ana='contributor']/@key", namespaces=self.__nsti)
        list_contributor = []
        if contributors is not None:
            for contributor in contributors:
                list_contributor.append(contributor)
        else:
            contributors = xml_source.xpath("//ti:titleStmt/ti:author[@ana='contributor']", namespaces=self.__nsti)
            for contributor in contributors:
                list_contributor.append(contributor)
        contributors = xml_source.xpath('//ti:titleStmt/ti:editor/@key', namespaces=self.__nsti)
        if contributors is not None:
            for contributor in contributors:
                if contributor in list_contributor:
                    continue
                else:
                    list_contributor.append(contributor)
        else:
            contributors = xml_source.xpath('//ti:titleStmt/ti:editor', namespaces=self.__nsti)
            for contributor in contributors:
                list_contributor.append(contributor)
        return list_contributor

    def obtain_date(self, xml_source):
        try:
            date = xml_source.xpath('//ti:profileDesc/ti:creation/ti:date/@when', namespaces=self.__nsti)[0]
        except:
            date = None
        if date is None:
            try:
                date = xml_source.xpath('//ti:profileDesc/ti:creation/ti:date/@notBefore', namespaces=self.__nsti)[0]
                date = "{0} - {1}".format(date, xml_source.xpath('//ti:profileDesc/ti:creation/ti:date/@notAfter', namespaces=self.__nsti)[0])
            except:
                date = "2022"
        return date

    def obtain_publisher(self, xml_source):
        publishers = xml_source.xpath('//ti:publicationStmt/ti:publisher', namespaces=self.__nsti)
        list_publisher = []
        for publisher in publishers:
            publisher = etree.tostring(publisher, encoding='unicode')
            publisher = re.match(r"<publisher.*?>(.*)<\/publisher>", publisher)
            publisher = publisher.group(1)
            list_publisher.append(publisher)
        return list_publisher

    def obtain_language(self, xml_source):
        try:
            language = xml_source.xpath('//ti:TEI/@xml:lang', namespaces=self.__nsti)[0]
        except:
            language = None
        if language is None:
            try:
                language = xml_source.xpath('//ti:profileDesc/ti:langUsage/ti:language/@ident', namespaces=self.__nsti)[0]
            except:
                language = None
        return language

    def obtain_rights(self, xml_source):
        try:
            rights = xml_source.xpath('//ti:fileDesc/ti:publicationStmt/ti:availability/ti:licence/@target', namespaces=self.__nsti)[0]
        except:
            rights = None
        return rights

    def obtain_description(self, xml_source):
        descriptions = xml_source.xpath("//ti:fileDesc/ti:noteStmt/ti:note[@type='abstract']", namespaces=self.__nsti)
        print(descriptions)
        list_description = []
        if descriptions is not None:
            for description in descriptions:
                list_description.append(description.text)
        return list_description

    def obtain_isPartOf(self, xml_source):
        try:
            isPartOfs = xml_source.xpath("//ti:fileDesc/ti:seriesStmt/ti:idno")[0]
        except:
            isPartOfs = None
        return isPartOfs

    def obtain_source(self, xml_source):
        xsltBibl = ET.parse("./templates/bibl_capitains.xsl")
        transformBibl = ET.XSLT(xsltBibl)
        source = transformBibl(xml_source)
        source = "\n".join([s for s in source.__str__().split("\n") if s])
        source = html.unescape(source)
        return source

    def obtain_metadata (self, folder_name, id):
        """
        Extract all the metadata inside the TEI-Header of an xml files to create

        :param folder_name: Path of the folder name
        :param id: name of the xml files
        :return: list of metadata export from the TEI HEADER
        """
        meta = {}
        src_edition = self.src_edition(id, folder_name)
        meta["id"] = id.replace(".xml", "")
        meta["identifier"] = self.obtain_identifier(src_edition)
        meta["title"] = self.obtain_title(src_edition, meta)
        meta["author"] = self.obtain_author(src_edition)
        meta["contributor"] = self.obtain_contributor(src_edition)
        meta["year"] = self.obtain_date(src_edition)
        meta["publisher"] = self.obtain_publisher(src_edition)
        meta["language"] = self.obtain_language(src_edition)
        meta["rights"] = self.obtain_rights(src_edition)
        meta["description"] = self.obtain_description(src_edition)
        meta["isPartOf"] = self.obtain_isPartOf(src_edition)
        meta["source"] = self.obtain_source(src_edition)
        return meta

    #Fonction qui écrit __capitains__.xml au niveau des éditions
    def write_work(self, folder_name, dest_path, list_works, from_scratch=True):
        cleanr = re.compile('<.*?>')
        for works in list_works:
            meta = self.obtain_metadata(folder_name, works)
            print(meta)
            template = self.__wg_template

            #Ajout des valeurs du tableau dans les valeurs dublin core classique
            work = template.xpath("//cpt:members/cpt:collection", namespaces=template.getroot().nsmap)
            work[0].attrib["path"] = "./{0}.xml".format(meta["id"])

            identifier = template.xpath("//cpt:identifier", namespaces=template.getroot().nsmap)
            for ide in identifier:
                ide.text = "{0}".format(meta["id"])

            parent = template.xpath("//cpt:parent", namespaces=template.getroot().nsmap)
            for par in parent:
                par.text = folder_name

            titles = template.xpath("//dc:title", namespaces=template.getroot().nsmap)
            for tit in titles:
                tit.text = re.sub(cleanr,'',meta["title"])

            titles = template.xpath("//dct:title", namespaces=template.getroot().nsmap)
            for tit in titles:
                tit.text = re.sub(cleanr,'',meta["title"])

            languages = template.xpath("//dc:language", namespaces=template.getroot().nsmap)
            for language in languages:
                language.text = meta["language"]


            #Ajout des valeurs dans les entrées dtc
            structuredMetadata = template.xpath("//cpt:structured-metadata", namespaces=template.getroot().nsmap)
            if meta["identifier"] is not None:
                elem = etree.Element(ET.QName(DC_NS, "identifier"), nsmap={'dct': DC_NS})
                elem.text = "{0}".format(meta["identifier"])
                structuredMetadata[0].append(elem)

            if meta["author"] is not []:
                for author in meta["author"]:
                    elem = etree.Element(ET.QName(DC_NS, "creator"), nsmap={'dc': DC_NS})
                    elem.text = "{0}".format(author)
                    structuredMetadata[0].append(elem)

            if meta["contributor"] is not []:
                for contributor in meta["contributor"]:
                    elem = etree.Element(ET.QName(DCT_NS, "contributor"), nsmap={'dct': DCT_NS})
                    elem.text = "{0}".format(contributor)
                    structuredMetadata[0].append(elem)

            if meta["description"] is not []:
                for descritpion in meta["description"]:
                    elem = etree.Element(ET.QName(DC_NS, "description"), nsmap={'dct': DC_NS})
                    elem.text = "{0}".format(descritpion)
                    structuredMetadata[0].append(elem)

            if meta["isPartOf"] is not None:
                elem = etree.Element(ET.QName(DC_NS, "isPartOf"), nsmap={'dct': DC_NS})
                elem.text = "{0}".format(meta["isPartOf"])
                structuredMetadata[0].append(elem)

            if meta["source"] is not None:
                elem = etree.Element(ET.QName(DC_NS, "source"), nsmap={'dct': DC_NS})
                elem.text = "{0}".format(meta["source"])
                structuredMetadata[0].append(elem)

            publishers = template.xpath("//dct:publisher", namespaces=template.getroot().nsmap)
            if meta["publisher"] != []:
                for publisher in publishers:
                    publisher.text = meta["publisher"][0]
            """        
            Méthode pour configurer l'url dts pour obtenir dts download    
            download_xml = etree.Element(ET.QName(DTS_NS, "download"), nsmap={'dts': DTS_NS})
            download_xml.text = "{0}/dts/document?id={0}".format(url_dts, meta["id"] )
            structuredMetadata[0].append(download_xml)
            """
            elem = etree.Element(ET.QName(DCT_NS, "language"), nsmap={'dct': DCT_NS})
            elem.text = "{0}".format(meta["language"])
            structuredMetadata[0].append(elem)

            elem = etree.Element(ET.QName(HTML_NS, "h1"), nsmap={'xml': HTML_NS})
            elem.text = "{0}".format(meta["title"])
            structuredMetadata[0].append(elem)

            if meta["rights"] is not None:
                elem = etree.Element(ET.QName(DCT_NS, "rights"), nsmap={'dct': DCT_NS})
                elem.text = "{0}".format(meta["rights"])
                structuredMetadata[0].append(elem)

            year = template.xpath("//dct:date", namespaces=template.getroot().nsmap)
            year[0].text = meta["year"]

            if work is None:
                raise ValueError('No work detected in the work template document')
            else:
                # make workgroup dir
                w_dirname = os.path.join(dest_path, folder_name, "{0}".format(meta["id"]))
                if os.path.isdir(w_dirname):
                    shutil.rmtree(w_dirname)
                os.makedirs(w_dirname)
                self.write_to_file(os.path.join(w_dirname, "__capitains__.xml"), template)

        return True

    #Ecriture de la position avec les nouvelles valeurs
    def write_edition(self, folder_name, dest_path, list_works):
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