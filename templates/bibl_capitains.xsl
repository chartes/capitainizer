<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:tei="http://www.tei-c.org/ns/1.0" 
    exclude-result-prefixes="xs tei"
    version="1.0">
    <xsl:output method="html" encoding="UTF-8"></xsl:output>    
    <xsl:template match="/">
        <xsl:apply-templates select="//tei:sourceDesc/tei:bibl"/>
    </xsl:template>
    <xsl:template match="tei:title">
        <i><xsl:apply-templates></xsl:apply-templates></i>
    </xsl:template>
</xsl:stylesheet>