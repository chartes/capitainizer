<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:tei="http://www.tei-c.org/ns/1.0" 
    exclude-result-prefixes="xs tei"
    version="1.0">
    <xsl:output method="html" encoding="UTF-8"></xsl:output>    
    <xsl:template match="/">
        <xsl:for-each select="//tei:titleStmt/tei:title">
            <xsl:apply-templates></xsl:apply-templates>
            <xsl:if test="position()!=last()">
                <xsl:choose>
                    <xsl:when test="substring(., string-length(.), 1)!='.'">
                        <xsl:text>. </xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text> </xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:if>     
        </xsl:for-each>
    </xsl:template>
    <xsl:template match="tei:title/tei:hi">
        <i><xsl:apply-templates></xsl:apply-templates></i>
    </xsl:template>
</xsl:stylesheet>