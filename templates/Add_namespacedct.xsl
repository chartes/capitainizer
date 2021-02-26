<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:dct="http://purl.org/dc/terms/">
        <xsl:output indent="yes"/>
        <xsl:strip-space elements="*"/>

        <xsl:template match="@*|node()">
            <xsl:copy>
                <xsl:apply-templates select="@*|node()"/>
            </xsl:copy>
        </xsl:template>
        
        <xsl:template match="*" priority="1">
            <xsl:choose>
                <xsl:when test="namespace-uri()=''">
                    <xsl:element name="dct:{name()}">
                        <xsl:apply-templates select="@*|node()"/>
                    </xsl:element>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:copy>
                        <xsl:apply-templates select="@*|node()"/>
                    </xsl:copy>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:template>
    </xsl:stylesheet>
